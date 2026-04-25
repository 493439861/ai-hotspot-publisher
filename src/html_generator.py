"""
HTML 生成模块
将 Markdown 文章转换为 HTML 格式，保存到按日期命名的目录下
"""

import re
from pathlib import Path
from typing import Dict


class HTMLGenerator:
    """HTML 生成器"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_html(self, article: Dict, images: Dict) -> str:
        """
        生成 HTML 文件

        Args:
            article: 文章数据
            images: 图片路径字典

        Returns:
            HTML 文件路径
        """
        html_content = self._build_html(article, images)

        # 保存 HTML 文件
        html_path = self.output_dir / "article.html"
        html_path.write_text(html_content, encoding="utf-8")

        return str(html_path)

    def _build_html(self, article: Dict, images: Dict) -> str:
        """构建 HTML 内容"""
        # 处理 Markdown 内容
        content = article.get("raw_markdown", article.get("content", ""))
        html_body = self._markdown_to_html(content)

        # 获取相对路径
        cover_relative = "./cover.png"
        article_image_relative = "./article.png"

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{article['title']}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.8;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            background-color: #fafafa;
        }}
        .cover-image {{
            text-align: center;
            margin: 30px 0;
        }}
        .cover-image img {{
            max-width: 100%;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        h1 {{
            font-size: 2em;
            color: #1a1a1a;
            margin-bottom: 20px;
            line-height: 1.3;
        }}
        .summary {{
            background-color: #f0f7ff;
            border-left: 4px solid #1890ff;
            padding: 15px 20px;
            margin: 20px 0;
            border-radius: 0 4px 4px 0;
            font-size: 0.95em;
            color: #666;
        }}
        .content {{
            margin-top: 30px;
        }}
        .content p {{
            margin-bottom: 1.2em;
            text-align: justify;
        }}
        .content h2, .content h3 {{
            margin-top: 1.5em;
            margin-bottom: 0.8em;
            color: #1a1a1a;
        }}
        .article-image {{
            text-align: center;
            margin: 30px 0;
        }}
        .article-image img {{
            max-width: 100%;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        .reference {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 0.9em;
            color: #888;
        }}
        .reference a {{
            color: #1890ff;
            text-decoration: none;
        }}
        .reference a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <article>
        <div class="cover-image">
            <img src="{cover_relative}" alt="封面图">
        </div>

        <h1>{article['title']}</h1>

        <div class="summary">
            <strong>摘要：</strong>{article.get('summary', '')}
        </div>

        <div class="article-image">
            <img src="{article_image_relative}" alt="文中插图">
        </div>

        <div class="content">
            {html_body}
        </div>

        <div class="reference">
            <strong>参考链接：</strong>
            <a href="{article.get('reference_url', '#')}" target="_blank">{article.get('reference_url', '')}</a>
        </div>
    </article>
</body>
</html>"""

        return html

    def _markdown_to_html(self, markdown: str) -> str:
        """简单的 Markdown 到 HTML 转换"""
        # 移除标题标记用于提取标题（已在外面处理）
        html = markdown

        # 移除标题行
        lines = html.split("\n")
        content_lines = []
        skip_next = False

        for i, line in enumerate(lines):
            if skip_next:
                skip_next = False
                continue

            line = line.strip()

            # 跳过已处理的标题和摘要
            if line.startswith("标题：") or line.startswith("# "):
                skip_next = True
                continue
            if line.startswith("摘要：") or line.startswith("## "):
                continue
            if line.startswith("---") or line.startswith("***"):
                continue

            # 处理标题
            if line.startswith("### "):
                content_lines.append(f"<h3>{line[4:].strip()}</h3>")
            elif line.startswith("## "):
                content_lines.append(f"<h2>{line[3:].strip()}</h2>")
            elif line.startswith("# "):
                content_lines.append(f"<h1>{line[2:].strip()}</h1>")
            elif line:
                # 包裹在 p 标签中
                # 简单处理加粗和链接
                line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
                line = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', line)
                content_lines.append(f"<p>{line}</p>")

        return "\n".join(content_lines)
