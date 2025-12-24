# Impact Analyzer Fix - Implementation Instructions

## Overview
This package fixes 5 critical issues in the impact analyzer:
1. Wrong comparison period calculation (uses action weeks instead of upload duration)
2. Holds/monitors getting credit when they shouldn't
3. Preventative negatives getting credit when no spend to save
4. Isolation negatives (from harvest) getting separate credit
5. Missing harvest winner source tracking

## Files to Modify

### 1. `core/db_manager.py`
- **Function:** `get_action_impact()` (lines 1131-1376)
- **Action:** Replace entire function with version in `db_manager_get_action_impact_FIXED.py`

### 2. `features/optimizer.py`
- **Function:** `_log_optimization_events()` or wherever actions are logged
- **Action:** Add winner source tracking for harvest actions (see `optimizer_logging_ADDITIONS.py`)

### 3. Database Schema
- **Action:** Run SQL migration in `schema_migration.sql`

### 4. `features/impact_dashboard.py`
- **Action:** No changes needed - it displays data correctly once db_manager is fixed

## Implementation Order

### Phase 1: Database Schema (5 minutes)
1. Run `schema_migration.sql` against your database
2. Verify columns added: `winner_source_campaign`, `new_campaign_name`, `before_match_type`, `after_match_type`

### Phase 2: Core Fix (15 minutes)
1. Backup current `db_manager.py`
2. Replace `get_action_impact()` function (lines 1131-1376) with fixed version
3. Test with sample data

### Phase 3: Action Logging (30 minutes)
1. Update optimizer.py to log winner source for harvest actions
2. Use code snippets in `optimizer_logging_ADDITIONS.py`
3. Re-run optimizer on test data to verify actions logged correctly

### Phase 4: Testing (15 minutes)
1. Run test cases in `test_cases.py`
2. Verify impact calculations match expected values
3. Check UI displays correctly

## Expected Results

### Before Fix:
- Actions from 1-week period only compared 7 days
- Holds showed impact when they shouldn't
- Preventative negatives showed "savings" with $0 before spend
- Harvest compared ALL campaigns not just winner

### After Fix:
- ✅ Comparison windows match upload duration (15-day upload = 15-day windows)
- ✅ Holds/monitors excluded from impact
- ✅ Preventative negatives excluded
- ✅ Isolation negatives show "no credit" (harvest gets credit)
- ✅ Harvest compares winner source only

## Rollback Plan
If issues occur:
1. Revert `db_manager.py` to backup
2. Keep database schema changes (harmless)
3. Report error with details

## Questions?
See detailed documentation in:
- `TECHNICAL_DETAILS.md` - How the fix works
- `EXAMPLE_SCENARIOS.md` - Before/after examples
- `TROUBLESHOOTING.md` - Common issues
