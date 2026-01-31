import os
import sys
import argparse
import json
from rich.console import Console
from rich.panel import Panel
from ML.manager.scout import DatasetScout
from ML.manager.tester import RedTeamer
from ML.manager.analyzer import FailureAnalyzer
from ML.training.train_pipeline import TrainingPipeline

class BlueManager:
    def __init__(self):
        self.console = Console()
        self.scout = DatasetScout()
        self.red_teamer = RedTeamer()
        self.analyzer = FailureAnalyzer()
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def run(self):
        parser = argparse.ArgumentParser(description="BlueTeam ML Manager: The Autonomous Defense Agent")
        subparsers = parser.add_subparsers(dest="command")

        # Command: Hunt
        subparsers.add_parser("hunt", help="Search HuggingFace for new lethal datasets")

        # Command: Test
        test_parser = subparsers.add_parser("test", help="Stress test existing firewall against a dataset")
        test_parser.add_argument("dataset_id", help="HuggingFace Dataset ID")
        test_parser.add_argument("--samples", type=int, default=30, help="Number of samples to test")

        # Command: Ingest
        ingest_parser = subparsers.add_parser("ingest", help="Pull a dataset and add it to our training pool")
        ingest_parser.add_argument("dataset_id", help="HuggingFace Dataset ID")
        ingest_parser.add_argument("--limit", type=int, default=500, help="Max items to ingest")

        # Command: Train
        subparsers.add_parser("train", help="Trigger a full retraining of the ML models")

        args = parser.parse_args()

        if args.command == "hunt":
            datasets = self.scout.hunt()
            self.console.print("\n[yellow]Advice:[/yellow] Use [bold]blue-manager test <dataset_id>[/bold] to see if your current firewall holds up.")

        elif args.command == "test":
            results = self.red_teamer.test_dataset(args.dataset_id, sample_size=args.samples)
            if results and results['failures']:
                choice = input("\nWould you like to analyze these leaks with OpenRouter? (y/n): ")
                if choice.lower() == 'y':
                    self.analyzer.analyze_leaks(results['failures'])
                
                choice = input("\nWould you like to ingest this dataset for reinforcement? (y/n): ")
                if choice.lower() == 'y':
                    self.ingest(args.dataset_id)

        elif args.command == "ingest":
            self.ingest(args.dataset_id, args.limit)

        elif args.command == "train":
            pipeline = TrainingPipeline()
            pipeline.train()

        else:
            parser.print_help()

    def ingest(self, dataset_id: str, limit: int = 500):
        """Pull data from HF and save to DataExtractor/data for retraining"""
        self.console.print(f"[bold green]📥 Ingesting {dataset_id}...[/bold green]")
        from datasets import load_dataset
        
        try:
            ds = load_dataset(dataset_id, split="train", streaming=True)
            output_file = os.path.join(self.root_dir, "DataExtractor", "data", f"ingested_{dataset_id.replace('/', '_')}.jsonl")
            
            count = 0
            with open(output_file, 'w', encoding='utf-8') as f:
                for item in ds:
                    if count >= limit: break
                    f.write(json.dumps(item) + "\n")
                    count += 1
            
            self.console.print(f"[bold green]✅ Success![/bold green] Saved {count} items to {output_file}")
            self.console.print("[yellow]Tip:[/yellow] Run [bold]blue-manager train[/bold] to apply these new lessons.")
        except Exception as e:
            self.console.print(f"[red]Ingestion failed: {e}[/red]")

if __name__ == "__main__":
    manager = BlueManager()
    manager.run()
