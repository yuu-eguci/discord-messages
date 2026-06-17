import argparse
import json
import logging
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta, timezone
from itertools import islice
from pathlib import Path
from typing import Any

from parsers.default import parse_default_content

logger = logging.getLogger(__name__)
JST = timezone(timedelta(hours=9))


def _default_output() -> str:
    return "main_002_rawjsonl_to_parsedjsonl.jsonl"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Parse raw JSONL exported from Discord messages into JSONL.",
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Input raw JSONL file path.",
    )
    parser.add_argument(
        "--output",
        default=_default_output(),
        type=Path,
        help="Output JSONL file path.",
    )
    parser.add_argument(
        "--limit",
        default=None,
        type=int,
        help="Record parse limit.",
    )
    parser.add_argument(
        "--parser",
        default="default",
        help="Parser name.",
    )
    return parser


def _parse_content(content: str, parser_name: str) -> list[dict[str, object]]:
    if parser_name == "default":
        return parse_default_content(content)
    raise ValueError(f"Unknown parser: {parser_name}")


def _iter_records(input_path: Path, limit: int | None) -> list[dict[str, Any]]:
    with input_path.open("r", encoding="utf-8") as input_file:
        records: Iterable[dict[str, Any]] = (
            json.loads(line)
            for line in input_file
            if line.strip()
        )
        if limit is not None:
            return list(islice(records, limit))
        return list(records)


def _format_created_at_jst(value: object) -> str:
    if not isinstance(value, str):
        return ""

    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(JST).isoformat()


def _build_content_preview(content: object) -> str:
    if not isinstance(content, str):
        return "..."

    normalized = " ".join(content.split())
    return f"{normalized[:20]}..."


def _warn_empty_parsed_record(content: object, created_at: object) -> None:
    logger.warning(
        "パースできなくて空っぽになってるメッセージがある: content_preview=%s created_at=%s",
        _build_content_preview(content),
        _format_created_at_jst(created_at),
    )


def _warn_entries_without_children(
    parsed: list[dict[str, object]],
    created_at: object,
) -> None:
    created_at_jst = _format_created_at_jst(created_at)

    for entry in parsed:
        heading = entry.get("heading")
        children = entry.get("children")
        if not isinstance(heading, str) or not heading:
            continue
        if isinstance(children, list) and not children:
            logger.warning(
                "heading はあるけど children のないメッセージがある: heading=%s created_at=%s",
                heading,
                created_at_jst,
            )


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    args = build_parser().parse_args()
    records = _iter_records(args.input, args.limit)
    output_path = Path("output") / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as output_file:
        for record in records:
            content = record.get("content", "")
            if not isinstance(content, str):
                content = str(content)
            parsed = _parse_content(content, args.parser)
            if not parsed:
                _warn_empty_parsed_record(content, record.get("created_at"))
            _warn_entries_without_children(parsed, record.get("created_at"))
            output_file.write(json.dumps(parsed, ensure_ascii=False) + "\n")

    logger.info("出力ファイル: %s", output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
