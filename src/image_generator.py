"""
配图生成模块 - 基于阿里云百炼 wan2.7-image
参考 article-illustration 项目实现
"""

import base64
import os
import time
from pathlib import Path
from typing import Dict, Optional

import requests


STYLE_INSTRUCTIONS = (
    "画面要求：科技蓝色温暖风格，现代感、数字感、未来感，温暖亲和。"
    "蓝色主调，温暖、高端、专业。"
    "适合内容平台配图，横向或方形构图，画面干净，主体清晰。"
    "如果画面中有文字，必须使用中文。"
)


class ImageGenerator:
    """配图生成器"""

    def __init__(self, config, output_dir: Path):
        self.config = config
        self.api_key = config.aliyun_bailian_api_key
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self.async_headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
        }

        # API endpoints
        self.dashscope_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.image_gen_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image-generation/generation"

        # Models
        self.prompt_model = "qwen-max"
        self.image_model = "wan2.7-image-pro"

    def generate_images(self, article: Dict) -> Dict:
        """
        生成封面图和文中插图

        Args:
            article: 文章数据，包含 title, summary, content 等

        Returns:
            包含图片路径的字典
        """
        # 生成封面图 (1024x1024 - wan2.7 支持的尺寸)
        print("  生成封面图...")
        cover_prompt = self._generate_prompt(f"{article['title']} {article['summary'][:100]}")
        cover_path = self.output_dir / "cover.png"
        self._generate_single_image(cover_prompt, str(cover_path), "1024x1024")
        print(f"    封面图已保存: {cover_path}")

        # 生成文中插图 (1024x1024)
        print("  生成文中插图...")
        article_prompt = self._generate_prompt(article["content"][:300])
        article_image_path = self.output_dir / "article.png"
        self._generate_single_image(article_prompt, str(article_image_path), "1024x1024")
        print(f"    文中插图已保存: {article_image_path}")

        return {
            "cover_image": str(cover_path),
            "article_image": str(article_image_path)
        }

    def _generate_prompt(self, content: str) -> str:
        """使用 Qwen 模型生成图像提示词"""
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        context = "\n".join(paragraphs[:3])
        if len(context) > 2000:
            context = context[:2000].rsplit(" ", 1)[0]

        payload = {
            "model": self.prompt_model,
            "input": {
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个文章配图提示词专家。根据文章内容生成一段详细的英文图像生成提示词。",
                    },
                    {"role": "user", "content": f"{context}\n\n{STYLE_INSTRUCTIONS}"},
                ]
            },
        }

        resp = requests.post(self.dashscope_url, json=payload, headers=self.headers, timeout=120)
        resp.raise_for_status()
        data = resp.json()

        if data.get("code"):
            raise RuntimeError(f"Qwen API error: {data['code']} - {data.get('message', '')}")

        try:
            return data["output"]["text"].strip()
        except KeyError:
            raise RuntimeError(f"Unexpected Qwen response: {data}")

    def _generate_single_image(self, prompt: str, output_path: str, size: str = None) -> None:
        """生成单张图片"""
        payload = {
            "model": self.image_model,
            "input": {
                "messages": [
                    {"role": "user", "content": [{"text": prompt}]}
                ]
            },
            "parameters": {
                "size": size.replace("x", "*") if size else "1024*1024",
                "n": 1,
                "watermark": False,
            },
        }

        resp = requests.post(self.image_gen_url, json=payload, headers=self.async_headers, timeout=120)
        if resp.status_code != 200:
            raise RuntimeError(f"Image API error: {resp.status_code} - {resp.text[:500]}")

        data = resp.json()
        if data.get("code"):
            raise RuntimeError(f"Image gen API error: {data['code']} - {data.get('message', '')}")

        # 检查是否是同步返回
        if "output" in data and "results" in data["output"]:
            result = data["output"]["results"][0]
            if "url" in result:
                image_data = self._download_image(result["url"])
                Path(output_path).write_bytes(image_data)
                return

        # 异步模式，需要轮询
        task_id = data["output"]["task_id"]
        print(f"    Task ID: {task_id}")
        image_data = self._poll_result(task_id)
        Path(output_path).write_bytes(image_data)

    def _poll_result(self, task_id: str, max_wait: int = 120) -> bytes:
        """轮询图片生成结果"""
        status_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
        poll_interval = 3

        while max_wait > 0:
            resp = requests.get(status_url, headers={
                "Authorization": f"Bearer {self.api_key}",
            }, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            status = data.get("output", {}).get("task_status", "UNKNOWN")

            if status == "SUCCEEDED":
                # wan2.7-image-pro returns image in choices[0].message.content[0].image
                choices = data.get("output", {}).get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", [])
                    if content and isinstance(content, list):
                        for item in content:
                            if item.get("type") == "image" and item.get("image"):
                                return self._download_image(item["image"])
                raise RuntimeError(f"No image in response: {data}")
            elif status in ("FAILED", "CANCELED"):
                raise RuntimeError(f"Image task failed: {data}")

            max_wait -= poll_interval
            time.sleep(poll_interval)

        raise RuntimeError("Image generation timed out")

    @staticmethod
    def _download_image(url: str) -> bytes:
        """下载图片"""
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        return resp.content
