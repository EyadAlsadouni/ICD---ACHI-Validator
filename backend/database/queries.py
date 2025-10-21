"""
Database Query Functions
Handles all database interactions for the validation system
"""
import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Optional

class DatabaseManager:
    def __init__(self, db_path: str = None):
        """
        Initialize database connection
        """
        if db_path is None:
            # Try both paths (running from backend/ or from root)
            script_dir = Path(__file__).parent
            db_path1 = script_dir.parent / 'data' / 'validation.db'
            db_path2 = Path('backend/data/validation.db')
            
            if db_path1.exists():
                db_path = str(db_path1)
            elif db_path2.exists():
                db_path = str(db_path2)
            else:
                db_path = str(db_path1)  # Use default path for error message
        
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """Establish database connection"""
        if not Path(self.db_path).exists():
            raise FileNotFoundError(f"Database not found at {self.db_path}. Run database_setup.py first.")
        
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def get_icd_with_category(self, icd_code: str) -> Optional[Dict]:
        """
        Get ICD code with its category from database
        """
        if not self.conn:
            self.connect()
        
        cursor = self.conn.execute("""
            SELECT 
                i.code,
                i.description,
                c.description as category
            FROM icd10am_codes i
            LEFT JOIN icd10_main_categories c 
                ON c.code LIKE substr(i.code, 1, 3) || '%'
            WHERE i.code = ?
            LIMIT 1
        """, (icd_code,))
        
        row = cursor.fetchone()
        if row:
            return {
                'code': row['code'],
                'description': row['description'],
                'category': row['category'] or 'Unknown'
            }
        return None
    
    def get_achi_with_category(self, achi_code: str) -> Optional[Dict]:
        """
        Get ACHI code with its block category
        """
        if not self.conn:
            self.connect()
        
        cursor = self.conn.execute("""
            SELECT 
                a.code,
                a.description,
                a.short_description,
                b.block_short_desc as category,
                b.block_description
            FROM achi_codes a
            LEFT JOIN code_blocks b ON a.block_id = b.block_id
            WHERE a.code = ?
            LIMIT 1
        """, (achi_code,))
        
        row = cursor.fetchone()
        if row:
            return {
                'code': row['code'],
                'description': row['description'],
                'short_description': row['short_description'],
                'category': row['category'] or 'Unknown',
                'block_description': row['block_description']
            }
        return None
    
    def get_exact_match(self, icd_code: str, achi_code: str) -> Optional[Dict]:
        """
        Check if exact relationship exists in database
        """
        if not self.conn:
            self.connect()
        
        cursor = self.conn.execute("""
            SELECT * FROM valid_relationships
            WHERE icd_code = ? AND achi_code = ?
        """, (icd_code, achi_code))
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def get_similar_examples(self, icd_category: str, achi_category: str, limit: int = 5) -> List[Dict]:
        """
        Get similar validated examples from same categories
        """
        if not self.conn:
            self.connect()
        
        cursor = self.conn.execute("""
            SELECT * FROM valid_relationships
            WHERE icd_category = ? AND achi_category = ?
            ORDER BY confidence DESC
            LIMIT ?
        """, (icd_category, achi_category, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def search_icd_codes(self, query_str: str, limit: int = 20) -> List[Dict]:
        """
        Search ICD codes for autocomplete
        """
        if not self.conn:
            self.connect()
        
        query_pattern = f"%{query_str}%"
        
        cursor = self.conn.execute("""
            SELECT code, description FROM icd10am_codes
            WHERE code LIKE ? OR description LIKE ?
            ORDER BY code
            LIMIT ?
        """, (query_pattern, query_pattern, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def search_achi_codes(self, query_str: str, limit: int = 20) -> List[Dict]:
        """
        Search ACHI codes for autocomplete
        """
        if not self.conn:
            self.connect()
        
        query_pattern = f"%{query_str}%"
        
        cursor = self.conn.execute("""
            SELECT 
                a.code,
                a.short_description as description,
                b.block_short_desc as category
            FROM achi_codes a
            LEFT JOIN code_blocks b ON a.block_id = b.block_id
            WHERE a.code LIKE ? 
               OR a.description LIKE ? 
               OR a.short_description LIKE ?
            ORDER BY a.code
            LIMIT ?
        """, (query_pattern, query_pattern, query_pattern, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def save_user_confirmed_relationship(self, icd_code: str, achi_code: str, 
                                        relationship: str, confidence: float, 
                                        icd_category: str, achi_category: str):
        """
        Save user-confirmed validation to database for continuous learning
        """
        if not self.conn:
            self.connect()
        
        # Get full code details
        icd_data = self.get_icd_with_category(icd_code)
        achi_data = self.get_achi_with_category(achi_code)
        
        if not icd_data or not achi_data:
            return False
        
        # Insert if not exists
        self.conn.execute("""
            INSERT OR IGNORE INTO valid_relationships 
            (icd_code, icd_description, icd_category, achi_code, achi_description, 
             achi_category, relationship, confidence, category, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'user_confirmed')
        """, (
            icd_code,
            icd_data['description'],
            icd_category,
            achi_code,
            achi_data['short_description'],
            achi_category,
            relationship,
            confidence,
            f"{icd_category}|{achi_category}"
        ))
        
        self.conn.commit()
        return True

# Global database manager instance
db_manager = DatabaseManager()

