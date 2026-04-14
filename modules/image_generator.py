"""
异步视觉梗图生成模块
实现: .claude/skills/4_visual_prompt_designer.md 中的视觉提示设计专家要求

核心功能:
1. 视觉潜力评估: 从神评论列表中挑选最具视觉潜力的条目（通常最幽默或最讽刺）
2. 视觉隐喻转化: 应用视觉隐喻库将抽象矛盾转化为具体图像
   - 权力不平等 → 大小对比
   - 虚伪 → 两面脸
   - 循环重复 → 仓鼠轮
3. 专业AI绘画提示词工程: 生成结构完整的视觉Prompt

视觉Prompt结构:
- [主体描述] + [关键动作] + [环境背景] + [视觉风格] + [技术参数] + [情感导向]

风格匹配策略:
- 讽刺情绪 → 企业宣传画/政治漫画风格
- 愤怒情绪 → 讽刺漫画/抗议海报风格
- 幽默情绪 → 网络梗图/搞笑漫画风格
- 政治新闻 → 政治漫画/社论插图风格
- 科技新闻 → 科技美学/概念设计风格

技术方案:
- 异步轮询架构: 使用 `X-ModelScope-Async-Mode: true` 提交任务，通过 `/tasks/{task_id}` 轮询状态
- 避免HTTP超时: 支持长达2分钟的生成任务，提升系统稳定性
- 降级策略: 图像生成失败时返回默认提示，不中断流程
"""

import requests
import time
from openai import OpenAI
from config import IMAGE_API_KEY, IMAGE_BASE_URL, IMAGE_GEN_MODEL


class ImageGenerator:
    def __init__(self):
        # 用于生成 prompt 的 LLM（仍然走 ModelScope OpenAI 兼容接口）
        self.llm_client = OpenAI(
            api_key=IMAGE_API_KEY,
            base_url=IMAGE_BASE_URL
        )

        # ModelScope 图像接口
        self.base_url = IMAGE_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {IMAGE_API_KEY}",
            "Content-Type": "application/json",
        }

    def generate_image(self, comment, analysis):
        """为评论生成匹配图片"""
        try:
            # 1️⃣ 生成绘画 Prompt
            prompt = self._generate_image_prompt(comment, analysis)
            print(f"[生成的画图Prompt]: {prompt}")

            # 2️⃣ 提交生成任务
            response = requests.post(
                f"{self.base_url}/images/generations",
                headers={**self.headers, "X-ModelScope-Async-Mode": "true"},
                json={
                    "model": IMAGE_GEN_MODEL,
                    "prompt": prompt,
                    # "n": 1  # 可选：生成多张图
                }
            )
            response.raise_for_status()
            task_id = response.json()["task_id"]

            # 3️⃣ 轮询任务状态
            max_retry = 100
            for i in range(max_retry):
                result = requests.get(
                    f"{self.base_url}/tasks/{task_id}",
                    headers={**self.headers, "X-ModelScope-Task-Type": "image_generation"},
                )
                result.raise_for_status()
                data = result.json()

                print(f"[任务状态]: {data['task_status']} (第{i+1}次)")

                if data["task_status"] == "SUCCEED":
                    # ✅ 返回图片 URL
                    return data["output_images"][0]

                elif data["task_status"] == "FAILED":
                    print("[图片生成失败]")
                    return None

                time.sleep(5)

            print("[超时] 图片生成任务未完成")
            return None

        except Exception as e:
            print(f"[生成图片异常]: {e}")
            return None
    def _generate_image_prompt(self, comment, analysis):
        """根据评论生成专业的AI绘画提示词，遵循4_visual_prompt_designer.md中的结构"""
        try:
            prompt = (
                f"# 视觉提示设计专家任务\n\n"
                f"## 新闻背景\n{analysis[:500]}\n\n"
                f"## 神评论列表\n{comment}\n\n"
                f"## 你的任务\n"
                f"1. 从以上评论中挑选最具视觉潜力的一条（通常是最幽默或最讽刺的）\n"
                f"2. 基于该评论设计一个讽刺意味强烈的视觉概念\n"
                f"3. 生成专业的AI绘画提示词，必须包含以下6个组件：\n\n"
                f"   ### 组件结构\n"
                f"   1. **[主体描述]**：具体的人物/物体，特征夸张\n"
                f"   2. **[关键动作]**：象征性动作，体现核心矛盾\n"
                f"   3. **[环境背景]**：强化主题的场景设置\n"
                f"   4. **[视觉风格]**：企业宣传画/讽刺漫画/网络梗图等风格\n"
                f"   5. **[技术参数]**：构图、灯光、色彩、细节等技术要求\n"
                f"   6. **[情感导向]**：希望观众感受到的情绪\n\n"
                f"   ### 视觉隐喻参考\n"
                f"   - 权力不平等 → 大小对比、俯视/仰视角度\n"
                f"   - 虚伪/双标 → 两面脸、镜像反差、面具掉落\n"
                f"   - 循环重复 → 莫比乌斯环、仓鼠轮\n"
                f"   - 技术失控 → 机器人表情、代码溢出\n\n"
                f"## 输出要求\n"
                f"1. 输出纯英文的完整AI绘画提示词\n"
                f"2. 提示词必须自然流畅，不要用编号标记组件\n"
                f"3. 必须包含：detailed, 4k, satirical, cinematic lighting\n"
                f"4. 确保提示词能在Qwen-Image-2512等AI绘画模型中良好工作\n"
                f"5. 不要添加任何解释，只输出提示词本身\n\n"
                f"## 示例格式\n"
                f"\"A tired-looking consumer with three arms, each holding a different version of the same smartphone, standing in a never-ending queue that spirals into infinity. Corporate advertisement style mixed with surrealism. Cinematic lighting, vibrant but slightly off-putting colors, ultra-detailed. Satirical commentary on constant product updates and consumer fatigue.\""
            )

            response = self.llm_client.chat.completions.create(
                model="Qwen/Qwen3-32B",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                stream=False,
                extra_body={
                    "enable_thinking": False
                }
            )

            generated_prompt = response.choices[0].message.content.strip()

            # 验证生成的提示词质量
            if self._validate_image_prompt(generated_prompt):
                return generated_prompt
            else:
                print("[警告] 生成的提示词质量较低，使用备用提示词")
                return self._get_fallback_prompt(comment, analysis)

        except Exception as e:
            print(f"[Prompt生成失败]: {e}")
            return self._get_fallback_prompt(comment, analysis)

    def _validate_image_prompt(self, prompt):
        """验证生成的提示词质量"""
        # 基本验证：长度、关键词检查
        if len(prompt) < 50:
            return False

        # 检查是否包含必要关键词
        required_keywords = ["detailed", "4k", "cinematic"]
        for keyword in required_keywords:
            if keyword not in prompt.lower():
                return False

        # 检查是否包含视觉描述元素
        visual_descriptors = ["standing", "sitting", "holding", "wearing", "with", "in", "on", "against"]
        has_visual_description = any(desc in prompt.lower() for desc in visual_descriptors)

        return has_visual_description

    def _get_fallback_prompt(self, comment, analysis):
        """生成备用提示词"""
        # 提取评论中的关键词用于备用提示词
        import re
        keywords = re.findall(r'\b\w+\b', comment[:100])
        main_keywords = " ".join(keywords[:3]) if keywords else "politics and money"

        return (
            f"A satirical scene about {main_keywords}, "
            f"cinematic lighting, ultra detailed, 4k resolution, "
            f"corporate advertisement style mixed with political cartoon"
        )
    # def _generate_image_prompt(self, comment, analysis):
    #     """根据评论生成 AI 绘画 Prompt"""
    #     try:
    #         prompt = (
    #             f"【新闻背景】\n{analysis[:500]}\n\n"
    #             f"以下是AI针对上述新闻生成的几条神评论：\n"
    #             f"{comment}\n\n"
    #             "【你的任务】\n"
    #             "1. 请从以上评论中挑选出最幽默的一条。\n"
    #             "2. 结合新闻背景，设计一个讽刺意味强烈的画面。\n"
    #             "3. 输出纯英文 AI 绘画 Prompt。\n"
    #             "4. 必须包含: detailed, 4k, satirical, cinematic lighting。\n\n"
    #             "【输出要求】\n"
    #             "只输出英文 Prompt，不要解释。"
    #         )
    #
    #         response = self.llm_client.chat.completions.create(
    #             model='Qwen/Qwen3-32B',
    #             messages=[{"role": "user", "content": prompt}],
    #             temperature=0.7
    #         )
    #
    #         return response.choices[0].message.content.strip()
    #
    #     except Exception as e:
            # print(f"[Prompt生成失败]: {e}")
            # return (
            #     "A satirical digital art scene about politics and money, "
            #     "cinematic lighting, ultra detailed, 4k"
            # )
