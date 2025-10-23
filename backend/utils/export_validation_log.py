"""
Export validation_test_log table to Excel
Extracts all test results for analysis
"""
import sqlite3
import pandas as pd
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def export_validation_log():
    """Export validation_test_log table to Excel"""
    
    # Database path
    db_path = Path(__file__).parent.parent / 'data' / 'validation.db'
    
    if not db_path.exists():
        print(f"Database not found at: {db_path}")
        return None
    
    # Connect to database
    conn = sqlite3.connect(str(db_path))
    
    try:
        # Get all validation test results
        query = """
        SELECT 
            test_id,
            icd_code,
            achi_code,
            ai_decision,
            ai_confidence_percent,
            ai_reasoning,
            timestamp,
            assistant_rating,
            assistant_notes
        FROM validation_test_log
        ORDER BY test_id
        """
        
        df = pd.read_sql_query(query, conn)
        
        print(f"Found {len(df)} test results in database")
        
        # Create Excel file
        output_path = Path(__file__).parent.parent.parent / 'validation_test_log_export.xlsx'
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Main results sheet
            df.to_excel(writer, sheet_name='All Results', index=False)
            
            # Summary statistics
            summary_data = {
                'Metric': [
                    'Total Tests',
                    'AI Valid Decisions',
                    'AI Invalid Decisions',
                    'Average Confidence (%)',
                    'Min Confidence (%)',
                    'Max Confidence (%)',
                    'Tests with Assistant Rating',
                    'Tests without Assistant Rating'
                ],
                'Value': [
                    len(df),
                    len(df[df['ai_decision'] == 'Valid']),
                    len(df[df['ai_decision'] == 'Invalid']),
                    round(df['ai_confidence_percent'].mean(), 2),
                    round(df['ai_confidence_percent'].min(), 2),
                    round(df['ai_confidence_percent'].max(), 2),
                    len(df[df['assistant_rating'].notna()]),
                    len(df[df['assistant_rating'].isna()])
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Valid decisions only
            valid_df = df[df['ai_decision'] == 'Valid']
            if len(valid_df) > 0:
                valid_df.to_excel(writer, sheet_name='Valid Decisions', index=False)
            
            # Invalid decisions only
            invalid_df = df[df['ai_decision'] == 'Invalid']
            if len(invalid_df) > 0:
                invalid_df.to_excel(writer, sheet_name='Invalid Decisions', index=False)
            
            # High confidence decisions (>90%)
            high_conf_df = df[df['ai_confidence_percent'] > 90]
            if len(high_conf_df) > 0:
                high_conf_df.to_excel(writer, sheet_name='High Confidence', index=False)
            
            # Low confidence decisions (<70%)
            low_conf_df = df[df['ai_confidence_percent'] < 70]
            if len(low_conf_df) > 0:
                low_conf_df.to_excel(writer, sheet_name='Low Confidence', index=False)
        
        print(f"Excel file exported to: {output_path}")
        
        # Print summary
        print("\nExport Summary:")
        print(f"Total tests: {len(df)}")
        print(f"Valid decisions: {len(df[df['ai_decision'] == 'Valid'])}")
        print(f"Invalid decisions: {len(df[df['ai_decision'] == 'Invalid'])}")
        print(f"Average confidence: {df['ai_confidence_percent'].mean():.1f}%")
        print(f"Confidence range: {df['ai_confidence_percent'].min():.1f}% - {df['ai_confidence_percent'].max():.1f}%")
        
        return output_path
        
    except Exception as e:
        print(f"Error exporting data: {e}")
        return None
    
    finally:
        conn.close()

def main():
    """Export validation log to Excel"""
    print("Exporting Validation Test Log to Excel")
    print("=" * 50)
    
    result = export_validation_log()
    
    if result:
        print(f"\nSUCCESS: Validation log exported to Excel")
        print(f"File location: {result}")
        print("\nThe Excel file contains:")
        print("- All Results: Complete test log")
        print("- Summary: Statistics and metrics")
        print("- Valid Decisions: Only valid AI decisions")
        print("- Invalid Decisions: Only invalid AI decisions")
        print("- High Confidence: Decisions with >90% confidence")
        print("- Low Confidence: Decisions with <70% confidence")
    else:
        print("FAILED: Could not export validation log")

if __name__ == "__main__":
    main()
