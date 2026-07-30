import unittest

from lottery_config import LOTTERIES


class LotteryConfigTest(unittest.TestCase):
    def test_ssq_and_dlt_have_independent_ranges(self):
        self.assertEqual(LOTTERIES["ssq"].areas[0].max_number, 33)
        self.assertEqual(LOTTERIES["ssq"].areas[1].max_number, 16)
        self.assertEqual(LOTTERIES["dlt"].areas[0].max_number, 35)
        self.assertEqual(LOTTERIES["dlt"].areas[1].max_number, 12)

    def test_each_lottery_has_source_and_disclaimer_name(self):
        self.assertEqual(LOTTERIES["ssq"].official_source, "中国福彩网")
        self.assertEqual(LOTTERIES["dlt"].official_source, "中国体彩网")

    def test_number_lotteries_allow_repeated_ordered_digits(self):
        for lottery_id in ("fc3d", "pl3", "pl5", "qxc"):
            area = LOTTERIES[lottery_id].areas[0]
            self.assertEqual(area.min_number, 0)
            self.assertEqual(area.max_number, 9)
            self.assertTrue(area.ordered)
            self.assertFalse(area.unique)

    def test_qlc_uses_own_thirty_number_range(self):
        self.assertEqual(LOTTERIES["qlc"].areas[0].count, 7)
        self.assertEqual(LOTTERIES["qlc"].areas[0].max_number, 30)
        self.assertEqual(LOTTERIES["qlc"].areas[1].count, 1)
        self.assertEqual(LOTTERIES["qlc"].areas[1].max_number, 30)


if __name__ == "__main__":
    unittest.main()
