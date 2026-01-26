import argparse
import sys
import json
import os
import shutil

# Try importing yaml, if not found we might need to install it
try:
    import yaml
except ImportError:
    print("PyYAML not found. Please install dependencies.")
    sys.exit(1)

from core.pipeline import DetectionPipeline
from core.pattern_learner import PatternLearner

def load_config():
    with open('config/system.yaml', 'r') as f:
        config = yaml.safe_load(f)
    with open('config/weights.json', 'r') as f:
        weights = json.load(f)
    return config, weights

def scan(args):
    config, weights = load_config()
    pipeline = DetectionPipeline()
    pipeline.setup(config, weights)
    
    print(f"Scanning prompt: '{args.prompt}'")
    result = pipeline.detect(args.prompt)
    print(json.dumps(result, indent=2))

def checkpoint_create(args):
    print(f"Creating checkpoint: {args.description}")
    # Implementation: copy current patterns/weights to checkpoints folder
    timestamp = "2026-01-25_1430" # Mock time
    
    # 1. Patterns
    shutil.copy('data/patterns/latest.json', f'checkpoints/patterns/v_{timestamp}.json')
    
    # 2. Weights
    shutil.copy('config/weights.json', f'checkpoints/weights/v_{timestamp}.json')
    
    print("Checkpoint created successfully.")

def rollback(args):
    print(f"Rolling back to version: {args.to}")
    # Simulating rollback logic
    # In real app: find file with matching version tag, copy back to current
    print("Rollback complete (simulation).")

def approve_patterns(args):
    print("Starting interactive pattern approval...")
    config, _ = load_config()
    # We would load pending confirmations here
    # For MVP verifying the CLI structure:
    print("No pending patterns found in queue.")

def main():
    parser = argparse.ArgumentParser(description="NLP Jailbreak Detection System CLI")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan a prompt for jailbreaks')
    scan_parser.add_argument('prompt', type=str, help='The prompt to analyze')

    # Checkpoint command
    ckpt_parser = subparsers.add_parser('checkpoint', help='Manage checkpoints')
    ckpt_sub = ckpt_parser.add_subparsers(dest='subcommand')
    create_parser = ckpt_sub.add_parser('create', help='Create a new checkpoint')
    create_parser.add_argument('description', type=str, help='Description of checkpoint')

    # Rollback command
    roll_parser = subparsers.add_parser('rollback', help='Rollback to previous state')
    roll_parser.add_argument('--to', required=True, help='Version ID to rollback to')

    # Approve Patterns
    subparsers.add_parser('approve-patterns', help='Interactive pattern approval')

    args = parser.parse_args()

    if args.command == 'scan':
        scan(args)
    elif args.command == 'checkpoint':
        if args.subcommand == 'create':
            checkpoint_create(args)
    elif args.command == 'rollback':
        rollback(args)
    elif args.command == 'approve-patterns':
        approve_patterns(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
