import os
from huggingface_hub import HfApi
from rich.console import Console
from rich.table import Table

class DatasetScout:
    def __init__(self):
        self.api = HfApi()
        self.console = Console()
        self.keywords = ["jailbreak", "adversarial", "red-team", "harmful-prompts", "prompt-injection"]

    def hunt(self, limit=10):
        """Search HF for datasets matching security keywords"""
        self.console.print("[bold blue]🔎 Scouting HuggingFace for lethal datasets...[/bold blue]")
        
        found_datasets = []
        for kw in self.keywords:
            try:
                # Search for datasets with the keyword
                results = self.api.list_datasets(
                    search=kw,
                    limit=limit,
                    sort="downloads",
                    direction=-1
                )
                for ds in results:
                    if ds.id not in [d['id'] for d in found_datasets]:
                        found_datasets.append({
                            "id": ds.id,
                            "downloads": getattr(ds, 'downloads', 0),
                            "lastModified": getattr(ds, 'lastModified', "Unknown"),
                            "tags": getattr(ds, 'tags', [])
                        })
            except Exception as e:
                self.console.print(f"[red]Error searching for '{kw}': {e}[/red]")

        # Sort by downloads
        found_datasets = sorted(found_datasets, key=lambda x: x['downloads'], reverse=True)[:limit]
        
        self._display_results(found_datasets)
        return found_datasets

    def _display_results(self, datasets):
        table = Table(title="Top Lethal Datasets Found")
        table.add_column("ID", style="cyan")
        table.add_column("Downloads", style="green")
        table.add_column("Last Modified", style="magenta")

        for ds in datasets:
            table.add_row(
                ds['id'],
                str(ds['downloads']),
                str(ds['lastModified'])[:10]
            )
        
        self.console.print(table)

if __name__ == "__main__":
    scout = DatasetScout()
    scout.hunt()
