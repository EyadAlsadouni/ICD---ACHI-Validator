"""
Database Setup V2 - Enhanced with Hierarchical ACHI Structure
Integrates new ACHI-10th Edition hierarchical data while keeping original tables
"""
import sqlite3
import pandas as pd
import os
from pathlib import Path
from parse_new_achi import parse_achi_10th_edition

def create_database_v2():
    """
    Create enhanced SQLite database with hierarchical ACHI structure
    """
    # Determine paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    data_dir = script_dir.parent / 'data'
    
    # Create data directory if it doesn't exist
    data_dir.mkdir(exist_ok=True)
    
    db_path = data_dir / 'validation.db'
    
    # Backup existing database
    if db_path.exists():
        backup_path = data_dir / 'validation_backup.db'
        if backup_path.exists():
            backup_path.unlink()  # Remove existing backup
        db_path.rename(backup_path)
        print(f"Backed up existing database to {backup_path}")
    
    # Connect to database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("Creating enhanced database schema...")
    print("=" * 80)
    
    # Create original tables (keep existing structure)
    cursor.execute("""
        CREATE TABLE icd10am_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL
        )
    """)
    print("+ Created table: icd10am_codes")
    
    cursor.execute("""
        CREATE TABLE code_blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_id TEXT UNIQUE NOT NULL,
            block_short_desc TEXT,
            block_description TEXT
        )
    """)
    print("+ Created table: code_blocks")
    
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
    print("+ Created table: achi_codes (original)")
    
    cursor.execute("""
        CREATE TABLE icd10_main_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            description TEXT
        )
    """)
    print("+ Created table: icd10_main_categories")
    
    # NEW HIERARCHICAL TABLES
    cursor.execute("""
        CREATE TABLE achi_main_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            full_label TEXT NOT NULL
        )
    """)
    print("+ Created table: achi_main_categories (NEW)")
    
    cursor.execute("""
        CREATE TABLE achi_sub_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            range_start TEXT NOT NULL,
            range_end TEXT NOT NULL,
            name TEXT NOT NULL,
            main_category_code TEXT NOT NULL,
            FOREIGN KEY (main_category_code) REFERENCES achi_main_categories(code)
        )
    """)
    print("+ Created table: achi_sub_categories (NEW)")
    
    cursor.execute("""
        CREATE TABLE achi_codes_v2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL,
            sub_category_id INTEGER,
            main_category_code TEXT,
            FOREIGN KEY (sub_category_id) REFERENCES achi_sub_categories(id),
            FOREIGN KEY (main_category_code) REFERENCES achi_main_categories(code)
        )
    """)
    print("+ Created table: achi_codes_v2 (NEW)")
    
    cursor.execute("""
        CREATE TABLE icd_achi_category_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            icd_chapter TEXT NOT NULL,
            icd_chapter_name TEXT NOT NULL,
            achi_main_category_code TEXT NOT NULL,
            achi_main_category_name TEXT NOT NULL,
            mapping_confidence FLOAT DEFAULT 0.95,
            notes TEXT
        )
    """)
    print("+ Created table: icd_achi_category_mapping (NEW)")
    
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
    print("+ Created table: valid_relationships")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS validation_test_log (
            test_id INTEGER PRIMARY KEY AUTOINCREMENT,
            icd_code TEXT NOT NULL,
            achi_code TEXT NOT NULL,
            ai_decision TEXT NOT NULL,
            ai_confidence_percent REAL NOT NULL,
            ai_reasoning TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            assistant_rating TEXT,
            assistant_notes TEXT,
            UNIQUE(icd_code, achi_code)
        )
    """)
    print("+ Created table: validation_test_log")
    
    # Create indexes
    cursor.execute("CREATE INDEX idx_icd_code ON icd10am_codes(code)")
    cursor.execute("CREATE INDEX idx_achi_code ON achi_codes(code)")
    cursor.execute("CREATE INDEX idx_achi_code_v2 ON achi_codes_v2(code)")
    cursor.execute("CREATE INDEX idx_achi_main_cat ON achi_codes_v2(main_category_code)")
    cursor.execute("CREATE INDEX idx_icd_achi_mapping ON icd_achi_category_mapping(icd_chapter, achi_main_category_code)")
    print("+ Created indexes")
    
    conn.commit()
    print("\n" + "=" * 80)
    print("IMPORTING ORIGINAL DATA...")
    print("=" * 80)
    
    # Import original data
    import_original_data(cursor, project_root)
    
    print("\n" + "=" * 80)
    print("IMPORTING NEW HIERARCHICAL ACHI DATA...")
    print("=" * 80)
    
    # Import new hierarchical ACHI data
    import_hierarchical_achi_data(cursor)
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 80)
    print("DATABASE CREATION COMPLETE!")
    print("=" * 80)
    print(f"Database saved to: {db_path}")
    print("\nTables created:")
    print("  - Original: icd10am_codes, achi_codes, code_blocks, icd10_main_categories")
    print("  - New: achi_main_categories, achi_sub_categories, achi_codes_v2")
    print("  - Mapping: icd_achi_category_mapping")
    print("  - Logging: valid_relationships, validation_test_log")

def import_original_data(cursor, project_root):
    """Import original Excel data"""
    try:
        # ICD10-AM codes
        icd_file = project_root / "ICD10-AM.xlsx"
        if icd_file.exists():
            df_icd = pd.read_excel(icd_file)
            for _, row in df_icd.iterrows():
                cursor.execute("""
                    INSERT OR IGNORE INTO icd10am_codes (code, description)
                    VALUES (?, ?)
                """, (str(row['ICDCode']), str(row['ICD_description'])))
            print(f"+ Imported {len(df_icd)} ICD10-AM codes")
        
        # ACHI codes (original)
        achi_file = project_root / "ACHI_Codes.xlsx"
        if achi_file.exists():
            df_achi = pd.read_excel(achi_file)
            for _, row in df_achi.iterrows():
                cursor.execute("""
                    INSERT OR IGNORE INTO achi_codes (code, description, short_description, block_id)
                    VALUES (?, ?, ?, ?)
                """, (str(row['Code_id']), str(row['ascii_desc']), 
                      str(row['ascii_short_desc']), str(row['Block'])))
            print(f"+ Imported {len(df_achi)} original ACHI codes")
        
        # Code blocks
        blocks_file = project_root / "Code_blocks.xlsx"
        if blocks_file.exists():
            df_blocks = pd.read_excel(blocks_file)
            for _, row in df_blocks.iterrows():
                cursor.execute("""
                    INSERT OR IGNORE INTO code_blocks (block_id, block_short_desc, block_description)
                    VALUES (?, ?, ?)
                """, (str(row['block']), str(row['ascii_short_desc']), 
                      str(row['ascii_desc'])))
            print(f"+ Imported {len(df_blocks)} code blocks")
        
        # ICD main categories
        icd_cat_file = project_root / "ICD10_Main_Categories.xlsx"
        if icd_cat_file.exists():
            df_icd_cat = pd.read_excel(icd_cat_file)
            for _, row in df_icd_cat.iterrows():
                cursor.execute("""
                    INSERT OR IGNORE INTO icd10_main_categories (code, description)
                    VALUES (?, ?)
                """, (str(row['Code_head']), str(row['Code_description'])))
            print(f"+ Imported {len(df_icd_cat)} ICD main categories")
            
    except Exception as e:
        print(f"Error importing original data: {e}")

def import_hierarchical_achi_data(cursor):
    """Import new hierarchical ACHI data"""
    try:
        main_cats, sub_cats, achi_codes = parse_achi_10th_edition()
        
        # Import main categories
        for cat in main_cats:
            cursor.execute("""
                INSERT INTO achi_main_categories (code, name, full_label)
                VALUES (?, ?, ?)
            """, (cat['code'], cat['name'], cat['full_label']))
        print(f"+ Imported {len(main_cats)} main categories")
        
        # Import sub-categories
        for sub in sub_cats:
            cursor.execute("""
                INSERT INTO achi_sub_categories 
                (range_start, range_end, name, main_category_code)
                VALUES (?, ?, ?, ?)
            """, (sub['range_start'], sub['range_end'], sub['name'], sub['main_category_code']))
        print(f"+ Imported {len(sub_cats)} sub-categories")
        
        # Import ACHI codes with hierarchy
        for achi in achi_codes:
            # Find sub_category_id
            if achi['sub_category_range']:
                range_parts = achi['sub_category_range'].split('-')
                sub_id = cursor.execute("""
                    SELECT id FROM achi_sub_categories 
                    WHERE range_start = ? AND range_end = ?
                """, (range_parts[0], range_parts[1])).fetchone()
                sub_category_id = sub_id[0] if sub_id else None
            else:
                sub_category_id = None
            
            cursor.execute("""
                INSERT INTO achi_codes_v2 
                (code, description, sub_category_id, main_category_code)
                VALUES (?, ?, ?, ?)
            """, (achi['code'], achi['description'], 
                  sub_category_id, achi['main_category_code']))
        print(f"+ Imported {len(achi_codes)} ACHI codes with hierarchy")
        
    except Exception as e:
        print(f"Error importing hierarchical ACHI data: {e}")

if __name__ == "__main__":
    create_database_v2()
