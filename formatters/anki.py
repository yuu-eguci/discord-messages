"""Parsed JSONL を Anki 用のテキストに変換します。

各 `heading` を表の 1 列目に、`children` を `<br />` 区切りで 2 列目に入れます。
3 列目は常に `discord` にします。
`#html:true` なので `&` `<` `>` は HTML エスケープし、列がずれないようにタブは半角スペースにします。
"""

from html import escape
from typing import Any


def _to_field(value: object) -> str:
    return escape(str(value), quote=False).replace("\t", " ")


def _render_entry(entry: dict[str, Any]) -> str:
    heading = _to_field(entry.get("heading", ""))
    children = entry.get("children", [])
    if not isinstance(children, list):
        children = []
    child_text = "<br />".join(_to_field(child) for child in children)
    return f"{heading}\t{child_text}\tdiscord"


def format_anki(records: list[list[dict[str, Any]]]) -> str:
    lines = ["#separator:tab", "#html:true"]
    for record in records:
        if not record:
            continue
        for entry in record:
            lines.append(_render_entry(entry))

    return "\n".join(lines) + "\n"
