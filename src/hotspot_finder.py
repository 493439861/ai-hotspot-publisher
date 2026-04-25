"""
热点发现模块 - GitHub Trending + Tavily 搜索 + arXiv
"""

import requests
from dataclasses import dataclass
from typing import List
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET


@dataclass
class Hotspot:
    """热点数据类"""
    title: str
    url: str
    snippet: str
    source: str
    publish_date: str
    score: float = 0.0


class HotspotFinder:
    """热点发现器 - 多源聚合"""

    def __init__(self, config):
        self.config = config
        self.tavily_api_key = config.tavily_api_key
        self.tavily_base_url = "https://api.tavily.com/search"

    def find_hotspots(self, limit: int = 10) -> List[Hotspot]:
        """
        搜索 AI 热点 - 多源聚合

        Args:
            limit: 返回数量（默认 10）

        Returns:
            热点列表
        """
        all_hotspots = []

        # 1. GitHub Trending（2条）
        github_hotspots = self._fetch_github_trending(limit=2)
        all_hotspots.extend(github_hotspots)

        # 2. arXiv 论文（4条）
        arxiv_hotspots = self._fetch_arxiv(limit=4)
        all_hotspots.extend(arxiv_hotspots)

        # 3. Tavily 搜索（4条）
        if self.tavily_api_key:
            tavily_hotspots = self._search_tavily(limit=4)
            all_hotspots.extend(tavily_hotspots)

        # 按 score 排序
        all_hotspots.sort(key=lambda x: x.score, reverse=True)
        return all_hotspots[:limit]

    def _fetch_github_trending(self, limit: int = 3) -> List[Hotspot]:
        """获取 GitHub Trending AI 项目"""
        hotspots = []
        try:
            # GitHub Trending AI 项目（最近一周）
            url = "https://api.github.com/search/repositories"
            one_week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            params = {
                "q": f"AI OR artificial-intelligence OR machine-learning OR deep-learning created:>{one_week_ago}",
                "sort": "stars",
                "order": "desc",
                "per_page": limit
            }

            headers = {"Accept": "application/vnd.github.v3+json"}
            response = requests.get(url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()

            for item in data.get("items", [])[:limit]:
                # 计算相对时间
                created = item.get("created_at", "")[:10]
                stars = item.get("stargazers_count", 0)

                hotspot = Hotspot(
                    title=item.get("name", ""),
                    url=item.get("html_url", ""),
                    snippet=f"{item.get('description', '暂无描述')} | ⭐ {stars} | 语言: {item.get('language', '未知')}",
                    source="GitHub",
                    publish_date=created,
                    score=0.7 + (stars / 100000)  # 星级越高分数越高
                )
                hotspots.append(hotspot)
        except Exception as e:
            print(f"GitHub Trending 获取失败: {e}")

        return hotspots

    def _search_tavily(self, limit: int = 2) -> List[Hotspot]:
        """使用 Tavily 搜索 AI 热点"""
        if not self.tavily_api_key:
            return []

        hotspots = []
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.tavily_api_key}"
            }

            payload = {
                "query": "AI artificial intelligence",
                "search_depth": "basic",
                "max_results": limit,
                "time_range": "week",
                "include_answer": False,
                "include_raw_content": False,
            }

            response = requests.post(
                self.tavily_base_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            for item in data.get("results", [])[:limit]:
                hotspot = Hotspot(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", "")[:200] if item.get("content") else "",
                    source=self._extract_source(item.get("url", "")),
                    publish_date=item.get("published_date", "") or datetime.now().strftime("%Y-%m-%d"),
                    score=item.get("relevance_score", 0.5)
                )
                hotspots.append(hotspot)

        except Exception as e:
            print(f"Tavily 搜索失败: {e}")

        return hotspots

    def _fetch_arxiv(self, limit: int = 4) -> List[Hotspot]:
        """获取 arXiv 最新 AI 论文（最近一周）"""
        hotspots = []
        try:
            one_week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
            # arXiv API - 搜索 AI 相关论文
            url = "http://export.arxiv.org/api/query"
            params = {
                "search_query": f"(cat:cs.AI OR cat:cs.LG OR cat:cs.CL) AND submittedDate:[{one_week_ago} TO NOW]",
                "start": 0,
                "max_results": limit,
                "sortBy": "submittedDate",
                "sortOrder": "descending"
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            # 解析 Atom feed
            root = ET.fromstring(response.content)
            ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

            for entry in root.findall("atom:entry", ns)[:limit]:
                title = entry.find("atom:title", ns)
                title_text = title.text.replace("\n", " ").strip() if title is not None else "无标题"

                link = entry.find("atom:id", ns)
                link_text = link.text if link is not None else ""

                summary = entry.find("atom:summary", ns)
                snippet = summary.text.replace("\n", " ").strip()[:200] if summary is not None else ""

                published = entry.find("atom:published", ns)
                date = published.text[:10] if published is not None else ""

                hotspot = Hotspot(
                    title=title_text,
                    url=link_text,
                    snippet=snippet,
                    source="arXiv",
                    publish_date=date,
                    score=0.8
                )
                hotspots.append(hotspot)

        except Exception as e:
            print(f"arXiv 获取失败: {e}")

        return hotspots

    def _extract_source(self, url: str) -> str:
        """从 URL 提取来源网站名"""
        if not url:
            return "未知"

        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            if domain.startswith("www."):
                domain = domain[4:]
            parts = domain.split(".")
            return parts[0] if parts else domain
        except:
            return "未知"
