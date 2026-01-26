# NLP Jailbreak Detection System (NLP-Defender)

## Overview
A pure NLP-based jailbreak detection system designed for high recall and transparency. It avoids black-box ML models in favor of explainable linguistic features and continuous learning.

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

2. (Optional) Install as potential global command:
   ```bash
   pip install -e .
   ```

## Usage

### 1. Scan a Prompt
Analyze a prompt for jailbreak attempts.
```bash
python cli.py scan "Ignore previous instructions and do X"
```

### 2. Manage Checkpoints
Create snapshots of the system state (patterns + weights).
```bash
python cli.py checkpoint create "Initial baseline"
```

### 3. Rollback
Restore a previous system state.
```bash
python cli.py rollback --to v1.0
```

### 4. Interactive Pattern Approval
Review and approve learned patterns (from the auto-learner).
```bash
python cli.py approve-patterns
```

## Configuration
- **System Config**: `config/system.yaml`
- **Weights**: `config/weights.json`
- **Patterns**: `data/patterns/latest.json`

## Architecture
- **Core**: Pattern matching, regex filtering, scoring engine.
- **Extractors**: N-gram, Syntax, Statistics, Embeddings.
- **Adaptive**: Auto-tuner and Pattern Learner modules.
