import contextlib
import json
import logging
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from main_002_rawjsonl_to_parsedjsonl import (
    _build_content_preview,
    _format_created_at_jst,
    _warn_empty_parsed_record,
    _warn_entries_without_children,
    main,
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


class Main002MainTests(unittest.TestCase):
    def _run_main(self, raw_records: list[dict[str, object]], *extra_args: str) -> list[object]:
        with tempfile.TemporaryDirectory() as temp_dir, contextlib.chdir(temp_dir):
            input_path = Path(temp_dir) / "raw.jsonl"
            input_path.write_text(
                "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in raw_records) + "\n",
                encoding="utf-8",
            )
            argv = ["main_002", "--input", str(input_path), "--output", "parsed.jsonl", *extra_args]
            with (
                mock.patch("sys.argv", argv),
                mock.patch("logging.basicConfig"),
                self.assertLogs("main_002_rawjsonl_to_parsedjsonl", level=logging.INFO),
            ):
                self.assertEqual(main(), 0)
            output_lines = (Path(temp_dir) / "output" / "parsed.jsonl").read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in output_lines]

    def test_parses_each_raw_record_into_one_output_line(self) -> None:
        raw_records: list[dict[str, object]] = [
            {"created_at": "2026-01-01T00:00:00+00:00", "content": "- foo\n    - bar"},
            {"created_at": "2026-01-01T00:00:00+00:00", "content": "ただの雑談"},
        ]

        self.assertEqual(
            self._run_main(raw_records),
            [[{"heading": "foo", "children": ["bar"]}], []],
        )

    def test_limits_number_of_records(self) -> None:
        raw_records: list[dict[str, object]] = [{"content": f"- h{index}\n    - c"} for index in range(3)]

        self.assertEqual(len(self._run_main(raw_records, "--limit", "2")), 2)


if __name__ == "__main__":
    unittest.main()
