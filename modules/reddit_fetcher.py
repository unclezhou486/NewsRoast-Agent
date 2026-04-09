import requests
from config import TAVILY_API_KEY # 假设你把 Tavily Key 也放在 .env 里

class RedditFetcher:
    def __init__(self):
        self.tavily_api_key = TAVILY_API_KEY
        self.hn_search_url = "https://hn.algolia.com/api/v1/search"

    def get_reference_comments(self, analysis):
        # 1. 联动提取：从 NewsAnalyzer 的结果中寻找 SEARCH_QUERY 标记
        query = self._extract_query_from_analysis(analysis)
        print(f"  [联动检索] 提取到的搜索词: {query}")

        if not query or len(query) < 3:
            return []

        # 2. 执行搜索 (Tavily 或 HN)
        if self.tavily_api_key:
            return self._fetch_via_tavily(query)
        return self._fetch_via_hn(query)

    def _extract_query_from_analysis(self, analysis):
        """解析 NewsAnalyzer 输出的特定标记内容"""
        try:
            if "SEARCH_QUERY:" in analysis:
                # 寻找标记后的内容
                query_part = analysis.split("SEARCH_QUERY:")[-1].strip()
                # 取第一行，防止后面有其他文字
                query = query_part.split('\n')[0].strip()
                print(query)
                return query
            
            # 兜底：如果 AI 没按格式写，取分析的前 50 个字符
            return analysis[:50].replace('\n', ' ')
        except Exception:
            return ""    
    
    def _fetch_via_tavily(self, query):
        """策略 A: 使用 Tavily 检索包含 Reddit 讨论的内容"""
        if not self.tavily_api_key:
            print("  [警告] 未配置 TAVILY_API_KEY，尝试切换到 HN...")
            return self._fetch_via_hn(query)

        url = "https://api.tavily.com/search"
        # 组合搜索词，限定在 reddit.com
        payload = {
            "api_key": self.tavily_api_key,
            "query": f"{query} site:reddit.com comments",
            "search_depth": "basic",
            "max_results": 5
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            results = response.json().get('results', [])
            
            ref_comments = []
            for res in results:
                ref_comments.append({
                    'text': res.get('content', '')[:500],
                    'score': "Tavily Search",
                    'url': res.get('url', '')
                })
            return ref_comments
        except Exception as e:
            print(f"  [Error] Tavily 搜索失败: {e}")
            return []

    def _fetch_via_hn(self, query):
        """策略 B: 使用 Hacker News Algolia API 获取评论"""
        params = {
            "query": query,
            "tags": "comment",
            "hitsPerPage": 5
        }
        try:
            response = requests.get(self.hn_search_url, params=params, timeout=10)
            hits = response.json().get('hits', [])
            
            ref_comments = []
            for hit in hits:
                text = hit.get('comment_text', '')
                # 清洗简单的 HTML 标签
                import re
                clean_text = re.sub('<[^<]+?>', '', text)
                ref_comments.append({
                    'text': clean_text[:500],
                    'score': hit.get('points', 0)
                })
            return ref_comments
        except Exception as e:
            print(f"  [Error] HN 检索失败: {e}")
            return []
