"""
流水线智能路由器

在 Stage 1（新闻分析）完成后，调用 LLM 基于分析结果自主决定：
  - 是否执行 Stage 2（Reddit 参考评论检索）
  - 是否执行 Stage 4（视觉 Prompt + 图像生成）

这使 agent 具备动态 skill 选择能力，而非硬编码顺序执行所有阶段。

决策逻辑：
  run_reddit_search  → 有明确 SEARCH_QUERY + 属于国际/科技/商业话题
  run_image_generation → 新闻有图片内容 OR 槽点具有强视觉化潜力
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from openai import OpenAI

from config.models import get_model_config
from config.settings import settings
from config.constants import TimeoutConstants

logger = logging.getLogger(__name__)

# 路由决策 Prompt
_ROUTING_PROMPT = """\
你是一个新闻处理流水线的智能路由器。
基于下方新闻分析摘要，决定是否需要执行后续两个可选阶段。

--- 新闻分析摘要 ---
{analysis_summary}
--- 结束 ---

判断规则：

1. **run_reddit_search**（是否搜索 Reddit 参考评论）
   - True：分析中包含有效的 SEARCH_QUERY 关键词，且话题属于国际、科技、商业、政治等 Reddit 有活跃讨论的领域
   - False：纯本地新闻、无 SEARCH_QUERY、话题过于小众或涉及地方政策

2. **run_image_generation**（是否生成梗图）
   - True：分析中有"视觉分析"内容（说明新闻有图片）或槽点包含强视觉化元素（权力对比、夸张场景、讽刺符号、身份反差）
   - False：纯文字新闻，槽点为抽象概念，缺乏可视化的具体场景

仅返回如下格式的纯 JSON，不要有任何其他文字：
{{"run_reddit_search": true, "run_image_generation": true, "reasoning": "一句话解释路由原因"}}
"""


@dataclass
class RoutingDecision:
    """路由决策结果。"""
    run_reddit_search: bool      # 是否执行 Stage 2
    run_image_generation: bool   # 是否执行 Stage 4
    reasoning: str               # 决策理由

    @classmethod
    def run_all(cls, reason: str = "fallback: 默认执行全部阶段") -> "RoutingDecision":
        """Fallback：全部阶段都跑。"""
        return cls(run_reddit_search=True, run_image_generation=True, reasoning=reason)


class PipelineRouter:
    """
    基于 LLM 的流水线路由器。

    使用 DeepSeek-V3.2（searcher 配置）对 Stage 1 分析结果做轻量决策调用，
    决定是否跳过 Stage 2 和 Stage 4。
    """

    def __init__(self) -> None:
        config = get_model_config("searcher")
        self.model = config.model_id
        self.client = OpenAI(
            api_key=settings.modelscope_api_key,
            base_url=settings.modelscope_base_url,
        )
        self.timeout = TimeoutConstants.LLM_INFERENCE_TIMEOUT

    def decide(self, analysis_text: str) -> RoutingDecision:
        """
        基于 Stage 1 分析文本做路由决策。

        Args:
            analysis_text: NewsAnalyzer.process_news() 返回的 Markdown 分析字符串

        Returns:
            RoutingDecision；若 LLM 调用或解析失败，返回 run_all() fallback
        """
        summary = self._extract_summary(analysis_text)
        prompt = _ROUTING_PROMPT.format(analysis_summary=summary)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200,
                timeout=self.timeout,
            )
            raw = response.choices[0].message.content.strip()
            return self._parse_response(raw)

        except Exception as e:
            logger.warning(f"路由决策 LLM 调用失败，使用 fallback（全部执行）: {e}")
            return RoutingDecision.run_all(reason=f"fallback: LLM 调用失败 ({type(e).__name__})")

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _extract_summary(self, analysis_text: str) -> str:
        """
        从分析文本中提取关键段落作为摘要，控制 token 消耗。
        优先保留：核心事件、槽点列表、SEARCH_QUERY、视觉分析段落首行。
        """
        lines = analysis_text.splitlines()
        kept: list[str] = []
        in_visual = False
        visual_lines = 0

        for line in lines:
            stripped = line.strip()

            # 核心事件段落
            if stripped.startswith("## 核心事件") or stripped.startswith("## 反直觉槽点"):
                kept.append(line)
                in_visual = False
                continue

            # 视觉分析段落（最多保留 5 行）
            if "视觉分析" in stripped and stripped.startswith("###"):
                in_visual = True
                visual_lines = 0
                kept.append(line)
                continue

            if in_visual:
                if stripped.startswith("#"):
                    in_visual = False
                elif visual_lines < 5:
                    kept.append(line)
                    visual_lines += 1
                continue

            # SEARCH_QUERY 行
            if "SEARCH_QUERY:" in stripped:
                kept.append(line)
                continue

            # 槽点条目（- 开头或数字列表）
            if re.match(r"^[-*\d]", stripped) and len(kept) > 0:
                kept.append(line)

        summary = "\n".join(kept).strip()
        # 保底：若提取结果过短，直接取前 800 字符
        if len(summary) < 100:
            summary = analysis_text[:800]
        return summary[:1200]  # 上限 1200 字符

    def _parse_response(self, raw: str) -> RoutingDecision:
        """
        解析 LLM 返回的 JSON。

        支持模型在 JSON 外包裹 ```json ... ``` 代码块的情况。
        """
        # 去掉可能的 markdown 代码块包裹
        clean = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()

        try:
            data = json.loads(clean)
        except json.JSONDecodeError:
            # 尝试提取第一个 {...} 片段
            match = re.search(r"\{.*?\}", clean, re.DOTALL)
            if match:
                data = json.loads(match.group())
            else:
                logger.warning(f"路由响应 JSON 解析失败，使用 fallback。原始内容: {raw[:200]}")
                return RoutingDecision.run_all(reason="fallback: JSON 解析失败")

        return RoutingDecision(
            run_reddit_search=bool(data.get("run_reddit_search", True)),
            run_image_generation=bool(data.get("run_image_generation", True)),
            reasoning=str(data.get("reasoning", "LLM 未提供理由")),
        )
