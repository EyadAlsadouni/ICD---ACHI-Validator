"""
Excel File Diagnostic Tool
Checks the actual structure and columns in the 4 Excel files
"""
import pandas as pd
from pathlib import Path

def diagnose_excel_files():
    """
    Check actual column names and structure of Excel files
    """
    project_root = Path(__file__).parent.parent.parent
    
    print("=" * 80)
    print("EXCEL FILES DIAGNOSTIC TOOL")
    print("=" * 80)
    print(f"Project root: {project_root}\n")
    
    files = [
        'ICD10-AM.xlsx',
        'ACHI_Codes.xlsx',
        'Code_blocks.xlsx',
        'ICD10_Main_Categories.xlsx'
    ]
    
    for filename in files:
        file_path = project_root / filename
        
        print("-" * 80)
        print(f"📄 File: {filename}")
        print("-" * 80)
        
        if not file_path.exists():
            print(f"❌ FILE NOT FOUND at {file_path}\n")
            continue
        
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            
            print(f"✅ File found and readable")
            print(f"   Rows: {len(df):,}")
            print(f"   Columns: {len(df.columns)}")
            print(f"\n   Column Names (exact):")
            
            for i, col in enumerate(df.columns, 1):
                print(f"      {i}. '{col}' (type: {df[col].dtype})")
            
            print(f"\n   First 3 rows (sample data):")
            print(df.head(3).to_string())
            
            print(f"\n   Column name analysis:")
            for col in df.columns:
                col_lower = col.lower().strip()
                print(f"      '{col}' → lowercase/stripped: '{col_lower}'")
            
        except Exception as e:
            print(f"❌ ERROR reading file: {e}")
        
        print()
    
    print("=" * 80)
    print("✅ Diagnostic complete!")
    print("=" * 80)
    print("\nThis information will help fix the database_setup.py script")
    print("to correctly match column names from your Excel files.")

if __name__ == "__main__":
    diagnose_excel_files()

