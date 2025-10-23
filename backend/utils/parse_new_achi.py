"""
Parse ACHI - 10th Edition.xlsx Sheet 3 into structured data
Extracts 3-level hierarchy: Main Categories → Sub-Categories → ACHI Codes
"""
import pandas as pd
import re
from pathlib import Path

def parse_achi_10th_edition():
    """
    Parse ACHI - 10th Edition.xlsx Sheet 3 into structured data
    Returns: main_categories, sub_categories, achi_codes
    """
    file_path = Path(__file__).parent.parent.parent / "ACHI - 10th Edition.xlsx"
    df = pd.read_excel(file_path, sheet_name="Procedure Counts Summary", skiprows=4)
    
    # Rename columns
    df.columns = ['row_label', 'procedure_count']
    
    main_categories = []
    sub_categories = []
    achi_codes = []
    
    current_main_cat = None
    current_sub_cat = None
    
    for idx, row in df.iterrows():
        label = str(row['row_label']).strip()
        
        # Skip empty rows or header rows
        if not label or label == 'nan' or 'Row Labels' in label:
            continue
        
        # Main Category: "01 Procedures on nervous system"
        if re.match(r'^\d{2}\s+[A-Z]', label):
            main_cat_code = label[:2]
            main_cat_name = label[3:].strip()
            current_main_cat = {
                'code': main_cat_code,
                'name': main_cat_name,
                'full_label': label
            }
            main_categories.append(current_main_cat)
            current_sub_cat = None
            print(f"Found main category: {main_cat_code} - {main_cat_name}")
        
        # Sub-Category: "0001-0028 Skull, Meninges and Brain"
        elif re.match(r'^\d{4}-\d{4}\s+', label):
            range_match = re.match(r'^(\d{4})-(\d{4})\s+(.+)', label)
            if range_match:
                sub_cat_start = range_match.group(1)
                sub_cat_end = range_match.group(2)
                sub_cat_name = range_match.group(3).strip()
                current_sub_cat = {
                    'range_start': sub_cat_start,
                    'range_end': sub_cat_end,
                    'name': sub_cat_name,
                    'main_category_code': current_main_cat['code'] if current_main_cat else None,
                    'main_category_name': current_main_cat['name'] if current_main_cat else None
                }
                sub_categories.append(current_sub_cat)
                print(f"  Found sub-category: {sub_cat_start}-{sub_cat_end} - {sub_cat_name}")
        
        # ACHI Code: "40803-00 Intracranial stereotactic localisation"
        elif re.match(r'^\d{5}-\d{2}\s+', label):
            code_match = re.match(r'^(\d{5}-\d{2})\s+(.+)', label)
            if code_match:
                achi_code = code_match.group(1)
                achi_desc = code_match.group(2).strip()
                achi_codes.append({
                    'code': achi_code,
                    'description': achi_desc,
                    'sub_category_range': f"{current_sub_cat['range_start']}-{current_sub_cat['range_end']}" if current_sub_cat else None,
                    'sub_category_name': current_sub_cat['name'] if current_sub_cat else None,
                    'main_category_code': current_main_cat['code'] if current_main_cat else None,
                    'main_category_name': current_main_cat['name'] if current_main_cat else None
                })
                if len(achi_codes) % 500 == 0:  # Progress indicator
                    print(f"    Processed {len(achi_codes)} ACHI codes...")
    
    print(f"\nParsing complete:")
    print(f"  Main Categories: {len(main_categories)}")
    print(f"  Sub-Categories: {len(sub_categories)}")
    print(f"  ACHI Codes: {len(achi_codes)}")
    
    return main_categories, sub_categories, achi_codes

def test_parse():
    """Test the parsing function"""
    try:
        main_cats, sub_cats, achi_codes = parse_achi_10th_edition()
        
        print("\n" + "="*80)
        print("SAMPLE MAIN CATEGORIES:")
        print("="*80)
        for cat in main_cats[:5]:
            print(f"{cat['code']}: {cat['name']}")
        
        print("\n" + "="*80)
        print("SAMPLE SUB-CATEGORIES:")
        print("="*80)
        for sub in sub_cats[:5]:
            print(f"{sub['range_start']}-{sub['range_end']}: {sub['name']}")
        
        print("\n" + "="*80)
        print("SAMPLE ACHI CODES:")
        print("="*80)
        for achi in achi_codes[:10]:
            print(f"{achi['code']}: {achi['description']}")
            print(f"  Category: {achi['main_category_name']}")
            print(f"  Sub-Category: {achi['sub_category_name']}")
            print()
        
        return True
    except Exception as e:
        print(f"Error during parsing: {e}")
        return False

if __name__ == "__main__":
    test_parse()
