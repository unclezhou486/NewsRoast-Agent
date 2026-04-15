"""
神评论风格化生成模块
实现: .claude/skills/3_god_comment_generator.md 中的神评论生成专家要求

核心功能:
1. 五种风格平行生成: 引战观点、一针见血的总结、抖机灵的玩笑、发人深省的提问、情感共鸣
2. Reddit 语态建模: 使用自然口语、Reddit 特有表达模式、英文缩写、社区句式结构
3. 去 AI 腔技术: 避免书面语和 AI 套话，模仿真实用户打字习惯

创作约束:
- 每条评论 1-3 句话，短小精悍，冒犯感或幽默感十足
- 禁止超过 500 字符，禁止使用 emoji
- 必须标注风格标识、目标受众、情绪基调、互动设计
"""

import logging
from typing import List, Dict, Any
from openai import OpenAI

from config.settings import settings
from config.models import get_model_config
from config.constants import LengthLimits, QuantityLimits, TimeoutConstants

from utils.error_handling import handle_exceptions, log_execution_time, ModelGenerationError

from skills.loader import get_skill_loader
from skills.prompt_builder import SkillPromptBuilder

logger = logging.getLogger(__name__)

# 固定的输出格式指令（不依赖技能文件，保持稳定）
_OUTPUT_FORMAT = """
## 输出格式
必须严格按照以下格式输出，每条评论标注完整元数据：

【引战观点】
**风格标识**: 引战观点
**目标受众**: [具体群体]
**情绪基调**: [具体情绪]
**互动设计**: [预期互动效果]
**评论内容**: [1-3句话的评论]

【一针见血的总结】
**风格标识**: 一针见血的总结
**目标受众**: [具体群体]
**情绪基调**: [具体情绪]
**互动设计**: [预期互动效果]
**评论内容**: [1-3句话的评论]

【抖机灵的玩笑】
**风格标识**: 抖机灵的玩笑
**目标受众**: [具体群体]
**情绪基调**: [具体情绪]
**互动设计**: [预期互动效果]
**评论内容**: [1-3句话的评论]

【发人深省的提问】
**风格标识**: 发人深省的提问
**目标受众**: [具体群体]
**情绪基调**: [具体情绪]
**互动设计**: [预期互动效果]
**评论内容**: [1-3句话的评论]

【情感共鸣】
**风格标识**: 情感共鸣
**目标受众**: [具体群体]
**情绪基调**: [具体情绪]
**互动设计**: [预期互动效果]
**评论内容**: [1-3句话的评论]

## 重要提醒
1. 严禁使用 AI 套话，必须模仿真实 Reddit 用户的自然口语
2. 每条评论严格控制在 1-3 句话，冒犯感或幽默感十足
3. 使用 Reddit 特有表达模式，如 "As someone who..."、"Let's be real..."、"Not gonna lie..."
4. 禁止超过 500 字符，禁止使用 emoji
"""


class CommentGenerator:
    def __init__(self):
        writer_config = get_model_config("writer")

        self.client = OpenAI(
            api_key=settings.modelscope_api_key,
            base_url=settings.modelscope_base_url,
        )
        self.model = writer_config.model_id
        self.timeout = TimeoutConstants.HTTP_REQUEST_TIMEOUT
        self.max_reference_comments = 5
        self.max_comment_length = LengthLimits.COMMENT_MAX_LENGTH

        # 加载技能文件
        self.god_comment_skill = None
        try:
            self.god_comment_skill = get_skill_loader().load_skill("god_comment_generator")
        except Exception as e:
            logger.warning(f"加载技能文件失败: {e}，将使用默认生成框架")

        logger.debug(f"CommentGenerator 初始化完成，使用模型: {self.model}")

    def _build_prompt(self, analysis: str, reference_text: str) -> str:
        """使用 SkillPromptBuilder 构建评论生成提示词。"""
        task_block = (
            "## 任务要求\n"
            "基于以下新闻分析和参考评论，生成 5 条不同风格的评论：\n\n"
            "### 新闻分析\n{analysis}\n\n"
            "### 参考评论\n{reference_text}\n"
            + _OUTPUT_FORMAT
        )
        fallback = (
            "你是神评论生成专家。基于以下材料生成 5 条 Reddit 风格的神评论：\n\n"
            "{analysis}\n\n{reference_text}"
        )
        builder = SkillPromptBuilder(
            skill=self.god_comment_skill,
            role=(
                "你是一个擅长写神评论的社交媒体段子手，精通讽刺、幽默和引发共鸣的技巧。"
                "你的任务不是生成 'AI 评论'，而是创造出能在 Reddit 上获得 500+ 赞、"
                "50+ 回复的病毒内容。"
            ),
            sections=[
                ("五种核心风格详解", "## 核心风格详解\n{content}"),
                ("Reddit语态",       "## Reddit 语态建模\n{content}"),
                ("创意生成框架",     "## 创意生成框架\n{content}"),
            ],
            task_block=task_block,
            fallback=fallback,
            title="神评论生成专家任务",
        )
        return builder.build(
            analysis=analysis[: LengthLimits.NEWS_TEXT_MAX_LENGTH],
            reference_text=reference_text,
        )

    @handle_exceptions(default_return="生成评论失败")
    @log_execution_time
    def generate_comments(self, analysis: Any, reference_comments: List[Dict[str, Any]]) -> str:
        """生成神评论。"""
        # 构建参考评论字符串
        reference_text = ""
        if reference_comments and isinstance(reference_comments, list):
            valid = [c for c in reference_comments if c and isinstance(c, dict)]
            if valid:
                reference_text = "以下是一些 Reddit 上的高赞评论作为灵感参考：\n"
                for i, comment in enumerate(valid[: self.max_reference_comments]):
                    text = comment.get("text", "（无评论内容）")
                    reference_text += f"{i+1}. {text}\n"

        prompt = self._build_prompt(str(analysis), reference_text)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是神评论生成专家，精通 Reddit 文化生态、多模态解构和犀利文字风格。"
                            "你的产出是经过战略设计的社交媒体内容产品，每一句话都以病毒传播、"
                            "高互动、情感引爆为目标。你天然排斥任何 AI 套话、中立客观的平庸表述，"
                            "语言必须像是一个浸淫 Reddit 多年的真实用户。"
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,
                timeout=self.timeout,
            )

            if response and response.choices:
                result = response.choices[0].message.content
                logger.info(f"成功生成评论，长度: {len(result)} 字符")
                return result
            else:
                raise ModelGenerationError(
                    message="API 未返回有效内容",
                    model_name=self.model,
                    prompt_length=len(prompt),
                )

        except Exception as e:
            logger.exception(f"生成评论失败: {e}")
            raise ModelGenerationError(
                message=f"生成评论失败: {str(e)}",
                model_name=self.model,
                prompt_length=len(prompt),
            )
