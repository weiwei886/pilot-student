"""加密货币内容聚合器主入口。"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Dict, List
from urllib.error import URLError
from urllib.request import urlopen
from xml.etree import ElementTree

import config
from filters import filter_and_rank_posts
from x_client import XClient


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def load_dotenv_if_exists(dotenv_path: str = ".env") -> None:
    """读取 .env 到环境变量（仅在当前进程生效）。"""
    if not os.path.exists(dotenv_path):
        return

    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def parse_rss_datetime(raw_value: str) -> str:
    if not raw_value:
        return ""
    try:
        dt = parsedate_to_datetime(raw_value)
        return dt.isoformat()
    except Exception:
        return raw_value


def _find_text(node, tags: List[str]) -> str:
    for tag in tags:
        found = node.find(tag)
        if found is not None and found.text:
            return found.text.strip()
    return ""


def fetch_rss_news() -> List[Dict]:
    """抓取并去重 RSS 新闻。"""
    all_news: List[Dict] = []
    seen = set()

    for source, url in config.RSS_SOURCES.items():
        logging.info("抓取 RSS: %s (%s)", source, url)
        try:
            with urlopen(url, timeout=20) as response:  # nosec B310
                content = response.read()
            root = ElementTree.fromstring(content)
        except (URLError, TimeoutError, ElementTree.ParseError, OSError) as exc:
            logging.error("RSS 抓取失败 [%s]: %s", source, exc)
            continue

        # 同时兼容 RSS(item) 与 Atom(entry)
        items = root.findall(".//item") + root.findall(".//{http://www.w3.org/2005/Atom}entry")

        for item in items:
            title = _find_text(item, ["title", "{http://www.w3.org/2005/Atom}title"])
            link = _find_text(item, ["link", "{http://www.w3.org/2005/Atom}link"])

            # Atom 的 link 往往在 href 属性中
            if not link:
                atom_link_node = item.find("{http://www.w3.org/2005/Atom}link")
                if atom_link_node is not None:
                    link = atom_link_node.attrib.get("href", "").strip()

            published_raw = _find_text(
                item,
                [
                    "pubDate",
                    "published",
                    "updated",
                    "{http://www.w3.org/2005/Atom}published",
                    "{http://www.w3.org/2005/Atom}updated",
                ],
            )
            published = parse_rss_datetime(published_raw)

            news_item = {
                "title": title,
                "link": link,
                "published": published,
                "source": source,
            }
            unique_key = (news_item["title"], news_item["link"])
            if unique_key in seen:
                continue

            seen.add(unique_key)
            all_news.append(news_item)

    all_news.sort(key=lambda n: n.get("published") or datetime.min.replace(tzinfo=timezone.utc).isoformat(), reverse=True)
    return all_news


def fetch_x_posts() -> List[Dict]:
    x_client = XClient(os.getenv("X_BEARER_TOKEN", config.X_BEARER_TOKEN), config.X_API_BASE_URL)
    raw_posts: List[Dict] = []

    for query in config.X_SEARCH_QUERIES:
        logging.info("抓取 X Recent Search: %s", query)
        posts = x_client.search_recent(query=query, max_results=config.X_MAX_RESULTS)
        raw_posts.extend(posts)

    deduped_by_id = {post.get("id"): post for post in raw_posts if post.get("id")}

    return filter_and_rank_posts(
        list(deduped_by_id.values()),
        min_engagement=int(os.getenv("MIN_ENGAGEMENT", str(config.MIN_ENGAGEMENT))),
        filter_keywords=config.FILTER_KEYWORDS,
        exclude_keywords=config.EXCLUDE_KEYWORDS,
    )


def save_json(path, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def print_preview(title: str, items: List[Dict], fields: List[str], limit: int = 5) -> None:
    print(f"\n=== {title}（前 {limit} 条）===")
    for idx, item in enumerate(items[:limit], start=1):
        view = {field: item.get(field) for field in fields}
        print(f"{idx}. {json.dumps(view, ensure_ascii=False)}")
    if not items:
        print("(暂无数据)")


def main() -> None:
    load_dotenv_if_exists()
    setup_logging()

    logging.info("开始运行加密货币内容聚合器 - %s", datetime.now().isoformat())

    news = fetch_rss_news()
    save_json(config.NEWS_OUTPUT_PATH, news)
    logging.info("RSS 新闻已保存: %s (共 %d 条)", config.NEWS_OUTPUT_PATH, len(news))

    x_posts = fetch_x_posts()
    save_json(config.X_POSTS_OUTPUT_PATH, x_posts)
    logging.info("X 帖子已保存: %s (共 %d 条)", config.X_POSTS_OUTPUT_PATH, len(x_posts))

    x_videos = [post for post in x_posts if post.get("has_video")]
    save_json(config.X_VIDEOS_OUTPUT_PATH, x_videos)
    logging.info("视频帖子已保存: %s (共 %d 条)", config.X_VIDEOS_OUTPUT_PATH, len(x_videos))

    print_preview("RSS 新闻", news, ["title", "source", "published", "link"], 5)
    print_preview(
        "X 热门帖子",
        x_posts,
        ["id", "author_name", "username", "engagement", "has_media", "has_video", "url"],
        5,
    )
    print_preview("含视频帖子", x_videos, ["id", "author_name", "username", "engagement", "has_video", "url"], 5)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.exception("程序发生未处理异常，已安全退出。")
