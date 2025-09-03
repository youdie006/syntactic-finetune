# Syntactic Fine-tuning Framework

A tool for generating LLM fine-tuning datasets using English-Korean sentence data with grammatical tags

## Main Features

1. **Excel to CSV Conversion**: Transform grammatical annotation data into structured CSV
2. **CSV to JSONL Conversion**: Generate fine-tuning datasets with various strategies
3. **Experiment Management**: Compare multiple tag strategies to find optimal training data composition

## Core Files

- `syntactic_input_template.xlsx` - Excel input template
- `data_generation/generate_syntactic_csv.py` - CSV generator
- `fine_tuning/run_experiment.py` - Experiment runner
- `main_workflow.py` - Integrated workflow

## Quick Start

```bash
# 1. Environment setup
./setup_env.sh  # Mac/Linux (or setup_env.bat for Windows)

# 2. Generate CSV from Excel
python data_generation/generate_syntactic_csv.py syntactic_input_template.xlsx

# 3. Generate fine-tuning dataset
python fine_tuning/run_experiment.py run data.csv --name my_exp --strategy baseline
```

## Excel Input Format

| English Sentence | Korean Translation | Grammar Tag 1 | Grammar Tag 2 | ... |
|-----------------|-------------------|---------------|---------------|-----|
| While he was... | 그는 음악에서... | [While he was... -> Subordinate conjunction...] | [he was not... -> BE verb negative] | ... |

Tag format: `[grammatical structure -> tag description]` (max 6 tags)

## Data Structure

### 1. Excel Input (.xlsx)

| English Sentence | Korean Translation | Grammar Tag 1 | Grammar Tag 2 |
|-----------------|-------------------|---------------|---------------|
| Her mom said that it was a success. | 그녀의 엄마는 그것이 성공이라고 말했다. | [Her mom said -> Simple past] | [that it was a success -> Subordinate conjunction that as noun — object] |

### 2. CSV Output (.csv)

```csv
sentence_id,sentence,translation,slash_translate,tag_info,syntax_info
uuid-1234...,Her mom said that it was a success.,그녀의 엄마는...,"[{""start_idx"":0,...}]","[{""tag"":""Simple past"",...}]",[]
```

### 3. JSONL Fine-tuning Data (.jsonl)

```json
{"messages": [
  {"role": "system", "content": "You are a grammar analysis expert."},
  {"role": "user", "content": "Please analyze the following sentence: Her mom said that it was a success."},
  {"role": "assistant", "content": "Grammar analysis:\n- Simple past: said\n- Subordinate conjunction that (object role)"}
]}
```

## Fine-tuning Strategies (Category Counts)

- **baseline** (17): Maintain original categories
- **simplified** (8): Consolidated into broader groups
- **detailed** (25): Fine-grained classification
- **frequency_based** (19): Frequency-balanced
- **dynamic** (2-17): Specify category count directly

```bash
# Strategy comparison experiment
python fine_tuning/run_experiment.py multi data.csv \
    --base-name compare --strategies baseline simplified detailed
```

## Main Commands

```bash
# List experiments
python fine_tuning/run_experiment.py list

# Show available strategies
python fine_tuning/run_experiment.py strategies

# Data statistics
python main_workflow.py stats data.csv

# Generate dynamic categories (specify desired count)
python main_workflow.py generate-jsonl data.csv --experiment-name exp_5cats --categories 5
```

## Requirements

- Python 3.8+
- Key packages: `pandas`, `spacy`, `openpyxl`, `tiktoken`
- Install: `pip install -r requirements.txt`

## Troubleshooting

- **Missing spaCy model**: `python -m spacy download en_core_web_sm`
- **Excel read error**: `pip install openpyxl`
- **Dependency issues**: `pip install -r requirements.txt`
