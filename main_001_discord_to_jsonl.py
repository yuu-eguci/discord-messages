import argparse
from datetime import date
from pathlib import Path


def _default_output() -> str:
    return f"{date.today():%Y-%m-%d}main_001_discord_to_jsonl.jsonl"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export Discord messages to JSONL.",
    )
    parser.add_argument(
        "--discord-application-id",
        required=True,
        help="Discord application ID. よくわかんなかったらここ行って: https://discord.com/developers/applications",
    )
    parser.add_argument(
        "--discord-public-key",
        required=True,
        help="Discord public key. これも Discord Application のページにある。",
    )
    parser.add_argument(
        "--discord-bot-token",
        required=True,
        help="Discord bot token. これも Discord Application のページにある。 Bot は application の下位リソース。",
    )
    parser.add_argument(
        "--discord-channel-id",
        required=True,
        help="Discord channel ID. Developer mode を ON にして、チャネル右クリックで取得できる: https://qiita.com/ymzkjpx/items/8f42733d0fb67d454e27",
    )
    parser.add_argument(
        "--discord-user-id",
        default=None,
        help="Discord user ID. これも Developer mode を ON にして、ユーザ右クリックで取得できる。",
    )
    parser.add_argument(
        "--output",
        default=_default_output(),
        type=Path,
        help="Output JSONL file path.",
    )
    parser.add_argument(
        "--date-from",
        default=None,
        help="Start date filter.",
    )
    parser.add_argument(
        "--limit",
        default=None,
        type=int,
        help="Message fetch limit.",
    )
    return parser


def main() -> int:
    build_parser().parse_args()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
