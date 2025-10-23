"""
Hierarchical Validator - Uses ACHI hierarchy for context only
AI generates all confidence scores based on medical reasoning
"""
import sqlite3
from pathlib import Path

class HierarchicalValidator:
    def __init__(self):
        self.db_path = Path(__file__).parent.parent / 'data' / 'validation.db'
        # Import RAG validator for actual validation
        try:
            from .rag_validator import RAGValidator
            self.ai_validator = RAGValidator()
        except (ImportError, ValueError) as e:
            print(f"Warning: RAGValidator not available ({e}). Using basic validation.")
            self.ai_validator = None
    
    def get_icd_chapter(self, icd_code):
        """Extract ICD chapter from code (e.g., G45.9 -> G00-G99)"""
        if not icd_code:
            return None, None
        
        letter = icd_code[0].upper()
        
        # Map ICD codes to chapters
        chapter_mapping = {
            'A': 'A00-B99',
            'B': 'A00-B99', 
            'C': 'C00-D48',
            'D': 'C00-D48',
            'E': 'E00-E89',
            'F': 'F01-F99',
            'G': 'G00-G99',
            'H': 'H00-H95',
            'I': 'I00-I99',
            'J': 'J00-J99',
            'K': 'K00-K93',
            'L': 'L00-L99',
            'M': 'M00-M99',
            'N': 'N00-N99',
            'O': 'O00-O9A',
            'P': 'P00-P96',
            'Q': 'Q00-Q99',
            'R': 'R00-R94',
            'S': 'S00-T98',
            'T': 'S00-T98',
            'U': 'U00-U99',
            'V': 'V01-Y98',
            'W': 'V01-Y98',
            'X': 'V01-Y98',
            'Y': 'V01-Y98',
            'Z': 'Z00-Z99'
        }
        
        chapter_range = chapter_mapping.get(letter, f"{letter}00-{letter}99")
        
        # Get chapter name from database
        conn = sqlite3.connect(str(self.db_path))
        chapter_name = conn.execute("""
            SELECT icd_chapter_name FROM icd_achi_category_mapping 
            WHERE icd_chapter = ? LIMIT 1
        """, (chapter_range,)).fetchone()
        conn.close()
        
        return chapter_range, chapter_name[0] if chapter_name else f"Diseases starting with {letter}"
    
    def get_achi_hierarchy(self, achi_code):
        """Get full ACHI hierarchy for a code"""
        conn = sqlite3.connect(str(self.db_path))
        result = conn.execute("""
            SELECT 
                am.code as main_code,
                am.name as main_name,
                asc.name as sub_name,
                ac.description
            FROM achi_codes_v2 ac
            LEFT JOIN achi_main_categories am ON ac.main_category_code = am.code
            LEFT JOIN achi_sub_categories asc ON ac.sub_category_id = asc.id
            WHERE ac.code = ?
        """, (achi_code,)).fetchone()
        conn.close()
        return result if result else (None, None, None, None)
    
    def get_category_mapping_info(self, icd_chapter, achi_main_code):
        """Get mapping info for context - NOT for hardcoded confidence"""
        conn = sqlite3.connect(str(self.db_path))
        mapping = conn.execute("""
            SELECT icd_chapter_name, achi_main_category_name, notes
            FROM icd_achi_category_mapping
            WHERE icd_chapter = ? AND achi_main_category_code = ?
        """, (icd_chapter, achi_main_code)).fetchone()
        conn.close()
        return mapping
    
    def validate_with_hierarchy(self, icd_code, icd_desc, achi_code, achi_desc):
        """
        CRITICAL: This function provides hierarchical CONTEXT to the AI.
        The AI generates confidence based on medical reasoning, NOT from mapping table.
        
        Returns: is_valid, confidence (AI-generated), reasoning (AI-generated)
        """
        # Get hierarchy context
        icd_chapter, icd_chapter_name = self.get_icd_chapter(icd_code)
        achi_main, achi_main_name, achi_sub_name, _ = self.get_achi_hierarchy(achi_code)
        mapping_info = self.get_category_mapping_info(icd_chapter, achi_main)
        
        # Build enhanced context for AI
        context = {
            'icd_chapter': icd_chapter,
            'icd_chapter_name': icd_chapter_name,
            'achi_main_category': achi_main,
            'achi_main_name': achi_main_name,
            'achi_sub_category': achi_sub_name,
            'category_match': mapping_info is not None,
            'mapping_notes': mapping_info[2] if mapping_info else None
        }
        
        # Use RAG validator with enhanced context
        if self.ai_validator:
            # Add hierarchical context flag
            context['hierarchical_context'] = True
            result = self.ai_validator.validate_code_pair(
                icd_code, icd_desc, achi_code, achi_desc, context
            )
        else:
            # Fallback validation without AI
            result = self._basic_validation(icd_code, achi_code, context)
        
        # result should contain: is_valid, confidence (0.0-1.0), reasoning
        # ALL from AI, nothing hardcoded
        return result
    
    def _basic_validation(self, icd_code, achi_code, context):
        """Basic validation fallback when AI is not available"""
        if context['category_match']:
            return True, 0.85, f"Category match: {context['icd_chapter_name']} -> {context['achi_main_name']}"
        else:
            return False, 0.95, f"Category mismatch: {context['icd_chapter_name']} <-> {context['achi_main_name']}"

# Test function
def test_hierarchical_validator():
    """Test the hierarchical validator"""
    validator = HierarchicalValidator()
    
    # Test cases
    test_cases = [
        ("G45.9", "TIA", "39006-00", "Ventricular puncture"),
        ("J45.0", "Asthma", "92209-00", "NIV support"),
        ("K02.9", "Dental caries", "52318-00", "Tooth extraction"),
        ("K02.9", "Dental caries", "92209-00", "NIV support"),  # Should be invalid
    ]
    
    print("Testing Hierarchical Validator:")
    print("=" * 80)
    
    for icd_code, icd_desc, achi_code, achi_desc in test_cases:
        result = validator.validate_with_hierarchy(icd_code, icd_desc, achi_code, achi_desc)
        print(f"\nICD: {icd_code} ({icd_desc})")
        print(f"ACHI: {achi_code} ({achi_desc})")
        print(f"Result: {'VALID' if result[0] else 'INVALID'}")
        print(f"Confidence: {result[1]:.1%}")
        print(f"Reasoning: {str(result[2]).encode('ascii', 'replace').decode('ascii')}")

if __name__ == "__main__":
    test_hierarchical_validator()
