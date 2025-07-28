#!/usr/bin/env python3
"""
Data Formatter - 분석 결과를 기존 CSV 형식에 맞게 포맷팅
"""

import json
from typing import List, Dict, Any
from language_analyzer import AnalysisResult, ChunkInfo, TokenInfo


class DataFormatter:
    """
    언어 분석 결과를 기존 CSV 형식에 맞게 변환하는 클래스
    """
    
    def format_slash_translate(self, analysis: AnalysisResult) -> List[Dict[str, Any]]:
        """
        slash_translate 형식으로 청크 정보 포맷팅
        기존 형식: [{'start_idx': 0, 'end_idx': 6, 'sentence': '...', 'translation': '...', 'words': [...]}]
        
        Args:
            analysis: 언어 분석 결과
            
        Returns:
            List[Dict]: slash_translate 형식의 데이터
        """
        slash_data = []
        
        for chunk in analysis.chunks:
            # 청크별 번역 처리
            # 실제 프로덕션에서는 번역 서비스를 연동해야 하지만,
            # 현재는 전체 번역을 청크 텍스트에 맞춰 부분적으로 매핑
            translation = self._get_chunk_translation(chunk, analysis.translation)
            
            chunk_data = {
                'start_idx': chunk.start_idx,
                'end_idx': chunk.end_idx,
                'sentence': chunk.text,
                'translation': translation,
                'words': chunk.words
            }
            slash_data.append(chunk_data)
            
        return slash_data
    
    def _get_chunk_translation(self, chunk: ChunkInfo, full_translation: str) -> str:
        """청크에 해당하는 번역 부분 추출"""
        if not full_translation:
            return ""
        
        # 간단한 휴리스틱: 청크 텍스트 길이에 비례한 번역 부분 추출
        # 실제로는 더 정교한 매핑이 필요함
        chunk_words_ratio = len(chunk.words) / 20  # 대략적인 비율
        
        # 번역을 단어 단위로 분리
        translation_words = full_translation.split()
        
        # 청크에 해당하는 대략적인 번역 부분 선택
        start_idx = int(chunk.start_idx * chunk_words_ratio * len(translation_words))
        end_idx = min(start_idx + len(chunk.words), len(translation_words))
        
        if start_idx < len(translation_words):
            return ' '.join(translation_words[start_idx:end_idx])
        else:
            return ""
    
    def format_tag_info(self, analysis: AnalysisResult) -> List[Dict[str, Any]]:
        """
        tag_info 형식으로 문법 정보 포맷팅
        기존 형식: [{'tag': '...', 'category': '...', 'words': [{'word': '...', 'word_index': n, 'part_of_speech': '...'}]}]
        
        Args:
            analysis: 언어 분석 결과
            
        Returns:
            List[Dict]: tag_info 형식의 데이터
        """
        # 기본적으로 grammatical_analysis 결과를 사용
        tag_data = analysis.grammatical_analysis.copy()
        
        # 주석이 있으면 주석만 사용, 없으면 추가 태그 생성
        if hasattr(analysis, 'syntax_annotations') and analysis.syntax_annotations:
            # 주석이 있는 경우: 제공된 한국어 태그만 사용
            return tag_data
        else:
            # 주석이 없는 경우: 추가적인 구문 분석 태그 생성
            tag_data.extend(self._generate_additional_tags(analysis))
            return tag_data
    
    def _generate_additional_tags(self, analysis: AnalysisResult) -> List[Dict[str, Any]]:
        """추가적인 문법 태그 생성"""
        additional_tags = []
        
        # 병렬 구조 분석
        parallel_tags = self._analyze_parallel_structures(analysis.tokens)
        additional_tags.extend(parallel_tags)
        
        # 구문 패턴 분석
        pattern_tags = self._analyze_sentence_patterns(analysis.tokens)
        additional_tags.extend(pattern_tags)
        
        # 부정 구조 분석
        negation_tags = self._analyze_negations(analysis.tokens)
        additional_tags.extend(negation_tags)
        
        return additional_tags
    
    def _analyze_parallel_structures(self, tokens: List[TokenInfo]) -> List[Dict[str, Any]]:
        """병렬 구조 분석"""
        parallel_tags = []
        
        # 'and', 'or' 연결된 구조 찾기
        for i, token in enumerate(tokens):
            if token.word.lower() in ['and', 'or'] and not token.is_punct:
                # 앞뒤 토큰 검사하여 병렬 구조 판단
                if i > 0 and i < len(tokens) - 1:
                    prev_token = tokens[i-1]
                    next_token = tokens[i+1]
                    
                    if prev_token.pos == next_token.pos:
                        parallel_type = self._determine_parallel_type(prev_token.pos)
                        if parallel_type:
                            parallel_tags.append({
                                'tag': parallel_type,
                                'category': '구문',
                                'words': [
                                    {
                                        'word': prev_token.word,
                                        'word_index': prev_token.index,
                                        'part_of_speech': prev_token.pos
                                    },
                                    {
                                        'word': token.word,
                                        'word_index': token.index,
                                        'part_of_speech': token.pos
                                    },
                                    {
                                        'word': next_token.word,
                                        'word_index': next_token.index,
                                        'part_of_speech': next_token.pos
                                    }
                                ]
                            })
        
        return parallel_tags
    
    def _determine_parallel_type(self, pos: str) -> str:
        """병렬 구조 유형 결정"""
        parallel_types = {
            'NOUN': 'n1 and n2 병렬',
            'VERB': 'v1 and v2 병렬',
            'ADJ': 'adj1 and adj2 병렬',
            'ADV': 'adv1 and adv2 병렬'
        }
        return parallel_types.get(pos, '')
    
    def _analyze_sentence_patterns(self, tokens: List[TokenInfo]) -> List[Dict[str, Any]]:
        """문장 형식 분석"""
        pattern_tags = []
        
        # be동사 + 형용사 패턴
        for i, token in enumerate(tokens):
            if token.word.lower() in ['is', 'are', 'was', 'were', 'am']:
                # 다음 토큰이 형용사인지 확인
                if i < len(tokens) - 1 and tokens[i+1].pos == 'ADJ':
                    pattern_tags.append({
                        'tag': 'be동사 + 형용사',
                        'category': '문장형식',
                        'words': [
                            {
                                'word': token.word,
                                'word_index': token.index,
                                'part_of_speech': 'VERB'
                            },
                            {
                                'word': tokens[i+1].word,
                                'word_index': tokens[i+1].index,
                                'part_of_speech': 'ADJ'
                            }
                        ]
                    })
        
        return pattern_tags
    
    def _analyze_negations(self, tokens: List[TokenInfo]) -> List[Dict[str, Any]]:
        """부정 구조 분석"""
        negation_tags = []
        
        for i, token in enumerate(tokens):
            if token.word.lower() in ['not', "n't"]:
                # 부정 구조 분석
                if i > 0:
                    prev_token = tokens[i-1]
                    
                    if prev_token.word.lower() in ['do', 'does', 'did']:
                        # 일반동사 부정 찾기
                        verb_token = None
                        for j in range(i+1, min(i+3, len(tokens))):
                            if tokens[j].pos == 'VERB':
                                verb_token = tokens[j]
                                break
                        
                        if verb_token:
                            negation_tags.append({
                                'tag': '일반동사 부정',
                                'category': '부정',
                                'words': [
                                    {
                                        'word': prev_token.word,
                                        'word_index': prev_token.index,
                                        'part_of_speech': 'VERB'
                                    },
                                    {
                                        'word': token.word,
                                        'word_index': token.index,
                                        'part_of_speech': 'ADV'
                                    },
                                    {
                                        'word': verb_token.word,
                                        'word_index': verb_token.index,
                                        'part_of_speech': 'VERB'
                                    }
                                ]
                            })
                    
                    elif prev_token.word.lower() in ['is', 'are', 'was', 'were', 'am']:
                        # be동사 부정
                        negation_tags.append({
                            'tag': 'be동사 부정',
                            'category': '부정',
                            'words': [
                                {
                                    'word': prev_token.word,
                                    'word_index': prev_token.index,
                                    'part_of_speech': 'VERB'
                                },
                                {
                                    'word': token.word,
                                    'word_index': token.index,
                                    'part_of_speech': 'ADV'
                                }
                            ]
                        })
        
        return negation_tags
    
    def format_pos_sequence(self, analysis: AnalysisResult) -> str:
        """POS 태그 시퀀스 문자열 생성"""
        pos_tags = [token.pos for token in analysis.tokens if not token.is_punct]
        return ' '.join(pos_tags)
    
    def format_chunks_string(self, analysis: AnalysisResult) -> str:
        """청크를 기존 형식의 문자열로 변환"""
        chunk_parts = []
        
        # 청크를 카테고리별로 분류
        for chunk in analysis.chunks:
            category = self._classify_chunk_category(chunk)
            chunk_str = f"[{category} {' '.join(chunk.words)}]"
            chunk_parts.append(chunk_str)
        
        return ' '.join(chunk_parts)
    
    def _classify_chunk_category(self, chunk: ChunkInfo) -> str:
        """청크를 카테고리로 분류"""
        # 간단한 휴리스틱 기반 분류
        words = [w.lower() for w in chunk.words]
        
        # 동사 그룹
        if any(pos in chunk.pos_pattern for pos in ['VERB']):
            return 'verbs'
        
        # 전치사 그룹
        elif any(w in ['in', 'on', 'at', 'by', 'for', 'with', 'to', 'from'] for w in words):
            return 'prepositions'
        
        # 접속사 그룹
        elif any(w in ['and', 'or', 'but', 'if', 'when', 'that'] for w in words):
            return 'connectors'
        
        # 기타
        else:
            return 'others'
    
    def create_grammatical_roles_string(self, analysis: AnalysisResult) -> str:
        """문법적 역할 설명 문자열 생성"""
        roles = []
        
        for tag_info in analysis.grammatical_analysis:
            tag_name = tag_info['tag']
            category = tag_info['category']
            role_desc = f"{category}:{tag_name}"
            roles.append(role_desc)
        
        return ' | '.join(roles)


if __name__ == "__main__":
    # 테스트 실행
    from language_analyzer import LanguageAnalyzer
    
    analyzer = LanguageAnalyzer()
    formatter = DataFormatter()
    
    test_sentence = "The students who study hard will pass the exam."
    analysis = analyzer.analyze(test_sentence)
    
    slash_translate = formatter.format_slash_translate(analysis)
    tag_info = formatter.format_tag_info(analysis)
    
    print("Slash translate format:")
    print(json.dumps(slash_translate, indent=2, ensure_ascii=False))
    
    print("\nTag info format:")
    print(json.dumps(tag_info, indent=2, ensure_ascii=False))