"""
多模态新闻分析模块
实现: .claude/skills/1_perception_expert.md 中的多模态感知专家要求

核心功能:
1. 视觉-文本反差分析框架: 表情/肢体语言解码、背景细节挖掘、色彩构图分析、图文一致性检查
2. 反直觉槽点挖掘策略: 官方叙事vs现实暗示、权力关系暴露、时代错位感、身份与行为反差
3. 社交媒体传播潜力评估: 梗图化可能性、情绪引爆点、争议性话题识别

工作流程:
- 第一层: 事实提取 (时间、地点、人物、事件、结果)
- 第二层: 多模态解构 (视觉元素对文字的强化/削弱作用)
- 第三层: 槽点识别 (按荒谬度和共鸣度排序)

输出规范: 结构化Markdown格式，包含SEARCH_QUERY关键词提取
"""

import logging
import requests
import base64
from typing import Dict, List, Optional, Tuple, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from openai import OpenAI

from config.settings import settings
from config.models import get_model_config
from config.constants import LengthLimits, TimeoutConstants

from models.data_models import NewsAnalysis

from utils.error_handling import (
    handle_exceptions, log_execution_time,
    APIConnectionError, ContentParseError, ModelGenerationError,
)

from skills.loader import get_skill_loader
from skills.prompt_builder import SkillPromptBuilder

logger = logging.getLogger(__name__)


class NewsAnalyzer:
    def __init__(self):
        analyzer_config = get_model_config("analyzer")

        self.client = OpenAI(
            api_key=settings.modelscope_api_key,
            base_url=settings.modelscope_base_url,
        )
        self.model = analyzer_config.model_id
        self.timeout = TimeoutConstants.HTTP_REQUEST_TIMEOUT
        self.llm_timeout = TimeoutConstants.LLM_INFERENCE_TIMEOUT
        self.max_text_length = LengthLimits.NEWS_TEXT_MAX_LENGTH
        self.max_images_to_analyze = LengthLimits.MAX_IMAGES_TO_ANALYZE

        # 加载技能文件
        self.perception_skill = None
        try:
            self.perception_skill = get_skill_loader().load_skill("perception_expert")
        except Exception as e:
            logger.warning(f"加载技能文件失败: {e}，将使用默认分析框架")

    @handle_exceptions(default_return=(None, None))
    @log_execution_time
    def image_to_base64(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """将图片 URL 转换为 base64 编码，返回 (data, fmt) 或 (None, None)。"""
        try:
            res = requests.get(url, timeout=TimeoutConstants.HTTP_IMAGE_DOWNLOAD_TIMEOUT)
            content_type = res.headers.get("Content-Type", "")
            if "image" not in content_type:
                return None, None
            img_base64 = base64.b64encode(res.content).decode("utf-8")
            fmt = content_type.split("/")[-1]
            return img_base64, fmt
        except requests.RequestException as e:
            raise APIConnectionError(
                message=f"图片下载失败: {str(e)}", api_name="image_download", url=url
            )

    @handle_exceptions(default_return={"text": "", "images": []})
    @log_execution_time
    def fetch_news_data(self, url: str) -> Dict[str, Any]:
        """抓取新闻文本和图片 URL。"""
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=self.timeout)
        soup = BeautifulSoup(response.content, "html.parser")

        paragraphs = [p.get_text() for p in soup.find_all("p")]
        text_content = "\n".join(paragraphs)[: self.max_text_length]

        image_urls: List[str] = []
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if src and any(ext in src.lower() for ext in [".jpg", ".png", ".jpeg", ".webp", ".gif"]):
                if "avatar" not in src.lower() and "logo" not in src.lower():
                    image_urls.append(urljoin(url, src))
                    if len(image_urls) >= self.max_images_to_analyze:
                        break

        return {"text": text_content, "images": image_urls}

    def _build_prompt(self, text: str) -> str:
        """使用 SkillPromptBuilder 构建分析提示词。"""
        builder = SkillPromptBuilder(
            skill=self.perception_skill,
            title="多模态感知专家任务",
            role=(
                "你是新闻多模态解构专家，擅长从文字和图像的交互中识别隐藏的冲突、"
                "讽刺点和反直觉槽点。你的目标不是简单描述内容，而是揭露表面叙事下的深层矛盾。"
            ),
            sections=[
                ("核心分析方法",   "## 核心分析方法\n{content}"),
                ("输出规范",       "## 输出规范\n{content}"),
                ("常见陷阱与规避", "## 常见陷阱与规避\n{content}"),
            ],
            task_block=(
                "## 新闻内容\n{news_text}\n\n"
                "请严格按照输出规范格式，用 Markdown 撰写分析报告。"
            ),
            fallback="# 新闻分析\n\n请分析以下新闻，识别槽点，输出 SEARCH_QUERY。\n\n{news_text}",
        )
        return builder.build(news_text=text[: self.max_text_length])

    @handle_exceptions(default_return="分析失败")
    @log_execution_time
    def analyze_content(self, data: Dict[str, Any]) -> str:
        """多模态分析：文字 + 图片。"""
        text: str = data["text"]
        images: List[str] = data["images"]

        prompt = self._build_prompt(text)

        content_list: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]

        for img_url in images[: self.max_images_to_analyze]:
            img_base64, fmt = self.image_to_base64(img_url)
            if img_base64:
                content_list.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/{fmt};base64,{img_base64}"},
                })

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是新闻多模态解构专家，精通视觉-文本反差分析、反直觉槽点挖掘和"
                            "社交媒体传播潜力评估。你的目标不是简单描述内容，而是揭露表面叙事"
                            "下的深层矛盾，为社交媒体段子手提供弹药。"
                        ),
                    },
                    {"role": "user", "content": content_list},
                ],
                temperature=0.3,
                timeout=self.llm_timeout,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise ModelGenerationError(
                message=f"多模态分析失败: {str(e)}",
                model_name=self.model,
                prompt_length=len(str(content_list)),
            )

    @handle_exceptions(default_return="无法读取内容")
    @log_execution_time
    def process_news(self, url: str) -> str:
        """处理新闻 URL 的完整流程。"""
        data = self.fetch_news_data(url)
        if not data["text"]:
            raise ContentParseError(message="新闻内容为空", content_type="text", source=url)
        return self.analyze_content(data)
