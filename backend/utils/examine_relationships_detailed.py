"""
Detailed examination of Valid_Relationships.xlsx
"""
import pandas as pd
from pathlib import Path
import sys

# Set UTF-8 encoding for output
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# Read the file
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
file_path = project_root / 'Valid_Relationships.xlsx'

df = pd.read_excel(file_path)

print("=" * 80)
print("VALID_RELATIONSHIPS.XLSX - DETAILED EXAMINATION")
print("=" * 80)

print(f"\nTotal Rows: {len(df)}")
print(f"Columns: {list(df.columns)}")

print(f"\nColumn Analysis:")
for col in df.columns:
    print(f"\n  {col}:")
    print(f"    Type: {df[col].dtype}")
    print(f"    Unique values: {df[col].nunique()}")
    print(f"    Null values: {df[col].isna().sum()}")

print(f"\nConfidence_Percent Statistics:")
print(df['Confidence_Percent'].describe())

print(f"\nRelation_Category Distribution:")
print(df['Relation_Category'].value_counts().head(20))

print(f"\nSample of relationships (first 5):")
for idx in range(min(5, len(df))):
    row = df.iloc[idx]
    print(f"\n--- Row {idx + 1} ---")
    print(f"ICD: {row['ICD_Code']} - {row['ICD_Description'][:60]}...")
    print(f"ACHI: {row['ACHI_Code']} - {row['ACHI_Description'][:60]}...")
    print(f"Category: {row['Relation_Category']}")
    print(f"Confidence: {row['Confidence_Percent']}")
    rel_text = str(row['Relationship'])
    print(f"Relationship: {rel_text[:100]}...")

print(f"\nChecking for suspicious patterns:")
# Check if all relationships are the same
unique_relationships = df['Relationship'].nunique()
print(f"Unique relationship texts: {unique_relationships}")

# Check if all confidences are the same
unique_confidences = df['Confidence_Percent'].nunique()
print(f"Unique confidence values: {unique_confidences}")

# Check for copy-paste patterns
if unique_relationships < 10:
    print("\n⚠️ WARNING: Very few unique relationship texts - possible copy-paste!")
    print("Most common relationship texts:")
    print(df['Relationship'].value_counts().head(5))

if unique_confidences < 10:
    print("\n⚠️ WARNING: Very few unique confidence values - likely hardcoded!")
    print("Confidence value distribution:")
    print(df['Confidence_Percent'].value_counts().head(10))


