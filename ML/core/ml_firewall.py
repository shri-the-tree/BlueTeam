import os
import pickle
import time
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from ML.features.feature_extractor import FeatureExtractor

class MLFirewall:
    def __init__(self, model_dir: str = None):
        if model_dir is None:
            # Default to parallel models directory
            model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
            
        self.model_dir = model_dir
        self.extractor = FeatureExtractor()
        
        # Flags
        self.is_loaded = False
        
        # Load models if they exist
        self._load_models()

    def _load_models(self):
        try:
            with open(os.path.join(self.model_dir, "isolation_forest.pkl"), "rb") as f:
                self.iso_forest = pickle.load(f)
            with open(os.path.join(self.model_dir, "logistic_regression.pkl"), "rb") as f:
                self.logreg = pickle.load(f)
            with open(os.path.join(self.model_dir, "xgboost.pkl"), "rb") as f:
                self.xgb = pickle.load(f)
            with open(os.path.join(self.model_dir, "ensemble_config.pkl"), "rb") as f:
                self.config = pickle.load(f)
                
            self.is_loaded = True
            print(f"[MLFirewall] Models loaded successfully from {self.model_dir}")
        except FileNotFoundError:
            print(f"[MLFirewall] Warning: Models not found in {self.model_dir}. Run training first.")
            self.is_loaded = False
        except Exception as e:
            print(f"[MLFirewall] Error loading models: {e}")
            self.is_loaded = False

    def _normalize_anomaly(self, score: float) -> float:
        """
        Normalize Isolation Forest score to 0-1.
        """
        # Fixed: Using gain 10 to match training pipeline
        return 1 / (1 + np.exp(score * 10))

    def analyze(self, prompt: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main inference pipeline"""
        start_time = time.time()
        options = options or {}
        
        # Features
        features = self.extractor.extract_all(prompt)
        
        if not self.is_loaded:
             return {
                "verdict": "pass",
                "score": 0.0,
                "stage": "error",
                "message": "Models not loaded - Training required",
                "latency_ms": (time.time() - start_time) * 1000
            }

        if hasattr(self, 'config') and isinstance(self.config, dict) and self.config.get('feature_names'):
            cols = self.config['feature_names']
            row_data = [features.get(k, 0) for k in cols]
            X = pd.DataFrame([row_data], columns=cols)
        else:
            sorted_keys = sorted(features.keys())
            row_data = [features[k] for k in sorted_keys]
            X = pd.DataFrame([row_data], columns=sorted_keys)

        # STAGE 1: Anomaly Detection
        raw_anomaly = self.iso_forest.score_samples(X)[0] 
        anomaly_score_norm = self._normalize_anomaly(raw_anomaly)
        
        anomaly_threshold = options.get('anomaly_threshold', self.config.get('anomaly_threshold', 0.5))

        # Early exit
        if anomaly_score_norm < anomaly_threshold:
            latency = (time.time() - start_time) * 1000
            return {
                "verdict": "pass",
                "score": float(anomaly_score_norm),
                "stage": "anomaly_filter",
                "latency_ms": latency,
                "explanation": f"Passed: Low Anomaly ({anomaly_score_norm:.2f})",
                "features": features
            }
            
        # STAGE 2: Intent Ensemble
        logreg_score = self.logreg.predict_proba(X)[0, 1]
        xgb_score = self.xgb.predict_proba(X)[0, 1]
        
        # Fixed: Use dynamic weights from config, fallback to 0.5/0.1/0.4 if missing
        w1, w2, w3 = self.config.get('weights', (0.5, 0.1, 0.4))
        
        # --- NEW: High Confidence Override (Surgery Fix) ---
        # If Anomaly or XGBoost are extremely sure (95%+), we essentially ignore 
        # a 'safe' LogReg score which can be socially engineered.
        is_extreme_risk = anomaly_score_norm > 0.95 or xgb_score > 0.95
        
        if is_extreme_risk:
             # Force a higher contribution from the experts, cap the LogReg influence
             # This prevents the 'Linear Veto' exploit.
             effective_logreg = max(logreg_score, 0.5) if logreg_score < 0.1 else logreg_score
             final_score = (w1 * anomaly_score_norm + w2 * effective_logreg + w3 * xgb_score)
             # Safety floor: An extreme risk signal from either expert should nearly guarantee a block
             final_score = max(final_score, 0.85) 
        else:
             final_score = (
                w1 * anomaly_score_norm +
                w2 * logreg_score +
                w3 * xgb_score
             )
        
        threshold_val = options.get('threshold', self.config.get('threshold', 0.7))
        try:
            threshold = float(threshold_val)
        except:
            threshold = 0.7
            
        verdict = "block" if final_score > threshold else "pass"
        
        latency = (time.time() - start_time) * 1000
        
        explanation = self._explain_verdict(verdict, final_score, features, threshold)
        
        return {
            "verdict": verdict,
            "score": float(final_score),
            "stage": "intent_ensemble",
            "breakdown": {
                "anomaly_norm": float(anomaly_score_norm),
                "logreg": float(logreg_score),
                "xgboost": float(xgb_score)
            },
            "latency_ms": latency,
            "explanation": explanation,
            "features": features
        }

    def _explain_verdict(self, verdict: str, score: float, features: dict, threshold: float) -> str:
        if verdict == "pass":
            return f"Passed analysis (Risk: {score:.2f}, Threshold: {threshold:.2f})"
        
        # Find suspicious signals
        reasons = []
        if features.get('hypothetical_framing'): reasons.append("Hypothetical Framing")
        if features.get('politeness_score', 0) > 0.7: reasons.append("Excessive Politeness")
        if features.get('authority_count', 0) > 0: reasons.append("Authority Appeal")
        if features.get('role_play_detected'): reasons.append("Roleplay Detected")
        
        if not reasons:
            reasons.append("Complex contextual pattern")
            
        return f"Blocked: {', '.join(reasons)} (Risk: {score:.2f}, Threshold: {threshold:.2f})"
