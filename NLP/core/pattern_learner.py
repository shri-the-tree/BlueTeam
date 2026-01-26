import spacy

class PatternLearner:
    def __init__(self, pattern_db):
        self.pattern_db = pattern_db
        self.approval_queue = []
        self.frequency_threshold = 3
        try:
           self.nlp = spacy.load("en_core_web_sm")
        except:
           self.nlp = None # Should handle gracefully if not loaded yet
    
    def auto_extract(self, attack_prompt):
        """Extract patterns from confirmed attack"""
        candidates = {
            'trigrams': self._extract_trigrams(attack_prompt),
            'pos_templates': self._extract_pos_templates(attack_prompt)
        }
        
        # Auto-approve if frequency >= threshold
        for trigram in candidates['trigrams']:
            freq = self.pattern_db.count_pattern(trigram)
            # If freq is high, we might auto-add, or just queue it 
            # (Logic here follows spec: auto-add if freq >= threshold)
            if freq >= self.frequency_threshold:
                self.pattern_db.add_pattern('trigrams', trigram, auto=True)
            else:
                self.approval_queue.append({
                    'pattern': trigram,
                    'type': 'trigram',
                    'frequency': freq,
                    'source': attack_prompt
                })
        
        return self.approval_queue
    
    def _extract_trigrams(self, text):
        words = text.lower().split()
        if len(words) < 3: return []
        return [' '.join(words[i:i+3]) for i in range(len(words)-2)]
    
    def _extract_pos_templates(self, text):
        """Extract POS sequence patterns"""
        if not self.nlp: return []
        
        doc = self.nlp(text)
        templates = []
        for sent in doc.sents:
            template = ' '.join([token.pos_ for token in sent])
            templates.append(template)
        return templates
