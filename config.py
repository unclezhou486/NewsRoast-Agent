“””
NewsRoast-Agent 统一配置文件（向后兼容适配器）

本文件为向后兼容而保留，作为旧代码与新模块化配置之间的适配层。
所有配置已迁移至新的模块化配置系统（config/目录下）。

设计原则:
- 保持与旧代码的完全向后兼容
- 从新的模块化配置系统重新导出所有变量
- 提供废弃警告，鼓励迁移到新系统

注意: 新代码应该直接导入config模块中的具体配置类，而不是使用本文件。
“””

import warnings
from dotenv import load_dotenv

# 加载环境变量以支持遗留代码
load_dotenv()

# 从新配置系统导入配置
from config.settings import settings
from config.api import get_api_config, MODELSCOPE_CONFIG, ALIYUN_ENHANCED_CONFIG, TAVILY_CONFIG, REDDIT_CONFIG, HACKERNEWS_CONFIG
from config.models import get_model_config, QWEN_VISION_MODEL, MINIMAX_M2_5_MODEL, DEEPSEEK_V3_2_MODEL, QWEN_IMAGE_MODEL, QWEN_3_32B_MODEL
from config.prompts import get_prompt, NEWS_ANALYSIS_PROMPT, COMMENT_GENERATION_PROMPT, SEARCH_QUERY_OPTIMIZATION_PROMPT, VISUAL_PROMPT_DESIGN_PROMPT
from config.constants import (
    CommentStyle, ImageStyle, CringeScoreWeights, LengthLimits,
    TimeoutConstants, PathConstants, QuantityLimits, QualityScoreRanges,
    ErrorCodes, RegexPatterns, RedditConstants, ImageGenerationConstants,
    OutputFormats
)

# 发出废弃警告
warnings.warn(
    “config.py已废弃，请迁移到模块化配置系统（导入config.settings, config.api等）”,
    DeprecationWarning,
    stacklevel=2
)

# ==========================================
# 🔑 API KEY 统一管理区（向后兼容导出）
# ==========================================

# 从settings中获取配置
MODELSCOPE_API_KEY = settings.modelscope_api_key
MODELSCOPE_BASE_URL = settings.modelscope_base_url

TAVILY_API_KEY = settings.tavily_api_key if settings.tavily_api_key else “”

ALIYUN_API_KEY = settings.aliyun_api_key if settings.aliyun_api_key else “”
ALIYUN_BASE_URL = settings.aliyun_base_url

# ==========================================
# 🤖 模块化模型配置（向后兼容导出）
# ==========================================

# 使用新配置系统中的模型配置
analyzer_config = get_model_config(“analyzer”)
writer_config = get_model_config(“writer”)
searcher_config = get_model_config(“searcher”)
image_gen_config = get_model_config(“image_gen”)

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

# ==========================================
# 📱 Reddit API 配置（向后兼容导出）
# ==========================================

REDDIT_CLIENT_ID = settings.reddit_client_id if settings.reddit_client_id else “”
REDDIT_CLIENT_SECRET = settings.reddit_client_secret if settings.reddit_client_secret else “”
REDDIT_USER_AGENT = settings.reddit_user_agent

# ==========================================
# ⚙️ 系统配置（向后兼容导出）
# ==========================================

MAX_REDDIT_COMMENTS = settings.max_reddit_comments
MAX_GENERATED_COMMENTS = settings.max_generated_comments

# ==========================================
# 📝 Prompt配置（向后兼容导出）
# ==========================================

# 直接使用从新配置系统导入的Prompt
NEWS_ANALYSIS_PROMPT = NEWS_ANALYSIS_PROMPT
COMMENT_GENERATION_PROMPT = COMMENT_GENERATION_PROMPT

# ==========================================
# 📋 常量导出（用于向后兼容）
# ==========================================

# 导出所有重要的常量类
__all__ = [
    # API配置
    “MODELSCOPE_API_KEY”, “MODELSCOPE_BASE_URL”, “TAVILY_API_KEY”,
    “ALIYUN_API_KEY”, “ALIYUN_BASE_URL”,

    # 模型配置
    “ANALYZER_API_KEY”, “ANALYZER_BASE_URL”, “ANALYZER_MODEL”,
    “WRITER_API_KEY”, “WRITER_BASE_URL”, “WRITER_MODEL”,
    “SEARCHER_API_KEY”, “SEARCHER_BASE_URL”, “SEARCHER_MODEL”,
    “IMAGE_API_KEY”, “IMAGE_BASE_URL”, “IMAGE_GEN_MODEL”,

    # Reddit配置
    “REDDIT_CLIENT_ID”, “REDDIT_CLIENT_SECRET”, “REDDIT_USER_AGENT”,

    # 系统配置
    “MAX_REDDIT_COMMENTS”, “MAX_GENERATED_COMMENTS”,

    # Prompt配置
    “NEWS_ANALYSIS_PROMPT”, “COMMENT_GENERATION_PROMPT”,

    # 常量类（用于向后兼容）
    “CommentStyle”, “ImageStyle”, “CringeScoreWeights”, “LengthLimits”,
    “TimeoutConstants”, “PathConstants”, “QuantityLimits”, “QualityScoreRanges”,
    “ErrorCodes”, “RegexPatterns”, “RedditConstants”, “ImageGenerationConstants”,
    “OutputFormats”,
]
