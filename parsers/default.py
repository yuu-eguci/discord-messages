"""Markdown の箇条書きを、見出しと子要素の配列に変換します。

この parser は、`content` の各行を見て次の形式だけを扱います。

- 先頭インデントがない `-` `*` `+` の行を `heading` として扱います。
- その直後に続く、インデント付きの `-` `*` `+` の行を `children` として扱います。
- 空行や、箇条書きではない行は無視します。

変換結果は、次のような構造です。

[
    {
        "heading": "foo",
        "children": ["bar", "baz"]
    }
]
"""

import re
from typing import Any

_LIST_ITEM_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<bullet>[-*+])(?P<text>(?:[ \t]+.*)?)$")


def _line_indent_width(value: str) -> int:
    return len(value.expandtabs(4))


def parse_default_content(content: str) -> list[dict[str, Any]]:
    parsed_items: list[dict[str, Any]] = []
    current_item: dict[str, Any] | None = None

    for line in content.splitlines():
        if not line.strip():
            continue

        match = _LIST_ITEM_RE.match(line)
        if match is None:
            continue

        text = match.group("text").strip()
        if not text:
            continue

        indent_width = _line_indent_width(match.group("indent"))
        if indent_width == 0:
            current_item = {
                "heading": text,
                "children": [],
            }
            parsed_items.append(current_item)
            continue

        if current_item is None:
            continue

        current_item["children"].append(text)

    return parsed_items
