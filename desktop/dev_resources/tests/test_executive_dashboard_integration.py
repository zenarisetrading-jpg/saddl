
import sys
import os
import unittest
from unittest.mock import MagicMock, patch, ANY
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add parent directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock streamlit before importing the module
sys.modules['streamlit'] = MagicMock()
import streamlit as st

# Import the module to test
from features.executive_dashboard import ExecutiveDashboard

class TestExecutiveDashboardIntegration(unittest.TestCase):
    def setUp(self):
        # Mock session state
        st.session_state = {
            'active_account_id': 'test_account',
            'db_manager': MagicMock()
        }
        
        # Setup mock db manager
        self.db_manager = st.session_state['db_manager']
        
        # Create instance
        self.dashboard = ExecutiveDashboard()

    def create_mock_target_stats(self):
        # Generate 60 days of data
        dates = pd.date_range(end=datetime.now(), periods=60, freq='D')
        data = []
        for date in dates:
            data.append({
                'Date': date,
                'Campaign Name': 'Campaign A',
                'Ad Group Name': 'Group 1',
                'Targeting': 'keyword',
                'Customer Search Term': 'search term',
                'Match Type': 'exact',
                'Spend': 100.0,
                'Sales': 300.0,
                'Orders': 10,
                'Clicks': 50,
                'Impressions': 1000
            })
            # Add some variability
            data.append({
                'Date': date,
                'Campaign Name': 'Campaign B',
                'Ad Group Name': 'Group 1',
                'Targeting': 'auto',
                'Customer Search Term': 'search term 2',
                'Match Type': 'auto',
                'Spend': 50.0,
                'Sales': 100.0,
                'Orders': 2,
                'Clicks': 30,
                'Impressions': 500
            })
        return pd.DataFrame(data)

    def create_mock_impact_data(self):
        return pd.DataFrame([
            {
                'action_type': 'BID_CHANGE',
                'before_sales': 100,
                'observed_after_sales': 150,
                'new_bid': 1.5,
                'old_bid': 1.0,
                'new_value': '1.5',
                'old_value': '1.0',
                'impact_score': 50
            },
            {
                'action_type': 'NEGATIVE',
                'before_sales': 50,
                'observed_after_sales': 10,
                'impact_score': 40
            }
        ])

    def test_fetch_data(self):
        print("\nTesting _fetch_data...")
        self.db_manager.get_target_stats_df.return_value = self.create_mock_target_stats()
        self.db_manager.get_action_impact.return_value = self.create_mock_impact_data()
        
        data = self.dashboard._fetch_data()
        
        self.assertIsNotNone(data)
        self.assertIn('df_current', data)
        self.assertIn('df_previous', data)
        self.assertIn('impact_df', data)
        self.assertIn('medians', data)
        
        # Verify derived columns exist
        self.assertIn('ROAS', data['df_current'].columns)
        self.assertIn('CVR', data['df_current'].columns)
        
        print("✓ Data fetch successful")
        print(f"  Current Period Rows: {len(data['df_current'])}")
        print(f"  Previous Period Rows: {len(data['df_previous'])}")

    @patch('streamlit.selectbox')
    @patch('streamlit.columns')
    @patch('streamlit.plotly_chart')
    @patch('streamlit.markdown')
    def test_rendering_no_errors(self, mock_markdown, mock_plotly, mock_columns, mock_selectbox):
        print("\nTesting rendering methods (smoke test)...")
        # Setup mocks for columns to return list of mocks based on input
        mock_col = MagicMock()
        
        def side_effect(spec):
            if isinstance(spec, int):
                return [mock_col] * spec
            elif isinstance(spec, list):
                return [mock_col] * len(spec)
            return [mock_col, mock_col]
            
        mock_columns.side_effect = side_effect
        mock_selectbox.return_value = "Last 30 Days"
        
        self.db_manager.get_target_stats_df.return_value = self.create_mock_target_stats()
        self.db_manager.get_action_impact.return_value = self.create_mock_impact_data()
        
        # Mock get_impact_summary to return realistic data
        self.db_manager.get_impact_summary.return_value = {
            'validated': {
                'decision_impact': 12500.0,
                'total_actions': 50
            },
            'all': {
                'decision_impact': 15000.0,
                'total_actions': 75
            }
        }
        
        # Run full pipeline
        self.dashboard.run()
        
        print("✓ run() executed without exceptions")
        
if __name__ == '__main__':
    unittest.main()
