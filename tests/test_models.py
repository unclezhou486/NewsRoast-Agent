"""
测试数据模型
"""
import pytest
from datetime import datetime
from models.data_models import (
    NewsAnalysis, RedditComment, GeneratedComment,
    CommentStyle, ImageGenerationRequest
)


class TestCommentStyle:
    """测试评论风格枚举"""

    def test_comment_style_values(self):
        """测试枚举值"""
        assert CommentStyle.CONTROVERSIAL == "引战观点"
        assert CommentStyle.RAZOR_SHARP == "一针见血的总结"
        assert CommentStyle.WITTY_JOKE == "抖机灵的玩笑"
        assert CommentStyle.THOUGHT_PROVOKING == "发人深省的提问"
        assert CommentStyle.EMOTIONAL_RESONANCE == "情感共鸣"

    def test_comment_style_iteration(self):
        """测试枚举可迭代"""
        styles = list(CommentStyle)
        assert len(styles) == 5
        assert all(isinstance(style, CommentStyle) for style in styles)


class TestNewsAnalysis:
    """测试新闻分析数据模型"""

    def test_news_analysis_creation(self):
        """测试创建新闻分析对象"""
        news = NewsAnalysis(
            url="https://example.com/news",
            text_content="这是一条测试新闻",
            image_urls=["https://example.com/image.jpg"],
            core_event="测试事件",
            visual_analysis=["图片显示..."],
            text_analysis=["文字分析..."],
            contrast_points=["反差点..."],
            cringe_points=[{"point": "槽点", "score": 8}],
            search_query="测试查询"
        )

        assert news.url == "https://example.com/news"
        assert news.text_content == "这是一条测试新闻"
        assert len(news.image_urls) == 1
        assert news.core_event == "测试事件"
        assert news.analysis_timestamp is not None
        assert isinstance(news.analysis_timestamp, datetime)

    def test_news_analysis_defaults(self):
        """测试默认值"""
        news = NewsAnalysis(
            url="https://example.com/news",
            text_content="测试",
            image_urls=[],
            core_event="事件",
            visual_analysis=[],
            text_analysis=[],
            contrast_points=[],
            cringe_points=[],
            search_query=""
        )

        assert news.analysis_timestamp is not None
        assert news.image_urls == []
        news.image_urls.append("new_url")
        # 验证列表是可变的
        assert len(news.image_urls) == 1


class TestRedditComment:
    """测试Reddit评论数据模型"""

    def test_reddit_comment_creation(self):
        """测试创建Reddit评论对象"""
        comment = RedditComment(
            text="这是一条有趣的评论",
            score="1.2k",
            source_url="https://reddit.com/r/test/comments/abc123",
            quality_score=85,
            style_category="幽默",
            emotion_tone="讽刺"
        )

        assert comment.text == "这是一条有趣的评论"
        assert comment.score == "1.2k"
        assert comment.source_url == "https://reddit.com/r/test/comments/abc123"
        assert comment.quality_score == 85
        assert comment.style_category == "幽默"
        assert comment.emotion_tone == "讽刺"

    def test_reddit_comment_optional_fields(self):
        """测试可选字段"""
        comment = RedditComment(
            text="评论内容",
            score="0",
            source_url="https://reddit.com"
        )

        assert comment.quality_score is None
        assert comment.style_category is None
        assert comment.emotion_tone is None


class TestGeneratedComment:
    """测试生成的评论数据模型"""

    def test_generated_comment_creation(self):
        """测试创建生成的评论对象"""
        comment = GeneratedComment(
            text="这是一条神评论",
            style=CommentStyle.CONTROVERSIAL,
            target_audience="科技爱好者",
            emotion_tone="挑衅",
            interaction_design="引发辩论"
        )

        assert comment.text == "这是一条神评论"
        assert comment.style == CommentStyle.CONTROVERSIAL
        assert comment.target_audience == "科技爱好者"
        assert comment.emotion_tone == "挑衅"
        assert comment.interaction_design == "引发辩论"

    def test_generated_comment_style_validation(self):
        """测试风格验证"""
        # 应该接受正确的枚举值
        comment = GeneratedComment(
            text="测试",
            style="引战观点",  # 字符串值应该被接受
            target_audience="",
            emotion_tone="",
            interaction_design=""
        )
        assert comment.style == "引战观点"


class TestImageGenerationRequest:
    """测试图像生成请求数据模型"""

    def test_image_generation_request_creation(self):
        """测试创建图像生成请求对象"""
        news = NewsAnalysis(
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

        comment = GeneratedComment(
            text="评论内容",
            style=CommentStyle.WITTY_JOKE,
            target_audience="",
            emotion_tone="",
            interaction_design=""
        )

        request = ImageGenerationRequest(
            comment=comment,
            news_analysis=news,
            visual_concept="视觉概念",
            prompt="绘画提示词"
        )

        assert request.comment == comment
        assert request.news_analysis == news
        assert request.visual_concept == "视觉概念"
        assert request.prompt == "绘画提示词"


if __name__ == "__main__":
    pytest.main([__file__])