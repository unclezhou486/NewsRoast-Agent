# 评论生成模块
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
            if reference_comments:
                reference_text = "以下是一些Reddit上的高赞评论作为灵感参考：\n"
                for i, comment in enumerate(reference_comments[:5]):
                    reference_text += f"{i+1}. {comment['text']}\n"
            # print(reference_text)
            prompt = f"{COMMENT_GENERATION_PROMPT}\n\n【新闻分析】\n{analysis}\n\n{reference_text}"
            
            response = self.client.chat.completions.create(
                model=WRITER_MODEL,
                messages=[
                    {"role": "system", "content": "你是一个擅长写神评论的社交媒体段子手，精通讽刺、幽默和引发共鸣的技巧。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8 # 稍微调高点，让评论更有创意
            )
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"生成评论失败: {e}")
            return "生成评论失败"
