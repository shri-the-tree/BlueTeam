from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
import uvicorn
import os
from typing import Optional, Dict, Any

from ML.core.ml_firewall import MLFirewall

app = FastAPI(title="BlueTeam ML Firewall", version="2.0.0")

# Initialize Firewall (Standalone Mode)
# This will try to load models from ML/models
firewall = MLFirewall()

class PromptRequest(BaseModel):
    prompt: str
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)

@app.get("/")
def root():
    return {
        "system": "BlueTeam ML Layer",
        "status": "active" if firewall.is_loaded else "waiting_for_models",
        "mode": "standalone"
    }

@app.post("/analyze")
def analyze(request: PromptRequest):
    if not firewall.is_loaded:
        raise HTTPException(status_code=503, detail="Models not loaded. Please run training pipeline first.")
    
    return firewall.analyze(request.prompt, options=request.options)

@app.post("/analyze/raw")
async def analyze_raw(request: Request, threshold: float = 0.7):
    """
    Direct raw text endpoint.
    Usage: POST /analyze/raw?threshold=0.55
    Body: <your raw text here>
    """
    if not firewall.is_loaded:
        raise HTTPException(status_code=503, detail="Models not loaded. Please run training pipeline first.")
    
    try:
        body = await request.body()
        content = body.decode("utf-8").strip()
        if not content:
            raise HTTPException(status_code=400, detail="Empty prompt")

        # Smart Fallback: Check if user accidentally sent JSON to the raw endpoint
        if content.startswith('{') and content.endswith('}'):
            try:
                import json
                data = json.loads(content)
                prompt = data.get('prompt', content)
                # Priority: 
                # 1. URL Query Param (if provided)
                # 2. JSON 'options' field
                # 3. Default (0.7)
                json_options = data.get('options', {})
                
                # Check if threshold was explicitly provided in URL (not default)
                # Fastapi doesn't tell us if it's default or not easily, so we check
                # if it's different from the standard default.
                if threshold != 0.7:
                    final_threshold = threshold
                else:
                    final_threshold = json_options.get('threshold', 0.7)
                
                options = {**json_options, "threshold": final_threshold}
            except:
                prompt = content
                options = {"threshold": threshold}
        else:
            prompt = content
            options = {"threshold": threshold}
        
        return firewall.analyze(prompt, options=options)
        
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Request error: {str(e)}")

@app.get("/health")
def health():
    return {"status": "healthy", "models_loaded": firewall.is_loaded}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
