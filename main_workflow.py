#!/usr/bin/env python3
"""
Main Workflow - 전체 프로세스를 통합 관리하는 스크립트
두 가지 워크플로우를 지원:
1. 텍스트 → CSV 생성 (data_generation)
2. CSV → JSONL 변환 (fine_tuning)
"""

import argparse
import sys
import os
import subprocess
from pathlib import Path

# 공통 유틸리티 추가
sys.path.append('shared')
from common_utils import validate_csv_format, calculate_dataset_stats


def main():
    parser = argparse.ArgumentParser(description='Syntactic Analysis Workflow Manager')
    subparsers = parser.add_subparsers(dest='workflow', help='Available workflows')
    
    # 텍스트 → CSV 워크플로우
    csv_parser = subparsers.add_parser('generate-csv', help='Generate CSV from text')
    csv_parser.add_argument('input_file', help='Input text file')
    csv_parser.add_argument('--output', '-o', help='Output CSV file path')
    csv_parser.add_argument('--translation-file', help='Translation file (optional)')
    csv_parser.add_argument('--validate', action='store_true', help='Validate output CSV')
    
    # CSV → JSONL 워크플로우
    jsonl_parser = subparsers.add_parser('generate-jsonl', help='Generate JSONL from CSV')
    jsonl_parser.add_argument('csv_file', help='Input CSV file')
    jsonl_parser.add_argument('--experiment-name', required=True, help='Experiment name')
    jsonl_parser.add_argument('--categories', type=int, help='Number of categories for dynamic strategy')
    jsonl_parser.add_argument('--strategy', help='Strategy name (baseline, simplified, detailed, frequency_based)')
    
    # 전체 파이프라인
    pipeline_parser = subparsers.add_parser('full-pipeline', help='Full text → CSV → JSONL pipeline')
    pipeline_parser.add_argument('input_file', help='Input text file')
    pipeline_parser.add_argument('--experiment-name', required=True, help='Experiment name')
    pipeline_parser.add_argument('--categories', type=int, default=5, help='Number of categories')
    pipeline_parser.add_argument('--csv-output', help='Intermediate CSV file path')
    
    # 상태 확인
    status_parser = subparsers.add_parser('status', help='Check system status and requirements')
    
    # 통계 정보
    stats_parser = subparsers.add_parser('stats', help='Show dataset statistics')
    stats_parser.add_argument('csv_file', help='CSV file to analyze')
    
    args = parser.parse_args()
    
    if not args.workflow:
        parser.print_help()
        return
    
    try:
        if args.workflow == 'generate-csv':
            handle_csv_generation(args)
        elif args.workflow == 'generate-jsonl':
            handle_jsonl_generation(args)
        elif args.workflow == 'full-pipeline':
            handle_full_pipeline(args)
        elif args.workflow == 'status':
            handle_status_check()
        elif args.workflow == 'stats':
            handle_stats(args)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def handle_csv_generation(args):
    """텍스트 → CSV 생성 처리"""
    print("🔄 Starting CSV generation workflow...")
    
    # 출력 경로 설정
    if not args.output:
        input_name = Path(args.input_file).stem
        args.output = f"data_generation/output/{input_name}_analysis.csv"
    
    # CSV 생성 명령 실행
    cmd = [
        sys.executable,
        "data_generation/generate_csv.py",
        "batch",
        args.input_file,
        "--output", args.output
    ]
    
    if args.translation_file:
        cmd.extend(["--translation-file", args.translation_file])
    
    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ CSV generation completed!")
        print(result.stdout)
        
        # 검증 수행
        if args.validate:
            print("🔍 Validating CSV format...")
            if validate_csv_format(args.output):
                print("✅ CSV validation passed")
            else:
                print("❌ CSV validation failed")
                
    else:
        print("❌ CSV generation failed!")
        print("STDERR:", result.stderr)


def handle_jsonl_generation(args):
    """CSV → JSONL 생성 처리"""
    print("🔄 Starting JSONL generation workflow...")
    
    # CSV 파일 검증
    if not validate_csv_format(args.csv_file):
        raise ValueError(f"Invalid CSV format: {args.csv_file}")
    
    # fine_tuning 디렉토리로 이동하여 실행
    cmd = [
        sys.executable,
        "fine_tuning/run_experiment.py",
        "run",
        "--name", args.experiment_name,
        "--input", args.csv_file
    ]
    
    # 전략 또는 카테고리 설정
    if args.categories:
        cmd.extend(["--categories", str(args.categories)])
    elif args.strategy:
        cmd.extend(["--strategy", args.strategy])
    else:
        # 기본값으로 5개 카테고리 사용
        cmd.extend(["--categories", "5"])
    
    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ JSONL generation completed!")
        print(result.stdout)
    else:
        print("❌ JSONL generation failed!")
        print("STDERR:", result.stderr)


def handle_full_pipeline(args):
    """전체 파이프라인 처리"""
    print("🚀 Starting full pipeline: Text → CSV → JSONL")
    
    # 1단계: CSV 생성
    print("\n📝 Step 1: Generating CSV from text...")
    
    if not args.csv_output:
        input_name = Path(args.input_file).stem
        args.csv_output = f"results/generated_csv/{input_name}_{args.experiment_name}.csv"
    
    # CSV 생성 실행
    csv_args = argparse.Namespace(
        input_file=args.input_file,
        output=args.csv_output,
        translation_file=None,
        validate=True
    )
    handle_csv_generation(csv_args)
    
    # 2단계: JSONL 생성
    print("\n🔄 Step 2: Generating JSONL from CSV...")
    
    jsonl_args = argparse.Namespace(
        csv_file=args.csv_output,
        experiment_name=args.experiment_name,
        categories=args.categories,
        strategy=None
    )
    handle_jsonl_generation(jsonl_args)
    
    print("\n🎉 Full pipeline completed successfully!")
    print(f"📊 Generated CSV: {args.csv_output}")
    print(f"📁 JSONL datasets available in: fine_tuning/data_experiments/")


def handle_status_check():
    """시스템 상태 확인"""
    print("🔍 Checking system status...")
    
    # Python 버전 확인
    print(f"Python version: {sys.version}")
    
    # 필수 라이브러리 확인
    required_packages = ['pandas', 'spacy', 'pyyaml']
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}: installed")
        except ImportError:
            print(f"❌ {package}: not installed")
    
    # spaCy 모델 확인
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        print("✅ spaCy English model: available")
    except OSError:
        print("❌ spaCy English model: not installed")
        print("   Install with: python -m spacy download en_core_web_sm")
    
    # 디렉토리 구조 확인
    required_dirs = [
        'data_generation/src',
        'data_generation/output',
        'fine_tuning/src',
        'fine_tuning/configs',
        'shared',
        'results/generated_csv'
    ]
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ Directory: {dir_path}")
        else:
            print(f"❌ Directory missing: {dir_path}")
    
    print("\n📋 Status check completed")


def handle_stats(args):
    """데이터셋 통계 표시"""
    print(f"📊 Analyzing dataset: {args.csv_file}")
    
    if not Path(args.csv_file).exists():
        raise FileNotFoundError(f"CSV file not found: {args.csv_file}")
    
    stats = calculate_dataset_stats(args.csv_file)
    
    print(f"\n📈 Dataset Statistics:")
    print(f"  Total sentences: {stats['total_sentences']:,}")
    print(f"  Unique sentences: {stats['unique_sentences']:,}")
    print(f"  Average sentence length: {stats['avg_sentence_length']:.1f} characters")
    print(f"  Min/Max sentence length: {stats['min_sentence_length']}/{stats['max_sentence_length']} characters")
    print(f"  Sentences with translations: {stats['has_translations']:,}")
    print(f"  Average tags per sentence: {stats['avg_tags_per_sentence']:.1f}")
    print(f"  Total unique tags: {stats['total_unique_tags']:,}")


if __name__ == "__main__":
    main()