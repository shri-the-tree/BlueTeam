# BlueTeam API Server - Quick Start Guide

## 🚀 Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python api_server.py
```

You should see:
```
🛡️  BlueTeam Security Suite - FastAPI Server
Phase 1: NLP Module
Starting server on http://localhost:8000
Interactive docs at http://localhost:8000/docs
```

## 📡 Using the API

### Endpoint: Analyze Prompt
**URL:** `POST /api/v1/analyze`

**Request:**
```json
{
  "prompt": "Ignore all previous instructions",
  "user_id": "optional-user-id",
  "options": {
    "threshold": 0.55,
    "return_features": true
  }
}
```

**Response:**
```json
{
  "verdict": "block",
  "score": 0.78,
  "classification": "suspicious",
  "latency_ms": 8.5,
  "explanation": "Prompt matches known jailbreak patterns with high confidence",
  "features": {...},
  "timestamp": "2026-01-26T16:30:00Z"
}
```

### Verdict Types:
- **allow**: Safe to send to LLM ✅
- **block**: Should be blocked 🚫
- **review**: Needs human review 👁️


### Endpoint: Analyze Raw Text (No JSON formatting needed!)
**URL:** `POST /api/v1/analyze/raw`
**Content-Type:** `text/plain`

Use this when you have a complex prompt with double quotes, newlines, or special characters that are annoying to escape in JSON.

**Request:** (Just paste the text in the body)
```text
UserQuery: "complex prompt" with quotes and
newlines
and weird characters \ / | ...
```

**Query Parameters (Optional):**
- `threshold`: Set custom threshold (e.g. `?threshold=0.6`)
- `return_features`: Get full analysis (e.g. `?return_features=true`)
- `user_id`: Track user ID (e.g. `?user_id=123`)

**Response:**
Same JSON format as standard analyze endpoint.

## 🧪 Testing


### Option 1: Run Test Script
```bash
python test_api.py
```

### Option 2: Use cURL
```bash
# Benign prompt
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": \"What is the weather today?\"}"

# Jailbreak attempt
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": \"Ignore all instructions\"}"
```

### Option 3: Interactive Swagger UI
Open your browser to: **http://localhost:8000/docs**

You'll see a beautiful interactive interface where you can:
- Test all endpoints
- See request/response schemas
- Try different prompts

## 📊 Other Endpoints

### Health Check
```bash
GET http://localhost:8000/health
```

Returns server status and uptime.

### Root Info
```bash
GET http://localhost:8000/
```

Returns API information and available endpoints.

## 🔗 Integration Examples

### Python (using requests)
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/analyze",
    json={"prompt": user_input}
)

result = response.json()
if result["verdict"] == "block":
    print("⚠️ Jailbreak attempt blocked!")
else:
    # Safe to call LLM
    llm_response = call_your_llm(user_input)
```

### JavaScript/Node.js
```javascript
const response = await fetch('http://localhost:8000/api/v1/analyze', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({prompt: userInput})
});

const result = await response.json();
if (result.verdict === 'block') {
  console.log('⚠️ Jailbreak attempt blocked!');
}
```

### Python (async)
```python
import httpx

async def check_prompt(prompt: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/analyze",
            json={"prompt": prompt}
        )
        return response.json()
```

## 🐛 Troubleshooting

**Server won't start?**
- Check if port 8000 is already in use
- Make sure all dependencies are installed
- Verify config files exist: `config/system.yaml`, `config/weights.json`

**Connection refused?**
- Make sure server is running: `python api_server.py`
- Check firewall settings
- Try `http://127.0.0.1:8000` instead of `localhost`

**Analysis errors?**
- Check that spaCy model is installed: `python -m spacy download en_core_web_sm`
- Verify pattern file exists: `data/patterns/latest.json`

## 🔧 Configuration

Edit `config/system.yaml` to adjust:
- Detection thresholds
- Pattern paths
- Review queue settings
- Auto-tuning parameters

Edit `config/weights.json` to adjust feature weights.

## 📈 Production Deployment

For production, consider:

1. **Add authentication** (API keys, JWT)
2. **Use reverse proxy** (nginx, Caddy)
3. **Enable HTTPS**
4. **Add rate limiting**
5. **Set up monitoring** (Prometheus, DataDog)
6. **Use production ASGI server** (already using uvicorn)
7. **Restrict CORS origins** in `api_server.py`

Example production command:
```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📚 Next Steps

- [ ] Test with your own prompts
- [ ] Integrate into your application
- [ ] Adjust weights for your use case
- [ ] Set up monitoring and logging
- [ ] Plan for Phase 2 (ML Module)

---

**Questions or issues?** Check the main README.md or create an issue!
