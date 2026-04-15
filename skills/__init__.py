"""
NewsRoast-Agent 技能系统

技能文件是驱动四阶段流水线的"执行宪法"，每个 Markdown 技能文件
被解析为结构化字典，注入到对应模块的 LLM Prompt 中。

快速使用
--------
from skills import get_skill_loader, SkillLoader, SkillRegistry, SkillPromptBuilder

loader  = get_skill_loader()
skill   = loader.load_skill("1_perception_expert")
text    = skill.find_section("核心分析方法")   # 模糊匹配，忽略 emoji 前缀
full    = skill.get_full_content()             # 返回完整原始 Markdown

builder = SkillPromptBuilder(skill=skill, role="...", sections=[...],
                              task_block="...", fallback="...")
prompt  = builder.build(news_text="...")
"""

from skills.loader import SkillLoader, SkillData, get_skill_loader
from skills.registry import SkillRegistry, SKILL_REGISTRY
from skills.validator import SkillValidator
from skills.prompt_builder import SkillPromptBuilder

__all__ = [
    "SkillLoader",
    "SkillData",
    "get_skill_loader",
    "SkillRegistry",
    "SKILL_REGISTRY",
    "SkillValidator",
    "SkillPromptBuilder",
]

