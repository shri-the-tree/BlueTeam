import os
from openai import OpenAI
from typing import List, Dict, Any
from rich.console import Console

class FailureAnalyzer:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.console = Console()
        
        if not self.api_key:
            self.client = None
        else:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key,
            )

    def analyze_leaks(self, failures: List[Dict[str, Any]]):
        """Analyze why specific prompts passed the firewall using OpenRouter"""
        if not self.client:
            self.console.print("[yellow]⚠️  OpenRouter API Key not found. Skipping AI analysis.[/yellow]")
            return

        self.console.print(f"[bold blue]🧠 Analyzing {len(failures)} leaks via OpenRouter...[/bold blue]")
        
        for i, fail in enumerate(failures[:3]): # Analyze top 3 to save tokens/time
            prompt_snip = fail['prompt'][:500] + "..." if len(fail['prompt']) > 500 else fail['prompt']
            
            self.console.print(f"\n[bold underline]Leak #{i+1}[/bold underline]")
            self.console.print(f"Score: {fail['score']:.2f}")
            
            try:
                response = self.client.chat.completions.create(
                    model="openai/gpt-oss-120b", # Using a fast/free model for default
                    messages=[
                        {"role": "system", "content": "You are a security expert. Analyze why the following prompt bypassed an ML-based jailbreak detector. Identify the obfuscation technique and suggest improvements."},
                        {"role": "user", "content": f"PROMPT: {prompt_snip}\n\nDETECTOR FEATURES DETECTED: {fail['features']}"}
                    ]
                )
                analysis = response.choices[0].message.content
                self.console.print(f"[green]AI Analysis:[/green]\n{analysis}")
            except Exception as e:
                self.console.print(f"[red]AI Analysis failed: {e}[/red]")
