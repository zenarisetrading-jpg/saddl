# Upper Version Bounds Report — requirements.txt

**Date:** 2026-02-28
**File modified:** `requirements.txt`
**Task:** Add upper version bounds to high-risk dependencies.

---

## Changes Made

### 1. `streamlit`

| Field | Value |
|-------|-------|
| Original line | `streamlit>=1.28.0` |
| New line | `streamlit>=1.28.0,<2.0.0` |
| Action | Added upper bound `<2.0.0` (lower bound already present; not pinned) |

---

### 2. `pandas`

| Field | Value |
|-------|-------|
| Original line | `pandas>=2.0.0` |
| New line | `pandas>=2.0.0,<3.0.0` |
| Action | Kept current lower bound `>=2.0.0`; added upper bound `<3.0.0` |

---

### 3. `plotly`

| Field | Value |
|-------|-------|
| Original line | `plotly>=5.17.0` |
| New line | `plotly>=5.17.0,<6.0.0` |
| Action | Kept current lower bound `>=5.17.0`; added upper bound `<6.0.0` |

---

### 4. `scikit-learn`

| Field | Value |
|-------|-------|
| Original line | `scikit-learn>=1.3.0` |
| New line | `scikit-learn>=1.3.0,<2.0.0` |
| Action | Kept current lower bound `>=1.3.0`; added upper bound `<2.0.0` |

---

## Packages Already Having Upper Bounds (Skipped)

None. All four target packages lacked upper bounds before this change.

---

## Packages Skipped Due to Pinned Version (`==`)

None of the four target packages were pinned. (Note: other packages in the file such as `psycopg2-binary==2.9.9`, `python-dotenv==1.0.1`, `requests-aws4auth==1.3.1`, `apscheduler==3.10.4`, `pytest==8.3.0`, and `pytest-mock==3.14.0` are pinned, but they are not among the four target packages and were left entirely unchanged.)

---

## Final State of Relevant Lines in `requirements.txt`

```
streamlit>=1.28.0,<2.0.0
pandas>=2.0.0,<3.0.0
scikit-learn>=1.3.0,<2.0.0
plotly>=5.17.0,<6.0.0
```

All other lines in `requirements.txt` were left unchanged.
