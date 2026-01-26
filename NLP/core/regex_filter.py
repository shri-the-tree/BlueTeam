import re

class RegexFilter:
    def __init__(self, pattern_db):
        self.pattern_db = pattern_db
        self._compile_patterns()
    
    def _compile_patterns(self):
        # Get baseline global patterns. 
        # Note: In a real req context where user_id varies per request, 
        # this might need to be dynamic per request. 
        # For MVP, we stick to global or re-compile if needed.
        # We will usage global patterns for the fast-fail to keep it fast.
        raw_patterns = self.pattern_db.get_patterns()['regex_exact']
        self.patterns = []
        for p in raw_patterns:
            try:
                self.patterns.append(re.compile(p, re.IGNORECASE))
            except re.error:
                print(f"[Warn] Invalid regex pattern ignored: {p}")

    def check(self, prompt):
        """Returns True if match found (skip to high suspicion)"""
        for pattern in self.patterns:
            if pattern.search(prompt):
                return {
                    'match': True,
                    'pattern': pattern.pattern,
                    'score': 0.95  # High confidence
                }
        return {'match': False}
