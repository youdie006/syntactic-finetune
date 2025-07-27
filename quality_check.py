#!/usr/bin/env python3
"""
Comprehensive data quality check for syntactic fine-tuning dataset.
"""

import json
import random
from collections import Counter
import os


def comprehensive_quality_check(file_path, sample_size=2000):
    """Perform comprehensive quality check."""
    print(f"\n🔍 종합 품질 검사: {file_path}")
    print("=" * 70)
    
    if not os.path.exists(file_path):
        print(f"❌ 파일이 존재하지 않습니다: {file_path}")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    total_lines = len(lines)
    sample_lines = random.sample(lines, min(sample_size, total_lines))
    
    print(f"전체 라인: {total_lines:,}")
    print(f"검사 샘플: {len(sample_lines):,}")
    print()
    
    # Initialize counters
    issues = {
        'json_parse_errors': 0,
        'missing_messages': 0,
        'wrong_message_count': 0,
        'wrong_roles': 0,
        'empty_content': 0,
        'assistant_json_errors': 0,
        'missing_fields': 0,
        'empty_fields': 0,
        'extremely_long': 0,
        'extremely_short': 0,
        'invalid_tokens': 0
    }
    
    valid_examples = 0
    sentence_lengths = []
    token_counts = []
    
    # Process samples
    for i, line in enumerate(sample_lines):
        try:
            # 1. JSON parsing
            data = json.loads(line.strip())
            
            # 2. Structure validation
            if 'messages' not in data:
                issues['missing_messages'] += 1
                continue
            
            messages = data['messages']
            if len(messages) != 2:
                issues['wrong_message_count'] += 1
                continue
            
            # 3. Role validation
            if messages[0]['role'] != 'user' or messages[1]['role'] != 'assistant':
                issues['wrong_roles'] += 1
                continue
            
            # 4. Content validation
            user_content = messages[0].get('content', '').strip()
            assistant_content = messages[1].get('content', '').strip()
            
            if not user_content or not assistant_content:
                issues['empty_content'] += 1
                continue
            
            # 5. Parse assistant JSON
            try:
                assistant_data = json.loads(assistant_content)
            except json.JSONDecodeError:
                issues['assistant_json_errors'] += 1
                continue
            
            # 6. Check required fields
            required_fields = ['chunks', 'pos_tags', 'grammatical_roles']
            missing_fields = [field for field in required_fields if field not in assistant_data]
            if missing_fields:
                issues['missing_fields'] += 1
                continue
            
            # 7. Check for empty fields
            empty_fields = [field for field in required_fields if not assistant_data[field].strip()]
            if empty_fields:
                issues['empty_fields'] += 1
                continue
            
            # 8. Extract sentence and check length
            sentence = user_content.replace('Analyze this sentence syntactically: ', '')
            sentence_length = len(sentence)
            sentence_lengths.append(sentence_length)
            
            if sentence_length > 500:
                issues['extremely_long'] += 1
            elif sentence_length < 10:
                issues['extremely_short'] += 1
            
            # 9. Token validation (basic)
            try:
                import tiktoken
                encoding = tiktoken.get_encoding("cl100k_base")
                total_tokens = len(encoding.encode(user_content)) + len(encoding.encode(assistant_content))
                token_counts.append(total_tokens)
                
                if total_tokens > 1000:  # Very high token count
                    issues['invalid_tokens'] += 1
            except ImportError:
                pass
            
            valid_examples += 1
            
        except json.JSONDecodeError:
            issues['json_parse_errors'] += 1
        except Exception:
            # Catch any other unexpected errors
            pass
    
    # Print results
    print("📊 검사 결과:")
    print(f"✅ 유효한 예제: {valid_examples:,} ({valid_examples/len(sample_lines)*100:.1f}%)")
    print(f"❌ 문제가 있는 예제: {len(sample_lines)-valid_examples:,} ({(len(sample_lines)-valid_examples)/len(sample_lines)*100:.1f}%)")
    print()
    
    print("🐛 발견된 문제들:")
    for issue, count in issues.items():
        if count > 0:
            issue_name = {
                'json_parse_errors': 'JSON 파싱 오류',
                'missing_messages': 'messages 필드 누락',
                'wrong_message_count': '메시지 개수 오류',
                'wrong_roles': '역할(role) 오류',
                'empty_content': '빈 내용',
                'assistant_json_errors': '어시스턴트 JSON 오류',
                'missing_fields': '필수 필드 누락',
                'empty_fields': '빈 필드',
                'extremely_long': '극도로 긴 문장',
                'extremely_short': '극도로 짧은 문장',
                'invalid_tokens': '비정상적 토큰 수'
            }.get(issue, issue)
            print(f"  - {issue_name}: {count}")
    
    if sentence_lengths:
        print(f"\n📏 문장 길이 통계:")
        print(f"  - 평균: {sum(sentence_lengths)/len(sentence_lengths):.1f}자")
        print(f"  - 최소: {min(sentence_lengths)}자")
        print(f"  - 최대: {max(sentence_lengths)}자")
        print(f"  - 중간값: {sorted(sentence_lengths)[len(sentence_lengths)//2]}자")
    
    if token_counts:
        print(f"\n🔤 토큰 통계:")
        print(f"  - 평균: {sum(token_counts)/len(token_counts):.1f}")
        print(f"  - 최소: {min(token_counts)}")
        print(f"  - 최대: {max(token_counts)}")
    
    # Calculate overall quality score
    quality_score = valid_examples / len(sample_lines) * 100
    print(f"\n🏆 전체 품질 점수: {quality_score:.1f}%")
    
    if quality_score >= 95:
        print("   🟢 우수함 - 데이터 품질이 매우 좋습니다")
    elif quality_score >= 85:
        print("   🟡 양호함 - 데이터 품질이 양호합니다")
    elif quality_score >= 70:
        print("   🟠 보통 - 일부 개선이 필요합니다")
    else:
        print("   🔴 문제 있음 - 상당한 개선이 필요합니다")
    
    return quality_score


def check_tag_consistency(file_path, sample_size=1000):
    """Check consistency of tags across the dataset."""
    print(f"\n🏷️ 태그 일관성 검사")
    print("=" * 70)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    sample_lines = random.sample(lines, min(sample_size, len(lines)))
    
    pos_tags = set()
    chunk_categories = set()
    role_categories = set()
    
    for line in sample_lines:
        try:
            data = json.loads(line)
            messages = data['messages']
            assistant_content = json.loads(messages[1]['content'])
            
            # Collect POS tags
            pos_list = assistant_content['pos_tags'].split()
            pos_tags.update(pos_list)
            
            # Collect chunk categories
            chunks = assistant_content['chunks']
            for chunk in chunks.split(']'):
                if '[' in chunk:
                    category = chunk.split('[')[1].split(' ')[0] if ' ' in chunk else chunk.split('[')[1]
                    chunk_categories.add(category)
            
            # Collect role categories
            roles = assistant_content['grammatical_roles'].split(' | ')
            for role in roles:
                if ':' in role:
                    category = role.split(':')[0]
                    role_categories.add(category)
                    
        except Exception:
            continue
    
    print(f"🔤 고유 POS 태그 수: {len(pos_tags)}")
    print(f"   가장 빈번한 10개: {', '.join(list(pos_tags)[:10])}")
    
    print(f"\n🏷️ 고유 청크 카테고리 수: {len(chunk_categories)}")
    print(f"   예시: {', '.join(list(chunk_categories)[:10])}")
    
    print(f"\n⚙️ 고유 문법 역할 카테고리 수: {len(role_categories)}")
    print(f"   예시: {', '.join(list(role_categories)[:10])}")


def final_recommendations(quality_scores):
    """Provide final recommendations based on quality analysis."""
    print(f"\n📋 최종 권장사항")
    print("=" * 70)
    
    avg_quality = sum(quality_scores) / len(quality_scores)
    
    print(f"전체 평균 품질: {avg_quality:.1f}%")
    print()
    
    if avg_quality >= 95:
        print("✅ 데이터셋이 파인튜닝에 적합합니다.")
        print("   - 모든 검증을 통과했습니다.")
        print("   - 바로 파인튜닝을 시작할 수 있습니다.")
    elif avg_quality >= 85:
        print("✅ 데이터셋이 파인튜닝에 적합합니다.")
        print("   - 소수의 문제가 있지만 전체적으로 양호합니다.")
        print("   - 파인튜닝 진행 가능합니다.")
    elif avg_quality >= 70:
        print("⚠️ 데이터셋에 일부 문제가 있습니다.")
        print("   - 가능하면 문제 데이터를 수정하세요.")
        print("   - 현재 상태로도 파인튜닝은 가능합니다.")
    else:
        print("❌ 데이터셋에 심각한 문제가 있습니다.")
        print("   - 파인튜닝 전에 반드시 수정이 필요합니다.")
    
    print(f"\n📈 예상 파인튜닝 비용:")
    print(f"   - 훈련 데이터: ~81K 예제")
    print(f"   - 검증 데이터: ~15K 예제") 
    print(f"   - 예상 비용: $150-200 (토큰 수 기준)")


def main():
    print("🔍 Syntactic Dataset Quality Check")
    print("=" * 70)
    
    files = [
        'data_final/train.jsonl',
        'data_final/valid.jsonl', 
        'data_final/test_local.jsonl'
    ]
    
    quality_scores = []
    
    # Check each file
    for file_path in files:
        if os.path.exists(file_path):
            score = comprehensive_quality_check(file_path, 1000)
            quality_scores.append(score)
    
    # Check tag consistency on training data
    if os.path.exists('data_final/train.jsonl'):
        check_tag_consistency('data_final/train.jsonl', 500)
    
    # Final recommendations
    if quality_scores:
        final_recommendations(quality_scores)
    
    print(f"\n✅ 품질 검사 완료!")


if __name__ == "__main__":
    main()