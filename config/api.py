"""
NewsRoast-Agent API 配置

统一管理所有外部API的基础URL、端点和请求配置。
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class APIConfig:
    """API配置数据类"""
    base_url: str
    endpoints: Dict[str, str]
    default_headers: Dict[str, str]
    timeout: int


# ==========================================
# 📡 ModelScope API 配置
# ==========================================

MODELSCOPE_CONFIG = APIConfig(
    base_url="https://api-inference.modelscope.cn/v1",
    endpoints={
        "chat_completion": "/chat/completions",
        "image_generation": "/images/generations",
        "task_status": "/tasks/{task_id}",
    },
    default_headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
    },
    timeout=30
)


# ==========================================
# 🌐 阿里云灵积增强接口配置
# ==========================================

ALIYUN_ENHANCED_CONFIG = APIConfig(
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    endpoints={
        "chat_completion": "/chat/completions",
        "image_generation": "/images/generations",
    },
    default_headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
    },
    timeout=30
)


# ==========================================
# 🔍 Tavily 搜索 API 配置
# ==========================================

TAVILY_CONFIG = APIConfig(
    base_url="https://api.tavily.com",
    endpoints={
        "search": "/search",
    },
    default_headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
    },
    timeout=30
)


# ==========================================
# 📱 Reddit API 配置
# ==========================================

REDDIT_CONFIG = APIConfig(
    base_url="https://oauth.reddit.com",
    endpoints={
        "search": "/search",
        "hot": "/hot",
        "new": "/new",
        "comments": "/r/{subreddit}/comments/{article_id}",
    },
    default_headers={
        "User-Agent": "News Comment Agent by /u/example_user",
        "Content-Type": "application/json",
    },
    timeout=30
)


# ==========================================
# 🧠 HackerNews API 配置 (降级方案)
# ==========================================

HACKERNEWS_CONFIG = APIConfig(
    base_url="https://hn.algolia.com/api/v1",
    endpoints={
        "search": "/search",
    },
    default_headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
    },
    timeout=30
)


# ==========================================
# 🎯 API 配置映射
# ==========================================

API_CONFIG = {
    "modelscope": MODELSCOPE_CONFIG,
    "aliyun": ALIYUN_ENHANCED_CONFIG,
    "tavily": TAVILY_CONFIG,
    "reddit": REDDIT_CONFIG,
    "hackernews": HACKERNEWS_CONFIG,
}


def get_api_config(api_name: str) -> APIConfig:
    """获取指定API的配置"""
    if api_name not in API_CONFIG:
        raise ValueError(f"未知的API配置: {api_name}")
    return API_CONFIG[api_name]