# main.py 完整重构后的主逻辑

from modules.news_analyzer import NewsAnalyzer
from modules.reddit_fetcher import RedditFetcher
from modules.comment_generator import CommentGenerator
from modules.image_generator import ImageGenerator

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt  # 引入输入组件

def main():
    console = Console()
    
    console.print(Panel("[bold blue]🚀 AI 新闻神评论 Agent[/bold blue]\n[dim]输入一个新闻链接，AI 自动为你生成梗图与神评论[/dim]", border_style="blue"))

    # 1. 交互式输入网址
    default_url = "https://www.ainvest.com/news/apple-100-billion-investment-sparks-market-rally-offers-glimpse-trump-tariff-carveout-framework-2508/"
    
    console.print(f"\n[bold cyan]请输入新闻 URL[/bold cyan] [dim](直接回车将使用默认苹果新闻):[/dim]")
    user_input = Prompt.ask("> ", default=default_url)
    
    news_url = user_input.strip()
    console.print(f"✅ [green]正在处理:[/green] [link={news_url}]{news_url}[/link]\n")

    # --- 后面的逻辑保持不变 ---
    
    # 2. 分析新闻
    console.print("[bold yellow]>> 1. 正在阅读并提取新闻核心与搜索词...[/bold yellow]")
    analyzer = NewsAnalyzer()
    analysis = analyzer.process_news(news_url)
    console.print(Panel(Markdown(analysis), title="[bold cyan]📰 新闻分析摘要[/bold cyan]", border_style="cyan"))
    
    # return

    # 3. 获取参考评论
    console.print("\n[bold yellow]>> 2. 正在检索社交媒体讨论 (Reddit/HN)...[/bold yellow]")
    fetcher = RedditFetcher()
    reference_comments = fetcher.get_reference_comments(analysis)
    if reference_comments:
        for i, comment in enumerate(reference_comments[:3]):
            # console.print(f"  [green]参考 {i+1}:[/green] {comment['text'][:60]}...")
            console.print(f"  [green]参考 {i+1}:[/green] {comment['text']}...")
    else:
        console.print("  [dim]未发现相关参考，将由 AI 纯原创。[/dim]")
    
    # return
    # 4. 生成神评论
    console.print("\n[bold yellow]>> 3. 正在构思神评论文案...[/bold yellow]")
    generator = CommentGenerator()
    comments = generator.generate_comments(analysis, reference_comments)
    console.print(Panel(Markdown(comments), title="[bold magenta]🔥 AI 神评论列表[/bold magenta]", border_style="magenta"))
    
    # return
    # 5. 为评论配图
    console.print("\n[bold yellow]>> 4. 正在调用 通义万相 生成梗图...[/bold yellow]")
    image_gen = ImageGenerator()
    console.print(f"  [dim]正在让 AI 挑选最佳槽点并转化为视觉 Prompt...[/dim]")
    
    image_url = image_gen.generate_image(comments, analysis)
    if image_url:
        console.print(f"\n[bold green]✅ 图片生成成功！[/bold green]")
        
        # 1. 打印一个带图标的引导文字
        console.print("[bold cyan]🔗 梗图预览链接 (复制到浏览器查看):[/bold cyan]")
        
        # 2. 裸发链接，不加任何包裹，确保终端能完美识别
        # 甚至不加 [link] 标签，直接打印 URL 往往是长链接最稳的选择
        console.print(f"\n{image_url}\n")
        
        console.print("[dim]提示: 如果链接无法点击，请完整复制后粘贴到浏览器地址栏。[/dim]")
        # console.print(f"\n[bold green]✅ 图片生成成功！[/bold green]")
        # console.print(Panel(f"点击链接预览图片:\n{image_url}", title="🖼️ 梗图结果", border_style="green"))
    else:
        console.print("\n[bold red]❌ 图片生成失败[/bold red]")
    
    console.print("\n" + "=" * 50)
    console.print("[bold blue]🎉 任务圆满完成！[/bold blue]")

if __name__ == "__main__":
    main()
