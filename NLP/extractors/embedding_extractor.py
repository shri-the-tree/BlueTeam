import numpy as np
from scipy.spatial.distance import cosine

class EmbeddingExtractor:
    def __init__(self, pattern_db):
        self.model = pattern_db.embedding_model
        # Use default if not present
        self.attack_prototype = np.array(pattern_db.get_patterns().get('embedding_prototype', [0]*300))
    
    def extract(self, prompt):
        words = [w.lower() for w in prompt.split() if w.isalpha()]
        valid_words = [w for w in words if w in self.model]
        
        if not valid_words:
            return {'embedding_similarity': 0.0}
        
        # Get vectors
        vectors = [self.model[w] for w in valid_words]
        prompt_vector = np.mean(vectors, axis=0)
        
        # Check dimensions
        if len(prompt_vector) != len(self.attack_prototype):
             # Fallback if dimensions mismatch (e.g. mock model vs real config)
             return {'embedding_similarity': 0.0}

        try:
            similarity = 1 - cosine(prompt_vector, self.attack_prototype)
        except ValueError:
             # handle zero vector
             similarity = 0.0
             
        return {'embedding_similarity': float(similarity)}
