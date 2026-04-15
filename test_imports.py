#!/usr/bin/env python3
"""测试重构后的模块导入"""

import sys
import os
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """测试所有模块的导入"""
    modules_to_test = [
        "config.settings",
        "config.constants",
        "config.api",
        "config.models",
        "config.prompts",
        "models.data_models",
        "utils.error_handling",
        "skills.loader",
        "modules.news_analyzer",
        "modules.reddit_fetcher",
        "modules.comment_generator",
        "modules.image_generator"
    ]

    success_count = 0
    total_count = len(modules_to_test)

    for module_name in modules_to_test:
        try:
            __import__(module_name)
            logger.info(f"✓ {module_name} 导入成功")
            success_count += 1
        except ImportError as e:
            logger.error(f"✗ {module_name} 导入失败: {e}")
        except Exception as e:
            logger.error(f"✗ {module_name} 导入时出错: {e}")

    logger.info(f"导入测试完成: {success_count}/{total_count} 成功")

    if success_count == total_count:
        logger.info("所有模块导入成功！")
        return True
    else:
        logger.error("部分模块导入失败")
        return False

def test_skill_loading():
    """测试技能文件加载"""
    try:
        from skills.loader import get_skill_loader

        skill_loader = get_skill_loader()
        logger.info("✓ 技能加载器创建成功")

        # 测试加载技能文件
        skill_files = [
            "1_perception_expert",
            "2_reddit_navigator",
            "3_god_comment_generator",
            "4_visual_prompt_designer"
        ]

        for skill_name in skill_files:
            try:
                skill_data = skill_loader.load_skill(skill_name)
                logger.info(f"✓ 技能文件 '{skill_name}' 加载成功")
                # 打印技能文件的部分信息
                sections = list(skill_data.keys())
                logger.debug(f"  包含章节: {sections[:3]}...")
            except Exception as e:
                logger.error(f"✗ 技能文件 '{skill_name}' 加载失败: {e}")
                return False

        logger.info("✓ 所有技能文件加载成功！")
        return True

    except Exception as e:
        logger.error(f"✗ 技能文件加载测试失败: {e}")
        return False

def test_module_initialization():
    """测试模块初始化"""
    modules_initialized = []

    try:
        # 测试NewsAnalyzer初始化
        from modules.news_analyzer import NewsAnalyzer
        analyzer = NewsAnalyzer()
        modules_initialized.append("NewsAnalyzer")
        logger.info("✓ NewsAnalyzer 初始化成功")
    except Exception as e:
        logger.error(f"✗ NewsAnalyzer 初始化失败: {e}")

    try:
        # 测试RedditFetcher初始化
        from modules.reddit_fetcher import RedditFetcher
        fetcher = RedditFetcher()
        modules_initialized.append("RedditFetcher")
        logger.info("✓ RedditFetcher 初始化成功")
    except Exception as e:
        logger.error(f"✗ RedditFetcher 初始化失败: {e}")

    try:
        # 测试CommentGenerator初始化
        from modules.comment_generator import CommentGenerator
        generator = CommentGenerator()
        modules_initialized.append("CommentGenerator")
        logger.info("✓ CommentGenerator 初始化成功")
    except Exception as e:
        logger.error(f"✗ CommentGenerator 初始化失败: {e}")

    try:
        # 测试ImageGenerator初始化
        from modules.image_generator import ImageGenerator
        image_gen = ImageGenerator()
        modules_initialized.append("ImageGenerator")
        logger.info("✓ ImageGenerator 初始化成功")
    except Exception as e:
        logger.error(f"✗ ImageGenerator 初始化失败: {e}")

    logger.info(f"模块初始化测试完成: {len(modules_initialized)}/4 个模块初始化成功")
    return len(modules_initialized) == 4

if __name__ == "__main__":
    logger.info("开始测试重构后的NewsRoast-Agent项目...")

    all_passed = True

    # 测试导入
    logger.info("\n=== 测试模块导入 ===")
    if not test_imports():
        all_passed = False

    # 测试技能文件加载
    logger.info("\n=== 测试技能文件加载 ===")
    if not test_skill_loading():
        all_passed = False

    # 测试模块初始化
    logger.info("\n=== 测试模块初始化 ===")
    if not test_module_initialization():
        all_passed = False

    logger.info("\n=== 测试结果汇总 ===")
    if all_passed:
        logger.info("🎉 所有测试通过！重构后的代码基础架构正常。")
        sys.exit(0)
    else:
        logger.error("❌ 部分测试失败，需要进一步检查。")
        sys.exit(1)