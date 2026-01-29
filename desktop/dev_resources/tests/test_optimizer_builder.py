import unittest
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(project_root)

from features.optimizer_run_summary import RunSummaryBuilder

class TestRunSummaryBuilder(unittest.TestCase):
    
    def setUp(self):
        # Fixture based on PRD schema
        self.mock_run_outputs = {
            "bids_old": {
                "t1": 1.0, "t2": 0.5, "t3": 2.0, "t4": 1.0
            },
            "bids_new": {
                "t1": 1.5, "t2": 0.4, "t3": 2.0, "t4": 0.0 # Paused
            },
            "negatives": ["n1", "n2"],
            "paused": ["t4"], # t4 is paused via bid=0
            "harvested": ["h1", "h2", "h3"],
            "term_metrics": {
                "t1": {"spend_14d": 100, "sales_14d": 500},
                "t2": {"spend_14d": 50, "sales_14d": 10},
                "t3": {"spend_14d": 200, "sales_14d": 800},
                "t4": {"spend_14d": 80, "sales_14d": 0}, # Wasted spend
                "n1": {"spend_14d": 120, "sales_14d": 0}, # Wasted spend
                "n2": {"spend_14d": 30, "sales_14d": 0}  # Wasted spend
            },
            "simulation": {
                "old_acos": 30.0,
                "new_acos": 25.0
            },
            "run_metadata": {"timestamp": "2023-01-01"}
        }
        self.builder = RunSummaryBuilder(self.mock_run_outputs)

    def test_waste_prevented(self):
        # Waste = spend of negatives + paused
        # n1 (120) + n2 (30) + t4 (80) = 230
        summary = self.builder.build()
        self.assertEqual(summary["waste_prevented"], 230.0)

    def test_efficiency_gain(self):
        # Gain = (30 - 25) / 30 = 0.1666...
        summary = self.builder.build()
        self.assertAlmostEqual(summary["efficiency_gain"], 0.166666, places=5)

    def test_bid_stats(self):
        # t1: 1.0 -> 1.5 (Inc)
        # t2: 0.5 -> 0.4 (Dec)
        # t3: 2.0 -> 2.0 (Unchanged)
        # t4: 1.0 -> 0.0 (Dec)
        # Total: 1 Inc, 2 Dec, 1 Unchanged
        stats = self.builder.build()["bid_stats"]
        self.assertEqual(stats["increases"], 1)
        self.assertEqual(stats["decreases"], 2)
        self.assertEqual(stats["unchanged"], 1)

    def test_top_opportunities(self):
        # Opportunities: only bid increases with sales
        # t1: Bid 1.0->1.5 (+50%), Sales 500 -> Uplift = 500 * 0.5 = 250
        # t3: Unchanged -> Skip
        # t2: Decrease -> Skip
        ops = self.builder.build()["top_opportunities"]
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0]["target_id"], "t1")
        self.assertEqual(ops[0]["uplift"], 250.0)

    def test_counts(self):
        summary = self.builder.build()
        self.assertEqual(summary["new_targets"], 3) # h1, h2, h3
        self.assertEqual(summary["negatives"], 2)   # n1, n2

    def test_contribution_chart(self):
        # Total Spend = 100+50+200+80+120+30 = 580
        # Negatives (n1, n2) = 150
        # Bid Up (t1) = 100
        # Bid Down (t2, t4) = 50 + 80 = 130
        # Unchanged (t3) = 200 (Implicitly remainder)
        
        # Ratios: 
        # Neg: 150/580 = 0.2586
        # Up: 100/580 = 0.1724
        # Down: 130/580 = 0.2241
        
        chart = self.builder.build()["contribution_chart"]
        self.assertAlmostEqual(chart["Negatives"], 150/580, places=4)
        self.assertAlmostEqual(chart["Bid Up"], 100/580, places=4)
        self.assertAlmostEqual(chart["Bid Down"], 130/580, places=4)

if __name__ == '__main__':
    unittest.main()
