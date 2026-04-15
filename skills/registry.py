"""
技能注册表

维护四个核心技能的元数据：名称、对应的模块、必须章节清单。
技能名与 .claude/skills/ 子目录名一致（无数字前缀），
执行顺序由 main.py 的调用顺序决定，不耦合在文件名里。
供 SkillValidator 和日志诊断使用。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SkillMeta:
    """单个技能的元数据描述。"""
    name: str                          # 目录名，如 "perception_expert"
    display_name: str                  # 可读名称
    module: str                        # 对应模块，如 "modules.news_analyzer"
    required_sections: List[str]       # 必须存在的章节（干净 key，无 emoji）
    optional_sections: List[str] = field(default_factory=list)


# ------------------------------------------------------------------
# 四阶段技能注册（顺序即执行顺序）
# ------------------------------------------------------------------
SKILL_REGISTRY: Dict[str, SkillMeta] = {
    "perception_expert": SkillMeta(
        name="perception_expert",
        display_name="多模态感知专家",
        module="modules.news_analyzer",
        required_sections=["核心分析方法", "输出规范"],
        optional_sections=["常见陷阱与规避", "工具箱", "质量评估标准"],
    ),
    "reddit_navigator": SkillMeta(
        name="reddit_navigator",
        display_name="Reddit 生态导航器",
        module="modules.reddit_fetcher",
        required_sections=["检索策略框架", "评论质量评估体系"],
        optional_sections=["Reddit特有表达模式", "技术实现要点", "时效性保障策略"],
    ),
    "god_comment_generator": SkillMeta(
        name="god_comment_generator",
        display_name="神评论生成器",
        module="modules.comment_generator",
        required_sections=["五种核心风格详解", "Reddit语态大师课"],
        optional_sections=["创意生成框架", "技术实现策略", "输出规范"],
    ),
    "visual_prompt_designer": SkillMeta(
        name="visual_prompt_designer",
        display_name="视觉提示设计师",
        module="modules.image_generator",
        required_sections=["AI绘画提示词工程", "视觉叙事原则"],
        optional_sections=["视觉风格矩阵", "创意生成技术", "模型特定优化"],
    ),
}


class SkillRegistry:
    """技能注册表查询接口。"""

    def __init__(self, registry: Dict[str, SkillMeta] = SKILL_REGISTRY):
        self._registry = registry

    def get(self, skill_name: str) -> Optional[SkillMeta]:
        return self._registry.get(skill_name)

    def all_skill_names(self) -> List[str]:
        return sorted(self._registry.keys())

    def required_sections(self, skill_name: str) -> List[str]:
        meta = self.get(skill_name)
        return meta.required_sections if meta else []
