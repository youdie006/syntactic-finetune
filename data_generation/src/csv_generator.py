#!/usr/bin/env python3
"""
CSV Generator - 원시 텍스트에서 구문 분석 CSV 생성
"""

import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from language_analyzer import LanguageAnalyzer
from data_formatter import DataFormatter


@dataclass
class SentenceData:
    """단일 문장 분석 결과를 담는 데이터 클래스"""
    sentence_id: str
    sentence: str
    translation: Optional[str] = None
    slash_translate: Optional[Dict] = None
    tag_info: Optional[List[Dict]] = None
    syntax_info: Optional[List] = None


class CSVGenerator:
    """
    원시 텍스트에서 구문 분석 CSV를 생성하는 메인 클래스
    """
    
    def __init__(self, use_translation: bool = False):
        """
        Args:
            use_translation: 번역 서비스 사용 여부
        """
        self.analyzer = LanguageAnalyzer()
        self.formatter = DataFormatter()
        self.use_translation = use_translation
        
    def generate_sentence_id(self) -> str:
        """고유한 문장 ID 생성"""
        timestamp = int(datetime.now().timestamp() * 1000000)
        return str(timestamp)
    
    def analyze_single_sentence(self, sentence: str, translation: Optional[str] = None) -> SentenceData:
        """
        단일 문장을 분석하여 SentenceData 객체 반환
        
        Args:
            sentence: 분석할 영어 문장
            translation: 한국어 번역 (선택사항)
            
        Returns:
            SentenceData: 분석 결과
        """
        # 기본 정보
        sentence_id = self.generate_sentence_id()
        
        # 언어 분석 수행
        analysis_result = self.analyzer.analyze(sentence)
        
        # 데이터 포맷팅
        slash_translate = self.formatter.format_slash_translate(analysis_result)
        tag_info = self.formatter.format_tag_info(analysis_result)
        
        # 번역 처리 (필요시)
        if translation is None and self.use_translation:
            # TODO: 번역 서비스 연동
            translation = sentence  # 임시로 원문 사용
        
        return SentenceData(
            sentence_id=sentence_id,
            sentence=sentence,
            translation=translation or "",
            slash_translate=slash_translate,
            tag_info=tag_info,
            syntax_info=[]  # 기존 CSV에서 빈 배열로 사용됨
        )
    
    def process_sentences(self, sentences: List[str], translations: Optional[List[str]] = None) -> List[SentenceData]:
        """
        여러 문장을 배치 처리
        
        Args:
            sentences: 분석할 영어 문장들
            translations: 한국어 번역들 (선택사항)
            
        Returns:
            List[SentenceData]: 분석 결과 리스트
        """
        results = []
        
        for i, sentence in enumerate(sentences):
            translation = translations[i] if translations and i < len(translations) else None
            
            try:
                result = self.analyze_single_sentence(sentence, translation)
                results.append(result)
                print(f"Processed {i+1}/{len(sentences)}: {sentence[:50]}...")
                
            except Exception as e:
                print(f"Error processing sentence {i+1}: {e}")
                continue
                
        return results
    
    def save_to_csv(self, sentence_data: List[SentenceData], output_path: str) -> None:
        """
        분석 결과를 CSV 파일로 저장
        
        Args:
            sentence_data: 분석 결과 리스트
            output_path: 출력 파일 경로
        """
        # DataFrame 생성
        rows = []
        for data in sentence_data:
            row = {
                'sentence_id': data.sentence_id,
                'sentence': data.sentence,
                'translation': data.translation,
                'slash_translate': json.dumps(data.slash_translate, ensure_ascii=False),
                'tag_info': json.dumps(data.tag_info, ensure_ascii=False),
                'syntax_info': json.dumps(data.syntax_info, ensure_ascii=False)
            }
            rows.append(row)
        
        df = pd.DataFrame(rows)
        
        # CSV 저장 (기존 형식과 동일하게)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"✅ CSV saved to: {output_path}")
        print(f"Total sentences: {len(sentence_data)}")
    
    def generate_from_text_file(self, input_path: str, output_path: str, 
                               translation_path: Optional[str] = None) -> None:
        """
        텍스트 파일에서 CSV 생성
        
        Args:
            input_path: 입력 텍스트 파일 경로
            output_path: 출력 CSV 파일 경로
            translation_path: 번역 파일 경로 (선택사항)
        """
        # 입력 파일 읽기
        with open(input_path, 'r', encoding='utf-8') as f:
            sentences = [line.strip() for line in f if line.strip()]
        
        # 번역 파일 읽기 (있는 경우)
        translations = None
        if translation_path:
            with open(translation_path, 'r', encoding='utf-8') as f:
                translations = [line.strip() for line in f if line.strip()]
        
        # 분석 및 저장
        print(f"🚀 Processing {len(sentences)} sentences...")
        results = self.process_sentences(sentences, translations)
        self.save_to_csv(results, output_path)


if __name__ == "__main__":
    # 테스트용 간단한 실행
    generator = CSVGenerator()
    
    test_sentences = [
        "This is a simple test sentence.",
        "The quick brown fox jumps over the lazy dog.",
        "Natural language processing is fascinating."
    ]
    
    results = generator.process_sentences(test_sentences)
    generator.save_to_csv(results, "data_generation/output/test_output.csv")