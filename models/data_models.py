"""
NewsRoast-Agent 统一数据模型

定义项目核心数据结构和类型，确保模块间数据传递的类型安全性和一致性。
基于 Pydantic 提供数据验证和序列化支持。
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any, Tuple, Union
from datetime import datetime
from enum import Enum


class CommentStyle(str, Enum):
    """评论风格枚举，对应 .claude/skills/3_god_comment_generator.md 中定义的五种风格"""
    CONTROVERSIAL = "引战观点"
    RAZOR_SHARP = "一针见血的总结"
    WITTY_JOKE = "抖机灵的玩笑"
    THOUGHT_PROVOKING = "发人深省的提问"
    EMOTIONAL_RESONANCE = "情感共鸣"


class ImageStyle(str, Enum):
    """图像风格枚举，对应 .claude/skills/4_visual_prompt_designer.md 中定义的视觉风格"""
    CORPORATE_AD = "企业宣传画"
    POLITICAL_CARTOON = "政治漫画"
    INTERNET_MEME = "网络梗图"
    TECH_AESTHETIC = "科技美学"
    EDITORIAL_ILLUSTRATION = "社论插图"


class CringePoint(BaseModel):
    """反直觉槽点数据模型"""
    description: str
    source: str  # "visual" 或 "text"
    source_detail: str  # 具体来源描述，如 "图片中CEO的表情" 或 "第二段第三句"
    absurdity_score: int = Field(ge=1, le=10)  # 荒谬度评分 1-10
    resonance_score: int = Field(ge=1, le=10)  # 共鸣度评分 1-10
    visual_potential: Optional[str] = None  # 可视化潜力描述


class NewsAnalysis(BaseModel):
    """新闻分析结果数据模型
    对应 .claude/skills/1_perception_expert.md 输出格式
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # 基础信息
    url: str
    analysis_timestamp: datetime = Field(default_factory=datetime.now)

    # 内容提取
    text_content: str
    image_urls: List[str]
    base64_images: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Base64编码的图片列表，格式: [{'base64': '...', 'format': 'png/jpg'}]"
    )

    # 分析结果
    core_event: str = Field(description="一句话概括核心事件")
    visual_analysis: List[str] = Field(
        default_factory=list,
        description="视觉分析发现列表"
    )
    text_analysis: List[str] = Field(
        default_factory=list,
        description="文本分析发现列表"
    )
    contrast_points: List[str] = Field(
        default_factory=list,
        description="图文反差亮点列表"
    )

    # 槽点分析（支持CringePoint对象或原始字典）
    cringe_points: List[Any] = Field(
        default_factory=list,
        description="反直觉槽点，按引爆潜力排序"
    )

    # 搜索关键词
    search_query: str = Field(
        description="Reddit搜索关键词，格式: 'keyword1 keyword2 keyword3 keyword4 keyword5'"
    )

    # 原始分析输出
    raw_analysis_markdown: Optional[str] = Field(
        default=None,
        description="原始分析Markdown输出，用于调试和审计"
    )


class RedditComment(BaseModel):
    """Reddit评论数据模型
    对应 .claude/skills/2_reddit_navigator.md 输出格式
    """
    # 基础信息
    text: str
    source_url: str
    timestamp: Optional[datetime] = None

    # 互动数据
    upvotes: int = 0
    downvotes: int = 0
    # score 支持字符串（如 "1.2k"）或整数
    score: Union[int, str] = 0
    replies_count: int = 0

    # 质量评估
    quality_score: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="质量综合评分 0-100"
    )

    # 分类信息
    style_category: Optional[str] = Field(
        default=None,
        description="风格分类，如 'expert_perspective', 'direct_callout'"
    )
    emotion_tone: Optional[str] = Field(
        default=None,
        description="情绪基调，如 'critical but informed', 'skeptical'"
    )

    # 奖项标识
    awards: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Reddit奖项信息"
    )

    # 元数据
    is_op_reply: bool = False
    key_phrases: List[str] = Field(default_factory=list)
    subreddit: Optional[str] = None


class GeneratedComment(BaseModel):
    """生成的评论数据模型
    对应 .claude/skills/3_god_comment_generator.md 输出格式
    """
    # 核心内容
    text: str = Field(
        description="评论文本，1-3句话，不超过500字符",
        max_length=500
    )

    # 风格分类
    style: CommentStyle

    # 目标设定
    target_audience: str = Field(
        description="目标受众，如 'r/technology用户', '普通消费者'"
    )
    emotion_tone: str = Field(
        description="情绪基调，如 '讽刺', '愤怒', '幽默', '失望'"
    )
    interaction_design: str = Field(
        description="互动设计，如 '引发辩论', '获得高赞', '被引用分享'"
    )

    # 创意信息
    cultural_references: List[str] = Field(
        default_factory=list,
        description="文化引用，如梗、流行文化参考"
    )

    # 质量评估
    quality_score: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="生成质量评分 0-100"
    )


class ImagePrompt(BaseModel):
    """图像提示数据模型
    对应 .claude/skills/4_visual_prompt_designer.md 输出格式
    """
    # 核心概念
    visual_concept: str = Field(
        description="视觉概念描述，一句话解释图像传达的核心讽刺"
    )

    # 提示词
    prompt: str = Field(
        description="完整AI绘画提示词，包含所有必要组件"
    )

    # 风格设定
    style: ImageStyle
    artist_references: List[str] = Field(
        default_factory=list,
        description="艺术家或风格参考"
    )

    # 技术参数
    technical_params: Dict[str, Any] = Field(
        default_factory=lambda: {
            "composition": "wide shot, rule of thirds",
            "lighting": "dramatic lighting",
            "colors": "vibrant colors, high contrast",
            "details": "highly detailed, 4k resolution"
        }
    )

    # 情感导向
    target_emotion: str = Field(
        description="希望观众感受到的主要情绪"
    )

    # 关联信息
    based_on_comment: GeneratedComment
    based_on_news: NewsAnalysis

    # 预期效果
    expected_understanding_time: str = Field(
        default="3秒内",
        description="预期理解时间"
    )
    expected_viral_potential: str = Field(
        default="中等",
        description="病毒传播潜力评估"
    )

    # 元数据
    generation_timestamp: datetime = Field(default_factory=datetime.now)


class PipelineResult(BaseModel):
    """完整流水线结果数据模型"""
    news_analysis: NewsAnalysis
    reddit_comments: List[RedditComment]
    generated_comments: List[GeneratedComment]
    image_prompt: Optional[ImagePrompt] = None

    # 执行元数据
    execution_time: float = Field(description="总执行时间（秒）")
    success: bool = True
    errors: List[str] = Field(default_factory=list)

    # 时间戳
    start_timestamp: datetime
    end_timestamp: Optional[datetime] = None

    def calculate_execution_time(self) -> float:
        """计算执行时间"""
        if self.end_timestamp and self.start_timestamp:
            return (self.end_timestamp - self.start_timestamp).total_seconds()
        return self.execution_time


# 辅助函数
def create_search_query(keywords: List[str], max_keywords: int = 5) -> str:
    """创建标准化搜索查询字符串"""
    # 清理关键词：移除特殊字符，限制长度
    cleaned_keywords = []
    for kw in keywords:
        if len(cleaned_keywords) >= max_keywords:
            break
        # 基本清理
        clean_kw = kw.strip().lower()
        if clean_kw and len(clean_kw) <= 50:
            cleaned_keywords.append(clean_kw)

    return " ".join(cleaned_keywords)


def calculate_cringe_point_score(cringe_point: CringePoint) -> float:
    """计算槽点综合得分（用于排序）"""
    # 加权计算：荒谬度权重0.6，共鸣度权重0.4
    return (cringe_point.absurdity_score * 0.6 + cringe_point.resonance_score * 0.4) * 10


def validate_comment_text(text: str) -> Tuple[bool, Optional[str]]:
    """验证评论文本是否符合要求"""
    if len(text) < 10:
        return False, "评论太短（最少10字符）"
    if len(text) > 500:
        return False, "评论太长（最多500字符）"
    if "作为一个人工智能" in text or "根据我的训练数据" in text:
        return False, "检测到AI腔表达"
    return True, None


# 向后兼容别名：ImagePrompt 原名为 ImageGenerationRequest
class ImageGenerationRequest(BaseModel):
    """图像生成请求（向后兼容包装器，等价于 ImagePrompt）"""
    comment: GeneratedComment
    news_analysis: NewsAnalysis
    visual_concept: str = ""
    prompt: str = ""
