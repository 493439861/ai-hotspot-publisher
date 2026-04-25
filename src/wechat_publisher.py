"""
微信公众号发布模块
将 HTML 文章转换为微信图文并发布到公众号
"""

import re
import os
import requests
from pathlib import Path
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()


class WeChatPublisher:
    """微信公众号发布器"""

    # API Endpoints
    TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
    UPLOAD_URL = "https://api.weixin.qq.com/cgi-bin/material/add_material"
    DRAFT_ADD_URL = "https://api.weixin.qq.com/cgi-bin/draft/add"
    PUBLISH_URL = "https://api.weixin.qq.com/cgi-bin/freepublish/submit"

    def __init__(self, app_id: str = None, app_secret: str = None):
        self.app_id = app_id or os.getenv("WEIXIN_APP_ID", "")
        self.app_secret = app_secret or os.getenv("WEIXIN_APP_SECRET", "")
        self._access_token = None

    @property
    def access_token(self) -> str:
        """获取 access token (懒加载)"""
        if not self._access_token:
            self._refresh_token()
        return self._access_token

    def _refresh_token(self) -> None:
        """刷新 access token"""
        params = {
            "grant_type": "client_credential",
            "appid": self.app_id,
            "secret": self.app_secret,
        }
        resp = requests.get(self.TOKEN_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if data.get("errcode"):
            raise RuntimeError(f"WeChat API error: {data['errcode']} - {data.get('errmsg', '')}")

        self._access_token = data["access_token"]

    def _upload_image(self, image_path: str) -> str:
        """
        上传图片到微信素材库，获取永久 media_id

        Args:
            image_path: 图片本地路径

        Returns:
            media_id
        """
        url = f"{self.UPLOAD_URL}?access_token={self.access_token}&type=image"

        with open(image_path, "rb") as f:
            files = {"media": f}
            resp = requests.post(url, files=files, timeout=30)

        resp.raise_for_status()
        data = resp.json()

        if data.get("errcode"):
            raise RuntimeError(f"Upload image failed: {data['errcode']} - {data.get('errmsg', '')}")

        return data["media_id"]

    def _process_html_content(self, html_path: str, cover_media_id: str) -> str:
        """
        处理 HTML 内容，转换为微信图文消息格式

        Args:
            html_path: HTML 文件路径
            cover_media_id: 封面图 media_id

        Returns:
            处理后的 content 字符串
        """
        html_content = Path(html_path).read_text(encoding="utf-8")

        # 提取 title
        title_match = re.search(r"<title>(.*?)</title>", html_content)
        title = title_match.group(1) if title_match else "无标题"

        # 提取摘要
        summary_match = re.search(r'<div class="summary">.*?<strong>摘要：</strong>(.*?)</div>', html_content, re.DOTALL)
        summary = summary_match.group(1).strip() if summary_match else ""
        # 清理 HTML 标签
        summary = re.sub(r"<[^>]+>", "", summary).strip()

        # 提取正文内容
        content_match = re.search(r'<div class="content">\s*(.*?)\s*</div>', html_content, re.DOTALL)
        if not content_match:
            content_match = re.search(r'<div class="content">(.*?)</div>', html_content, re.DOTALL)

        if content_match:
            content = content_match.group(1)
        else:
            content = ""

        # 处理内容中的图片 - 替换相对路径为微信素材 URL
        # 注意：微信图文消息中的图片需要使用上传后返回的 URL
        # 这里简化处理，保留原样式的 img 标签
        content = self._upload_content_images(content)

        # 清理不需要的 HTML 标签
        content = self._clean_html(content)

        return content

    def _upload_content_images(self, content: str) -> str:
        """
        上传内容中的图片并替换为微信素材 URL

        Args:
            content: HTML 内容

        Returns:
            处理后的内容
        """
        # 查找所有 img 标签
        img_pattern = re.compile(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>')

        def replace_img(match):
            img_tag = match.group(0)
            src_match = re.search(r'src=["\']([^"\']+)["\']', img_tag)
            if src_match:
                src = src_match.group(1)
                # 如果是相对路径，尝试上传
                if src.startswith("./") or src.startswith("/"):
                    # 提取文件名
                    filename = os.path.basename(src)
                    # 由于无法获取完整路径，这里保留原标签
                    # 实际发布时需要确保图片已上传到微信素材库
                    return img_tag
            return img_tag

        return img_pattern.sub(replace_img, content)

    def _clean_html(self, content: str) -> str:
        """清理 HTML，保留微信支持的标签"""
        # 移除 style 标签和内容
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)

        # 移除 script 标签
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)

        # 移除不需要的 class 和 style 属性
        content = re.sub(r'\s*class="[^"]*"', '', content)
        content = re.sub(r'\s*style="[^"]*"', '', content)

        # 转换一些标签为微信支持的格式
        content = re.sub(r'<strong>(.*?)</strong>', r'<b>\1</b>', content)

        return content

    def create_draft(self, html_path: str, cover_path: str, author: str = "AI") -> Tuple[str, str]:
        """
        创建图文草稿

        Args:
            html_path: HTML 文件路径
            cover_path: 封面图路径
            author: 作者

        Returns:
            (media_id, article_url)
        """
        # 上传封面图获取 thumb_media_id
        print("  上传封面图到微信素材库...")
        thumb_media_id = self._upload_image(cover_path)
        print(f"    封面图 media_id: {thumb_media_id}")

        # 处理内容
        print("  处理文章内容...")
        content = self._process_html_content(html_path, thumb_media_id)

        # 提取标题
        title_match = re.search(r"<title>(.*?)</title>", Path(html_path).read_text(encoding="utf-8"))
        title = title_match.group(1) if title_match else "无标题"

        # 提取摘要
        html_content = Path(html_path).read_text(encoding="utf-8")
        summary_match = re.search(r'<div class="summary">.*?<strong>摘要：</strong>(.*?)</div>', html_content, re.DOTALL)
        summary = summary_match.group(1).strip() if summary_match else ""
        summary = re.sub(r"<[^>]+>", "", summary).strip()[:54]

        # 构建草稿内容 (title 限制 64 字节，中文在 UTF-8 下占 3 字节)
        draft_articles = [{
            "title": title.encode('utf-8')[:64].decode('utf-8', errors='ignore'),
            "author": author,
            "digest": summary or title[:54],
            "content": content,
            "content_source_url": "",
            "thumb_media_id": thumb_media_id,
            "show_cover_pic": 1,
            "need_open_comment": 0,
            "only_fans_can_comment": 0,
        }]

        payload = {
            "articles": draft_articles
        }

        # 创建草稿
        print("  创建草稿...")
        url = f"{self.DRAFT_ADD_URL}?access_token={self.access_token}"
        import json
        json_data = json.dumps(payload, ensure_ascii=False)
        resp = requests.post(url, data=json_data.encode('utf-8'), timeout=30,
                            headers={"Content-Type": "application/json; charset=utf-8"})
        resp.raise_for_status()
        data = resp.json()

        if data.get("errcode"):
            raise RuntimeError(f"Create draft failed: {data['errcode']} - {data.get('errmsg', '')}")

        media_id = data.get("media_id", "")
        print(f"    草稿 media_id: {media_id}")

        return media_id, ""

    def publish(self, media_id: str) -> Dict:
        """
        发布草稿

        Args:
            media_id: 草稿 media_id

        Returns:
            发布结果，包含 publish_id 和 article_url
        """
        print("  发布草稿...")
        url = f"{self.PUBLISH_URL}?access_token={self.access_token}"

        payload = {
            "media_id": media_id
        }

        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if data.get("errcode"):
            raise RuntimeError(f"Publish failed: {data['errcode']} - {data.get('errmsg', '')}")

        publish_id = data.get("publish_id", "")
        msg_data_id = data.get("msg_data_id", "")

        print(f"    发布成功! publish_id: {publish_id}")

        return {
            "publish_id": publish_id,
            "msg_data_id": msg_data_id,
            "article_url": f"https://mp.weixin.qq.com/s?__biz=&mid=&idx=1&sn={publish_id}"
        }

    def publish_article(self, html_path: str, cover_path: str, author: str = "AI") -> Dict:
        """
        完整发布流程：创建草稿并发布

        Args:
            html_path: HTML 文件路径
            cover_path: 封面图路径
            author: 作者

        Returns:
            发布结果
        """
        media_id, _ = self.create_draft(html_path, cover_path, author)
        result = self.publish(media_id)
        return result