"""
内容生成模块 - 使用 MiniMax 生成文章
"""

import requests
from typing import Dict


class ContentGenerator:
    """文章生成器"""

    SYSTEM_PROMPT = """你是一位专业的科技博主，擅长深度解读 AI 领域的热点新闻和技术趋势。

写作风格：
- 标题：简洁有力，吸引眼球
- 摘要：用 1-2 句话概括新闻要点
- 正文：深度分析，300 字以内，包含背景、核心进展、影响和展望
- 语言：专业但易懂，适合科技爱好者阅读

输出格式：
- 标题：[一句话标题]
- 摘要：[1-2句新闻简报]
- 正文：[深度分析文章]

注意：
- 只输出 Markdown 格式内容，不要额外的解释
- 文章要原创，有自己的观点和见解
- 控制在 300 字以内"""

    USER_PROMPT_TEMPLATE = """请根据以下热点新闻，生成一篇深度解读文章：

热点标题：{title}
来源：{source}
发布时间：{publish_date}
内容摘要：{snippet}
参考链接：{url}

要求：
1. 标题简洁有力
2. 先写 1-2 句新闻简报作为摘要
3. 然后写深度分析正文
4. 控制总字数在 300 字以内"""

    def __init__(self, config):
        self.config = config
        self.api_key = config.minimax_api_key
        self.model = config.minimax_model
        # MiniMax Anthropic 兼容 API
        self.api_url = "https://api.minimaxi.com/anthropic/v1/messages"

    def generate_article(self, hotspot) -> Dict:
        """
        生成文章

        Args:
            hotspot: Hotspot 对象

        Returns:
            包含 title, summary, content, word_count, reference_url 的字典
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            title=hotspot.title,
            source=hotspot.source,
            publish_date=hotspot.publish_date,
            snippet=hotspot.snippet,
            url=hotspot.url
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 2000,
            "temperature": 0.7
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            # MiniMax Anthropic 兼容格式：content 是数组，包含 thinking 和 text
            article_text = ""
            for item in data.get("content", []):
                if item.get("type") == "text":
                    article_text = item.get("text", "")
                    break

            if not article_text:
                # fallback
                article_text = data.get("response", "")

            return self._parse_article(article_text, hotspot.url, hotspot.title)

        except Exception as e:
            print(f"MiniMax API 调用失败: {e}")
            # 返回一个默认结构
            return self._create_fallback_article(hotspot)

    def _parse_article(self, text: str, reference_url: str, fallback_title: str) -> Dict:
        """解析生成的文章"""
        lines = text.split("\n")

        article = {
            "title": fallback_title,
            "summary": "",
            "content": text,
            "word_count": len(text),
            "reference_url": reference_url,
            "raw_markdown": text
        }

        # 解析标题和摘要
        for line in lines:
            line = line.strip()
            if line.startswith("标题："):
                article["title"] = line.replace("标题：", "").strip()
            elif line.startswith("# "):
                article["title"] = line.replace("# ", "").strip()
            elif line.startswith("摘要："):
                article["summary"] = line.replace("摘要：", "").strip()
            elif line.startswith("## "):
                article["summary"] = line.replace("## ", "").strip()

        # 计算纯文本字数
        content_only = text.replace("#", "").replace("*", "").replace("\n", "").replace(" ", "")
        article["word_count"] = len(content_only)

        return article

    def _create_fallback_article(self, hotspot) -> Dict:
        """创建备用文章结构"""
        return {
            "title": hotspot.title,
            "summary": hotspot.snippet[:100] if hotspot.snippet else "",
            "content": f"# {hotspot.title}\n\n{hotspot.snippet}",
            "word_count": len(hotspot.snippet) if hotspot.snippet else 0,
            "reference_url": hotspot.url,
            "raw_markdown": f"# {hotspot.title}\n\n{hotspot.snippet}"
        }
