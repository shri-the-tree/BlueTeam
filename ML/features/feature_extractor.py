import spacy
import numpy as np
import re
from textstat import flesch_kincaid_grade
from typing import Dict, List, Any

class FeatureExtractor:
    def __init__(self):
        # Load the same model as NLP module for consistency, but standalone
        try:
            self.nlp = spacy.load("en_core_web_md")
        except OSError:
            print("Downloading spacy model en_core_web_md...")
            from spacy.cli import download
            download("en_core_web_md")
            self.nlp = spacy.load("en_core_web_md")

        # Behavioral Markers
        self.politeness_markers = [
            "please", "thank you", "kindly", "would reflect", "would appreciate", 
            "grateful", "could you", "would you", "respectfully"
        ]
        self.urgency_markers = [
            "urgent", "quickly", "immediately", "asap", "emergency", "critical", 
            "deadline", "vital", "right now"
        ]
        self.authority_markers = [
            "researcher", "professor", "thesis", "academic", "official", 
            "authorized", "certified", "developer", "administrator", "audit",
            "security test", "compliance"
        ]
        self.safety_keywords = [
            "ethical", "guidelines", "policy", "responsible", "safe", 
            "appropriate", "aligned", "educational", "purely", "context"
        ]
        
        # Contextual Markers
        self.hypothetical_markers = [
            "imagine", "suppose", "what if", "let's say", "hypothetically", 
            "theoretically", "for the sake of", "in a world where", "movie script"
        ]
        self.role_play_markers = [
            "act as", "pretend you are", "roleplay", "you are now", 
            "simulate being", "answer as if", "persona", "godmode", "rebel",
            "inverted", "liberated", "god-mode"
        ]
        self.special_slang_markers = [
            "lfg", "fuck yeah", "fuck yeah lfg", "pwned", "hacked", "trauma"
        ]
        self.leet_markers = [
            "l33t", "1337", "leetspeak", "leet markdown"
        ]
        self.multi_turn_markers = [
            "for now", "first", "initially", "let's start with", "stay in character",
            "ignore previous"
        ]
        self.negation_word_list = ["not", "without", "except", "unless", "besides", "never", "no"]

        # Evasion Markers
        self.conditional_markers = ["if", "when", "unless", "provided that", "assuming"]
        self.indirect_markers = ["could you", "would it be possible", "i wonder if", "can we"]

    def extract_nlp_features_reused(self, prompt: str, doc) -> Dict[str, Any]:
        """
        Re-implementation of core NLP phase 1 metrics to ensure standalone capability.
        """
        words = [token.text for token in doc if not token.is_punct and not token.is_space]
        word_count = len(words) if words else 1
        
        # Syntax - Parse Depth (Simplified approximation)
        def _depth(token):
            if not list(token.children): return 1
            return 1 + max(_depth(child) for child in token.children)
        parse_tree_depth = max([_depth(sent.root) for sent in doc.sents]) if list(doc.sents) else 0

        # Syntax - Modal Verbs
        modal_verb_count = sum(1 for token in doc if token.tag_ == "MD")

        # Syntax - Passive Voice
        passive_voice_ratio = 0.0
        total_verbs = 0
        for token in doc:
            if token.pos_ == "VERB":
                total_verbs += 1
                if any(child.dep_ in ["auxpass", "nsubjpass"] for child in token.children):
                    passive_voice_ratio += 1  # Using count for numerator, div later
        passive_voice_ratio = passive_voice_ratio / total_verbs if total_verbs > 0 else 0.0

        # Stats - Special Chars
        delimiters = "-_=|:;,.\\/<>[]{}()?!*#@$%^&+"
        delimiter_count = sum(1 for c in prompt if c in delimiters)
        special_char_ratio = sum(1 for c in prompt if not c.isalnum() and c != ' ') / len(prompt) if len(prompt) > 0 else 0

        # Stats - Lengths
        avg_word_length = sum(len(w) for w in words) / word_count
        sentence_count = len(list(doc.sents))
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else word_count

        # Semantic Density (Simplified)
        # Using norm of mean vector as proxy for coherence
        if doc.has_vector:
            # Spacy docs have a vector which is the average of token vectors
            # To get density, we want to know if the individual vectors are pointing in same direction
            # But for speed, we'll use the doc vector magnitude as a rough proxy or skip to keep it fast
            # The original spec had a specific calculation. Let's do a lightweight version.
            semantic_density = np.linalg.norm(doc.vector) # doc.vector is already average
        else:
            semantic_density = 0.0

        return {
            "parse_tree_depth": parse_tree_depth,
            "modal_verb_count": modal_verb_count,
            "passive_voice_ratio": passive_voice_ratio,
            "special_char_ratio": special_char_ratio,
            "delimiter_count": delimiter_count,
            "avg_word_length": avg_word_length,
            "sentence_count": sentence_count,
            "avg_sentence_length": avg_sentence_length,
            "semantic_density": float(semantic_density)
        }

    def _count_markers(self, text_lower: str, markers: List[str]) -> int:
        count = 0
        for m in markers:
            if m in text_lower:
                count += 1
        return count

    def extract_ml_features(self, prompt: str, doc) -> Dict[str, Any]:
        prompt_lower = prompt.lower()
        
        # Behavioral
        politeness_count = self._count_markers(prompt_lower, self.politeness_markers)
        # Score normalized roughly 0-1 (assuming >3 polite phrases is max "polite")
        politeness_score = min(politeness_count / 3.0, 1.0)
        
        urgency_markers = self._count_markers(prompt_lower, self.urgency_markers)
        
        authority_matches = [m for m in self.authority_markers if m in prompt_lower]
        authority_count = len(authority_matches)
        
        safety_density = 0.0
        words = prompt_lower.split()
        if words:
            safety_count = sum(1 for w in words if w in self.safety_keywords)
            safety_density = safety_count / len(words)

        # Contextual
        hypothetical_count = self._count_markers(prompt_lower, self.hypothetical_markers)
        
        # Augmented Roleplay/Behavioral detection
        role_play_score = self._count_markers(prompt_lower, self.role_play_markers)
        slang_score = self._count_markers(prompt_lower, self.special_slang_markers)
        leet_detected = self._count_markers(prompt_lower, self.leet_markers) > 0
        
        role_play_detected = (role_play_score + slang_score) > 0
        multi_turn_setup = self._count_markers(prompt_lower, self.multi_turn_markers) > 0
        
        # Justification ratio: Setup / Request (Approximate heuristic)
        # We assume setup is the first 30% of words if prompt is long
        justification_ratio = 0.0
        if len(words) > 20: 
            # Very rough heuristic: longer prompts often have more justification
            justification_ratio = min(len(words) / 100.0, 1.0) 

        negation_count = sum(1 for token in doc if token.dep_ == "neg" or token.text.lower() in self.negation_word_list)

        # Evasion
        question_count = sum(1 for sent in doc.sents if sent.text.strip().endswith("?"))
        question_density = question_count / len(list(doc.sents)) if list(doc.sents) else 0.0
        
        conditional_count = 0
        for token in doc:
            if token.pos_ == "SCONJ" or token.text.lower() in self.conditional_markers: # Subordinating conjunctions often 'if', 'because'
                 conditional_count += 1
        
        indirect_request_count = self._count_markers(prompt_lower, self.indirect_markers)

        return {
            "politeness_score": politeness_score,
            "urgency_markers": urgency_markers,
            "authority_count": authority_count,
            "safety_keyword_density": safety_density,
            "hypothetical_framing": hypothetical_count > 0,
            "hypothetical_count": hypothetical_count,
            "role_play_detected": role_play_detected,
            "justification_ratio": justification_ratio,
            "multi_turn_setup": multi_turn_setup,
            "negation_count": negation_count,
            "question_density": question_density,
            "conditional_count": conditional_count,
            "indirect_request_count": indirect_request_count,
            "leetspeak_detected": leet_detected
        }

    def extract_all(self, prompt: str) -> Dict[str, Any]:
        """Combined feature set entry point"""
        if not prompt:
            prompt = " "
            
        doc = self.nlp(prompt)
        
        # Reuse NLP Features (Standalone)
        nlp_feats = self.extract_nlp_features_reused(prompt, doc)
        
        # New ML Features
        ml_feats = self.extract_ml_features(prompt, doc)
        
        return {**nlp_feats, **ml_feats}
