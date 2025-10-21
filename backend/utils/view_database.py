"""
SQLite Database Viewer
Simple script to view tables and data in the validation database
"""
import sqlite3
import pandas as pd
from pathlib import Path

def view_database():
    """
    Display database contents in a formatted way
    """
    script_dir = Path(__file__).parent
    db_path = script_dir.parent / 'data' / 'validation.db'
    
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        print("Please run: python utils/database_setup.py first")
        return
    
    conn = sqlite3.connect(str(db_path))
    
    print("=" * 80)
    print("DATABASE VIEWER - ICD-ACHI Validation System")
    print("=" * 80)
    print(f"Database: {db_path}")
    print()
    
    # Get all tables
    tables = pd.read_sql("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name
    """, conn)
    
    print(f"📊 Tables in database: {len(tables)}")
    print("-" * 80)
    
    for table_name in tables['name']:
        # Get row count
        count = pd.read_sql(f"SELECT COUNT(*) as count FROM {table_name}", conn)['count'][0]
        
        # Get column info
        columns = pd.read_sql(f"PRAGMA table_info({table_name})", conn)
        
        print(f"\n📋 Table: {table_name}")
        print(f"   Rows: {count:,}")
        print(f"   Columns: {len(columns)}")
        print(f"   Structure:")
        for _, col in columns.iterrows():
            print(f"      - {col['name']} ({col['type']})")
        
        # Show sample data (first 3 rows)
        if count > 0:
            print(f"   Sample data (first 3 rows):")
            sample = pd.read_sql(f"SELECT * FROM {table_name} LIMIT 3", conn)
            for idx, row in sample.iterrows():
                print(f"      Row {idx + 1}:")
                for col in sample.columns[:5]:  # Show first 5 columns only
                    value = str(row[col])
                    if len(value) > 50:
                        value = value[:50] + "..."
                    print(f"         {col}: {value}")
        print("-" * 80)
    
    # Special focus on valid_relationships
    print("\n" + "=" * 80)
    print("🔍 VALID RELATIONSHIPS TABLE (Sample Ground Truth)")
    print("=" * 80)
    
    rel_count = pd.read_sql("SELECT COUNT(*) as count FROM valid_relationships", conn)['count'][0]
    print(f"Total sample relationships: {rel_count}")
    
    if rel_count > 0:
        print("\n📊 Statistics:")
        
        # By source
        by_source = pd.read_sql("""
            SELECT source, COUNT(*) as count
            FROM valid_relationships
            GROUP BY source
        """, conn)
        print("\nBy Source:")
        for _, row in by_source.iterrows():
            print(f"  {row['source']}: {row['count']}")
        
        # By category
        by_category = pd.read_sql("""
            SELECT category, COUNT(*) as count
            FROM valid_relationships
            GROUP BY category
            ORDER BY count DESC
            LIMIT 10
        """, conn)
        print("\nTop 10 Categories (by count):")
        for idx, row in by_category.iterrows():
            print(f"  {idx + 1}. {row['category']}: {row['count']}")
        
        # Sample relationships
        print("\n📋 Sample Valid Relationships:")
        samples = pd.read_sql("""
            SELECT icd_code, icd_description, achi_code, achi_description, 
                   confidence, category
            FROM valid_relationships
            ORDER BY confidence DESC
            LIMIT 5
        """, conn)
        
        for idx, row in samples.iterrows():
            print(f"\n  {idx + 1}. ICD: {row['icd_code']} - {row['icd_description'][:50]}")
            print(f"     ACHI: {row['achi_code']} - {row['achi_description'][:50]}")
            print(f"     Category: {row['category']}")
            print(f"     Confidence: {row['confidence']:.2f}")
    else:
        print("\n⚠️ No sample relationships found!")
        print("Run: python utils/generate_sample_relationships.py to generate them")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ Database viewer complete!")
    print("=" * 80)
    print("\n💡 To view with a GUI tool, download DB Browser for SQLite:")
    print("   https://sqlitebrowser.org/")
    print(f"\n   Then open: {db_path}")

if __name__ == "__main__":
    view_database()

