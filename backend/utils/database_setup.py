"""
Database Setup Script
Converts 4 Excel files into unified SQLite database with complete schema
"""
import sqlite3
import pandas as pd
import os
from pathlib import Path

def create_database():
    """
    Create SQLite database from 4 Excel files
    """
    # Determine paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    data_dir = script_dir.parent / 'data'
    
    # Create data directory if it doesn't exist
    data_dir.mkdir(exist_ok=True)
    
    db_path = data_dir / 'validation.db'
    
    # Remove existing database
    if db_path.exists():
        db_path.unlink()
        print(f"Removed existing database at {db_path}")
    
    # Connect to database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("Creating database schema...")
    print("=" * 80)
    
    # Create tables
    cursor.execute("""
        CREATE TABLE icd10am_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL
        )
    """)
    print("✓ Created table: icd10am_codes")
    
    cursor.execute("""
        CREATE TABLE code_blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_id TEXT UNIQUE NOT NULL,
            block_short_desc TEXT,
            block_description TEXT
        )
    """)
    print("✓ Created table: code_blocks")
    
    cursor.execute("""
        CREATE TABLE achi_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL,
            short_description TEXT,
            block_id TEXT,
            FOREIGN KEY (block_id) REFERENCES code_blocks(block_id)
        )
    """)
    print("✓ Created table: achi_codes")
    
    cursor.execute("""
        CREATE TABLE icd10_main_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            description TEXT
        )
    """)
    print("✓ Created table: icd10_main_categories")
    
    cursor.execute("""
        CREATE TABLE valid_relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            icd_code TEXT NOT NULL,
            icd_description TEXT NOT NULL,
            icd_category TEXT NOT NULL,
            achi_code TEXT NOT NULL,
            achi_description TEXT NOT NULL,
            achi_category TEXT NOT NULL,
            relationship TEXT NOT NULL,
            confidence FLOAT NOT NULL,
            category TEXT NOT NULL,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source TEXT DEFAULT 'ai_generated',
            FOREIGN KEY (icd_code) REFERENCES icd10am_codes(code),
            FOREIGN KEY (achi_code) REFERENCES achi_codes(code)
        )
    """)
    print("✓ Created table: valid_relationships")
    
    # Create indexes
    print("\nCreating indexes...")
    cursor.execute("CREATE INDEX idx_icd_code ON icd10am_codes(code)")
    cursor.execute("CREATE INDEX idx_icd_desc ON icd10am_codes(description)")
    cursor.execute("CREATE INDEX idx_achi_code ON achi_codes(code)")
    cursor.execute("CREATE INDEX idx_achi_desc ON achi_codes(short_description)")
    cursor.execute("CREATE INDEX idx_category_code ON icd10_main_categories(code)")
    cursor.execute("CREATE INDEX idx_valid_rel_icd ON valid_relationships(icd_code)")
    cursor.execute("CREATE INDEX idx_valid_rel_achi ON valid_relationships(achi_code)")
    cursor.execute("CREATE INDEX idx_valid_rel_icd_cat ON valid_relationships(icd_category)")
    cursor.execute("CREATE INDEX idx_valid_rel_achi_cat ON valid_relationships(achi_category)")
    cursor.execute("CREATE INDEX idx_valid_rel_category ON valid_relationships(category)")
    print("✓ Created all indexes")
    
    conn.commit()
    
    # Import data from Excel files
    print("\n" + "=" * 80)
    print("Importing data from Excel files...")
    print("=" * 80)
    
    # 1. Import ICD10-AM codes
    try:
        icd_file = project_root / 'ICD10-AM.xlsx'
        print(f"\nReading {icd_file}...")
        icd_df = pd.read_excel(icd_file)
        print(f"Columns found: {list(icd_df.columns)}")
        print(f"Rows: {len(icd_df)}")
        
        # Map actual column names: ICDCode → code, ICD_description → description
        icd_df = icd_df.rename(columns={
            'ICDCode': 'code',
            'ICD_description': 'description'
        })
        
        # Insert data
        icd_df[['code', 'description']].to_sql('icd10am_codes', conn, if_exists='append', index=False)
        print(f"✓ Imported {len(icd_df)} ICD-10-AM codes")
    except Exception as e:
        print(f"✗ Error importing ICD10-AM: {e}")
    
    # 2. Import Code Blocks
    try:
        blocks_file = project_root / 'Code_blocks.xlsx'
        print(f"\nReading {blocks_file}...")
        blocks_df = pd.read_excel(blocks_file)
        print(f"Columns found: {list(blocks_df.columns)}")
        print(f"Rows: {len(blocks_df)}")
        
        # Map actual column names: block → block_id, ascii_desc → block_description, ascii_short_desc → block_short_desc
        blocks_df = blocks_df.rename(columns={
            'block': 'block_id',
            'ascii_desc': 'block_description',
            'ascii_short_desc': 'block_short_desc'
        })
        
        # Insert data
        blocks_df[['block_id', 'block_short_desc', 'block_description']].to_sql('code_blocks', conn, if_exists='append', index=False)
        print(f"✓ Imported {len(blocks_df)} code blocks")
    except Exception as e:
        print(f"✗ Error importing Code Blocks: {e}")
    
    # 3. Import ACHI codes
    try:
        achi_file = project_root / 'ACHI_Codes.xlsx'
        print(f"\nReading {achi_file}...")
        achi_df = pd.read_excel(achi_file)
        print(f"Columns found: {list(achi_df.columns)}")
        print(f"Rows: {len(achi_df)}")
        
        # Map actual column names: Code_id → code, Block → block_id, ascii_desc → description, ascii_short_desc → short_description
        achi_df = achi_df.rename(columns={
            'Code_id': 'code',
            'Block': 'block_id',
            'ascii_desc': 'description',
            'ascii_short_desc': 'short_description'
        })
        
        # Insert data
        achi_df[['code', 'description', 'short_description', 'block_id']].to_sql('achi_codes', conn, if_exists='append', index=False)
        print(f"✓ Imported {len(achi_df)} ACHI codes")
    except Exception as e:
        print(f"✗ Error importing ACHI codes: {e}")
    
    # 4. Import ICD10 Main Categories
    try:
        categories_file = project_root / 'ICD10_Main_Categories.xlsx'
        print(f"\nReading {categories_file}...")
        categories_df = pd.read_excel(categories_file)
        print(f"Columns found: {list(categories_df.columns)}")
        print(f"Rows: {len(categories_df)}")
        
        # Map actual column names: Code_head → code, Code_description → description
        categories_df = categories_df.rename(columns={
            'Code_head': 'code',
            'Code_description': 'description'
        })
        
        # Insert data
        categories_df[['code', 'description']].to_sql('icd10_main_categories', conn, if_exists='append', index=False)
        print(f"✓ Imported {len(categories_df)} ICD-10 main categories")
    except Exception as e:
        print(f"✗ Error importing ICD10 Main Categories: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 80)
    print(f"✅ Database created successfully at: {db_path}")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Run: python utils/discover_categories.py (to see all categories)")
    print("2. Run: python utils/generate_sample_relationships.py (to generate samples)")

if __name__ == "__main__":
    create_database()

