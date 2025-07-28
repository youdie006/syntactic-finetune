#!/usr/bin/env python3
"""
Generate CSV - CSV 생성을 위한 CLI 인터페이스
"""

import argparse
import sys
import os
from pathlib import Path

# src 디렉토리를 path에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from csv_generator import CSVGenerator


def main():
    parser = argparse.ArgumentParser(description='Generate syntactic analysis CSV from text')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # 단일 문장 분석
    single_parser = subparsers.add_parser('single', help='Analyze a single sentence')
    single_parser.add_argument('sentence', help='Sentence to analyze')
    single_parser.add_argument('--translation', help='Korean translation (optional)')
    single_parser.add_argument('--output', '-o', default='data_generation/output/single_analysis.csv',
                              help='Output CSV file path')
    
    # 파일 배치 처리
    batch_parser = subparsers.add_parser('batch', help='Process text file in batch')
    batch_parser.add_argument('input_file', help='Input text file path')
    batch_parser.add_argument('--output', '-o', required=True, help='Output CSV file path')
    batch_parser.add_argument('--translation-file', help='Translation file path (optional)')
    batch_parser.add_argument('--use-translation', action='store_true',
                             help='Enable automatic translation (requires API setup)')
    
    # 샘플 생성
    sample_parser = subparsers.add_parser('sample', help='Generate sample CSV')
    sample_parser.add_argument('--count', '-c', type=int, default=5,
                              help='Number of sample sentences')
    sample_parser.add_argument('--output', '-o', default='data_generation/output/sample.csv',
                              help='Output CSV file path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # CSV Generator 초기화
    generator = CSVGenerator(use_translation=getattr(args, 'use_translation', False))
    
    try:
        if args.command == 'single':
            handle_single_sentence(generator, args)
        elif args.command == 'batch':
            handle_batch_processing(generator, args)
        elif args.command == 'sample':
            handle_sample_generation(generator, args)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def handle_single_sentence(generator: CSVGenerator, args):
    """단일 문장 처리"""
    print(f"🔍 Analyzing sentence: {args.sentence}")
    
    # 출력 디렉토리 생성
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 분석 및 저장
    results = generator.process_sentences([args.sentence], 
                                        [args.translation] if args.translation else None)
    generator.save_to_csv(results, args.output)


def handle_batch_processing(generator: CSVGenerator, args):
    """배치 파일 처리"""
    print(f"📂 Processing file: {args.input_file}")
    
    # 입력 파일 확인
    if not os.path.exists(args.input_file):
        raise FileNotFoundError(f"Input file not found: {args.input_file}")
    
    # 출력 디렉토리 생성
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 파일 처리
    generator.generate_from_text_file(
        input_path=args.input_file,
        output_path=args.output,
        translation_path=args.translation_file
    )


def handle_sample_generation(generator: CSVGenerator, args):
    """샘플 데이터 생성"""
    print(f"🎯 Generating {args.count} sample sentences")
    
    # 샘플 문장들
    sample_sentences = [
        "The quick brown fox jumps over the lazy dog.",
        "Natural language processing is a fascinating field of study.",
        "Students who study hard will achieve their academic goals.",
        "The weather was beautiful, so we decided to go for a walk.",
        "If you practice regularly, you will improve your skills.",
        "She bought a book that her friend had recommended.",
        "The company, which was founded in 1990, has grown significantly.",
        "After finishing his homework, Tom went to play with his friends.",
        "The scientist discovered a new species in the Amazon rainforest.",
        "Technology has revolutionized the way we communicate with each other."
    ]
    
    # 요청된 개수만큼 선택
    selected_sentences = sample_sentences[:args.count]
    
    # 출력 디렉토리 생성
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 분석 및 저장
    results = generator.process_sentences(selected_sentences)
    generator.save_to_csv(results, args.output)


if __name__ == "__main__":
    main()