"""
Category Discovery Script
Extracts ALL unique categories from the database to ensure 100% coverage
"""
import sqlite3
import pandas as pd
from pathlib import Path

def discover_all_categories():
    """
    Extract ALL unique categories from the database
    Ensures we know every category that needs coverage
    """
    script_dir = Path(__file__).parent
    db_path = script_dir.parent / 'data' / 'validation.db'
    
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        print("Please run: python utils/database_setup.py first")
        return None, None
    
    conn = sqlite3.connect(str(db_path))
    
    print("=" * 80)
    print("CATEGORY DISCOVERY REPORT")
    print("=" * 80)
    
    # Get ALL ICD categories
    icd_categories = pd.read_sql("""
        SELECT DISTINCT description 
        FROM icd10_main_categories
        WHERE description IS NOT NULL AND description != ''
        ORDER BY description
    """, conn)
    
    # Get ALL ACHI categories
    achi_categories = pd.read_sql("""
        SELECT DISTINCT block_short_desc 
        FROM code_blocks
        WHERE block_short_desc IS NOT NULL AND block_short_desc != ''
        ORDER BY block_short_desc
    """, conn)
    
    print(f"\nICD Categories: {len(icd_categories)}")
    print(f"ACHI Categories: {len(achi_categories)}")
    print(f"Total category combinations: {len(icd_categories) * len(achi_categories):,}")
    
    print(f"\n" + "=" * 80)
    print(f"TOP 20 ICD CATEGORIES:")
    print("=" * 80)
    for i, cat in enumerate(icd_categories['description'].head(20), 1):
        # Count codes in this category
        count = pd.read_sql(f"""
            SELECT COUNT(*) as count FROM icd10_main_categories 
            WHERE description = ?
        """, conn, params=(cat,))['count'][0]
        print(f"{i:2}. {cat} ({count} codes)")
    
    print(f"\n" + "=" * 80)
    print(f"TOP 20 ACHI CATEGORIES:")
    print("=" * 80)
    for i, cat in enumerate(achi_categories['block_short_desc'].head(20), 1):
        # Count codes in this category
        count = pd.read_sql(f"""
            SELECT COUNT(*) as count FROM code_blocks 
            WHERE block_short_desc = ?
        """, conn, params=(cat,))['count'][0]
        print(f"{i:2}. {cat} ({count} blocks)")
    
    conn.close()
    
    print(f"\n" + "=" * 80)
    print("✅ Category discovery complete!")
    print("=" * 80)
    
    return icd_categories['description'].tolist(), achi_categories['block_short_desc'].tolist()

if __name__ == "__main__":
    discover_all_categories()

