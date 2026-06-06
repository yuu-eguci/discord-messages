import argparse
import json
import logging
from collections.abc import Iterable
from itertools import islice
from pathlib import Path
from typing import Any

from parsers.default import parse_default_content

logger = logging.getLogger(__name__)


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
            output_file.write(json.dumps(parsed, ensure_ascii=False) + "\n")

    logger.info("出力ファイル: %s", output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
