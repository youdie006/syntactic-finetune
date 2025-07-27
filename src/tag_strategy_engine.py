#!/usr/bin/env python3
"""
Tag Strategy Engine - 다양한 태그 분류 전략을 적용하는 엔진
"""

import yaml
import os
import re
from typing import Dict, List, Any, Tuple
from datetime import datetime
from dynamic_strategy_generator import DynamicStrategyGenerator


class TagStrategyEngine:
    """태그 분류 전략을 로드하고 적용하는 엔진"""
    
    def __init__(self, config_dir: str = "configs/tag_strategies"):
        self.config_dir = config_dir
        self.strategies = {}
        self.current_strategy = None
        self.dynamic_generator = DynamicStrategyGenerator()
        self.load_all_strategies()
    
    def load_all_strategies(self):
        """모든 전략 설정 파일을 로드"""
        if not os.path.exists(self.config_dir):
            print(f"Warning: Config directory {self.config_dir} not found")
            return
        
        for filename in os.listdir(self.config_dir):
            if filename.endswith('.yaml') or filename.endswith('.yml'):
                strategy_path = os.path.join(self.config_dir, filename)
                try:
                    with open(strategy_path, 'r', encoding='utf-8') as f:
                        strategy = yaml.safe_load(f)
                    
                    strategy_name = strategy.get('name', filename.split('.')[0])
                    self.strategies[strategy_name] = strategy
                    
                    print(f"✅ Loaded strategy: {strategy_name} ({strategy.get('version', 'unknown')})")
                    
                except Exception as e:
                    print(f"❌ Failed to load {filename}: {e}")
    
    def set_strategy(self, strategy_name: str):
        """특정 전략을 현재 전략으로 설정"""
        if strategy_name not in self.strategies:
            raise ValueError(f"Strategy '{strategy_name}' not found. Available: {list(self.strategies.keys())}")
        
        self.current_strategy = self.strategies[strategy_name]
        print(f"🎯 Set strategy to: {strategy_name}")
        return self.current_strategy
    
    def list_strategies(self) -> List[Dict]:
        """사용 가능한 모든 전략 목록 반환"""
        return [
            {
                'name': name,
                'version': strategy.get('version', 'unknown'),
                'description': strategy.get('description', 'No description'),
                'categories': strategy.get('statistics', {}).get('total_categories', 'unknown')
            }
            for name, strategy in self.strategies.items()
        ]
    
    def apply_strategy(self, tag_info: List[Dict]) -> Tuple[str, str, str]:
        """
        현재 전략을 적용하여 태그 정보를 변환
        
        Args:
            tag_info: 원본 태그 정보 리스트
            
        Returns:
            Tuple of (chunks, pos_tags, grammatical_roles)
        """
        if not self.current_strategy:
            raise ValueError("No strategy set. Use set_strategy() first.")
        
        strategy_type = self.current_strategy.get('strategy_type', 'original')
        
        if strategy_type == 'original':
            return self._apply_original_strategy(tag_info)
        elif strategy_type == 'merged':
            return self._apply_merged_strategy(tag_info)
        elif strategy_type == 'expanded':
            return self._apply_expanded_strategy(tag_info)
        elif strategy_type == 'frequency_weighted':
            return self._apply_frequency_strategy(tag_info)
        elif strategy_type == 'dynamic_merged':
            return self._apply_dynamic_strategy(tag_info)
        else:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
    
    def _apply_original_strategy(self, tag_info: List[Dict]) -> Tuple[str, str, str]:
        """기본 전략 적용 - 원본 태그 그대로 사용"""
        chunks = []
        pos_tags = []
        roles = []
        
        for item in tag_info:
            category = item.get('category', 'UNK')
            tag = item.get('tag', '')
            words = item.get('words', [])
            
            # 청크 생성
            word_list = [word_item['word'] for word_item in words]
            if word_list:
                chunks.append(f"[{category} {' '.join(word_list)}]")
            
            # POS 태그 수집
            for word_item in words:
                pos_tags.append(word_item.get('part_of_speech', 'UNK'))
            
            # 문법 역할 생성
            roles.append(f"{category}:{tag}")
        
        return ' '.join(chunks), ' '.join(pos_tags), ' | '.join(roles)
    
    def _apply_merged_strategy(self, tag_info: List[Dict]) -> Tuple[str, str, str]:
        """단순화 전략 적용 - 카테고리 통합"""
        mapping = self.current_strategy['tag_mapping']['syntax_groups']
        
        # 역방향 매핑 생성 (원본 카테고리 -> 통합 카테고리)
        reverse_mapping = {}
        for merged_cat, original_cats in mapping.items():
            for orig_cat in original_cats:
                reverse_mapping[orig_cat] = merged_cat
        
        chunks = []
        pos_tags = []
        roles = []
        
        for item in tag_info:
            original_category = item.get('category', 'UNK')
            tag = item.get('tag', '')
            words = item.get('words', [])
            
            # 카테고리 매핑
            mapped_category = reverse_mapping.get(original_category, original_category)
            
            # 청크 생성
            word_list = [word_item['word'] for word_item in words]
            if word_list:
                chunks.append(f"[{mapped_category} {' '.join(word_list)}]")
            
            # POS 태그 수집
            for word_item in words:
                pos_tags.append(word_item.get('part_of_speech', 'UNK'))
            
            # 문법 역할 생성
            roles.append(f"{mapped_category}:{tag}")
        
        return ' '.join(chunks), ' '.join(pos_tags), ' | '.join(roles)
    
    def _apply_expanded_strategy(self, tag_info: List[Dict]) -> Tuple[str, str, str]:
        """세분화 전략 적용 - 카테고리 확장"""
        mapping = self.current_strategy['tag_mapping']['syntax_groups']
        
        chunks = []
        pos_tags = []
        roles = []
        
        for item in tag_info:
            original_category = item.get('category', 'UNK')
            tag = item.get('tag', '')
            words = item.get('words', [])
            
            # 세분화된 카테고리 찾기
            detailed_category = self._find_detailed_category(original_category, tag, mapping)
            
            # 청크 생성
            word_list = [word_item['word'] for word_item in words]
            if word_list:
                chunks.append(f"[{detailed_category} {' '.join(word_list)}]")
            
            # POS 태그 수집
            for word_item in words:
                pos_tags.append(word_item.get('part_of_speech', 'UNK'))
            
            # 문법 역할 생성
            roles.append(f"{detailed_category}:{tag}")
        
        return ' '.join(chunks), ' '.join(pos_tags), ' | '.join(roles)
    
    def _apply_frequency_strategy(self, tag_info: List[Dict]) -> Tuple[str, str, str]:
        """빈도 기반 전략 적용"""
        mapping = self.current_strategy['tag_mapping']['syntax_groups']
        
        chunks = []
        pos_tags = []
        roles = []
        
        for item in tag_info:
            original_category = item.get('category', 'UNK')
            tag = item.get('tag', '')
            words = item.get('words', [])
            
            # 빈도 기반 카테고리 찾기
            freq_category = self._find_frequency_category(original_category, tag, mapping)
            
            # 청크 생성
            word_list = [word_item['word'] for word_item in words]
            if word_list:
                chunks.append(f"[{freq_category} {' '.join(word_list)}]")
            
            # POS 태그 수집
            for word_item in words:
                pos_tags.append(word_item.get('part_of_speech', 'UNK'))
            
            # 문법 역할 생성
            roles.append(f"{freq_category}:{tag}")
        
        return ' '.join(chunks), ' '.join(pos_tags), ' | '.join(roles)
    
    def _find_detailed_category(self, original_category: str, tag: str, mapping: Dict) -> str:
        """세분화된 카테고리 찾기"""
        for detailed_cat, rules in mapping.items():
            if isinstance(rules, dict) and 'original_category' in rules:
                if rules['original_category'] == original_category:
                    # 패턴 매칭
                    patterns = rules.get('patterns', [])
                    for pattern in patterns:
                        if pattern.lower() in tag.lower():
                            return detailed_cat
            elif isinstance(rules, list) and original_category in rules:
                return detailed_cat
        
        return original_category  # 매칭되지 않으면 원본 사용
    
    def _find_frequency_category(self, original_category: str, tag: str, mapping: Dict) -> str:
        """빈도 기반 카테고리 찾기"""
        for freq_cat, rules in mapping.items():
            if isinstance(rules, dict):
                if 'original_category' in rules and rules['original_category'] == original_category:
                    patterns = rules.get('patterns', [])
                    for pattern in patterns:
                        if pattern.lower() in tag.lower():
                            return freq_cat
                elif isinstance(rules, list) and original_category in rules:
                    return freq_cat
            elif isinstance(rules, list) and original_category in rules:
                return freq_cat
        
        return original_category  # 매칭되지 않으면 원본 사용
    
    def _apply_dynamic_strategy(self, tag_info: List[Dict]) -> Tuple[str, str, str]:
        """동적 전략 적용 - 런타임에 생성된 카테고리 매핑 사용"""
        mapping = self.current_strategy['tag_mapping']['syntax_groups']
        
        # 역방향 매핑 생성 (원본 카테고리 -> 동적 카테고리)
        reverse_mapping = {}
        for dynamic_cat, original_cats in mapping.items():
            for orig_cat in original_cats:
                reverse_mapping[orig_cat] = dynamic_cat
        
        chunks = []
        pos_tags = []
        roles = []
        
        for item in tag_info:
            original_category = item.get('category', 'UNK')
            tag = item.get('tag', '')
            words = item.get('words', [])
            
            # 동적 카테고리 매핑
            mapped_category = reverse_mapping.get(original_category, original_category)
            
            # 청크 생성
            word_list = [word_item['word'] for word_item in words]
            if word_list:
                chunks.append(f"[{mapped_category} {' '.join(word_list)}]")
            
            # POS 태그 수집
            for word_item in words:
                pos_tags.append(word_item.get('part_of_speech', 'UNK'))
            
            # 문법 역할 생성
            roles.append(f"{mapped_category}:{tag}")
        
        return ' '.join(chunks), ' '.join(pos_tags), ' | '.join(roles)
    
    def create_dynamic_strategy(self, target_categories: int, strategy_name: str = None) -> str:
        """
        지정된 카테고리 수로 동적 전략 생성
        
        Args:
            target_categories: 목표 카테고리 수 (2-17)
            strategy_name: 전략 이름 (없으면 자동 생성)
            
        Returns:
            생성된 전략 이름
        """
        if strategy_name is None:
            strategy_name = f"dynamic_{target_categories}cats"
        
        # 동적 전략 생성
        strategy = self.dynamic_generator.generate_strategy(target_categories, strategy_name)
        
        # 메모리에 전략 추가
        self.strategies[strategy_name] = strategy
        
        print(f"✅ 동적 전략 생성됨: {strategy_name} ({target_categories}개 카테고리)")
        
        return strategy_name
    
    def set_dynamic_strategy(self, target_categories: int, strategy_name: str = None) -> str:
        """
        동적 전략을 생성하고 현재 전략으로 설정
        
        Args:
            target_categories: 목표 카테고리 수
            strategy_name: 전략 이름 (없으면 자동 생성)
            
        Returns:
            생성된 전략 이름
        """
        strategy_name = self.create_dynamic_strategy(target_categories, strategy_name)
        self.set_strategy(strategy_name)
        return strategy_name
    
    def save_dynamic_strategy(self, strategy_name: str) -> str:
        """동적 전략을 YAML 파일로 저장"""
        if strategy_name not in self.strategies:
            raise ValueError(f"Strategy '{strategy_name}' not found")
        
        strategy = self.strategies[strategy_name]
        return self.dynamic_generator.save_strategy(strategy, self.config_dir)
    
    def get_strategy_info(self, strategy_name: str = None) -> Dict:
        """전략 정보 반환"""
        if strategy_name:
            return self.strategies.get(strategy_name, {})
        elif self.current_strategy:
            return self.current_strategy
        else:
            return {}
    
    def save_experiment_log(self, experiment_name: str, results: Dict):
        """실험 결과 로그 저장"""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        log_entry = {
            'experiment_name': experiment_name,
            'timestamp': datetime.now().isoformat(),
            'strategy': self.current_strategy.get('name', 'unknown'),
            'strategy_version': self.current_strategy.get('version', 'unknown'),
            'results': results
        }
        
        log_file = os.path.join(log_dir, f"{experiment_name}_log.yaml")
        with open(log_file, 'w', encoding='utf-8') as f:
            yaml.dump(log_entry, f, default_flow_style=False)
        
        print(f"📝 Experiment log saved: {log_file}")


def main():
    """태그 전략 엔진 테스트"""
    engine = TagStrategyEngine()
    
    print("\n🚀 Tag Strategy Engine Test")
    print("=" * 50)
    
    # 사용 가능한 전략 목록
    print("\n📋 Available strategies:")
    for strategy in engine.list_strategies():
        print(f"  - {strategy['name']} ({strategy['version']}): {strategy['categories']} categories")
        print(f"    {strategy['description']}")
    
    # 기본 전략 설정
    engine.set_strategy('baseline')
    
    # 테스트 태그 정보
    test_tag_info = [
        {
            'tag': '단순 현재 — 3인칭 단수 주어',
            'category': '동사_시제',
            'words': [
                {'word': 'has', 'word_index': 3, 'part_of_speech': 'VERB'},
                {'word': 'tells', 'word_index': 8, 'part_of_speech': 'VERB'}
            ]
        },
        {
            'tag': '전치사 after',
            'category': '전치사',
            'words': [
                {'word': 'after', 'word_index': 15, 'part_of_speech': 'ADP'}
            ]
        }
    ]
    
    print(f"\n🧪 Testing with baseline strategy:")
    chunks, pos, roles = engine.apply_strategy(test_tag_info)
    print(f"Chunks: {chunks}")
    print(f"POS: {pos}")
    print(f"Roles: {roles}")


if __name__ == "__main__":
    main()