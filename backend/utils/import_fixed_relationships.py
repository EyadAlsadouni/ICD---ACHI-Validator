"""
Import FIXED relationships (only valid ones) into database
"""
import pandas as pd
import sqlite3
from pathlib import Path

# Paths
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
input_file = project_root / 'Valid_Relationships_FIXED.xlsx'
db_path = script_dir.parent / 'data' / 'validation.db'

print("=" * 80)
print("IMPORTING FIXED VALID_RELATIONSHIPS TO DATABASE")
print("=" * 80)

# Read fixed file
df = pd.read_excel(input_file)
print(f"\nTotal relationships in file: {len(df)}")

# Filter for ONLY VALID ones (confidence >= 70%)
df_valid = df[df['Confidence_Percent'] >= 70].copy()
print(f"Valid relationships (confidence >= 70%): {len(df_valid)}")

# Map columns
df_mapped = pd.DataFrame({
    'icd_code': df_valid['ICD_Code'],
    'icd_description': df_valid['ICD_Description'],
    'icd_category': df_valid['Relation_Category'],
    'achi_code': df_valid['ACHI_Code'],
    'achi_description': df_valid['ACHI_Description'],
    'achi_category': df_valid['Relation_Category'],
    'relationship': df_valid['Relationship'],
    'confidence': df_valid['Confidence_Percent'] / 100.0,
    'category': df_valid['Relation_Category'],
    'source': 'manual_curated'
})

# Connect to database
conn = sqlite3.connect(str(db_path))

# Clear existing
print("\nClearing old data...")
conn.execute("DELETE FROM valid_relationships")
conn.commit()

# Import
print(f"Importing {len(df_mapped)} VALID relationships...")
df_mapped.to_sql('valid_relationships', conn, if_exists='append', index=False)
conn.commit()

# Verify
count = conn.execute("SELECT COUNT(*) FROM valid_relationships").fetchone()[0]

print(f"\n" + "=" * 80)
print("SUCCESS!")
print("=" * 80)
print(f"Imported {count} VALID relationships")
print(f"\nConfidence breakdown:")
conf_stats = df_mapped['confidence'].describe()
print(f"  Min:  {conf_stats['min']:.2f}")
print(f"  Mean: {conf_stats['mean']:.2f}")
print(f"  Max:  {conf_stats['max']:.2f}")

print(f"\nTop categories:")
top_cats = df_mapped['category'].value_counts().head(10)
for cat, count in top_cats.items():
    print(f"  {cat}: {count}")

conn.close()

print("\n" + "=" * 80)
print("DATABASE IS NOW READY TO USE!")
print("=" * 80)
print("\nStart the application:")
print("  Terminal 1: cd backend && uvicorn app:app --host 0.0.0.0 --port 5003 --reload")
print("  Terminal 2: cd frontend && npm start")


