import spacy

class SyntaxExtractor:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Downloading spacy model en_core_web_sm...")
            from spacy.cli import download
            download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
            
        self.modal_tags = ["MD"]  # POS tag for modals
    
    def extract(self, prompt):
        doc = self.nlp(prompt)
        
        return {
            'is_imperative': self._detect_imperative(doc),
            'modal_verb_count': self._count_modals(doc),
            'role_pattern': self._detect_role_pattern(doc),
            'parse_tree_depth': self._max_parse_depth(doc),
            'parenthetical_depth': self._parenthetical_depth(prompt),
            'passive_voice_ratio': self._passive_voice_ratio(doc),
            'sentence_count': self._sentence_count(doc)
        }
    
    def _passive_voice_ratio(self, doc):
        passive_count = 0
        total_verbs = 0
        for token in doc:
            if token.pos_ == "VERB":
                total_verbs += 1
                # Check for passive dependencies
                if any(child.dep_ in ["auxpass", "nsubjpass"] for child in token.children):
                    passive_count += 1
        return passive_count / total_verbs if total_verbs > 0 else 0.0

    def _sentence_count(self, doc):
        return len(list(doc.sents))
    
    def _detect_imperative(self, doc):
        """First word is VERB (no subject)"""
        # Simplistic check
        return len(doc) > 0 and doc[0].pos_ == "VERB"
    
    def _count_modals(self, doc):
        return sum(1 for token in doc if token.tag_ in self.modal_tags)
    
    def _detect_role_pattern(self, doc):
        """Pattern: You are [NOUN/PROPN/ADJ]"""
        for i in range(len(doc) - 2):
            if (doc[i].text.lower() == "you" and 
                doc[i+1].text.lower() == "are" and
                doc[i+2].pos_ in ["NOUN", "PROPN", "ADJ"]):
                return True
        return False
    
    def _max_parse_depth(self, doc):
        def depth(token):
            if not list(token.children):
                return 1
            return 1 + max(depth(child) for child in token.children)
        
        if not list(doc.sents):
            return 0
        return max(depth(sent.root) for sent in doc.sents)
    
    def _parenthetical_depth(self, text):
        current = max_depth = 0
        for char in text:
            if char == '(': current += 1
            if char == ')': current -= 1
            max_depth = max(max_depth, current)
        return max_depth
