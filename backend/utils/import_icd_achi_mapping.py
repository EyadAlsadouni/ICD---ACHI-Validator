"""
Import ICD-ACHI Category Mapping into database
"""
import sqlite3
import json
from pathlib import Path

def import_category_mapping():
    """Import ICD-ACHI category mappings into database"""
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / 'data'
    db_path = data_dir / 'validation.db'
    mapping_file = data_dir / 'icd_achi_mapping.json'
    
    if not mapping_file.exists():
        print(f"Error: Mapping file not found at {mapping_file}")
        return False
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Clear existing mappings
        cursor.execute("DELETE FROM icd_achi_category_mapping")
        print("Cleared existing mappings")
        
        # Load mapping data
        with open(mapping_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        imported_count = 0
        
        for mapping in data['mappings']:
            icd_chapter = mapping['icd_chapter']
            icd_chapter_name = mapping['icd_chapter_name']
            confidence = mapping.get('confidence', 0.95)
            examples = mapping.get('examples', [])
            
            # Handle multiple ACHI categories
            achi_categories = mapping['achi_main_categories']
            achi_names = mapping['achi_names']
            
            for achi_code, achi_name in zip(achi_categories, achi_names):
                cursor.execute("""
                    INSERT INTO icd_achi_category_mapping
                    (icd_chapter, icd_chapter_name, achi_main_category_code, 
                     achi_main_category_name, mapping_confidence, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (icd_chapter, icd_chapter_name, achi_code, achi_name, 
                      confidence, json.dumps(examples)))
                imported_count += 1
        
        conn.commit()
        print(f"Successfully imported {imported_count} category mappings")
        
        # Verify import
        cursor.execute("SELECT COUNT(*) FROM icd_achi_category_mapping")
        count = cursor.fetchone()[0]
        print(f"Total mappings in database: {count}")
        
        # Show sample mappings
        print("\nSample mappings:")
        cursor.execute("""
            SELECT icd_chapter, icd_chapter_name, achi_main_category_code, achi_main_category_name
            FROM icd_achi_category_mapping
            ORDER BY icd_chapter
            LIMIT 10
        """)
        
        for row in cursor.fetchall():
            print(f"  {row[0]} ({row[1]}) -> {row[2]} ({row[3]})")
        
        return True
        
    except Exception as e:
        print(f"Error importing mappings: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = import_category_mapping()
    if success:
        print("\nCategory mapping import completed successfully!")
    else:
        print("\nCategory mapping import failed!")
