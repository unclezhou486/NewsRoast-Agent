"""
多模态新闻分析模块
实现: .claude/skills/1_perception_expert.md 中的多模态感知专家要求

核心功能:
1. 视觉-文本反差分析框架: 表情/肢体语言解码、背景细节挖掘、色彩构图分析、图文一致性检查
2. 反直觉槽点挖掘策略: 官方叙事vs现实暗示、权力关系暴露、时代错位感、身份与行为反差
3. 社交媒体传播潜力评估: 梗图化可能性、情绪引爆点、争议性话题识别

工作流程:
- 第一层: 事实提取 (时间、地点、人物、事件、结果)
- 第二层: 多模态解构 (视觉元素对文字的强化/削弱作用)
- 第三层: 槽点识别 (按荒谬度和共鸣度排序)

输出规范: 结构化Markdown格式，包含SEARCH_QUERY关键词提取
"""

import requests
import base64
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from openai import OpenAI
from config import ANALYZER_API_KEY, ANALYZER_BASE_URL, NEWS_ANALYSIS_PROMPT, ANALYZER_MODEL


class NewsAnalyzer:
    def __init__(self):
        self.client = OpenAI(api_key=ANALYZER_API_KEY, base_url=ANALYZER_BASE_URL)
    
    def image_to_base64(self, url):
        try:
            res = requests.get(url, timeout=5)
            content_type = res.headers.get("Content-Type", "")
            
            if "image" not in content_type:
                return None, None
            
            img_base64 = base64.b64encode(res.content).decode("utf-8")
            
            # 提取格式，例如 image/png → png
            fmt = content_type.split("/")[-1]
            
            return img_base64, fmt
        except:
            return None, None
    def fetch_news_data(self, url):
        """同时获取新闻文字和图片链接"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 1. 提取文本
            paragraphs = [p.get_text() for p in soup.find_all('p')]
            text_content = "\n".join(paragraphs)[:3000]

            # 2. 提取图片 (尝试寻找正文大图)
            image_urls = []
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src')
                if src and ('.jpg' in src or '.png' in src or '.jpeg' in src):
                    # 过滤掉太小的图标或表情包
                    if 'avatar' not in src and 'logo' not in src:
                        full_url = urljoin(url, src)
                        image_urls.append(full_url)
                        if len(image_urls) >= 2: # 只取前两张主图，避免干扰
                            break
            
            return {"text": text_content, "images": image_urls}
        except Exception as e:
            print(f"抓取失败: {e}")
            return {"text": "", "images": []}

    def analyze_content(self, data):
        """多模态分析：文字 + 图片"""
        text = data["text"]
        images = data["images"]
        
        # 构建多模态消息格式
        content_list = [{"type": "text", "text": f"{NEWS_ANALYSIS_PROMPT}\n\n新闻文字内容：\n{text}"}]
        
        # 如果抓到了图片，就把图片传给模型
        if images:
            for img_url in images:
                img_base64, fmt = self.image_to_base64(img_url)

                if img_base64:
                    content_list.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/{fmt};base64,{img_base64}"}
                    })
            print(f"  [视觉触发] 已识别到 {len(images)} 张新闻配图，正在进行联合分析...")

        try:
            response = self.client.chat.completions.create(
                model=ANALYZER_MODEL,
                messages=[
                    {"role": "system", "content": "你是一个具备视觉理解能力的社交媒体专家，请结合文字和图片识别槽点。"},
                    {"role": "user", "content": content_list}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"多模态分析报错: {e}")
            return "分析失败"

    def process_news(self, url):
        data = self.fetch_news_data(url)
        if not data["text"]: return "无法读取内容"
        return self.analyze_content(data)
