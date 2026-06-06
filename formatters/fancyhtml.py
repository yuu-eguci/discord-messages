"""Parsed JSONL を、クリックで開閉できる縦並びの HTML に変換します."""

from html import escape
from typing import Any


def _render_children(children: list[str]) -> str:
    if not children:
        return ""

    items = "\n".join(f"                <li>{escape(child)}</li>" for child in children)
    return f"\n            <ul class=\"children\">\n{items}\n            </ul>"


def _render_entry(entry: dict[str, Any]) -> str:
    heading = escape(str(entry.get("heading", "")))
    children = entry.get("children", [])
    if not isinstance(children, list):
        children = []
    child_texts = [str(child) for child in children]
    return (
        "        <details class=\"entry\">\n"
        f"            <summary>{heading}</summary>"
        f"{_render_children(child_texts)}\n"
        "        </details>"
    )


def format_fancyhtml(records: list[list[dict[str, Any]]]) -> str:
    blocks = []
    for record in records:
        if not record:
            continue
        entries = "\n".join(_render_entry(entry) for entry in record)
        blocks.append(f"    <section class=\"record\">\n{entries}\n    </section>")

    body = "\n".join(blocks)
    return (
        "<!doctype html>\n"
        '<html lang="ja">\n'
        "<head>\n"
        '    <meta charset="utf-8">\n'
        '    <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "    <title>Parsed JSONL</title>\n"
        "    <style>\n"
        "        :root {\n"
        "            color-scheme: light;\n"
        "        }\n"
        "        body {\n"
        "            margin: 0;\n"
        "            font-family: system-ui, sans-serif;\n"
        "            background: #f5f1e8;\n"
        "            color: #1f2933;\n"
        "        }\n"
        "        main {\n"
        "            max-width: 960px;\n"
        "            margin: 0 auto;\n"
        "            padding: 32px 20px 64px;\n"
        "        }\n"
        "        .record {\n"
        "            display: flex;\n"
        "            flex-direction: column;\n"
        "            gap: 12px;\n"
        "            margin-bottom: 24px;\n"
        "        }\n"
        "        .entry {\n"
        "            border: 1px solid #d4c8b8;\n"
        "            border-radius: 14px;\n"
        "            background: rgba(255, 255, 255, 0.78);\n"
        "            box-shadow: 0 8px 24px rgba(31, 41, 51, 0.08);\n"
        "            overflow: hidden;\n"
        "        }\n"
        "        .entry summary {\n"
        "            cursor: pointer;\n"
        "            list-style: none;\n"
        "            padding: 16px 18px;\n"
        "            font-weight: 700;\n"
        "            outline: none;\n"
        "        }\n"
        "        .entry summary::-webkit-details-marker {\n"
        "            display: none;\n"
        "        }\n"
        "        .entry[open] summary {\n"
        "            border-bottom: 1px solid #e6ddd0;\n"
        "        }\n"
        "        .children {\n"
        "            margin: 0;\n"
        "            padding: 14px 24px 18px 44px;\n"
        "        }\n"
        "        .children li {\n"
        "            margin: 6px 0;\n"
        "            line-height: 1.5;\n"
        "        }\n"
        "    </style>\n"
        "</head>\n"
        "<body>\n"
        "    <main>\n"
        f"{body}\n"
        "    </main>\n"
        "</body>\n"
        "</html>\n"
    )
