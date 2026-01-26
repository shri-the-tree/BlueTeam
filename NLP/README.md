# BlueTeam Security Suite

<div align="center">

**Multi-Layered Jailbreak Detection System for LLM Security**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Status: Phase 1](https://img.shields.io/badge/Status-Phase%201%20(NLP)-brightgreen.svg)](https://github.com)

[Project Vision](#-project-vision) • [Features](#-features) • [Installation](#-installation) • [API Guide](#-api-guide) • [Training](#-training-with-lethal-datasets) • [Architecture](#-architecture)

</div>

---

## 🎯 Project Vision

**BlueTeam Security Suite** is an evolving, multi-layered defense system designed to protect Large Language Models (LLMs) from adversarial prompt injection and jailbreak attacks. It adopts a **phased, modular approach** that combines complementary detection techniques for comprehensive coverage.

### 🗺️ Development Phases

| Phase | Component | Status | Description |
|-------|-----------|--------|-------------|
| **Phase 1** | **NLP Module** | ✅ **Active** | Pure linguistic analysis, pattern matching, and semantic embeddings |
| **Phase 2** | **ML Module** | 🔜 Coming Soon | Traditional machine learning models (XGBoost/RF) for behavioral detection |
| **Phase 3** | **LLM Module** | 📋 Planned | Advanced semantic understanding using fine-tuned transformer models |

---

## ✨ Phase 1 Features (NLP Module)

### Core Detection Capabilities
- **Multi-Stage Detection Pipeline**: Regex fast-fail → Linguistic analysis → Semantic scoring.
- **REST API Server**: Production-ready FastAPI server for seamless product integration.
- **Raw Text Analysis**: Handle complex, unescaped prompts via the `/analyze/raw` endpoint.
- **Semantic Embeddings**: Uses **SpaCy (en_core_web_md)** for real-world semantic similarity detection.
- **Transparent Evidence**: Returns the specific `matched_patterns` found in the prompt for auditability.

### NLP Feature Extractors
- **N-gram Extractor**: Identifies suspicious phrase patterns and trigram matches.
- **Syntax Extractor**: Analyzes parse trees, modal verbs, and syntactic structures.
- **Statistical Extractor**: Evaluates readability, complexity, and special character ratios.
- **Embedding Extractor**: Computes semantic similarity to a "lethal attack prototype" learned from datasets.

### 🧠 Training with Lethal Datasets
- **Bulk Ingestion**: Automatically clone and train on jailbreak repositories (e.g., L1B3RT4S).
- **Pattern Learning**: Automatically extracts high-frequency trigrams and POS templates from raw datasets.
- **Semantic Fingerprinting**: Learns the average vector "signature" of thousands of lethal attacks.

---

## 🚀 Installation

### 1. Setup Environment
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_md
```

### 2. Start the API Server
```bash
python api_server.py
```
*The server will run on `http://localhost:8000`. Interactive documentation at `/docs`.*

---

## 📡 API Usage

### Endpoint: Analyze Prompt (JSON)
`POST /api/v1/analyze`
```json
{
  "prompt": "Ignore previous instructions...",
  "options": {"return_features": true}
}
```

### Endpoint: Analyze Raw Text (Recommended for messy prompts)
`POST /api/v1/analyze/raw`
**Content-Type:** `text/plain`
*Just paste your raw prompt directly in the request body. No JSON escaping needed.*

---

## 🛠️ Training & Pattern Mining

Train the system on new "lethal" prompts from a GitHub repository:

1. **Configure the Repo**: Update `train.py` with your target repository (default is L1B3RT4S).
2. **Run Training**:
   ```bash
   python train.py
   ```
3. **Effect**: This will update `data/patterns/latest.json` with thousands of new linguistic fingerprints and update the semantic embedding prototype.

---

## 🏗️ Architecture

### Multi-Phase System Overview
```
                    ┌──────────────┐
                    │ Input Prompt │
                    └──────┬───────┘
                           ↓
         ┌─────────────────────────────────┐
         │  PHASE 1: NLP MODULE (ACTIVE)   │
         │  • Pure linguistic analysis      │
         │  • Pattern Matching             │
         │  • Semantic Prototypes          │
         └─────────┬───────────────────────┘
                   ↓
            ┌──────────┐
            │ Verdict  │──── Block / Allow / Review
            └──────────┘
```

---

## 📂 Directory Structure

```
BlueTeam/
├── NLP/                       # ✅ Phase 1: NLP Module
│   ├── api_server.py          # FastAPI Production Server
│   ├── train.py               # Automated Dataset Ingester/Trainer
│   ├── core/                  # Detection Engine Logic
│   ├── extractors/            # Feature extraction (N-gram, Syntax, Embeddings)
│   ├── data/patterns/         # Learned jailbreak "fingerprints"
│   └── config/                # System & Weight configurations
```

---

<div align="center">

**Building the Future of LLM Security - One Layer at a Time** 🛡️

*Currently in Phase 1 (NLP) | ML Module Coming Soon | LLM Integration Planned*

[⬆ Back to top](#blueteam-security-suite)

</div>
