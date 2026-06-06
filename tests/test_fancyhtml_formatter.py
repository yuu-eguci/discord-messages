import unittest

from formatters.fancyhtml import format_fancyhtml


class FancyHtmlFormatterTests(unittest.TestCase):
    def test_renders_clickable_sections_with_children(self) -> None:
        html = format_fancyhtml(
            [
                [
                    {
                        "heading": "foo & bar",
                        "children": [
                            "baz <qux>",
                        ],
                    },
                ],
            ],
        )

        self.assertIn("<!doctype html>", html)
        self.assertIn("<details class=\"entry\">", html)
        self.assertIn("<summary>foo &amp; bar</summary>", html)
        self.assertIn("<li>baz &lt;qux&gt;</li>", html)

    def test_skips_empty_records(self) -> None:
        html = format_fancyhtml(
            [
                [],
                [
                    {
                        "heading": "foo",
                        "children": [
                            "bar",
                        ],
                    },
                ],
                [],
            ],
        )

        self.assertEqual(html.count("<section class=\"record\">"), 1)
        self.assertIn("<summary>foo</summary>", html)


if __name__ == "__main__":
    unittest.main()
