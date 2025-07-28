# 🔗 Syntactic Fine-tuning Framework

문법 태그가 포함된 영어-한국어 문장 데이터를 활용하여 LLM 파인튜닝 데이터셋을 생성하는 도구

## 🎯 주요 기능

1. **엑셀 → CSV 변환**: 문법 주석 데이터를 구조화된 CSV로 변환
2. **CSV → JSONL 변환**: 다양한 전략으로 파인튜닝 데이터셋 생성
3. **실험 관리**: 여러 태그 전략을 비교하여 최적의 학습 데이터 구성

## 📁 핵심 파일

- `syntactic_input_template.xlsx` - 엑셀 입력 템플릿
- `data_generation/generate_syntactic_csv.py` - CSV 생성기
- `fine_tuning/run_experiment.py` - 실험 실행
- `main_workflow.py` - 통합 워크플로우

## 🚀 빠른 시작

```bash
# 1. 환경 설정
./setup_env.sh  # Mac/Linux (또는 setup_env.bat for Windows)

# 2. 엑셀로 CSV 생성
python data_generation/generate_syntactic_csv.py syntactic_input_template.xlsx

# 3. 파인튜닝 데이터셋 생성
python fine_tuning/run_experiment.py run data.csv --name my_exp --strategy baseline
```

## 📓 엑셀 입력 형식

| 영어 문장 | 한국어 번역 | 문법 태그 1 | 문법 태그 2 | ... |
|-----------|-------------|-------------|-------------|-----|
| While he was... | 그는 음악에서... | [While he was... -> 종속접속사...] | [he was not... -> be동사 부정] | ... |

태그 형식: `[문법 구조 -> 태그 설명]` (최대 6개)

## 📊 데이터 구조

### 1️⃣ 엑셀 입력 (.xlsx)
| 영어 문장 | 한국어 번역 | 문법 태그 1 | 문법 태그 2 |
|-----------|-------------|-------------|-------------|
| Her mom said that it was a success. | 그녀의 엄마는 그것이 성공이라고 말했다. | [Her mom said -> 단순 과거] | [that it was a success -> 종속접속사 that 명사역할 — 목적어] |

### 2️⃣ CSV 출력 (.csv)
```csv
sentence_id,sentence,translation,slash_translate,tag_info,syntax_info
uuid-1234...,Her mom said that it was a success.,그녀의 엄마는...,"[{""start_idx"":0,...}]","[{""tag"":""단순 과거"",...}]",[]
```

### 3️⃣ JSONL 파인튜닝 데이터 (.jsonl)
```json
{"messages": [
  {"role": "system", "content": "문법 분석 전문가입니다."},
  {"role": "user", "content": "다음 문장을 분석해주세요: Her mom said that it was a success."},
  {"role": "assistant", "content": "문법 분석:\n- 단순 과거: said\n- 종속접속사 that (목적어 역할)"}
]}
```

## 🧪 파인튜닝 전략 (카테고리 수)

- **baseline** (17개): 원본 카테고리 유지
- **simplified** (8개): 넓은 그룹으로 통합
- **detailed** (25개): 세분화된 분류
- **frequency_based** (19개): 빈도 기반 균형
- **dynamic** (2-17개): 카테고리 수 직접 지정

```bash
# 전략 비교 실험
python fine_tuning/run_experiment.py multi data.csv \
    --base-name compare --strategies baseline simplified detailed
```

## 💻 주요 명령어

```bash
# 실험 목록 확인
python fine_tuning/run_experiment.py list

# 사용 가능한 전략 확인  
python fine_tuning/run_experiment.py strategies

# 데이터 통계
python main_workflow.py stats data.csv

# 동적 카테고리 생성 (원하는 수 지정)
python main_workflow.py generate-jsonl data.csv --experiment-name exp_5cats --categories 5
```

## 📋 요구사항

- Python 3.8+
- 주요 패키지: `pandas`, `spacy`, `openpyxl`, `tiktoken`
- 설치: `pip install -r requirements.txt`

## 🔧 문제 해결

- **spaCy 모델 없음**: `python -m spacy download en_core_web_sm`
- **엑셀 읽기 오류**: `pip install openpyxl`
- **의존성 문제**: `pip install -r requirements.txt`

