"""データ収集アダプター - 複数ソースからの並列フェッチ."""

import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import cast

import feedparser
import requests
import structlog
from atproto import Client as BskyClient

from app.domain.models import Article

logger = structlog.get_logger(__name__)

REQUEST_TIMEOUT = 15

MEDIA_FILTER_KEYWORDS: set[str] = {
    "kyodonews",
    "yahoo",
    "nhk",
    "asahi",
    "mainichi",
    "yomiuri",
    "sankei",
    "nikkei",
    "jiji",
    "reuters",
    "afpbb",
    "cnn",
    "bbc",
    "press",
    "news",
    "times",
    "journal",
    "media",
    "official",
}


class MultiSourceCollector:
    """複数ソースからデータを並列収集する."""

    def __init__(self, bsky_handle: str = "", bsky_password: str = "") -> None:
        self._bsky_handle = bsky_handle
        self._bsky_password = bsky_password

    def collect(
        self, keyword: str
    ) -> tuple[list[Article], list[Article], list[Article], list[dict[str, str | int]]]:
        with ThreadPoolExecutor(max_workers=3) as executor:
            f_news = executor.submit(self._fetch_news, keyword)
            f_bsky = executor.submit(self._fetch_bsky, keyword)
            f_hatena = executor.submit(self._fetch_hatena, keyword)

            news = f_news.result()
            bsky = f_bsky.result()
            hatena_articles, hatena_entries = f_hatena.result()

        return news, bsky, hatena_articles, hatena_entries

    def _fetch_news(self, keyword: str) -> list[Article]:
        encoded = urllib.parse.quote(keyword)
        ts = datetime.now().timestamp()
        url = f"https://news.google.com/rss/search?q={encoded}&hl=ja&gl=JP&ceid=JP:ja&_t={ts}"
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
        except Exception as e:
            logger.warning("ニュース取得失敗", error=str(e))
            return []

        articles = []
        for entry in feed.entries[:30]:
            published_at = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pp = cast("tuple[int, ...]", entry.published_parsed)
                published_at = datetime(pp[0], pp[1], pp[2], pp[3], pp[4], pp[5])
            articles.append(
                Article(
                    title=str(entry.title),
                    url=str(entry.link),
                    source="news",
                    published_at=published_at,
                )
            )
        return articles

    def _fetch_bsky(self, keyword: str) -> list[Article]:
        if not self._bsky_handle or not self._bsky_password:
            return []
        try:
            client = BskyClient()
            client.login(self._bsky_handle, self._bsky_password)
            response = client.app.bsky.feed.search_posts(
                params={"q": keyword, "limit": 20, "lang": "ja"}
            )
        except Exception as e:
            logger.warning("BlueSky取得失敗", error=str(e))
            return []

        articles = []
        for post in response.posts:
            author = post.author.handle
            if any(kw in author.lower() for kw in MEDIA_FILTER_KEYWORDS):
                continue
            rkey = post.uri.split("/")[-1]
            text = str(getattr(post.record, "text", ""))
            articles.append(
                Article(
                    title=text,
                    url=f"https://bsky.app/profile/{author}/post/{rkey}",
                    source="bluesky",
                    author=f"@{author}",
                )
            )
        return articles

    def _fetch_hatena(self, keyword: str) -> tuple[list[Article], list[dict[str, str | int]]]:
        quoted = f'"{keyword}"'
        search_url = (
            f"https://b.hatena.ne.jp/search/text?q={urllib.parse.quote(quoted)}&users=3&mode=rss"
        )
        try:
            resp = requests.get(search_url, timeout=10)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
        except Exception:
            return [], []

        entries: list[dict[str, str | int]] = []
        for entry in feed.entries:
            if keyword not in str(entry.title):
                continue
            entries.append(
                {
                    "title": str(entry.title),
                    "url": str(entry.link),
                    "bookmark_count": int(str(entry.get("hatena_bookmarkcount", 0) or 0)),
                }
            )

        entries.sort(key=lambda x: int(x["bookmark_count"]), reverse=True)
        top_entries = entries[:5]

        articles: list[Article] = []
        entry_data: list[dict[str, str | int]] = []
        for entry in top_entries:
            time.sleep(0.5)
            comments = self._get_hatena_comments(str(entry["url"]))
            if comments:
                entry_data.append(entry)
                for c in comments:
                    articles.append(
                        Article(
                            title=c["comment"],
                            url=str(entry["url"]),
                            source="hatena",
                            author=c["user"],
                            metadata={
                                "entry_title": str(entry["title"]),
                                "bookmark_count": int(entry["bookmark_count"]),
                            },
                        )
                    )
        return articles, entry_data

    def _get_hatena_comments(self, url: str) -> list[dict[str, str]]:
        api_url = f"https://b.hatena.ne.jp/entry/json/?url={urllib.parse.quote(url)}"
        try:
            resp = requests.get(api_url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []
        if not data or "bookmarks" not in data:
            return []
        return [
            {"user": b.get("user", ""), "comment": b["comment"].strip()}
            for b in data["bookmarks"]
            if b.get("comment", "").strip()
        ]
