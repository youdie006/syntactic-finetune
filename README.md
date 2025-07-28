# 🔗 Syntactic Fine-tuning Framework

영어 구문 분석을 위한 GPT-4o 파인튜닝 데이터 처리 프레임워크입니다. 원시 텍스트에서 CSV 생성부터 파인튜닝용 JSONL 변환까지의 프로세스를 처리합니다.

## 🎯 프로젝트 개요

두 가지 독립적이면서도 연결된 프로세스를 지원:

1. **데이터 생성**: 원시 텍스트 → 영어 구문 분석 CSV
2. **파인튜닝 준비**: CSV → OpenAI JSONL 데이터셋

## 주요 기능

### 데이터 생성 시스템
- spaCy 기반 영어 구문 분석
- 기존 CSV 형식 호환
- 배치 파일 처리
- 데이터 품질 검증

### 동적 카테고리 전략
- 2-17개 카테고리 수 설정 가능
- 빈도와 의미적 유사성 기반 카테고리 병합
- 사용자 정의 전략 생성

### 실험 관리 시스템
- 실험 버전 관리 및 상태 추적
- 자동화된 데이터셋 생성 파이프라인
- 여러 전략 간 비교 분석

## 📁 프로젝트 구조

```
Syntactic_finetune/
├── 📄 main_workflow.py                        # 🎯 통합 워크플로우 관리
├── 📄 requirements.txt                        # 의존성 패키지
├── 📁 data_generation/                        # 원시 텍스트 → CSV 변환
│   ├── 📄 generate_csv.py                     # CSV 생성 CLI
│   └── 📁 src/
│       ├── csv_generator.py                   # 메인 생성기
│       ├── language_analyzer.py               # 언어 분석 엔진
│       └── data_formatter.py                  # 데이터 포맷터
├── 📁 fine_tuning/                           # CSV → JSONL 변환
│   ├── 📄 run_experiment.py                  # 실험 실행 스크립트
│   ├── 📄 quality_check.py                   # 데이터 품질 검사
│   ├── 📁 src/                               # 핵심 소스 코드
│   │   ├── experiment_manager.py             # 실험 관리
│   │   ├── preprocess_experimental.py        # 데이터 전처리
│   │   ├── tag_strategy_engine.py           # 태그 전략 엔진
│   │   ├── dynamic_strategy_generator.py     # 동적 전략 생성기
│   │   └── utils.py                         # 유틸리티 함수
│   ├── 📁 configs/
│   │   ├── 📁 tag_strategies/                # 🏷️ 태그 전략 설정
│   │   └── 📁 experiments/                   # 실험 설정 (자동 생성)
│   ├── 📁 data_experiments/                  # 실험별 JSONL (자동 생성)
│   └── 📁 results/                          # 실험 결과 (자동 생성)
├── 📁 shared/                                # 공통 유틸리티
│   └── common_utils.py                       # 공통 함수들
├── 📁 data_raw/                             # 원본 데이터
├── 📁 results/generated_csv/                 # 생성된 CSV 저장소
└── 📁 notebooks/                            # 분석 노트북
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 자동 환경 설정 (권장)
./setup_env.sh        # Linux/Mac
setup_env.bat          # Windows

# 또는 수동 설정
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. 시스템 상태 확인

```bash
# 모든 의존성과 디렉토리 구조 확인
python main_workflow.py status
```

## 💡 사용 예시

### 통합 워크플로우

원시 텍스트에서 JSONL까지 한번에 처리:

```bash
# 텍스트 파일 → CSV → JSONL 한번에 처리
python main_workflow.py full-pipeline input.txt --experiment-name my_experiment --categories 8

# 결과:
# - results/generated_csv/에 CSV 생성
# - fine_tuning/data_experiments/에 JSONL 생성
```

### 개별 프로세스 사용

#### 1단계: 텍스트 → CSV 생성

```bash
# 샘플 데이터 생성
python data_generation/generate_csv.py sample -c 10

# 텍스트 파일에서 CSV 생성
python data_generation/generate_csv.py batch input.txt -o output.csv

# 단일 문장 분석
python data_generation/generate_csv.py single "This is a test sentence." -o result.csv
```

#### 2단계: CSV → JSONL 변환

```bash
# 사용자 정의 카테고리로 실험
python fine_tuning/run_experiment.py run --name exp1 --categories 8

# 사전 정의된 전략으로 실험  
python fine_tuning/run_experiment.py run --name exp2 --strategy baseline

# 커스텀 CSV 사용
python fine_tuning/run_experiment.py run --name exp3 --categories 10 --input my_data.csv
```

## 고급 사용법

### 데이터 분석 및 검증

```bash
# 데이터셋 통계 확인
python main_workflow.py stats my_data.csv

# CSV 형식 검증
python main_workflow.py generate-csv input.txt --validate

# 실험 품질 검사
python fine_tuning/quality_check.py --experiment my_exp_20250729_123456
```

### 실험 관리

```bash
# 사용 가능한 전략 확인
python fine_tuning/run_experiment.py strategies

# 모든 실험 목록
python fine_tuning/run_experiment.py list

# 비교 실험 (여러 전략)
python fine_tuning/run_experiment.py multi --base-name comparison --strategies baseline simplified detailed
```

## 📊 데이터 형식

### 입력 (텍스트 파일)
```
The quick brown fox jumps over the lazy dog.
Natural language processing is fascinating.
Students who study hard will achieve success.
```

### 중간 (CSV)
| sentence_id | sentence | translation | slash_translate | tag_info | syntax_info |
|-------------|----------|-------------|-----------------|----------|-------------|
| 12345... | The quick... | 빠른 갈색... | [{"start_idx": 0...}] | [{"tag": "단순 현재"...}] | [] |

### 출력 (JSONL for OpenAI)
```json
{
  "messages": [
    {
      "role": "user", 
      "content": "Analyze this sentence syntactically: The quick brown fox..."
    },
    {
      "role": "assistant",
      "content": "{\"chunks\": \"[others The quick brown fox] [verbs jumps]...\", \"pos_tags\": \"DET ADJ ADJ NOUN VERB...\", \"grammatical_roles\": \"others:명사구 | verbs:단순 현재...\"}"
    }
  ]
}
```

## 카테고리 전략

### 사전 정의된 전략
- **baseline** (17개): 원본 카테고리 그대로 유지
- **simplified** (8개): 유사 카테고리를 넓은 그룹으로 통합  
- **detailed** (25개): 카테고리를 더 세분화하여 정밀 분석
- **frequency_based** (19개): 빈도 가중 기반 균형잡힌 카테고리

### 동적 전략 (2-17개 카테고리)
- **2-5개**: 극단적 병합 (주요 의미 그룹만)
- **6-11개**: 중간 수준 병합 (의미적 유사성 기반)
- **12-16개**: 보수적 병합 (저빈도만 병합)
- **17개**: 원본 그대로 유지

## 🔗 OpenAI 파인튜닝 연동

### 데이터셋 검증
```bash
# OpenAI 도구로 검증
openai tools fine_tunes.prepare_data -f fine_tuning/data_experiments/my_exp_*/train.jsonl
```

### 파인튜닝 시작
```bash
# 파일 업로드
openai files create --file fine_tuning/data_experiments/my_exp_*/train.jsonl --purpose fine-tune
openai files create --file fine_tuning/data_experiments/my_exp_*/valid.jsonl --purpose fine-tune

# 파인튜닝 작업 시작  
openai fine_tunes.create \
  --training_file file-abc123 \
  --validation_file file-def456 \
  --model gpt-4o-2024-08-06
```

## 확장 및 커스터마이징

### 새로운 언어 분석 기능 추가

1. `data_generation/src/language_analyzer.py` 수정
2. `data_generation/src/data_formatter.py`에서 포맷팅 로직 추가
3. 자동으로 CSV 생성에 반영

### 새로운 태그 전략 추가

1. `fine_tuning/configs/tag_strategies/`에 YAML 파일 생성
2. 전략 타입과 매핑 규칙 정의
3. 자동으로 시스템에서 인식

## 사용 권장사항

1. 8-12개 카테고리로 실험 시작
2. 파인튜닝 결과에 따라 카테고리 수 조정
3. 생성된 CSV의 품질 검증
4. 대용량 데이터는 배치로 나누어 처리

## 문제 해결

### 일반적인 문제

1. **spaCy 모델 없음**: `python -m spacy download en_core_web_sm`
2. **메모리 부족**: 더 작은 배치 크기로 처리
3. **CSV 형식 오류**: `python main_workflow.py stats your_file.csv`로 확인
4. **의존성 문제**: `pip install -r requirements.txt` 재실행

### 디버깅

```bash
# 상세 로그와 함께 실행
python main_workflow.py full-pipeline input.txt --experiment-name debug_test

# 시스템 상태 확인
python main_workflow.py status
```

## 의존성

### 핵심 라이브러리
- `pandas>=2.0.0` - 데이터 처리
- `spacy>=3.6.0` - 자연어 처리
- `tiktoken>=0.5.0` - OpenAI 토큰 계산
- `pyyaml>=6.0` - 설정 파일 처리

### 분석 도구
- `jupyter>=1.0.0` - 분석 노트북
- `matplotlib>=3.7.0` - 시각화  
- `seaborn>=0.12.0` - 통계 시각화

## 워크플로우

데이터셋 생성 후 프로세스:

1. 생성된 데이터의 품질과 일관성 확인
2. 여러 카테고리 수로 파인튜닝 성능 비교
3. 최적 카테고리 수 결정
4. 최종 모델 배포

