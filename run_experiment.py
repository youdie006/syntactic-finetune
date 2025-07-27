#!/usr/bin/env python3
"""
Experiment Runner - 태그 분류 실험을 실행하는 통합 스크립트
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.append('src')

from experiment_manager import ExperimentManager
from tag_strategy_engine import TagStrategyEngine


def run_experiment(experiment_name: str,
                  strategy_name: str = None,
                  categories: int = None,
                  description: str = "",
                  input_csv: str = "data_raw/legacy_sentence_analysis.csv",
                  auto_generate: bool = True) -> str:
    """
    Complete experiment workflow: create -> generate dataset -> ready for fine-tuning
    
    Args:
        experiment_name: Name of the experiment
        strategy_name: Tag strategy to use (mutually exclusive with categories)
        categories: Number of categories for dynamic strategy (mutually exclusive with strategy_name)
        description: Experiment description
        input_csv: Path to input CSV file
        auto_generate: Whether to automatically generate dataset
        
    Returns:
        Experiment ID
    """
    # Validate input parameters
    if strategy_name and categories:
        raise ValueError("Cannot specify both strategy_name and categories. Use one or the other.")
    if not strategy_name and not categories:
        raise ValueError("Must specify either strategy_name or categories.")
    
    # Initialize managers
    manager = ExperimentManager()
    tag_engine = TagStrategyEngine()
    
    # Handle dynamic strategy creation
    if categories:
        if not (2 <= categories <= 17):
            raise ValueError("Categories must be between 2 and 17.")
        
        print(f"🚀 Starting experiment: {experiment_name}")
        print(f"Dynamic strategy: {categories} categories")
        print("=" * 60)
        
        # Create dynamic strategy
        strategy_name = tag_engine.set_dynamic_strategy(categories, f"dynamic_{categories}cats_{experiment_name}")
        
        # Save dynamic strategy to file so subprocess can access it
        tag_engine.save_dynamic_strategy(strategy_name)
        
        # Update description if not provided
        if not description:
            description = f"Dynamic experiment with {categories} categories"
    else:
        print(f"🚀 Starting experiment: {experiment_name}")
        print(f"Strategy: {strategy_name}")
        print("=" * 60)
        
        # Validate strategy
        available_strategies = [s['name'] for s in tag_engine.list_strategies()]
        if strategy_name not in available_strategies:
            raise ValueError(f"Strategy '{strategy_name}' not found. Available: {available_strategies}")
    
    # Create experiment
    print("📝 Creating experiment...")
    experiment_id = manager.create_experiment(
        experiment_name=experiment_name,
        strategy_name=strategy_name,
        description=description
    )
    
    if auto_generate:
        # Generate dataset
        print(f"🔄 Generating dataset with strategy '{strategy_name}'...")
        
        # Run experimental preprocessing
        cmd = [
            sys.executable,
            "src/preprocess_experimental.py",
            "--experiment-id", experiment_id,
            "--strategy", strategy_name,
            "--input", input_csv
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
            
            if result.returncode == 0:
                print("✅ Dataset generation completed successfully!")
                print(result.stdout)
            else:
                print("❌ Dataset generation failed!")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                manager.update_experiment_status(experiment_id, 'failed', {
                    'error': result.stderr
                })
                return experiment_id
                
        except Exception as e:
            print(f"❌ Error running dataset generation: {e}")
            manager.update_experiment_status(experiment_id, 'failed', {
                'error': str(e)
            })
            return experiment_id
    
    print(f"\n🎯 Experiment '{experiment_id}' is ready!")
    print(f"Dataset location: data_experiments/{experiment_id}/")
    print(f"Next steps:")
    print(f"1. Validate dataset: python quality_check.py --experiment {experiment_id}")
    print(f"2. Start fine-tuning with the generated dataset")
    print(f"3. Compare results: python compare_experiments.py")
    
    return experiment_id


def list_experiments():
    """List all experiments"""
    manager = ExperimentManager()
    experiments = manager.list_experiments()
    
    print("📋 All Experiments")
    print("=" * 60)
    
    if not experiments:
        print("No experiments found.")
        return
    
    for exp in experiments:
        print(f"🧪 {exp['experiment_id']}")
        print(f"   Name: {exp['experiment_name']}")
        print(f"   Strategy: {exp['strategy_name']}")
        print(f"   Status: {exp['status']}")
        print(f"   Created: {exp['created_at']}")
        if exp.get('description'):
            print(f"   Description: {exp['description']}")
        print()


def list_strategies():
    """List all available strategies"""
    tag_engine = TagStrategyEngine()
    strategies = tag_engine.list_strategies()
    
    print("🏷️ Available Tag Strategies")
    print("=" * 60)
    
    for strategy in strategies:
        print(f"📚 {strategy['name']} ({strategy['version']})")
        print(f"   Categories: {strategy['categories']}")
        print(f"   Description: {strategy['description']}")
        print()


def create_multiple_experiments(base_name: str, strategies: list = None):
    """Create multiple experiments with different strategies for comparison"""
    if strategies is None:
        strategies = ['baseline', 'simplified', 'detailed', 'frequency_based']
    
    experiment_ids = []
    
    print(f"🔄 Creating multiple experiments for comparison")
    print(f"Base name: {base_name}")
    print(f"Strategies: {strategies}")
    print("=" * 60)
    
    for strategy in strategies:
        try:
            experiment_name = f"{base_name}_{strategy}"
            description = f"Comparative experiment using {strategy} strategy"
            
            exp_id = run_experiment(
                experiment_name=experiment_name,
                strategy_name=strategy,
                description=description,
                auto_generate=True
            )
            
            experiment_ids.append(exp_id)
            print(f"✅ Completed: {exp_id}")
            
        except Exception as e:
            print(f"❌ Failed to create experiment with {strategy}: {e}")
            continue
    
    print(f"\n🎉 Created {len(experiment_ids)} experiments for comparison:")
    for exp_id in experiment_ids:
        print(f"  - {exp_id}")
    
    return experiment_ids


def main():
    parser = argparse.ArgumentParser(description='Run tag classification experiments')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run single experiment
    run_parser = subparsers.add_parser('run', help='Run a single experiment')
    run_parser.add_argument('--name', required=True, help='Experiment name')
    
    # Strategy options - mutually exclusive
    strategy_group = run_parser.add_mutually_exclusive_group(required=True)
    strategy_group.add_argument('--strategy', help='Tag strategy name (baseline, simplified, detailed, frequency_based)')
    strategy_group.add_argument('--categories', type=int, metavar='N', 
                               help='Number of categories for dynamic strategy (2-17)')
    
    run_parser.add_argument('--description', default='', help='Experiment description')
    run_parser.add_argument('--input', default='data_raw/legacy_sentence_analysis.csv', 
                           help='Input CSV file')
    run_parser.add_argument('--no-generate', action='store_true', 
                           help='Skip automatic dataset generation')
    
    # Run multiple experiments
    multi_parser = subparsers.add_parser('multi', help='Run multiple experiments for comparison')
    multi_parser.add_argument('--base-name', required=True, help='Base name for experiments')
    multi_parser.add_argument('--strategies', nargs='+', 
                             default=['baseline', 'simplified', 'detailed', 'frequency_based'],
                             help='List of strategies to test')
    
    # List commands
    subparsers.add_parser('list', help='List all experiments')
    subparsers.add_parser('strategies', help='List available strategies')
    
    args = parser.parse_args()
    
    if args.command == 'run':
        run_experiment(
            experiment_name=args.name,
            strategy_name=args.strategy,
            categories=args.categories,
            description=args.description,
            input_csv=args.input,
            auto_generate=not args.no_generate
        )
    
    elif args.command == 'multi':
        create_multiple_experiments(args.base_name, args.strategies)
    
    elif args.command == 'list':
        list_experiments()
    
    elif args.command == 'strategies':
        list_strategies()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()