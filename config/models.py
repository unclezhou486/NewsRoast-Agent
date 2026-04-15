"""
NewsRoast-Agent 模型配置

统一管理所有AI模型的详细配置，包括模型名称、参数、能力和推荐使用场景。
"""

from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum


class ModelCapability(str, Enum):
    """模型能力枚举"""
    VISION = "vision"  # 视觉理解
    TEXT_GENERATION = "text_generation"  # 文本生成
    REASONING = "reasoning"  # 逻辑推理
    HUMOR = "humor"  # 幽默感
    CREATIVITY = "creativity"  # 创造力
    ANALYSIS = "analysis"  # 分析能力


@dataclass
class ModelConfig:
    """模型配置数据类"""
    model_id: str  # 模型唯一标识
    display_name: str  # 显示名称
    capabilities: list[ModelCapability]  # 模型能力
    recommended_temperature: float  # 推荐温度
    max_tokens: int  # 最大输出长度
    context_length: int  # 上下文长度
    cost_per_1k_tokens: float  # 每1k token成本（估算）
    recommended_scenarios: list[str]  # 推荐使用场景


# ==========================================
# 🤖 视觉分析模型 (需要强大的视觉理解能力)
# ==========================================

QWEN_VISION_MODEL = ModelConfig(
    model_id="Qwen/Qwen3.5-35B-A3B",
    display_name="通义千问3.5-35B-A3B (视觉增强版)",
    capabilities=[
        ModelCapability.VISION,
        ModelCapability.ANALYSIS,
        ModelCapability.REASONING,
    ],
    recommended_temperature=0.2,
    max_tokens=4096,
    context_length=128000,
    cost_per_1k_tokens=0.0,  # 根据实际计费调整
    recommended_scenarios=[
        "新闻图文联合分析",
        "视觉槽点识别",
        "多模态解构",
    ]
)


# ==========================================
# ✍️ 评论生成模型 (需要极强的网感和幽默感)
# ==========================================

MINIMAX_M2_5_MODEL = ModelConfig(
    model_id="MiniMax/MiniMax-M2.5",
    display_name="MiniMax M2.5 (旗舰模型)",
    capabilities=[
        ModelCapability.TEXT_GENERATION,
        ModelCapability.HUMOR,
        ModelCapability.CREATIVITY,
    ],
    recommended_temperature=0.7,
    max_tokens=1024,
    context_length=128000,
    cost_per_1k_tokens=0.0,  # 根据实际计费调整
    recommended_scenarios=[
        "神评论生成",
        "社交媒体内容创作",
        "幽默段子生成",
    ]
)


# ==========================================
# 🔍 搜索优化模型 (需要理解关键词提取)
# ==========================================

DEEPSEEK_V3_2_MODEL = ModelConfig(
    model_id="deepseek-ai/DeepSeek-V3.2",
    display_name="DeepSeek V3.2",
    capabilities=[
        ModelCapability.ANALYSIS,
        ModelCapability.REASONING,
    ],
    recommended_temperature=0.3,
    max_tokens=512,
    context_length=128000,
    cost_per_1k_tokens=0.0,  # 根据实际计费调整
    recommended_scenarios=[
        "搜索词优化",
        "关键词提取",
        "语义分析",
    ]
)


# ==========================================
# 🎨 图像生成模型
# ==========================================

QWEN_IMAGE_MODEL = ModelConfig(
    model_id="Qwen/Qwen-Image-2512",
    display_name="通义万相 2512",
    capabilities=[
        ModelCapability.CREATIVITY,
        ModelCapability.VISION,
    ],
    recommended_temperature=0.8,
    max_tokens=1024,  # 图像生成提示词长度
    context_length=4096,
    cost_per_1k_tokens=0.0,  # 根据实际计费调整
    recommended_scenarios=[
        "梗图生成",
        "视觉讽刺创作",
        "社交媒体图像设计",
    ]
)


# ==========================================
# 🧠 视觉提示设计模型
# ==========================================

QWEN_3_32B_MODEL = ModelConfig(
    model_id="Qwen/Qwen3-32B",
    display_name="通义千问3-32B",
    capabilities=[
        ModelCapability.CREATIVITY,
        ModelCapability.ANALYSIS,
        ModelCapability.TEXT_GENERATION,
    ],
    recommended_temperature=0.6,
    max_tokens=2048,
    context_length=128000,
    cost_per_1k_tokens=0.0,  # 根据实际计费调整
    recommended_scenarios=[
        "视觉提示设计",
        "创意概念生成",
        "叙事构建",
    ]
)


# ==========================================
# 🎯 模型配置映射
# ==========================================

MODEL_CONFIG = {
    "analyzer": QWEN_VISION_MODEL,
    "writer": MINIMAX_M2_5_MODEL,
    "searcher": DEEPSEEK_V3_2_MODEL,
    "image_gen": QWEN_IMAGE_MODEL,
    "visual_designer": QWEN_3_32B_MODEL,
}


def get_model_config(model_type: str) -> ModelConfig:
    """获取指定类型的模型配置"""
    if model_type not in MODEL_CONFIG:
        raise ValueError(f"未知的模型类型: {model_type}")
    return MODEL_CONFIG[model_type]


def get_model_id(model_type: str) -> str:
    """获取指定类型模型的ID"""
    return get_model_config(model_type).model_id