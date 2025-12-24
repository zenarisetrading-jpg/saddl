"""
Test new validation rules: Isolation vs Bleeder negatives
"""

import sys
import os
sys.path.append(os.getcwd())

from core.bulk_validation import (
    validate_isolation_negative,
    validate_bleeder_negative,
    detect_negative_type,
    NegativeType,
)

def test_isolation_vs_bleeder():
    print("=== Testing Isolation vs Bleeder Detection ===\n")
    
    # Test match type detection
    test_cases = [
        ("campaign negative exact", NegativeType.ISOLATION),
        ("campaign negative phrase", NegativeType.ISOLATION),
        ("negative exact", NegativeType.BLEEDER),
        ("negative phrase", NegativeType.BLEEDER),
        ("negativeExact", NegativeType.BLEEDER),
        ("exact", None),  # Positive keyword
        ("broad", None),
    ]
    
    for match_type, expected in test_cases:
        result = detect_negative_type(match_type)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{match_type}' -> {result} (expected: {expected})")
        assert result == expected, f"Failed for {match_type}"
    
    print("\n--- Testing Isolation Negative Validation ---")
    
    # Valid isolation negative
    valid_isolation = {
        "Campaign Name": "Test Campaign",
        "Ad Group Name": "",  # MUST BE BLANK
        "Match Type": "campaign negative exact",
        "State": "enabled",
        "Bid": "",
    }
    issues = validate_isolation_negative(valid_isolation, 1)
    print(f"  Valid Isolation: {len(issues)} issues (expected: 0)")
    assert len(issues) == 0, f"Expected 0 issues, got {issues}"
    
    # Invalid isolation: has Ad Group
    invalid_isolation = {
        "Campaign Name": "Test Campaign",
        "Ad Group Name": "Some Ad Group",  # SHOULD BE BLANK
        "Match Type": "campaign negative exact",
        "State": "enabled",
        "Bid": "",
    }
    issues = validate_isolation_negative(invalid_isolation, 1)
    print(f"  Invalid Isolation (has Ad Group): {len(issues)} issues (expected: 1)")
    assert len(issues) == 1 and issues[0].code == "ISO001", f"Expected ISO001, got {issues}"
    
    print("\n--- Testing Bleeder Negative Validation ---")
    
    # Valid bleeder negative
    valid_bleeder = {
        "Campaign Name": "Test Campaign",
        "Ad Group Name": "Test Ad Group",  # REQUIRED
        "Match Type": "negative exact",
    }
    issues = validate_bleeder_negative(valid_bleeder, 1)
    print(f"  Valid Bleeder: {len(issues)} issues (expected: 0)")
    assert len(issues) == 0, f"Expected 0 issues, got {issues}"
    
    # Invalid bleeder: missing Ad Group
    invalid_bleeder = {
        "Campaign Name": "Test Campaign",
        "Ad Group Name": "",  # SHOULD BE POPULATED
        "Match Type": "negative exact",
    }
    issues = validate_bleeder_negative(invalid_bleeder, 1)
    print(f"  Invalid Bleeder (missing Ad Group): {len(issues)} issues (expected: 1)")
    assert len(issues) == 1 and issues[0].code == "BLD001", f"Expected BLD001, got {issues}"
    
    print("\n✅ ALL ISOLATION/BLEEDER TESTS PASSED")

if __name__ == "__main__":
    test_isolation_vs_bleeder()
