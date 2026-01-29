import unittest
import pandas as pd
from datetime import datetime
import sys
import os

# Add project root to path to allow importing 'features'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(project_root)

from features.optimizer_results_adapter import adapt_run_outputs, validate_run_outputs

class TestOptimizerAdapter(unittest.TestCase):
    
    def setUp(self):
        # Fixture: Standard Run
        self.mock_run_results = {
            "df": pd.DataFrame({
                "Campaign Name": ["Camp A", "Camp B"],
                "Ad Group Name": ["AG A", "AG B"],
                "Targeting": ["term1", "term2"],
                "Spend": [100.0, 50.0],
                "Sales": [300.0, 100.0],
                "Orders": [10, 5]
            }),
            "bids_exact": pd.DataFrame({
                "Campaign Name": ["Camp A"],
                "Ad Group Name": ["AG A"],
                "Targeting": ["term1"],
                "Current Bid": [1.0],
                "New Bid": [1.2]
            }),
            "neg_kw": pd.DataFrame({
                "Campaign Name": ["Camp B"],
                "Ad Group Name": ["AG B"],
                "Term": ["bad_term"]
            }),
            "harvest": pd.DataFrame({
                "Customer Search Term": ["new_term"]
            }),
            "simulation": {
                "scenarios": {
                    "current": {"spend": 1000, "sales": 3000},
                    "expected": {"spend": 900, "sales": 3200}
                }
            }
        }

    def test_s1_schema_compliance(self):
        """S1: All required fields present and correct types."""
        output = adapt_run_outputs(self.mock_run_results)
        try:
            validate_run_outputs(output)
        except AssertionError as e:
            self.fail(f"Schema validation failed: {e}")
            
    def test_a1_mapping_accuracy(self):
        """A1: Verify exact field mapping."""
        output = adapt_run_outputs(self.mock_run_results)
        
        # Bids
        bid_key = "Camp A|AG A|term1"
        self.assertIn(bid_key, output["bids_old"])
        self.assertEqual(output["bids_old"][bid_key], 1.0)
        self.assertEqual(output["bids_new"][bid_key], 1.2)
        
        # Negatives
        neg_key = "Camp B|AG B|bad_term"
        self.assertIn(neg_key, output["negatives"])
        
        # Harvest
        self.assertIn("new_term", output["harvested"])
        
        # Simulation
        # Old ACOS: 1000/3000 = 33.33%
        # New ACOS: 900/3200 = 28.125%
        self.assertAlmostEqual(output["simulation"]["old_acos"], 33.333, places=2)
        self.assertAlmostEqual(output["simulation"]["new_acos"], 28.125, places=2)

    def test_null_handling(self):
        """Test resilience to empty inputs."""
        output = adapt_run_outputs({})
        validate_run_outputs(output)
        self.assertEqual(output["bids_old"], {})
        self.assertIsNone(output["simulation"])

    def test_broken_simulation_ignored(self):
        """Ensure broken simulation data doesn't crash adapter."""
        broken_sim = self.mock_run_results.copy()
        broken_sim["simulation"] = {"scenarios": {}} # Missing expected keys
        
        output = adapt_run_outputs(broken_sim)
        self.assertIsNone(output["simulation"])

if __name__ == '__main__':
    unittest.main()
