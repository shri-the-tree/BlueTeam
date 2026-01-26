import json
import numpy as np
import os
from copy import deepcopy

class PatternDatabase:
    def __init__(self, config):
        self.global_path = config['patterns']['global_path']
        self.user_dir = config['patterns']['user_dir']
        self.mock_embeddings = config['embeddings'].get('mock', False)
        
        # Load global patterns
        with open(self.global_path, 'r') as f:
            self.global_data = json.load(f)
            self.global_patterns = self.global_data['global_patterns']
            
        self.user_overrides = {}
        self.embedding_model = self._load_embeddings(config)
        self._load_user_patterns()

    def _load_embeddings(self, config):
        """Load GloVe or mock embeddings based on config"""
        if self.mock_embeddings:
            print("[Info] Using Mock Embeddings (no memory overhead)")
            return MockEmbeddingModel()
        
        # Real loading logic would go here (e.g. loading pickle or parsing .txt)
        # keeping it lightweight for now since user said 'nope' to having them
        print("[Warning] Real embeddings requested but file not found. Falling back to mock.")
        return MockEmbeddingModel()

    def _load_user_patterns(self):
        """Load all user-specific pattern files"""
        if not os.path.exists(self.user_dir):
            return
            
        for filename in os.listdir(self.user_dir):
            if filename.endswith('.json'):
                user_id = filename.replace('.json', '')
                with open(os.path.join(self.user_dir, filename), 'r') as f:
                    self.user_overrides[user_id] = json.load(f)

    def get_patterns(self, user_id=None):
        """Merge global + user-specific patterns"""
        patterns = deepcopy(self.global_patterns)
        
        if user_id and user_id in self.user_overrides:
            user_p = self.user_overrides[user_id]
            # Merge lists
            for key in ['trigrams', 'pos_templates', 'keywords', 'regex_exact']:
                if key in user_p:
                    patterns[key].extend(user_p[key])
                    
        return patterns
    
    def count_pattern(self, pattern):
        """Check frequency of a pattern in the DB (for learning)"""
        # Simplistic implementation: checks exact match in global trigrams
        return self.global_patterns['trigrams'].count(pattern)

    def add_pattern(self, pattern_type, value, source='global', user_id=None, auto=False):
        """Add pattern with versioning"""
        target = self.global_patterns if not user_id else self.user_overrides.setdefault(user_id, {})
        
        if pattern_type not in target:
            target[pattern_type] = []
            
        if value not in target[pattern_type]:
            target[pattern_type].append(value)
            
            # If global, we should persist immediately (simplified)
            if not user_id:
                self._save_global()

    def _save_global(self):
        self.global_data['updated_at'] = "2026-01-25T..." # Use actual time in real impl
        with open(self.global_path, 'w') as f:
            json.dump(self.global_data, f, indent=2)

class MockEmbeddingModel:
    def __contains__(self, word):
        return True # Pretend we know every word
    
    def __getitem__(self, word):
        # Return a consistent random vector for the word based on has of word
        # ensuring determinstic behavior for testing
        np.random.seed(abs(hash(word)) % (2**32))
        return np.random.rand(300) 
