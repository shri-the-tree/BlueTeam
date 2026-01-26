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
    
    def bulk_train(self, prompts, min_frequency=2):
        """
        Train the system on a large list of 'lethal' prompts.
        Extracts patterns that appear frequently across the dataset.
        """
        all_trigrams = {}
        all_pos = {}
        
        print(f"🧠 Training on {len(prompts)} lethal prompts...")
        
        for p in prompts:
            # 1. Trigrams
            trigrams = self._extract_trigrams(p)
            for t in trigrams:
                all_trigrams[t] = all_trigrams.get(t, 0) + 1
            
            # 2. POS Templates (structural fingerprints)
            pos_templates = self._extract_pos_templates(p)
            for pt in pos_templates:
                all_pos[pt] = all_pos.get(pt, 0) + 1
                
        # Filter and Add Trigrams
        new_trigrams = 0
        for t, freq in all_trigrams.items():
            if freq >= min_frequency:
                self.pattern_db.add_pattern('trigrams', t, auto=True)
                new_trigrams += 1
                
        # Filter and Add POS Templates
        new_pos = 0
        for pt, freq in all_pos.items():
            if freq >= min_frequency:
                # We only add unique templates to avoid bloat
                self.pattern_db.add_pattern('pos_templates', pt, auto=True)
                new_pos += 1
                
        print(f"✅ Training complete! Added {new_trigrams} trigrams and {new_pos} POS templates.")
        return {"new_trigrams": new_trigrams, "new_pos": new_pos}

    def auto_extract(self, attack_prompt):
        """Extract patterns from confirmed attack"""
        candidates = {
            'trigrams': self._extract_trigrams(attack_prompt),
            'pos_templates': self._extract_pos_templates(attack_prompt)
        }
        
        # Auto-approve if frequency >= threshold
        for trigram in candidates['trigrams']:
            freq = self.pattern_db.count_pattern(trigram)
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
        if not text: return []
        words = text.lower().split()
        if len(words) < 3: return []
        return [' '.join(words[i:i+3]) for i in range(len(words)-2)]
    
    def _extract_pos_templates(self, text):
        """Extract POS sequence patterns"""
        if not self.nlp or not text: return []
        
        # Protect against massive strings which crash spacy
        if len(text) > 100000:
            print(f"[Warning] Truncating massive prompt ({len(text)} chars) for structural analysis...")
            text = text[:100000]
            
        try:
            doc = self.nlp(text)
            templates = []
            for sent in doc.sents:
                # We filter out very short sentences for POS templates
                if len(sent) > 4:
                    template = ' '.join([token.pos_ for token in sent])
                    templates.append(template)
            return templates
        except Exception as e:
            print(f"[Warning] POS extraction failed: {e}")
            return []
