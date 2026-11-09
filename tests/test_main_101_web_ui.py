import asyncio
import sys
import unittest
from unittest import mock

from fastapi.testclient import TestClient

import main_101_web_ui


class TrustedHostTests(unittest.TestCase):
    def test_rejects_unknown_host_header(self) -> None:
        # DNS rebinding で別ドメイン経由のアクセスが来たケース。
        client = TestClient(main_101_web_ui.app, base_url="http://evil.example")

        response = client.get("/api/defaults")

        self.assertEqual(response.status_code, 400)

    def test_accepts_localhost_and_loopback_with_any_port(self) -> None:
        for base_url in ("http://localhost:8000", "http://127.0.0.1:8080"):
            with self.subTest(base_url=base_url):
                client = TestClient(main_101_web_ui.app, base_url=base_url)

                response = client.get("/")

                self.assertEqual(response.status_code, 200)


class CrossOriginPostTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(main_101_web_ui.app, base_url="http://localhost:8080")
        patcher = mock.patch.object(main_101_web_ui, "_server", mock.Mock(should_exit=False))
        self.server = patcher.start()
        self.addCleanup(patcher.stop)

    def test_rejects_post_from_another_origin(self) -> None:
        response = self.client.post("/api/shutdown", headers={"Origin": "http://evil.example"})

        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.server.should_exit)

    def test_accepts_post_from_same_origin_or_without_origin(self) -> None:
        for headers in ({"Origin": "http://localhost:8080"}, {}):
            with self.subTest(headers=headers):
                response = self.client.post("/api/shutdown", headers=headers)

                self.assertEqual(response.status_code, 200)

        self.assertTrue(self.server.should_exit)


class RunRequestTests(unittest.TestCase):
    def test_requires_only_bot_token_and_channel_id(self) -> None:
        request = main_101_web_ui.RunRequest(discord_bot_token="token", discord_channel_id=1)

        self.assertEqual(request.discord_channel_id, 1)

    def test_rejects_missing_bot_token_unless_dry_run(self) -> None:
        with self.assertRaises(ValueError):
            main_101_web_ui.RunRequest(discord_channel_id=1)

        self.assertTrue(main_101_web_ui.RunRequest(dry_run=True).dry_run)


class BuildCommandsTests(unittest.TestCase):
    def test_passes_bot_token_by_environment_not_by_argument(self) -> None:
        request = main_101_web_ui.RunRequest(
            discord_bot_token="secret-token",
            discord_channel_id=1,
            discord_user_id=2,
            date_from="2026-01-01",
            limit=3,
            format="fancyhtml",
        )

        commands = main_101_web_ui._build_commands(request)
        env = main_101_web_ui._build_env(request)

        for _, command in commands:
            self.assertNotIn("secret-token", command)
        self.assertEqual(env["DISCORD_BOT_TOKEN"], "secret-token")
        self.assertEqual(
            commands[0][1][1:],
            [
                main_101_web_ui.SCRIPT_001,
                "--discord-channel-id",
                "1",
                "--discord-user-id",
                "2",
                "--date-from",
                "2026-01-01",
                "--limit",
                "3",
            ],
        )
        self.assertEqual(commands[2][1][-2:], ["--format", "fancyhtml"])


class RunScriptTests(unittest.IsolatedAsyncioTestCase):
    async def test_streams_output_with_given_environment(self) -> None:
        queue: asyncio.Queue = asyncio.Queue()
        command = [sys.executable, "-c", "import os; print(os.environ['DISCORD_BOT_TOKEN'] == 'secret-token')"]

        await main_101_web_ui._run_script(queue, 1, "fake.py", command, {"DISCORD_BOT_TOKEN": "secret-token"})

        events = [queue.get_nowait() for _ in range(queue.qsize())]
        self.assertEqual(
            events,
            [
                {"type": "step_start", "step": 1, "script": "fake.py"},
                {"type": "log", "step": 1, "line": "True"},
                {"type": "step_end", "step": 1, "script": "fake.py"},
            ],
        )

    async def test_raises_when_script_fails(self) -> None:
        queue: asyncio.Queue = asyncio.Queue()

        with self.assertRaises(RuntimeError):
            await main_101_web_ui._run_script(queue, 1, "fake.py", [sys.executable, "-c", "raise SystemExit(3)"], {})


if __name__ == "__main__":
    unittest.main()
