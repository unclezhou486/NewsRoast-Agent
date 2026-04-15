"""
NewsRoast-Agent 模块化配置包

本包提供统一、类型安全的配置管理，替代原有的单一config.py文件。
使用Pydantic Settings进行环境变量验证和类型检查。
"""

from .settings import Settings, get_settings
from .api import API_CONFIG, get_api_config, MODELSCOPE_CONFIG, TAVILY_CONFIG, REDDIT_CONFIG, HACKERNEWS_CONFIG
from .models import MODEL_CONFIG, get_model_config, QWEN_VISION_MODEL, MINIMAX_M2_5_MODEL, DEEPSEEK_V3_2_MODEL, QWEN_IMAGE_MODEL, QWEN_3_32B_MODEL
from .prompts import PROMPT_TEMPLATES, get_prompt, NEWS_ANALYSIS_PROMPT, COMMENT_GENERATION_PROMPT, SEARCH_QUERY_OPTIMIZATION_PROMPT, VISUAL_PROMPT_DESIGN_PROMPT
from .constants import *

# 向后兼容变量导出（供旧代码使用）
settings = get_settings()

# API Key 导出
MODELSCOPE_API_KEY = settings.modelscope_api_key
MODELSCOPE_BASE_URL = settings.modelscope_base_url
TAVILY_API_KEY = settings.tavily_api_key if settings.tavily_api_key else ""
ALIYUN_API_KEY = settings.aliyun_api_key if settings.aliyun_api_key else ""
ALIYUN_BASE_URL = settings.aliyun_base_url
REDDIT_CLIENT_ID = settings.reddit_client_id if settings.reddit_client_id else ""
REDDIT_CLIENT_SECRET = settings.reddit_client_secret if settings.reddit_client_secret else ""
REDDIT_USER_AGENT = settings.reddit_user_agent

# 模型配置导出
analyzer_config = get_model_config("analyzer")
writer_config = get_model_config("writer")
searcher_config = get_model_config("searcher")
image_gen_config = get_model_config("image_gen")

ANALYZER_API_KEY = MODELSCOPE_API_KEY
ANALYZER_BASE_URL = MODELSCOPE_BASE_URL
ANALYZER_MODEL = analyzer_config.model_id

WRITER_API_KEY = MODELSCOPE_API_KEY
WRITER_BASE_URL = MODELSCOPE_BASE_URL
WRITER_MODEL = writer_config.model_id

SEARCHER_API_KEY = MODELSCOPE_API_KEY
SEARCHER_BASE_URL = MODELSCOPE_BASE_URL
SEARCHER_MODEL = searcher_config.model_id

IMAGE_API_KEY = MODELSCOPE_API_KEY
IMAGE_BASE_URL = MODELSCOPE_BASE_URL
IMAGE_GEN_MODEL = image_gen_config.model_id

# 系统配置导出
MAX_REDDIT_COMMENTS = settings.max_reddit_comments
MAX_GENERATED_COMMENTS = settings.max_generated_comments

__all__ = [
    "Settings",
    "get_settings",
    "API_CONFIG",
    "MODEL_CONFIG",
    "PROMPT_TEMPLATES",
    # 向后兼容导出
    "MODELSCOPE_API_KEY", "MODELSCOPE_BASE_URL", "TAVILY_API_KEY",
    "ALIYUN_API_KEY", "ALIYUN_BASE_URL",
    "ANALYZER_API_KEY", "ANALYZER_BASE_URL", "ANALYZER_MODEL",
    "WRITER_API_KEY", "WRITER_BASE_URL", "WRITER_MODEL",
    "SEARCHER_API_KEY", "SEARCHER_BASE_URL", "SEARCHER_MODEL",
    "IMAGE_API_KEY", "IMAGE_BASE_URL", "IMAGE_GEN_MODEL",
    "REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USER_AGENT",
    "MAX_REDDIT_COMMENTS", "MAX_GENERATED_COMMENTS",
    "NEWS_ANALYSIS_PROMPT", "COMMENT_GENERATION_PROMPT",
]