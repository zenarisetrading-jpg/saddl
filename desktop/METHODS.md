# Saddl - Methodologies & Calculation Logic

**Version**: 1.0  
**Last Updated**: January 2026

This document details the specific mathematical formulas and logic used in the Executive Dashboard and Optimizer.

---

## 1. Executive Dashboard Metrics

### 1.1 Efficiency Index ("Where The Money Is")

Measures whether a match type or segment is generating revenue efficiently relative to its spend.

**Formula**:
$$ \text{Efficiency Ratio} = \frac{\text{Share of Revenue} \%}{\text{Share of Spend} \%} $$

**Classification Thresholds**:
| Status | Threshold | Color | Meaning |
|--------|-----------|-------|---------|
| **Amplifier** | Ratio > 1.0 | 🟢 Emerald | Generating more revenue share than it costs in spend. |
| **Balanced** | 0.75 - 1.0 | 🔵 Teal | Performing adequately; spend matches return. |
| **Review** | 0.50 - 0.75 | 🟡 Amber | Underperforming; potential drag on efficiency. |
| **Drag** | < 0.50 | 🔴 Rose | Inefficient; consuming budget with little return. |

---

### 1.2 Performance Quadrants (Scatter Plot)

Classifies campaigns into four strategic zones based on ROAS and Conversion Rate (CVR).

**Baselines**:
- **Median ROAS**: Median of all active campaigns (Fallback: 3.0x)
- **Median CVR**: Median of all active campaigns (Fallback: 5.0%)

**Quadrants**:
1. **Stars (high ROAS, high CVR)**:
   - *Strategy*: Scale aggressively.
   - *Color*: 🟢 Emerald
2. **Scale Potential (high ROAS, low CVR)**:
   - *Strategy*: Increase traffic/bids; CVR is low but efficiency is high.
   - *Color*: 🟡 Amber
3. **Profit Potential (low ROAS, high CVR)**:
   - *Strategy*: Lower bids to improve ROAS; conversion is strong.
   - *Color*: 🔵 Cyan
4. **Cut (low ROAS, low CVR)**:
   - *Strategy*: Pause or aggressive negative targeting.
   - *Color*: 🔴 Rose

---

### 1.3 Strategic Gauges

#### A. Decision ROI
Return on Investment for the optimizer's actions.

$$ \text{Decision ROI} = \frac{\text{Net Decision Impact (\$)}}{\text{Total Managed Spend (\$)}} \times 100 $$

- **Target**: > 5%
- **Logic**: For every $100 managed, how much *incremental* value did decisions generated?

#### B. Spend Efficiency
Percentage of total spend flowing into "efficient" ad groups.

$$ \text{Efficiency Score} = \frac{\text{Spend in Ad Groups with ROAS} \ge 2.0}{\text{Total Spend}} \times 100 $$

- **Target**: > 50%
- **Logic**: Ensures budget is concentrating in high-performing areas.

---

## 2. Decision Impact Methodology

### 2.1 Incremental Value

Measured by comparing performance **14 days before** vs. **14 days after** an action, adjusted for market trends.

**Validation Status**:
Actions are only "Validated" if:
1. **Harvests**: Source term spend drops >90% (migration successful).
2. **Negatives**: Term spend drops to $0.
3. **Bid Changes**: CPC changes in the intended direction (>5%) AND/OR efficiency improves.

### 2.2 Market Tags
Used to distinguish decision quality from market movements.

- **Offensive Win**: Positive impact in a stable/growing market.
- **Defensive Win**: Spend saved (avoided waste) during a downturn or from a bleeder.
- **Gap Action**: Closing a performance gap (e.g., getting more traffic for a high-ROAS term).
- **Market Drag**: Negative impact caused by broader market conditions, not the decision itself.
