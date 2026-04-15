#!/usr/bin/env python3
"""
NewsRoast-Agent 主程序
四阶段技能链式调用流水线：多模态新闻分析 → Reddit评论检索 → 神评论生成 → 梗图生成
"""

import os
import sys
import logging
from typing import Optional

# Rich库用于终端美化
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

# 新配置系统
from config.settings import settings
from config.constants import ErrorCodes, PathConstants

# 重构后的模块
from modules.news_analyzer import NewsAnalyzer
from modules.reddit_fetcher import RedditFetcher
from modules.comment_generator import CommentGenerator
from modules.image_generator import ImageGenerator
from modules.pipeline_router import PipelineRouter

# 数据模型
from models.data_models import NewsAnalysis, GeneratedComment, CommentStyle

# 错误处理
from utils.error_handling import (
    handle_exceptions, log_execution_time,
    NewsRoastError, APIConnectionError, ContentParseError, ModelGenerationError
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_skill_files() -> list:
    """
    验证技能文件是否存在，确保四阶段技能链式调用的完整性

    Returns:
        缺失的文件列表，每个元素为(文件名, 阶段名称)元组
    """
    skill_files = {
        PathConstants.PERCEPTION_EXPERT_SKILL: "多模态感知与槽点挖掘阶段",
        PathConstants.REDDIT_NAVIGATOR_SKILL: "Reddit生态导航与参考材料检索阶段",
        PathConstants.GOD_COMMENT_GENERATOR_SKILL: "神评论生成与风格化创作阶段",
        PathConstants.VISUAL_PROMPT_DESIGNER_SKILL: "视觉叙事与梗图设计阶段"
    }

    missing_files = []
    for skill_name, stage_name in skill_files.items():
        filepath = os.path.join(PathConstants.SKILLS_DIR, skill_name, "SKILL.md")
        if not os.path.exists(filepath):
            missing_files.append((skill_name, stage_name))
            logger.warning(f"技能文件缺失: {skill_name}/SKILL.md ({stage_name})")

    if not missing_files:
        logger.info("所有技能文件验证通过")

    return missing_files

def create_simple_generated_comment(text: str, style: CommentStyle = CommentStyle.WITTY_JOKE) -> GeneratedComment:
    """
    创建简单的GeneratedComment对象（临时解决方案）

    Args:
        text: 评论文本
        style: 评论风格，默认为抖机灵的玩笑

    Returns:
        GeneratedComment对象
    """
    return GeneratedComment(
        text=text[:500],  # 截断到最大长度
        style=style,
        target_audience="Reddit users",
        emotion_tone="satirical",
        interaction_design="引发讨论和点赞"
    )


def create_simple_news_analysis(url: str, text_content: str) -> NewsAnalysis:
    """
    创建简单的NewsAnalysis对象（临时解决方案）

    Args:
        url: 新闻URL
        text_content: 新闻分析文本

    Returns:
        NewsAnalysis对象
    """
    # 从分析文本中提取搜索查询
    search_query = ""
    if "SEARCH_QUERY:" in text_content:
        search_query = text_content.split("SEARCH_QUERY:")[-1].strip().split('\n')[0]
    else:
        search_query = text_content[:50]  # 前50个字符作为查询词

    return NewsAnalysis(
        url=url,
        text_content=text_content[:3000],  # 截断到最大长度
        image_urls=[],  # 暂时为空
        core_event="未提取",
        visual_analysis=["未提取"],
        text_analysis=["未提取"],
        contrast_points=["未提取"],
        cringe_points=[{"topic": "未提取", "absurdity": 5, "resonance": 5}],
        search_query=search_query
    )


@handle_exceptions(default_return=ErrorCodes.SYSTEM_ERROR)
@log_execution_time
def main() -> int:
    """
    NewsRoast-Agent 主程序入口

    Returns:
        程序退出码 (0表示成功，非0表示错误)
    """
    console = Console()
    logger.info("启动 NewsRoast-Agent")

    # 验证技能文件完整性
    missing_files = validate_skill_files()
    if missing_files:
        console.print(Panel(
            "[bold red]⚠️  技能文件完整性检查失败[/bold red]\n\n"
            "[yellow]以下技能文件缺失，可能影响系统执行质量：[/yellow]\n\n" +
            "\n".join([f"  • {filename} ({stage_name})" for filename, stage_name in missing_files]) +
            "\n\n[dim]请确保.claude/skills/目录下的四个技能文件完整存在。[/dim]",
            border_style="red"
        ))

        # 询问是否继续
        if sys.stdin.isatty():
            response = Prompt.ask("是否继续执行？", choices=["y", "n"], default="y")
            if response.lower() != "y":
                console.print("[dim]程序已退出。[/dim]")
                logger.warning("用户选择退出（技能文件缺失）")
                return ErrorCodes.CONFIGURATION_ERROR
        else:
            console.print("[yellow]非交互式模式，继续执行但质量可能受影响。[/yellow]")
            logger.warning("技能文件缺失，继续执行")

    console.print(Panel(
        "[bold blue]🚀 NewsRoast-Agent[/bold blue]\n"
        "[dim]输入新闻链接，自动执行四阶段技能链：多模态分析 → Reddit检索 → 神评论生成 → 梗图生成[/dim]",
        border_style="blue"
    ))

    # 1. 交互式输入网址
    default_url = "https://www.ainvest.com/news/apple-100-billion-investment-sparks-market-rally-offers-glimpse-trump-tariff-carveout-framework-2508/"

    # 检查是否在交互式环境（避免脚本运行时EOFError）
    if sys.stdin.isatty():
        console.print(f"\n[bold cyan]请输入新闻 URL[/bold cyan] [dim](直接回车将使用默认苹果新闻):[/dim]")
        try:
            user_input = Prompt.ask("> ", default=default_url)
            news_url = user_input.strip()
        except KeyboardInterrupt:
            console.print("\n[yellow]用户中断输入[/yellow]")
            logger.info("用户中断程序")
            return ErrorCodes.SUCCESS
    else:
        # 非交互式环境，直接使用默认URL
        news_url = default_url
        console.print(f"\n[dim]非交互式模式，使用默认新闻URL[/dim]")

    if not news_url:
        console.print("[bold red]错误: URL不能为空[/bold red]")
        logger.error("URL输入为空")
        return ErrorCodes.CONTENT_PARSE_ERROR

    console.print(f"✅ [green]正在处理:[/green] [link={news_url}]{news_url[:80]}...[/link]\n")
    logger.info(f"开始处理新闻URL: {news_url}")

    # 2. 多模态新闻分析阶段（挂载: perception_expert/SKILL.md）
    console.print("[bold yellow]>> 1. 多模态新闻分析与槽点挖掘[/bold yellow] [dim](挂载: perception_expert/SKILL.md)[/dim]")
    try:
        analyzer = NewsAnalyzer()
        analysis_text = analyzer.process_news(news_url)

        if not analysis_text or "分析失败" in analysis_text:
            raise ContentParseError("新闻分析失败", content_type="news_analyzer")

        console.print(Panel(Markdown(analysis_text), title="[bold cyan]📰 多模态新闻分析结果[/bold cyan]", border_style="cyan"))
        logger.info("新闻分析阶段完成")

    except Exception as e:
        logger.exception(f"新闻分析阶段失败: {e}")
        console.print(Panel(
            f"[bold red]新闻分析失败[/bold red]\n\n[dim]{str(e)}[/dim]",
            title="❌ 错误",
            border_style="red"
        ))
        return ErrorCodes.CONTENT_PARSE_ERROR

    # 路由决策：基于 Stage 1 分析结果，动态决定是否执行 Stage 2 / Stage 4
    console.print("\n[bold yellow]>> 路由决策[/bold yellow] [dim](agent 自主选择后续 skill)[/dim]")
    try:
        router = PipelineRouter()
        routing = router.decide(analysis_text)
        console.print(Panel(
            f"[bold]决策理由[/bold]: {routing.reasoning}\n"
            f"  Reddit 检索 (Stage 2): {'[green]执行[/green]' if routing.run_reddit_search else '[yellow]跳过[/yellow]'}\n"
            f"  图像生成 (Stage 4): {'[green]执行[/green]' if routing.run_image_generation else '[yellow]跳过[/yellow]'}",
            title="[bold blue]🧭 流水线路由[/bold blue]",
            border_style="blue"
        ))
        logger.info(f"路由决策: reddit={routing.run_reddit_search}, image={routing.run_image_generation}, reason={routing.reasoning}")
    except Exception as e:
        logger.warning(f"路由决策异常，降级为全执行: {e}")
        from modules.pipeline_router import RoutingDecision
        routing = RoutingDecision.run_all(reason=f"异常降级: {type(e).__name__}")

    # 3. Reddit生态导航阶段（挂载: reddit_navigator/SKILL.md）
    console.print("\n[bold yellow]>> 2. Reddit生态导航与参考材料检索[/bold yellow] [dim](挂载: reddit_navigator/SKILL.md)[/dim]")
    if not routing.run_reddit_search:
        console.print("  [yellow]⏭ 已跳过（路由决策：话题不适合 Reddit 检索）[/yellow]")
        reference_comments = []
    else:
        try:
            fetcher = RedditFetcher()
            reference_comments = fetcher.get_reference_comments(analysis_text)

            if reference_comments:
                console.print(f"  [green]✅ 成功检索到 {len(reference_comments)} 条参考评论[/green]")
                for i, comment in enumerate(reference_comments[:3]):
                    text = comment.get('text', '')
                    score = comment.get('score', '')
                    preview = text[:80] + "..." if len(text) > 80 else text
                    console.print(f"    [dim]{i+1}.[/dim] [cyan]{preview}[/cyan] [dim]({score})[/dim]")
                logger.info(f"检索到 {len(reference_comments)} 条参考评论")
            else:
                console.print("  [yellow]⚠️ 未发现相关参考，将由 AI 纯原创[/yellow]")
                logger.info("未检索到参考评论，使用纯原创模式")

        except Exception as e:
            logger.exception(f"Reddit检索阶段失败: {e}")
            console.print("  [yellow]⚠️ Reddit检索失败，降级为纯原创模式[/yellow]")
            reference_comments = []
    # 4. 神评论生成阶段（挂载: god_comment_generator/SKILL.md）
    console.print("\n[bold yellow]>> 3. 神评论生成与风格化创作[/bold yellow] [dim](挂载: god_comment_generator/SKILL.md)[/dim]")
    try:
        generator = CommentGenerator()
        comments_text = generator.generate_comments(analysis_text, reference_comments)

        if not comments_text or "生成评论失败" in comments_text:
            raise ModelGenerationError("评论生成失败", model_name="comment_generator")

        console.print(Panel(Markdown(comments_text), title="[bold magenta]🔥 AI 神评论列表[/bold magenta]", border_style="magenta"))
        logger.info("神评论生成阶段完成")

    except Exception as e:
        logger.exception(f"评论生成阶段失败: {e}")
        console.print(Panel(
            f"[bold red]评论生成失败[/bold red]\n\n[dim]{str(e)}[/dim]",
            title="❌ 错误",
            border_style="red"
        ))
        return ErrorCodes.COMMENT_GENERATION_FAILED
    
    # return
    # 5. 视觉叙事与梗图设计阶段（挂载: visual_prompt_designer/SKILL.md）
    console.print("\n[bold yellow]>> 4. 视觉叙事与梗图设计[/bold yellow] [dim](挂载: visual_prompt_designer/SKILL.md)[/dim]")
    if not routing.run_image_generation:
        console.print("  [yellow]⏭ 已跳过（路由决策：新闻缺乏视觉化潜力）[/yellow]")
        image_url = None
    else:
        try:
            image_gen = ImageGenerator()
            console.print("  [dim]正在挑选最佳槽点并转化为视觉Prompt...[/dim]")

            # 创建临时数据对象（TODO: 未来需要真正的结构化解析）
            simple_comment = create_simple_generated_comment(comments_text)
            simple_analysis = create_simple_news_analysis(news_url, analysis_text)

            image_url = image_gen.generate_image(simple_comment, simple_analysis)

            if image_url:
                console.print(f"\n[bold green]✅ 图片生成成功！[/bold green]")
                console.print("[bold cyan]🔗 梗图预览链接 (复制到浏览器查看):[/bold cyan]")
                console.print(f"\n{image_url}\n")
                console.print("[dim]提示: 如果链接无法点击，请完整复制后粘贴到浏览器地址栏。[/dim]")
                logger.info("图片生成成功")
            else:
                console.print("\n[yellow]⚠️ 图片生成失败或超时[/yellow]")
                logger.warning("图片生成失败")

        except Exception as e:
            logger.exception(f"图片生成阶段失败: {e}")
            console.print("\n[yellow]⚠️ 图片生成失败，跳过此阶段[/yellow]")
            image_url = None

    # 6. 结束语
    console.print("\n" + "=" * 50)
    if image_url:
        console.print("[bold blue]🎉 四阶段技能链执行完成！[/bold blue]")
    else:
        console.print("[bold yellow]⚠️ 任务完成（图片生成阶段跳过）[/bold yellow]")

    logger.info("NewsRoast-Agent执行完成")
    return ErrorCodes.SUCCESS

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code if exit_code != ErrorCodes.SUCCESS else 0)
    except KeyboardInterrupt:
        print("\n\n[yellow]程序被用户中断[/yellow]")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"程序崩溃: {e}")
        print(f"\n[bold red]程序崩溃: {str(e)}[/bold red]")
        sys.exit(ErrorCodes.SYSTEM_ERROR)
