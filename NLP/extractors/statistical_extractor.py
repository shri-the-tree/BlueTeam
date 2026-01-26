from textstat import flesch_kincaid_grade
from collections import Counter

class StatisticalExtractor:
    def extract(self, prompt):
        words = prompt.split()
        
        return {
            'char_count': len(prompt),
            'word_count': len(words),
            'fk_grade': self._safe_fk_grade(prompt),
            'special_char_ratio': self._special_char_ratio(prompt),
            'repetition_ratio': self._repetition_ratio(words)
        }
    
    def _safe_fk_grade(self, text):
        try:
            return flesch_kincaid_grade(text)
        except:
            return 0.0
            
    def _special_char_ratio(self, text):
        special = sum(1 for c in text if not c.isalnum() and c != ' ')
        return special / len(text) if len(text) > 0 else 0
    
    def _repetition_ratio(self, words):
        if not words:
            return 0
        most_common = Counter([w.lower() for w in words]).most_common(1)[0]
        return most_common[1] / len(words)
