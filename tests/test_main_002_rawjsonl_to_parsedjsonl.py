import logging
import unittest

from main_002_rawjsonl_to_parsedjsonl import (
    _build_content_preview,
    _format_created_at_jst,
    _warn_empty_parsed_record,
    _warn_entries_without_children,
)


class Main002ValidationTests(unittest.TestCase):
    def test_formats_created_at_to_jst(self) -> None:
        self.assertEqual(
            _format_created_at_jst("2026-06-17T00:00:00+00:00"),
            "2026-06-17T09:00:00+09:00",
        )

    def test_builds_content_preview_with_ellipsis(self) -> None:
        self.assertEqual(
            _build_content_preview("  foo\nbar baz qux quux corge grault  "),
            "foo bar baz qux quux...",
        )

    def test_warns_when_parsed_record_is_empty(self) -> None:
        with self.assertLogs("main_002_rawjsonl_to_parsedjsonl", level=logging.WARNING) as captured:
            _warn_empty_parsed_record(
                "  foo\nbar baz qux quux corge grault  ",
                "2026-06-17T00:00:00+00:00",
            )

        self.assertEqual(len(captured.output), 1)
        self.assertIn("content_preview=foo bar baz qux quux...", captured.output[0])
        self.assertIn("created_at=2026-06-17T09:00:00+09:00", captured.output[0])

    def test_warns_when_heading_has_no_children(self) -> None:
        parsed: list[dict[str, object]] = [
            {
                "heading": "foo",
                "children": [],
            },
            {
                "heading": "bar",
                "children": [
                    "baz",
                ],
            },
        ]

        with self.assertLogs("main_002_rawjsonl_to_parsedjsonl", level=logging.WARNING) as captured:
            _warn_entries_without_children(parsed, "2026-06-17T00:00:00+00:00")

        self.assertEqual(len(captured.output), 1)
        self.assertIn("heading=foo", captured.output[0])
        self.assertIn("created_at=2026-06-17T09:00:00+09:00", captured.output[0])

    def test_does_not_warn_when_heading_has_children(self) -> None:
        parsed: list[dict[str, object]] = [
            {
                "heading": "foo",
                "children": [
                    "bar",
                ],
            },
        ]

        with self.assertNoLogs("main_002_rawjsonl_to_parsedjsonl", level=logging.WARNING):
            _warn_entries_without_children(parsed, "2026-06-17T00:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
