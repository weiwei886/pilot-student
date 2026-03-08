"""筛选逻辑模块。

该文件负责：
1) 计算互动热度；
2) 按关键词做基础相关性过滤；
3) 过滤广告/抽奖类内容；
4) 按英文优先和热度排序。
"""

from __future__ import annotations

from typing import Dict, List


def compute_engagement(post: Dict) -> int:
    """计算帖子热度：点赞 + 转发 + 回复。"""
    metrics = post.get("public_metrics", {}) or {}
    return int(metrics.get("like_count", 0)) + int(metrics.get("retweet_count", 0)) + int(
        metrics.get("reply_count", 0)
    )


def is_relevant_post(
    text: str,
    filter_keywords: List[str],
    exclude_keywords: List[str],
) -> bool:
    """判断是否为相关帖子。

    规则：
    - 如果命中排除词，直接剔除；
    - 如果配置了保留词，则至少命中一个；
    - 若保留词为空，则默认通过。
    """
    lowered = (text or "").lower()

    if any(keyword in lowered for keyword in exclude_keywords):
        return False

    if not filter_keywords:
        return True

    return any(keyword in lowered for keyword in filter_keywords)


def filter_and_rank_posts(
    posts: List[Dict],
    min_engagement: int,
    filter_keywords: List[str],
    exclude_keywords: List[str],
) -> List[Dict]:
    """按规则过滤并排序。

    排序优先级：
    1) 英文内容优先 (lang == 'en')
    2) 互动热度高优先
    """
    filtered: List[Dict] = []

    for post in posts:
        text = post.get("text", "")

        if not is_relevant_post(text, filter_keywords, exclude_keywords):
            continue

        engagement = compute_engagement(post)
        if engagement < min_engagement:
            continue

        post["engagement"] = engagement
        filtered.append(post)

    filtered.sort(
        key=lambda item: (
            item.get("lang") != "en",  # False(英文) 在前
            -item.get("engagement", 0),
        )
    )
    return filtered
