import contextlib
import json
import logging
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from main_003_parsedjsonl_to_anotherformat import main


class Main003MainTests(unittest.TestCase):
    def _run_main(self, *extra_args: str) -> dict[str, str]:
        parsed_records = [[{"heading": "foo", "children": ["bar", "baz"]}], []]
        with tempfile.TemporaryDirectory() as temp_dir, contextlib.chdir(temp_dir):
            input_path = Path(temp_dir) / "parsed.jsonl"
            input_path.write_text(
                "".join(json.dumps(record) + "\n" for record in parsed_records),
                encoding="utf-8",
            )
            argv = ["main_003", "--input", str(input_path), *extra_args]
            with (
                mock.patch("sys.argv", argv),
                mock.patch("logging.basicConfig"),
                self.assertLogs("main_003_parsedjsonl_to_anotherformat", level=logging.INFO),
            ):
                self.assertEqual(main(), 0)
            output_dir = Path(temp_dir) / "output"
            return {path.name: path.read_text(encoding="utf-8") for path in output_dir.iterdir()}

    def test_writes_anki_text_to_default_output_by_default(self) -> None:
        self.assertEqual(
            self._run_main(),
            {
                "main_003_parsedjsonl_to_anotherformat_anki.txt": (
                    "#separator:tab\n#html:true\nfoo\tbar<br />baz\tdiscord\n"
                ),
            },
        )

    def test_writes_fancyhtml_to_given_output(self) -> None:
        outputs = self._run_main("--format", "fancyhtml", "--output", "cards.html")

        self.assertEqual(list(outputs), ["cards.html"])
        self.assertIn("<summary>foo</summary>", outputs["cards.html"])


if __name__ == "__main__":
    unittest.main()
