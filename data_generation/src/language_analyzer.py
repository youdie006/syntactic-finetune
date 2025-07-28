#!/usr/bin/env python3
"""
Language Analyzer - 영어 문장의 구문 분석을 수행
"""

import spacy
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class TokenInfo:
    """토큰 정보를 담는 데이터 클래스"""
    word: str
    index: int
    pos: str
    tag: str
    dep: str
    head_index: int
    is_punct: bool


@dataclass
class ChunkInfo:
    """구문 청크 정보를 담는 데이터 클래스"""
    start_idx: int
    end_idx: int
    text: str
    words: List[str]
    pos_pattern: str


@dataclass
class AnalysisResult:
    """전체 분석 결과를 담는 데이터 클래스"""
    sentence: str
    tokens: List[TokenInfo]
    chunks: List[ChunkInfo]
    pos_tags: List[str]
    grammatical_analysis: List[Dict[str, Any]]


class LanguageAnalyzer:
    """
    spaCy를 사용한 영어 구문 분석기
    """
    
    def __init__(self):
        """spaCy 모델 로드"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("❌ spaCy English model not found. Please install it:")
            print("python -m spacy download en_core_web_sm")
            raise
    
    def analyze(self, sentence: str) -> AnalysisResult:
        """
        문장을 분석하여 구문 정보 추출
        
        Args:
            sentence: 분석할 영어 문장
            
        Returns:
            AnalysisResult: 분석 결과
        """
        doc = self.nlp(sentence)
        
        # 토큰 정보 추출
        tokens = self._extract_tokens(doc)
        
        # 청크 정보 생성
        chunks = self._create_chunks(tokens)
        
        # POS 태그 추출
        pos_tags = [token.pos for token in tokens if not token.is_punct]
        
        # 문법적 분석
        grammatical_analysis = self._analyze_grammar(tokens, doc)
        
        return AnalysisResult(
            sentence=sentence,
            tokens=tokens,
            chunks=chunks,
            pos_tags=pos_tags,
            grammatical_analysis=grammatical_analysis
        )
    
    def _extract_tokens(self, doc) -> List[TokenInfo]:
        """spaCy 문서에서 토큰 정보 추출"""
        tokens = []
        
        for i, token in enumerate(doc):
            token_info = TokenInfo(
                word=token.text,
                index=i,
                pos=self._map_pos_tag(token.pos_),
                tag=token.tag_,
                dep=token.dep_,
                head_index=token.head.i if token.head != token else i,
                is_punct=token.is_punct
            )
            tokens.append(token_info)
            
        return tokens
    
    def _map_pos_tag(self, spacy_pos: str) -> str:
        """spaCy POS 태그를 기존 CSV 형식에 맞게 매핑"""
        pos_mapping = {
            'VERB': 'VERB',
            'NOUN': 'NOUN', 
            'ADJ': 'ADJ',
            'ADV': 'ADV',
            'ADP': 'ADP',  # 전치사
            'DET': 'DET',  # 관사, 한정사
            'PRON': 'PRON',
            'CONJ': 'CONJ',
            'CCONJ': 'CONJ',
            'SCONJ': 'ADP',  # 種속접속사는 ADP로 매핑
            'PRT': 'PRT',   # 불변화사
            'PUNCT': 'PUNCT',
            'NUM': 'NUM',
            'X': 'X'
        }
        return pos_mapping.get(spacy_pos, spacy_pos)
    
    def _create_chunks(self, tokens: List[TokenInfo]) -> List[ChunkInfo]:
        """토큰을 기반으로 의미 있는 청크 생성"""
        chunks = []
        current_chunk = []
        chunk_start = 0
        
        for i, token in enumerate(tokens):
            if token.is_punct and token.word in ['.', '!', '?']:
                # 문장 끝 처리
                if current_chunk:
                    chunk = self._create_chunk_from_tokens(current_chunk, chunk_start)
                    chunks.append(chunk)
                    current_chunk = []
                continue
                
            elif token.word in [',', ';'] or (token.pos == 'ADP' and len(current_chunk) > 3):
                # 구문 경계 처리
                if current_chunk:
                    chunk = self._create_chunk_from_tokens(current_chunk, chunk_start)
                    chunks.append(chunk)
                    current_chunk = []
                    chunk_start = i
                    
            current_chunk.append(token)
        
        # 마지막 청크 처리
        if current_chunk:
            chunk = self._create_chunk_from_tokens(current_chunk, chunk_start)
            chunks.append(chunk)
            
        return chunks
    
    def _create_chunk_from_tokens(self, tokens: List[TokenInfo], start_idx: int) -> ChunkInfo:
        """토큰 리스트에서 청크 정보 생성"""
        words = [token.word for token in tokens if not token.is_punct]
        text = ' '.join(words)
        pos_pattern = ' '.join([token.pos for token in tokens if not token.is_punct])
        
        return ChunkInfo(
            start_idx=start_idx,
            end_idx=start_idx + len(tokens) - 1,
            text=text,
            words=words,
            pos_pattern=pos_pattern
        )
    
    def _analyze_grammar(self, tokens: List[TokenInfo], doc) -> List[Dict[str, Any]]:
        """문법적 구조 분석"""
        grammar_tags = []
        
        # 동사 시제 분석
        grammar_tags.extend(self._analyze_verb_tenses(tokens, doc))
        
        # 전치사 분석
        grammar_tags.extend(self._analyze_prepositions(tokens))
        
        # 접속사 분석
        grammar_tags.extend(self._analyze_conjunctions(tokens))
        
        # 관계사 분석
        grammar_tags.extend(self._analyze_relatives(tokens))
        
        return grammar_tags
    
    def _analyze_verb_tenses(self, tokens: List[TokenInfo], doc) -> List[Dict[str, Any]]:
        """동사 시제 분석"""
        verb_tags = []
        
        for token in doc:
            if token.pos_ == 'VERB':
                tense_info = self._determine_tense(token)
                if tense_info:
                    verb_tags.append({
                        'tag': tense_info,
                        'category': '동사_시제',
                        'words': [{
                            'word': token.text,
                            'word_index': token.i,
                            'part_of_speech': 'VERB'
                        }]
                    })
                    
        return verb_tags
    
    def _determine_tense(self, token) -> str:
        """동사의 시제 판단"""
        if token.tag_ in ['VBD', 'VBN']:
            return '단순 과거'
        elif token.tag_ in ['VBZ', 'VBP']:
            if token.tag_ == 'VBZ':
                return '단순 현재 — 3인칭 단수 주어'
            else:
                return '단순 현재'
        elif token.tag_ == 'VBG':
            return '현재진행'
        elif token.lemma_ in ['have', 'has'] and any(child.tag_ == 'VBN' for child in token.children):
            return '현재완료'
        
        return '단순 현재'
    
    def _analyze_prepositions(self, tokens: List[TokenInfo]) -> List[Dict[str, Any]]:
        """전치사 분석"""
        prep_tags = []
        
        for token in tokens:
            if token.pos == 'ADP':
                prep_tags.append({
                    'tag': f'전치사 {token.word}',
                    'category': '전치사',
                    'words': [{
                        'word': token.word,
                        'word_index': token.index,
                        'part_of_speech': 'ADP'
                    }]
                })
                
        return prep_tags
    
    def _analyze_conjunctions(self, tokens: List[TokenInfo]) -> List[Dict[str, Any]]:
        """접속사 분석"""
        conj_tags = []
        
        for token in tokens:
            if token.pos == 'CONJ' or token.word.lower() in ['and', 'or', 'but', 'if', 'when', 'that', 'because']:
                conj_type = self._classify_conjunction(token.word.lower())
                conj_tags.append({
                    'tag': conj_type,
                    'category': '접속사',
                    'words': [{
                        'word': token.word,
                        'word_index': token.index,
                        'part_of_speech': token.pos
                    }]
                })
                
        return conj_tags
    
    def _classify_conjunction(self, word: str) -> str:
        """접속사 유형 분류"""
        coordinating_conj = {
            'and': '등위접속사 and',
            'or': '등위접속사 or', 
            'but': '등위접속사 but'
        }
        
        subordinating_conj = {
            'if': '종속접속사 if 부사역할 — 조건',
            'when': '종속접속사 when 부사역할 — 시간',
            'that': '종속접속사 that 명사역할 — 목적어',
            'because': '종속접속사 because 부사역할 — 이유'
        }
        
        return coordinating_conj.get(word) or subordinating_conj.get(word) or f'접속사 {word}'
    
    def _analyze_relatives(self, tokens: List[TokenInfo]) -> List[Dict[str, Any]]:
        """관계사 분석"""
        rel_tags = []
        
        for token in tokens:
            if token.word.lower() in ['who', 'which', 'that', 'where', 'when']:
                rel_type = self._classify_relative(token.word.lower())
                rel_tags.append({
                    'tag': rel_type,
                    'category': '관계사',
                    'words': [{
                        'word': token.word,
                        'word_index': token.index,
                        'part_of_speech': token.pos
                    }]
                })
                
        return rel_tags
    
    def _classify_relative(self, word: str) -> str:
        """관계사 유형 분류"""
        relative_types = {
            'who': '주격 관계대명사 who 형용사역할',
            'which': '주격 관계대명사 which 형용사역할',
            'that': '주격 관계대명사 that 형용사역할',
            'where': '관계부사 where',
            'when': '관계부사 when'
        }
        
        return relative_types.get(word, f'관계사 {word}')


if __name__ == "__main__":
    # 테스트 실행
    analyzer = LanguageAnalyzer()
    
    test_sentence = "The students who study hard will pass the exam."
    result = analyzer.analyze(test_sentence)
    
    print(f"Sentence: {result.sentence}")
    print(f"Tokens: {len(result.tokens)}")
    print(f"Chunks: {len(result.chunks)}")
    print(f"Grammar tags: {len(result.grammatical_analysis)}")