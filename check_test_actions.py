#!/usr/bin/env python3
"""Check action types in TEST database"""

import sqlite3
from pathlib import Path

db_path = Path("data/ppc_test.db")

if not db_path.exists():
    print(f"Database not found: {db_path}")
    exit(1)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("\n" + "=" * 50)
print("ACTION TYPES IN TEST DATABASE")
print("=" * 50)

cursor.execute("""
    SELECT action_type, COUNT(*) as count 
    FROM actions_log 
    GROUP BY action_type 
    ORDER BY count DESC
""")

results = cursor.fetchall()

if not results:
    print("No actions found in database")
else:
    print(f"\n{'Action Type':<25} {'Count':>10}")
    print("-" * 50)
    for action_type, count in results:
        print(f"{action_type:<25} {count:>10,}")
    
    cursor.execute("SELECT COUNT(*) FROM actions_log")
    total = cursor.fetchone()[0]
    print("-" * 50)
    print(f"{'TOTAL':<25} {total:>10,}")

print("=" * 50 + "\n")

conn.close()
