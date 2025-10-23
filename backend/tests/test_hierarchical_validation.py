"""
Test script for hierarchical validation system
Tests the new ACHI-10th Edition hierarchical structure integration
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.queries import db_manager
from validators.hierarchical_validator import HierarchicalValidator

def test_database_structure():
    """Test that all new tables exist and have data"""
    print("Testing Database Structure")
    print("=" * 50)
    
    try:
        # Test ACHI main categories
        result = db_manager.conn.execute("SELECT COUNT(*) FROM achi_main_categories").fetchone()
        print(f"+ ACHI Main Categories: {result[0]} records")
        
        # Test ACHI sub categories
        result = db_manager.conn.execute("SELECT COUNT(*) FROM achi_sub_categories").fetchone()
        print(f"+ ACHI Sub Categories: {result[0]} records")
        
        # Test ACHI codes v2
        result = db_manager.conn.execute("SELECT COUNT(*) FROM achi_codes_v2").fetchone()
        print(f"+ ACHI Codes v2: {result[0]} records")
        
        # Test category mapping
        result = db_manager.conn.execute("SELECT COUNT(*) FROM icd_achi_category_mapping").fetchone()
        print(f"+ ICD-ACHI Category Mapping: {result[0]} records")
        
        return True
    except Exception as e:
        print(f"X Database structure test failed: {e}")
        return False

def test_hierarchical_search():
    """Test hierarchical search functionality"""
    print("\nTesting Hierarchical Search")
    print("=" * 50)
    
    try:
        # Test ICD search
        icd_results = db_manager.search_icd_codes("G45", limit=5)
        print(f"+ ICD Search (G45): {len(icd_results)} results")
        for r in icd_results[:2]:
            print(f"  - {r['code']}: {r['description']}")
        
        # Test ACHI v2 search
        achi_results = db_manager.search_achi_codes_v2("39006", limit=5)
        print(f"+ ACHI v2 Search (39006): {len(achi_results)} results")
        for r in achi_results[:2]:
            print(f"  - {r['code']}: {r['description']} [{r['category']}]")
        
        return True
    except Exception as e:
        print(f"X Hierarchical search test failed: {e}")
        return False

def test_hierarchical_context():
    """Test hierarchical context retrieval"""
    print("\nTesting Hierarchical Context")
    print("=" * 50)
    
    try:
        # Test ICD chapter info
        icd_info = db_manager.get_icd_chapter_info("G45.9")
        if icd_info:
            print(f"+ ICD Chapter Info: {icd_info['chapter_code']} - {icd_info['chapter_name']}")
        else:
            print("X No ICD chapter info found")
        
        # Test ACHI hierarchy
        achi_info = db_manager.get_achi_with_hierarchy("39006-00")
        if achi_info:
            print(f"+ ACHI Hierarchy: {achi_info['main_category_name']} / {achi_info['sub_category_name']}")
        else:
            print("X No ACHI hierarchy found")
        
        # Test category mapping
        if icd_info and achi_info:
            mapping = db_manager.get_category_mapping(
                icd_info['chapter_code'], 
                achi_info['main_category_code']
            )
            if mapping:
                print(f"+ Category Mapping: {mapping['icd_chapter_name']} <-> {mapping['achi_main_category_name']}")
            else:
                print("X No category mapping found")
        
        return True
    except Exception as e:
        print(f"X Hierarchical context test failed: {e}")
        return False

def test_validation_cases():
    """Test validation with hierarchical context"""
    print("\nTesting Validation Cases")
    print("=" * 50)
    
    test_cases = [
        # (ICD, ACHI, Expected, Description)
        ("G45.9", "39006-00", True, "TIA + Ventricular puncture (Nervous system)"),
        ("J45.0", "92209-00", True, "Asthma + NIV support (Respiratory)"),
        ("K02.9", "52318-00", True, "Dental caries + Tooth extraction (Dental)"),
        ("K02.9", "92209-00", False, "Dental caries + NIV support (Cross-category)"),
        ("G45.9", "52318-00", False, "TIA + Tooth extraction (Cross-category)"),
    ]
    
    validator = HierarchicalValidator()
    
    for icd, achi, expected, description in test_cases:
        try:
            # Get descriptions
            icd_data = db_manager.get_icd_with_category(icd)
            achi_data = db_manager.get_achi_with_hierarchy(achi)
            
            if not icd_data or not achi_data:
                print(f"✗ {description}: Code not found")
                continue
            
            # Validate
            result = validator.validate_with_hierarchy(
                icd, icd_data['description'],
                achi, achi_data['description']
            )
            
            is_valid, confidence, reasoning = result
            status = "+" if is_valid == expected else "X"
            
            print(f"{status} {description}")
            print(f"    Result: {'VALID' if is_valid else 'INVALID'} (Expected: {'VALID' if expected else 'INVALID'})")
            print(f"    Confidence: {confidence:.1%}")
            print(f"    Reasoning: {reasoning[:100]}...")
            print()
            
        except Exception as e:
            print(f"X {description}: Error - {e}")

def main():
    """Run all tests"""
    print("Hierarchical Validation System Test")
    print("=" * 60)
    
    # Initialize database connection
    try:
        db_manager.connect()
        print("+ Database connected")
    except Exception as e:
        print(f"X Database connection failed: {e}")
        return
    
    # Run tests
    tests = [
        test_database_structure,
        test_hierarchical_search,
        test_hierarchical_context,
        test_validation_cases
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"X Test {test.__name__} failed with exception: {e}")
    
    print(f"\nTest Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("SUCCESS: All tests passed! Hierarchical system is working correctly.")
    else:
        print("WARNING: Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
