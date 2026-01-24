# UI Components package for SADDL AdPulse
# Contains reusable glassmorphic components

# Re-export commonly used functions from the sibling components.py module
# This allows: from ui.components import metric_card
import sys
from pathlib import Path

# Import from the sibling components.py file (ui/components.py)
# We need to handle the case where both ui/components.py and ui/components/ exist
_parent_dir = Path(__file__).parent.parent
_components_file = _parent_dir / "components.py"

if _components_file.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location("ui_components_module", _components_file)
    _module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_module)
    
    # Export the key functions
    metric_card = _module.metric_card
    metric_card_with_tooltip = _module.metric_card_with_tooltip
