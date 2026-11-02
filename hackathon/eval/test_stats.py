import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stats as s  # noqa: E402


class TestBootstrap(unittest.TestCase):
    def test_fixed_array_mean_inside_ci(self):
        point, lo, hi = s.bootstrap_ci([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.assertEqual(point, 5.5)
        self.assertLess(lo, point)
        self.assertGreater(hi, point)

    def test_deterministic_for_seed(self):
        v = [0, 1, 1, 0, 1, 0, 0, 1, 1, 1]
        self.assertEqual(s.bootstrap_ci(v, seed=3), s.bootstrap_ci(v, seed=3))

    def test_all_zero_bootstrap_is_degenerate(self):  # why rates use rate_ci instead
        self.assertEqual(s.bootstrap_ci([0] * 130), (0.0, 0.0, 0.0))

    def test_empty_and_nan_raise(self):
        with self.assertRaises(ValueError):
            s.bootstrap_ci([])
        with self.assertRaises(ValueError):
            s.bootstrap_ci([1.0, None])

    def test_non_mean_stat(self):
        point, lo, hi = s.bootstrap_ci(list(range(100)), stat=lambda a: float(s.np.percentile(a, 95)))
        self.assertTrue(lo <= point <= hi)


class TestRate(unittest.TestCase):
    def test_zero_events_has_real_upper_bound(self):
        rate, lo, hi = s.rate_ci(0, 130)
        self.assertEqual((rate, lo), (0.0, 0.0))
        self.assertGreater(hi, 0.02)  # rule of three: about 3/130

    def test_bad_counts_raise(self):
        with self.assertRaises(ValueError):
            s.rate_ci(5, 3)


class TestPaired(unittest.TestCase):
    def test_identical_systems(self):
        v = [0, 1, 0, 0, 1, 1, 0, 1]
        self.assertEqual(s.paired_bootstrap_diff(v, v), (0.0, 0.0, 0.0, 1.0))

    def test_separated_systems_significant(self):
        a = [1] * 40 + [0] * 90   # 31% fail
        b = [1] * 5 + [0] * 125   # 4% fail
        diff, lo, hi, p = s.paired_bootstrap_diff(a, b)
        self.assertGreater(lo, 0)
        self.assertLess(p, 0.05)
        self.assertGreater(p, 0)  # never reported as exactly 0

    def test_tie_heavy_small_difference_not_significant(self):
        a = [1, 0] + [0] * 128
        b = [0, 1] + [0] * 128
        diff, lo, hi, p = s.paired_bootstrap_diff(a, b)
        self.assertEqual(diff, 0.0)
        self.assertLessEqual(lo, 0)
        self.assertGreaterEqual(hi, 0)
        self.assertGreater(p, 0.5)

    def test_ci_excluding_zero_agrees_with_p(self):
        a = [1] * 20 + [0] * 110
        b = [1] * 8 + [0] * 122
        diff, lo, hi, p = s.paired_bootstrap_diff(a, b)
        if lo > 0:
            self.assertLess(p, 0.05)

    def test_unaligned_raises(self):
        with self.assertRaises(ValueError):
            s.paired_bootstrap_diff([1, 2], [1])


class TestSmall(unittest.TestCase):
    def test_sign_test(self):
        self.assertLess(s.judge_sign_test(15, 2), 0.01)
        self.assertEqual(s.judge_sign_test(0, 0), 1.0)
        with self.assertRaises(ValueError):
            s.judge_sign_test(-1, 2)

    def test_percentiles_and_cost(self):
        self.assertEqual(s.percentiles([1, 2, 3, 4, 5])["p50"], 3.0)
        self.assertAlmostEqual(s.cost_per_1k([0.001, 0.003]), 2.0)


if __name__ == "__main__":
    unittest.main()
