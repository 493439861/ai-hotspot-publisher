"""
配置管理模块
"""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


@dataclass
class Config:
    """配置类"""

    # MiniMax API (用于文章生成)
    minimax_api_key: str = os.getenv("MINIMAX_API_KEY", "")
    minimax_model: str = "minimax2.7"

    # 阿里云百炼 API
    aliyun_bailian_api_key: str = os.getenv("ALIYUN_BAILIAN_API_KEY", "")

    # Tavily API
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")

    # 微信公众号 API
    weixin_app_id: str = os.getenv("WEIXIN_APP_ID", "")
    weixin_app_secret: str = os.getenv("WEIXIN_APP_SECRET", "")

    # 热点搜索配置
    hotspot_limit: int = 5

    # 文章配置
    article_max_words: int = 300

    # 配图配置
    image_style: str = "手绘漫画，科技蓝色温暖风格，适合内容平台配图（横向长方形构图，画面干净，主体清晰）"

    # 输出目录
    output_dir: Path = Path(__file__).parent.parent / "output"

    def validate(self) -> bool:
        """验证配置是否完整"""
        required = [
            self.aliyun_bailian_api_key,
        ]
        return bool(self.minimax_api_key) and all(required)
