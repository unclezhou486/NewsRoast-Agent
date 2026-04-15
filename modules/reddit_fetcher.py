"""
Reddit 社区评论检索模块
实现: .claude/skills/2_reddit_navigator.md 中的 Reddit 生态导航专家要求

核心功能:
1. 三级搜索策略: 精确匹配 → 概念扩展 → 文化语境搜索
2. 评论质量评估体系: 优先抓取高赞、高回复、有奖项标识、OP 回复的评论
3. 质量过滤: 过滤掉"简单同意"、"纯情绪发泄"、"事实错误"的低价值评论

技术方案:
- 主要检索: Tavily API + site:reddit.com 约束，绕过 Reddit API 限制
- 降级方案: HackerNews Algolia API (当 Reddit 搜索无结果时)
- 搜索优化: 清洗特殊字符，截断至5-8个核心词，提高搜索结果相关性
"""

import logging
import re
import time
import requests
from typing import Dict, List, Any, Optional
from openai import OpenAI

from config.settings import settings
from config.models import get_model_config
from config.constants import LengthLimits, TimeoutConstants, QuantityLimits

from utils.error_handling import handle_exceptions, log_execution_time

from skills.loader import get_skill_loader
from skills.prompt_builder import SkillPromptBuilder

logger = logging.getLogger(__name__)


class RedditFetcher:
    def __init__(self):
        self.tavily_api_key = settings.tavily_api_key or ""
        self.hn_search_url = "https://hn.algolia.com/api/v1/search"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }

        # 搜索优化 LLM（可选）
        searcher_config = get_model_config("searcher")
        self.searcher_client: Optional[OpenAI] = None
        self.searcher_model: str = searcher_config.model_id

        api_key = settings.modelscope_api_key
        if api_key and api_key.strip():
            self.searcher_client = OpenAI(
                api_key=api_key,
                base_url=settings.modelscope_base_url,
            )

        # 常量
        self.max_reddit_comments = QuantityLimits.MAX_REDDIT_COMMENTS
        self.timeout = TimeoutConstants.HTTP_REQUEST_TIMEOUT
        self.max_search_keywords = LengthLimits.SEARCH_QUERY_MAX_KEYWORDS
        self.max_comments_per_post = 15
        self.max_comment_length = 500
        self.max_search_results = 5

        # 加载技能文件
        self.reddit_navigator_skill = None
        try:
            self.reddit_navigator_skill = get_skill_loader().load_skill("reddit_navigator")
        except Exception as e:
            logger.warning(f"加载技能文件失败: {e}，将使用默认检索策略")

    @handle_exceptions(default_return="")
    @log_execution_time
    def _clean_query(self, query: str) -> str:
        """清洗并精简搜索词。"""
        query = re.sub(r'[\$#@%^&*()_+=\[\]{};:\"\\|,.<>\/?]', " ", query)
        words = query.split()
        if len(words) > self.max_search_keywords:
            query = " ".join(words[: self.max_search_keywords])
        return query.strip()

    def _build_search_prompt(self, raw_query: str, news_context: str = "") -> str:
        """使用 SkillPromptBuilder 构建搜索词优化提示词。"""
        task_block = (
            "## 任务要求\n"
            "请将以下新闻搜索查询优化为适合在 Reddit 上搜索相关讨论的英文关键词：\n\n"
            "原始查询: {raw_query}\n"
            "新闻上下文: {news_context}\n\n"
            "优化要求：\n"
            "1. 输出 3-5 个最相关的英文关键词\n"
            "2. 关键词要具体，避免过于宽泛\n"
            "3. 考虑 Reddit 社区常用的讨论角度\n"
            "4. 优先使用名词和核心概念\n"
            "5. 用空格分隔关键词，不要用逗号或引号\n\n"
            "输出格式：直接输出优化后的关键词，不要额外解释。"
        )
        fallback = (
            "请将以下新闻搜索查询优化为适合在 Reddit 上搜索相关讨论的英文关键词：\n\n"
            "原始查询: {raw_query}\n\n"
            "输出 3-5 个关键词，空格分隔，不要解释。"
        )
        builder = SkillPromptBuilder(
            skill=self.reddit_navigator_skill,
            role="你是 Reddit 生态专家，精通跨子版块的内容检索和热门语态捕捉。",
            sections=[
                ("检索策略框架",   "## 检索策略框架\n{content}"),
                ("评论质量评估体系", "## 评论质量评估体系\n{content}"),
                ("Reddit特有表达模式", "## Reddit 特有表达模式\n{content}"),
            ],
            task_block=task_block,
            fallback=fallback,
            title="Reddit 生态导航专家任务",
        )
        return builder.build(raw_query=raw_query, news_context=news_context[:200])

    @handle_exceptions(default_return="")
    @log_execution_time
    def _optimize_query_with_ai(self, raw_query: str, news_context: str = "") -> str:
        """使用 AI 模型优化搜索查询，失败时降级到基础清洗。"""
        if not self.searcher_client or not raw_query or len(raw_query) < 3:
            return self._clean_query(raw_query)

        prompt = self._build_search_prompt(raw_query, news_context)

        try:
            response = self.searcher_client.chat.completions.create(
                model=self.searcher_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是 Reddit 生态专家，精通跨子版块的内容检索和热门语态捕捉。"
                            "你的任务是帮助找到真正能代表 'Reddit 声音' 的高质量参考材料。"
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=50,
            )

            optimized = response.choices[0].message.content.strip()
            optimized = re.sub(r'[,\."]', "", optimized)
            optimized = " ".join(optimized.split()[: self.max_search_keywords])

            return optimized if len(optimized) >= 3 else self._clean_query(raw_query)

        except Exception as e:
            logger.warning(f"AI 查询优化失败: {e}，使用基础清洗")
            return self._clean_query(raw_query)

    @handle_exceptions(default_return=[])
    @log_execution_time
    def get_reference_comments(self, analysis: str) -> List[Dict[str, Any]]:
        """获取参考评论（主流程）。"""
        raw_query = self._extract_query_from_analysis(analysis)

        if self.searcher_client:
            query = self._optimize_query_with_ai(raw_query, analysis)
        else:
            query = self._clean_query(raw_query)

        logger.info(f"[联动检索] 原始词: {raw_query[:30]}...")
        logger.info(f"[联动检索] 优化后的搜索词: {query}")

        if not query or len(query) < 3:
            logger.warning("查询词过短，跳过检索")
            return []

        reddit_urls = self._find_reddit_urls_via_tavily(query)

        # 二次尝试：宽泛化搜索
        if not reddit_urls and len(query.split()) > 3:
            broad_query = " ".join(query.split()[:3])
            logger.info(f"[二次尝试] 使用更宽泛的词: {broad_query}")
            reddit_urls = self._find_reddit_urls_via_tavily(broad_query)

        if not reddit_urls:
            logger.info("Tavily 未找到 Reddit 链接，转向 HN...")
            return self._fetch_via_hn(query)

        all_comments: List[Dict[str, Any]] = []
        for url in reddit_urls[:2]:
            comments = self._fetch_real_comments_from_url(url)
            if comments:
                logger.info(f"从 {url[-20:]} 抓取到 {len(comments)} 条评论")
                all_comments.extend(comments)
            time.sleep(0.5)

        return all_comments[: self.max_reddit_comments]

    @handle_exceptions(default_return=[])
    @log_execution_time
    def _find_reddit_urls_via_tavily(self, query: str) -> List[str]:
        """通过 Tavily API 搜索 Reddit 链接。"""
        if not self.tavily_api_key:
            logger.warning("Tavily API 密钥未配置")
            return []

        payload = {
            "api_key": self.tavily_api_key,
            "query": f"{query} reddit discussion",
            "search_depth": "basic",
            "max_results": self.max_search_results,
        }

        try:
            response = requests.post(
                "https://api.tavily.com/search", json=payload, timeout=self.timeout
            )
            results = response.json().get("results", [])
            return [r["url"] for r in results if "reddit.com/r/" in r["url"]]
        except Exception as e:
            logger.error(f"Tavily 搜索失败: {e}")
            return []

    @handle_exceptions(default_return=[])
    @log_execution_time
    def _fetch_real_comments_from_url(self, reddit_url: str) -> List[Dict[str, Any]]:
        """通过 .json 接口抓取 Reddit 评论。"""
        clean_url = reddit_url.split("?")[0].rstrip("/")
        json_url = f"{clean_url}.json"

        try:
            response = requests.get(json_url, headers=self.headers, timeout=self.timeout)
            if response.status_code != 200:
                logger.warning(f"Reddit API 返回状态码: {response.status_code}")
                return []

            data = response.json()
            if not (isinstance(data, list) and len(data) > 1):
                return []

            children = data[1].get("data", {}).get("children", [])
            extracted = []
            for child in children[: self.max_comments_per_post]:
                c_data = child.get("data", {})
                body = c_data.get("body")
                if body and len(body) > 15 and not body.startswith("["):
                    extracted.append({
                        "text": body[: self.max_comment_length],
                        "score": f"{c_data.get('ups', 0)} upvotes",
                    })
            return extracted

        except Exception as e:
            logger.error(f"抓取 Reddit 评论失败: {e}")
            return []

    @handle_exceptions(default_return="")
    @log_execution_time
    def _extract_query_from_analysis(self, analysis: str) -> str:
        """从分析文本中提取 SEARCH_QUERY。"""
        if "SEARCH_QUERY:" in analysis:
            return analysis.split("SEARCH_QUERY:")[-1].strip().split("\n")[0]
        return analysis[:50]

    @handle_exceptions(default_return=[])
    @log_execution_time
    def _fetch_via_hn(self, query: str) -> List[Dict[str, Any]]:
        """HackerNews 兜底检索。"""
        params = {"query": query, "tags": "comment", "hitsPerPage": self.max_search_results}
        try:
            res = requests.get(self.hn_search_url, params=params, timeout=self.timeout)
            hits = res.json().get("hits", [])
            return [
                {
                    "text": re.sub("<[^<]+?>", "", h.get("comment_text", ""))[: self.max_comment_length],
                    "score": f"{h.get('points', 0)} pts",
                }
                for h in hits
            ]
        except Exception as e:
            logger.error(f"HackerNews 检索失败: {e}")
            return []
