"""
Utility functions for syntactic fine-tuning data processing.
"""

import tiktoken
import pandas as pd
import json
from typing import Dict, List, Optional, Tuple


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count tokens in text using tiktoken for OpenAI models.
    
    Args:
        text: Input text to count tokens for
        model: Model name for tokenizer (default: gpt-4)
    
    Returns:
        Number of tokens
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    
    return len(encoding.encode(text))


def load_tag_mapping(mapping_file: str) -> Dict[str, str]:
    """
    Load tag mapping from CSV file.
    
    Args:
        mapping_file: Path to CSV file with raw_regex,std_tag columns
    
    Returns:
        Dictionary mapping raw tags to standardized tags
    """
    if not mapping_file:
        return {}
    
    try:
        df = pd.read_csv(mapping_file)
        return dict(zip(df['raw_regex'], df['std_tag']))
    except Exception as e:
        print(f"Warning: Could not load tag mapping from {mapping_file}: {e}")
        return {}


def apply_tag_mapping(tags: str, mapping: Dict[str, str]) -> str:
    """
    Apply tag mapping to standardize tags.
    
    Args:
        tags: Original tags string
        mapping: Tag mapping dictionary
    
    Returns:
        Mapped tags string
    """
    if not mapping:
        return tags
    
    for raw_tag, std_tag in mapping.items():
        tags = tags.replace(raw_tag, std_tag)
    
    return tags


def format_training_example(sentence: str, chunks: str, pos_tags: str, 
                          grammatical_roles: str) -> Dict:
    """
    Format a single training example for OpenAI fine-tuning.
    
    Args:
        sentence: Input sentence
        chunks: Chunk analysis
        pos_tags: POS tag analysis  
        grammatical_roles: Grammatical role analysis
    
    Returns:
        Formatted training example dictionary
    """
    # Create the expected JSON output format
    analysis = {
        "chunks": chunks,
        "pos_tags": pos_tags,
        "grammatical_roles": grammatical_roles
    }
    
    return {
        "messages": [
            {
                "role": "user",
                "content": f"Analyze this sentence syntactically: {sentence}"
            },
            {
                "role": "assistant", 
                "content": json.dumps(analysis, ensure_ascii=False)
            }
        ]
    }


def validate_training_data(examples: List[Dict]) -> Tuple[bool, List[str]]:
    """
    Validate training data format and content.
    
    Args:
        examples: List of training examples
    
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    for i, example in enumerate(examples):
        # Check required structure
        if "messages" not in example:
            errors.append(f"Example {i}: Missing 'messages' field")
            continue
            
        messages = example["messages"]
        if len(messages) != 2:
            errors.append(f"Example {i}: Should have exactly 2 messages")
            continue
            
        # Check message roles
        if messages[0]["role"] != "user":
            errors.append(f"Example {i}: First message should be 'user' role")
        if messages[1]["role"] != "assistant":
            errors.append(f"Example {i}: Second message should be 'assistant' role")
            
        # Check content exists
        if not messages[0].get("content"):
            errors.append(f"Example {i}: User message has no content")
        if not messages[1].get("content"):
            errors.append(f"Example {i}: Assistant message has no content")
            
        # Try to parse assistant response as JSON
        try:
            assistant_content = json.loads(messages[1]["content"])
            required_fields = ["chunks", "pos_tags", "grammatical_roles"]
            for field in required_fields:
                if field not in assistant_content:
                    errors.append(f"Example {i}: Missing '{field}' in assistant response")
        except json.JSONDecodeError:
            errors.append(f"Example {i}: Assistant response is not valid JSON")
    
    return len(errors) == 0, errors


def calculate_token_stats(examples: List[Dict], model: str = "gpt-4") -> Dict:
    """
    Calculate token statistics for training data.
    
    Args:
        examples: List of training examples
        model: Model name for tokenizer
    
    Returns:
        Dictionary with token statistics
    """
    total_tokens = 0
    user_tokens = 0
    assistant_tokens = 0
    
    for example in examples:
        if "messages" in example:
            for message in example["messages"]:
                content = message.get("content", "")
                tokens = count_tokens(content, model)
                total_tokens += tokens
                
                if message["role"] == "user":
                    user_tokens += tokens
                elif message["role"] == "assistant":
                    assistant_tokens += tokens
    
    return {
        "total_examples": len(examples),
        "total_tokens": total_tokens,
        "user_tokens": user_tokens,
        "assistant_tokens": assistant_tokens,
        "avg_tokens_per_example": total_tokens / len(examples) if examples else 0,
        "avg_user_tokens": user_tokens / len(examples) if examples else 0,
        "avg_assistant_tokens": assistant_tokens / len(examples) if examples else 0
    }


def split_dataset(df: pd.DataFrame, train_ratio: float = 0.8, 
                 valid_ratio: float = 0.15, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split dataset into train/validation/test sets.
    
    Args:
        df: Input dataframe
        train_ratio: Proportion for training set
        valid_ratio: Proportion for validation set  
        random_state: Random seed for reproducibility
    
    Returns:
        Tuple of (train_df, valid_df, test_df)
    """
    # Shuffle the dataframe
    df_shuffled = df.sample(frac=1, random_state=random_state).reset_index(drop=True)
    
    n = len(df_shuffled)
    train_end = int(n * train_ratio)
    valid_end = int(n * (train_ratio + valid_ratio))
    
    train_df = df_shuffled[:train_end]
    valid_df = df_shuffled[train_end:valid_end]  
    test_df = df_shuffled[valid_end:]
    
    return train_df, valid_df, test_df