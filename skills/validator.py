"""
技能文件验证器

在流水线启动前检查技能文件是否存在、章节是否完整，
输出结构化的验证报告。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from skills.loader import SkillLoader, get_skill_loader
from skills.registry import SkillRegistry, SKILL_REGISTRY

logger = logging.getLogger(__name__)


@dataclass
class SectionCheckResult:
    section: str
    found: bool
    matched_key: str = ""        # 实际匹配到的原始 key
    content_preview: str = ""    # 前 80 字符


@dataclass
class SkillValidationResult:
    skill_name: str
    file_exists: bool
    required_sections: List[SectionCheckResult] = field(default_factory=list)
    optional_sections: List[SectionCheckResult] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return self.file_exists and all(r.found for r in self.required_sections)

    @property
    def missing_required(self) -> List[str]:
        return [r.section for r in self.required_sections if not r.found]

    def report(self) -> str:
        lines = [f"[{self.skill_name}] {'✅ 通过' if self.is_valid else '❌ 不通过'}"]
        if not self.file_exists:
            lines.append("  文件不存在")
            return "\n".join(lines)
        for r in self.required_sections:
            icon = "✅" if r.found else "❌"
            matched = f" (matched: {r.matched_key})" if r.matched_key and r.matched_key != r.section else ""
            lines.append(f"  {icon} [必须] {r.section}{matched}")
        for r in self.optional_sections:
            icon = "✅" if r.found else "⚠️"
            lines.append(f"  {icon} [可选] {r.section}")
        return "\n".join(lines)


class SkillValidator:
    """
    验证技能文件完整性。

    Usage
    -----
    validator = SkillValidator()
    results = validator.validate_all()
    print(validator.summary(results))
    """

    def __init__(
        self,
        loader: Optional[SkillLoader] = None,
        registry: Optional[SkillRegistry] = None,
    ):
        self.loader = loader or get_skill_loader()
        self.registry = registry or SkillRegistry(SKILL_REGISTRY)

    def validate_skill(self, skill_name: str) -> SkillValidationResult:
        """验证单个技能文件。"""
        meta = self.registry.get(skill_name)

        try:
            skill_data = self.loader.load_skill(skill_name)
            file_exists = True
        except FileNotFoundError:
            return SkillValidationResult(skill_name=skill_name, file_exists=False)

        required_results = []
        optional_results = []

        def _check(section: str) -> SectionCheckResult:
            content = skill_data.find_section(section)
            found = bool(content)
            matched_key = ""
            if found:
                # 找到实际匹配的原始 key
                for raw_key in skill_data.keys():
                    if section in raw_key or raw_key.endswith(section):
                        matched_key = raw_key
                        break
            return SectionCheckResult(
                section=section,
                found=found,
                matched_key=matched_key,
                content_preview=content[:80] if content else "",
            )

        if meta:
            required_results = [_check(s) for s in meta.required_sections]
            optional_results = [_check(s) for s in meta.optional_sections]

        return SkillValidationResult(
            skill_name=skill_name,
            file_exists=file_exists,
            required_sections=required_results,
            optional_sections=optional_results,
        )

    def validate_all(self) -> Dict[str, SkillValidationResult]:
        """验证所有注册的技能文件。"""
        results: Dict[str, SkillValidationResult] = {}
        for name in self.registry.all_skill_names():
            results[name] = self.validate_skill(name)
            if not results[name].is_valid:
                logger.warning(f"技能验证失败: {name}\n{results[name].report()}")
            else:
                logger.debug(f"技能验证通过: {name}")
        return results

    @staticmethod
    def summary(results: Dict[str, SkillValidationResult]) -> str:
        """生成所有技能的验证摘要。"""
        lines = ["=== 技能文件验证报告 ==="]
        passed = sum(1 for r in results.values() if r.is_valid)
        lines.append(f"通过: {passed}/{len(results)}\n")
        for result in results.values():
            lines.append(result.report())
        return "\n".join(lines)
