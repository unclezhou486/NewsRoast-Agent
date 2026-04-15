"""
技能驱动的 Prompt 构建器

将四个模块中重复的 _build_skill_based_prompt 逻辑统一到一处。
每个模块只需声明自己依赖哪些章节和 Prompt 模板，无需重复编写
try/except/fallback 样板代码。

用法
----
from skills.prompt_builder import SkillPromptBuilder

# 声明式构建
builder = SkillPromptBuilder(
    skill=self.perception_skill,
    role="你是新闻多模态解构专家...",
    sections=[
        ("核心分析方法", "## 核心分析方法\n{content}"),
        ("输出规范",    "## 输出规范\n{content}"),
        ("常见陷阱与规避", "## 常见陷阱与规避\n{content}"),
    ],
    task_block="## 新闻内容\n{news_text}\n\n请严格按照输出规范撰写分析报告。",
    fallback="# 新闻分析\n\n{news_text}",
)
prompt = builder.build(news_text=text[:max_len])
"""

from __future__ import annotations

import logging
from string import Formatter
from typing import Optional, List, Tuple

from skills.loader import SkillData

logger = logging.getLogger(__name__)


class SkillPromptBuilder:
    """
    声明式技能 Prompt 构建器。

    Parameters
    ----------
    skill:
        加载好的 SkillData 对象（可为 None，此时直接用 fallback）。
    role:
        任务的角色定位描述，拼在 Prompt 开头。
    sections:
        章节注入列表，每项为 (section_query, template) 二元组。
        - section_query: 传给 SkillData.find_section() 的查询词（支持模糊匹配）
        - template: 该章节的 Prompt 片段，用 {content} 占位符引用章节文本
    task_block:
        任务描述模板，用 Python 格式化字符串，build() 的关键字参数会填入。
    fallback:
        技能加载失败或异常时使用的备用 Prompt，同样支持 build() 的关键字参数。
    title:
        Prompt 第一行的标题（可选）。
    """

    def __init__(
        self,
        skill: Optional[SkillData],
        role: str,
        sections: List[Tuple[str, str]],
        task_block: str,
        fallback: str,
        title: str = "",
    ):
        self.skill = skill
        self.role = role
        self.sections = sections
        self.task_block = task_block
        self.fallback = fallback
        self.title = title

    def build(self, **kwargs) -> str:
        """
        构建最终 Prompt。

        如果 skill 存在且章节提取成功，返回技能增强版 Prompt；
        否则返回 fallback（用 kwargs 填充占位符）。

        Parameters
        ----------
        **kwargs:
            task_block 和 fallback 模板中的占位符值。
        """
        if not self.skill:
            return self._render(self.fallback, **kwargs)

        try:
            parts: list[str] = []

            if self.title:
                parts.append(f"# {self.title}")

            if self.role:
                parts.append(f"## 角色定位\n{self.role}")

            # 注入技能章节
            for section_query, section_template in self.sections:
                content = self.skill.find_section(section_query)
                if content:
                    rendered = section_template.format(content=content)
                    parts.append(rendered)
                else:
                    logger.debug(f"章节 '{section_query}' 未找到，跳过注入")

            # 注入任务块
            parts.append(self._render(self.task_block, **kwargs))

            return "\n\n".join(parts)

        except Exception as e:
            logger.warning(f"技能 Prompt 构建失败: {e}，降级到 fallback")
            return self._render(self.fallback, **kwargs)

    @staticmethod
    def _render(template: str, **kwargs) -> str:
        """安全渲染模板，未知占位符保留原样。"""
        try:
            return template.format(**kwargs)
        except KeyError:
            # 部分占位符缺失时，只替换已提供的
            formatter = Formatter()
            result = template
            for _, field_name, _, _ in formatter.parse(template):
                if field_name and field_name in kwargs:
                    result = result.replace("{" + field_name + "}", str(kwargs[field_name]))
            return result
