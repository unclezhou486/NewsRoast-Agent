"""
异步视觉梗图生成模块
实现: .claude/skills/4_visual_prompt_designer.md 中的视觉提示设计专家要求

核心功能:
1. 视觉潜力评估：从神评论中挑选最具视觉潜力的条目
2. 视觉隐喻转化：将抽象矛盾映射到具体图像（权力不平等→大小对比、虚伪→两面脸）
3. AI 绘画提示词工程：生成结构完整的视觉 Prompt

视觉 Prompt 结构:
[主体描述] + [关键动作] + [环境背景] + [视觉风格] + [技术参数] + [情感导向]

技术方案:
- 异步轮询架构: 使用 X-ModelScope-Async-Mode: true 提交任务，通过 /tasks/{task_id} 轮询
- 降级策略: 图像生成失败时返回 None，不中断主流程
"""

import logging
import re
import time
import requests
from typing import Optional
from openai import OpenAI

from config.settings import settings
from config.models import get_model_config
from config.constants import TimeoutConstants, ImageGenerationConstants

from models.data_models import GeneratedComment, NewsAnalysis

from utils.error_handling import handle_exceptions, log_execution_time

from skills.loader import get_skill_loader
from skills.prompt_builder import SkillPromptBuilder

logger = logging.getLogger(__name__)

# 备用提示词（当技能加载或 LLM 生成失败时使用）
_FALLBACK_PROMPT = (
    "A satirical scene about {keywords}, {style}, cinematic lighting, "
    "ultra detailed, 4k resolution, vibrant colors, sharp focus, satirical commentary."
)

_STYLE_MAP = {
    "引战观点":      "corporate advertisement style",
    "一针见血的总结": "political cartoon style",
    "抖机灵的玩笑":  "internet meme style",
    "发人深省的提问": "editorial illustration style",
    "情感共鸣":      "tech aesthetic style",
}

_REQUIRED_KEYWORDS = ["detailed", "4k", "cinematic", "satirical"]
_VISUAL_DESCRIPTORS = [
    "standing", "sitting", "holding", "wearing", "with", "in", "on",
    "against", "facing", "looking", "surrounded",
]


class ImageGenerator:
    def __init__(self):
        image_gen_config = get_model_config("image_gen")
        llm_config = get_model_config("searcher")  # DeepSeek-V3.2 用于视觉提示词生成

        api_key = settings.modelscope_api_key
        base_url = settings.modelscope_base_url

        self.llm_client = OpenAI(api_key=api_key, base_url=base_url)
        self.llm_model = llm_config.model_id

        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self.image_gen_model = image_gen_config.model_id

        self.timeout = TimeoutConstants.HTTP_REQUEST_TIMEOUT
        self.max_retry_count = TimeoutConstants.MAX_RETRY_COUNT
        self.polling_interval = TimeoutConstants.IMAGE_GENERATION_POLLING_INTERVAL
        self.max_analysis_length = 500
        self.min_prompt_length = 50

        self.async_mode_header = ImageGenerationConstants.ASYNC_MODE_HEADER
        self.async_mode_value = ImageGenerationConstants.ASYNC_MODE_VALUE

        # 加载技能文件
        self.visual_designer_skill = None
        try:
            self.visual_designer_skill = get_skill_loader().load_skill("4_visual_prompt_designer")
        except Exception as e:
            logger.warning(f"加载技能文件失败: {e}，将使用默认视觉设计框架")

    @handle_exceptions(default_return=None)
    @log_execution_time
    def generate_image(self, comment: GeneratedComment, analysis: NewsAnalysis) -> Optional[str]:
        """为评论生成匹配图片，返回图片 URL 或 None。"""
        prompt = self._generate_image_prompt(comment, analysis)
        logger.info(f"生成的画图 Prompt: {prompt[:100]}...")

        try:
            response = requests.post(
                f"{self.base_url}/images/generations",
                headers={**self.headers, self.async_mode_header: self.async_mode_value},
                json={"model": self.image_gen_model, "prompt": prompt},
                timeout=self.timeout,
            )
            response.raise_for_status()

            task_id = response.json().get("task_id")
            if not task_id:
                logger.error("API 响应中缺少 task_id 字段")
                return None

            for i in range(self.max_retry_count):
                result = requests.get(
                    f"{self.base_url}/tasks/{task_id}",
                    headers={**self.headers, "X-ModelScope-Task-Type": "image_generation"},
                    timeout=self.timeout,
                )
                result.raise_for_status()

                data = result.json()
                task_status = data.get("task_status")
                logger.debug(f"任务状态: {task_status} (第{i+1}次轮询)")

                if task_status == "SUCCEED":
                    output_images = data.get("output_images", [])
                    if output_images:
                        logger.info("图片生成成功")
                        return output_images[0]
                    logger.warning("任务成功但未返回图片")
                    return None
                elif task_status == "FAILED":
                    logger.error("图片生成任务失败")
                    return None

                time.sleep(self.polling_interval)

            logger.error("图片生成任务超时")
            return None

        except requests.RequestException as e:
            logger.exception(f"API 请求失败: {e}")
            return None

    def _build_visual_prompt_request(self, comment: GeneratedComment, analysis: NewsAnalysis) -> str:
        """使用 SkillPromptBuilder 构建视觉提示词生成请求。"""
        builder = SkillPromptBuilder(
            skill=self.visual_designer_skill,
            role=(
                "你是 AI 绘画的视觉叙事专家，擅长将文字梗转化为生动、讽刺、传播力强的视觉图像。"
                "你的目标是设计能在 3 秒内传达核心矛盾、引发情感共鸣的梗图视觉概念。"
            ),
            sections=[
                ("视觉叙事原则",       "## 视觉叙事原则\n{content}"),
                ("AI绘画提示词工程",   "## AI绘画提示词工程\n{content}"),
                ("视觉风格矩阵",       "## 视觉风格矩阵\n{content}"),
                ("评论到视觉的转化框架", "## 转化框架\n{content}"),
            ],
            task_block=(
                "## 输入材料\n"
                "### 新闻背景\n{news_text}\n\n"
                "### 神评论\n{comment_text}\n\n"
                "### 评论风格分析\n"
                "- 风格: {style}\n"
                "- 目标受众: {target_audience}\n"
                "- 情绪基调: {emotion_tone}\n\n"
                "## 输出要求\n"
                "1. 输出纯英文的完整 AI 绘画提示词（自然流畅的一段话）\n"
                "2. 必须包含: detailed, 4k, satirical, cinematic lighting\n"
                "3. 禁止使用编号标记组件\n"
                "4. 不要添加任何解释，只输出提示词本身\n"
            ),
            fallback=(
                "Generate a satirical AI image prompt for this comment: {comment_text}\n\n"
                "News context: {news_text}\n\n"
                "Requirements: include detailed, 4k, satirical, cinematic lighting. "
                "Output only the prompt, no explanations."
            ),
            title="视觉叙事与梗图设计专家任务",
        )
        return builder.build(
            news_text=analysis.text_content[: self.max_analysis_length],
            comment_text=comment.text,
            style=comment.style,
            target_audience=comment.target_audience,
            emotion_tone=comment.emotion_tone,
        )

    @handle_exceptions(default_return="")
    @log_execution_time
    def _generate_image_prompt(self, comment: GeneratedComment, analysis: NewsAnalysis) -> str:
        """根据评论生成专业的 AI 绘画提示词。"""
        try:
            request_prompt = self._build_visual_prompt_request(comment, analysis)

            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": request_prompt}],
                temperature=0.7,
                stream=False,
                timeout=self.timeout,
            )

            generated = None
            if response and response.choices and response.choices[0].message.content:
                generated = response.choices[0].message.content.strip()

            if not generated:
                logger.warning("LLM 未返回有效 Prompt，使用备用策略")
                return self._get_fallback_prompt(comment)

            if self._validate_prompt(generated):
                return generated
            else:
                logger.warning("生成的提示词质量较低，使用备用提示词")
                return self._get_fallback_prompt(comment)

        except Exception as e:
            logger.exception(f"Prompt 生成失败: {e}")
            return self._get_fallback_prompt(comment)

    def _validate_prompt(self, prompt: str) -> bool:
        """验证提示词是否满足质量要求。"""
        if len(prompt) < self.min_prompt_length:
            return False
        missing = [kw for kw in _REQUIRED_KEYWORDS if kw not in prompt.lower()]
        if missing:
            logger.debug(f"Prompt 缺少关键词: {missing}")
            return False
        if not any(d in prompt.lower() for d in _VISUAL_DESCRIPTORS):
            logger.debug("Prompt 缺少视觉描述元素")
            return False
        return True

    def _get_fallback_prompt(self, comment: GeneratedComment) -> str:
        """生成备用提示词。"""
        logger.warning("使用备用提示词生成策略")
        keywords = re.findall(r"\b\w+\b", comment.text[:100])
        main_keywords = " ".join(keywords[:3]) if keywords else "politics and money"
        style = _STYLE_MAP.get(str(comment.style.value), "corporate advertisement style")
        return _FALLBACK_PROMPT.format(keywords=main_keywords, style=style)
