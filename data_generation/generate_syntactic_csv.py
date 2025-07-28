#!/usr/bin/env python3
"""
문법 주석 텍스트 파일을 CSV로 변환하는 메인 생성기
"""

import pandas as pd
import json
import re
import os
import argparse
from typing import List, Dict, Any
import openpyxl


class SyntacticCSVGenerator:
    """문법 주석이 달린 텍스트를 CSV로 변환"""
    
    def __init__(self):
        self.patterns = self._load_patterns()
    
    def _load_patterns(self) -> Dict:
        """저장된 패턴 로드 (있으면)"""
        if os.path.exists('original_patterns.json'):
            with open('original_patterns.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _generate_id(self, index: int) -> str:
        """sentence_id 생성 (UUID 형식)"""
        import uuid
        return str(uuid.uuid4())
    
    def process_file(self, input_path: str) -> List[Dict]:
        """입력 파일 처리 (텍스트 또는 엑셀)"""
        if input_path.endswith('.xlsx') or input_path.endswith('.xls'):
            return self._process_excel(input_path)
        else:
            return self._process_text(input_path)
    
    def _process_excel(self, excel_path: str) -> List[Dict]:
        """엑셀 파일 처리"""
        df = pd.read_excel(excel_path)
        data = []
        sentence_count = 0
        
        for idx, row in df.iterrows():
            # 빈 행 건너뛰기
            if pd.isna(row.iloc[0]) or str(row.iloc[0]).strip() == '':
                continue
            
            sentence = str(row.iloc[0]).strip()  # 영어 문장
            translation = str(row.iloc[1]).strip() if not pd.isna(row.iloc[1]) else ""  # 한국어 번역
            
            # 문법 태그 수집 (문법 태그 1~6 컬럼)
            tags = []
            for i in range(2, min(len(row), 8)):  # 최대 6개 태그
                if not pd.isna(row.iloc[i]) and str(row.iloc[i]).strip():
                    tag = str(row.iloc[i]).strip()
                    if tag.startswith('[') and tag.endswith(']'):
                        tags.append(tag)
            
            # 데이터 생성
            if sentence in self.patterns:
                # 패턴이 있으면 사용
                pattern = self.patterns[sentence]
                data.append({
                    'sentence_id': self._generate_id(sentence_count),
                    'sentence': sentence,
                    'translation': pattern['translation'],
                    'slash_translate': json.dumps(pattern['slash_translate'], ensure_ascii=False),
                    'tag_info': json.dumps(pattern['tag_info'], ensure_ascii=False),
                    'syntax_info': '[]'
                })
            else:
                # 패턴이 없으면 기본 생성
                data.append(self._create_default_entry(
                    sentence, translation, tags, sentence_count
                ))
            
            sentence_count += 1
        
        return data
    
    def _process_text(self, text_path: str) -> List[Dict]:
        """텍스트 파일 처리"""
        data = []
        
        with open(text_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        sentence_count = 0
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            # 라인 번호 제거
            line = re.sub(r'^\d+→', '', line).strip()
            
            # 영어 문장 찾기
            if line and line[0].isupper() and not line.startswith('['):
                sentence = line
                translation = ""
                tags = []
                
                # 다음 라인에서 번역 찾기
                j = i + 1
                if j < len(lines):
                    next_line = lines[j].strip()
                    next_line = re.sub(r'^\d+→', '', next_line).strip()
                    if next_line and not next_line.startswith('[') and not next_line[0].isupper():
                        translation = next_line
                        j += 1
                
                # 태그 수집
                while j < len(lines):
                    tag_line = lines[j].strip()
                    tag_line = re.sub(r'^\d+→', '', tag_line).strip()
                    
                    if tag_line.startswith('['):
                        tags.append(tag_line)
                    elif tag_line == "" or (tag_line and tag_line[0].isupper()):
                        break
                    j += 1
                
                # 데이터 생성
                if sentence in self.patterns:
                    # 패턴이 있으면 사용
                    pattern = self.patterns[sentence]
                    data.append({
                        'sentence_id': self._generate_id(sentence_count),
                        'sentence': sentence,
                        'translation': pattern['translation'],
                        'slash_translate': json.dumps(pattern['slash_translate'], ensure_ascii=False),
                        'tag_info': json.dumps(pattern['tag_info'], ensure_ascii=False),
                        'syntax_info': '[]'
                    })
                else:
                    # 패턴이 없으면 기본 생성
                    data.append(self._create_default_entry(
                        sentence, translation, tags, sentence_count
                    ))
                
                sentence_count += 1
            
            i += 1
        
        return data
    
    def _create_default_entry(self, sentence: str, translation: str, 
                             tags: List[str], index: int) -> Dict:
        """기본 데이터 항목 생성"""
        # 단어 분리
        words = sentence.replace(',', ' ,').replace('.', ' .').replace(':', ' :').split()
        
        # 기본 slash_translate
        slash_translate = [{
            'start_idx': 0,
            'end_idx': len(words) - 1,
            'sentence': sentence,
            'translation': translation,
            'words': words
        }]
        
        # tag_info 생성
        tag_info = []
        for tag in tags:
            match = re.match(r'\[(.+) -> (.+)\]', tag)
            if match:
                tag_text = match.group(1)
                tag_type = match.group(2)
                
                # 카테고리 분류
                category = self._classify_category(tag_type)
                
                tag_info.append({
                    'tag': tag[1:-1],
                    'category': category,
                    'words': []
                })
        
        return {
            'sentence_id': self._generate_id(index),
            'sentence': sentence,
            'translation': translation,
            'slash_translate': json.dumps(slash_translate, ensure_ascii=False),
            'tag_info': json.dumps(tag_info, ensure_ascii=False),
            'syntax_info': '[]'
        }
    
    def _classify_category(self, tag_type: str) -> str:
        """태그 타입에 따른 카테고리 분류"""
        if '접속사' in tag_type:
            return '접속사'
        elif '동사' in tag_type or '시제' in tag_type:
            return '동사_시제'
        elif '관계' in tag_type:
            return '관계사'
        elif '전치사' in tag_type:
            return '전치사'
        elif '동명사' in tag_type or '분사' in tag_type or 'to부정사' in tag_type:
            return '준동사'
        else:
            return '구문'
    
    def generate_csv(self, input_path: str, output_path: str) -> pd.DataFrame:
        """CSV 생성"""
        file_type = '📓 엑셀' if input_path.endswith(('.xlsx', '.xls')) else '📄 텍스트'
        print(f"\n{file_type} 입력 파일: {input_path}")
        print(f"💾 출력 파일: {output_path}")
        print(f"🆔 ID 형식: UUID")
        
        # 데이터 처리
        data = self.process_file(input_path)
        
        # DataFrame 생성
        df = pd.DataFrame(data)
        
        # CSV 저장
        columns = ['sentence_id', 'sentence', 'translation', 
                  'slash_translate', 'tag_info', 'syntax_info']
        df[columns].to_csv(output_path, index=False, encoding='utf-8')
        
        print(f"\n✅ CSV 생성 완료!")
        print(f"📊 총 {len(df)}개의 문장 처리")
        
        return df


def main():
    parser = argparse.ArgumentParser(
        description='문법 주석 텍스트를 CSV로 변환'
    )
    parser.add_argument(
        'input', 
        help='입력 파일 경로 (.txt 또는 .xlsx)'
    )
    parser.add_argument(
        '-o', '--output',
        default='syntactic_analysis.csv',
        help='출력 CSV 파일 경로 (기본값: syntactic_analysis.csv)'
    )
    
    args = parser.parse_args()
    
    # CSV 생성
    generator = SyntacticCSVGenerator()
    df = generator.generate_csv(args.input, args.output)
    
    # 샘플 출력
    print("\n📋 생성된 CSV 샘플:")
    print("-" * 60)
    for idx in range(min(3, len(df))):
        print(f"\n[문장 {idx+1}]")
        print(f"ID: {df.iloc[idx]['sentence_id']}")
        print(f"문장: {df.iloc[idx]['sentence'][:50]}...")
        slash_data = json.loads(df.iloc[idx]['slash_translate'])
        print(f"청크 수: {len(slash_data)}")


if __name__ == "__main__":
    main()