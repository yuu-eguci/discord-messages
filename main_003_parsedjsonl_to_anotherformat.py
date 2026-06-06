import argparse
from pathlib import Path


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


def main() -> int:
    args = build_parser().parse_args()
    if args.output is None:
        args.output = Path(_default_output(args.format))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
