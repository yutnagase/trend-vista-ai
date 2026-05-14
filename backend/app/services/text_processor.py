"""テキスト処理サービス - 形態素解析・キーワード抽出."""

import re
from collections import Counter

from janome.tokenizer import Tokenizer

_NUMERIC_PATTERN = re.compile(r"^[\d,.\-+%０-９]+$")
_SHORT_ASCII_PATTERN = re.compile(r"^[A-Za-z]{1,2}$")

STOP_WORDS: set[str] = {
    "の",
    "に",
    "は",
    "が",
    "を",
    "で",
    "と",
    "も",
    "た",
    "だ",
    "する",
    "いる",
    "ある",
    "こと",
    "それ",
    "これ",
    "ない",
    "なる",
    "れる",
    "られる",
    "よう",
    "さん",
    "ため",
    "から",
    "まで",
    "など",
    "について",
    "として",
    "における",
    "Yahoo",
    "ニュース",
    "新聞",
    "速報",
    "記事",
    "配信",
    "発表",
    "https",
    "http",
    "www",
    "com",
    "jp",
}


def create_tokenizer() -> Tokenizer:
    return Tokenizer()


def extract_media_names(titles: list[str]) -> set[str]:
    media_names: set[str] = set()
    for title in titles:
        if " - " in title:
            media = title.rsplit(" - ", 1)[-1].strip()
            if media:
                media_names.add(media)
                for token in media.split():
                    if len(token) > 1:
                        media_names.add(token)
    return media_names


def extract_keywords(
    titles: list[str],
    search_keyword: str,
    tokenizer: Tokenizer | None = None,
    extra_stop_words: set[str] | None = None,
) -> list[tuple[str, int]]:
    tok = tokenizer or create_tokenizer()
    stop = STOP_WORDS | {search_keyword}
    if extra_stop_words:
        stop |= extra_stop_words
    words: list[str] = []
    for title in titles:
        for token in tok.tokenize(title):
            part: str = token.part_of_speech.split(",")[0]
            surface: str = token.surface
            if (
                part == "名詞"
                and len(surface) > 1
                and surface not in stop
                and not _NUMERIC_PATTERN.match(surface)
                and not _SHORT_ASCII_PATTERN.match(surface)
            ):
                words.append(surface)
    return Counter(words).most_common()
