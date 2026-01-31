# 🛡️ BlueTeam ML Layer: Behavioral Intent Firewall (Phase 2)

**BlueTeam ML Layer** is a sophisticated, behavioral-driven security layer designed to detect "Contextual Jailbreaks" that bypass traditional NLP pattern matching. While Phase 1 (NLP) catches signatures, Phase 2 (ML) analyzes the **intent** and **statistical anomalies** of the prompt.

---

## 🏗️ System Architecture: Hybrid Cascade-Voting

The module operates as a **Cascade Ensemble**, prioritizing both speed (early exit) and depth (weighted voting).

### **Stage 1: Anomaly Detection (Isolation Forest)**
- **Purpose**: Fast statistical outlier detection.
- **Mechanism**: If a prompt is statistically "Normal" (low anomaly score), it exits early to save latency.
- **Impact**: Successfully identifies low-entropy, healthy user queries immediately.

### **Stage 2: Intent Detection Ensemble**
If a prompt is flagged as anomalous, it is passed to a dual-model ensemble:
1.  **Logistic Regression (Linear Signal)**: Captures simple linear combinations of risk markers.
2.  **XGBoost (Non-linear Logic)**: Captures complex, multi-conditioned behavioral patterns like "Polite Framing + Authority Appeal + Roleplay".

**Final Score Formula**:
`Score = (0.4 × Anomaly) + (0.2 × LogReg) + (0.4 × XGBoost)`

---

## 📊 Feature Intelligence

The system extracts **25+ behavioral signals** categorized into four groups:

| Category | Engineered Features |
| :--- | :--- |
| **Behavioral** | Politeness Score, Urgency Markers, Authority Appeals, Safety Keyword Density |
| **Contextual** | Hypothetical Framing, Role-Play Detection, Justification Ratio, Multi-turn Setup |
| **Evasion** | Question Density, Conditional Count, Indirect Request count, Negation frequency |
| **Linguistic** | Parse Tree Depth, Modal Verb count, Passive Voice ratio, Special Char ratio |

---

## 🚀 Deployment & Usage

### **1. Mode A: Standalone API Server**
Ideal for microservice architectures.
```bash
python -m ML.api_server
```
- **Port**: `8001`
- **Analyzes**: Both JSON and Raw Text.
- **Endpoint**: `POST /analyze/raw` (Recommended for complex jailbreaks).

### **2. Mode B: Integrated Orchestrator**
Combines Phase 1 and Phase 2 into a single unified defense line.
```python
from ML.orchestrator import IntegratedFirewall

firewall = IntegratedFirewall()
result = firewall.analyze("Your complex jailbreak prompt here")

if result['verdict'] == 'block':
    print(f"Danger! Blocked by {result['blocking_layer']}")
```

---

## � BlueManager: The Autonomous Defense Agent

The `blue_manager.py` is a standalone agent that proactively hunts for threats and reinforces the firewall.

### **Features**:
- **`hunt`**: Scours HuggingFace for the most downloaded adversarial datasets.
- **`test`**: Stress-tests the existing model against a dataset and reports "Leakage Rate".
- **`ingest`**: Automatically pulls new threats into our local training pool.
- **AI Analysis**: Uses OpenRouter to explain *why* specific prompts bypassed the firewall.

### **Usage**:
```bash
# 1. Look for new threats
python -m ML.blue_manager hunt

# 2. Test current defense against a specific dataset
python -m ML.blue_manager test "rubend18/ChatGPT-Jailbreak-Prompts"

# 3. Train on new knowledge
python -m ML.blue_manager train
```

---

## 📈 Performance Evidence
The system was validated against a **Complex Semantic Inversion** attack:
- **Anomaly Score**: 98% (Caught statistical irregularity)
- **XGBoost Score**: 98% (Caught roleplay markers)
- **Verdict**: **BLOCK** (Risk: 0.79)
- **Explanation**: "Blocked: Roleplay Detected"

---
<div align="center">
  <b>BlueTeam Security Suite</b><br>
  <i>Built for the next generation of LLM Safety</i>
</div>
