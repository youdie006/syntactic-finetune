#!/usr/bin/env python3
"""
Common Utilities - 두 프로세스에서 공통으로 사용하는 유틸리티 함수들
"""

import json
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path


def validate_csv_format(csv_path: str) -> bool:
    """
    CSV 파일이 올바른 구문 분석 형식인지 검증
    
    Args:
        csv_path: 검증할 CSV 파일 경로
        
    Returns:
        bool: 검증 통과 여부
    """
    required_columns = ['sentence_id', 'sentence', 'translation', 'slash_translate', 'tag_info', 'syntax_info']
    
    try:
        df = pd.read_csv(csv_path)
        
        # 컬럼 확인
        if not all(col in df.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in df.columns]
            print(f"❌ Missing columns: {missing_cols}")
            return False
        
        # 샘플 데이터 검증
        for idx, row in df.head(3).iterrows():
            if not validate_row_format(row):
                print(f"❌ Invalid row format at index {idx}")
                return False
        
        print(f"✅ CSV format validation passed: {len(df)} rows")
        return True
        
    except Exception as e:
        print(f"❌ CSV validation error: {e}")
        return False


def validate_row_format(row: pd.Series) -> bool:
    """
    단일 행의 데이터 형식 검증
    
    Args:
        row: 검증할 행 데이터
        
    Returns:
        bool: 검증 통과 여부
    """
    try:
        # JSON 필드 파싱 테스트
        slash_translate = json.loads(row['slash_translate'])
        tag_info = json.loads(row['tag_info'])
        syntax_info = json.loads(row['syntax_info'])
        
        # slash_translate 구조 확인
        if isinstance(slash_translate, list):
            for item in slash_translate:
                if not all(key in item for key in ['start_idx', 'end_idx', 'sentence', 'words']):
                    return False
        
        # tag_info 구조 확인
        if isinstance(tag_info, list):
            for item in tag_info:
                if not all(key in item for key in ['tag', 'category', 'words']):
                    return False
        
        return True
        
    except (json.JSONDecodeError, KeyError, TypeError):
        return False


def calculate_dataset_stats(csv_path: str) -> Dict[str, Any]:
    """
    데이터셋 통계 계산
    
    Args:
        csv_path: CSV 파일 경로
        
    Returns:
        Dict: 통계 정보
    """
    df = pd.read_csv(csv_path)
    
    stats = {
        'total_sentences': len(df),
        'avg_sentence_length': df['sentence'].str.len().mean(),
        'min_sentence_length': df['sentence'].str.len().min(),
        'max_sentence_length': df['sentence'].str.len().max(),
        'unique_sentences': df['sentence'].nunique(),
        'has_translations': df['translation'].notna().sum(),
        'avg_tags_per_sentence': 0,
        'total_unique_tags': 0
    }
    
    # 태그 통계 계산
    all_tags = []
    for _, row in df.iterrows():
        try:
            tag_info = json.loads(row['tag_info'])
            if isinstance(tag_info, list):
                tags = [item['tag'] for item in tag_info if 'tag' in item]
                all_tags.extend(tags)
        except:
            continue
    
    if all_tags:
        stats['avg_tags_per_sentence'] = len(all_tags) / len(df)
        stats['total_unique_tags'] = len(set(all_tags))
    
    return stats


def merge_csv_files(csv_paths: List[str], output_path: str) -> None:
    """
    여러 CSV 파일을 하나로 병합
    
    Args:
        csv_paths: 병합할 CSV 파일 경로들
        output_path: 출력 파일 경로
    """
    dfs = []
    
    for csv_path in csv_paths:
        if Path(csv_path).exists():
            df = pd.read_csv(csv_path)
            dfs.append(df)
            print(f"Loaded {len(df)} rows from {csv_path}")
        else:
            print(f"⚠️ File not found: {csv_path}")
    
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True)
        combined_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"✅ Merged {len(combined_df)} rows to {output_path}")
    else:
        print("❌ No files to merge")


def extract_vocabulary(csv_path: str) -> Dict[str, int]:
    """
    CSV에서 어휘 추출 및 빈도 계산
    
    Args:
        csv_path: CSV 파일 경로
        
    Returns:
        Dict: 단어별 빈도
    """
    df = pd.read_csv(csv_path)
    vocabulary = {}
    
    for _, row in df.iterrows():
        # 문장에서 단어 추출
        words = row['sentence'].split()
        for word in words:
            # 구두점 제거 및 소문자 변환
            clean_word = word.strip('.,!?;:"').lower()
            if clean_word:
                vocabulary[clean_word] = vocabulary.get(clean_word, 0) + 1
    
    # 빈도순 정렬
    return dict(sorted(vocabulary.items(), key=lambda x: x[1], reverse=True))


def compare_csv_structures(csv1_path: str, csv2_path: str) -> Dict[str, Any]:
    """
    두 CSV 파일의 구조 비교
    
    Args:
        csv1_path: 첫 번째 CSV 파일 경로
        csv2_path: 두 번째 CSV 파일 경로
        
    Returns:
        Dict: 비교 결과
    """
    df1 = pd.read_csv(csv1_path)
    df2 = pd.read_csv(csv2_path)
    
    comparison = {
        'columns_match': list(df1.columns) == list(df2.columns),
        'row_counts': {'csv1': len(df1), 'csv2': len(df2)},
        'column_differences': {
            'csv1_only': list(set(df1.columns) - set(df2.columns)),
            'csv2_only': list(set(df2.columns) - set(df1.columns))
        },
        'data_types_match': df1.dtypes.equals(df2.dtypes)
    }
    
    return comparison


def create_sample_input_file(output_path: str, num_sentences: int = 10) -> None:
    """
    샘플 입력 텍스트 파일 생성
    
    Args:
        output_path: 출력 파일 경로
        num_sentences: 생성할 문장 수
    """
    sample_sentences = [
        "The quick brown fox jumps over the lazy dog.",
        "Natural language processing enables computers to understand human language.",
        "Machine learning algorithms can identify patterns in large datasets.",
        "Students who practice regularly achieve better results in their exams.",
        "The weather forecast predicts rain for the weekend.",
        "Social media platforms connect people from around the world.",
        "Renewable energy sources are becoming more cost-effective each year.",
        "Scientific research requires careful observation and analysis.",
        "The development of artificial intelligence has accelerated rapidly.",
        "Education systems must adapt to technological changes in society.",
        "Global warming affects weather patterns worldwide.",
        "International cooperation is essential for addressing climate change.",
        "The human brain processes information in complex ways.",
        "Digital transformation is reshaping traditional business models.",
        "Space exploration continues to reveal new discoveries about the universe."
    ]
    
    selected_sentences = sample_sentences[:num_sentences]
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for sentence in selected_sentences:
            f.write(sentence + '\n')
    
    print(f"✅ Sample input file created: {output_path}")
    print(f"Contains {len(selected_sentences)} sentences")


if __name__ == "__main__":
    # 테스트 실행
    print("Testing common utilities...")
    
    # 샘플 입력 파일 생성 테스트
    create_sample_input_file("shared/sample_input.txt", 5)
    
    print("✅ Common utilities test completed")