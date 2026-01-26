import json
import os
from datetime import datetime

class AutoTuner:
    def __init__(self, checkpoint_path='checkpoints/weights/'):
        self.checkpoint_path = checkpoint_path
        self.review_history = []
        self.tune_interval = 100  # Reviews per tune
        if not os.path.exists(self.checkpoint_path):
            os.makedirs(self.checkpoint_path)
    
    def collect_review(self, features, verdict):
        """Track which features fired on TP/FP"""
        self.review_history.append({
            'features': features,
            'verdict': verdict,
            'timestamp': datetime.utcnow()
        })
        
        if len(self.review_history) >= self.tune_interval:
            self.tune_weights()
    
    def tune_weights(self):
        """Adjust weights based on feature performance"""
        feature_stats = self._compute_precision()
        
        adjustments = {}
        for feature, stats in feature_stats.items():
            total = stats['tp'] + stats['fp']
            if total == 0: continue
            
            precision = stats['tp'] / total
            
            if precision < 0.7:
                adjustments[feature] = 0.9  # Reduce weight
            elif precision > 0.85:
                adjustments[feature] = 1.1  # Increase weight
        
        if adjustments:
             self._update_weights(adjustments)
             self._checkpoint()
             # Clear history after tuning? Spec doesn't say, but usually yes for windows
             self.review_history = [] 

    def _compute_precision(self):
        """Calculate TP/FP per feature"""
        stats = {}
        for review in self.review_history:
            for feature, value in review['features'].items():
                if value > 0:  # Feature fired (normalized value > 0)
                    if feature not in stats:
                        stats[feature] = {'tp': 0, 'fp': 0}
                    
                    if review['verdict'] == 'suspicious':
                        stats[feature]['tp'] += 1
                    else:
                        stats[feature]['fp'] += 1
        return stats

    def _update_weights(self, adjustments):
        # In a real app, this would load current weights, apply math, and save.
        print(f"[AutoTuner] Suggesting weight adjustments: {adjustments}")
        pass

    def _checkpoint(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        path = os.path.join(self.checkpoint_path, f"auto_tuned_{timestamp}.json")
        # Save snapshot logic here
        pass
