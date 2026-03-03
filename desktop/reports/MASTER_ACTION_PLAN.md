# SADDL Master Action Plan

**Generated:** 2026-02-28
**Source Reports:** agent1_deadcode_report.md, agent2_dependencies_report.md, agent3_sessionstate_report.md, agent4_dbwrite_report.md

---

## CRITICAL — Fix First (Stability / Data Integrity Impact)

### 1. SQLite / PostgreSQL Parameterization Mismatch in Optimizer Save Flow
- **What to do:** Fix `flush_pending_actions_to_db()` to detect backend type and use correct placeholder format (`%s` for PostgreSQL, `?` for SQLite), OR enforce PostgreSQL-only usage at runtime with a clear error if SQLite detected.
- **File:** `features/optimizer_shared/logging.py` lines ~150–167
- **Confidence:** HIGH
- **Risk if NOT fixed:** 100% failure rate when users with SQLite backend try to save optimizer results. Actions log insert fails with `sqlite3.ProgrammingError: Incorrect number of bindings supplied`.

### 2. Missing `delete_action_batch()` & `clear_todays_actions()` in SQLite Backend
- **What to do:** Implement `delete_action_batch()` and `clear_todays_actions()` in `app_core/db_manager.py` (currently only exist in `postgres_manager.py`). Called by `ui/action_confirmation.py`.
- **File:** `app_core/db_manager.py` (add methods to SQLite class)
- **Confidence:** HIGH
- **Risk if NOT fixed:** `AttributeError` crash when any SQLite user tries to undo actions or clear today's actions. Undo functionality 100% broken on SQLite.

### 3. CRASH RISK: `theme_mode` Read Without Initialization Guard
- **What to do:** Add `if "theme_mode" not in st.session_state:` guard before the dot-notation access at `ui/theme.py:18`. Change to safe conditional init.
- **File:** `ui/theme.py` lines 10–25
- **Confidence:** HIGH
- **Risk if NOT fixed:** `KeyError` crash on first load if session state not pre-initialized before theme module runs.

### 4. CRASH RISK: `unified_data` Dictionary Access Without None Guard
- **What to do:** Replace `st.session_state.unified_data['search_term_report']` with `st.session_state.get("unified_data", {}).get("search_term_report")`.
- **File:** `features/assistant.py` line 260
- **Confidence:** HIGH
- **Risk if NOT fixed:** `KeyError` or `TypeError` crash if `unified_data` is `None` or missing key during assistant feature usage.

### 5. CRASH RISK: `active_perf_tab` Initialization Not Guaranteed Before Feature-Flag Branches
- **What to do:** Move `st.session_state["active_perf_tab"]` initialization to before line 215 in the entry point, outside all conditional feature-flag logic so it runs on every load.
- **File:** `ppcsuite_v4_ui_experiment.py` lines 212–228
- **Confidence:** HIGH
- **Risk if NOT fixed:** Feature-flag branches at lines 215–216 can skip initialization; lines 226+ then try to read it — `KeyError` in specific feature configurations.

### 6. CRASH RISK: `amazon_connected` & `amazon_client_id` Never Set But Read
- **What to do:** Either (A) implement the Amazon OAuth logic that sets these keys, OR (B) remove the dead read code at `ui/onboarding.py:407,458` if this feature is cancelled.
- **File:** `ui/onboarding.py` lines 407, 458
- **Confidence:** MEDIUM
- **Risk if NOT fixed:** `KeyError` crash if user reaches this onboarding path. Indicates incomplete OAuth feature.

### 7. CRASH RISK: `read_only_mode` Never Set But Read in Shared Report Feature
- **What to do:** Add explicit `read_only_mode` initialization in the shared report handler. Currently read at `ui/client_report_page.py:1295` with no assignment anywhere in the codebase.
- **File:** `ui/client_report_page.py` line 1295
- **Confidence:** MEDIUM
- **Risk if NOT fixed:** `KeyError` when any user opens a shared report link — the entire shared reports feature is broken.

### 8. CRASH RISK: `onboarding_step` Read Without Guaranteed Init in Render Path
- **What to do:** Add guard at `ui/onboarding.py:100` before reading `st.session_state.onboarding_step`: `if "onboarding_step" not in st.session_state: st.session_state.onboarding_step = 0`.
- **File:** `ui/onboarding.py` lines 94–110
- **Confidence:** MEDIUM
- **Risk if NOT fixed:** `KeyError` if user hits the onboarding page in certain state transitions.

---

## HIGH — Remove (Clear Dead Code, High Confidence)

### 1. Delete `features/diagnostics/overview_old.py`
- **What to do:** Delete the file. Contains only `render_overview_page()`, explicitly marked "draft only, not yet wired to nav" in docstring. Superseded by `control_center.py`.
- **File:** `features/diagnostics/overview_old.py` (~3,372 bytes)
- **Confidence:** HIGH
- **Risk if NOT removed:** None — never imported anywhere. Pure clutter.

### 2. Delete `features/diagnostics/signals_old.py`
- **What to do:** Delete the file. Contains `render_signals_page()`, marked "draft only, intended to be integrated after Phase 2 validation gate." Superseded by `control_center.py`.
- **File:** `features/diagnostics/signals_old.py` (~2,463 bytes)
- **Confidence:** HIGH
- **Risk if NOT removed:** None — never imported anywhere.

### 3. Delete `features/diagnostics/trends_old.py`
- **What to do:** Delete the file. Contains `_render_plotly_chart()`, `_fetch_trends_frame()`, `_fetch_cvr_frame()`, `render_trends_page()`. Marked as draft. Superseded by `control_center.py`.
- **File:** `features/diagnostics/trends_old.py` (~5,480 bytes)
- **Confidence:** HIGH
- **Risk if NOT removed:** None — never imported anywhere. ~11KB total for all 3 files.

### 4. Remove `openpyxl` from `requirements.txt`
- **What to do:** Delete `openpyxl` line from `requirements.txt`. Not imported anywhere. `xlsxwriter` covers all Excel output (`utils/formatters.py`).
- **File:** `requirements.txt`
- **Confidence:** HIGH
- **Risk if NOT removed:** Unnecessary install overhead. Zero functional impact.

### 5. Remove `kaleido` from `requirements.txt`
- **What to do:** Delete `kaleido` line from `requirements.txt`. Not imported anywhere. No static Plotly image export (`write_image()` / `to_image()`) exists in the codebase.
- **File:** `requirements.txt`
- **Confidence:** HIGH
- **Risk if NOT removed:** ~50MB dead weight added to every install/deploy.

### 6. Remove `supabase` from `requirements.txt`
- **What to do:** Delete `supabase` line if staying with psycopg2 direct SQL (current architecture). Not imported anywhere — all DB access uses raw psycopg2.
- **File:** `requirements.txt`
- **Confidence:** MEDIUM (depends on whether Supabase SDK migration is planned)
- **Risk if NOT removed:** Dead SDK dependency. Only keep if migrating to Supabase SDK (auth, realtime, etc.).

---

## MEDIUM — Cleanup (Low Risk Improvements)

### 1. Remove Write-Only Session State Key: `last_upload_result`
- **What to do:** Remove assignment at `ui/data_hub.py:370`. Set but never read anywhere.
- **File:** `ui/data_hub.py` line 370
- **Confidence:** HIGH

### 2. Remove Write-Only Session State Key: `onboarding_completed`
- **What to do:** Either wire to a real check or remove assignment at `ui/onboarding.py:65`. Set but never read.
- **File:** `ui/onboarding.py` line 65
- **Confidence:** HIGH

### 3. Remove Write-Only Session State Key: `perf_dash_spapi_available`
- **What to do:** Remove assignment at `ui/performance_dashboard/business_overview.py:1672`. Set but never read.
- **File:** `ui/performance_dashboard/business_overview.py` line 1672
- **Confidence:** HIGH

### 4. Remove Write-Only Session State Keys: `run_optimizer` & `should_log_actions`
- **What to do:** Remove both assignments at `app_core/data_hub.py` lines 130, 131, 576, 577. Both keys set but never read — legacy flags not wired to anything.
- **File:** `app_core/data_hub.py` lines 130, 131, 576, 577
- **Confidence:** HIGH

### 5. Remove Write-Only Session State Key: `data`
- **What to do:** Remove assignment at `ppcsuite_v4_ui_experiment.py:154`. Set but never read. Could be a large dict bloating every user session.
- **File:** `ppcsuite_v4_ui_experiment.py` line 154
- **Confidence:** HIGH

### 6. Verify & Remove Write-Only Session State Key: `single_account_mode`
- **What to do:** Confirm `single_account_mode` (set at `ui/account_manager.py:84,99`) is never read, then remove both assignments.
- **File:** `ui/account_manager.py` lines 84, 99
- **Confidence:** HIGH

### 7. Verify & Remove Write-Only Session State Key: `_impact_metrics`
- **What to do:** Confirm `_impact_metrics` (set at `features/impact/components/hero.py:62`) has no read location, then remove the assignment.
- **File:** `features/impact/components/hero.py` line 62
- **Confidence:** MEDIUM

### 8. Consolidate 12 Fragmented `opt_*` Config Keys Into Single Dict
- **What to do:** Replace the 12 individual flat `opt_*` keys with a single `opt_config` dict initialized at `features/optimizer_shared/__init__.py`. Reduces fragility and makes future audits trivial.
- **File:** `features/optimizer_shared/__init__.py` lines 36–59
- **Confidence:** MEDIUM

### 9. Replace `save_account_health` Silent Failure with Proper Logging
- **What to do:** In `app_core/postgres_manager.py:2006–2044`, replace `print(...)` in the exception handler with proper `logging.error(...)`. Audit all callers to confirm they check the `False` return value.
- **File:** `app_core/postgres_manager.py` lines ~2006–2044
- **Confidence:** MEDIUM

### 10. Fix `get_client_ids` Bare `except` to Distinguish Error from Empty
- **What to do:** Change `except: return []` at `app_core/db_manager.py:~1191` to `except Exception as e: logger.error(f"get_client_ids failed: {e}"); return []`. DB failure and "no clients" should not be silent equals.
- **File:** `app_core/db_manager.py` line ~1191
- **Confidence:** MEDIUM

### 11. Add Upper Version Bounds to High-Risk Dependencies
- **What to do:** Add upper bounds in `requirements.txt` for: `streamlit`, `pandas`, `plotly`, `scikit-learn`. Example: `streamlit>=1.28.0,<2.0.0`.
- **File:** `requirements.txt`
- **Confidence:** MEDIUM

### 12. Standardize Session State Initialization Pattern
- **What to do:** Create a centralized `init_session_state()` function (e.g., in `app_core/session_state.py`) that initializes all 57 known keys with sensible defaults at app startup. Call it once at the top of `ppcsuite_v4_ui_experiment.py`.
- **File:** New file + `ppcsuite_v4_ui_experiment.py`
- **Confidence:** MEDIUM

---

## LOW — Nice to Have

### 1. Audit Connection Pool Return on Cursor Failure
- **What to do:** Verify that `putconn` is always called in `app_core/postgres_manager.py:302–314` even if `conn.cursor()` raises. Edge case that could exhaust the connection pool under stress.
- **File:** `app_core/postgres_manager.py` lines ~302–314
- **Confidence:** LOW

### 2. Replace All Bare `except:` Blocks in DB Code
- **What to do:** Systematic replacement of all bare `except:` and unlogged `except Exception:` in:
  - `app_core/db_manager.py` lines ~822, ~1124–1131, ~1715, ~1946
  - `app_core/postgres_manager.py` line ~351

  Use typed catches with logging to surface silent data corruption (invalid dates, missing stats, skipped migrations).
- **File:** `app_core/db_manager.py`, `app_core/postgres_manager.py`
- **Confidence:** MEDIUM

### 3. Document SQLite vs PostgreSQL Support Decision
- **What to do:** Create an architecture decision record documenting: is dual-backend (SQLite + PostgreSQL) supported? If yes, implement missing SQLite methods (items 1–2 in CRITICAL). If no, document PostgreSQL-only and remove SQLite compatibility code to eliminate future confusion.
- **File:** `dev_resources/ARCHITECTURE_DECISIONS.md` (new file)
- **Confidence:** MEDIUM

### 4. Add `TypedDict` or `dataclass` for Session State Schema
- **What to do:** Define a `SessionState` typed structure to enable IDE type-checking and catch uninitialized key reads at development time rather than at runtime.
- **File:** New `app_core/session_schema.py`
- **Confidence:** LOW

### 5. Remove `lightgbm.py` Root-Level File (Investigate First)
- **What to do:** Verify whether `lightgbm.py` at the project root is a standalone experiment or an active module. If standalone/unused, delete it — it appears misplaced for a production app root.
- **File:** `lightgbm.py` (project root)
- **Confidence:** LOW (needs verification)

---

## Summary

| Category | Items | Priority |
|----------|-------|----------|
| **CRITICAL** — Fix First | 8 | Immediate |
| **HIGH** — Remove Dead Code | 6 | This week |
| **MEDIUM** — Cleanup | 12 | Within sprint |
| **LOW** — Nice to Have | 5 | Backlog |
| **TOTAL** | **31** | — |

## Estimated Effort

| Category | Effort |
|----------|--------|
| CRITICAL fixes | 8–12 hours |
| HIGH removals | 1–2 hours |
| MEDIUM cleanup | 4–6 hours |
| LOW improvements | 2–4 hours |
| **Total** | **~20–25 hours** |

## Post-Fix Testing Checklist

- [ ] After CRITICAL fixes: run full test suite with both SQLite and PostgreSQL backends
- [ ] After HIGH deletions: verify no import errors on app startup
- [ ] After session state cleanup: manually walk through every page in app to confirm no KeyErrors
- [ ] Regression test: optimizer save → action confirmation → undo flow end-to-end
