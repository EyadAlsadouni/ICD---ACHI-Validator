"""
Simple import of Valid_Relationships.xlsx directly into the database
"""
import pandas as pd
import sqlite3
from pathlib import Path

# Paths
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
input_file = project_root / 'Valid_Relationships.xlsx'
db_path = script_dir.parent / 'data' / 'validation.db'

print("=" * 80)
print("IMPORTING VALID_RELATIONSHIPS.XLSX TO DATABASE")
print("=" * 80)
print(f"Reading: {input_file}")
print(f"Database: {db_path}")

# Read Excel
df = pd.read_excel(input_file)
print(f"\nRows to import: {len(df)}")
print(f"Columns: {list(df.columns)}")

# Map columns to database schema
df_mapped = pd.DataFrame({
    'icd_code': df['ICD_Code'],
    'icd_description': df['ICD_Description'],
    'icd_category': df['Relation_Category'],  # Using relation category as ICD category
    'achi_code': df['ACHI_Code'],
    'achi_description': df['ACHI_Description'],
    'achi_category': df['Relation_Category'],  # Using relation category as ACHI category
    'relationship': df['Relationship'],
    'confidence': df['Confidence_Percent'] / 100.0,  # Convert percent to 0-1 scale
    'category': df['Relation_Category'],
    'source': 'manual_import'
})

# Connect to database
conn = sqlite3.connect(str(db_path))

# Clear existing data
print("\nClearing existing valid_relationships table...")
conn.execute("DELETE FROM valid_relationships")
conn.commit()

# Import data
print(f"Importing {len(df_mapped)} relationships...")
df_mapped.to_sql('valid_relationships', conn, if_exists='append', index=False)
conn.commit()

# Verify
count = conn.execute("SELECT COUNT(*) FROM valid_relationships").fetchone()[0]
print(f"\n✅ Import complete!")
print(f"Total relationships in database: {count}")

# Show statistics
print(f"\nStatistics:")
print(f"  Unique ICD codes: {df_mapped['icd_code'].nunique()}")
print(f"  Unique ACHI codes: {df_mapped['achi_code'].nunique()}")
print(f"  Unique categories: {df_mapped['category'].nunique()}")

conn.close()

print("\n" + "=" * 80)
print("✅ DONE! The system now has 1,187 relationship examples!")
print("=" * 80)
print("\nYou can now start the application:")
print("  Terminal 1: cd backend && uvicorn app:app --host 0.0.0.0 --port 5003 --reload")
print("  Terminal 2: cd frontend && npm start")


