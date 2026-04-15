"""
NewsRoast-Agent 核心配置管理

基于Pydantic Settings的环境变量验证和类型安全配置管理。
支持从.env文件自动加载配置。
"""

import os
from typing import Optional
from functools import lru_cache

try:
    from pydantic_settings import BaseSettings
    from pydantic_settings import SettingsConfigDict
    PYDANTIC_SETTINGS_AVAILABLE = True
except ImportError:
    from pydantic import BaseModel as BaseSettings
    SettingsConfigDict = None
    PYDANTIC_SETTINGS_AVAILABLE = False


class Settings(BaseSettings):
    """应用全局配置"""

    # ==========================================
    # 🔑 API 密钥配置
    # ==========================================

    # 阿里云百炼 (通义千问/通义万相)
    modelscope_api_key: str = ""
    modelscope_base_url: str = "https://api-inference.modelscope.cn/v1"

    # 阿里云灵积增强接口 (备用)
    aliyun_api_key: Optional[str] = None
    aliyun_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # 搜索增强 API (Tavily)
    tavily_api_key: Optional[str] = None

    # ==========================================
    # 🤖 模块化模型配置
    # ==========================================

    # --- 1. 新闻分析模块 (需要强大的 Vision 视觉能力) ---
    analyzer_model: str = "Qwen/Qwen3.5-35B-A3B"

    # --- 2. 评论生成模块 (需要极强的"网感"和幽默感) ---
    writer_model: str = "MiniMax/MiniMax-M2.5"

    # --- 3. 搜索词优化模块 (需要理解关键词提取) ---
    searcher_model: str = "deepseek-ai/DeepSeek-V3.2"

    # --- 4. 图像生成模块 (决定了最后的梗图质量) ---
    image_gen_model: str = "Qwen/Qwen-Image-2512"

    # ==========================================
    # 📱 Reddit API 配置
    # ==========================================

    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_user_agent: str = "News Comment Agent by /u/example_user"

    # ==========================================
    # ⚙️ 系统配置
    # ==========================================

    max_reddit_comments: int = 10
    max_generated_comments: int = 5
    request_timeout: int = 30

    # 新闻分析配置
    max_text_length: int = 3000
    max_images_to_analyze: int = 2

    # 图像生成配置
    image_generation_timeout: int = 120
    max_retry_count: int = 100
    polling_interval: int = 5

    # 开发与调试配置
    debug_mode: bool = False
    log_level: str = "INFO"

    if PYDANTIC_SETTINGS_AVAILABLE and SettingsConfigDict is not None:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore",
        )


@lru_cache()
def get_settings() -> Settings:
    """获取单例配置实例"""
    return Settings()


# 向后兼容的全局配置实例
settings = get_settings()