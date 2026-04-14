"""
神评论风格化生成模块
实现: .claude/skills/3_god_comment_generator.md 中的神评论生成专家要求

核心功能:
1. 五种风格平行生成: 引战观点、一针见血的总结、抖机灵的玩笑、发人深省的提问、情感共鸣
2. Reddit语态建模: 使用自然口语、Reddit特有表达模式、英文缩写、社区句式结构
3. 去AI腔技术: 避免书面语和AI套话，模仿真实用户打字习惯

风格详解:
- 引战观点: 挑战主流共识，引发争议辩论，使用挑衅但不出格的语言
- 一针见血: 犀利洞察本质，用最少字数说最痛点，类似ELI5风格
- 抖机灵: 幽默调侃，使用网络梗、双关语、流行文化引用
- 发人深省: 看似简单但直击要害的问题，引发深度思考
- 情感共鸣: 代表普通网友心声，表达无奈、愤怒或讽刺情绪

创作约束:
- 每条评论1-3句话，短小精悍，冒犯感或幽默感十足
- 禁止超过500字符，禁止使用emoji
- 必须标注风格标识、目标受众、情绪基调、互动设计
"""

from openai import OpenAI
from config import WRITER_API_KEY, WRITER_BASE_URL, WRITER_MODEL, COMMENT_GENERATION_PROMPT

class CommentGenerator:
    def __init__(self):
        self.client = OpenAI(
            api_key=WRITER_API_KEY,
            base_url=WRITER_BASE_URL
        )
    
    def generate_comments(self, analysis, reference_comments):
        """生成神评论"""
        try:
            # 构建参考评论字符串
            reference_text = ""
            # 1. 增加对 reference_comments 的过滤，确保里面的元素不是 None 且是字典
            if reference_comments and isinstance(reference_comments, list):
                valid_comments = [c for c in reference_comments if c is not None and isinstance(c, dict)]
                
                if valid_comments:
                    reference_text = "以下是一些Reddit上的高赞评论作为灵感参考：\n"
                    for i, comment in enumerate(valid_comments[:5]):
                        # 2. 使用 .get('text') 替代 ['text']，更安全
                        text = comment.get('text', '（无评论内容）')
                        reference_text += f"{i+1}. {text}\n"

            prompt = f"{COMMENT_GENERATION_PROMPT}\n\n【新闻分析】\n{analysis}\n\n{reference_text}"
            
            response = self.client.chat.completions.create(
                model=WRITER_MODEL,
                messages=[
                    {"role": "system", "content": "你是一个擅长写神评论的社交媒体段子手，精通讽刺、幽默和引发共鸣的技巧。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8
            )

            # 3. 检查 response 和 choices 是否存在
            if response and response.choices:
                return response.choices[0].message.content
            else:
                return "生成评论失败：API未返回有效内容"
            
        except Exception as e:
            # 打印完整的错误栈方便定位
            import traceback
            print(f"生成评论失败: {e}")
            traceback.print_exc() 
            return "生成评论失败"
