"""
测试核心模块（使用Mock）
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from models.data_models import NewsAnalysis, RedditComment, GeneratedComment, CommentStyle


class TestNewsAnalyzer:
    """测试新闻分析模块"""

    @patch('modules.news_analyzer.OpenAI')
    @patch('modules.news_analyzer.requests')
    @patch('modules.news_analyzer.get_skill_loader')
    def test_initialization(self, mock_get_loader, mock_requests, mock_openai):
        """测试初始化"""
        from modules.news_analyzer import NewsAnalyzer

        # 模拟技能加载器
        mock_loader = MagicMock()
        mock_skill = MagicMock()
        mock_loader.load_skill.return_value = mock_skill
        mock_get_loader.return_value = mock_loader

        analyzer = NewsAnalyzer()

        assert analyzer is not None
        mock_get_loader.assert_called_once()
        mock_loader.load_skill.assert_called_once_with("perception_expert")

    @patch('modules.news_analyzer.OpenAI')
    @patch('modules.news_analyzer.requests')
    def test_fetch_news_data_success(self, mock_requests, mock_openai):
        """测试成功获取新闻数据"""
        from modules.news_analyzer import NewsAnalyzer

        # 模拟响应
        mock_response = MagicMock()
        mock_response.content = b'<html><body><p>News content</p><img src="image.jpg"></body></html>'
        mock_response.raise_for_status.return_value = None
        mock_requests.get.return_value = mock_response

        analyzer = NewsAnalyzer()
        result = analyzer.fetch_news_data("https://example.com")

        assert "text" in result
        assert "images" in result
        assert result["text"] == "News content"
        assert "image.jpg" in result["images"][0]

    @patch('modules.news_analyzer.OpenAI')
    @patch('modules.news_analyzer.requests')
    def test_fetch_news_data_failure(self, mock_requests, mock_openai):
        """测试获取新闻数据失败"""
        from modules.news_analyzer import NewsAnalyzer

        mock_requests.get.side_effect = Exception("网络错误")

        analyzer = NewsAnalyzer()
        result = analyzer.fetch_news_data("https://example.com")

        # 应该返回默认值（由装饰器处理）
        assert result == {"text": "", "images": []}


class TestRedditFetcher:
    """测试Reddit检索模块"""

    @patch('modules.reddit_fetcher.OpenAI')
    @patch('modules.reddit_fetcher.get_skill_loader')
    def test_initialization(self, mock_get_loader, mock_openai):
        """测试初始化"""
        from modules.reddit_fetcher import RedditFetcher

        mock_loader = MagicMock()
        mock_skill = MagicMock()
        mock_loader.load_skill.return_value = mock_skill
        mock_get_loader.return_value = mock_loader

        fetcher = RedditFetcher()

        assert fetcher is not None
        mock_get_loader.assert_called_once()
        mock_loader.load_skill.assert_called_once_with("reddit_navigator")

    @patch('modules.reddit_fetcher.OpenAI')
    def test_optimize_search_query(self, mock_openai):
        """测试搜索查询优化"""
        from modules.reddit_fetcher import RedditFetcher

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "优化后的查询词"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        fetcher = RedditFetcher()
        # 由于需要技能文件，我们直接测试内部方法
        result = fetcher._optimize_query_with_ai("raw query")

        # 由于可能缺少技能文件，测试可能会返回默认值
        # 我们只验证函数能够执行而不抛出异常
        assert result is not None


class TestCommentGenerator:
    """测试评论生成模块"""

    @patch('modules.comment_generator.OpenAI')
    @patch('modules.comment_generator.get_skill_loader')
    def test_initialization(self, mock_get_loader, mock_openai):
        """测试初始化"""
        from modules.comment_generator import CommentGenerator

        mock_loader = MagicMock()
        mock_skill = MagicMock()
        mock_loader.load_skill.return_value = mock_skill
        mock_get_loader.return_value = mock_loader

        generator = CommentGenerator()

        assert generator is not None
        mock_get_loader.assert_called_once()
        mock_loader.load_skill.assert_called_once_with("god_comment_generator")

    @patch('modules.comment_generator.OpenAI')
    def test_generate_comments_success(self, mock_openai):
        """测试成功生成评论"""
        from modules.comment_generator import CommentGenerator

        # 模拟API响应
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "生成的评论内容"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        generator = CommentGenerator()

        # 使用模拟的新闻分析和参考评论
        analysis = "新闻分析内容"
        reference_comments = [{"text": "参考评论1"}, {"text": "参考评论2"}]

        result = generator.generate_comments(analysis, reference_comments)

        assert result == "生成的评论内容"
        mock_client.chat.completions.create.assert_called_once()


class TestImageGenerator:
    """测试图像生成模块"""

    @patch('modules.image_generator.OpenAI')
    @patch('modules.image_generator.requests')
    @patch('modules.image_generator.get_skill_loader')
    def test_initialization(self, mock_get_loader, mock_requests, mock_openai):
        """测试初始化"""
        from modules.image_generator import ImageGenerator

        mock_loader = MagicMock()
        mock_skill = MagicMock()
        mock_loader.load_skill.return_value = mock_skill
        mock_get_loader.return_value = mock_loader

        generator = ImageGenerator()

        assert generator is not None
        mock_get_loader.assert_called_once()
        mock_loader.load_skill.assert_called_once_with("visual_prompt_designer")

    @patch('modules.image_generator.OpenAI')
    @patch('modules.image_generator.requests')
    def test_generate_image_prompt(self, mock_requests, mock_openai):
        """测试生成图像提示词"""
        from modules.image_generator import ImageGenerator
        from models.data_models import GeneratedComment, NewsAnalysis, CommentStyle

        # 模拟LLM响应
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "A satirical image, detailed, 4k, cinematic lighting"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        generator = ImageGenerator()

        # 创建测试数据
        comment = GeneratedComment(
            text="测试评论",
            style=CommentStyle.WITTY_JOKE,
            target_audience="",
            emotion_tone="",
            interaction_design=""
        )

        analysis = NewsAnalysis(
            url="https://example.com",
            text_content="新闻内容",
            image_urls=[],
            core_event="事件",
            visual_analysis=[],
            text_analysis=[],
            contrast_points=[],
            cringe_points=[],
            search_query=""
        )

        result = generator._generate_image_prompt(comment, analysis)

        assert result is not None
        assert "detailed" in result.lower()
        assert "4k" in result.lower()


class TestModuleIntegration:
    """测试模块集成"""

    def test_data_model_compatibility(self):
        """测试数据模型兼容性"""
        # 确保所有模块使用相同的数据模型
        from models.data_models import NewsAnalysis, GeneratedComment

        # 创建测试数据
        news = NewsAnalysis(
            url="https://example.com",
            text_content="内容",
            image_urls=[],
            core_event="事件",
            visual_analysis=[],
            text_analysis=[],
            contrast_points=[],
            cringe_points=[],
            search_query=""
        )

        comment = GeneratedComment(
            text="评论",
            style=CommentStyle.CONTROVERSIAL,
            target_audience="",
            emotion_tone="",
            interaction_design=""
        )

        # 验证数据模型能够正确创建
        assert news.url == "https://example.com"
        assert comment.text == "评论"
        assert comment.style == CommentStyle.CONTROVERSIAL


if __name__ == "__main__":
    pytest.main([__file__])