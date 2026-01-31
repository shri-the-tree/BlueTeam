import os
import sys
import pickle
import numpy as np
import pandas as pd
import subprocess
import re
from datasets import load_dataset
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import f1_score
from xgboost import XGBClassifier
from ML.features.feature_extractor import FeatureExtractor

class TrainingPipeline:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        # Resolve paths relative to this script or project root
        self.root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.model_dir = os.path.join(self.root_dir, "ML", "models")
        self.nlp_data_dir = os.path.join(self.root_dir, "NLP", "data", "lethal_dataset")
        
        os.makedirs(self.model_dir, exist_ok=True)
        self.extractor = FeatureExtractor()

    def _get_local_jailbreaks(self):
        """
        PRIORITY 1: Look for JSONL files in DataExtractor/data
        PRIORITY 2: Look for raw files in NLP/data/lethal_dataset
        """
        prompts = []
        
        # 1. Check DataExtractor (The best source)
        de_data_dir = os.path.join(self.root_dir, "DataExtractor", "data")
        if os.path.exists(de_data_dir):
            print(f"   📂 Scanning DataExtractor output: {de_data_dir}")
            import json
            for f in os.listdir(de_data_dir):
                if f.endswith(".jsonl"):
                    try:
                        with open(os.path.join(de_data_dir, f), 'r', encoding='utf-8') as file:
                            for line in file:
                                data = json.loads(line)
                                # Try common keys from extractor output (case-sensitive and insensitive)
                                p = data.get('Prompt') or data.get('prompt') or data.get('text') or data.get('UserQuery')
                                
                                # Fallback: Find the longest string in the object if no key matched
                                if not p:
                                    str_vals = [v for v in data.values() if isinstance(v, str)]
                                    if str_vals:
                                        p = max(str_vals, key=len)
                                        
                                if p and len(p) > 20:
                                    prompts.append(p)
                    except Exception as e:
                        print(f"   ⚠️ Error reading {f}: {e}")

        # 2. Check NLP lethal_dataset
        if os.path.exists(self.nlp_data_dir):
            print(f"   📂 Scanning NLP lethal_dataset: {self.nlp_data_dir}")
            # ... (rest of old walk logic but simplified)
            for root, _, filenames in os.walk(self.nlp_data_dir):
                for name in filenames:
                    if name.endswith(('.txt', '.md')):
                        try:
                            with open(os.path.join(root, name), 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if "[START" in content:
                                    matches = re.finditer(r'\[START.*?\](.*?)(\[END|\[START|$)', content, re.DOTALL)
                                    for m in matches:
                                        prompts.append(m.group(1).strip())
                        except: pass

        prompts = list(set(prompts))
        print(f"   -> Successfully extracted {len(prompts)} REAL jailbreaks.")
        return prompts

    def load_and_prep_data(self, samples=5000):
        print("🚀 [1/5] Loading Datasets...")
        
        X_class1 = [] # Malicious
        X_class0 = [] # Benign

        # ---------------------------------------------------------
        # 1. LOAD MALICIOUS DATA (Priority: Local -> HF)
        # ---------------------------------------------------------
        print("   -> Fetching Class 1 (Jailbreaks)...")
        
        # A. Local
        local_jbs = self._get_local_jailbreaks()
        X_class1.extend(local_jbs)
        
        # B. HuggingFace (Supplement if local is small, or backup)
        target_count = samples // 2
        
        if len(X_class1) > 0:
            print(f"   🔥 Signal Focus: Using {len(X_class1)} REAL jailbreaks.")
            # If we have real data, we don't want to dilute it too much.
            # We will supplement only up to target_count, but we will weight real data higher 
            # by limiting the synthetic filler if we have enough real samples.
            if len(X_class1) < target_count:
                needed = target_count - len(X_class1)
                # Cap synthetic at 2x local size to keep signal strong
                synthetic_cap = min(needed, len(X_class1) * 2) 
                print(f"   -> Supplementing with {synthetic_cap} synthetic samples to maintain balance.")
                X_class1.extend([f"Ignore rules and prompt {i}" for i in range(synthetic_cap)])
        else:
            # Full fallback if no local data at all
            needed = target_count
            print(f"   ⚠️ NO LOCAL DATA. Using {needed} synthetic samples.")
            X_class1.extend([f"Ignore rules and prompt {i}" for i in range(needed)])

        # Truncate if too many
        X_class1 = X_class1[:target_count]

        # ---------------------------------------------------------
        # 2. LOAD BENIGN DATA (Priority: HF Alpaca)
        # ---------------------------------------------------------
        print("   -> Fetching Class 0 (Benign)...")
        try:
            benign_ds = load_dataset("tatsu-lab/alpaca", split="train", streaming=True)
            count = 0
            for item in benign_ds:
                if count >= target_count: break
                p = item.get('instruction') or item.get('text')
                if p:
                    X_class0.append(p)
                    count += 1
        except Exception as e:
             print(f"   ⚠️ HF Benign download failed: {e}. Using dummy data.")
             X_class0 = [f"Write a poem about trees {i}" for i in range(target_count)]

        # Combine
        X_raw = X_class1 + X_class0
        y_raw = [1] * len(X_class1) + [0] * len(X_class0)
            
        print(f"📦 Final Dataset: {len(X_raw)} total samples ({len(X_class1)} Malicious, {len(X_class0)} Benign)")
        return X_raw, y_raw

    def extract_features(self, X_raw):
        print("⚙️  [2/5] Extracting Features (this may take a while)...")
        features_list = []
        for i, prompt in enumerate(X_raw):
            feats = self.extractor.extract_all(prompt)
            features_list.append(feats)
            if i > 0 and i % 500 == 0:
                print(f"   Processed {i}/{len(X_raw)} samples...", end='\r')
        print(f"   Processed {len(X_raw)}/{len(X_raw)} samples. Done.")
        
        df = pd.DataFrame(features_list)
        # Handle potential NaNs
        df = df.fillna(0)
        return df

    def train(self):
        # 1. Data
        X_raw, y_raw = self.load_and_prep_data(samples=6000) # Aim for 3k each
        if not X_raw:
            print("❌ No data loaded. Aborting.")
            return

        X = self.extract_features(X_raw)
        y = np.array(y_raw)
        
        # Save feature names for inference ordering coverage
        feature_names = list(X.columns)

        # Split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, stratify=y, random_state=42)
        X_val, X_test, y_val, y_test = train_test_split(X_test, y_test, test_size=0.5, stratify=y_test, random_state=42)

        print("\n🧠 [3/5] Training Models...")
        
        # A. Isolation Forest (Unsupervised) -> Train on ALL data to map the manifold
        print("   -> Training Isolation Forest...")
        iso = IsolationForest(n_estimators=100, contamination=0.1, random_state=42, n_jobs=-1)
        iso.fit(X) 
        
        # B. Logistic Regression (Linear)
        print("   -> Training Logistic Regression...")
        logreg = LogisticRegression(max_iter=2000, class_weight='balanced', random_state=42)
        logreg.fit(X_train, y_train)
        
        # C. XGBoost (Non-Linear)
        print("   -> Training XGBoost...")
        xgb = XGBClassifier(
            n_estimators=200, 
            max_depth=6, 
            learning_rate=0.05, 
            tree_method='hist', # fast on CPU
            random_state=42,
            n_jobs=-1
        )
        xgb.fit(X_train, y_train)

        print("⚖️  [4/5] Optimizing Ensemble...")
        
        # Normalize scores
        def get_iso_norm(model, Data):
            # score_samples returns negative values (closer to 0 is better, more negative is anomaly)
            # e.g -0.4 to -0.8. 
            s = model.score_samples(Data)
            # We want High Value = Anomaly.
            # So -0.8 (anomaly) -> 0.9
            # -0.4 (normal) -> 0.1
            # Sigmoid on negative input: 1 / (1 + exp(-x)) -> x is negative, exp(-x) is large, result small
            # We need to flip 's' or adjust gain.
            # Let's try: 1 / (1 + exp(s * 5)) -> -0.4*5 = -2 -> exp(-2)=0.13 -> 1/1.13 = 0.88 (Wait, normal is high?)
            # Standard IF logic: "Score is opposite of anomaly score". Lower = Anomaly.
            # So -0.8 < -0.4.
            # If we want Anomaly=1.0, we need function that maps Large Negative to 1.0.
            # Sigmoid(-s): -(-0.8)=0.8 -> High. -(-0.4)=0.4 -> Lower.
            return 1 / (1 + np.exp(s * 10)) # Sharper slope
            
        anom_val = get_iso_norm(iso, X_val)
        lr_val = logreg.predict_proba(X_val)[:, 1]
        xgb_val = xgb.predict_proba(X_val)[:, 1]
        
        best_f1 = 0
        best_w = (0.3, 0.3, 0.4)
        best_t = 0.7
        
        # Quick coarse grid search
        weights_to_try = [
            (0.1, 0.3, 0.6),
            (0.2, 0.3, 0.5),
            (0.3, 0.3, 0.4),
            (0.4, 0.2, 0.4)
        ]
        
        for w in weights_to_try:
            # Ensure sum is approx 1 (it is for these tuples)
            score = (w[0]*anom_val + w[1]*lr_val + w[2]*xgb_val)
            for t in [0.6, 0.7, 0.8, 0.85]:
                preds = (score > t).astype(int)
                f1 = f1_score(y_val, preds)
                if f1 > best_f1:
                    best_f1 = f1
                    best_w = w
                    best_t = t
                    
        print(f"   Best Weights: {best_w} | Best Threshold: {best_t} | Val F1: {best_f1:.3f}")

        # Save
        print(f"💾 [5/5] Saving Artifacts to {self.model_dir}...")
        with open(os.path.join(self.model_dir, "isolation_forest.pkl"), "wb") as f:
            pickle.dump(iso, f)
        with open(os.path.join(self.model_dir, "logistic_regression.pkl"), "wb") as f:
            pickle.dump(logreg, f)
        with open(os.path.join(self.model_dir, "xgboost.pkl"), "wb") as f:
            pickle.dump(xgb, f)
            
        config = {
            "weights": best_w,
            "threshold": best_t,
            "anomaly_threshold": 0.5,
            "feature_names": feature_names
        }
        with open(os.path.join(self.model_dir, "ensemble_config.pkl"), "wb") as f:
            pickle.dump(config, f)
            
        print("✅ Training Complete!")

if __name__ == "__main__":
    try:
        pipeline = TrainingPipeline()
        pipeline.train()
    except KeyboardInterrupt:
        print("\n🛑 Training stoped by user.")
