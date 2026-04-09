# 配置文件
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ==========================================
# 🔑 API KEY 统一管理区
# ==========================================
# 阿里云百炼 (通义千问/通义万相)
MODELSCOPE_API_KEY = os.getenv('MODELSCOPE_API_KEY', '')
MODELSCOPE_BASE_URL = "https://api-inference.modelscope.cn/v1"

# 搜索增强 API (Tavily)
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY', '')

ALIYUN_API_KEY = os.getenv('ALIYUN_API_KEY', '')
ALIYUN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


# OpenAI 官方 (备用)
# OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# 硅基流动 SiliconFlow (适合白嫖 Flux 或其他开源大模型)
# SILICONFLOW_API_KEY = os.getenv('SILICONFLOW_API_KEY', '')


# ==========================================
# 🤖 模块化模型配置 (你可以为每个环节指定不同 AI)
# ==========================================

# --- 1. 新闻分析模块 (需要强大的 Vision 视觉能力) ---
# 默认使用阿里云百炼增强接口
ANALYZER_API_KEY = MODELSCOPE_API_KEY
ANALYZER_BASE_URL = MODELSCOPE_BASE_URL
ANALYZER_MODEL = "Qwen/Qwen3.5-35B-A3B" # 推荐理由：视觉理解力强，且支持公网 URL

# --- 2. 评论生成模块 (需要极强的“网感”和幽默感) ---
# 你可以预留给像 Claude 或者 Qwen-Max 这种逻辑更强的模型
WRITER_API_KEY = MODELSCOPE_API_KEY
WRITER_BASE_URL = MODELSCOPE_BASE_URL
WRITER_MODEL = "Qwen/Qwen3.5-27B" # 推荐理由：旗舰模型，文笔比 plus 更细腻

# --- 3. 搜索词优化模块 (需要理解关键词提取) ---
# 这个环节可以用响应最快、最便宜的模型
SEARCHER_API_KEY = ALIYUN_API_KEY
SEARCHER_BASE_URL = ALIYUN_BASE_URL
SEARCHER_MODEL = "qwen-turbo" # 推荐理由：快且省钱

# --- 4. 图像生成模块 (决定了最后的梗图质量) ---
# 默认使用通义万相 WanX
IMAGE_API_KEY = MODELSCOPE_API_KEY
IMAGE_BASE_URL = MODELSCOPE_BASE_URL
IMAGE_GEN_MODEL = "Qwen/Qwen-Image-2512" 

# ModelScope API 配置
# MODELSCOPE_API_KEY = os.getenv('MODELSCOPE_API_KEY', '')
# # ModelScope 的 OpenAI 兼容接口地址
# MODELSCOPE_BASE_URL = "https://api-inference.modelscope.cn/v1"
# # 指定使用的 ModelScope 文本模型 (通义千问2.5-72B)
# LLM_MODEL = "Qwen/Qwen2.5-72B-Instruct"

# 使用阿里云百炼(DashScope)的增强版兼容接口，这是目前魔搭生态最稳定、速度最快的接口
# MODELSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# 使用 "qwen-plus" (通义千问增强版) 或 "qwen-max" (千问旗舰版)。
# 这里推荐使用 qwen-plus，它的智商极高，而且完全兼容这套接口
# LLM_MODEL = "qwen-plus"

# Reddit API 配置
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID', '')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET', '')
REDDIT_USER_AGENT = 'News Comment Agent by /u/example_user'

TAVILY_API_KEY = os.getenv('TAVILY_API_KEY', '')

# 系统配置
MAX_REDDIT_COMMENTS = 10
MAX_GENERATED_COMMENTS = 5

# 新闻分析配置
# NEWS_ANALYSIS_PROMPT = """
# 请作为【深度内容分析agent】，同时审视新闻文字和配图：
# 1. **核心要点**：一句话总结发生了什么。
# 2. **多模态解读**：
#    - 文字里隐藏了什么槽点？
#    - 图片里有什么视觉暗示？（比如人物的神情、背景的讽刺感、图表的变化）
#    - 图片与文字结合后，是否产生了额外的反差感或讽刺点？
# 3. **识别槽点与争议**：哪些点最能引发网友“互喷”或“狂赞”？
# 4. **搜索关键词**：SEARCH_QUERY: 提取 3 个最适合搜 Reddit 神评论的英文词。
#
# 请以 Markdown 格式输出。
# """
NEWS_ANALYSIS_PROMPT = """
请作为【深度内容分析agent】，同时审视新闻文字和配图，分析以下新闻内容，提取：
1. 核心事件和要点
2. 可能的笑点或槽点
3. 核心观点和潜在争议点
4. 关键实体（人物、公司、产品等）
5. 【重要】请提供一组专门用于在 Reddit 搜索该话题神评论的英文关键词，格式为：SEARCH_QUERY: 关键词1 关键词2...(不要有双引号,方便进行匹配)

请以结构化的方式输出分析结果，并严格遵守格式。
"""

# 评论生成配置
COMMENT_GENERATION_PROMPT = """
基于以下新闻分析和Reddit参考评论，生成5条不同风格的神评论：
1. 引战观点
2. 一针见血的总结
3. 抖机灵的玩笑
4. 发人深省的提问
5. 情感共鸣

每条评论要：
- 紧扣新闻内容
- 有独特视角
- 能激发用户互动
- 语言风格符合对应类型
- 纯文本输出，不要多余的寒暄
"""
