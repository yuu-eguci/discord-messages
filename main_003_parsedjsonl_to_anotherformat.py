import argparse
import json
import logging
from pathlib import Path
from typing import Any

from formatters.fancyhtml import format_fancyhtml

logger = logging.getLogger(__name__)


def _default_output(format_name: str) -> str:
    return f"main_003_parsedjsonl_to_anotherformat_{format_name}.jsonl"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert parsed JSONL into another format.",
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Input parsed JSONL file path.",
    )
    parser.add_argument(
        "--format",
        default="anki",
        choices=["anki", "fancyhtml"],
        help="Output format name.",
    )
    parser.add_argument(
        "--output",
        default=None,
        type=Path,
        help="Output file path.",
    )
    return parser


def _load_records(input_path: Path) -> list[list[dict[str, Any]]]:
    with input_path.open("r", encoding="utf-8") as input_file:
        return [
            json.loads(line)
            for line in input_file
            if line.strip()
        ]


def _format_records(records: list[list[dict[str, Any]]], format_name: str) -> str:
    if format_name == "fancyhtml":
        return format_fancyhtml(records)
    if format_name == "anki":
        return "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n"
    raise ValueError(f"Unknown format: {format_name}")


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    args = build_parser().parse_args()
    output_name = args.output if args.output is not None else Path(_default_output(args.format))
    output_path = Path("output") / output_name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    records = _load_records(args.input)
    rendered = _format_records(records, args.format)

    output_path.write_text(rendered, encoding="utf-8")
    logger.info("出力ファイル: %s", output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
