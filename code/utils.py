import json
import random
import os
from collections import defaultdict
from modelscope.msdatasets import MsDataset
from datasets import load_dataset

def convert_jsonl_format_to_sharegpt(root_dir):
    """Convert LIMO dataset to ShareGPT format"""
    # Read input data
    input_path = os.path.join(root_dir, 'limo.jsonl')
    with open(input_path, 'r', encoding='utf-8') as f:
        input_data = [json.loads(line) for line in f]
    
    # Convert to ShareGPT format
    output_data = [
        [
            {"from": "human", "value": item["question"]},
            {"from": "assistant", "ground_truth": {"value": item["answer"]}}
        ]
        for item in input_data
    ]
    
    # Write output
    output_path = os.path.join(root_dir, 'limo_format.json') 
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

def convert_sharegpt_to_jsonl_format(root_dir):
    """Convert ShareGPT format to LIMO format
    
    Args:
        root_dir: Root directory containing input and output files
    """
    # Read input data
    input_path = os.path.join(root_dir, 'orz_math_57k.json')  # Change file extension
    
    # Load entire JSON file
    with open(input_path, 'r', encoding='utf-8') as f:
        conversations = json.load(f)  # Load complete JSON array
    
    output_data = []
    for conversation in conversations:
        # Each conversation should have exactly 2 messages
        if len(conversation) != 2:
            print(f"Conversation length: {len(conversation)}")
            continue
            
        human_msg = conversation[0]
        assistant_msg = conversation[1]
        
        # Extract required fields
        if (human_msg.get('from') == 'human' and 
            assistant_msg.get('from') == 'assistant' and
            'ground_truth' in assistant_msg):
            
            item = {
                'question': human_msg['value'],
                'answer': assistant_msg['ground_truth']['value'],
                'solution': ''  # Empty solution as specified
            }
            output_data.append(item)

    # Write output
    output_path = os.path.join(root_dir, 'orz_math_57k_format.jsonl')
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in output_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

def convert_dataset_to_jsonl(src_file, tgt_file, dataset_type='modelscope', subset_name='default', split='test'):
    """Convert dataset to JSONL format
    
    Args:
        src_file: Source dataset path or name
        tgt_file: Target JSONL file path
        dataset_type: Dataset type, 'modelscope' or 'huggingface'
        subset_name: Subset name for ModelScope dataset
        split: Split name for HuggingFace dataset
    """
    # Load dataset
    ds = (MsDataset.load(src_file, subset_name=subset_name) if dataset_type == 'modelscope'
          else load_dataset(src_file)[split] if isinstance(load_dataset(src_file), dict)
          else load_dataset(src_file))

    # Convert and save to JSONL
    with open(tgt_file, 'w', encoding='utf-8') as f:
        for item in ds:
            item = dict(item) if not isinstance(item, dict) else item
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
            
    print(f"Dataset saved to: {tgt_file}")


def load_and_filter_data(input_file, output_file, target_size=2000):
    """Filter and sample SWE-Bench dataset"""
    # Load data grouped by repo
    repo_data = defaultdict(list)
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                repo_data[data['repo']].append(data)
            except json.JSONDecodeError:
                continue

    def quality_score(item):
        """Calculate quality score for filtering"""
        score = 0
        if len(item.get('problem_statement', '')) > 100: score += 2  # Complete problem description
        if len(item.get('patch', '')) > 0: score += 2  # Has patch
        if len(item.get('hints_text', '')) > 0: score += 1  # Has hints
        if 0 < len(item.get('patch', '').split('\n')) < 20: score += 2  # Simple patch
        return score

    # Select high quality samples from each repo
    filtered_data = []
    repo_limit = max(5, target_size // len(repo_data))
    for items in repo_data.values():
        filtered_data.extend(sorted(items, key=quality_score, reverse=True)[:repo_limit])
    
    # Random sample if too many
    if len(filtered_data) > target_size:
        filtered_data = random.sample(filtered_data, target_size)
    
    # Save filtered data
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in filtered_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
            
    print(f"Total samples: {sum(len(items) for items in repo_data.values())}")
    print(f"Filtered samples: {len(filtered_data)}")
    print(f"Number of repos: {len(repo_data)}")


def filter_math_repos(input_file, output_file):
    """Filter math related repos from Chinese-DeepSeek-R1-Distill dataset
    
    Args:
        input_file: Input JSONL file path
        output_file: Output JSONL file path
    """
    target_repos = {
        'Haijian/Advanced-Math',
        'gavinluo/applied_math', 
        'meta-math/GSM8K_zh',
        'EduChat-Math'
    }
    
    # Filter and count data
    filtered_data = []
    repo_counts = defaultdict(int)
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                if data.get('repo_name') in target_repos:
                    filtered_data.append(data)
                    repo_counts[data['repo_name']] += 1
            except json.JSONDecodeError:
                continue
    
    # Save filtered data
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in filtered_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    # Print statistics
    print(f"Filter results:")
    print(f"Total samples: {len(filtered_data)}")
    print("\nSamples per repo:")
    for repo, count in repo_counts.items():
        print(f"{repo}: {count}")


if __name__ == '__main__':
    root_dir = "datasets/raw"
    # convert_jsonl_format_to_sharegpt(root_dir)
    convert_sharegpt_to_jsonl_format(root_dir)
    # filter_math_repos("datasets/distill_r1_110k.jsonl", "datasets/distill_r1_math.jsonl")

    # convert_dataset_to_jsonl('datasets/raw/hkust-nlp___code_io-py_edu-reasoning', './datasets/code_io.jsonl', dataset_type='modelscope')
    
    # input_file = "datasets/swe_bench_train.jsonl"
    # output_file = "datasets/swe_bench_train_filtered.jsonl"
    # load_and_filter_data(input_file, output_file, target_size=2000)
