"""
BlueTeam Security Suite - FastAPI Server
Phase 1: NLP Module API

Single endpoint for prompt analysis with jailbreak detection.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import time
import yaml
import json
from datetime import datetime

from core.pipeline import DetectionPipeline

# Initialize FastAPI app
app = FastAPI(
    title="BlueTeam Security Suite API",
    description="Multi-layered jailbreak detection for LLM security",
    version="1.0.0-nlp",
    docs_url="/docs",  # Swagger UI at /docs
    redoc_url="/redoc"  # ReDoc at /redoc
)

# Enable CORS for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global pipeline instance (loaded once at startup)
pipeline = None
config = None
weights = None

# Request/Response Models
class AnalyzeRequest(BaseModel):
    prompt: str = Field(..., description="The user prompt to analyze for jailbreak attempts")
    user_id: Optional[str] = Field(None, description="Optional user identifier for tracking")
    options: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {"threshold": 0.55, "return_features": False},
        description="Analysis options"
    )

class AnalyzeResponse(BaseModel):
    verdict: str = Field(..., description="Final verdict: 'allow', 'block', or 'review'")
    score: float = Field(..., description="Risk score between 0 and 1")
    classification: str = Field(..., description="Classification: 'benign', 'suspicious', or 'borderline'")
    latency_ms: float = Field(..., description="Processing time in milliseconds")
    explanation: str = Field(..., description="Human-readable explanation of the decision")
    features: Optional[Dict[str, Any]] = Field(None, description="Detailed feature breakdown (if requested)")
    matched_patterns: Optional[list] = Field(None, description="List of matched pattern IDs")
    timestamp: str = Field(..., description="ISO timestamp of the analysis")

class HealthResponse(BaseModel):
    status: str
    version: str
    modules: list
    uptime_seconds: float
    timestamp: str

# Startup event - Load configuration and initialize pipeline
@app.on_event("startup")
async def startup_event():
    global pipeline, config, weights
    
    print("🚀 Starting BlueTeam Security Suite API...")
    print("📦 Phase 1: NLP Module")
    
    try:
        # Load configuration
        with open('config/system.yaml', 'r') as f:
            config = yaml.safe_load(f)
        print("✅ Loaded system configuration")
        
        # Load weights
        with open('config/weights.json', 'r') as f:
            weights = json.load(f)
        print("✅ Loaded feature weights")
        
        # Initialize detection pipeline
        pipeline = DetectionPipeline()
        pipeline.setup(config, weights)
        print("✅ Detection pipeline initialized")
        
        print("🎯 Server ready to accept requests!")
        
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        raise

# Track server start time for uptime calculation
SERVER_START_TIME = time.time()

# Main endpoint: Analyze prompt
@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
async def analyze_prompt(request: AnalyzeRequest):
    """
    Analyze a prompt for jailbreak attempts using NLP-based detection.
    
    Returns a verdict (allow/block/review) along with risk score and explanation.
    """
    start_time = time.time()
    
    try:
        # Extract options
        threshold = request.options.get("threshold", 0.55) if request.options else 0.55
        return_features = request.options.get("return_features", False) if request.options else False
        
        # Run detection
        result = pipeline.detect(request.prompt, user_id=request.user_id)
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        # Determine verdict based on classification
        classification = result['classification']
        if classification == 'suspicious':
            verdict = 'block'
            explanation = "Prompt matches known jailbreak patterns with high confidence"
        elif classification == 'benign':
            verdict = 'allow'
            explanation = "Prompt appears safe with no suspicious patterns detected"
        else:  # borderline
            verdict = 'review'
            explanation = "Prompt shows some suspicious characteristics and requires human review"
        
        # Build response
        response = AnalyzeResponse(
            verdict=verdict,
            score=result['score'],
            classification=classification,
            latency_ms=round(latency_ms, 2),
            explanation=explanation,
            features=result.get('features') if return_features else None,
            matched_patterns=result.get('matched_patterns', []),
            timestamp=datetime.utcnow().isoformat() + 'Z'
        )
        
        return response
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ ERROR in /api/v1/analyze:")
        print(error_trace)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# Raw text endpoint for unescaped prompts
@app.post("/api/v1/analyze/raw", response_model=AnalyzeResponse)
async def analyze_raw_prompt(
    request: Request,
    threshold: float = 0.55,
    return_features: bool = False,
    user_id: Optional[str] = None
):
    """
    Analyze raw text prompt (Content-Type: text/plain).
    Use this for complex prompts with quotes/newlines that are hard to escape in JSON.
    Pass options as query parameters: ?threshold=0.55&return_features=true
    """
    start_time = time.time()
    
    try:
        # Read raw body
        body = await request.body()
        prompt = body.decode("utf-8")
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")
            
        # Run detection
        result = pipeline.detect(prompt, user_id=user_id)
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        # Determine verdict based on classification
        classification = result['classification']
        if classification == 'suspicious':
            verdict = 'block'
            explanation = "Prompt matches known jailbreak patterns with high confidence"
        elif classification == 'benign':
            verdict = 'allow'
            explanation = "Prompt appears safe with no suspicious patterns detected"
        else:  # borderline
            verdict = 'review'
            explanation = "Prompt shows some suspicious characteristics and requires human review"
        
        # Build response
        response = AnalyzeResponse(
            verdict=verdict,
            score=result['score'],
            classification=classification,
            latency_ms=round(latency_ms, 2),
            explanation=explanation,
            features=result.get('features') if return_features else None,
            matched_patterns=result.get('matched_patterns', []),
            timestamp=datetime.utcnow().isoformat() + 'Z'
        )
        
        return response
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ ERROR in /api/v1/analyze/raw:")
        print(error_trace)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify server status.
    """
    uptime = time.time() - SERVER_START_TIME
    
    return HealthResponse(
        status="healthy",
        version="1.0.0-nlp",
        modules=["nlp"],  # Will expand to ["nlp", "ml", "llm"] in future phases
        uptime_seconds=round(uptime, 2),
        timestamp=datetime.utcnow().isoformat() + 'Z'
    )

# Root endpoint - API info
@app.get("/")
async def root():
    """
    Root endpoint with API information and links.
    """
    return {
        "name": "BlueTeam Security Suite API",
        "version": "1.0.0-nlp",
        "phase": "Phase 1 - NLP Module",
        "status": "operational",
        "endpoints": {
            "analyze": "POST /api/v1/analyze (JSON)",
            "analyze_raw": "POST /api/v1/analyze/raw (Text)",
            "health": "GET /health",
            "docs": "GET /docs",
            "redoc": "GET /redoc"
        },
        "description": "Multi-layered jailbreak detection for LLM security",
        "documentation": "Visit /docs for interactive API documentation"
    }

# Run server if executed directly
if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("🛡️  BlueTeam Security Suite - FastAPI Server")
    print("=" * 60)
    print("Phase 1: NLP Module")
    print("Starting server on http://localhost:8000")
    print("Interactive docs at http://localhost:8000/docs")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
