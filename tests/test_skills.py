"""
测试技能文件加载器 — 覆盖 SkillData / SkillLoader / SkillValidator / SkillPromptBuilder
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from skills.loader import SkillLoader, SkillData, _normalize_key


# ──────────────────────────────────────────────
# _normalize_key 辅助函数
# ──────────────────────────────────────────────
class TestNormalizeKey:
    def test_strips_emoji(self):
        assert _normalize_key("🔍 核心分析方法") == "核心分析方法"
        assert _normalize_key("🛠️ 检索策略框架") == "检索策略框架"
        assert _normalize_key("📊 评论质量评估体系") == "评论质量评估体系"

    def test_plain_key_unchanged(self):
        assert _normalize_key("核心功能") == "核心功能"

    def test_strips_leading_spaces(self):
        assert _normalize_key("  输出规范  ") == "输出规范"


# ──────────────────────────────────────────────
# SkillData
# ──────────────────────────────────────────────
class TestSkillData:
    def _make(self, sections: dict, content: str = "", skill_name: str = "test") -> SkillData:
        return SkillData(sections, full_content=content, skill_name=skill_name)

    def test_get_exact_key(self):
        sd = self._make({"核心功能": "desc"})
        assert sd.get("核心功能") == "desc"

    def test_get_clean_key_ignores_emoji(self):
        sd = self._make({"🔍 核心分析方法": "some content"})
        assert sd.get("核心分析方法") == "some content"

    def test_get_missing_returns_default(self):
        sd = self._make({"A": "B"})
        assert sd.get("MISSING") is None
        assert sd.get("MISSING", "default") == "default"

    def test_find_section_exact(self):
        sd = self._make({"核心功能": "exact"})
        assert sd.find_section("核心功能") == "exact"

    def test_find_section_strips_emoji(self):
        sd = self._make({"🔍 核心分析方法": "matched"})
        assert sd.find_section("核心分析方法") == "matched"

    def test_find_section_partial_match(self):
        sd = self._make({"🛠️ 检索策略框架": "partial"})
        # 子串匹配
        assert sd.find_section("检索策略") == "partial"

    def test_find_section_missing_returns_default(self):
        sd = self._make({"A": "B"})
        assert sd.find_section("NOTHERE") == ""
        assert sd.find_section("NOTHERE", "fallback") == "fallback"

    def test_contains(self):
        sd = self._make({"🎭 五种核心风格详解": "styles"})
        assert "五种核心风格详解" in sd
        assert "MISSING" not in sd

    def test_bool_empty_is_false(self):
        sd = self._make({})
        assert not bool(sd)

    def test_bool_nonempty_is_true(self):
        sd = self._make({"k": "v"})
        assert bool(sd)

    def test_get_full_content(self):
        sd = self._make({}, content="## Hello\nworld")
        assert sd.get_full_content() == "## Hello\nworld"

    def test_get_subsection(self):
        section_content = "intro\n\n### 三级搜索策略\nstrategy content\n\n### 其他\nother"
        sd = self._make({"🛠️ 检索策略框架": section_content})
        result = sd.get_subsection("检索策略", "三级搜索策略")
        assert "strategy content" in result

    def test_summary(self):
        sd = self._make({"A": "content"}, skill_name="my_skill")
        s = sd.summary()
        assert "my_skill" in s
        assert "A" in s

    def test_len(self):
        sd = self._make({"A": "1", "B": "2"})
        assert len(sd) == 2

    def test_keys_and_items(self):
        sd = self._make({"A": "1"})
        assert "A" in list(sd.keys())
        assert ("A", "1") in list(sd.items())


# ──────────────────────────────────────────────
# SkillLoader
# ──────────────────────────────────────────────
class TestSkillLoader:
    def test_initialization(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = SkillLoader(skills_dir=tmpdir)
            assert loader.skills_dir == Path(tmpdir)
            assert loader.skills_cache == {}

    def test_load_skill_file_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = SkillLoader(skills_dir=tmpdir)
            with pytest.raises(FileNotFoundError) as exc_info:
                loader.load_skill("nonexistent_skill")
            assert "技能文件不存在" in str(exc_info.value)

    def test_load_skill_success_returns_skill_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_content = "## 核心功能\n这是核心功能描述\n\n## 输出规范\n这是输出规范\n"
            Path(tmpdir, "test_skill.md").write_text(skill_content, encoding="utf-8")

            loader = SkillLoader(skills_dir=tmpdir)
            sd = loader.load_skill("test_skill")

            assert isinstance(sd, SkillData)
            assert "核心功能" in sd
            assert sd.find_section("核心功能") == "这是核心功能描述"

    def test_load_skill_caching(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir, "cached_skill.md")
            p.write_text("## 测试\n内容", encoding="utf-8")

            loader = SkillLoader(skills_dir=tmpdir)
            data1 = loader.load_skill("cached_skill")
            assert "cached_skill" in loader.skills_cache

            p.unlink()
            data2 = loader.load_skill("cached_skill")   # 应从缓存读取
            assert data1 is data2

    def test_clear_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "s.md").write_text("## A\nB", encoding="utf-8")
            loader = SkillLoader(skills_dir=tmpdir)
            loader.load_skill("s")
            assert "s" in loader.skills_cache
            loader.clear_cache()
            assert loader.skills_cache == {}

    def test_get_all_skills(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "skill_a.md").write_text("## A\nC1", encoding="utf-8")
            Path(tmpdir, "skill_b.md").write_text("## B\nC2", encoding="utf-8")
            loader = SkillLoader(skills_dir=tmpdir)
            skills = loader.get_all_skills()
            assert "skill_a" in skills
            assert "skill_b" in skills

    def test_get_skill_section(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "s.md").write_text("## 🔍 核心方法\n内容", encoding="utf-8")
            loader = SkillLoader(skills_dir=tmpdir)
            result = loader.get_skill_section("s", "核心方法")
            assert result == "内容"

    # ------------------------------------------------------------------
    # _parse_skill_markdown 向后兼容
    # ------------------------------------------------------------------
    def test_parse_skill_markdown_basic(self):
        loader = SkillLoader()
        content = "## 章节1\n内容1\n\n## 章节2\n内容2\n"
        result = loader._parse_skill_markdown(content)
        assert "章节1" in result
        assert result["章节1"] == "内容1"

    def test_parse_skill_markdown_empty_section(self):
        loader = SkillLoader()
        content = "## 章节1\n\n## 章节2\n内容\n"
        result = loader._parse_skill_markdown(content)
        assert result["章节1"] == ""
        assert result["章节2"] == "内容"

    def test_parse_skill_markdown_subheadings(self):
        loader = SkillLoader()
        content = "## 主章节\n主内容\n\n### 子章节1\n子内容1\n"
        result = loader._parse_skill_markdown(content)
        assert "主章节" in result
        assert "### 子章节1" in result["主章节"]
        assert "子内容1" in result["主章节"]

    def test_parse_skill_markdown_frontmatter(self):
        loader = SkillLoader()
        content = "---\nname: 测试技能\ndescription: 测试描述\n---\n\n## 核心功能\n功能描述\n"
        result = loader._parse_skill_markdown(content)
        assert result.get("name") == "测试技能"
        assert result.get("核心功能") == "功能描述"

    def test_parse_skill_markdown_code_blocks(self):
        loader = SkillLoader()
        content = '## 代码示例\n```python\ndef hello():\n    print("Hello")\n```\n'
        result = loader._parse_skill_markdown(content)
        assert "代码示例" in result
        assert "```python" in result["代码示例"]

    # ------------------------------------------------------------------
    # 边界情况
    # ------------------------------------------------------------------
    def test_empty_skill_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "empty_skill.md").write_text("", encoding="utf-8")
            loader = SkillLoader(skills_dir=tmpdir)
            sd = loader.load_skill("empty_skill")
            assert len(sd) == 0

    def test_path_traversal_raises(self):
        loader = SkillLoader(skills_dir="/tmp/skills_notexist")
        with pytest.raises(FileNotFoundError):
            loader.load_skill("../etc/passwd")

    def test_only_frontmatter(self):
        loader = SkillLoader()
        content = "---\nname: 只有Frontmatter\ndescription: 测试\n---\n"
        result = loader._parse_skill_markdown(content)
        assert result.get("name") == "只有Frontmatter"
        assert len(result) == 2

    def test_unicode_content(self):
        loader = SkillLoader()
        content = "## 中文章节\n内容包含特殊字符：😀🎉✨\n"
        result = loader._parse_skill_markdown(content)
        assert "中文章节" in result
        assert "😀🎉✨" in result["中文章节"]

    def test_get_skill_loader_singleton(self):
        from skills.loader import get_skill_loader
        l1 = get_skill_loader()
        l2 = get_skill_loader()
        assert l1 is l2

    # ------------------------------------------------------------------
    # 真实技能文件集成测试
    # ------------------------------------------------------------------
    def test_real_skill_files_emoji_sections(self):
        """真实技能文件中的 emoji 章节可通过 find_section 访问"""
        loader = SkillLoader()
        skill_map = {
            "1_perception_expert": "核心分析方法",
            "2_reddit_navigator": "检索策略框架",
            "3_god_comment_generator": "五种核心风格详解",
            "4_visual_prompt_designer": "AI绘画提示词工程",
        }
        for skill_name, section_query in skill_map.items():
            try:
                sd = loader.load_skill(skill_name)
                content = sd.find_section(section_query)
                assert content, (
                    f"{skill_name}.find_section('{section_query}') 返回空 — "
                    f"章节列表: {list(sd.keys())}"
                )
            except FileNotFoundError:
                pytest.skip(f"技能文件 {skill_name}.md 不存在")


# ──────────────────────────────────────────────
# SkillValidator
# ──────────────────────────────────────────────
class TestSkillValidator:
    def test_validate_nonexistent_skill(self):
        from skills.validator import SkillValidator
        from skills.registry import SkillRegistry, SkillMeta

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = SkillLoader(skills_dir=tmpdir)
            registry = SkillRegistry({
                "ghost_skill": SkillMeta(
                    name="ghost_skill",
                    display_name="Ghost",
                    module="modules.ghost",
                    required_sections=["必须章节"],
                )
            })
            validator = SkillValidator(loader=loader, registry=registry)
            result = validator.validate_skill("ghost_skill")
            assert not result.is_valid
            assert not result.file_exists

    def test_validate_valid_skill(self):
        from skills.validator import SkillValidator
        from skills.registry import SkillRegistry, SkillMeta

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "ok_skill.md").write_text(
                "## 必须章节\n有内容\n", encoding="utf-8"
            )
            loader = SkillLoader(skills_dir=tmpdir)
            registry = SkillRegistry({
                "ok_skill": SkillMeta(
                    name="ok_skill",
                    display_name="OK",
                    module="modules.ok",
                    required_sections=["必须章节"],
                )
            })
            validator = SkillValidator(loader=loader, registry=registry)
            result = validator.validate_skill("ok_skill")
            assert result.is_valid

    def test_validate_missing_required_section(self):
        from skills.validator import SkillValidator
        from skills.registry import SkillRegistry, SkillMeta

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "partial.md").write_text(
                "## 其他章节\n内容\n", encoding="utf-8"
            )
            loader = SkillLoader(skills_dir=tmpdir)
            registry = SkillRegistry({
                "partial": SkillMeta(
                    name="partial",
                    display_name="Partial",
                    module="modules.x",
                    required_sections=["必须章节"],
                )
            })
            validator = SkillValidator(loader=loader, registry=registry)
            result = validator.validate_skill("partial")
            assert not result.is_valid
            assert "必须章节" in result.missing_required

    def test_report_contains_skill_name(self):
        from skills.validator import SkillValidator
        from skills.registry import SkillRegistry, SkillMeta

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = SkillLoader(skills_dir=tmpdir)
            registry = SkillRegistry({
                "missing_skill": SkillMeta(
                    name="missing_skill",
                    display_name="Missing",
                    module="modules.m",
                    required_sections=[],
                )
            })
            validator = SkillValidator(loader=loader, registry=registry)
            result = validator.validate_skill("missing_skill")
            report = result.report()
            assert "missing_skill" in report

    def test_summary(self):
        from skills.validator import SkillValidator, SkillValidationResult

        results = {
            "skill_a": SkillValidationResult("skill_a", file_exists=True),
            "skill_b": SkillValidationResult("skill_b", file_exists=False),
        }
        summary = SkillValidator.summary(results)
        assert "skill_a" in summary
        assert "skill_b" in summary


# ──────────────────────────────────────────────
# SkillPromptBuilder
# ──────────────────────────────────────────────
class TestSkillPromptBuilder:
    from skills.prompt_builder import SkillPromptBuilder

    def _make_skill(self, sections: dict) -> "SkillData":
        return SkillData(sections, full_content="", skill_name="test_skill")

    def test_build_with_valid_skill_injects_sections(self):
        from skills.prompt_builder import SkillPromptBuilder

        skill = self._make_skill({"核心方法": "方法内容"})
        builder = SkillPromptBuilder(
            skill=skill,
            role="测试角色",
            sections=[("核心方法", "## 核心方法\n{content}")],
            task_block="## 任务\n{task_text}",
            fallback="fallback: {task_text}",
        )
        result = builder.build(task_text="执行任务")
        assert "方法内容" in result
        assert "执行任务" in result
        assert "测试角色" in result

    def test_build_with_none_skill_uses_fallback(self):
        from skills.prompt_builder import SkillPromptBuilder

        builder = SkillPromptBuilder(
            skill=None,
            role="角色",
            sections=[("章节", "## 章节\n{content}")],
            task_block="## 任务\n{task_text}",
            fallback="fallback_content: {task_text}",
        )
        result = builder.build(task_text="fallback_value")
        assert result == "fallback_content: fallback_value"

    def test_build_missing_section_skipped(self):
        from skills.prompt_builder import SkillPromptBuilder

        skill = self._make_skill({"存在章节": "内容"})
        builder = SkillPromptBuilder(
            skill=skill,
            role="角色",
            sections=[
                ("存在章节", "## 存在\n{content}"),
                ("完全缺失的章节XYZ", "## MISSING_MARKER\n{content}"),
            ],
            task_block="任务",
            fallback="fallback",
        )
        result = builder.build()
        assert "内容" in result
        assert "MISSING_MARKER" not in result

    def test_build_with_title(self):
        from skills.prompt_builder import SkillPromptBuilder

        skill = self._make_skill({"A": "B"})
        builder = SkillPromptBuilder(
            skill=skill,
            role="角色",
            sections=[],
            task_block="任务",
            fallback="fallback",
            title="专家任务标题",
        )
        result = builder.build()
        assert "# 专家任务标题" in result

    def test_build_kwargs_substitution_in_task_block(self):
        from skills.prompt_builder import SkillPromptBuilder

        skill = self._make_skill({"A": "B"})
        builder = SkillPromptBuilder(
            skill=skill,
            role="",
            sections=[],
            task_block="新闻: {news}\n评论: {comment}",
            fallback="fallback",
        )
        result = builder.build(news="某新闻", comment="某评论")
        assert "某新闻" in result
        assert "某评论" in result

    def test_build_fallback_on_exception(self):
        from skills.prompt_builder import SkillPromptBuilder

        # A skill whose find_section raises
        class BrokenSkill:
            def find_section(self, *a, **kw):
                raise RuntimeError("boom")
            def __bool__(self):
                return True

        builder = SkillPromptBuilder(
            skill=BrokenSkill(),  # type: ignore[arg-type]
            role="角色",
            sections=[("章节", "## 章节\n{content}")],
            task_block="任务",
            fallback="安全fallback",
        )
        result = builder.build()
        assert result == "安全fallback"

    def test_render_partial_kwargs_preserved(self):
        from skills.prompt_builder import SkillPromptBuilder

        template = "名称: {name}, 值: {value}, 未知: {unknown}"
        result = SkillPromptBuilder._render(template, name="张三", value="42")
        assert "张三" in result
        assert "42" in result
        # 未提供的占位符保持原样
        assert "{unknown}" in result

    def test_render_complete_kwargs(self):
        from skills.prompt_builder import SkillPromptBuilder

        template = "a={a} b={b}"
        result = SkillPromptBuilder._render(template, a="1", b="2")
        assert result == "a=1 b=2"

    def test_build_no_sections_no_role(self):
        """纯任务块 Prompt（无角色、无章节）"""
        from skills.prompt_builder import SkillPromptBuilder

        skill = self._make_skill({"X": "Y"})
        builder = SkillPromptBuilder(
            skill=skill,
            role="",
            sections=[],
            task_block="纯任务: {x}",
            fallback="fallback",
        )
        result = builder.build(x="输入")
        assert "纯任务: 输入" in result
        assert "角色定位" not in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
