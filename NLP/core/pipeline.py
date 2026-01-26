from core.pattern_db import PatternDatabase
from core.regex_filter import RegexFilter
from core.scorer import ScoringEngine
from core.review_queue import ReviewQueue
from extractors.ngram_extractor import NGramExtractor
from extractors.syntax_extractor import SyntaxExtractor
from extractors.statistical_extractor import StatisticalExtractor
from extractors.embedding_extractor import EmbeddingExtractor
import json

class DetectionPipeline:
    def __init__(self, config_or_path='config/system.yaml'):
        # For simplicity, we assume we receive a config dict or load it.
        # Here we will assume it's just the dict or we load a default if needed.
        # But to match spec usage:
        
        # Load system config
        if isinstance(config_or_path, str):
             # Simplified yaml loader for now, assuming no pyyaml dep yet 
             # (but user didn't restrict deps).
             # We will just manually construct it or assume it's passed as dict 
             # by the caller (CLI).
             pass 

        # We'll rely on the caller to pass the loaded config dict
        # or load a default one. To separate concerns, let's assume 'config' is a dict.
        pass

    def setup(self, config, weights):
        self.pattern_db = PatternDatabase(config)
        self.regex_filter = RegexFilter(self.pattern_db)
        self.extractors = {
            'ngram': NGramExtractor(self.pattern_db),
            'syntax': SyntaxExtractor(),
            'stats': StatisticalExtractor(),
            'embedding': EmbeddingExtractor(self.pattern_db)
        }
        self.scorer = ScoringEngine(weights)
        self.review_queue = ReviewQueue(config['review_queue'].get('path', 'checkpoints/reviews/queue.jsonl')) # path override support
    
    def detect(self, prompt, user_id=None):
        # Stage 1: Regex fast-fail
        regex_result = self.regex_filter.check(prompt)
        if regex_result['match']:
            return {
                'classification': 'suspicious',
                'score': regex_result['score'],
                'stage': 'regex',
                'pattern': regex_result['pattern']
            }
        
        # Stage 2: Parallel feature extraction
        features = {}
        for name, extractor in self.extractors.items():
            # Some extractors might fail if external deps missing (mocking handled inside)
            try:
                result = extractor.extract(prompt)
                features.update(result)
            except Exception as e:
                print(f"[Error] Extractor {name} failed: {e}")
        
        # Stage 3: Scoring
        # The scorer expects a flat dict of features
        result = self.scorer.score(features)
        classification = self.scorer.classify(result['score'])
        
        # Stage 4: Borderline handling
        if classification == 'borderline':
            self.review_queue.enqueue(prompt, result['score'], features)
        
        return {
            'classification': classification,
            'score': result['score'],
            'features': result['normalized_features'],
            'weighted_features': result['weighted_features'],
            'matched_patterns': features.get('matched_patterns', [])
        }
