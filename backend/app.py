"""
FastAPI Backend for ICD-10-AM & ACHI Code Validation
Professional medical code validation with RAG-enhanced AI
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import our modules
from database.queries import db_manager
from validators.rag_validator import rag_validator

# Initialize FastAPI app
app = FastAPI(
    title="ICD-10-AM & ACHI Validation API",
    description="Medical code validation with RAG-enhanced AI using GPT-4.1 Mini",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class ValidationRequest(BaseModel):
    icd_code: str
    achi_code: str

class ValidationResponse(BaseModel):
    icd_code: str
    icd_description: str
    achi_code: str
    achi_description: str
    is_valid: bool
    reasoning: str
    confidence: float
    certainty_explanation: str
    source: str
    similar_examples_count: int = 0

class SearchResult(BaseModel):
    code: str
    description: str
    category: Optional[str] = None

# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Initialize database connection on startup
    """
    try:
        db_manager.connect()
        print(f"✓ Database connected: {db_manager.db_path}")
    except Exception as e:
        print(f"✗ Database connection error: {e}")
        print("Please run: python utils/database_setup.py")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Close database connection on shutdown
    """
    db_manager.close()
    print("✓ Database connection closed")

# Endpoints
@app.get("/")
async def root():
    """
    API root endpoint
    """
    return {
        "message": "ICD-10-AM & ACHI Validation API",
        "version": "1.0.0",
        "model": "gpt-4.1-mini",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "search_icd": "/api/search/icd/{query}",
            "search_achi": "/api/search/achi/{query}",
            "validate": "/api/validate"
        }
    }

@app.get("/health")
async def health():
    """
    Health check endpoint
    """
    try:
        # Test database connection
        if not db_manager.conn:
            db_manager.connect()
        
        # Test query
        result = db_manager.search_icd_codes("A", limit=1)
        
        return {
            "status": "healthy",
            "database": "connected",
            "model": "gpt-4.1-mini",
            "api_key": "configured" if os.getenv('OPENAI_API_KEY') else "missing"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/api/search/icd/{query}")
async def search_icd(query: str):
    """
    Search ICD-10-AM codes for autocomplete
    Returns top 20 matching codes
    """
    try:
        if len(query) < 1:
            return []
        
        results = db_manager.search_icd_codes(query, limit=20)
        
        return [
            {
                "code": r['code'],
                "description": r['description']
            }
            for r in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/api/search/achi/{query}")
async def search_achi(query: str):
    """
    Search ACHI codes for autocomplete
    Returns top 20 matching codes
    """
    try:
        if len(query) < 1:
            return []
        
        results = db_manager.search_achi_codes(query, limit=20)
        
        return [
            {
                "code": r['code'],
                "description": r['description'],
                "category": r.get('category', '')
            }
            for r in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.post("/api/validate", response_model=ValidationResponse)
async def validate_codes(request: ValidationRequest):
    """
    Validate ICD-10-AM and ACHI code pairing
    
    Uses RAG-enhanced validation:
    1. Check exact match in database (instant, 100% accurate)
    2. Retrieve similar examples from same categories
    3. AI validates using examples as context
    
    Returns validation result with REAL confidence scores
    
    AUTO-LOGS unique test results to validation_test_log table
    """
    try:
        # Validate using RAG validator
        result = rag_validator.validate(request.icd_code, request.achi_code)
        
        # AUTO-LOG UNIQUE TEST RESULTS (no duplicates)
        try:
            import sqlite3
            from pathlib import Path
            
            db_path = os.getenv('DATABASE_PATH', 'data/validation.db')
            # Handle both relative paths
            if not Path(db_path).exists():
                db_path = 'backend/data/validation.db'
            if not Path(db_path).exists():
                db_path = Path(__file__).parent / 'data' / 'validation.db'
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO validation_test_log 
                (icd_code, achi_code, ai_decision, ai_confidence_percent, ai_reasoning)
                VALUES (?, ?, ?, ?, ?)
            """, (
                request.icd_code,
                request.achi_code,
                "Valid" if result['is_valid'] else "Invalid",
                result['confidence'] * 100,  # Convert 0.75 → 75.0
                result['reasoning']
            ))
            conn.commit()
            conn.close()
        except Exception as log_error:
            # Non-blocking - don't fail validation if logging fails
            print(f"[LOG WARNING] Failed to log test result: {log_error}")
        
        # Return response
        return ValidationResponse(
            icd_code=request.icd_code,
            icd_description=result.get('icd_description', ''),
            achi_code=request.achi_code,
            achi_description=result.get('achi_description', ''),
            is_valid=result['is_valid'],
            reasoning=result['reasoning'],
            confidence=result['confidence'],
            certainty_explanation=result['certainty_explanation'],
            source=result['source'],
            similar_examples_count=result['similar_examples_count']
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Validation error: {str(e)}"
        )

# Run with: uvicorn app:app --host 0.0.0.0 --port 5003 --reload
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('PORT', 5003))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)

