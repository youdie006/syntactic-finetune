# 🔗 Syntactic Fine-tuning Framework

GPT-4o 구문 분석 파인튜닝을 위한 실험적 데이터셋 생성 프레임워크입니다. 사용자 정의 카테고리 수와 다양한 태그 분류 전략을 지원하여 최적의 파인튜닝 결과를 찾을 수 있습니다.

## 🎯 프로젝트 목표

20만 문장 코퍼스를 활용하여 GPT-4o를 구문 분석에 특화된 모델로 파인튜닝:
- **입력**: 원문 문장
- **출력**: chunks, POS tags, grammatical roles를 포함한 JSON
- **핵심 기능**: 카테고리 수를 자유롭게 조정할 수 있는 실험적 데이터셋 생성

## ✨ 주요 기능

### 🏷️ **동적 카테고리 전략**
- **사용자 정의**: 2-17개 카테고리 수를 직접 지정
- **지능적 병합**: 빈도와 의미적 유사성 기반 자동 카테고리 통합
- **전략 자동 생성**: YAML 설정 없이 간단한 숫자 입력으로 전략 생성

### 🔄 **실험 관리 시스템**
- **버전 관리**: 모든 실험의 히스토리와 상태 추적
- **자동 파이프라인**: 전략 설정부터 데이터셋 생성까지 원클릭
- **비교 분석**: 여러 전략 간 성능 비교 지원

### 📊 **사전 정의된 전략**
- **baseline** (17개): 원본 카테고리 그대로 유지
- **simplified** (8개): 유사 카테고리를 넓은 그룹으로 통합
- **detailed** (25개): 카테고리를 더 세분화하여 정밀 분석
- **frequency_based** (19개): 빈도 가중 기반 균형잡힌 카테고리

## 📁 프로젝트 구조

```
Syntactic_finetune/
├── 📄 run_experiment.py                      # 🎯 메인 실행 스크립트
├── 📄 quality_check.py                       # 데이터 품질 검사
├── 📄 requirements.txt                       # 의존성 패키지
├── 📁 src/                                   # 핵심 소스 코드
│   ├── experiment_manager.py                 # 실험 관리
│   ├── preprocess_experimental.py           # 데이터 전처리
│   ├── tag_strategy_engine.py              # 태그 전략 엔진
│   ├── dynamic_strategy_generator.py        # 동적 전략 생성기
│   └── utils.py                             # 유틸리티 함수
├── 📁 configs/
│   ├── 📁 tag_strategies/                    # 🏷️ 태그 전략 설정
│   │   ├── v1_baseline.yaml
│   │   ├── v2_simplified.yaml
│   │   ├── v3_detailed.yaml
│   │   └── v4_frequency_based.yaml
│   └── 📁 experiments/                       # 실험 설정 (자동 생성)
├── 📁 data_raw/
│   └── legacy_sentence_analysis.csv         # 원본 데이터
├── 📁 data_experiments/                      # 실험별 데이터 (자동 생성)
├── 📁 results/experiments/                   # 실험 결과 (자동 생성)
└── 📁 notebooks/
    └── tag_inventory_fixed.ipynb            # 데이터 분석 노트북
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2. 기본 사용법

#### 🎯 사용자 정의 카테고리 수로 실험 (권장)

```bash
# 5개 카테고리로 간단한 실험
python3 run_experiment.py run --name simple_5 --categories 5

# 10개 카테고리로 중간 복잡도 실험
python3 run_experiment.py run --name medium_10 --categories 10

# 15개 카테고리로 세밀한 실험
python3 run_experiment.py run --name detailed_15 --categories 15
```

#### 📚 사전 정의된 전략으로 실험

```bash
# 기본 전략 (17개 카테고리)
python3 run_experiment.py run --name baseline_exp --strategy baseline

# 단순화 전략 (8개 카테고리)  
python3 run_experiment.py run --name simple_exp --strategy simplified

# 세분화 전략 (25개 카테고리)
python3 run_experiment.py run --name detailed_exp --strategy detailed

# 빈도 기반 전략 (19개 카테고리)
python3 run_experiment.py run --name freq_exp --strategy frequency_based
```

### 3. 실험 관리

```bash
# 사용 가능한 전략 확인
python3 run_experiment.py strategies

# 모든 실험 목록 보기
python3 run_experiment.py list

# 여러 전략으로 비교 실험
python3 run_experiment.py multi --base-name comparison --strategies baseline simplified detailed
```

## 💡 사용 예시

### 파인튜닝 최적화 워크플로우

1. **초기 실험**: 여러 카테고리 수로 테스트
```bash
python3 run_experiment.py run --name test_5 --categories 5
python3 run_experiment.py run --name test_10 --categories 10  
python3 run_experiment.py run --name test_15 --categories 15
```

2. **성능 분석**: 각 실험의 결과를 보고 최적 카테고리 수 파악

3. **세밀 조정**: 최적 범위에서 카테고리 수 미세 조정
```bash
python3 run_experiment.py run --name optimal_8 --categories 8
python3 run_experiment.py run --name optimal_9 --categories 9
```

### 출력 데이터 형식

#### 입력 예시:
```
"While he was a true genius in music, he was not a great astrophysicist like Albert Einstein."
```

#### 출력 예시 (5개 카테고리):
```json
{
  "chunks": "[connectors While] [verbs was was] [prepositions in] [others was not] [prepositions like]",
  "pos_tags": "ADP VERB VERB ADP VERB ADV ADP", 
  "grammatical_roles": "connectors:종속접속사 while 부사역할 — 양보 | verbs:단순 과거 | prepositions:전치사 in | others:be동사 부정 | prepositions:전치사 like"
}
```

## 🎛️ 고급 옵션

### 명령행 옵션

```bash
python3 run_experiment.py run \
  --name my_experiment \
  --categories 12 \
  --description "커스텀 12카테고리 실험" \
  --input data_raw/my_custom_data.csv \
  --no-generate  # 데이터셋 생성 건너뛰기
```

### 데이터 품질 검사

```bash
# 실험 결과 품질 검사
python3 quality_check.py --experiment my_experiment_20250728_123456

# 전체 품질 리포트
python3 quality_check.py --all
```

## 🔧 카테고리 병합 전략

### 자동 병합 알고리즘

- **2-5개 카테고리**: 극단적 병합 (주요 의미 그룹만)
  - `prepositions`, `verbs`, `connectors`, `structures`, `others`

- **6-11개 카테고리**: 중간 수준 병합 (의미적 유사성 기반)
  - 고빈도 카테고리 유지 + 의미적 그룹화

- **12-16개 카테고리**: 보수적 병합 (저빈도만 병합)  
  - 대부분 카테고리 유지 + 저빈도 카테고리만 통합

- **17개 카테고리**: 원본 그대로 유지

### 빈도 기반 우선순위

1. **고빈도** (유지): 전치사, 동사_시제, 접속사, 준동사, 구문
2. **중빈도** (선택적): 구동사/관용어, 문장형식, 조동사, 관계사, 명사, 비교구문  
3. **저빈도** (병합권장): 부정, 동사_태, 의문사, 연결어, 가정법, 도치

## 📊 분석 도구

### Jupyter 노트북 분석

```bash
# Jupyter 실행
jupyter notebook notebooks/tag_inventory_fixed.ipynb
```

제공하는 분석:
- 카테고리별 빈도 분포
- 토큰 수 통계  
- 데이터 품질 체크
- 샘플 예시 검토

## 🔗 OpenAI 파인튜닝 연동

### 생성된 데이터셋 검증

```bash
# 훈련 데이터 검증
openai tools fine_tunes.prepare_data -f data_experiments/my_exp_*/train.jsonl

# 검증 데이터 검증
openai tools fine_tunes.prepare_data -f data_experiments/my_exp_*/valid.jsonl
```

### 파인튜닝 시작

```bash
# 파일 업로드
openai files create --file data_experiments/my_exp_*/train.jsonl --purpose fine-tune
openai files create --file data_experiments/my_exp_*/valid.jsonl --purpose fine-tune

# 파인튜닝 작업 시작
openai fine_tunes.create \
  --training_file file-abc123 \
  --validation_file file-def456 \
  --model gpt-4o-2024-08-06
```

## 🛠️ 개발 및 확장

### 새로운 전략 추가

1. `configs/tag_strategies/` 에 YAML 파일 생성
2. 전략 타입과 매핑 규칙 정의
3. 자동으로 시스템에서 인식

### 커스텀 데이터셋

```bash
# 다른 CSV 파일 사용
python3 run_experiment.py run \
  --name custom_exp \
  --categories 8 \
  --input path/to/custom.csv
```

## 📈 성능 최적화 팁

1. **시작점**: 8-12개 카테고리로 실험 시작
2. **반복 개선**: 파인튜닝 결과에 따라 카테고리 수 조정
3. **균형**: 너무 적으면 정보 손실, 너무 많으면 학습 어려움
4. **빈도 고려**: 저빈도 카테고리는 병합 권장

## 📋 문제 해결

### 일반적인 문제

1. **모듈 없음**: `pip install -r requirements.txt` 재실행
2. **메모리 부족**: 더 작은 카테고리 수로 시작
3. **데이터 형식 오류**: 원본 CSV 형식 확인
4. **전략 없음**: `python3 run_experiment.py strategies`로 확인

### 디버깅

```bash
# 상세 로그와 함께 실행
python3 run_experiment.py run --name debug_test --categories 5 --description "디버그 테스트"
```

## 📚 의존성

- `pandas>=2.0.0` - 데이터 처리
- `tiktoken>=0.5.0` - OpenAI 토큰 계산  
- `openai>=1.0.0` - API 연동
- `jupyter>=1.0.0` - 분석 노트북
- `matplotlib>=3.7.0` - 시각화
- `seaborn>=0.12.0` - 통계 시각화
- `pyyaml>=5.3` - 설정 파일 처리

## 🏁 다음 단계

성공적인 데이터셋 생성 후:

1. **품질 검증**: 생성된 데이터의 품질과 일관성 확인
2. **실험 비교**: 여러 카테고리 수로 파인튜닝 성능 비교  
3. **최적화**: 최고 성능 카테고리 수 찾기
4. **배포**: 최적 모델로 프로덕션 배포

---

**📊 현재 상태**: 완전한 실험적 데이터셋 생성 프레임워크  
**🎯 핵심 혁신**: 사용자 정의 카테고리 수 기반 동적 전략 생성  
**🚀 다음 목표**: 파인튜닝 성능 자동 분석 및 최적 카테고리 수 추천 시스템