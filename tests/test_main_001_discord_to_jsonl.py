import contextlib
import io
import os
import unittest
from unittest import mock

from main_001_discord_to_jsonl import parse_args


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


if __name__ == "__main__":
    unittest.main()
