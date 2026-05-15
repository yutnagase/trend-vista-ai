# データ収集 — feedparser / atproto / requests

## 概要

3つの情報源からデータを集めている。それぞれ取得方法が異なるため、用途に合ったライブラリを使い分けている。

| 情報源 | ライブラリ | プロトコル |
|--------|-----------|-----------|
| Googleニュース | feedparser | RSS（XML） |
| BlueSky | atproto | AT Protocol（REST API） |
| はてなブックマーク | requests + feedparser | HTTP（JSON API + RSS） |

本プロジェクトでは`ThreadPoolExecutor`で3ソースを並列フェッチし、レスポンス時間を短縮している。

## Googleニュース — feedparser

### RSSとは

RSS（Really Simple Syndication）は、Webサイトの更新情報を配信するためのXML形式のフォーマット。GoogleニュースもRSSフィードを提供しているので、APIキー不要・認証不要で最新ニュースを取得できる。

### 実装

```python
import urllib.parse
import feedparser
import requests

def _fetch_news(self, keyword: str) -> list[Article]:
    encoded = urllib.parse.quote(keyword)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=ja&gl=JP&ceid=JP:ja"
    resp = requests.get(url, timeout=15)
    feed = feedparser.parse(resp.text)
    return [
        Article(title=entry.title, url=entry.link, source="news")
        for entry in feed.entries[:30]
    ]
```

`feedparser.parse()`にURLを直接渡す方法もあるが、タイムアウト制御のためにrequestsで取得してからパースしている。

## BlueSky — atproto

### AT Protocolとは

AT Protocol（Authenticated Transfer Protocol）は、BlueSkyが開発した分散型SNSのためのプロトコル。Twitterと違い、オープンな仕様で誰でもクライアントを作れる。

### メディアアカウントの除外

BlueSkyで検索すると、ニュースメディアの公式アカウントの投稿も混ざる。本プロジェクトでは「個人の生の声」を拾いたいので、メディアアカウントをフィルタリングしている。

```python
MEDIA_FILTER_KEYWORDS = {
    "kyodonews", "yahoo", "nhk", "asahi", "mainichi",
    "nikkei", "reuters", "press", "news", "official",
}

def _is_media_account(handle: str) -> bool:
    return any(kw in handle.lower() for kw in MEDIA_FILTER_KEYWORDS)
```

ハンドル名に「news」「press」などが含まれていたらメディアとみなして除外する。完璧ではないが、大半のメディアアカウントはこれで弾ける。

### 投稿URLの組み立て

BlueSkyのAPIが返すのは内部URI（`at://did:plc:xxx/app.bsky.feed.post/yyy`）なので、ブラウザで開けるURLに変換している。

```python
rkey = post.uri.split("/")[-1]
post_url = f"https://bsky.app/profile/{post.author.handle}/post/{rkey}"
```

## はてなブックマーク — requests

### 2つのAPIの組み合わせ

1. **検索RSS** — キーワードでブックマークされた記事を検索
2. **エントリーJSON API** — 特定記事のコメント一覧を取得

```python
# 検索RSSで記事を探す
quoted = f'"{keyword}"'  # フレーズ検索
url = f"https://b.hatena.ne.jp/search/text?q={urllib.parse.quote(quoted)}&users=3&mode=rss"
feed = feedparser.parse(resp.text)

# ブックマーク数上位5件のコメントを取得
for entry in top_entries[:5]:
    time.sleep(0.5)  # サーバー負荷への配慮
    comments = self._get_hatena_comments(entry["url"])
```

### サーバーへの配慮

はてなのAPIは公開されているが、短時間に大量リクエストを送るとアクセス制限される可能性がある。以下の対策をしている。

- 取得対象をブックマーク数上位5件に限定
- リクエスト間に0.5秒のスリープを挿入
- フレーズ検索で不要なリクエストを削減

## 並列フェッチ

3ソースの取得は互いに独立しているため、`ThreadPoolExecutor`で並列実行している。

```python
def collect(self, keyword: str):
    with ThreadPoolExecutor(max_workers=3) as executor:
        f_news = executor.submit(self._fetch_news, keyword)
        f_bsky = executor.submit(self._fetch_bsky, keyword)
        f_hatena = executor.submit(self._fetch_hatena, keyword)

        news = f_news.result()
        bsky = f_bsky.result()
        hatena_articles, hatena_entries = f_hatena.result()
    return news, bsky, hatena_articles, hatena_entries
```

直列実行だと3ソース合計で5〜10秒かかるところが、並列化で最も遅いソースの時間（通常3〜5秒）に短縮される。

## AND検索を採用しない理由

各ソースの1回の取得件数はGoogleニュース30件・BlueSky 20件・はてブ数十件程度であり、ANDで絞り込むと母数が数件になる。この件数では後段の感情分析パイプラインが統計的に機能しない。

詳細は [DEVELOPMENT_INSIGHT.md](DEVELOPMENT_INSIGHT.md) を参照。

## 参考リンク

- [feedparser ドキュメント](https://feedparser.readthedocs.io/)
- [atproto（Python SDK）GitHub](https://github.com/MarshalX/atproto)
- [AT Protocol 仕様](https://atproto.com/)
- [はてなブックマーク エントリー情報取得API](https://developer.hatena.ne.jp/ja/documents/bookmark/apis/getinfo)
