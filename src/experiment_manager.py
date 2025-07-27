#!/usr/bin/env python3
"""
Experiment Manager - 태그 분류 실험을 관리하는 시스템
"""

import os
import json
import yaml
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from tag_strategy_engine import TagStrategyEngine


class ExperimentManager:
    """실험 관리 및 버전 관리 시스템"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.experiments_dir = self.base_dir / "configs" / "experiments"
        self.results_dir = self.base_dir / "results" / "experiments"
        self.data_dir = self.base_dir / "data_experiments"
        
        # 디렉토리 생성
        self.experiments_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.tag_engine = TagStrategyEngine()
        
    def create_experiment(self, 
                         experiment_name: str,
                         strategy_name: str,
                         description: str = "",
                         dataset_params: Dict = None) -> str:
        """
        새로운 실험 생성
        
        Args:
            experiment_name: 실험 이름
            strategy_name: 사용할 태그 전략
            description: 실험 설명
            dataset_params: 데이터셋 생성 파라미터
            
        Returns:
            실험 ID
        """
        # 실험 ID 생성 (timestamp 기반)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        experiment_id = f"{experiment_name}_{timestamp}"
        
        # 실험 디렉토리 생성
        exp_dir = self.experiments_dir / experiment_id
        exp_dir.mkdir(exist_ok=True)
        
        # 실험 설정 파일 생성
        experiment_config = {
            'experiment_id': experiment_id,
            'experiment_name': experiment_name,
            'strategy_name': strategy_name,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'status': 'created',
            'dataset_params': dataset_params or {
                'train_ratio': 0.8,
                'valid_ratio': 0.15,
                'random_seed': 42
            },
            'files': {
                'config_file': f"{experiment_id}_config.yaml",
                'dataset_dir': f"data_experiments/{experiment_id}",
                'results_file': f"results/experiments/{experiment_id}_results.json"
            }
        }
        
        # 설정 파일 저장
        config_file = exp_dir / f"{experiment_id}_config.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(experiment_config, f, default_flow_style=False)
        
        print(f"✅ Created experiment: {experiment_id}")
        print(f"   Strategy: {strategy_name}")
        print(f"   Config: {config_file}")
        
        return experiment_id
    
    def list_experiments(self) -> List[Dict]:
        """모든 실험 목록 반환"""
        experiments = []
        
        for exp_dir in self.experiments_dir.iterdir():
            if exp_dir.is_dir():
                config_files = list(exp_dir.glob("*_config.yaml"))
                if config_files:
                    try:
                        with open(config_files[0], 'r', encoding='utf-8') as f:
                            config = yaml.safe_load(f)
                        experiments.append(config)
                    except Exception as e:
                        print(f"Warning: Failed to load {config_files[0]}: {e}")
        
        # 생성 시간 순으로 정렬
        experiments.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return experiments
    
    def get_experiment(self, experiment_id: str) -> Optional[Dict]:
        """특정 실험 정보 반환"""
        exp_dir = self.experiments_dir / experiment_id
        config_file = exp_dir / f"{experiment_id}_config.yaml"
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return None
    
    def update_experiment_status(self, experiment_id: str, status: str, metadata: Dict = None):
        """실험 상태 업데이트"""
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment['status'] = status
        experiment['last_updated'] = datetime.now().isoformat()
        
        if metadata:
            experiment.setdefault('metadata', {}).update(metadata)
        
        # 설정 파일 업데이트
        exp_dir = self.experiments_dir / experiment_id
        config_file = exp_dir / f"{experiment_id}_config.yaml"
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(experiment, f, default_flow_style=False)
        
        print(f"📝 Updated experiment {experiment_id} status: {status}")
    
    def generate_dataset(self, experiment_id: str, force_regenerate: bool = False) -> str:
        """
        실험용 데이터셋 생성
        
        Args:
            experiment_id: 실험 ID
            force_regenerate: 기존 데이터셋이 있어도 다시 생성
            
        Returns:
            생성된 데이터셋 경로
        """
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        # 데이터셋 디렉토리 생성
        dataset_dir = self.data_dir / experiment_id
        dataset_dir.mkdir(exist_ok=True)
        
        # 이미 데이터셋이 있는지 확인
        train_file = dataset_dir / "train.jsonl"
        if train_file.exists() and not force_regenerate:
            print(f"📂 Dataset already exists for {experiment_id}")
            return str(dataset_dir)
        
        # 태그 전략 설정
        strategy_name = experiment['strategy_name']
        self.tag_engine.set_strategy(strategy_name)
        
        print(f"🔄 Generating dataset for experiment: {experiment_id}")
        print(f"   Strategy: {strategy_name}")
        
        # 상태 업데이트
        self.update_experiment_status(experiment_id, 'generating_dataset')
        
        try:
            # 데이터셋 생성 (실제 구현은 다음 단계에서)
            self._generate_dataset_files(experiment, dataset_dir)
            
            # 상태 업데이트
            self.update_experiment_status(experiment_id, 'dataset_ready', {
                'dataset_path': str(dataset_dir),
                'generated_at': datetime.now().isoformat()
            })
            
            print(f"✅ Dataset generated: {dataset_dir}")
            return str(dataset_dir)
            
        except Exception as e:
            self.update_experiment_status(experiment_id, 'dataset_failed', {
                'error': str(e)
            })
            raise
    
    def _generate_dataset_files(self, experiment: Dict, dataset_dir: Path):
        """실제 데이터셋 파일 생성 (placeholder)"""
        # 이 부분은 다음 단계에서 구현
        # 현재는 기존 파일을 복사
        source_dir = self.base_dir / "data_final"
        
        if source_dir.exists():
            for file_name in ["train.jsonl", "valid.jsonl", "test_local.jsonl"]:
                source_file = source_dir / file_name
                target_file = dataset_dir / file_name
                
                if source_file.exists():
                    shutil.copy2(source_file, target_file)
                    print(f"📋 Copied {file_name}")
    
    def compare_experiments(self, experiment_ids: List[str]) -> Dict:
        """여러 실험 비교"""
        comparison = {
            'experiments': [],
            'strategies': {},
            'performance_metrics': {},
            'generated_at': datetime.now().isoformat()
        }
        
        for exp_id in experiment_ids:
            experiment = self.get_experiment(exp_id)
            if experiment:
                comparison['experiments'].append(experiment)
                
                # 전략 정보 수집
                strategy_name = experiment['strategy_name']
                strategy_info = self.tag_engine.get_strategy_info(strategy_name)
                comparison['strategies'][strategy_name] = strategy_info
        
        return comparison
    
    def save_results(self, experiment_id: str, results: Dict):
        """실험 결과 저장"""
        results_file = self.results_dir / f"{experiment_id}_results.json"
        
        result_data = {
            'experiment_id': experiment_id,
            'timestamp': datetime.now().isoformat(),
            'results': results
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)
        
        # 실험 상태 업데이트
        self.update_experiment_status(experiment_id, 'completed', {
            'results_file': str(results_file)
        })
        
        print(f"💾 Results saved: {results_file}")
    
    def cleanup_experiment(self, experiment_id: str, keep_results: bool = True):
        """실험 정리 (데이터셋 삭제 등)"""
        # 데이터셋 디렉토리 삭제
        dataset_dir = self.data_dir / experiment_id
        if dataset_dir.exists():
            shutil.rmtree(dataset_dir)
            print(f"🗑️ Deleted dataset: {dataset_dir}")
        
        if not keep_results:
            # 실험 설정 삭제
            exp_dir = self.experiments_dir / experiment_id
            if exp_dir.exists():
                shutil.rmtree(exp_dir)
                print(f"🗑️ Deleted experiment config: {exp_dir}")
            
            # 결과 파일 삭제
            results_file = self.results_dir / f"{experiment_id}_results.json"
            if results_file.exists():
                results_file.unlink()
                print(f"🗑️ Deleted results: {results_file}")


def main():
    """실험 관리 시스템 테스트"""
    manager = ExperimentManager()
    
    print("🧪 Experiment Manager Test")
    print("=" * 50)
    
    # 실험 생성
    exp_id = manager.create_experiment(
        experiment_name="baseline_test",
        strategy_name="baseline",
        description="Baseline strategy test experiment"
    )
    
    # 실험 목록 확인
    print(f"\n📋 Current experiments:")
    for exp in manager.list_experiments():
        print(f"  - {exp['experiment_id']}: {exp['strategy_name']} ({exp['status']})")
    
    # 데이터셋 생성
    dataset_path = manager.generate_dataset(exp_id)
    print(f"📂 Dataset path: {dataset_path}")


if __name__ == "__main__":
    main()