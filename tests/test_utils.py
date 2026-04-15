"""
测试工具函数和错误处理
"""
import pytest
import logging
from unittest.mock import patch, MagicMock
from utils.error_handling import (
    NewsRoastError, APIConnectionError, ContentParseError,
    ModelGenerationError, ImageGenerationError,
    handle_exceptions, log_execution_time, with_retry
)


class TestNewsRoastError:
    """测试自定义异常"""

    def test_base_error(self):
        """测试基础异常"""
        error = NewsRoastError("测试错误", "test_module")
        assert "test_module" in str(error)
        assert "测试错误" in str(error)
        assert error.module == "test_module"
        assert error.message == "测试错误"

    def test_api_connection_error(self):
        """测试API连接异常"""
        error = APIConnectionError("连接失败", "api_module")
        assert isinstance(error, NewsRoastError)
        assert "api_module" in str(error)

    def test_content_parse_error(self):
        """测试内容解析异常"""
        error = ContentParseError("解析失败", "parse_module")
        assert isinstance(error, NewsRoastError)

    def test_model_generation_error(self):
        """测试模型生成异常"""
        error = ModelGenerationError("生成失败", "model_name", 100)
        assert error.model_name == "model_name"
        assert error.prompt_length == 100
        assert "model_name" in str(error)

    def test_image_generation_error(self):
        """测试图像生成异常"""
        error = ImageGenerationError("图像生成失败", "image_model", "task_123")
        assert error.model_name == "image_model"
        assert error.task_id == "task_123"


class TestHandleExceptionsDecorator:
    """测试异常处理装饰器"""

    def test_handle_exceptions_success(self):
        """测试函数成功执行"""
        @handle_exceptions(default_return="默认值")
        def successful_function():
            return "成功"

        result = successful_function()
        assert result == "成功"

    def test_handle_exceptions_newsroast_error(self):
        """测试捕获NewsRoastError"""
        @handle_exceptions(default_return="默认值")
        def failing_function():
            raise NewsRoastError("业务错误", "test")

        result = failing_function()
        assert result == "默认值"

    def test_handle_exceptions_general_error(self):
        """测试捕获一般异常"""
        @handle_exceptions(default_return="默认值")
        def failing_function():
            raise ValueError("意外错误")

        result = failing_function()
        assert result == "默认值"

    def test_handle_exceptions_no_default(self):
        """测试没有默认返回值"""
        @handle_exceptions()
        def failing_function():
            raise NewsRoastError("错误", "test")

        result = failing_function()
        assert result is None


class TestLogExecutionTimeDecorator:
    """测试执行时间日志装饰器"""

    @patch('utils.error_handling.logger')
    def test_log_execution_time(self, mock_logger):
        """测试记录执行时间"""
        @log_execution_time
        def slow_function():
            import time
            time.sleep(0.01)
            return "完成"

        result = slow_function()
        assert result == "完成"
        assert mock_logger.info.called
        call_args = mock_logger.info.call_args[0][0]
        assert "slow_function" in call_args
        assert "执行时间" in call_args


class TestWithRetryDecorator:
    """测试重试装饰器"""

    def test_with_retry_success_first_try(self):
        """测试第一次尝试成功"""
        call_count = 0

        @with_retry(max_retries=3, delay=0.01)
        def successful_function():
            nonlocal call_count
            call_count += 1
            return "成功"

        result = successful_function()
        assert result == "成功"
        assert call_count == 1

    def test_with_retry_success_after_retry(self):
        """测试重试后成功"""
        call_count = 0

        @with_retry(max_retries=3, delay=0.01)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise APIConnectionError("暂时失败", "test")
            return "成功"

        result = flaky_function()
        assert result == "成功"
        assert call_count == 2

    def test_with_retry_failure(self):
        """测试重试后仍然失败"""
        call_count = 0

        @with_retry(max_retries=2, delay=0.01)
        def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise APIConnectionError("永久失败", "test")

        with pytest.raises(APIConnectionError):
            always_failing_function()
        assert call_count == 3  # 初始调用 + 2次重试

    def test_with_retry_exception_filter(self):
        """测试异常过滤器"""
        call_count = 0

        @with_retry(max_retries=2, delay=0.01, retry_exceptions=(ValueError,))
        def function_with_wrong_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("不应该重试的错误")

        with pytest.raises(TypeError):
            function_with_wrong_error()
        assert call_count == 1  # 不应该重试

    def test_with_retry_logging(self):
        """测试重试日志"""
        with patch('utils.error_handling.logger') as mock_logger:
            call_count = 0

            @with_retry(max_retries=2, delay=0.01)
            def flaky_function():
                nonlocal call_count
                call_count += 1
                if call_count < 2:
                    raise APIConnectionError("失败", "test")
                return "成功"

            result = flaky_function()
            assert result == "成功"
            # 检查是否有重试日志
            assert any("重试" in str(call) for call in mock_logger.warning.call_args_list)


class TestErrorHandlingIntegration:
    """测试错误处理集成"""

    def test_decorator_combination(self):
        """测试装饰器组合使用"""
        call_count = 0

        @handle_exceptions(default_return="降级结果")
        @log_execution_time
        @with_retry(max_retries=1, delay=0.01)
        def problematic_function():
            nonlocal call_count
            call_count += 1
            raise APIConnectionError("API失败", "test")

        result = problematic_function()
        assert result == "降级结果"
        assert call_count == 2  # 初始调用 + 1次重试


if __name__ == "__main__":
    pytest.main([__file__])