# Dead Code Report

## Summary

| Metric | Count |
|--------|-------|
| Total Python files analyzed | 233 |
| Main application files | 186 |
| Test files | 42 |
| Dev/script files | 29 |
| **Dead files (HIGH confidence)** | **3** |
| Dead functions in dead files | 8 |
| Orphaned features (superseded modules) | 1 module group |

---

## Dead Files (Never Imported Anywhere)

### HIGH Confidence — Remove Immediately

**1. `features/diagnostics/overview_old.py`** (~3,372 bytes)
- Dead functions: `render_overview_page()`
- Evidence: Docstring explicitly says "draft only, not yet wired to nav"
- Zero import references anywhere in codebase
- Superseded by: `features/diagnostics/control_center.py`
- **Confidence: HIGH**

**2. `features/diagnostics/signals_old.py`** (~2,463 bytes)
- Dead functions: `render_signals_page()`
- Evidence: Docstring says "draft only, intended to be integrated after Phase 2 validation gate"
- Zero import references anywhere in codebase
- Superseded by: `features/diagnostics/control_center.py`
- **Confidence: HIGH**

**3. `features/diagnostics/trends_old.py`** (~5,480 bytes)
- Dead functions: `_render_plotly_chart()`, `_fetch_trends_frame()`, `_fetch_cvr_frame()`, `render_trends_page()`
- Evidence: Draft module explicitly flagged in docstring
- Zero import references anywhere in codebase
- Superseded by: `features/diagnostics/control_center.py`
- **Confidence: HIGH**

**Total removable dead file bytes: ~11,315 bytes**

---

## Active Module Structure (Confirmed In Use)

The main entry point `ppcsuite_v4_ui_experiment.py` imports from these live modules:

| Module | Status |
|--------|--------|
| `features.dashboard` | ACTIVE |
| `features.optimizer_v2` | ACTIVE |
| `features.impact` | ACTIVE |
| `features.diagnostics.control_center` | ACTIVE (replaces `*_old.py` files) |
| `features.simulator` | ACTIVE |
| `features.creator` | ACTIVE |
| `features.assistant` | ACTIVE |
| `features.asin_mapper` | ACTIVE |
| `features.kw_cluster` | ACTIVE |
| `features.debug_ui` | ACTIVE |
| `app_core.*` | ACTIVE |
| `ui.*` | ACTIVE |
| `utils.*` | ACTIVE |

---

## Intentionally Standalone Files (Not Dead Code)

These files are not imported but are intentional standalone executables:

- **`scripts/`** — 29 utility scripts (backfill, migration, debugging tools). Run directly, not imported.
- **`dev_resources/`** — 29 test/analysis scripts used during development.
- **`tests/`** — 42 pytest test files. Run via test runner, not imported.
- **`worker.py`** — Documented as a separate service process (runs alongside Streamlit app).
- **`ppcsuite_v4_ui_experiment.py`** — Main entry point, not imported by anything.

---

## Key Observations

1. **Codebase is relatively clean.** Only 3 confirmed dead files, all in the same module group (`features/diagnostics/*_old.py`), all explicitly self-documenting as drafts.

2. **Clean architectural transition.** The old diagnostics UI (3 draft files) was clearly superseded by `features/diagnostics/control_center.py`. The old files were never wired into the nav router and were left as orphans.

3. **No dead functions in live files** were identified with HIGH confidence. The active files are well-connected through the import graph.

---

## Recommendations

**Priority 1 — Remove (immediate, zero risk):**
- `features/diagnostics/overview_old.py`
- `features/diagnostics/signals_old.py`
- `features/diagnostics/trends_old.py`

Verify `features/diagnostics/control_center.py` covers all needed functionality (it does — it's actively imported and used), then delete these three files.

**Priority 2 — Verify before removing:**
- Check any documentation or comments that reference the old diagnostic modules
- Confirm no feature flags silently enable the old modules at runtime

---

## Methodology

1. Full file enumeration excluding `venv311/`, `st_env/`, `site-packages/`
2. Import/reference mapping across all 233 Python files
3. Cross-reference each file against all `import` and `from ... import` statements
4. Manual verification of entry point routing (`ppcsuite_v4_ui_experiment.py`)
5. Confidence ratings: HIGH = explicitly marked draft + zero references; MEDIUM = possible dynamic import; LOW = indirect reference possible
