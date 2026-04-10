# 图片生成模块（ModelScope 版本）

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
        """根据评论生成 AI 绘画 Prompt（Qwen3-32B thinking版）"""
        try:
            prompt = (
                f"【新闻背景】\n{analysis[:500]}\n\n"
                f"以下是AI针对上述新闻生成的几条神评论：\n"
                f"{comment}\n\n"
                "【你的任务】\n"
                "1. 请从以上评论中挑选出最幽默的一条。\n"
                "2. 结合新闻背景，设计一个讽刺意味强烈的画面。\n"
                "3. 输出纯英文 AI 绘画 Prompt。\n"
                "4. 必须包含: detailed, 4k, satirical, cinematic lighting。\n\n"
                "【输出要求】\n"
                "只输出英文 Prompt，不要解释。"
            )

            response = self.llm_client.chat.completions.create(
                model="Qwen/Qwen3-32B",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                stream=False,  # ✅ 关键：关闭流式
                extra_body={
                    "enable_thinking": False
                }
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"[Prompt生成失败]: {e}")
            return (
                "A satirical digital art scene about politics and money, "
                "cinematic lighting, ultra detailed, 4k"
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
