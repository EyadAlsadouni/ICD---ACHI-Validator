"""
Fix Valid_Relationships.xlsx with REAL AI-generated relationships and confidence scores
"""
import pandas as pd
from pathlib import Path
import os
from openai import OpenAI
import json
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def validate_pair_with_ai(icd_code, icd_desc, achi_code, achi_desc, category):
    """
    Use GPT-4.1 Mini to generate REAL relationship and confidence
    """
    prompt = f"""You are an expert clinical coding specialist for Australian medical codes.

Analyze this ICD-ACHI pairing and provide a SPECIFIC, DETAILED explanation of their relationship:

ICD-10-AM: {icd_code} - {icd_desc}
ACHI: {achi_code} - {achi_desc}
Category: {category}

INSTRUCTIONS:
1. If this is a VALID pairing:
   - Explain SPECIFICALLY why this procedure is appropriate for this diagnosis
   - Mention the clinical indication
   - Use medical terminology
   - Be specific about HOW the procedure treats/addresses the condition

2. If this is INVALID or QUESTIONABLE:
   - Explain why this combination doesn't make clinical sense
   - Mention what procedure WOULD be appropriate instead
   - Be honest about the mismatch

3. Provide HONEST confidence:
   - 0.90-1.0: Clear, direct clinical relationship
   - 0.75-0.89: Generally appropriate, may have exceptions
   - 0.50-0.74: Questionable, context-dependent
   - Below 0.50: Likely inappropriate or unrelated

Respond with JSON only:
{{
    "is_valid": true/false,
    "relationship": "Detailed clinical explanation of relationship (2-3 sentences)",
    "confidence": 0.0-1.0
}}"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        print(f"  ✗ API Error: {e}")
        return {
            'is_valid': False,
            'relationship': f'Error validating: {str(e)}',
            'confidence': 0.0
        }

def fix_relationships():
    """
    Fix the Valid_Relationships.xlsx file with real AI-generated content
    """
    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    input_file = project_root / 'Valid_Relationships.xlsx'
    output_file = project_root / 'Valid_Relationships_Fixed.xlsx'
    
    print("=" * 80)
    print("FIXING VALID_RELATIONSHIPS.XLSX")
    print("=" * 80)
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    
    # Read the file
    df = pd.read_excel(input_file)
    print(f"\nTotal relationships to fix: {len(df)}")
    
    # Estimate cost and time
    estimated_cost = len(df) * 0.0007
    estimated_time_minutes = (len(df) * 2) / 60
    
    print(f"Estimated cost: ${estimated_cost:.2f}")
    print(f"Estimated time: {estimated_time_minutes:.1f} minutes")
    print("\nStarting in 3 seconds...")
    time.sleep(3)
    
    # Process each row
    fixed_count = 0
    invalid_count = 0
    
    for idx, row in df.iterrows():
        print(f"\n[{idx+1}/{len(df)}] Processing: {row['ICD_Code']} + {row['ACHI_Code']}")
        
        # Get AI validation
        result = validate_pair_with_ai(
            row['ICD_Code'],
            row['ICD_Description'],
            row['ACHI_Code'],
            row['ACHI_Description'],
            row['Relation_Category']
        )
        
        # Update the row
        df.at[idx, 'Relationship'] = result['relationship']
        df.at[idx, 'Confidence_Percent'] = int(result['confidence'] * 100)
        
        if result['is_valid']:
            print(f"  ✓ Valid (confidence: {result['confidence']:.2f})")
            fixed_count += 1
        else:
            print(f"  ✗ Invalid (confidence: {result['confidence']:.2f})")
            invalid_count += 1
        
        # Save progress every 50 rows
        if (idx + 1) % 50 == 0:
            df.to_excel(output_file, index=False)
            print(f"\n📊 Progress saved! ({idx+1}/{len(df)} completed)")
        
        # Small delay to avoid rate limiting
        time.sleep(0.1)
    
    # Final save
    df.to_excel(output_file, index=False)
    
    print("\n" + "=" * 80)
    print("✅ FIXING COMPLETE!")
    print("=" * 80)
    print(f"Fixed relationships saved to: {output_file}")
    print(f"\nStatistics:")
    print(f"  Total processed: {len(df)}")
    print(f"  Valid: {fixed_count}")
    print(f"  Invalid/Questionable: {invalid_count}")
    print(f"\nUnique relationships: {df['Relationship'].nunique()}")
    print(f"Unique confidences: {df['Confidence_Percent'].nunique()}")
    print(f"\nConfidence distribution:")
    print(df['Confidence_Percent'].describe())
    
    print(f"\n💡 Next step: Import this fixed file into the database:")
    print(f"   python utils/import_relationships_to_db.py")

if __name__ == "__main__":
    fix_relationships()


