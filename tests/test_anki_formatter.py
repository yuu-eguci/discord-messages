import unittest

from formatters.anki import format_anki


class AnkiFormatterTests(unittest.TestCase):
    def test_renders_tab_separated_cards(self) -> None:
        text = format_anki(
            [
                [
                    {
                        "heading": "foo",
                        "children": [
                            "bar",
                            "baz",
                        ],
                    },
                    {
                        "heading": "qux",
                        "children": [
                            "quux",
                        ],
                    },
                ],
            ],
        )

        self.assertEqual(
            text,
            "#separator:tab\n#html:false\nfoo\tbar<br />baz\tdiscord\nqux\tquux\tdiscord\n",
        )


if __name__ == "__main__":
    unittest.main()

