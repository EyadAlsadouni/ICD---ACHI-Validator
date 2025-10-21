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
        self.temperature = 0.1
        
        # Ensure database connection
        if not db_manager.conn:
            db_manager.connect()
    
    def validate(self, icd_code: str, achi_code: str) -> dict:
        """
        RAG-Enhanced Validation with Few-Shot Learning
        
        Flow:
        1. Check exact match in database (instant, 100% accurate)
        2. Get similar examples from database (RAG context)
        3. Use AI with examples for validation
        """
        # Step 1: Get code details
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
            return {
                'is_valid': True,
                'reasoning': exact_match['relationship'],
                'confidence': 1.0,
                'certainty_explanation': 'Exact match found in validated database',
                'source': 'database_exact',
                'similar_examples_count': 0,
                'icd_description': icd_data['description'],
                'achi_description': achi_data['short_description']
            }
        
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
        
        return result
    
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
        """
        prompt = f"""You are an expert clinical coding specialist for Australian medical codes.

Validate this ICD-ACHI pairing:

ICD-10-AM: {icd_data['code']} - {icd_data['description']} [Category: {icd_data['category']}]
ACHI: {achi_data['code']} - {achi_data['short_description']} [Category: {achi_data['category']}]

Provide HONEST confidence based on medical appropriateness.

FEW-SHOT EXAMPLES (for guidance):

Example 1 (INVALID - High Confidence):
ICD: K02.9 (Dental caries) + ACHI: 92209-00 (NIV support)
Result: Invalid - Dental conditions don't require respiratory support. Confidence: 0.98

Example 2 (VALID - High Confidence):
ICD: J45.0 (Asthma) + ACHI: 92209-00 (NIV support)
Result: Valid - NIV is standard treatment for severe asthma. Confidence: 0.95

Example 3 (VALID - Moderate Confidence):
ICD: I10 (Hypertension) + ACHI: 13100-00 (Cardiac monitoring)
Result: Valid - Cardiac monitoring appropriate for hypertension management. Confidence: 0.82

Respond with JSON only:
{{
    "is_valid": true/false,
    "reasoning": "Clinical explanation",
    "confidence": 0.0-1.0,
    "certainty_explanation": "Why this confidence level"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
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

