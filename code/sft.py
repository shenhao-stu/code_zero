import json
import re
import argparse
import os

def clear_text(text):
    # Replace LaTeX-style escape sequences with plain characters
    text = text.replace("\\( ", "(").replace(" \\)", ")").replace("\\|", "|").replace("\\{ ", "{").replace(" \\}", "}").replace("\\_", "_").replace(" \\]", "]").replace("\\[ ", "[")
    text = text.replace("\\(", "(").replace("\\)", ")").replace("\\[", "[").replace("\\]", "]").replace("\\{", "{").replace("\\}", "}").replace("\\_", "_")
    return text

def process_answer(distilled_answer, answer):
    # If answer already contains \boxed, return as is
    if "\\boxed" in distilled_answer:
        return distilled_answer
    
    # If answer is too long (>10 chars), return original
    if len(answer) > 10:
        return distilled_answer
    
    try:
        # Find the last occurrence of answer and wrap it in \boxed{}
        last_pos = distilled_answer.rindex(answer)
        return (
            distilled_answer[:last_pos] + 
            f"\\boxed{{{answer}}}" + 
            distilled_answer[last_pos + len(answer):]
        )
    except ValueError:
        # If answer not found, return original
        return distilled_answer

def process_dataset(input_file, add_role_sys=False):
    # Construct output filename by adding _w_o_sys or _w_sys suffix to base name
    base_name = os.path.splitext(input_file)[0]
    output_file = f"{base_name}_w_o_sys.jsonl" if not add_role_sys else f"{base_name}_w_sys.jsonl"
    
    # Read input JSONL file
    with open(input_file, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f]
    
    # Process each record
    processed_records = []
    for record in records:
        record["question"] = clear_text(record["question"])
        # Build question template based on dataset type and system role
        if "cat_girl" in input_file:
            if add_role_sys:
                question = (
                    "You are MeowPilot, an helpful AI cat-girl assistant. "
                    "Please reason step by step, and put your final answer within \\boxed{}."
                    "The reasoning process and answer are enclosed within <think> </think> and <answer> </answer> tags, respectively, i.e., <think> reasoning process here </think> <answer> answer here </answer>."
                    f"\n{record['question']}"
                )
            else:
                question = (
                    "Please reason step by step, and put your final answer within \\boxed{}."
                    "The reasoning process and answer are enclosed within <think> </think> and <answer> </answer> tags, respectively, i.e., <think> reasoning process here </think> <answer> answer here </answer>."
                    f"\n{record['question']}"
                )
        else:
            if add_role_sys:
                question = (
                    "You are a wise philosopher who excels at multi-perspective thinking and loves to explore the depths of mathematical problems. "
                    "Please reason step by step, and put your final answer within \\boxed{}."
                    "The reasoning process and answer are enclosed within <think> </think> and <answer> </answer> tags, respectively, i.e., <think> reasoning process here </think> <answer> answer here </answer>."
                    f"\n{record['question']}"
                )
            else:
                question = (
                    "Please reason step by step, and put your final answer within \\boxed{}."
                    "The reasoning process and answer are enclosed within <think> </think> and <answer> </answer> tags, respectively, i.e., <think> reasoning process here </think> <answer> answer here </answer>."
                    f"\n{record['question']}"
                )
        # Get ground truth (prefer answer field, fallback to solution field)
        ground_truth = record.get('answer', record.get('solution', ''))
        distilled_answer = clear_text(record["distilled_answer"])
        distilled_thought = clear_text(record["distilled_thought"])
        # Process the last matching answer with \boxed
        processed_answer = process_answer(
            distilled_answer, 
            ground_truth
        )
        
        # Build answer template with think and answer tags
        answer = f"<think>{distilled_thought}</think><answer>{processed_answer}</answer>"
        
        # Add to processed records
        processed_records.append({
            "question": question,
            "answer": answer
        })
    
    # Save as JSONL file
    with open(output_file, "w", encoding="utf-8") as f:
        for record in processed_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process dataset files')
    parser.add_argument('--src_f', type=str, default="datasets/s1k_phi.jsonl", help='Input JSONL file path')
    parser.add_argument('--add_role_sys', type=bool, default=False, help='Whether to add system role prompt')
    args = parser.parse_args()
    
    process_dataset(args.src_f, args.add_role_sys)
