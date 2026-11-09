import unittest

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


if __name__ == "__main__":
    unittest.main()
