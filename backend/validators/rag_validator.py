"""
RAG-Enhanced AI Validator
Uses Retrieval-Augmented Generation with GPT-4.1 Mini for validation
"""
import json
import os
import sys
from pathlib import Path
from openai import OpenAI

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.queries import db_manager

class RAGValidator:
    def __init__(self):
        """
        Initialize RAG validator with OpenAI client
        """
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4.1-mini"
        self.temperature = 0.0  # ZERO randomness for consistency
        self.seed = 42  # Fixed seed for reproducibility
        self.cache = {}  # Response cache for identical pairs
        
        # Ensure database connection
        if not db_manager.conn:
            db_manager.connect()
    
    def _get_cache_key(self, icd_code, achi_code):
        """Generate cache key for ICD-ACHI pair"""
        import hashlib
        return hashlib.md5(f"{icd_code}:{achi_code}".encode()).hexdigest()
    
    def validate(self, icd_code: str, achi_code: str) -> dict:
        """
        RAG-Enhanced Validation with Few-Shot Learning
        
        Flow:
        1. Check cache (instant, consistent)
        2. Check exact match in database (instant, 100% accurate)
        3. Get similar examples from database (RAG context)
        4. Use AI with examples for validation
        """
        # Step 1: Check cache first
        cache_key = self._get_cache_key(icd_code, achi_code)
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Step 2: Get code details
        icd_data = db_manager.get_icd_with_category(icd_code)
        achi_data = db_manager.get_achi_with_category(achi_code)
        
        if not icd_data:
            return {
                'is_valid': False,
                'reasoning': f'ICD code {icd_code} not found in database',
                'confidence': 0.0,
                'certainty_explanation': 'Code not found',
                'source': 'error',
                'similar_examples_count': 0
            }
        
        if not achi_data:
            return {
                'is_valid': False,
                'reasoning': f'ACHI code {achi_code} not found in database',
                'confidence': 0.0,
                'certainty_explanation': 'Code not found',
                'source': 'error',
                'similar_examples_count': 0
            }
        
        # Step 2: Check EXACT match in database
        exact_match = db_manager.get_exact_match(icd_code, achi_code)
        if exact_match:
            result = {
                'is_valid': True,
                'reasoning': exact_match['relationship'],
                'confidence': 1.0,
                'certainty_explanation': 'Exact match found in validated database',
                'source': 'database_exact',
                'similar_examples_count': 0,
                'icd_description': icd_data['description'],
                'achi_description': achi_data['short_description']
            }
            # Cache before returning
            self.cache[cache_key] = result
            return result
        
        # Step 3: Get SIMILAR examples from database
        similar_examples = db_manager.get_similar_examples(
            icd_data['category'],
            achi_data['category'],
            limit=5
        )
        
        if similar_examples:
            # Use similar examples as few-shot context
            result = self.validate_with_similar_examples(
                icd_data, achi_data, similar_examples
            )
        else:
            # No similar examples - pure AI inference
            result = self.validate_pure_ai(icd_data, achi_data)
        
        # Add descriptions to result
        result['icd_description'] = icd_data['description']
        result['achi_description'] = achi_data['short_description']
        
        # Cache before returning
        self.cache[cache_key] = result
        
        return result
    
    def validate_with_hierarchical_context(self, icd_code: str, icd_desc: str, achi_code: str, achi_desc: str, context: dict) -> dict:
        """
        AI validation with hierarchical context from ACHI-10th Edition structure
        Context provides medical domain information but AI generates confidence
        """
        # Build hierarchical context prompt
        hierarchical_info = f"""
HIERARCHICAL CONTEXT:

ICD-10-AM Code: {icd_code} - {icd_desc}
└─ ICD Chapter: {context['icd_chapter']} ({context['icd_chapter_name']})

ACHI Code: {achi_code} - {achi_desc}
└─ Main Category: {context['achi_main_category']} - {context['achi_main_name']}
└─ Sub-Category: {context['achi_sub_category']}

CATEGORY MAPPING STATUS:
{context['icd_chapter_name']} ↔ {context['achi_main_name']}
Mapping Found: {'Yes' if context['category_match'] else 'No'}
"""
        
        if context['mapping_notes']:
            hierarchical_info += f"\nMAPPING EXAMPLES: {context['mapping_notes']}"
        
        prompt = f"""You are an expert clinical coding specialist for Australian ICD-10-AM and ACHI codes.

{hierarchical_info}

TASK: Validate if this ACHI procedure is clinically appropriate for this ICD-10-AM diagnosis.

CRITICAL INSTRUCTIONS:
- Use the hierarchical context as MEDICAL DOMAIN GUIDANCE only
- Generate confidence based on your ACTUAL medical knowledge and reasoning
- Do NOT use mapping confidence as your validation confidence
- Be HONEST about your certainty level
- Consider the specific procedure within its sub-category context

CONFIDENCE GUIDELINES (be honest):
- 0.90-1.0: Clear clinical indication or contraindication
- 0.80-0.89: Strong clinical evidence but some edge cases possible  
- 0.70-0.79: Moderate clinical appropriateness
- 0.50-0.69: Uncertain, requires clinical judgment
- Below 0.50: Very uncertain or inappropriate

Respond with JSON only:
{{
    "is_valid": true/false,
    "reasoning": "Detailed clinical explanation using hierarchical context",
    "confidence": 0.0-1.0,
    "certainty_explanation": "Why this confidence level based on medical reasoning"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                seed=self.seed,
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            result['source'] = 'ai_hierarchical'
            result['hierarchical_context'] = True
            
            return result
        
        except Exception as e:
            return {
                'is_valid': False,
                'reasoning': f'API Error: {str(e)}',
                'confidence': 0.0,
                'certainty_explanation': 'Error calling AI model',
                'source': 'error',
                'hierarchical_context': False
            }
    
    def validate_code_pair(self, icd_code: str, icd_desc: str, achi_code: str, achi_desc: str, context: dict = None) -> dict:
        """
        Wrapper method for compatibility with hierarchical validator
        Falls back to regular validation if no context provided
        """
        if context and context.get('hierarchical_context'):
            return self.validate_with_hierarchical_context(icd_code, icd_desc, achi_code, achi_desc, context)
        else:
            # Fallback to regular validation
            return self.validate(icd_code, achi_code)
    
    def validate_with_similar_examples(self, icd_data: dict, achi_data: dict, examples: list) -> dict:
        """
        AI validation with similar examples as few-shot learning
        """
        # Format examples for prompt
        examples_text = "\n\n".join([
            f"Example {i+1} (VALID - Confidence: {ex['confidence']:.2f}):\n"
            f"ICD: {ex['icd_code']} - {ex['icd_description']}\n"
            f"ACHI: {ex['achi_code']} - {ex['achi_description']}\n"
            f"Reasoning: {ex['relationship']}"
            for i, ex in enumerate(examples)
        ])
        
        prompt = f"""You are an expert clinical coding specialist for Australian medical codes.

You have these VALIDATED EXAMPLES from the database showing VALID pairings:

{examples_text}

Now validate this NEW pair based on similar patterns:

ICD-10-AM: {icd_data['code']} - {icd_data['description']} [Category: {icd_data['category']}]
ACHI: {achi_data['code']} - {achi_data['short_description']} [Category: {achi_data['category']}]

INSTRUCTIONS:
1. Compare this pair to the examples above
2. Determine if it follows similar clinical logic
3. Provide HONEST confidence based on:
   - High (0.90-1.0): Very similar to examples, clear clinical indication
   - Moderate (0.75-0.89): Somewhat similar, generally appropriate
   - Low (0.60-0.74): Uncertain, edge case
   - Very low (<0.60): Probably invalid or insufficient evidence
4. Be conservative: if unsure, mark invalid or give low confidence
5. Explain WHY you have this confidence level

Respond with JSON only:
{{
    "is_valid": true/false,
    "reasoning": "Clinical explanation comparing to examples",
    "confidence": 0.0-1.0,
    "certainty_explanation": "Why this confidence level based on example similarity"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                seed=self.seed,  # Deterministic
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            result['source'] = 'ai_with_examples'
            result['similar_examples_count'] = len(examples)
            
            return result
        
        except Exception as e:
            return {
                'is_valid': False,
                'reasoning': f'API Error: {str(e)}',
                'confidence': 0.0,
                'certainty_explanation': 'Error calling AI model',
                'source': 'error',
                'similar_examples_count': 0
            }
    
    def validate_pure_ai(self, icd_data: dict, achi_data: dict) -> dict:
        """
        AI validation without examples (fallback for uncovered categories)
        Uses enhanced prompt with decision tree and 8 diverse few-shot examples
        """
        prompt = f"""You are an expert clinical coding specialist for Australian ICD-10-AM and ACHI codes.

DECISION GUIDANCE (use as reference, not strict rules):

1. CATEGORY MISMATCH: Completely unrelated categories → INVALID, high confidence (≥0.90)
2. SYMPTOM CODES (R/S/T): Valid if procedure is diagnostic, moderate confidence (0.70-0.80)
3. UNSPECIFIED (.9): Valid but moderate confidence (0.75-0.85) due to lack of specificity
4. CLEAR INDICATION: Direct clinical relationship → VALID, high confidence (≥0.90)
5. CONTEXT-DEPENDENT: Valid but requires specific context → moderate confidence (0.70-0.85)

CONFIDENCE GUIDELINES (honest assessment, not constraints):
- 0.90-1.00: Crystal clear indication or contraindication
- 0.75-0.89: Strong evidence, generally appropriate or inappropriate
- 0.60-0.74: Moderate confidence, context-dependent
- Below 0.60: Uncertain or insufficient evidence

FEW-SHOT EXAMPLES:

Example 1 (INVALID, high confidence):
ICD: K02.9 (Dental caries) + ACHI: 92209-00 (NIV respiratory support)
Result: {{"is_valid": false, "confidence": 0.98, "reasoning": "Dental condition has no respiratory indication", "certainty_explanation": "Clear category mismatch"}}

Example 2 (VALID, high confidence):
ICD: J45.0 (Asthma) + ACHI: 92209-00 (NIV respiratory support)
Result: {{"is_valid": true, "confidence": 0.95, "reasoning": "Direct indication for respiratory support in severe asthma", "certainty_explanation": "Textbook indication"}}

Example 3 (VALID, moderate confidence - symptom code):
ICD: R07.3 (Other chest pain) + ACHI: 92043-00 (Respiratory medication via nebuliser)
Result: {{"is_valid": true, "confidence": 0.75, "reasoning": "Symptom code allows plausible respiratory cause, but chest pain is non-specific", "certainty_explanation": "Symptom code reduces certainty"}}

Example 4 (VALID, moderate confidence - unspecified):
ICD: J18.9 (Pneumonia, unspecified) + ACHI: 55130-00 (Bronchoscopy with lavage)
Result: {{"is_valid": true, "confidence": 0.80, "reasoning": "Bronchoscopy appropriate for pneumonia workup, but .9 code lacks specificity", "certainty_explanation": "Unspecified diagnosis"}}

Example 5 (VALID, moderate-low confidence - context-dependent):
ICD: R10.4 (Unspecified abdominal pain) + ACHI: 30473-00 (Diagnostic laparoscopy)
Result: {{"is_valid": true, "confidence": 0.72, "reasoning": "Symptom code suggests investigation, but valid only if alarm features present or failed conservative therapy", "certainty_explanation": "Requires clinical context"}}

Example 6 (VALID, moderate confidence - context-dependent):
ICD: I10 (Essential hypertension) + ACHI: 13100-00 (Continuous arterial monitoring)
Result: {{"is_valid": true, "confidence": 0.82, "reasoning": "Appropriate for hypertensive crisis or perioperative monitoring, not routine outpatient", "certainty_explanation": "Context-specific indication"}}

Example 7 (VALID, high confidence - preventive):
ICD: A00.9 (Cholera, unspecified) + ACHI: 92498-00 (Vaccination against cholera)
Result: {{"is_valid": true, "confidence": 0.90, "reasoning": "Direct prophylactic measure for cholera", "certainty_explanation": "Standard prevention"}}

Example 8 (INVALID, high confidence - clear mismatch):
ICD: A90 (Dengue fever) + ACHI: 16520-00 (Caesarean section)
Result: {{"is_valid": false, "confidence": 0.95, "reasoning": "Dengue is viral infection, not obstetric indication for C-section", "certainty_explanation": "Completely unrelated categories"}}

NOW VALIDATE THIS PAIR:

ICD-10-AM: {icd_data['code']} - {icd_data['description']} [Category: {icd_data['category']}]
ACHI: {achi_data['code']} - {achi_data['short_description']} [Category: {achi_data['category']}]

Provide HONEST confidence based on your actual medical certainty. No artificial caps or floors.

Respond with JSON only:
{{
    "is_valid": true/false,
    "reasoning": "Detailed clinical explanation",
    "confidence": 0.0-1.0,
    "certainty_explanation": "Why this confidence level"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                seed=self.seed,  # Deterministic
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            result['source'] = 'ai_inference'
            result['similar_examples_count'] = 0
            
            return result
        
        except Exception as e:
            return {
                'is_valid': False,
                'reasoning': f'API Error: {str(e)}',
                'confidence': 0.0,
                'certainty_explanation': 'Error calling AI model',
                'source': 'error',
                'similar_examples_count': 0
            }

# Global validator instance
rag_validator = RAGValidator()

