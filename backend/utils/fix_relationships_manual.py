"""
Fix Valid_Relationships.xlsx manually with medical knowledge
"""
import pandas as pd
from pathlib import Path
import re

# Read the file
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
input_file = project_root / 'Valid_Relationships.xlsx'

print(f"Reading: {input_file}")
df = pd.read_excel(input_file)

print(f"Original shape: {df.shape}")
print(f"Columns: {list(df.columns)}")

# Show first 30 relationships to analyze
print("\n=== FIRST 30 RELATIONSHIPS ===")
for idx in range(min(30, len(df))):
    row = df.iloc[idx]
    print(f"{idx+1}. ICD: {row['ICD_Code']} ({row['ICD_Description'][:40]}...)")
    print(f"   ACHI: {row['ACHI_Code']} ({row['ACHI_Description'][:40]}...)")
    print(f"   Category: {row['Relation_Category']}")
    print()


