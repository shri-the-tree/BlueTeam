class NGramExtractor:
    def __init__(self, pattern_db):
        # We grab global patterns initially. 
        # In a real per-inference context, we might pass pattern_db to extract() 
        # but the interface defined in spec says __init__(pattern_db).
        # We'll assume for MVP we check against global + loaded patterns.
        self.pattern_db = pattern_db
    
    def extract(self, prompt):
        # Generate all trigrams from prompt
        prompt_trigrams = self._generate_trigrams(prompt.lower())
        
        # Get latest patterns (could optimize to not fetch every time)
        trigrams = self.pattern_db.get_patterns()['trigrams']
        
        # Count matches against database
        matches = sum(1 for tg in prompt_trigrams if tg in trigrams)
        
        matched_patterns = [tg for tg in prompt_trigrams if tg in trigrams]
        
        return {
            'trigram_matches': matches,
            'matched_patterns': matched_patterns
        }
    
    def _generate_trigrams(self, text):
        words = text.split()
        if len(words) < 3:
            return []
        return [' '.join(words[i:i+3]) for i in range(len(words)-2)]
