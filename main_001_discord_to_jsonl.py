import argparse
import asyncio
import json
from datetime import UTC, date, datetime, time
from pathlib import Path

import discord


def _default_output() -> str:
    return f"{date.today():%Y-%m-%d}main_001_discord_to_jsonl.jsonl"


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
        "--discord-application-id",
        required=True,
        type=int,
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


def build_intents() -> discord.Intents:
    """
    メッセージ本文を取得できるように intents を組み立てます。
    NOTE: Message.content を取得するには、 Application の Bot の設定で Message Content Intent ON が必要だし、
          こっちでこの設定↓も必要。
    """
    intents = discord.Intents.default()
    intents.message_content = True
    return intents


async def _run() -> None:
    args = build_parser().parse_args()
    after = _parse_date_from(args.date_from)

    client = discord.Client(intents=build_intents())
    async with client:
        await client.login(args.discord_bot_token)
        channel = await client.fetch_channel(args.discord_channel_id)
        if not hasattr(channel, "history"):
            raise TypeError("指定された channel はメッセージ履歴を取得できない。")

        # Message の中身: https://discordpy.readthedocs.io/en/v2.3.2/api.html#discord.Message
        async for message in channel.history(
            limit=args.limit,
            after=after,
            oldest_first=True,
        ):
            if args.discord_user_id is not None and message.author.id != args.discord_user_id:
                continue
            print(
                json.dumps(
                    {
                        "message_id": message.id,
                        "author_id": message.author.id,
                        "created_at": message.created_at.isoformat(),
                        "content": message.content,
                    },
                    ensure_ascii=False,
                ),
            )


def main() -> int:
    asyncio.run(_run())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
