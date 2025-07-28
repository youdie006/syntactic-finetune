#!/usr/bin/env python3
"""
동적 전략 생성기 - 사용자가 지정한 카테고리 수에 따라 자동으로 태그 전략을 생성
"""

import json
import os
from typing import Dict, List, Tuple
from datetime import datetime
from collections import defaultdict


class DynamicStrategyGenerator:
    """사용자 정의 카테고리 수에 따른 동적 전략 생성기"""
    
    def __init__(self, analysis_file: str = "results/category_analysis.json"):
        """
        Args:
            analysis_file: 카테고리 분석 결과 파일 경로
        """
        self.analysis_file = analysis_file
        self.category_analysis = self._load_analysis()
        
        # 원본 17개 카테고리
        self.original_categories = [
            '전치사', '동사_시제', '접속사', '준동사', '구문', '구동사, 관용어',
            '문장형식', '조동사', '관계사', '명사', '비교구문', '부정', 
            '동사_태', '의문사', '연결어', '가정법', '도치'
        ]
        
        # 의미적 그룹 정의 (분석 결과 기반)
        self.semantic_groups = {
            'verb_related': ['동사_시제', '동사_태', '조동사'],
            'connecting_words': ['접속사', '연결어', '관계사'],
            'prepositions': ['전치사'],
            'sentence_structure': ['문장형식', '구문'],
            'modification': ['부정', '비교구문'],
            'special_constructions': ['의문사', '가정법', '도치'],
            'word_classes': ['명사', '준동사', '구동사, 관용어']
        }
        
        # 빈도 기반 그룹 (분석 결과 기반)
        self.frequency_groups = {
            'high': ['전치사', '동사_시제', '접속사', '준동사', '구문'],
            'medium': ['구동사, 관용어', '문장형식', '조동사', '관계사', '명사', '비교구문'],
            'low': ['부정', '동사_태', '의문사', '연결어', '가정법', '도치']
        }
    
    def _load_analysis(self) -> Dict:
        """분석 결과 파일 로드"""
        if not os.path.exists(self.analysis_file):
            print(f"⚠️ 분석 파일이 없습니다: {self.analysis_file}")
            print("먼저 analyze_categories.py를 실행해주세요.")
            return {}
        
        with open(self.analysis_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def generate_strategy(self, target_categories: int, strategy_name: str = None) -> Dict:
        """
        지정된 카테고리 수에 맞는 전략 생성
        
        Args:
            target_categories: 목표 카테고리 수 (2-17)
            strategy_name: 전략 이름 (없으면 자동 생성)
            
        Returns:
            생성된 전략 딕셔너리
        """
        if not (2 <= target_categories <= 17):
            raise ValueError("카테고리 수는 2-17 사이여야 합니다.")
        
        if strategy_name is None:
            strategy_name = f"dynamic_{target_categories}cats"
        
        print(f"🎯 {target_categories}개 카테고리 전략 생성 중: {strategy_name}")
        
        # 카테고리 병합 계획 수립
        merge_plan = self._create_merge_plan(target_categories)
        
        # 전략 딕셔너리 생성
        strategy = {
            'name': strategy_name,
            'version': f"dynamic_v1.0_{datetime.now().strftime('%Y%m%d')}",
            'description': f"Dynamic strategy with {target_categories} categories - auto-generated based on frequency and semantic similarity",
            'created_date': datetime.now().strftime('%Y-%m-%d'),
            'strategy_type': 'dynamic_merged',
            'tag_mapping': {
                'syntax_groups': merge_plan['mapping']
            },
            'output_format': {
                'chunk_format': '[{category} {words}]',
                'role_format': '{category}:{tag}',
                'separator': ' | ',
                'include_dynamic_info': True
            },
            'quality_filters': {
                'min_sentence_length': 10,
                'max_sentence_length': 500,
                'min_tags_per_sentence': 1,
                'max_tags_per_sentence': 50,
                'balance_by_frequency': True
            },
            'statistics': {
                'total_categories': target_categories,
                'original_categories': 17,
                'merge_groups': len(merge_plan['groups']),
                'target_distribution': 'frequency_balanced'
            },
            'merge_details': merge_plan['details']
        }
        
        return strategy
    
    def _create_merge_plan(self, target_categories: int) -> Dict:
        """카테고리 병합 계획 수립"""
        
        if target_categories == 17:
            # 원본 그대로 유지
            return self._create_original_plan()
        elif target_categories >= 12:
            # 저빈도만 병합
            return self._create_conservative_merge_plan(target_categories)
        elif target_categories >= 8:
            # 중간 수준 병합
            return self._create_moderate_merge_plan(target_categories)
        else:
            # 적극적 병합
            return self._create_aggressive_merge_plan(target_categories)
    
    def _create_original_plan(self) -> Dict:
        """원본 17개 카테고리 유지"""
        mapping = {}
        for cat in self.original_categories:
            mapping[cat] = [cat]
        
        return {
            'mapping': mapping,
            'groups': [[cat] for cat in self.original_categories],
            'details': {
                'strategy': 'original',
                'description': '원본 카테고리 그대로 유지'
            }
        }
    
    def _create_conservative_merge_plan(self, target_categories: int) -> Dict:
        """보수적 병합 (12-16 카테고리)"""
        # 저빈도 카테고리만 병합
        mapping = {}
        groups = []
        
        # 고빈도 + 중빈도 카테고리는 유지
        keep_categories = self.frequency_groups['high'] + self.frequency_groups['medium']
        for cat in keep_categories:
            mapping[cat] = [cat]
            groups.append([cat])
        
        # 저빈도 카테고리들 병합
        low_freq = self.frequency_groups['low']
        remaining_slots = target_categories - len(keep_categories)
        
        if remaining_slots >= len(low_freq):
            # 모든 저빈도 카테고리 개별 유지
            for cat in low_freq:
                mapping[cat] = [cat]
                groups.append([cat])
        else:
            # 저빈도 카테고리들을 의미적으로 병합
            low_groups = self._merge_by_semantics(low_freq, remaining_slots)
            for i, group in enumerate(low_groups):
                group_name = f"special_constructions_{i+1}" if len(group) > 1 else group[0]
                mapping[group_name] = group
                groups.append(group)
        
        return {
            'mapping': mapping,
            'groups': groups,
            'details': {
                'strategy': 'conservative',
                'description': f'저빈도 카테고리 위주 병합으로 {target_categories}개 카테고리 생성'
            }
        }
    
    def _create_moderate_merge_plan(self, target_categories: int) -> Dict:
        """중간 수준 병합 (8-11 카테고리)"""
        mapping = {}
        groups = []
        
        # 고빈도 카테고리는 대부분 유지
        high_freq = self.frequency_groups['high']
        for cat in high_freq:
            mapping[cat] = [cat]
            groups.append([cat])
        
        current_count = len(high_freq)
        remaining_slots = target_categories - current_count
        
        # 중빈도 + 저빈도 카테고리들을 의미적으로 병합
        merge_candidates = self.frequency_groups['medium'] + self.frequency_groups['low']
        merged_groups = self._merge_by_semantics(merge_candidates, remaining_slots)
        
        for i, group in enumerate(merged_groups):
            if len(group) == 1:
                group_name = group[0]
            else:
                # 의미적 그룹명 찾기
                group_name = self._find_semantic_group_name(group)
            
            mapping[group_name] = group
            groups.append(group)
        
        return {
            'mapping': mapping,
            'groups': groups,
            'details': {
                'strategy': 'moderate',
                'description': f'의미적 유사성 기반 병합으로 {target_categories}개 카테고리 생성'
            }
        }
    
    def _create_aggressive_merge_plan(self, target_categories: int) -> Dict:
        """적극적 병합 (2-7 카테고리)"""
        mapping = {}
        groups = []
        
        if target_categories <= 5:
            # 극단적 병합: 주요 의미 그룹으로만 구성
            core_groups = [
                (['전치사'], 'prepositions'),
                (['동사_시제', '동사_태', '조동사'], 'verbs'),
                (['접속사', '연결어', '관계사'], 'connectors'),
                (['문장형식', '구문'], 'structures'),
                (['명사', '준동사', '구동사, 관용어', '부정', '비교구문', '의문사', '연결어', '가정법', '도치'], 'others')
            ]
            
            selected_groups = core_groups[:target_categories]
            
            for group_cats, group_name in selected_groups:
                mapping[group_name] = group_cats
                groups.append(group_cats)
        
        else:
            # 의미적 그룹 기반 병합
            semantic_mapping = {
                'verbs': ['동사_시제', '동사_태', '조동사'],
                'connectors': ['접속사', '연결어', '관계사'],
                'prepositions': ['전치사'],
                'structures': ['문장형식', '구문'],
                'words': ['명사', '준동사'],
                'phrases': ['구동사, 관용어'],
                'special': ['의문사', '가정법', '도치', '부정', '비교구문']
            }
            
            # target_categories에 맞게 조정
            if target_categories == 6:
                semantic_mapping['modifiers'] = semantic_mapping.pop('special')
            elif target_categories == 7:
                semantic_mapping['modifiers'] = ['부정', '비교구문']
                semantic_mapping['special'] = ['의문사', '가정법', '도치']
            
            # 필요한 만큼만 선택
            selected_keys = list(semantic_mapping.keys())[:target_categories]
            for key in selected_keys:
                mapping[key] = semantic_mapping[key]
                groups.append(semantic_mapping[key])
        
        return {
            'mapping': mapping,
            'groups': groups,
            'details': {
                'strategy': 'aggressive',
                'description': f'주요 의미 그룹 중심으로 {target_categories}개 카테고리 생성'
            }
        }
    
    def _merge_by_semantics(self, categories: List[str], target_count: int) -> List[List[str]]:
        """의미적 유사성에 따라 카테고리들을 병합"""
        if target_count >= len(categories):
            return [[cat] for cat in categories]
        
        # 의미적 그룹별로 카테고리 분류
        semantic_clusters = defaultdict(list)
        
        for cat in categories:
            for group_name, group_cats in self.semantic_groups.items():
                if cat in group_cats:
                    semantic_clusters[group_name].append(cat)
                    break
            else:
                semantic_clusters['misc'].append(cat)
        
        # 클러스터를 target_count에 맞게 조정
        result_groups = []
        
        # 각 의미적 클러스터를 하나씩 처리
        for cluster_cats in semantic_clusters.values():
            if len(result_groups) < target_count:
                result_groups.append(cluster_cats)
        
        # 남은 그룹들을 기존 그룹에 병합
        while len(result_groups) > target_count:
            # 가장 작은 두 그룹을 병합
            result_groups.sort(key=len)
            smallest = result_groups.pop(0)
            result_groups[0].extend(smallest)
        
        return result_groups
    
    def _find_semantic_group_name(self, categories: List[str]) -> str:
        """카테고리 그룹의 의미적 이름 찾기"""
        # 의미적 그룹과 매칭
        for group_name, group_cats in self.semantic_groups.items():
            if any(cat in group_cats for cat in categories):
                if group_name == 'verb_related':
                    return 'verbs'
                elif group_name == 'connecting_words':
                    return 'connectors'
                elif group_name == 'sentence_structure':
                    return 'structures'
                elif group_name == 'word_classes':
                    return 'words'
                elif group_name == 'modification':
                    return 'modifiers'
                elif group_name == 'special_constructions':
                    return 'special'
                else:
                    return group_name
        
        # 매칭되지 않으면 첫 번째 카테고리 이름 사용
        return categories[0] if categories else 'misc'
    
    def save_strategy(self, strategy: Dict, output_dir: str = "configs/tag_strategies") -> str:
        """생성된 전략을 파일로 저장"""
        import yaml
        
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{strategy['name']}.yaml"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(strategy, f, default_flow_style=False, allow_unicode=True)
        
        print(f"💾 전략이 저장되었습니다: {filepath}")
        return filepath


def main():
    """테스트용 메인 함수"""
    generator = DynamicStrategyGenerator()
    
    # 여러 카테고리 수로 테스트
    test_cases = [5, 8, 12, 15]
    
    for target in test_cases:
        print(f"\n{'='*60}")
        strategy = generator.generate_strategy(target)
        
        print(f"전략명: {strategy['name']}")
        print(f"카테고리 수: {strategy['statistics']['total_categories']}")
        print(f"병합 전략: {strategy['merge_details']['strategy']}")
        print("카테고리 매핑:")
        
        for new_cat, orig_cats in strategy['tag_mapping']['syntax_groups'].items():
            if len(orig_cats) == 1:
                print(f"  • {new_cat}: (유지)")
            else:
                print(f"  • {new_cat}: {' + '.join(orig_cats)}")


if __name__ == "__main__":
    main()