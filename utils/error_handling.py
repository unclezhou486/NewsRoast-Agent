"""
NewsRoast-Agent 统一错误处理框架

基于Pydantic的数据验证和自定义异常类，提供统一的错误处理和降级策略。
"""

import logging
import traceback
from typing import Type, Optional, Any, Callable, Dict
from functools import wraps
from datetime import datetime

from config.constants import ErrorCodes

# 配置日志记录器
logger = logging.getLogger(__name__)


class NewsRoastError(Exception):
    """NewsRoast-Agent基础异常类"""

    def __init__(self,
                 message: str,
                 module: str = "unknown",
                 error_code: int = ErrorCodes.SYSTEM_ERROR,
                 details: Optional[Dict[str, Any]] = None):
        """
        初始化异常

        Args:
            message: 错误消息
            module: 发生错误的模块名称
            error_code: 错误码（使用ErrorCodes中的常量）
            details: 额外的错误详情
        """
        self.message = message
        self.module = module
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now()

        super().__init__(f"[{module}] {message} (code: {error_code})")

    def to_dict(self) -> Dict[str, Any]:
        """将异常转换为字典格式，便于日志记录或API返回"""
        return {
            "error_code": self.error_code,
            "error_message": self.message,
            "error_module": self.module,  # 避免与 logging.LogRecord 的保留字冲突
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


class APIConnectionError(NewsRoastError):
    """API连接异常"""

    def __init__(self,
                 message: str,
                 api_name: str = "unknown_api",
                 url: Optional[str] = None,
                 status_code: Optional[int] = None):
        self.api_name = api_name
        super().__init__(
            message=message,
            module=f"api.{api_name}",
            error_code=ErrorCodes.API_CONNECTION_ERROR,
            details={
                "api_name": api_name,
                "url": url,
                "status_code": status_code,
            }
        )


class ContentParseError(NewsRoastError):
    """内容解析异常"""

    def __init__(self,
                 message: str,
                 content_type: str = "unknown",
                 source: Optional[str] = None):
        self.content_type = content_type
        super().__init__(
            message=message,
            module="content_parser",
            error_code=ErrorCodes.CONTENT_PARSE_ERROR,
            details={
                "content_type": content_type,
                "source": source,
            }
        )


class ModelGenerationError(NewsRoastError):
    """模型生成异常"""

    def __init__(self,
                 message: str,
                 model_name: str = "unknown_model",
                 prompt_length: Optional[int] = None):
        self.model_name = model_name
        self.prompt_length = prompt_length
        super().__init__(
            message=message,
            module=f"model.{model_name}",
            error_code=ErrorCodes.COMMENT_GENERATION_FAILED,
            details={
                "model_name": model_name,
                "prompt_length": prompt_length,
            }
        )


class ImageGenerationError(NewsRoastError):
    """图像生成异常"""

    def __init__(self,
                 message: str,
                 model_name: str = "unknown_model",
                 task_id: Optional[str] = None,
                 status: Optional[str] = None):
        self.model_name = model_name
        self.task_id = task_id
        self.status = status
        super().__init__(
            message=message,
            module="image_generator",
            error_code=ErrorCodes.IMAGE_GENERATION_FAILED,
            details={
                "model_name": model_name,
                "task_id": task_id,
                "status": status,
            }
        )


class ConfigurationError(NewsRoastError):
    """配置异常"""

    def __init__(self,
                 message: str,
                 config_key: Optional[str] = None):
        super().__init__(
            message=message,
            error_code=ErrorCodes.CONFIGURATION_ERROR,
            module="config",
            details={
                "config_key": config_key,
            }
        )


class ValidationError(NewsRoastError):
    """数据验证异常"""

    def __init__(self,
                 message: str,
                 field_name: Optional[str] = None,
                 value: Any = None):
        super().__init__(
            message=message,
            error_code=ErrorCodes.CONTENT_VALIDATION_ERROR,
            module="validation",
            details={
                "field_name": field_name,
                "value": value,
            }
        )


def handle_exceptions(default_return=None, re_raise: bool = False):
    """
    异常处理装饰器

    Args:
        default_return: 发生异常时返回的默认值
        re_raise: 是否重新抛出异常（用于需要外部处理的场景）

    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except NewsRoastError as e:
                # 业务异常，记录错误日志但不重新抛出（除非指定re_raise）
                logger.error(f"业务异常 [{e.module}]: {e.message}")
                if re_raise:
                    raise
                return default_return
            except Exception as e:
                # 未预期的异常，记录详细堆栈
                logger.exception(f"未预期的异常: {str(e)}")
                if re_raise:
                    raise
                return default_return
        return wrapper
    return decorator


def with_retry(max_retries: int = 3,
               delay: float = 1.0,
               delay_base: Optional[float] = None,
               exponential_backoff: bool = True,
               retry_exceptions: Optional[tuple] = None):
    """
    重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 基础延迟时间（秒），delay_base的别名
        delay_base: 基础延迟时间（秒，向后兼容）
        exponential_backoff: 是否使用指数退避
        retry_exceptions: 允许重试的异常类型元组，None表示默认重试API/Model/Image错误

    Returns:
        装饰器函数
    """
    # delay_base 优先，保持向后兼容
    effective_delay = delay_base if delay_base is not None else delay

    # 默认重试异常类型
    if retry_exceptions is None:
        _retry_exceptions = (APIConnectionError, ModelGenerationError, ImageGenerationError)
    else:
        _retry_exceptions = retry_exceptions

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time

            last_exception = None
            for attempt in range(max_retries + 1):  # 包括初始尝试
                try:
                    return func(*args, **kwargs)
                except _retry_exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.warning(f"操作失败，已达到最大重试次数 ({max_retries})")
                        raise

                    # 计算延迟时间
                    if exponential_backoff:
                        wait = effective_delay * (2 ** attempt)
                    else:
                        wait = effective_delay

                    logger.warning(
                        f"操作失败，将在 {wait:.1f} 秒后重试 "
                        f"(尝试 {attempt + 1}/{max_retries + 1}): {e}"
                    )
                    time.sleep(wait)
                except Exception as e:
                    # 其他类型的异常不重试
                    logger.error(f"非重试型异常: {str(e)}")
                    raise

            # 如果所有重试都失败，抛出最后一个异常
            raise last_exception
        return wrapper
    return decorator


def log_execution_time(func: Callable) -> Callable:
    """
    记录函数执行时间的装饰器

    Args:
        func: 要装饰的函数

    Returns:
        装饰后的函数
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        import time
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            logger.info(
                f"函数 {func.__name__} 执行时间: {execution_time:.3f} 秒"
            )

            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"函数 {func.__name__} 执行失败，耗时: {execution_time:.3f} 秒, 错误: {e}"
            )
            raise

    return wrapper


def setup_logging(log_level: str = "INFO") -> None:
    """
    配置日志系统

    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # 创建格式化器
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 配置控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(console_handler)

    # 为我们的模块设置特定级别
    logger.setLevel(getattr(logging, log_level.upper()))

    logger.info(f"日志系统已配置，级别: {log_level}")


def safe_execute(func: Callable, *args, default_return=None, **kwargs) -> Any:
    """
    安全执行函数，捕获所有异常并返回默认值

    Args:
        func: 要执行的函数
        *args: 函数位置参数
        default_return: 异常时的返回值
        **kwargs: 函数关键字参数

    Returns:
        函数返回值或默认值
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"安全执行失败: {func.__name__} - {str(e)}")
        return default_return