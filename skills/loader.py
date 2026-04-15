"""
技能文件加载器 — 通用化重写

核心改进
--------
1. SkillData 包装器：提供 find_section() 模糊匹配（自动忽略 emoji/空格前缀）
2. get_full_content()：返回原始 Markdown，方便直接嵌入 prompt
3. get_subsection()：按 ### 子标题精确提取子章节内容
4. emoji 标准化：解析时剥离 ## 标题里的 emoji 和空格，生成"干净 key"
   原始 key 同时保留，两者均可查找

目录结构
--------
.claude/skills/
  1_perception_expert.md
  2_reddit_navigator.md
  3_god_comment_generator.md
  4_visual_prompt_designer.md
"""

from __future__ import annotations

import os
import re
import unicodedata
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

# 匹配 emoji / Unicode 符号（排除汉字、字母、数字、空格）
_EMOJI_RE = re.compile(
    r"[\U0001F300-\U0001FFFF"      # 杂项符号和表情
    r"\U00002600-\U000027BF"       # 杂项符号
    r"\U0000FE00-\U0000FE0F"       # 变体选择符
    r"\U0001F900-\U0001F9FF"       # 补充符号
    r"\u2600-\u26FF"               # 杂项符号
    r"\u2700-\u27BF]+",            # 装饰符号
    flags=re.UNICODE,
)


def _normalize_key(raw: str) -> str:
    """去掉标题中的 emoji、多余空格，返回干净 key。"""
    cleaned = _EMOJI_RE.sub("", raw).strip()
    # 压缩中间多余空格
    return re.sub(r"\s{2,}", " ", cleaned)


class SkillData:
    """
    单个技能文件的解析结果包装器。

    内部维护两份索引：
      _sections     : {原始 key: content}     — e.g. {"🔍 核心分析方法": "..."}
      _clean_index  : {干净 key: 原始 key}    — e.g. {"核心分析方法": "🔍 核心分析方法"}
    """

    def __init__(self, raw_sections: Dict[str, str], full_content: str, skill_name: str = ""):
        self._sections: Dict[str, str] = raw_sections
        self._full_content: str = full_content
        self.skill_name: str = skill_name

        # 建立干净 key → 原始 key 的映射
        self._clean_index: Dict[str, str] = {
            _normalize_key(k): k for k in raw_sections
        }

    # ------------------------------------------------------------------
    # 字典兼容接口（向后兼容旧代码的 .get() 调用）
    # ------------------------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        """精确匹配（原始 key），找不到则尝试干净 key 匹配。"""
        if key in self._sections:
            return self._sections[key]
        clean = _normalize_key(key)
        raw_key = self._clean_index.get(clean)
        if raw_key:
            return self._sections[raw_key]
        return default

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None

    def __bool__(self) -> bool:
        return bool(self._sections)

    def keys(self):
        return self._sections.keys()

    def items(self):
        return self._sections.items()

    def __len__(self) -> int:
        return len(self._sections)

    # ------------------------------------------------------------------
    # 新增：模糊匹配查找
    # ------------------------------------------------------------------
    def find_section(self, query: str, default: str = "") -> str:
        """
        模糊查找章节内容。

        匹配规则（优先级从高到低）：
        1. 精确匹配原始 key
        2. 精确匹配干净 key（忽略 emoji 前缀）
        3. 子串包含：query 是某个干净 key 的子串，或某干净 key 是 query 的子串
        4. 返回 default

        示例
        ----
        skill.find_section("核心分析方法")    # 匹配 "🔍 核心分析方法"
        skill.find_section("检索策略")        # 匹配 "🛠️ 检索策略框架"
        """
        # 1. 精确原始 key
        if query in self._sections:
            return self._sections[query]

        # 2. 精确干净 key
        clean_query = _normalize_key(query)
        raw_key = self._clean_index.get(clean_query)
        if raw_key:
            return self._sections[raw_key]

        # 3. 子串包含
        for clean_key, raw_key in self._clean_index.items():
            if clean_query in clean_key or clean_key in clean_query:
                return self._sections[raw_key]

        return default

    def get_subsection(self, section_query: str, subsection_query: str, default: str = "") -> str:
        """
        提取章节内容中的 ### 子章节。

        Args:
            section_query: 父章节查询词（支持模糊匹配）
            subsection_query: 子章节查询词（忽略 emoji）

        Returns:
            子章节内容字符串
        """
        section_content = self.find_section(section_query)
        if not section_content:
            return default

        # 按 ### 分割子章节
        sub_pattern = re.compile(r"^###\s+(.+?)$", re.MULTILINE)
        matches = list(sub_pattern.finditer(section_content))

        if not matches:
            return default

        clean_sub_query = _normalize_key(subsection_query)

        for i, match in enumerate(matches):
            sub_title = _normalize_key(match.group(1))
            if clean_sub_query in sub_title or sub_title in clean_sub_query:
                start = match.end()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(section_content)
                return section_content[start:end].strip()

        return default

    def get_full_content(self) -> str:
        """返回完整原始 Markdown 内容，适合直接嵌入 LLM prompt。"""
        return self._full_content

    def summary(self) -> str:
        """返回技能文件的顶层章节列表，方便调试。"""
        lines = [f"Skill: {self.skill_name or '(unnamed)'}"]
        for raw_key in self._sections:
            preview = self._sections[raw_key][:60].replace("\n", " ")
            lines.append(f"  [{raw_key}] → {preview}...")
        return "\n".join(lines)


class SkillLoader:
    """技能文件加载器，将 .md 文件解析为 SkillData 对象并缓存。"""

    def __init__(self, skills_dir: str = ".claude/skills"):
        self.skills_dir = Path(skills_dir)
        self.skills_cache: Dict[str, SkillData] = {}

        if not self.skills_dir.exists():
            logger.warning(f"技能目录不存在: {self.skills_dir}，尝试创建")
            self.skills_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------
    def load_skill(self, skill_name: str) -> SkillData:
        """
        加载技能文件，返回 SkillData 对象（带缓存）。

        Args:
            skill_name: 技能文件名（不含 .md 后缀），例如 "1_perception_expert"

        Returns:
            SkillData 实例

        Raises:
            FileNotFoundError: 文件不存在
        """
        if skill_name in self.skills_cache:
            return self.skills_cache[skill_name]

        skill_file = self.skills_dir / f"{skill_name}.md"
        if not skill_file.exists():
            logger.error(f"技能文件不存在: {skill_file}")
            raise FileNotFoundError(f"技能文件不存在: {skill_file}")

        try:
            content = skill_file.read_text(encoding="utf-8")
            skill_data = self._parse_skill_file(content, skill_name)
            self.skills_cache[skill_name] = skill_data
            logger.info(f"成功加载技能: {skill_name} ({len(skill_data)} 个章节)")
            return skill_data

        except Exception as e:
            logger.exception(f"加载技能文件失败: {skill_file}, 错误: {e}")
            raise

    def get_all_skills(self) -> Dict[str, SkillData]:
        """加载并返回技能目录下所有 .md 文件。"""
        skills: Dict[str, SkillData] = {}
        if not self.skills_dir.exists():
            return skills
        for skill_file in sorted(self.skills_dir.glob("*.md")):
            name = skill_file.stem
            try:
                skills[name] = self.load_skill(name)
            except Exception as e:
                logger.error(f"加载技能失败: {name}, 错误: {e}")
        return skills

    def get_skill_section(self, skill_name: str, section_query: str) -> Optional[str]:
        """快捷方法：加载技能并模糊查找章节。"""
        try:
            return self.load_skill(skill_name).find_section(section_query)
        except Exception as e:
            logger.error(f"获取技能章节失败: {skill_name}.{section_query}, 错误: {e}")
            return None

    def clear_cache(self):
        """清空缓存（测试或热重载时使用）。"""
        self.skills_cache.clear()
        logger.debug("技能缓存已清空")

    # ------------------------------------------------------------------
    # 内部解析
    # ------------------------------------------------------------------
    def _parse_skill_file(self, content: str, skill_name: str = "") -> SkillData:
        """将原始 Markdown 解析为 SkillData。"""
        sections = self._extract_sections(content)

        # 合并 YAML frontmatter
        frontmatter = self._extract_frontmatter(content)
        if frontmatter and isinstance(frontmatter, dict):
            sections.update(frontmatter)

        return SkillData(sections, full_content=content, skill_name=skill_name)

    # 向后兼容：旧代码直接调用 _parse_skill_markdown
    def _parse_skill_markdown(self, content: str) -> Dict[str, Any]:
        """向后兼容接口，返回普通字典（原始 key，不含 emoji 标准化）。"""
        skill_data = self._parse_skill_file(content)
        result = dict(skill_data.items())
        return result

    def _extract_sections(self, content: str) -> Dict[str, str]:
        """
        按 ## 标题切分章节，返回 {原始 key: 内容} 字典。
        ### 子标题保留在父章节内容中。
        """
        sections: Dict[str, str] = {}
        current_section: Optional[str] = None
        current_lines: List[str] = []

        # 剥离 frontmatter 块后再解析
        body = re.sub(r"^---\s*\n.*?\n---\s*\n", "", content, flags=re.DOTALL)

        for line in body.split("\n"):
            if line.startswith("## "):
                if current_section is not None:
                    sections[current_section] = "\n".join(current_lines).strip()
                current_section = line[3:].strip()
                current_lines = []
            else:
                current_lines.append(line)

        if current_section is not None:
            sections[current_section] = "\n".join(current_lines).strip()

        return sections

    @staticmethod
    def _extract_frontmatter(content: str) -> Optional[Dict[str, Any]]:
        """提取 YAML frontmatter。"""
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if match:
            try:
                return yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError as e:
                logger.warning(f"YAML frontmatter 解析失败: {e}")
        return None


# ------------------------------------------------------------------
# 单例
# ------------------------------------------------------------------
_skill_loader_instance: Optional[SkillLoader] = None


def get_skill_loader(skills_dir: str = ".claude/skills") -> SkillLoader:
    """返回全局单例 SkillLoader。"""
    global _skill_loader_instance
    if _skill_loader_instance is None:
        _skill_loader_instance = SkillLoader(skills_dir)
    return _skill_loader_instance
