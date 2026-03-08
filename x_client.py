"""X API v2 客户端。"""

from __future__ import annotations

import json
import logging
from typing import Dict, List
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class XClient:
    """简单的 X API v2 客户端。"""

    def __init__(self, bearer_token: str, base_url: str = "https://api.x.com/2") -> None:
        self.bearer_token = bearer_token
        self.base_url = base_url.rstrip("/")

    def search_recent(self, query: str, max_results: int = 50) -> List[Dict]:
        """搜索最近帖子并返回标准化结果列表。"""
        if not self.bearer_token:
            logging.warning("X_BEARER_TOKEN 未设置，跳过 X 抓取。")
            return []

        params = {
            "query": query,
            "max_results": max(10, min(max_results, 100)),
            "expansions": "author_id,attachments.media_keys",
            "tweet.fields": "id,text,author_id,created_at,public_metrics,lang,attachments",
            "user.fields": "id,name,username",
            "media.fields": "media_key,type,duration_ms,preview_image_url,url,variants",
        }
        url = f"{self.base_url}/tweets/search/recent?{urlencode(params)}"

        request = Request(url)
        request.add_header("Authorization", f"Bearer {self.bearer_token}")

        try:
            with urlopen(request, timeout=20) as response:  # nosec B310
                body = response.read().decode("utf-8")
                payload = json.loads(body)
        except HTTPError as exc:
            logging.error("X 请求失败: HTTP %s", exc.code)
            return []
        except (URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            logging.error("X 请求失败: %s", exc)
            return []

        data = payload.get("data", []) or []
        includes = payload.get("includes", {}) or {}

        users_by_id = {
            user.get("id"): user for user in includes.get("users", []) if user.get("id")
        }
        media_by_key = {
            media.get("media_key"): media
            for media in includes.get("media", [])
            if media.get("media_key")
        }

        posts: List[Dict] = []
        for tweet in data:
            author_id = tweet.get("author_id")
            user = users_by_id.get(author_id, {})

            media_items: List[Dict] = []
            media_keys = (
                tweet.get("attachments", {}).get("media_keys", [])
                if tweet.get("attachments")
                else []
            )
            for media_key in media_keys:
                media = media_by_key.get(media_key)
                if not media:
                    continue
                media_items.append(
                    {
                        "media_key": media.get("media_key"),
                        "type": media.get("type"),
                        "duration_ms": media.get("duration_ms"),
                        "preview_image_url": media.get("preview_image_url"),
                        "url": media.get("url"),
                        "variants": media.get("variants", []),
                    }
                )

            has_media = len(media_items) > 0
            has_video = any(item.get("type") in {"video", "animated_gif"} for item in media_items)

            posts.append(
                {
                    "id": tweet.get("id"),
                    "text": tweet.get("text"),
                    "author_id": author_id,
                    "author_name": user.get("name"),
                    "username": user.get("username"),
                    "created_at": tweet.get("created_at"),
                    "public_metrics": tweet.get("public_metrics", {}),
                    "source_query": query,
                    "url": f"https://x.com/{user.get('username', 'i')}/status/{tweet.get('id')}",
                    "lang": tweet.get("lang"),
                    "media": media_items,
                    "has_media": has_media,
                    "has_video": has_video,
                }
            )

        return posts
