"""
Quick check if relationships were imported
"""
import sqlite3
from pathlib import Path

script_dir = Path(__file__).parent
db_path = script_dir.parent / 'data' / 'validation.db'

conn = sqlite3.connect(str(db_path))

# Check count
count = conn.execute("SELECT COUNT(*) FROM valid_relationships").fetchone()[0]
print(f"Valid relationships in database: {count}")

# Show sample
if count > 0:
    print("\nFirst 3 relationships:")
    cursor = conn.execute("""
        SELECT icd_code, achi_code, confidence, category 
        FROM valid_relationships 
        LIMIT 3
    """)
    for row in cursor:
        print(f"  {row[0]} + {row[1]} = confidence {row[2]:.2f}, category: {row[3]}")

conn.close()


