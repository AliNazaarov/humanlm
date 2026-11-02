"""Offline tests for collect_real.extract_intro / clean_markdown (no network)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collect_real as cr  # noqa: E402

PROSE = ("Acme is a small tool that turns your meeting notes into tasks. It reads the notes you already keep, "
         "finds the action items, and files them in the tracker your team uses. Nothing leaves your laptop, "
         "and there is no account to create. We built it because we kept losing follow-ups after long calls, "
         "and every app we tried wanted us to change how we write notes.")  # 68 words

README = f"""<p align="center"><img src="logo.png" width="120"></p>

# Acme

[![CI](https://img.shields.io/badge/ci-passing-green)](https://ci.example) [![npm](https://img.shields.io/npm/v/acme)](https://npm.im/acme)

[Docs](https://docs.example) · [Discord](https://discord.gg/x) · [Website](https://acme.example)

{PROSE.replace("tracker", "[tracker](https://tracker.example)")}

| Feature | Acme |
|---|---|
| Local | yes |

```bash
npm install acme
```

## Installation

Run `npm install acme` and then follow the setup wizard to connect your tracker account today.
"""


class TestExtract(unittest.TestCase):
    def test_strips_badges_images_links_tables_code(self):
        text, why = cr.extract_intro(README)
        self.assertEqual(why, "ok")
        for junk in ("shields.io", "![", "](", "<img", "|", "```", "npm install", "Discord", "http"):
            self.assertNotIn(junk, text)
        self.assertIn("files them in the tracker your team uses", text)  # link text kept, url gone
        self.assertTrue(text.startswith("Acme\n\n"))  # title kept on its own line
        self.assertNotIn("Installation", text)  # stops at the first H2

    def test_word_count_filter(self):
        short = "# Tiny\n\n" + PROSE.split(" Nothing")[0].replace(". ", ".\n\n") + "\n"  # 2 prose paras, < 60 words
        self.assertEqual(cr.extract_intro(short), (None, "too_short"))
        long_para = "# Big\n\n" + " ".join([PROSE] * 4) + "\n"  # one 272-word paragraph
        self.assertEqual(cr.extract_intro(long_para), (None, "too_long"))
        # several paragraphs: trimmed at a paragraph boundary to <= MAX_WORDS
        multi = "# Big\n\n" + "\n\n".join([PROSE] * 5) + "\n"
        text, why = cr.extract_intro(multi)
        self.assertEqual(why, "ok")
        n = len(cr.m.words(text))
        self.assertTrue(cr.MIN_WORDS <= n <= cr.MAX_WORDS, n)

    def test_list_only_and_non_english_skipped(self):
        lst = "# L\n\n" + "\n".join(f"- feature number {i} makes your work faster and easier than before" for i in range(12))
        self.assertEqual(cr.extract_intro(lst)[1], "list_only")
        zh = "# 工具\n\n" + "这是一个非常好用的工具，可以帮助你管理任务和笔记，并且完全在本地运行。" * 8
        self.assertIsNone(cr.extract_intro(zh)[0])

    def test_soft_wrapped_lines_are_joined(self):
        md = "# W\n\n" + PROSE.replace(". ", ".\n") + "\n"
        text, _ = cr.extract_intro(md)
        self.assertEqual(text.split("\n\n")[1], PROSE)

    def test_leakage_ngrams(self):
        a = "one two three four five six seven eight nine"
        self.assertTrue(cr.ngrams(a) & cr.ngrams("zero " + a))
        self.assertFalse(cr.ngrams("one two three four five six seven") & cr.ngrams(a))


if __name__ == "__main__":
    unittest.main()
