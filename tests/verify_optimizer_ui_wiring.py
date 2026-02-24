import sys
import os
import unittest
from unittest.mock import MagicMock

# Mock streamlit before imports
sys.modules["streamlit"] = MagicMock()

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../desktop")))

class TestOptimizerWiring(unittest.TestCase):
    def test_imports_and_instantiation(self):
        """Verify all new UI modules can be imported and the OptimizerModule initializes."""
        try:
            print("\nAttempting to import OptimizerModule...")
            from features.optimizer_shared import OptimizerModule
            
            print("Attempting to import UI Submodules directly...")
            from features.optimizer_shared.ui.landing import render_landing_page
            from features.optimizer_shared.ui.results import render_results_dashboard
            from features.optimizer_shared.ui.components import inject_optimizer_css
            from features.optimizer_shared.ui.charts import render_spend_reallocation_chart
            
            print("Initializing OptimizerModule...")
            opt = OptimizerModule()
            
            # Verify critical methods exist
            self.assertTrue(hasattr(opt, "render_ui"), "render_ui method missing")
            self.assertTrue(hasattr(opt, "_run_analysis"), "_run_analysis method missing")
            
            # Verify UI module attributes
            print("Verifying UI module functions...")
            self.assertTrue(callable(render_landing_page), "render_landing_page is not callable")
            self.assertTrue(callable(render_results_dashboard), "render_results_dashboard is not callable")
            
            print("✅ WIRING SUCCESS: All modules imported and linked correctly.")
            
        except ImportError as e:
            self.fail(f"Wiring Failed: Import Error - {str(e)}")
        except Exception as e:
            self.fail(f"Wiring Failed: Runtime Error - {str(e)}")

if __name__ == "__main__":
    unittest.main()
