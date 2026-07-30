import unittest

from lottery_rules import check_prize


class LotteryRulesTest(unittest.TestCase):
    def test_ssq_first_and_sixth_prize(self):
        draw = {"Red": "01,02,03,04,05,06", "Blue": "07"}
        self.assertEqual(check_prize("ssq", draw, [[1, 2, 3, 4, 5, 6], [7]])["level"], "一等奖")
        self.assertEqual(check_prize("ssq", draw, [[8, 9, 10, 11, 12, 13], [7]])["level"], "六等奖")

    def test_dlt_first_and_eighth_prize(self):
        draw = {"Front": "01,02,03,04,05", "Back": "06,07"}
        self.assertEqual(check_prize("dlt", draw, [[1, 2, 3, 4, 5], [6, 7]])["level"], "一等奖")
        self.assertEqual(check_prize("dlt", draw, [[1, 2, 8, 9, 10], [6, 7]])["level"], "八等奖")

    def test_dlt_ninth_prize(self):
        draw = {"Front": "01,02,03,04,05", "Back": "06,07"}
        self.assertEqual(check_prize("dlt", draw, [[1, 8, 9, 10, 11], [6, 7]])["level"], "九等奖")


if __name__ == "__main__":
    unittest.main()
