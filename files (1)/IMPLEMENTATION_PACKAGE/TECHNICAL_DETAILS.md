# Technical Details - How the Fix Works

## Overview

The impact analyzer calculates the performance change caused by optimization actions by comparing "before" and "after" periods around each action. The fix addresses 5 fundamental issues in how these comparisons are made.

---

## Problem 1: Wrong Comparison Period Calculation

### Original Logic (WRONG):
```python
# Get weeks where actions occurred
action_weeks = actions_df['action_date'].dt.to_period('W-MON').unique()
num_action_weeks = len(action_weeks)

# After period = num_action_weeks after last action
after_start = (action_weeks[-1].end_time + 1 day)
after_end = after_start + num_action_weeks * 7 days

# Before period = match after duration
before_duration = (after_end - after_start).days
before_end = after_start - 1 day
before_start = before_end - before_duration
```

**Issue:** Uses number of action weeks as comparison duration, not upload duration.

**Example Failure:**
```
Actions: Week of Nov 1-7 (1 week)
Upload: Dec 1-15 (15 days of new data)

Wrong calculation:
  Before: Oct 26 - Nov 7 (7 days)
  After: Nov 8-14 (7 days)
  
Result: Only compares 7 days when you have 15 days of new data!
```

### Fixed Logic (CORRECT):
```python
# Calculate upload duration from most recent data
max_stats_date = stats_df['start_date'].max()
recent_dates = stats_df['start_date'].unique()
upload_days = len([d for d in recent_dates if (max_stats_date - d).days <= 30])

# For each action individually:
action_date = action['action_date']

# Before: upload_days before action
before_end = action_date
before_start = action_date - timedelta(days=upload_days - 1)

# After: upload_days after action  
after_start = action_date + timedelta(days=1)
after_end = action_date + timedelta(days=upload_days)
```

**Why This Works:**
- Uses actual data availability (upload duration) as baseline
- Works with any upload frequency (weekly, bi-weekly, monthly)
- Comparison windows always match upload granularity

---

## Problem 2: Non-Creditable Actions Getting Credit

### Original Logic (WRONG):
```python
# No filtering
SELECT * FROM actions_log WHERE client_id = ?
```

### Fixed Logic (CORRECT):
```python
# Filter at query level
SELECT * FROM actions_log 
WHERE client_id = ? 
  AND action_type NOT IN ('hold', 'monitor', 'flagged')
```

**Action Type Decision Matrix:**

| Action Type | Gets Credit? | Why? |
|-------------|--------------|------|
| bid_increase | ✅ Yes | Direct causation - bid up → more volume |
| bid_decrease | ✅ Yes | Direct causation - bid down → less spend |
| negative_add | ✅ Conditional | Only if before_spend > 0 |
| harvest | ✅ Yes | Consolidation gain (winner → exact) |
| pause | ✅ Yes | Structural change - stops spend |
| activate | ✅ Yes | Structural change - starts spend |
| hold | ❌ No | No action = no credit |
| monitor | ❌ No | Observation only |
| flagged | ❌ No | Just a flag |

---

## Problem 3: Preventative Negatives Getting Credit

### Original Logic (WRONG):
```python
# All negatives treated the same
if action_type == 'negative_add':
    impact = after_spend - before_spend  # Could show "savings" with $0 before
```

### Fixed Logic (CORRECT):
```python
if action_type == 'negative_add':
    if before_spend == 0:
        # Preventative negative - no spend to save
        return {
            'attribution': 'preventative',
            'impact': 0,
            'reason': 'No spend to save'
        }
    else:
        # Actual bleeder - credit cost avoidance
        return {
            'attribution': 'cost_avoidance',
            'impact_sales': 0,  # Don't credit revenue
            'impact_spend': -before_spend  # Cost saved
        }
```

**Why This Matters:**
```
Scenario A: Preventative Negative
  Before: $0 spend (never triggered)
  After: $0 spend (blocked)
  Wrong: "Saved $0" but shows in report
  Correct: Excluded, no false credit

Scenario B: Actual Bleeder
  Before: $75 spend, $0 sales
  After: $0 spend (blocked)
  Wrong: Shows revenue impact (incorrect)
  Correct: "$75 cost avoided" (accurate)
```

---

## Problem 4: Isolation Negatives Getting Separate Credit

### What Are Isolation Negatives?

When you harvest a keyword from Campaign A to Exact Campaign:
1. Add keyword to Exact Campaign (harvest action)
2. Add as negative in Campaign B, C, D (isolation negatives)

The isolation negatives are part of the harvest consolidation strategy - they shouldn't get separate credit because the harvest already measures the full impact.

### Original Logic (WRONG):
```python
# Treats all negatives the same
if action_type == 'negative_add':
    impact = -before_spend  # Credits each isolation negative separately
```

### Fixed Logic (CORRECT):
```python
if action_type == 'negative_add':
    reason = action.get('reason', '').lower()
    
    if 'isolation' in reason or 'harvest' in reason:
        return {
            'attribution': 'isolation_negative',
            'impact': 0,
            'reason': 'Part of harvest - no separate credit'
        }
```

**Example:**
```
Harvest "wireless headphones" from 3 campaigns → 1 exact campaign

Wrong:
  - Harvest: +$100 impact
  - Isolation Campaign B: +$30 "savings"
  - Isolation Campaign C: +$20 "savings"
  Total: +$150 (inflated!)

Correct:
  - Harvest: +$100 impact (compares winner → exact)
  - Isolation negatives: $0 (marked as part of harvest)
  Total: +$100 (accurate)
```

---

## Problem 5: Harvest Comparing All Campaigns

### Original Logic (WRONG):
```python
# Simple target_text match
target_before = stats_df[stats_df['target_text'] == keyword]

# This matches ALL campaigns with this keyword!
```

### Fixed Logic (CORRECT):
```python
if action_type == 'harvest':
    winner_source = action.get('winner_source_campaign')
    new_campaign = action.get('new_campaign_name')
    
    # Before: Winner source only
    target_before = stats_df[
        (stats_df['target_text'] == keyword) &
        (stats_df['campaign_name'] == winner_source)
    ]
    
    # After: New exact campaign only
    target_after = stats_df[
        (stats_df['target_text'] == keyword) &
        (stats_df['campaign_name'] == new_campaign)
    ]
```

**Why This Matters:**
```
Keyword appears in 3 campaigns:
  Campaign A: $100 spend, $500 sales (5.0x ROAS) ← Winner
  Campaign B: $100 spend, $200 sales (2.0x ROAS)
  Campaign C: $100 spend, $300 sales (3.0x ROAS)

Wrong (sum all):
  Before: $300 spend, $1000 sales
  After: $120 spend, $600 sales (exact)
  Impact: +$300 sales, -$180 spend
  
Correct (winner only):
  Before: $100 spend, $500 sales (Campaign A)
  After: $120 spend, $600 sales (exact)
  Impact: +$100 sales, +$20 spend
```

The correct approach measures the **incremental improvement from the best source**, not the aggregate effect of consolidating all sources (which would inflate impact).

---

## Time Selector vs Comparison Period

Two different concepts that work together:

### Comparison Period (Internal Calculation)
- **Purpose:** Calculate before/after windows for each action
- **Based on:** Upload duration (data availability)
- **Affects:** Accuracy of impact measurement
- **Example:** 15-day upload → 15-day before/after windows

### Time Selector (UI Filter)
- **Purpose:** Filter which actions to display
- **Based on:** How long ago action was taken
- **Affects:** Which actions user sees
- **Example:** "30D" shows actions from last 30 days only

**How They Work Together:**
```python
# Step 1: Calculate impact for ALL actions (with correct windows)
all_impacts = get_action_impact(client_id)  # Uses upload duration internally

# Step 2: Filter by time selector for display
days_ago = {'7D': 7, '30D': 30}[time_frame]
cutoff = now() - timedelta(days=days_ago)
filtered = all_impacts[all_impacts['action_date'] >= cutoff]
```

---

## Database Schema Changes

New columns in `actions_log`:

| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| winner_source_campaign | TEXT | For harvest: which campaign was winner | "Auto_Campaign_A" |
| new_campaign_name | TEXT | For harvest: where it's moving to | "Harvest_Exact_SKU123" |
| before_match_type | TEXT | Match type before action | "broad" |
| after_match_type | TEXT | Match type after action | "exact" |

These enable proper harvest attribution by tracking the source and destination.

---

## Performance Considerations

### Caching
The impact dashboard uses `@st.cache_data` to avoid re-querying on every tab switch:

```python
@st.cache_data(ttl=300)  # Cache for 5 minutes
def _fetch_impact_data(client_id, test_mode, window_days, cache_version):
    ...
```

Cache is invalidated by:
- `cache_version` changes (tied to data upload timestamp)
- TTL expiration (5 minutes)
- Manual clear: `st.cache_data.clear()`

### Query Optimization
The fixed version:
- Filters at SQL level (not in Python)
- Single pass through actions (no multiple queries)
- Pre-calculates upload duration once

---

## Edge Cases Handled

1. **Insufficient after data:** If action was recent and not enough after data exists, returns `attribution='insufficient_data'`

2. **Missing winner source:** If harvest action doesn't have `winner_source_campaign`, falls back to matching all campaigns (old behavior)

3. **Duplicate actions:** Groups by target_text + action_type + date to dedupe

4. **Date gaps in data:** Infers upload duration from available dates, caps at 7-30 days for sanity

5. **Zero spend keywords:** Returns None for is_winner (not counted as winner or loser)

---

## Testing Strategy

See `test_cases.py` for runnable tests covering:
1. Comparison windows match upload duration
2. Holds excluded
3. Preventative negatives get no credit
4. Isolation negatives get no credit  
5. Harvest uses winner source only
6. Regular negatives with spend get cost avoidance credit

Run after implementation to verify everything works.
