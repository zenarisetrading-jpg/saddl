# Dependency Audit Report

## Summary

| Metric | Count |
|--------|-------|
| Total packages in requirements.txt | 19 |
| Ghost Dependencies (in requirements, not used in code) | 3 |
| Orphaned Imports (in code, not in requirements) | 0 |
| Active Dependencies (confirmed in use) | 16 |

---

## Ghost Dependencies (in requirements.txt but not used in code)

### 1. `openpyxl` — Confidence: HIGH
- Not directly imported anywhere in the project.
- The codebase explicitly uses the `xlsxwriter` engine for Excel output (`utils/formatters.py`).
- While pandas can use openpyxl as an alternate Excel engine, no code requests it.
- **Recommendation**: Remove. `xlsxwriter` covers all Excel output needs.

### 2. `kaleido` — Confidence: HIGH
- Typically required by Plotly for static image export (`fig.write_image()`, `fig.to_image()`).
- No usage of `write_image()` or `to_image()` found anywhere in the codebase.
- Plotly is used only for interactive Streamlit displays.
- **Recommendation**: Remove. Dead weight — adds ~50MB to install size for zero benefit.

### 3. `supabase` — Confidence: MEDIUM
- No `from supabase import` or `import supabase` statements found anywhere.
- All database connections use `psycopg2` directly with raw SQL.
- Supabase is the hosting platform (DATABASE_URL points to Supabase Postgres) but the Python SDK is never used.
- Likely a remnant from early planning or an alternate implementation that was abandoned.
- **Recommendation**: Remove if staying with psycopg2. Only keep if planning to migrate to Supabase SDK features (auth, realtime, etc.).

---

## Orphaned Imports (used in code but not in requirements.txt)

**None found.** All external packages imported in live code are declared in requirements.txt.

---

## Active Dependencies (confirmed in use)

| Package | Version Spec | Primary Usage | Key Files |
|---------|-------------|---------------|-----------|
| `streamlit` | >=1.28.0 | UI framework | `ui/*`, `features/*`, `ppcsuite_v4_ui_experiment.py` |
| `pandas` | >=2.0.0 | Data manipulation | `app_core/*`, `features/*`, `utils/*`, `tests/*` |
| `numpy` | >=1.24.0 | Numerical operations | `features/*`, `app_core/*` |
| `plotly` | >=5.17.0 | Data visualization | `features/impact/*`, `features/report_card.py` |
| `bcrypt` | >=4.0.1 | Password hashing | `app_core/auth/hashing.py` |
| `requests` | >=2.31.0 | HTTP requests | `api/*`, `pipelines/spapi_pipeline.py` |
| `psycopg2-binary` | ==2.9.9 | PostgreSQL driver | `app_core/postgres_manager.py`, `db/migrate.py` |
| `python-dotenv` | ==1.0.1 | Environment variables | `app_core/auth/service.py`, `utils/diagnostics.py` |
| `xlsxwriter` | >=3.1.0 | Excel file writing | `utils/formatters.py` |
| `fpdf2` | >=2.7.0 | PDF generation | `features/report_card.py` |
| `html2image` | >=2.0.0 | HTML → image conversion | `features/report_card.py` |
| `apscheduler` | ==3.10.4 | Background task scheduling | `pipelines/scheduler.py` |
| `requests-aws4auth` | ==1.3.1 | AWS Signature v4 auth (SP-API) | `pipelines/sp_api_client.py` |
| `scikit-learn` | >=1.3.0 | ML clustering (TF-IDF, KMeans) | `features/kw_cluster.py` |
| `pytest` | ==8.3.0 | Testing framework | `tests/*` |
| `pytest-mock` | ==3.14.0 | Test mocking | `tests/pipeline/*` |

---

## Version Pinning Analysis

### Strictly Pinned (`==`) — 6 packages
| Package | Assessment |
|---------|------------|
| `psycopg2-binary==2.9.9` | Appropriate — production DB driver, stability matters |
| `python-dotenv==1.0.1` | Reasonable — low-churn package |
| `apscheduler==3.10.4` | Appropriate — scheduler behavior must not change unexpectedly |
| `requests-aws4auth==1.3.1` | Appropriate — AWS auth signature format is sensitive |
| `pytest==8.3.0` | Acceptable — test-only, isolation is fine |
| `pytest-mock==3.14.0` | Acceptable — test-only |

### Flexible Lower Bound (`>=`) — 10 packages
- Consider adding **upper version bounds** for production stability.
- Example: `pandas>=2.0.0,<3.0.0` prevents silent major-version breakage.
- Highest risk packages for silent breaking changes: `streamlit`, `pandas`, `plotly`, `scikit-learn`.

---

## Recommendations

1. **Remove `openpyxl`** — not used, `xlsxwriter` covers all Excel output
2. **Remove `kaleido`** — no static Plotly image export exists; saves ~50MB install size
3. **Remove `supabase`** — psycopg2 is the actual DB driver; SDK is unused
4. **Add upper version bounds** on `streamlit`, `pandas`, `plotly`, `scikit-learn` to prevent silent major-version breakage in production deployments

---

## Methodology

- 233 Python files scanned (excluding `venv311/`, `st_env/`, `__pycache__/`, `.pytest_cache/`)
- Each package in requirements.txt mapped against `import` and `from ... import` statements
- Both direct imports and common aliased forms checked (e.g., `import numpy as np`)
