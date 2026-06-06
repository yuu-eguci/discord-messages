import unittest

from parsers.default import parse_default_content


class ParseDefaultContentTests(unittest.TestCase):
    def test_extracts_headings_and_children(self) -> None:
        content = "\n".join(
            [
                "- foo",
                "    - bar",
                "    + baz",
                "    * qux",
                "- quux",
                "    - corge",
            ],
        )

        self.assertEqual(
            parse_default_content(content),
            [
                {
                    "heading": "foo",
                    "children": [
                        "bar",
                        "baz",
                        "qux",
                    ],
                },
                {
                    "heading": "quux",
                    "children": [
                        "corge",
                    ],
                },
            ],
        )

    def test_ignores_non_list_lines_and_children_before_heading(self) -> None:
        content = "\n".join(
            [
                "plain text",
                "    - ignored child",
                "",
                "* heading",
                "    - child",
                "not a list again",
            ],
        )

        self.assertEqual(
            parse_default_content(content),
            [
                {
                    "heading": "heading",
                    "children": [
                        "child",
                    ],
                },
            ],
        )


if __name__ == "__main__":
    unittest.main()

