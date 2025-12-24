# Impact Analyzer - Visual Examples

## Example 1: Dynamic Comparison Windows

### Scenario: Bi-Weekly Upload

```
Timeline:
────────────────────────────────────────────────────────
Nov 1    Nov 15   Nov 20   Dec 1    Dec 15   Dec 31
  │        │        │        │        │        │
  │        │        │        │        │        │
  │◄──15d──┤        │        │◄──15d──┤        │
  │  Before Period  │        │  After Period   │
  │                 │        │   (New Upload)  │
  │                 │        │                 │
  └─────────────────┴────────┴─────────────────┘
                  Action
                  Taken
```

**Logic:**
- New upload: Dec 1-15 (15 days)
- Action taken: Nov 20
- Before window: Nov 6-20 (15 days before action)
- After window: Dec 1-15 (15 days, from new upload)

**Why it works:**
- Same duration (15 days) for fair comparison
- Before captures baseline performance
- After captures post-action performance
- Normalizes for different upload frequencies

---

## Example 2: Harvest Attribution (Winner Comparison)

### Scenario: Harvest "wireless earbuds" from Multiple Campaigns

```
BEFORE (Auto/Broad Campaigns):
────────────────────────────────────────────────────

Campaign A (Auto):
  wireless earbuds: 30 clicks, $45 spend, $180 sales, 4.0x ROAS
  
Campaign B (Broad):  
  wireless earbuds: 50 clicks, $75 spend, $225 sales, 3.0x ROAS ← WINNER
  
Campaign C (Auto):
  wireless earbuds: 20 clicks, $30 spend, $90 sales, 3.0x ROAS

Winner Selection:
  Performance Score = Sales + (ROAS × 5)
  A: 180 + (4.0 × 5) = 200
  B: 225 + (3.0 × 5) = 240 ← HIGHEST
  C: 90 + (3.0 × 5) = 105

────────────────────────────────────────────────────

AFTER (Exact Campaign):
────────────────────────────────────────────────────

Harvest_Exact_Campaign:
  wireless earbuds (exact): 65 clicks, $130 spend, $325 sales, 2.5x ROAS

────────────────────────────────────────────────────

IMPACT CALCULATION:
────────────────────────────────────────────────────

Compare: New Exact vs Winner (Campaign B Broad)

Before (Campaign B):  50 clicks, $75 spend, $225 sales
After (Exact):        65 clicks, $130 spend, $325 sales
────────────────────────────────────────────────────
Delta:                +15 clicks, +$55 spend, +$100 sales

Impact:
  Revenue Lift: +$100 (+44%)
  Spend Increase: +$55 (+73%)
  ROAS Change: 3.0x → 2.5x (-0.5x)
  
Attribution: harvest_consolidation
Confidence: medium (both have 50+ clicks)
Reason: Harvest from Campaign B broad to exact

```

**Why Winner Comparison:**
- Most accurate baseline (highest performing source)
- Avoids inflated impact from low-performing sources
- Realistic expectation of harvest performance
- Fair attribution when multiple sources exist

---

## Example 3: Action Attribution Matrix

```
ACTION TYPE          | HAS SPEND | GETS CREDIT | LOGIC
──────────────────────────────────────────────────────────
Hold                 | Any       | ❌ No       | No action taken
Monitor              | Any       | ❌ No       | No action taken
Negative (preventative) | $0     | ❌ No       | Nothing to save
Negative (blocker)   | >$0       | ✅ Yes      | Cost avoidance = before spend
Bid Increase         | Any       | ✅ Yes      | Direct causation
Bid Decrease         | Any       | ✅ Yes      | Direct causation
Harvest              | Any       | ✅ Yes      | Compare winner → exact
Pause                | Any       | ✅ Yes      | Structural change
Activate             | Any       | ✅ Yes      | Structural change
```

---

## Example 4: Weekly vs Monthly Uploads

### Weekly Upload (7 days)

```
Week 1: Nov 1-7    Week 2: Nov 8-14   Week 3: Nov 15-21
  │                  │                  │
  │                  │                  │
  │◄──7d─┤           │◄──7d─┤           │◄──7d─┤
  │ Before│          │ Before│          │ Before│
  │       │          │       │          │       │
  └───────┴──────────┴───────┴──────────┴───────┘
        Action            Action            Action
       Nov 7            Nov 14            Nov 21
```

**Impact calculation:**
- Each action gets 7-day before/after window
- Comparison: Nov 1-7 (before) vs Nov 8-14 (after)
- Next action: Nov 8-14 (before) vs Nov 15-21 (after)

---

### Monthly Upload (30 days)

```
Month 1: Nov 1-30                Month 2: Dec 1-30
  │                                │
  │                                │
  │◄────────30d───────┤           │◄────────30d───────┤
  │      Before       │           │       After        │
  │                   │           │                    │
  └───────────────────┴───────────┴────────────────────┘
                   Action
                  Nov 30
```

**Impact calculation:**
- Action gets 30-day before/after window
- Comparison: Nov 1-30 (before) vs Dec 1-30 (after)
- Aggregated impact over longer period
- More stable but less frequent feedback

---

## Example 5: Multiple Actions Same Period

### Scenario: 3 Actions Taken Nov 10-20, Upload Covers Dec 1-15

```
Timeline:
────────────────────────────────────────────────────
Oct 27  Nov 10  Nov 15  Nov 20  Dec 1  Dec 15
  │       │       │       │       │      │
  │       │       │       │       │      │
  │◄─15d─┤       │       │       │◄─15d─┤
  │ A-Before     │       │       │ After │
  │              │       │       │       │
  │     │◄─15d──┤       │       │       │
  │     │ B-Before      │       │       │
  │     │               │       │       │
  │     │      │◄─15d──┤       │       │
  │     │      │ C-Before      │       │
  └─────┴──────┴───────┴───────┴───────┘
      Action  Action  Action   Upload
       A       B       C       Period
```

**Impact calculation:**
- Action A: Oct 27-Nov 10 (before) vs Nov 26-Dec 10 (after)
- Action B: Nov 1-Nov 15 (before) vs Dec 1-Dec 15 (after) ✓
- Action C: Nov 6-Nov 20 (before) vs Dec 6-Dec 20 (after) ✗ partial

**Notes:**
- Action B has complete before/after data ✓
- Action A: after period only partially in upload
- Action C: after period extends beyond upload
- Partial overlaps get lower confidence scores

---

## Example 6: Hold vs Bid Change

### Scenario A: Hold (No Credit)

```
Keyword: "baby toys"
Current Bid: $2.00
ROAS: 5.0x (above target 3.0x)

Before Period: 100 clicks, $200 spend, $1000 sales
Action: HOLD (no bid change)
After Period: 110 clicks, $220 spend, $1100 sales

Impact Attribution:
  Revenue Delta: +$100 
  Spend Delta: +$20
  Attribution: EXCLUDED ❌
  Reason: No action taken - hold status
  Credit: $0
  
Explanation: Performance improved naturally or due to external
factors (seasonality, competitor changes, etc). We didn't DO
anything, so we don't take credit.
```

---

### Scenario B: Bid Increase (Gets Credit)

```
Keyword: "baby toys"
Current Bid: $2.00 → New Bid: $2.50 (+25%)
ROAS: 3.0x (at target)

Before Period: 100 clicks, $200 spend, $600 sales
Action: BID INCREASE +25%
After Period: 130 clicks, $325 spend, $975 sales

Impact Attribution:
  Revenue Delta: +$375
  Spend Delta: +$125
  Attribution: direct_causation ✅
  Reason: Bid changed from $2.00 to $2.50
  Credit: +$375 revenue, +$125 spend
  Confidence: high (100+ clicks both periods)
  
Explanation: We increased bid, got more impressions/clicks,
generated more sales. Clear causal mechanism.
```

---

## Key Takeaways

### 1. Dynamic Windows Adapt to Upload Frequency
- Weekly uploads → 7-day windows
- Bi-weekly uploads → 15-day windows  
- Monthly uploads → 30-day windows
- **Always** same duration before/after

### 2. Harvest Compares Winner Only
- Find best performing source campaign
- Use that as baseline
- Compare winner source vs new exact
- Realistic, not inflated

### 3. No Credit Without Causation
- Hold = no action = no credit
- Preventative negative = nothing saved = no credit
- Only credit when there's a clear mechanism

### 4. Confidence Depends on Volume
- High: 30+ clicks both periods
- Medium: 10-30 clicks or variance
- Low: <10 clicks or incomplete data

### 5. Partial Overlaps Get Flagged
- If action's after period extends beyond upload
- Flag as "partial_data"
- Lower confidence score
- Still report but with caveat
