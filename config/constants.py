"""
NewsRoast-Agent 系统常量

统一管理项目中的所有魔法数字、枚举值和固定配置。
枚举类型（CommentStyle、ImageStyle）的单一定义位于 models/data_models.py，
此处通过重新导出保持向后兼容。
"""

# 枚举单一来源：models/data_models.py
from models.data_models import CommentStyle, ImageStyle

__all__ = ["CommentStyle", "ImageStyle"]


# 📊 槽点评分常量
# ==========================================

class CringeScoreWeights:
    """槽点评分权重"""
    ABSURDITY_WEIGHT = 0.6  # 荒谬度权重
    RESONANCE_WEIGHT = 0.4  # 共鸣度权重
    MAX_SCORE = 10  # 最大单维度评分
    MIN_SCORE = 1   # 最小单维度评分


# ==========================================
# 📏 长度限制常量
# ==========================================

class LengthLimits:
    """长度限制"""
    # 评论文本限制
    COMMENT_MIN_LENGTH = 10
    COMMENT_MAX_LENGTH = 500

    # 新闻文本限制
    NEWS_TEXT_MAX_LENGTH = 3000

    # 搜索关键词限制
    SEARCH_QUERY_MAX_KEYWORDS = 5
    SEARCH_KEYWORD_MAX_LENGTH = 50

    # Prompt长度限制
    PROMPT_MIN_LENGTH = 50

    # 图像分析限制
    MAX_IMAGES_TO_ANALYZE = 2


# ==========================================
# ⏱️ 超时与重试常量
# ==========================================

class TimeoutConstants:
    """超时与重试配置"""
    # HTTP请求超时
    HTTP_REQUEST_TIMEOUT = 30
    HTTP_IMAGE_DOWNLOAD_TIMEOUT = 10

    # LLM 推理超时（多模态大模型单次调用可能需要 60-120 秒）
    LLM_INFERENCE_TIMEOUT = 180

    # 图像生成超时
    IMAGE_GENERATION_TIMEOUT = 120
    IMAGE_GENERATION_POLLING_INTERVAL = 5

    # 重试配置
    MAX_RETRY_COUNT = 30   # 图像生成最大轮询次数 (30次×5秒=150秒)
    RETRY_DELAY_BASE = 1.0  # 指数退避基础延迟


# ==========================================
# 📁 文件与路径常量
# ==========================================

class PathConstants:
    """路径常量"""
    # 技能文件目录
    SKILLS_DIR = ".claude/skills"

    # 技能文件名
    PERCEPTION_EXPERT_SKILL = "1_perception_expert.md"
    REDDIT_NAVIGATOR_SKILL = "2_reddit_navigator.md"
    GOD_COMMENT_GENERATOR_SKILL = "3_god_comment_generator.md"
    VISUAL_PROMPT_DESIGNER_SKILL = "4_visual_prompt_designer.md"

    # 缓存目录
    CACHE_DIR = ".cache"
    IMAGE_CACHE_DIR = ".cache/images"


# ==========================================
# 🔢 数量限制常量
# ==========================================

class QuantityLimits:
    """数量限制"""
    # Reddit评论数量
    MAX_REDDIT_COMMENTS = 10
    MIN_REDDIT_COMMENTS = 3

    # 生成评论数量
    MAX_GENERATED_COMMENTS = 5
    MIN_GENERATED_COMMENTS = 3

    # 图像分析数量
    MAX_IMAGES_TO_ANALYZE = 2

    # 槽点数量
    MAX_CRINGE_POINTS = 5
    MIN_CRINGE_POINTS = 3


# ==========================================
# 🎯 质量评分常量
# ==========================================

class QualityScoreRanges:
    """质量评分范围"""
    # Reddit评论质量评分
    REDDIT_COMMENT_MIN_SCORE = 0
    REDDIT_COMMENT_MAX_SCORE = 100

    # 生成评论质量评分
    GENERATED_COMMENT_MIN_SCORE = 0
    GENERATED_COMMENT_MAX_SCORE = 100

    # 槽点综合评分
    CRINGE_POINT_MIN_SCORE = 0
    CRINGE_POINT_MAX_SCORE = 100


# ==========================================
# 🚨 错误码常量
# ==========================================

class ErrorCodes:
    """错误码"""
    # 成功
    SUCCESS = 0

    # API错误
    API_CONNECTION_ERROR = 1000
    API_RATE_LIMIT_ERROR = 1001
    API_AUTHENTICATION_ERROR = 1002

    # 内容错误
    CONTENT_PARSE_ERROR = 2000
    CONTENT_NOT_FOUND_ERROR = 2001
    CONTENT_VALIDATION_ERROR = 2002

    # 系统错误
    CONFIGURATION_ERROR = 3000
    FILE_SYSTEM_ERROR = 3001
    NETWORK_ERROR = 3002
    SYSTEM_ERROR = 3003

    # 业务错误
    NO_CRINGE_POINTS_FOUND = 4000
    NO_REDDIT_COMMENTS_FOUND = 4001
    COMMENT_GENERATION_FAILED = 4002
    IMAGE_GENERATION_FAILED = 4003


# ==========================================
# 🔤 正则表达式常量
# ==========================================

class RegexPatterns:
    """正则表达式模式"""
    # URL验证
    URL_PATTERN = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.\-?=&%#+]*'

    # 搜索关键词清理
    KEYWORD_CLEAN_PATTERN = r'[^a-zA-Z0-9\s]'

    # AI腔检测
    AI_PHRASE_PATTERN = r'(作为一个人工智能|根据我的训练数据|我认为|需要注意的是)'


# ==========================================
# 🌐 Reddit相关常量
# ==========================================

class RedditConstants:
    """Reddit相关常量"""
    # 用户代理
    USER_AGENT = "News Comment Agent by /u/example_user"

    # 搜索时间范围
    SEARCH_TIME_RANGE = "month"  # month, year, all

    # 搜索深度
    SEARCH_DEPTH = "advanced"  # basic, advanced

    # 最大搜索结果
    MAX_SEARCH_RESULTS = 10


# ==========================================
# 🎨 图像生成常量
# ==========================================

class ImageGenerationConstants:
    """图像生成常量"""
    # 异步模式头
    ASYNC_MODE_HEADER = "X-ModelScope-Async-Mode"
    ASYNC_MODE_VALUE = "true"

    # 图像格式
    IMAGE_FORMAT_PNG = "png"
    IMAGE_FORMAT_JPG = "jpg"

    # 图像质量
    DEFAULT_IMAGE_QUALITY = 85  # 0-100


# ==========================================
# 📝 输出格式常量
# ==========================================

class OutputFormats:
    """输出格式常量"""
    # Markdown分隔符
    MARKDOWN_CODE_BLOCK = "```"

    # 搜索查询前缀
    SEARCH_QUERY_PREFIX = "SEARCH_QUERY:"

    # 槽点前缀
    CRINGE_POINT_HIGH = "**[高潜力]**"
    CRINGE_POINT_MEDIUM = "**[中潜力]**"
    CRINGE_POINT_LOW = "**[低潜力]**"