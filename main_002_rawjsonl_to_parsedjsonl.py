import argparse
from datetime import date
from pathlib import Path


def _default_output() -> str:
    return f"({date.today():%Y-%m-%d})main_002_rawjsonl_to_parsedjsonl.jsonl"


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


def main() -> int:
    build_parser().parse_args()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
