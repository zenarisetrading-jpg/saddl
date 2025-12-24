# FOR IDE AGENT: Implementation Summary

## Quick Start

You are implementing a fix for an impact analyzer in a PPC optimization tool. This package contains everything needed.

## Files in This Package

1. **INSTRUCTIONS.md** ← Start here
2. **db_manager_get_action_impact_FIXED.py** ← Replace function in core/db_manager.py (lines 1131-1376)
3. **schema_migration.sql** ← Run against database
4. **optimizer_logging_ADDITIONS.py** ← Add to features/optimizer.py
5. **test_cases.py** ← Run after implementation
6. **TROUBLESHOOTING.md** ← If issues occur
7. **TECHNICAL_DETAILS.md** ← How it works

## What You're Fixing

**Current Problem:**
- Impact analyzer uses wrong comparison periods (action weeks instead of upload duration)
- Gives credit to actions that shouldn't get credit (holds, preventative negatives)
- Harvest comparisons include all campaigns instead of winner only

**Expected Behavior After Fix:**
- Comparison windows match upload duration (15-day upload = 15-day windows)
- Only creditable actions get impact attribution
- Harvest compares winner source campaign → new exact campaign

## Implementation Steps

### 1. Database (5 min)
```bash
sqlite3 your_database.db < schema_migration.sql
```

### 2. Core Fix (15 min)
In `core/db_manager.py`:
- Locate function `get_action_impact()` at line 1131
- Replace entire function (lines 1131-1376) with content from `db_manager_get_action_impact_FIXED.py`

### 3. Action Logging (30 min)
In `features/optimizer.py`:
- Find where harvest actions are logged
- Add winner source tracking using examples in `optimizer_logging_ADDITIONS.py`
- Update `log_action()` signature to accept new parameters

### 4. Test (15 min)
```bash
python test_cases.py
```

## Key Changes

### Before:
```python
# WRONG: Uses action weeks
action_weeks = len(actions) 
before_period = X weeks before actions
after_period = X weeks after actions
```

### After:
```python
# CORRECT: Uses upload duration
upload_days = 15  # From new upload
before_period = 15 days before each action
after_period = 15 days after each action
```

## What NOT to Change

- `impact_dashboard.py` - No changes needed (displays data correctly once db_manager is fixed)
- Time selector (7D/30D/etc) - Keep as is (filters which actions to show, not how to measure)

## Success Criteria

After implementation:
- [ ] Test suite passes (all 6 tests green)
- [ ] Impact dashboard loads without errors
- [ ] Holds/monitors don't appear in impact table
- [ ] Preventative negatives show attribution='preventative', impact=0
- [ ] Comparison periods match upload duration
- [ ] Harvest actions compare winner source only

## If Something Breaks

1. Check TROUBLESHOOTING.md for your specific error
2. Verify schema migration completed
3. Check that comparison_days matches upload duration
4. Ensure action filtering is working (WHERE ... NOT IN ('hold', 'monitor'))

## Questions the IDE Agent Should Ask

Before implementing, verify:
1. What's the database type? (SQLite or PostgreSQL)
2. Where exactly are harvest actions logged in optimizer.py?
3. Does the `log_action()` method already exist or needs to be created?
4. Are there any custom modifications to db_manager.py that need to be preserved?

## Estimated Time

- Database migration: 5 minutes
- Core fix: 15 minutes  
- Logging updates: 30 minutes
- Testing: 15 minutes
- **Total: ~1 hour**

## Rollback

If issues occur:
- Database changes are additive (safe to keep)
- Just revert db_manager.py to previous version
- Existing data/functionality won't be affected

---

**Implementation Order:**
1. Read INSTRUCTIONS.md
2. Run schema_migration.sql
3. Replace get_action_impact() function
4. Update optimizer logging
5. Run test_cases.py
6. If issues, check TROUBLESHOOTING.md
