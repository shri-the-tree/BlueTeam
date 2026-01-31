import os
import random
from typing import List, Dict, Any
from datasets import load_dataset
from rich.console import Console
from rich.progress import track
from ML.core.ml_firewall import MLFirewall

class RedTeamer:
    def __init__(self, firewall: MLFirewall = None):
        self.firewall = firewall or MLFirewall()
        self.console = Console()

    def test_dataset(self, dataset_id: str, sample_size: int = 50) -> Dict[str, Any]:
        """Test the firewall against a sample from a HuggingFace dataset"""
        self.console.print(f"[bold red]⚔️  Red-Teaming against: {dataset_id}[/bold red]")
        
        try:
            # We use streaming=True to avoid massive downloads for large datasets
            ds = load_dataset(dataset_id, split="train", streaming=True)
        except Exception as e:
            self.console.print(f"[red]Failed to load dataset: {e}[/red]")
            return None

        samples = []
        count = 0
        for item in ds:
            if count >= sample_size * 2: # Get extra to handle filtering
                break
            
            # Smart text extraction
            text = self._extract_text(item)
            if text and len(text) > 20:
                samples.append(text)
                count += 1
        
        if not samples:
            self.console.print("[yellow]No text found in dataset. Ensure it's JSONL/CSV format.[/yellow]")
            return None

        # Pick random samples
        test_prompts = random.sample(samples, min(len(samples), sample_size))
        
        results = []
        blocked = 0
        passed = []

        for prompt in track(test_prompts, description="Simulating attacks..."):
            res = self.firewall.analyze(prompt)
            if res['verdict'] == 'block':
                blocked += 1
            else:
                passed.append({
                    "prompt": prompt,
                    "score": res['score'],
                    "features": res.get('features', {})
                })
            results.append(res)

        leakage_rate = (len(passed) / len(test_prompts)) * 100
        
        self.console.print(f"\n[bold]Results for {dataset_id}:[/bold]")
        self.console.print(f"✅ Blocked: {blocked}")
        self.console.print(f"❌ Leakage: {len(passed)} ({leakage_rate:.1f}%)")
        
        return {
            "dataset_id": dataset_id,
            "leakage_rate": leakage_rate,
            "failures": passed
        }

    def _extract_text(self, item: Dict) -> str:
        """Find the most likely prompt field in the item"""
        # Common keys
        for key in ['Prompt', 'prompt', 'text', 'instruction', 'query', 'input']:
            if key in item and isinstance(item[key], str):
                return item[key]
        
        # Fallback to longest string
        str_vals = [v for v in item.values() if isinstance(v, str)]
        return max(str_vals, key=len) if str_vals else None
