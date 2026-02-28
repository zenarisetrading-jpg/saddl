# Database Write Audit Report

## Summary

- **Total Write Operations Found**: 14 major database write operations
- **Confirmed Critical Issues**: 2
- **Suspected Issues**: 3
- **Operations Using Safe Context Managers**: 11/14 (79%)

---

## Actions Table Write Chain (Complete Call Path)

```
UI Button Click ("Run Analysis & Optimize" or "Save Run to History")
    ↓
features/optimizer_ui.py:142  →  run_clicked = st.button(...)
    ↓
features/optimizer_v2/runner.py  →  Optimization execution
    ↓
features/optimizer_shared/logging.py:89  →  log_optimization_events()
    (creates action list, stores in session state)
    ↓
st.session_state['pending_actions'] = {actions, client_id, batch_id, report_date}
    ↓
ui/action_confirmation.py:73  →  _save_pending_actions_and_navigate()
    OR
features/optimizer_v2/runner.py  →  direct flush_pending_actions_to_db() call
    ↓
features/optimizer_shared/logging.py:130  →  flush_pending_actions_to_db()
    ↓
get_db_manager(test_mode)  →  returns DatabaseManager (SQLite) OR PostgresManager
    ↓
db._get_connection()  (context manager)
    ↓
cur.execute(SQL, params)  for each action
    ↓
conn.commit()  (from context manager __exit__)
    ↓
actions_log table receives INSERT
```

---

## CRITICAL: Confirmed Write Failures

### 1. SQLite / PostgreSQL Parameterization Mismatch
- **File**: `features/optimizer_shared/logging.py` lines ~150–167
- **Issue**: `flush_pending_actions_to_db` uses PostgreSQL-style `%s` placeholders, but when the
  backend is SQLite (`DatabaseManager` from `db_manager.py`), SQLite expects `?` placeholders.
- **Failure mode**: `sqlite3.ProgrammingError: Incorrect number of bindings supplied` (or silent wrong-value binding).
- **Impact**: **100% failure rate** when using SQLite backend with the optimizer save flow.
- **Confidence**: HIGH

### 2. Missing `delete_action_batch` / `clear_todays_actions` in SQLite Backend
- **File**: `app_core/db_manager.py` — these methods are absent
- **Caller**: `ui/action_confirmation.py` calls `db.delete_action_batch()` and `db.clear_todays_actions()`
- **Failure mode**: `AttributeError` when user tries to undo or clear actions on a SQLite backend.
- **Impact**: Undo functionality completely broken for SQLite users.
- **Confidence**: HIGH

---

## SUSPECTED: Potential Write Failures

### 1. `save_account_health` Silent Failure
- **File**: `app_core/postgres_manager.py` lines ~2006–2044
- **Pattern**: `except Exception as e: print(...); return False`
- **Risk**: Callers may not check the `False` return value → account health silently not saved.
- **Verify**: Audit all callers of `save_account_health` to confirm return-value checks exist.

### 2. `get_client_ids` Returns Empty List on Any Error
- **File**: `app_core/db_manager.py` line ~1191
- **Pattern**: `except: return []`
- **Risk**: DB unreachable and "no clients found" produce identical return values → silent data loss
  or blank UI with no error shown to the user.
- **Confidence**: MEDIUM

### 3. Connection Pool Not Returned on `cursor()` Failure
- **File**: `app_core/postgres_manager.py` lines ~302–314
- **Risk**: If `conn.cursor()` raises, the `finally` block still calls `putconn`, but if
  `pool.getconn()` itself raises, the connection is never returned. Repeated failures could
  exhaust the pool.
- **Confidence**: LOW (edge case, needs stress test to confirm)

---

## Silent Failure Patterns

### `app_core/db_manager.py`

| Line | Pattern | Risk |
|------|---------|------|
| ~822 | `except:` in date parsing — returns `datetime.now().date()` | MEDIUM — invalid dates silently replaced |
| ~1124–1131 | `except:` in float parsing — sets values to `None` | MEDIUM — corrupted stats, no alert |
| ~1191 | `except: return []` in `get_client_ids` | HIGH — masks DB connectivity failures |
| ~1715 | `except:` in JSON parsing — returns empty metadata | LOW — silent metadata loss |
| ~1946 | `except:` in `migrate_bid_updates` schema check | LOW — migration skipped silently |

### `app_core/postgres_manager.py`

| Line | Pattern | Risk |
|------|---------|------|
| ~351 | `except Exception:` in `_schema_is_current` returns `False` | MEDIUM — schema init skipped on transient error |
| ~2006–2044 | `except Exception` in `save_account_health` — prints + returns `False` | HIGH — no log entry, caller may ignore |

---

## All DB Write Operations Inventory

| # | Operation | File | Line | Commit Pattern | Risk |
|---|-----------|------|------|----------------|------|
| 1 | `log_action_batch` (SQLite) | `app_core/db_manager.py` | ~1198–1255 | Context manager (auto-commit) | LOW |
| 2 | `log_action_batch` (PostgreSQL) | `app_core/postgres_manager.py` | ~1704–1775 | Context manager (auto-commit) | LOW |
| 3 | `flush_pending_actions_to_db` | `features/optimizer_shared/logging.py` | ~130–200 | Explicit `conn.commit()` + ctx mgr | **CRITICAL** |
| 4 | `save_weekly_stats` | `app_core/db_manager.py` | ~339–376 | Context manager | LOW |
| 5 | `save_weekly_stats_batch` | `app_core/db_manager.py` | ~379–419 | Context manager | LOW |
| 6 | `save_target_stats_batch` (SQLite) | `app_core/db_manager.py` | ~704–900 | Context manager | LOW |
| 7 | `save_target_stats_batch` (PostgreSQL) | `app_core/postgres_manager.py` | ~832–995 | Context manager | LOW |
| 8 | `save_category_mapping` | `app_core/db_manager.py` | ~922–960 | Context manager | LOW |
| 9 | `save_advertised_product_map` | `app_core/db_manager.py` | ~961–1065 | Context manager | LOW |
| 10 | `save_bulk_mapping` | `app_core/db_manager.py` | ~1066–1150 | Context manager | LOW |
| 11 | `save_account_health` (PostgreSQL) | `app_core/postgres_manager.py` | ~2006–2044 | Try/except + ctx mgr | MEDIUM |
| 12 | `delete_account` | `app_core/db_manager.py` | ~1720–1730 | Context manager | LOW |
| 13 | `delete_action_batch` | `app_core/postgres_manager.py` | ~1928–1936 | Context manager | **MISSING IN SQLite** |
| 14 | `clear_todays_actions` | `app_core/postgres_manager.py` | ~1938–1948 | Context manager | **MISSING IN SQLite** |

---

## Connection Management Summary

### SQLite (`app_core/db_manager.py`)
- Context manager defined at lines ~57–70
- Auto-commits on `__exit__` (line ~61)
- Auto-rollbacks on exception (line ~63)
- **Safe** for all operations using `with self._get_connection() as conn:`

### PostgreSQL (`app_core/postgres_manager.py`)
- Context manager defined at lines ~268–316
- Uses `ThreadedConnectionPool` for connection reuse
- Auto-commits on `__exit__` (line ~293)
- Rollback + marks connection bad on exception (lines ~302–308)
- Per-query statement timeout: 45 seconds (line ~291)
