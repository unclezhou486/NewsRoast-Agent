"""
Reddit社区评论检索模块
实现: .claude/skills/2_reddit_navigator.md 中的Reddit生态导航专家要求

核心功能:
1. 三级搜索策略: 精确匹配 → 概念扩展 → 文化语境搜索
2. 评论质量评估体系: 优先抓取高赞、高回复、有奖项标识、OP回复的评论
3. 质量过滤: 过滤掉"简单同意"、"纯情绪发泄"、"事实错误"的低价值评论

技术方案:
- 主要检索: Tavily API + `site:reddit.com` 约束，绕过Reddit API限制
- 降级方案: HackerNews Algolia API (当Reddit搜索无结果时)
- 搜索优化: 清洗特殊字符，截断至5-8个核心词，提高搜索结果相关性

输出规范: 结构化JSON包含评论文本、赞数、质量分数、风格分类、关键短语、情绪基调
"""

import requests
import re
import time
from config import TAVILY_API_KEY, SEARCHER_API_KEY, SEARCHER_BASE_URL, SEARCHER_MODEL
from openai import OpenAI

class RedditFetcher:
    def __init__(self):
        self.tavily_api_key = TAVILY_API_KEY
        self.hn_search_url = "https://hn.algolia.com/api/v1/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        # 初始化搜索优化客户端（如果API密钥可用）
        self.searcher_client = None
        if SEARCHER_API_KEY and SEARCHER_API_KEY.strip():
            try:
                self.searcher_client = OpenAI(
                    api_key=SEARCHER_API_KEY,
                    base_url=SEARCHER_BASE_URL
                )
                print(f"  [搜索优化] 已启用AI搜索查询优化，使用模型: {SEARCHER_MODEL}")
            except Exception as e:
                print(f"  [搜索优化] 初始化失败: {e}，将使用基础清洗方法")

    def _clean_query(self, query):
        """核心改进：清洗并精简搜索词"""
        # 1. 移除特殊字符和过长的停用词
        query = re.sub(r'[\$#@%^&*()_+=\[\]{};:\"\\|,.<>\/?]', ' ', query)
        # 2. 只保留前 5-8 个核心关键词（搜索词越长，结果越少）
        words = query.split()
        if len(words) > 6:
            # 优先提取前几个词，通常是新闻的主体
            query = " ".join(words[:6])
        return query.strip()

    def _optimize_query_with_ai(self, raw_query, news_context=""):
        """使用AI模型优化搜索查询，返回更适合Reddit搜索的查询词"""
        if not self.searcher_client or not raw_query or len(raw_query) < 3:
            return self._clean_query(raw_query)

        try:
            prompt = f"""
            请将以下新闻搜索查询优化为适合在Reddit上搜索相关讨论的英文关键词：

            原始查询: {raw_query}

            优化要求：
            1. 输出3-5个最相关的英文关键词
            2. 关键词要具体，避免过于宽泛
            3. 考虑Reddit社区常用的讨论角度
            4. 优先使用名词和核心概念
            5. 用空格分隔关键词，不要用逗号或引号

            示例：
            输入: "Apple gets tariff exemption from Trump"
            输出: "Apple Trump tariff exemption"

            输出格式：直接输出优化后的关键词，不要额外解释。
            """

            response = self.searcher_client.chat.completions.create(
                model=SEARCHER_MODEL,
                messages=[
                    {"role": "system", "content": "你是搜索查询优化专家，擅长将新闻话题转化为适合社交媒体搜索的关键词。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=50
            )

            optimized_query = response.choices[0].message.content.strip()

            # 清理响应，确保只保留关键词
            optimized_query = re.sub(r'[,\."]', '', optimized_query)
            optimized_query = ' '.join(optimized_query.split()[:6])  # 限制长度

            if optimized_query and len(optimized_query) >= 3:
                print(f"  [AI优化] 原始: '{raw_query[:30]}...' → 优化: '{optimized_query}'")
                return optimized_query
            else:
                return self._clean_query(raw_query)

        except Exception as e:
            print(f"  [AI优化] 失败: {e}，使用基础清洗")
            return self._clean_query(raw_query)

    def get_reference_comments(self, analysis):
        # 1. 提取原始 query
        raw_query = self._extract_query_from_analysis(analysis)

        # 2. 优化查询：优先使用AI优化，失败时使用基础清洗
        if self.searcher_client:
            query = self._optimize_query_with_ai(raw_query, analysis)
        else:
            query = self._clean_query(raw_query)

        print(f"  [联动检索] 原始词: {raw_query[:30]}...")
        print(f"  [联动检索] 优化后的搜索词: {query}")

        if not query or len(query) < 3:
            return []

        # 尝试获取 Reddit 链接
        reddit_urls = self._find_reddit_urls_via_tavily(query)
        
        # 如果第一次没搜到，尝试更宽泛的词（取前3个词）
        if not reddit_urls and len(query.split()) > 3:
            broad_query = " ".join(query.split()[:3])
            print(f"  [二次尝试] 使用更宽泛的词: {broad_query}")
            reddit_urls = self._find_reddit_urls_via_tavily(broad_query)

        if not reddit_urls:
            print("  [提示] Tavily 依然未找到 Reddit 链接，转向 HN...")
            return self._fetch_via_hn(query)

        # 抓取评论
        all_real_comments = []
        for url in reddit_urls[:2]:
            comments = self._fetch_real_comments_from_url(url)
            if comments:
                print(f"  [成功] 从 {url[-20:]} 抓取到 {len(comments)} 条评论")
                all_real_comments.extend(comments)
            time.sleep(0.5)

        return all_real_comments[:10]

    def _find_reddit_urls_via_tavily(self, query):
        if not self.tavily_api_key: return []
        url = "https://api.tavily.com/search"
        # 搜索策略：加上 "discussion" 或 "comments" 能更容易搜到帖子而非新闻稿
        payload = {
            "api_key": self.tavily_api_key,
            "query": f"{query} reddit discussion",
            "search_depth": "basic",
            "max_results": 5
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            results = response.json().get('results', [])
            # 只要链接里包含 reddit.com/r/ 就算
            return [res['url'] for res in results if 'reddit.com/r/' in res['url']]
        except Exception as e:
            print(f"  [Error] Tavily 搜索失败: {e}")
            return []

    def _fetch_real_comments_from_url(self, reddit_url):
        """通过 .json 接口抓取"""
        try:
            # 规范化 URL，去掉末尾斜线并加 .json
            clean_url = reddit_url.split('?')[0].rstrip('/')
            json_url = f"{clean_url}.json"
            
            # 这里必须加 timeout 和合理的 headers
            response = requests.get(json_url, headers=self.headers, timeout=8)
            if response.status_code != 200:
                return []

            data = response.json()
            # Reddit 的 JSON 结构很深
            if isinstance(data, list) and len(data) > 1:
                children = data[1].get('data', {}).get('children', [])
                extracted = []
                for child in children[:15]:
                    c_data = child.get('data', {})
                    body = c_data.get('body')
                    if body and len(body) > 15 and not body.startswith("["):
                        extracted.append({
                            'text': body[:500],
                            'score': f"{c_data.get('ups', 0)} upvotes"
                        })
                return extracted
        except Exception:
            return []
        return []

    def _extract_query_from_analysis(self, analysis):
        try:
            if "SEARCH_QUERY:" in analysis:
                query = analysis.split("SEARCH_QUERY:")[-1].strip().split('\n')[0]
                return query
            return analysis[:50]
        except:
            return ""

    def _fetch_via_hn(self, query):
        """Hacker News 兜底"""
        params = {"query": query, "tags": "comment", "hitsPerPage": 5}
        try:
            res = requests.get(self.hn_search_url, params=params, timeout=8)
            hits = res.json().get('hits', [])
            return [{'text': re.sub('<[^<]+?>', '', h.get('comment_text', ''))[:500], 
                     'score': f"{h.get('points', 0)} pts"} for h in hits]
        except:
            return []
