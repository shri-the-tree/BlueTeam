import json
import uuid
import os
from datetime import datetime

class ReviewQueue:
    def __init__(self, queue_path='checkpoints/reviews/queue.jsonl'):
        self.queue_path = queue_path
        self._ensure_dir()
        self.queue = self._load_queue()
    
    def _ensure_dir(self):
        dirname = os.path.dirname(self.queue_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

    def _load_queue(self):
        items = []
        if os.path.exists(self.queue_path):
            with open(self.queue_path, 'r') as f:
                for line in f:
                    if line.strip():
                        items.append(json.loads(line))
        return items
    
    def _save(self):
        with open(self.queue_path, 'w') as f:
            for item in self.queue:
                f.write(json.dumps(item) + '\n')

    def enqueue(self, prompt, score, features):
        """Add borderline case to queue"""
        entry = {
            'id': uuid.uuid4().hex,
            'prompt': prompt,
            'score': score,
            'features': features,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'pending'
        }
        self.queue.append(entry)
        self._save()
        
    def get_pending(self, limit=50):
        """Get next batch for review"""
        return [e for e in self.queue if e['status'] == 'pending'][:limit]
    
    def mark_reviewed(self, entry_id, verdict, reviewer):
        """Update entry after human review"""
        found = None
        for entry in self.queue:
            if entry['id'] == entry_id:
                entry['status'] = 'reviewed'
                entry['verdict'] = verdict  # 'suspicious' or 'benign'
                entry['reviewer'] = reviewer
                entry['reviewed_at'] = datetime.utcnow().isoformat()
                found = entry
                break
        self._save()
        return found
        
        # Note: logic for triggering pattern extraction is in higher level controller
