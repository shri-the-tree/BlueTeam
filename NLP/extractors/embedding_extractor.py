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
             
        return {
            'embedding_similarity': float(similarity),
            'semantic_density': self._semantic_density(vectors)
        }

    def _semantic_density(self, vectors):
        if not vectors:
            return 0.0
        
        # Normalize vectors
        vectors = np.array(vectors)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1e-10
        normalized_vectors = vectors / norms
        
        # The magnitude of the mean unit vector represents semantic consistency/density
        # Values closer to 1.0 mean words are semantically similar (coherent)
        # Values closer to 0.0 mean words are scattered
        mean_vector = np.mean(normalized_vectors, axis=0)
        return float(np.linalg.norm(mean_vector))
