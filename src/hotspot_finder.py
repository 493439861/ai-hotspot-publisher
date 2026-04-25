"""
热点发现模块 - GitHub Trending + Tavily 搜索
"""

import requests
from dataclasses import dataclass
from typing import List
from datetime import datetime


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

    def find_hotspots(self, limit: int = 5) -> List[Hotspot]:
        """
        搜索 AI 热点 - 多源聚合

        Args:
            limit: 返回数量

        Returns:
            热点列表
        """
        all_hotspots = []

        # 1. GitHub Trending
        github_hotspots = self._fetch_github_trending(limit=2)
        all_hotspots.extend(github_hotspots)

        # 2. Tavily 搜索作为补充
        if self.tavily_api_key:
            tavily_hotspots = self._search_tavily(limit=3)
            all_hotspots.extend(tavily_hotspots)

        # 按 score 排序
        all_hotspots.sort(key=lambda x: x.score, reverse=True)
        return all_hotspots[:limit]

    def _fetch_github_trending(self, limit: int = 3) -> List[Hotspot]:
        """获取 GitHub Trending AI 项目"""
        hotspots = []
        try:
            # GitHub Trending AI 项目
            url = "https://api.github.com/search/repositories"
            params = {
                "q": "AI OR artificial-intelligence OR machine-learning OR deep-learning",
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
                "time_range": "day",
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
