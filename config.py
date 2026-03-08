"""项目统一配置。

将所有可以调节的参数集中在这里，方便后续维护。
对于敏感信息（如 X_BEARER_TOKEN）请放到环境变量中。
"""

import os
from pathlib import Path


# ====== 基础路径 ======
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# ====== RSS 配置 ======
RSS_SOURCES = {
    "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "Cointelegraph": "https://cointelegraph.com/rss",
}


# ====== X API 配置 ======
X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN", "")
X_API_BASE_URL = "https://api.x.com/2"
X_MAX_RESULTS = 50  # Recent Search 每次请求最多 100

# 按照需求给出的关键词。
X_SEARCH_QUERIES = [
    "bitcoin OR btc OR ethereum OR eth OR solana OR sol OR etf OR sec OR exchange OR hack OR regulation"
]

# ====== 内容过滤配置 ======
# 至少满足：点赞 + 转发 + 回复 >= MIN_ENGAGEMENT
MIN_ENGAGEMENT = int(os.getenv("MIN_ENGAGEMENT", "15"))

# 希望保留的关键词（可为空）。
FILTER_KEYWORDS = [
    "bitcoin",
    "btc",
    "ethereum",
    "eth",
    "solana",
    "sol",
    "etf",
    "sec",
    "exchange",
    "hack",
    "regulation",
]

# 明显广告/抽奖等关键词，后续可自行增删。
EXCLUDE_KEYWORDS = [
    "giveaway",
    "airdrop",
    "promo",
    "promotion",
    "referral",
    "use my code",
    "sponsored",
    "casino",
    "bet now",
]


# ====== 输出文件 ======
NEWS_OUTPUT_PATH = OUTPUT_DIR / "news.json"
X_POSTS_OUTPUT_PATH = OUTPUT_DIR / "x_posts.json"
X_VIDEOS_OUTPUT_PATH = OUTPUT_DIR / "x_videos.json"
