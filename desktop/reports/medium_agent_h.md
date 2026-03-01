# Fix Report: Bare `except` in `get_all_clients` (db_manager.py)

## Summary

Replaced a bare `except:` block in `app_core/db_manager.py` with a proper exception handler that logs the error.

---

## Original Bare Except Block

Located at approximately line 1191 (before edits), inside the `get_all_clients` method:

```python
def get_all_clients(self) -> List[str]:
    """Get list of all client IDs with data."""
    with self._get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT DISTINCT client_id FROM target_stats ORDER BY client_id")
            return [row[0] for row in cursor.fetchall()]
        except:
            return []
```

Note: The task referenced a function named `get_client_ids`; the actual function in the file is `get_all_clients`. The bare `except:` at the expected line range was inside this function.

---

## Logger Variable Used

No logger existed in the file prior to this change. The following were added near the top of the file (after existing imports):

```python
import logging
logger = logging.getLogger(__name__)
```

The logger variable name is: `logger`

---

## Exact Replacement Made

### Imports / logger added (lines 9 and 18):

```python
# Added after: import sqlite3
import logging

# Added after all imports, before the class definition:
logger = logging.getLogger(__name__)
```

### Exception handler replacement:

**Before:**
```python
        except:
            return []
```

**After:**
```python
        except Exception as e:
            logger.error(f"get_client_ids failed: {e}")
            return []
```

---

## Syntax Check Result

```
SYNTAX OK
```

Command run:
```
python3 -c "import ast; ast.parse(open('app_core/db_manager.py').read()); print('SYNTAX OK')"
```

---

## Files Changed

- `app_core/db_manager.py` — two surgical edits only:
  1. Added `import logging` and `logger = logging.getLogger(__name__)` near the top.
  2. Replaced bare `except:` with `except Exception as e:` + `logger.error(...)` in `get_all_clients`.
