#!/usr/bin/env python3
"""
Experimental preprocessing script with tag strategy support.
Extends the original preprocessing to support different tag classification strategies.
"""

import argparse
import ast
import json
import os
import sys
from pathlib import Path

import pandas as pd

from utils import (
    load_tag_mapping, validate_training_data, calculate_token_stats, split_dataset
)
from tag_strategy_engine import TagStrategyEngine
from experiment_manager import ExperimentManager


def format_training_example_with_strategy(sentence: str, chunks: str, pos_tags: str, 
                                        grammatical_roles: str) -> dict:
    """
    Format a single training example for OpenAI fine-tuning with strategy-applied tags.
    """
    # Create the expected JSON output format
    analysis = {
        "chunks": chunks,
        "pos_tags": pos_tags,
        "grammatical_roles": grammatical_roles
    }
    
    return {
        "messages": [
            {
                "role": "user",
                "content": f"Analyze this sentence syntactically: {sentence}"
            },
            {
                "role": "assistant", 
                "content": json.dumps(analysis, ensure_ascii=False)
            }
        ]
    }


def load_and_validate_csv(csv_path: str) -> pd.DataFrame:
    """Load and validate the input CSV file."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Input CSV file not found: {csv_path}")
    
    print(f"Loading CSV from: {csv_path}")
    df = pd.read_csv(csv_path)
    
    print(f"Loaded {len(df)} rows")
    print(f"Available columns: {list(df.columns)}")
    
    # Check required columns for the actual CSV structure
    required_columns = ['sentence', 'tag_info']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print("Available columns:", list(df.columns))
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Remove rows with missing data
    initial_count = len(df)
    df = df.dropna(subset=required_columns)
    final_count = len(df)
    
    if initial_count != final_count:
        print(f"Removed {initial_count - final_count} rows with missing data")
    
    return df


def process_data_with_strategy(df: pd.DataFrame, tag_engine: TagStrategyEngine) -> list:
    """
    Process the DataFrame and convert to training examples using the specified tag strategy.
    """
    print("Processing data with strategy...")
    examples = []
    
    strategy_info = tag_engine.get_strategy_info()
    print(f"Using strategy: {strategy_info.get('name', 'unknown')} ({strategy_info.get('version', 'unknown')})")
    
    for idx, row in df.iterrows():
        if idx % 10000 == 0:
            print(f"Processing row {idx}/{len(df)}")
        
        try:
            # Get data from row
            sentence = str(row['sentence']).strip()
            
            # Parse tag_info JSON (using ast.literal_eval for Python-style strings)
            tag_info_str = str(row['tag_info']).strip()
            if tag_info_str == '[]' or tag_info_str == 'nan':
                continue  # Skip rows with empty tag info
                
            tag_info = ast.literal_eval(tag_info_str)
            
            # Apply tag strategy to extract syntactic information
            chunks, pos_tags, grammatical_roles = tag_engine.apply_strategy(tag_info)
            
            # Skip empty or invalid entries
            if not all([sentence, chunks, pos_tags, grammatical_roles]):
                continue
                
            # Format as training example
            example = format_training_example_with_strategy(sentence, chunks, pos_tags, grammatical_roles)
            examples.append(example)
            
        except (ValueError, SyntaxError, KeyError, Exception) as e:
            if idx < 10:  # Only print first 10 errors to avoid spam
                print(f"Error processing row {idx}: {e}")
            continue
    
    print(f"Created {len(examples)} training examples")
    return examples


def save_jsonl(examples: list, output_path: str):
    """Save examples to JSONL format."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    print(f"Saved {len(examples)} examples to: {output_path}")


def generate_experimental_dataset(experiment_id: str,
                                strategy_name: str,
                                input_csv: str,
                                output_dir: str = None,
                                train_ratio: float = 0.8,
                                valid_ratio: float = 0.15,
                                random_seed: int = 42) -> dict:
    """
    Generate dataset for a specific experiment with the given strategy.
    
    Returns:
        Dictionary with dataset statistics and paths
    """
    # Initialize tag engine with strategy
    tag_engine = TagStrategyEngine()
    tag_engine.set_strategy(strategy_name)
    
    # Set output directory
    if output_dir is None:
        output_dir = f"data_experiments/{experiment_id}"
    
    # Load and validate CSV
    df = load_and_validate_csv(input_csv)
    
    # Process data with strategy
    examples = process_data_with_strategy(df, tag_engine)
    
    if not examples:
        raise ValueError("No valid examples created. Check your data and strategy.")
    
    # Validate training data
    print("Validating training data format...")
    is_valid, errors = validate_training_data(examples)
    
    if not is_valid:
        print("Validation errors found:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")
        raise ValueError("Training data validation failed")
    
    print("✓ Training data validation passed")
    
    # Calculate token statistics
    print("Calculating token statistics...")
    stats = calculate_token_stats(examples)
    
    # Create DataFrame from examples for splitting
    examples_df = pd.DataFrame(examples)
    
    # Split dataset
    print("Splitting dataset...")
    train_df, valid_df, test_df = split_dataset(
        examples_df, 
        train_ratio=train_ratio,
        valid_ratio=valid_ratio,
        random_state=random_seed
    )
    
    print(f"Dataset split:")
    print(f"  Training: {len(train_df)} examples ({len(train_df)/len(examples):.1%})")
    print(f"  Validation: {len(valid_df)} examples ({len(valid_df)/len(examples):.1%})")
    print(f"  Test: {len(test_df)} examples ({len(test_df)/len(examples):.1%})")
    
    # Save to JSONL files
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    train_path = output_dir / 'train.jsonl'
    valid_path = output_dir / 'valid.jsonl'
    test_path = output_dir / 'test_local.jsonl'
    
    save_jsonl(train_df.to_dict('records'), train_path)
    save_jsonl(valid_df.to_dict('records'), valid_path)
    save_jsonl(test_df.to_dict('records'), test_path)
    
    # Prepare results
    results = {
        'experiment_id': experiment_id,
        'strategy_name': strategy_name,
        'strategy_info': tag_engine.get_strategy_info(),
        'dataset_stats': {
            'total_examples': len(examples),
            'train_examples': len(train_df),
            'valid_examples': len(valid_df),
            'test_examples': len(test_df),
            'split_ratios': {
                'train': train_ratio,
                'valid': valid_ratio,
                'test': 1.0 - train_ratio - valid_ratio
            }
        },
        'token_stats': stats,
        'file_paths': {
            'train': str(train_path),
            'valid': str(valid_path),
            'test': str(test_path)
        },
        'quality_score': 100.0 if is_valid else 0.0
    }
    
    print(f"\n✅ Dataset generation completed!")
    print(f"Strategy: {strategy_name}")
    print(f"Output directory: {output_dir}")
    print(f"Total examples: {len(examples):,}")
    print(f"Average tokens per example: {stats['avg_tokens_per_example']:.1f}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Generate experimental dataset with tag strategy')
    parser.add_argument('--experiment-id', required=True,
                       help='Experiment ID')
    parser.add_argument('--strategy', required=True,
                       help='Tag strategy name (baseline, simplified, detailed, frequency_based)')
    parser.add_argument('--input', default='data_raw/legacy_sentence_analysis.csv',
                       help='Input CSV file path')
    parser.add_argument('--output-dir', default=None,
                       help='Output directory (default: data_experiments/{experiment_id})')
    parser.add_argument('--train-ratio', type=float, default=0.8,
                       help='Training set ratio (default: 0.8)')
    parser.add_argument('--valid-ratio', type=float, default=0.15,
                       help='Validation set ratio (default: 0.15)')
    parser.add_argument('--random-seed', type=int, default=42,
                       help='Random seed for data splitting (default: 42)')
    
    args = parser.parse_args()
    
    try:
        # Generate dataset
        results = generate_experimental_dataset(
            experiment_id=args.experiment_id,
            strategy_name=args.strategy,
            input_csv=args.input,
            output_dir=args.output_dir,
            train_ratio=args.train_ratio,
            valid_ratio=args.valid_ratio,
            random_seed=args.random_seed
        )
        
        # Save results summary
        results_file = f"results/experiments/{args.experiment_id}_generation_results.json"
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 Results saved to: {results_file}")
        
        # Update experiment manager if available
        try:
            manager = ExperimentManager()
            manager.update_experiment_status(args.experiment_id, 'dataset_ready', {
                'generation_results': results,
                'generated_at': pd.Timestamp.now().isoformat()
            })
        except Exception as e:
            print(f"Warning: Could not update experiment status: {e}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()