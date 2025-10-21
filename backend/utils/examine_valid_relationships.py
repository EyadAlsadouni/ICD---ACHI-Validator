"""
Examine the Valid_Relationships.xlsx file
"""
import pandas as pd
from pathlib import Path

# Read the file from project root
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
file_path = project_root / 'Valid_Relationships.xlsx'

print(f"Looking for file at: {file_path}")
print(f"File exists: {file_path.exists()}")

df = pd.read_excel(file_path)

print("=" * 80)
print("VALID_RELATIONSHIPS.XLSX - EXAMINATION")
print("=" * 80)

print(f"\nRows: {len(df)}")
print(f"Columns: {len(df.columns)}")

print(f"\nColumn Names:")
for i, col in enumerate(df.columns, 1):
    print(f"  {i}. {col}")

print(f"\nFirst 10 rows:")
print(df.head(10).to_string())

print(f"\nColumn dtypes:")
print(df.dtypes)

print(f"\nSample relationships:")
for idx, row in df.head(5).iterrows():
    print(f"\n--- Row {idx + 1} ---")
    for col in df.columns:
        value = str(row[col])
        if len(value) > 100:
            value = value[:100] + "..."
        print(f"{col}: {value}")

