import argparse
import asyncio
import json
import logging
import os
from collections.abc import Sequence
from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Any

import discord

logger = logging.getLogger(__name__)
BOT_TOKEN_ENV = "DISCORD_BOT_TOKEN"


def _default_output() -> str:
    return "main_001_discord_to_jsonl.jsonl"


def _parse_date_from(value: str | None) -> datetime | None:
    if value is None:
        return None
    parsed_date = date.fromisoformat(value)
    return datetime.combine(parsed_date, time.min, tzinfo=UTC)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export Discord messages to JSONL.",
    )
    parser.add_argument(
        "--discord-bot-token",
        default=None,
        help=(
            "Discord bot token. Discord Application のページ (https://discord.com/developers/applications) にある。"
            f" 省略時は環境変数 {BOT_TOKEN_ENV} を使う。"
        ),
    )
    parser.add_argument(
        "--discord-channel-id",
        required=True,
        type=int,
        help="Discord channel ID. Developer mode を ON にして、チャネル右クリックで取得できる: https://qiita.com/ymzkjpx/items/8f42733d0fb67d454e27",
    )
    parser.add_argument(
        "--discord-user-id",
        default=None,
        type=int,
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


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """
    引数をパースします。 bot token は引数を優先し、無ければ環境変数から取ります。
    (シェル履歴やプロセス一覧に token を残したくないときは環境変数で渡してね。)
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.discord_bot_token:
        args.discord_bot_token = os.environ.get(BOT_TOKEN_ENV)
    if not args.discord_bot_token:
        parser.error(f"--discord-bot-token か環境変数 {BOT_TOKEN_ENV} が必要だよ。")
    return args


def build_intents() -> discord.Intents:
    """
    メッセージ本文を取得できるように intents を組み立てます。
    NOTE: Message.content を取得するには、 Application の Bot の設定で Message Content Intent ON が必要だし、
          こっちでこの設定↓も必要。
    """
    intents = discord.Intents.default()
    intents.message_content = True
    return intents


async def export_messages(
    channel: Any,
    output_path: Path,
    *,
    limit: int | None,
    after: datetime | None,
    user_id: int | None,
) -> None:
    """
    channel の履歴を古い順に JSONL へ書き出します。 user_id があればそのユーザのメッセージだけにします。
    NOTE: Discord クライアントから切り離しているのは、偽の channel でテストできるようにするため。
    """
    # Message の中身: https://discordpy.readthedocs.io/en/stable/api.html#discord.Message
    with output_path.open("w", encoding="utf-8") as output_file:
        async for message in channel.history(limit=limit, after=after, oldest_first=True):
            if user_id is not None and message.author.id != user_id:
                continue
            record = {
                "message_id": message.id,
                "author_id": message.author.id,
                "created_at": message.created_at.isoformat(),
                "content": message.content,
            }
            output_file.write(json.dumps(record, ensure_ascii=False) + "\n")


async def _run() -> None:
    args = parse_args()
    after = _parse_date_from(args.date_from)
    output_path = Path("output") / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    client = discord.Client(intents=build_intents())
    async with client:
        await client.login(args.discord_bot_token)
        channel = await client.fetch_channel(args.discord_channel_id)
        if not hasattr(channel, "history"):
            raise TypeError("指定された channel はメッセージ履歴を取得できない。")

        await export_messages(
            channel,
            output_path,
            limit=args.limit,
            after=after,
            user_id=args.discord_user_id,
        )

    logger.info("出力ファイル: %s", output_path)


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_run())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
