"""
AI 热点自动发布系统 - 主入口
每日抓取热点，用户选择后生成文章和配图，输出 HTML 到按日期+时间命名的目录
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from hotspot_finder import HotspotFinder
from content_generator import ContentGenerator
from image_generator import ImageGenerator
from html_generator import HTMLGenerator
from wechat_publisher import WeChatPublisher
from config import Config


class AIHotspotPublisher:
    """AI 热点发布系统主类"""

    def __init__(self):
        self.config = Config()
        self.hotspot_finder = HotspotFinder(self.config)
        self.content_generator = ContentGenerator(self.config)

        # 输出目录：output/{日期+时间}/
        today = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.output_dir = self.config.output_dir / today
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.image_generator = ImageGenerator(self.config, self.output_dir)
        self.html_generator = HTMLGenerator(self.output_dir)

    def run(self, publish_to_wechat: bool = True):
        """运行完整流程

        Args:
            publish_to_wechat: 是否发布到微信公众号
        """
        print("=" * 50)
        print("AI 热点自动发布系统")
        print("=" * 50)

        # 1. 搜索热点
        print("\n[1/6] 正在搜索 AI 热点...")
        hotspots = self.hotspot_finder.find_hotspots(limit=5)
        if not hotspots:
            print("未找到热点，请稍后重试")
            return

        # 2. 显示热点列表供用户选择
        print("\n请选择要写作的热点（输入数字 1-5）：")
        for i, hotspot in enumerate(hotspots, 1):
            print(f"  {i}. {hotspot.title}")
            print(f"     来源: {hotspot.source} | 时间: {hotspot.publish_date}")
            print(f"     摘要: {hotspot.snippet[:80]}...")
            print()

        choice = input("请输入选择 (1-5): ").strip()
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(hotspots):
                print("无效选择")
                return
            selected_hotspot = hotspots[idx]
        except ValueError:
            print("无效输入")
            return

        print(f"\n已选择: {selected_hotspot.title}")

        # 3. 生成文章 (MiniMax, 300字)
        print("\n[2/6] 正在生成文章 (MiniMax2.7, 300字深度解读)...")
        article = self.content_generator.generate_article(selected_hotspot)
        print(f"文章已生成: {article['title']}")
        print(f"字数: {article['word_count']} 字")

        # 4. 生成配图 (wan2.7, 128x128)
        print("\n[3/6] 正在生成配图 (阿里云 wan2.7)...")
        images = self.image_generator.generate_images(article)
        print(f"封面图: {images['cover_image']}")
        print(f"文中插图: {images['article_image']}")

        # 5. 保存文章 Markdown
        print("\n[4/6] 正在保存 Markdown 文档...")
        md_path = self.output_dir / "article.md"
        md_path.write_text(article.get("raw_markdown", article.get("content", "")), encoding="utf-8")
        print(f"Markdown 已保存: {md_path}")

        # 6. 生成 HTML 格式
        print("\n[5/6] 正在转换为 HTML 格式...")
        html_path = self.html_generator.generate_html(article, images)
        print(f"HTML 已保存: {html_path}")

        # 7. 发布到微信公众号草稿箱
        if publish_to_wechat and self.config.weixin_app_id and self.config.weixin_app_secret:
            print("\n[6/6] 正在创建微信公众号草稿...")
            try:
                wechat = WeChatPublisher(self.config.weixin_app_id, self.config.weixin_app_secret)
                media_id, article_url = wechat.create_draft(
                    html_path=str(html_path),
                    cover_path=images["cover_image"],
                    author="AI"
                )
                print(f"草稿创建成功!")
                print(f"  media_id: {media_id}")
                print(f"  请前往微信公众号后台 -> 内容与互动 -> 草稿箱 -> 检查并发布文章")
            except Exception as e:
                print(f"微信发布失败: {e}")
                print("文章已保存本地，可手动发布")
        else:
            print("\n[6/6] 完成！")
            print("=" * 50)
            print(f"输出目录: {self.output_dir}")
            print(f"  - article.html (HTML 格式)")
            print(f"  - article.md (Markdown 格式)")
            print(f"  - cover.png (封面图)")
            print(f"  - article.png (文中插图)")
            print("=" * 50)
            print("\n请复制 HTML 内容到微信后台编辑器和配图进行发布。")


def main():
    """入口函数"""
    import argparse
    parser = argparse.ArgumentParser(description="AI 热点自动发布系统")
    parser.add_argument("--no-publish", action="store_true", help="不发布到微信公众号")
    args = parser.parse_args()

    publisher = AIHotspotPublisher()
    publisher.run(publish_to_wechat=not args.no_publish)


if __name__ == "__main__":
    main()
