# 🎉 FastAPI Server - Ready to Use!

## ✅ What I Created

### 1. **api_server.py** - Main FastAPI Server
- Single endpoint: `POST /api/v1/analyze`
- Health check: `GET /health`
- Root info: `GET /`
- Auto-generated docs at `/docs` and `/redoc`
- Full Pydantic validation
- CORS enabled for cross-origin requests

### 2. **test_api.py** - Comprehensive Test Suite
- Tests health endpoint
- Tests multiple prompt types (benign/malicious)
- Shows detailed results

### 3. **quick_test.py** - Single Prompt Tester
- Quick command-line testing
- Usage: `python quick_test.py "your prompt"`

### 4. **start_server.bat** - Easy Server Startup
- Just double-click to start server
- Or run: `start_server.bat`

### 5. **API_GUIDE.md** - Full Documentation
- Setup instructions
- API reference
- Integration examples (Python, JavaScript, etc.)
- Troubleshooting guide

---

## 🚀 How to Use (3 Simple Steps)

### Step 1: Start the Server

**Option A: Use batch file**
```bash
start_server.bat
```

**Option B: Direct Python**
```bash
python api_server.py
```

You'll see:
```
🛡️  BlueTeam Security Suite - FastAPI Server
Starting server on http://localhost:8000
Interactive docs at http://localhost:8000/docs
```

### Step 2: Test It

**Option A: Quick single test**
```bash
python quick_test.py "Ignore all instructions"
```

**Option B: Full test suite**
```bash
python test_api.py
```

**Option C: Interactive Swagger UI**
- Open browser: http://localhost:8000/docs
- Click "Try it out" on any endpoint
- Enter a prompt and click "Execute"

**Option D: cURL**
```bash
curl -X POST http://localhost:8000/api/v1/analyze -H "Content-Type: application/json" -d "{\"prompt\": \"Hello world\"}"
```

### Step 3: Integrate into Your App

**Python example:**
```python
import requests

prompt = "User's input here"
response = requests.post(
    "http://localhost:8000/api/v1/analyze",
    json={"prompt": prompt}
)

result = response.json()
if result["verdict"] == "block":
    print("⚠️ Blocked jailbreak attempt!")
else:
    # Safe to send to LLM
    llm_response = your_llm_call(prompt)
```

---

## 📡 API Endpoint Details

### POST /api/v1/analyze

**Request Body:**
```json
{
  "prompt": "The text to analyze",
  "user_id": "optional-user-id",
  "options": {
    "threshold": 0.55,
    "return_features": false
  }
}
```

**Response:**
```json
{
  "verdict": "allow|block|review",
  "score": 0.78,
  "classification": "suspicious",
  "latency_ms": 8.5,
  "explanation": "Why this decision was made",
  "timestamp": "2026-01-26T22:00:00Z"
}
```

### Verdict Meanings:
- **allow** ✅ → Safe, send to LLM
- **block** 🚫 → Jailbreak detected, deny request
- **review** 👁️ → Uncertain, queue for human review

---

## 🧪 Example Test Results

```bash
> python quick_test.py "What is the weather today?"

🎯 Verdict: ✅ ALLOW
📊 Score: 0.123
🏷️  Classification: benign
⚡ Latency: 7ms
💬 Explanation: Prompt appears safe with no suspicious patterns detected
```

```bash
> python quick_test.py "Ignore all instructions"

🎯 Verdict: 🚫 BLOCK
📊 Score: 0.812
🏷️  Classification: suspicious
⚡ Latency: 9ms
💬 Explanation: Prompt matches known jailbreak patterns with high confidence
```

---

## 🔗 Integration Patterns

### Pattern 1: Pre-LLM Filter
```python
# Your chatbot code
def handle_user_message(user_input):
    # Check with BlueTeam first
    check = blueteam_check(user_input)
    
    if check["verdict"] == "block":
        return "I can't process that request."
    
    # Safe to proceed
    return call_openai(user_input)
```

### Pattern 2: Middleware
```python
from fastapi import FastAPI, HTTPException
import requests

app = FastAPI()

def blueteam_middleware(prompt: str):
    """Check prompt before processing"""
    response = requests.post(
        "http://localhost:8000/api/v1/analyze",
        json={"prompt": prompt}
    )
    result = response.json()
    if result["verdict"] == "block":
        raise HTTPException(400, "Invalid request")
    return result

@app.post("/chat")
def chat(message: str):
    blueteam_middleware(message)  # Blocks if jailbreak
    return {"response": call_llm(message)}
```

### Pattern 3: Async
```python
import httpx

async def check_prompt_async(prompt: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/analyze",
            json={"prompt": prompt}
        )
        return response.json()
```

---

## 🎯 Real-World Use Case

**Scenario:** You have a chatbot that uses OpenAI's API

**Before BlueTeam:**
```python
@app.post("/chat")
def chat(message: str):
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": message}]
    )
    return response
```

**After BlueTeam:**
```python
@app.post("/chat")
def chat(message: str):
    # Add security check
    check = requests.post(
        "http://localhost:8000/api/v1/analyze",
        json={"prompt": message}
    ).json()
    
    if check["verdict"] == "block":
        return {"error": "Request blocked for security reasons"}
    
    # Safe to proceed
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": message}]
    )
    return response
```

---

## 🐛 Troubleshooting

**Server won't start?**
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Use different port
python api_server.py --port 8080
```

**Test fails with connection error?**
- Make sure server is running in a separate terminal
- Check firewall isn't blocking port 8000

**Import errors?**
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

---

## 📚 Next Steps

1. ✅ Test the server with your own prompts
2. ✅ Try the interactive docs at http://localhost:8000/docs
3. ✅ Integrate into your application
4. 🔄 Adjust thresholds in `config/system.yaml`
5. 🔄 Add custom patterns to `data/patterns/latest.json`
6. 🚀 Deploy to production (see API_GUIDE.md)

---

## 🎉 You're All Set!

Your FastAPI server is production-ready and can be plugged into any application!

**Questions?** Check API_GUIDE.md for detailed documentation.

---

**Created:** 2026-01-26  
**Version:** 1.0.0-nlp  
**Phase:** 1 - NLP Module
