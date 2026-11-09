import contextlib
import io
import json
import os
import tempfile
import unittest
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from main_001_discord_to_jsonl import _parse_date_from, export_messages, parse_args


class FakeChannel:
    """
    discord の channel の代わりです。 history() に渡された引数を覚えておき、合成メッセージを返します。
    """

    def __init__(self, messages: list[SimpleNamespace]) -> None:
        self.messages = messages
        self.history_kwargs: dict[str, object] = {}

    async def history(self, **kwargs: object) -> AsyncIterator[SimpleNamespace]:
        self.history_kwargs = kwargs
        for message in self.messages:
            yield message


def _message(message_id: int, author_id: int, content: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=message_id,
        author=SimpleNamespace(id=author_id),
        created_at=datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
        content=content,
    )


class ParseArgsTests(unittest.TestCase):
    def test_uses_bot_token_from_argument(self) -> None:
        with mock.patch.dict(os.environ, {"DISCORD_BOT_TOKEN": "env-token"}):
            args = parse_args(["--discord-bot-token", "arg-token", "--discord-channel-id", "1"])

        self.assertEqual(args.discord_bot_token, "arg-token")
        self.assertEqual(args.discord_channel_id, 1)

    def test_falls_back_to_bot_token_from_environment(self) -> None:
        with mock.patch.dict(os.environ, {"DISCORD_BOT_TOKEN": "env-token"}):
            args = parse_args(["--discord-channel-id", "1"])

        self.assertEqual(args.discord_bot_token, "env-token")

    def test_errors_when_bot_token_is_missing(self) -> None:
        with (
            mock.patch.dict(os.environ, {}, clear=True),
            contextlib.redirect_stderr(io.StringIO()) as stderr,
            self.assertRaises(SystemExit),
        ):
            parse_args(["--discord-channel-id", "1"])

        self.assertIn("DISCORD_BOT_TOKEN", stderr.getvalue())

    def test_rejects_removed_unused_arguments(self) -> None:
        for removed in ("--discord-application-id", "--discord-public-key"):
            with (
                self.subTest(removed=removed),
                contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit),
            ):
                parse_args(["--discord-bot-token", "t", "--discord-channel-id", "1", removed, "x"])


class ParseDateFromTests(unittest.TestCase):
    def test_converts_date_to_utc_midnight(self) -> None:
        self.assertEqual(_parse_date_from("2026-01-02"), datetime(2026, 1, 2, tzinfo=UTC))

    def test_returns_none_when_not_given(self) -> None:
        self.assertIsNone(_parse_date_from(None))


class ExportMessagesTests(unittest.IsolatedAsyncioTestCase):
    async def test_writes_messages_as_jsonl_oldest_first(self) -> None:
        channel = FakeChannel([_message(1, 10, "- 見出し\n    - 子"), _message(2, 20, "two")])
        after = datetime(2026, 1, 1, tzinfo=UTC)

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "out.jsonl"
            await export_messages(channel, output_path, limit=5, after=after, user_id=None)
            lines = output_path.read_text(encoding="utf-8").splitlines()

        self.assertEqual(channel.history_kwargs, {"limit": 5, "after": after, "oldest_first": True})
        self.assertEqual(
            [json.loads(line) for line in lines],
            [
                {
                    "message_id": 1,
                    "author_id": 10,
                    "created_at": "2026-01-02T03:04:05+00:00",
                    "content": "- 見出し\n    - 子",
                },
                {"message_id": 2, "author_id": 20, "created_at": "2026-01-02T03:04:05+00:00", "content": "two"},
            ],
        )
        # 日本語はエスケープせずそのまま書きます。
        self.assertIn("見出し", lines[0])

    async def test_keeps_only_messages_from_given_user(self) -> None:
        channel = FakeChannel([_message(1, 10, "a"), _message(2, 20, "b"), _message(3, 10, "c")])

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "out.jsonl"
            await export_messages(channel, output_path, limit=None, after=None, user_id=10)
            records = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual([record["message_id"] for record in records], [1, 3])


if __name__ == "__main__":
    unittest.main()
