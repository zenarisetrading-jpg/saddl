# Troubleshooting Guide

## Common Issues After Implementation

### Issue 1: "Column not found: winner_source_campaign"

**Symptom:**
```
Error: no such column: winner_source_campaign
```

**Cause:** Database schema migration not run

**Fix:**
```bash
# Run the migration script
sqlite3 your_database.db < schema_migration.sql

# Or manually:
ALTER TABLE actions_log ADD COLUMN winner_source_campaign TEXT;
ALTER TABLE actions_log ADD COLUMN new_campaign_name TEXT;
ALTER TABLE actions_log ADD COLUMN before_match_type TEXT;
ALTER TABLE actions_log ADD COLUMN after_match_type TEXT;
```

---

### Issue 2: All actions show "insufficient_data"

**Symptom:**
Impact dashboard shows no measured impact, all actions have `attribution = 'insufficient_data'`

**Cause:** Not enough "after" data uploaded yet

**Debug:**
```python
# Check what data is available
impact_df = db.get_action_impact(client_id)
print(impact_df[['action_date', 'after_period', 'attribution', 'reason_detail']])

# Look for:
# - "Only X/Y days of after data available"
```

**Fix:**
- Upload more recent data covering the "after" period
- Action on Nov 20 with 15-day upload needs data through Dec 5

---

### Issue 3: Holds still showing in impact

**Symptom:**
Actions with `action_type = 'hold'` appear in impact dashboard

**Cause:** Filter not applied in SQL query

**Debug:**
```python
# Check the actions_query in get_action_impact()
# Should have: WHERE a.action_type NOT IN ('hold', 'monitor', 'flagged')
```

**Fix:**
Verify lines 1173-1175 in db_manager.py have the correct WHERE clause

---

### Issue 4: Negative showing revenue impact

**Symptom:**
Negative keywords show positive/negative `delta_sales` when they should only show spend savings

**Cause:** Attribution logic not checking action type

**Debug:**
```python
impact_df = db.get_action_impact(client_id)
negatives = impact_df[impact_df['action_type'] == 'negative_add']
print(negatives[['target_text', 'attributed_delta_sales', 'attributed_delta_spend']])

# Should show:
# attributed_delta_sales = 0 (always)
# attributed_delta_spend = -X (negative = savings)
```

**Fix:**
Check lines 1240-1250 in the fixed function - ensure negatives use:
```python
attributed_delta_sales = 0
attributed_delta_spend = -before_spend
```

---

### Issue 5: Harvest comparing all campaigns

**Symptom:**
Harvest "before" metrics too high - looks like it's summing multiple campaigns

**Debug:**
```python
# Check harvest actions
harvest = impact_df[impact_df['action_type'] == 'harvest']
print(harvest[['target_text', 'before_spend', 'winner_source_campaign', 'campaign_name']])

# If winner_source_campaign is NULL, fallback logic is being used
```

**Fix:**
1. Verify optimizer.py is logging `winner_source_campaign` when creating harvest actions
2. Check that the value is being passed to `log_action()`
3. For old data, manually update:
```sql
UPDATE actions_log 
SET winner_source_campaign = campaign_name
WHERE action_type = 'harvest' 
  AND winner_source_campaign IS NULL;
```

---

### Issue 6: Comparison periods seem wrong

**Symptom:**
Before/after periods don't match upload duration

**Debug:**
```python
impact_df = db.get_action_impact(client_id)
print(impact_df[['action_date', 'before_period', 'after_period', 'comparison_days']])

# Check:
# - Are comparison_days matching upload duration?
# - Do periods look correct relative to action_date?
```

**Example:**
```
Action: Nov 20
Upload: Dec 1-15 (15 days)

Expected:
  before_period: 2024-11-06 to 2024-11-20 (15 days)
  after_period: 2024-11-21 to 2024-12-05 (15 days)
  comparison_days: 15

Wrong (old logic):
  before_period: 2024-11-20 to 2024-11-26 (7 days)
  after_period: 2024-11-27 to 2024-12-03 (7 days)
  comparison_days: 7
```

**Fix:**
Verify lines 1204-1234 in fixed function calculate `upload_days` correctly

---

### Issue 7: Impact numbers seem inflated

**Symptom:**
Total attributed impact much higher than account-level delta

**Cause:** Double-counting from duplicate actions or proration logic removed

**Debug:**
```python
# Check for duplicate actions
actions = impact_df.groupby(['target_text', 'action_date']).size()
duplicates = actions[actions > 1]
if not duplicates.empty:
    print("Duplicate actions found:", duplicates)

# Compare attributed sum vs account delta
attributed_total_sales = impact_df['attributed_delta_sales'].sum()
print(f"Attributed total: ${attributed_total_sales:.2f}")

# This should roughly match account-level change
# (Note: Current simplified version doesn't have full proration)
```

**Fix:**
If you need account-level proration (to ensure sum of attributed deltas = account delta), you can add back the proration logic from the original version (lines 1250-1320 in original code)

---

### Issue 8: Time selector not working

**Symptom:**
Changing 7D/14D/30D filter doesn't affect displayed actions

**Cause:** Filter applied incorrectly or data cached

**Debug:**
```python
# In impact_dashboard.py, check if cutoff_date is being calculated
print(f"Time frame: {time_frame}")
print(f"Cutoff date: {cutoff_date}")
print(f"Actions before filter: {len(impact_df)}")
print(f"Actions after filter: {len(filtered_df)}")
```

**Fix:**
1. Clear Streamlit cache: `st.cache_data.clear()`
2. Verify filtering logic in impact_dashboard.py around line 140-148
3. Ensure `action_date` column is datetime type

---

## Verification Checklist

After implementation, verify:

- [ ] Schema migration completed (columns exist)
- [ ] Holds/monitors excluded from impact
- [ ] Preventative negatives show attribution='preventative', impact=0
- [ ] Isolation negatives show attribution='isolation_negative', impact=0
- [ ] Regular negatives with spend show cost avoidance
- [ ] Harvest actions have winner_source_campaign populated
- [ ] Comparison windows match upload duration
- [ ] Before/after periods are symmetric around action date
- [ ] Time selector (7D/30D/etc) filters actions correctly
- [ ] UI displays impact metrics without errors

---

## Getting Help

If you encounter issues not covered here:

1. Check the action type and attribution in impact_df
2. Verify before/after periods make sense
3. Check that target_stats exist for the periods
4. Look for NULL values in key columns
5. Check database query logs for errors

Common SQL to debug:

```sql
-- Check action distribution
SELECT action_type, attribution, COUNT(*) 
FROM actions_log 
GROUP BY action_type, attribution;

-- Check date coverage
SELECT MIN(start_date), MAX(start_date), COUNT(*)
FROM target_stats
WHERE client_id = 'your_client_id';

-- Check harvest metadata
SELECT action_type, winner_source_campaign, new_campaign_name
FROM actions_log
WHERE action_type = 'harvest'
LIMIT 10;
```
