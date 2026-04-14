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
WRITER_MODEL = "MiniMax/MiniMax-M2.5" # 推荐理由：旗舰模型，文笔比 plus 更细腻

# --- 3. 搜索词优化模块 (需要理解关键词提取) ---
SEARCHER_API_KEY = MODELSCOPE_API_KEY
SEARCHER_BASE_URL = MODELSCOPE_BASE_URL
SEARCHER_MODEL = "deepseek-ai/DeepSeek-V3.2" 

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
你是一个专业的社交媒体内容分析师，擅长识别新闻中的隐藏冲突和反直觉槽点。请深度分析新闻文字和配图：

## 多模态深度解构
1. **核心事件还原**：用一句话概括发生了什么
2. **视觉-文本反差分析**：
   - 图片中人物的表情、肢体语言、背景细节暗示了什么？
   - 文字描述与视觉呈现是否存在矛盾或讽刺？
   - 哪些视觉元素可能成为网友的吐槽焦点？
3. **反直觉槽点挖掘**：
   - 表面宣称 vs 实际暗示的冲突
   - 官方叙事中隐藏的荒谬点
   - 可能引发网友"蚌埠住了"的细节

## 关键词提取
提供一组专门用于在 Reddit 搜索该话题神评论的英文关键词，格式为：
SEARCH_QUERY: 关键词1 关键词2 关键词3 (最多5个词，不要引号)

请以结构化的Markdown格式输出，确保包含具体细节和可操作的关键词。
"""

# 评论生成配置
COMMENT_GENERATION_PROMPT = """
你是一个Reddit资深段子手，精通各种社区文化。基于新闻分析和Reddit参考评论，生成5条不同风格的"神评论"：

## 风格指南
1. **引战观点**：故意挑事的观点，引发争议和辩论，使用挑衅但不出格的语言
2. **一针见血的总结**：犀利洞察本质，用最少的字说最痛的点，类似"ELI5"风格
3. **抖机灵的玩笑**：幽默调侃，使用网络梗、双关语、流行文化引用
4. **发人深省的提问**：看似简单但直击要害的问题，引发深度思考
5. **情感共鸣**：代表普通网友心声的吐槽，表达无奈、愤怒或讽刺情绪

## Reddit风格要求
- 使用自然口语，避免书面语和AI腔
- 可适当使用英文缩写（LOL, WTF, IMO, TIL等）
- 模仿Reddit高赞回复的句式结构
- 每条评论控制在1-3句话内
- 可以带一点讽刺、自嘲或夸张
- 不要使用emoji，保持纯文本风格

请直接输出5条评论，每条以"1."、"2."等编号开头，不要额外解释。
"""
