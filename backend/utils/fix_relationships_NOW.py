"""
Fix ALL relationships using medical knowledge
"""
import pandas as pd
from pathlib import Path

def evaluate_relationship(icd_code, icd_desc, achi_code, achi_desc, category):
    """
    Use medical knowledge to evaluate if relationship is valid and assign confidence
    """
    icd_lower = icd_desc.lower()
    achi_lower = achi_desc.lower()
    
    # RULE 1: Vaccination relationships
    if 'vacc' in achi_lower:
        # Extract vaccine type
        if 'cholera' in achi_lower and 'cholera' in icd_lower:
            return True, "Cholera vaccination is the primary prevention method for cholera infection.", 90
        elif 'measles' in achi_lower and 'measles' in icd_lower:
            return True, "Measles vaccination prevents measles infection.", 90
        elif 'rabies' in achi_lower and 'rabies' in icd_lower:
            return True, "Rabies vaccination prevents rabies infection.", 90
        elif 'yellow fever' in achi_lower and ('yellow fever' in icd_lower or 'dengue' in icd_lower):
            # Dengue and yellow fever are related (both flaviviruses)
            if 'dengue' in icd_lower:
                return True, "Yellow fever vaccine may provide cross-protection against dengue (both flaviviruses).", 60
            return True, "Yellow fever vaccination prevents yellow fever infection.", 90
        elif 'varicella' in achi_lower and ('zoster' in icd_lower or 'varicella' in icd_lower):
            return True, "Varicella-zoster immunoglobulin treats or prevents varicella-zoster infections.", 92
        elif 'q fever' in achi_lower and 'q fever' in icd_lower:
            return True, "Q fever vaccination prevents Q fever infection.", 90
        else:
            # Wrong vaccine for the disease
            return False, f"Vaccination mismatch: {achi_desc} is not indicated for {icd_desc}. Different pathogens require specific vaccines.", 25
    
    # RULE 2: CNS investigations for CNS infections
    if 'cns' in achi_lower and 'evoked' in achi_lower:
        if 'cns' in icd_lower or 'central nervous' in icd_lower or 'brain' in icd_lower or 'enceph' in icd_lower:
            return True, "CNS evoked response studies assess neurological function in CNS infections/disorders.", 85
        else:
            return False, "CNS evoked response studies are for neurological conditions, not appropriate for this diagnosis.", 30
    
    # RULE 3: Caesarean section
    if 'caesarean' in achi_lower or 'cesarean' in achi_lower:
        if 'pregn' in icd_lower or 'deliver' in icd_lower or 'labor' in icd_lower or 'fetal' in icd_lower or 'obstet' in icd_lower:
            return True, "Caesarean section is a surgical delivery method for complicated pregnancies.", 88
        else:
            # Completely unrelated diagnosis
            return False, f"Caesarean section is for obstetric conditions only. Not clinically related to {icd_desc}.", 15
    
    # RULE 4: Surgical drainage for infections
    if 'drain' in achi_lower:
        if 'abscess' in icd_lower or 'infect' in icd_lower or 'pus' in icd_lower:
            return True, "Drainage is indicated for abscesses and infected fluid collections.", 87
        elif 'hydroceph' in icd_lower or 'fluid' in icd_lower:
            return True, "Drainage procedures manage fluid accumulation in body cavities.", 85
        else:
            return False, "Drainage procedure not typically indicated for this condition without fluid accumulation.", 40
    
    # RULE 5: Imaging services
    if 'imaging' in category.lower() or 'image' in achi_lower or 'radiograph' in achi_lower:
        # Imaging is broadly applicable for diagnosis
        return True, "Imaging services aid in diagnosis and monitoring of various medical conditions.", 70
    
    # RULE 6: Exercise/respiratory tests
    if 'exercise' in achi_lower or 'respiratory' in achi_lower:
        if 'respiratory' in icd_lower or 'lung' in icd_lower or 'asthma' in icd_lower or 'copd' in icd_lower:
            return True, "Exercise/respiratory testing assesses respiratory function in lung diseases.", 85
        else:
            return False, "Exercise/respiratory tests are for respiratory conditions, not appropriate here.", 35
    
    # RULE 7: Debridement
    if 'debride' in achi_lower:
        if 'wound' in icd_lower or 'ulcer' in icd_lower or 'gangrene' in icd_lower or 'necros' in icd_lower:
            return True, "Debridement removes dead/infected tissue from wounds or ulcers.", 88
        elif 'vascular' in icd_lower or 'ischemia' in icd_lower:
            return True, "Debridement treats tissue damage from vascular insufficiency.", 82
        else:
            return False, "Debridement is for wound/tissue damage, not indicated for this condition.", 40
    
    # RULE 8: Excision/surgery
    if 'excision' in achi_lower or 'removal' in achi_lower:
        # Check if body regions match
        if 'skull' in achi_lower and 'head' in icd_lower or 'skull' in icd_lower:
            return True, "Skull excision procedures treat skull lesions/abnormalities.", 85
        elif 'lesion' in achi_lower:
            if 'lesion' in icd_lower or 'tumor' in icd_lower or 'neoplasm' in icd_lower:
                return True, "Excision of lesions is standard treatment for various growths.", 85
            else:
                return False, "Lesion excision not indicated without a lesion diagnosis.", 30
        else:
            # Generic surgical relationship
            return True, "Surgical excision may be indicated for this condition depending on clinical context.", 55
    
    # RULE 9: Male/Female genital procedures
    if 'male genital' in achi_lower:
        if 'male' in icd_lower or 'prostat' in icd_lower or 'testis' in icd_lower or 'penis' in icd_lower:
            return True, "Male genital procedures treat male reproductive system conditions.", 80
        else:
            return False, "Male genital procedures only applicable to male reproductive conditions.", 20
    
    if 'female genital' in achi_lower:
        if 'female' in icd_lower or 'uter' in icd_lower or 'ovar' in icd_lower or 'vagin' in icd_lower:
            return True, "Female genital procedures treat female reproductive system conditions.", 80
        else:
            return False, "Female genital procedures only applicable to female reproductive conditions.", 20
    
    # RULE 10: Radiation treatment
    if 'radiation' in achi_lower:
        if 'cancer' in icd_lower or 'carcinoma' in icd_lower or 'tumor' in icd_lower or 'neoplasm' in icd_lower or 'malignan' in icd_lower:
            return True, "Radiation therapy treats malignant tumors.", 88
        else:
            return False, "Radiation therapy primarily for cancer treatment, not indicated here.", 25
    
    # RULE 11: Osteomyelitis procedures
    if 'osteomyelitis' in achi_lower:
        if 'osteomyelitis' in icd_lower or 'bone infection' in icd_lower:
            return True, "Specific procedures treat osteomyelitis (bone infection).", 90
        else:
            return False, "Osteomyelitis procedures only for bone infections.", 30
    
    # RULE 12: Revision procedures
    if 'revision' in achi_lower or 'repair' in achi_lower:
        # Check for complications or follow-up conditions
        if 'complication' in icd_lower or 'disorder' in icd_lower or 'disease' in icd_lower:
            return True, "Revision/repair procedures address complications or structural issues.", 75
        else:
            return True, "Revision/repair procedures may be clinically appropriate depending on specific condition.", 60
    
    # RULE 13: Manipulation/reconstruction
    if 'manipulat' in achi_lower or 'reconstruct' in achi_lower:
        # Check for musculoskeletal conditions
        if 'talus' in achi_lower or 'foot' in achi_lower or 'ankle' in achi_lower:
            if 'foot' in icd_lower or 'ankle' in icd_lower or 'talus' in icd_lower or 'orthoped' in icd_lower:
                return True, "Manipulation/reconstruction procedures treat foot/ankle structural problems.", 85
            else:
                return False, "Foot/ankle procedures not indicated for non-orthopedic conditions.", 30
        else:
            return True, "Manipulation/reconstruction may be indicated for structural abnormalities.", 65
    
    # RULE 14: Incision procedures
    if 'incision' in achi_lower:
        if 'fascia' in achi_lower:
            if 'musculoskeletal' in icd_lower or 'muscle' in icd_lower or 'fascia' in icd_lower:
                return True, "Fascial incision releases pressure or accesses deeper structures.", 80
            else:
                return False, "Fascial incision not indicated for non-musculoskeletal conditions.", 35
        else:
            return True, "Incision procedures may be part of surgical treatment.", 60
    
    # RULE 15: Eye procedures
    if 'conjunctiv' in achi_lower or 'eye' in achi_lower:
        if 'eye' in icd_lower or 'conjunctiv' in icd_lower or 'ocular' in icd_lower or 'ophthalm' in icd_lower:
            return True, "Eye/conjunctival procedures treat eye conditions.", 85
        else:
            return False, "Eye procedures only for ophthalmologic conditions.", 25
    
    # DEFAULT: Unknown relationship
    return True, "Relationship between diagnosis and procedure requires clinical context and judgment.", 50


# Main execution
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
input_file = project_root / 'Valid_Relationships.xlsx'
output_file = project_root / 'Valid_Relationships_FIXED.xlsx'

print("=" * 80)
print("FIXING VALID_RELATIONSHIPS.XLSX WITH MEDICAL KNOWLEDGE")
print("=" * 80)

# Read file
df = pd.read_excel(input_file)
print(f"\nProcessing {len(df)} relationships...")

# Fix each relationship
fixed_count = 0
invalid_count = 0

for idx, row in df.iterrows():
    is_valid, relationship, confidence = evaluate_relationship(
        row['ICD_Code'],
        row['ICD_Description'],
        row['ACHI_Code'],
        row['ACHI_Description'],
        row['Relation_Category']
    )
    
    # Update row
    df.at[idx, 'Relationship'] = relationship
    df.at[idx, 'Confidence_Percent'] = confidence
    
    if is_valid:
        fixed_count += 1
    else:
        invalid_count += 1
    
    if (idx + 1) % 100 == 0:
        print(f"  Processed {idx + 1}/{len(df)}...")

# Save fixed file
df.to_excel(output_file, index=False)

print(f"\n" + "=" * 80)
print("FIXED!")
print("=" * 80)
print(f"Output: {output_file}")
print(f"\nResults:")
print(f"  Valid relationships: {fixed_count}")
print(f"  Invalid/questionable: {invalid_count}")
print(f"  Unique relationships: {df['Relationship'].nunique()}")
print(f"  Unique confidence values: {df['Confidence_Percent'].nunique()}")
print(f"\nConfidence distribution:")
print(df['Confidence_Percent'].describe())


