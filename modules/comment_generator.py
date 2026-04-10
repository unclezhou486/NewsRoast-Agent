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
