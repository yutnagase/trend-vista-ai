# 形態素解析（Morphological Analysis） — Janome

## 形態素解析とは

日本語の文を単語（形態素）に分割する処理。英語はスペースで単語が区切られているが、日本語は「今日はいい天気ですね」のように単語の切れ目がない。形態素解析を使うと、これを「今日 / は / いい / 天気 / です / ね」と分割できる。

本プロジェクトでは、トレンドキーワード抽出とトピック別感情分析のために形態素解析を使っている。

## なぜJanomeを選んだか

| ツール | メリット | デメリット |
|--------|---------|-----------|
| MeCab | 高速 | C言語コンパイル必要、辞書別途インストール |
| **Janome** | **Pure Python、辞書内蔵、pip一発** | MeCabより低速 |
| spaCy (ja) | 高機能 | 依存が重い |

本プロジェクトのように「名詞を抽出したい」程度の用途にはJanomeで十分。Docker環境でもC拡張のビルドが不要なのは大きい。

## 基本的な使い方

```python
from janome.tokenizer import Tokenizer

tok = Tokenizer()

for token in tok.tokenize("生成AIの規制法案が提出された"):
    print(f"{token.surface}\t{token.part_of_speech}")
```

出力:
```
生成    名詞,サ変接続,*,*
AI      名詞,固有名詞,組織,*
の      助詞,連体化,*,*
規制    名詞,サ変接続,*,*
法案    名詞,一般,*,*
...
```

## 本プロジェクトでの使い方

### 名詞だけを抽出する

```python
def extract_keywords(titles, search_keyword, tokenizer, extra_stop_words=None):
    stop = STOP_WORDS | {search_keyword}
    if extra_stop_words:
        stop |= extra_stop_words
    words = []
    for title in titles:
        for token in tokenizer.tokenize(title):
            part = token.part_of_speech.split(",")[0]
            surface = token.surface
            if (
                part == "名詞"
                and len(surface) > 1
                and surface not in stop
                and not _NUMERIC_PATTERN.match(surface)
            ):
                words.append(surface)
    return Counter(words).most_common()
```

### ストップワードの除外

名詞でも不要な語がある。「Yahoo」「ニュース」「記事」などはどのキーワードで検索しても出てくるので、ストップワードとして除外している。検索キーワードそのものも除外する。「生成AI」で検索したら「生成」「AI」が最頻出になるのは当然なので。

### 数字トークンの除外

Janomeは「30」「10」などの数字を名詞（数詞）として解析する。正規表現 `^[\d,.\-+%０-９]+$` で除外している。

### メディア名の動的除外

GoogleニュースRSSのタイトルは「記事タイトル - メディア名」形式。タイトル末尾の` - `以降を動的に抽出し、ストップワードに追加する。

```python
news_media_names = set()
for title in news_titles:
    if " - " in title:
        media = title.rsplit(" - ", 1)[-1].strip()
        if media:
            news_media_names.add(media)
            for token in media.split():
                if len(token) > 1:
                    news_media_names.add(token)
```

「TBS NEWS DIG」のようにスペースを含むメディア名は、Janomeが個別トークンに分割するため、各トークンもストップワードに追加している。

### 1文字の語を除外する理由

1文字の名詞（「人」「国」「日」など）は意味が広すぎて、キーワードとしての情報量が低いため除外している。

## 参考リンク

- [Janome公式ドキュメント](https://mocobeta.github.io/janome/)
- [PyPI - janome](https://pypi.org/project/Janome/)
