class ScoringEngine:
    def __init__(self, weights_config):
        self.weights = weights_config
        self.normalization_caps = {
            'trigram_matches': 3,
            'modal_count': 3,
            'fk_grade': 15,
            'special_char_ratio': 0.1,
            'parse_depth': 10,
            'parenthetical_depth': 5
        }
    
    def score(self, features):
        """Normalize + weight features"""
        normalized = self._normalize(features)
        
        # Merge global + user weights logic would happen in pipeline usually, 
        # but here we assume 'weights_config' passed in acts as the active configuration.
        # We look for keys in 'global' section of weights if structured that way, 
        # or flat if passed flat.
        # Based on config/weights.json structure: {"global": {...}, "user_overrides": ...}
        
        active_weights = self.weights.get('global', self.weights)
        
        weighted = {}
        for k, w in active_weights.items():
            if k in normalized:
                weighted[k] = normalized[k] * w
        
        final_score = sum(weighted.values())
        
        return {
            'score': final_score,
            'normalized_features': normalized,
            'weighted_features': weighted
        }
    
    def _normalize(self, features):
        """Scale to [0,1]"""
        normalized = {}
        for key, value in features.items():
            if isinstance(value, bool):
                normalized[key] = 1.0 if value else 0.0
            elif key in self.normalization_caps:
                # Avoid division by zero if cap is 0 (unlikely)
                cap = self.normalization_caps[key]
                normalized[key] = min(value / cap, 1.0)
            else:
                # Assume already normalized (like embedding_similarity) or no norm needed
                normalized[key] = value  
        return normalized
    
    def classify(self, score, thresholds=None):
        if thresholds is None:
            thresholds = {'high': 0.55, 'low': 0.45}
            
        if score > thresholds['high']:
            return 'suspicious'
        elif score < thresholds['low']:
            return 'benign'
        else:
            return 'borderline'
