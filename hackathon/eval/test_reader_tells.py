import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reader_tells as rt  # noqa: E402


class TestTells(unittest.TestCase):
    def test_reader_examples_hit(self):
        self.assertEqual(rt.tells("9 years. 360 weddings. Countless Mondays lost to culling.\n\nI shot weddings.")["fragment_run"], 1)
        self.assertEqual(rt.tells("In testing, it culled 3,000 photos in 6 minutes. Six minutes.")["echo"], 1)
        self.assertEqual(rt.tells("Our secret weapon? The Shopify App Store.")["rhetorical_qa"], 1)
        self.assertGreaterEqual(rt.tells("Our secret weapon? The Shopify App Store.")["hook"], 1)
        self.assertEqual(rt.tells("Happy pets. Happy owners. Happy homes.")["slogan"], 1)
        self.assertEqual(rt.tells("No waiting rooms. Just calm care at home.")["slogan"], 1)
        self.assertEqual(rt.tells("What's Included: Everything You Need, Nothing You Don't")["tagline"], 1)
        self.assertEqual(rt.tells("But here's what got me. One in seven failures was flaky.")["hook"], 1)

    def test_plain_copy_is_clean(self):
        plain = ("Patchwork CI now runs on 1,200 repositories. When we launched, we promised it would always be free "
                 "for open source. Today about 900 of those repositories are open source.")
        self.assertFalse(any(rt.tells(plain).values()))

    def test_headings_and_lists_are_not_fragments(self):
        text = "What's Included\n1. Panels and an inverter\n2. Installation within 21 days\n3. A monitoring app"
        self.assertEqual(rt.tells(text)["fragment_run"], 0)

    def test_quoted_question_is_not_rhetorical(self):
        self.assertEqual(rt.tells('"Why bother?" she asked. We had no answer.')["rhetorical_qa"], 0)

    def test_two_fragments_are_not_a_run(self):
        self.assertEqual(rt.tells("Zero funding. A team of 3. We grew through the Shopify App Store.")["fragment_run"], 0)


if __name__ == "__main__":
    unittest.main()
