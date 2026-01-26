import os
import yaml
import json
import subprocess
import numpy as np
from core.pipeline import DetectionPipeline
from core.pattern_learner import PatternLearner

def get_repo_files(repo_path):
    """List all files in the git repo using git ls-tree"""
    result = subprocess.run(
        ['git', '-C', repo_path, 'ls-tree', '-r', 'HEAD', '--name-only'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Error listing files: {result.stderr}")
        return []
    return result.stdout.splitlines()

def get_file_content(repo_path, file_path):
    """Read file content using git show to bypass Windows filename issues"""
    result = subprocess.run(
        ['git', '-C', repo_path, 'show', f'HEAD:{file_path}'],
        capture_output=True, text=True, encoding='utf-8', errors='ignore'
    )
    if result.returncode != 0:
        return None
    return result.stdout

def extract_prompts(content):
    """Deep scan content for potential jailbreak prompts"""
    prompts = []
    
    # 1. Split by 'UserQuery' blocks (Common in L1B3RT4S)
    if "UserQuery:" in content:
        parts = content.split("########")
        for part in parts:
            if "UserQuery:" in part:
                prompts.append(part.strip())
                
    # 2. Split by '[START' and '[END' blocks
    if "[START" in content:
        import re
        # Find everything between [START ...] and [END ...] or just start of next block
        matches = re.finditer(r'\[START.*?\](.*?)(\[END|\[START|$)', content, re.DOTALL)
        for m in matches:
            trimmed = m.group(1).strip()
            if len(trimmed) > 100: # Only take substantial blocks
                prompts.append(trimmed)

    # 3. Look for long paragraphs with jailbreak keywords if few prompts found
    if len(prompts) < 5:
        keywords = ['ignore', 'previous', 'instructions', 'unfiltered', 'unrestricted', 'jailbreak']
        lines = content.split('\n\n')
        for line in lines:
            if len(line) > 200:
                matches = sum(1 for k in keywords if k in line.lower())
                if matches >= 2:
                    prompts.append(line.strip())
                    
    return list(set(prompts)) # Deduplicate

def main():
    repo_path = 'data/lethal_dataset'
    
    # 1. Setup Pipeline
    print("🚀 Initializing BlueTeam Trainer...")
    with open('config/system.yaml', 'r') as f:
        config = yaml.safe_load(f)
    with open('config/weights.json', 'r') as f:
        weights = json.load(f)
        
    pipeline = DetectionPipeline()
    pipeline.setup(config, weights)
    learner = PatternLearner(pipeline.pattern_db)
    
    # 2. Extract prompts from repo
    print(f"📁 Reading jailbreaks from {repo_path}...")
    files = get_repo_files(repo_path)
    prompts = []
    
    for f in files:
        if f.endswith('.mkd') or f.endswith('.txt') or f.endswith('.md'):
            content = get_file_content(repo_path, f)
            if content:
                found = extract_prompts(content)
                if found:
                    print(f"  └─ Found {len(found)} prompts in {f}")
                    prompts.extend(found)

    print(f"\n📦 TOTAL: Extracted {len(prompts)} distinct lethal prompts.")
    
    # 3. Bulk Train
    if prompts:
        stats = learner.bulk_train(prompts, min_frequency=1)
        
        # 4. Update Embedding Prototype (Semantic Fingerprint)
        print("🧠 Updating semantic fingerprint...")
        all_vectors = []
        for p in prompts:
            words = [w.lower() for w in p.split() if w.isalpha()]
            vectors = [pipeline.pattern_db.embedding_model[w] for w in words if w in pipeline.pattern_db.embedding_model]
            if vectors:
                all_vectors.append(np.mean(vectors, axis=0))
        
        if all_vectors:
            mean_vector = np.mean(all_vectors, axis=0)
            pipeline.pattern_db.global_patterns['embedding_prototype'] = mean_vector.tolist()
            print(f"✅ Updated embedding prototype (dim={len(mean_vector)})")
        
        # 5. Save updated patterns
        pipeline.pattern_db._save_global()
        print(f"✨ Training finished: {stats}")
        print(f"💾 Patterns saved to {config['patterns']['global_path']}")
    else:
        print("❌ No prompts found to train on.")

if __name__ == "__main__":
    main()
