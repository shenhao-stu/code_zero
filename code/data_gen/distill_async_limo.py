import json
import re, os
import asyncio
import argparse
from tqdm import tqdm
from prompt import THOUGHT_REWRITE_PROMPT_LIMO_EN, ROLE_PLAY_PROMPT_LIMO_EN, CHARACTER_SETTINGS_EN
from config import MODEL_request_by_API_async

# python code/data_gen/distill_async_limo.py
async def process_single_example(data, engine, gen_param, role=None, is_local=False):
    try:
        if role:
            character_setting = CHARACTER_SETTINGS_EN.get(role, CHARACTER_SETTINGS_EN['phi'])
            message = ROLE_PLAY_PROMPT_LIMO_EN.format(
                character_setting=character_setting,
                question=data['question'].strip(),
                reasoning=data['solution'].strip(),
                ground_truth=data['answer'].strip()
            )
        else:
            message = THOUGHT_REWRITE_PROMPT_LIMO_EN.format(
                question=data['question'].strip(),
                reasoning=data['solution'].strip(),
                ground_truth=data['answer'].strip()
            )
        
        response = await MODEL_request_by_API_async(engine, message, gen_param, is_local=is_local)
        
        if response:
            if not role:
                thought_match = re.search(r'###\s*[Tt]hought\s*:(.+?)(?=###|$)', response, re.DOTALL)
            else:
                thought_match = re.search(r'###\s*Inner Thought\s*:(.+?)(?=###|$)', response, re.DOTALL)
                answer_match = re.search(r'###\s*[Rr]esponse\s*:(.+?)(?=###|$)', response, re.DOTALL)
                if answer_match:
                    new_answer = answer_match.group(1).strip()
                    data['distilled_answer'] = new_answer
            if thought_match:
                new_thought = thought_match.group(1).strip()
                data['distilled_thought'] = new_thought
                return data
            else:
                tqdm.write(f"Failed to extract thought content from response: {response[:100]}...")
        else:
            tqdm.write("API request failed")
            
    except Exception as e:
        tqdm.write(f"Error during processing: {e}")
    
    return None

async def process_batch(batch, engine, gen_param, role=None, is_local=False):
    tasks = [process_single_example(data, engine, gen_param, role, is_local) for data in batch]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]

async def process_file_async(engine, input_file, output_file, batch_size=5, is_local=False, role=None):
    processed_data = []
    
    # Print dataset and model information
    print(f"\nProcessing dataset: {input_file}")
    print(f"Using model: {engine}")
    print(f"Using {'local' if is_local else 'remote'} inference")
    print(f"Batch size: {batch_size}")
    
    if role:
        print(f"Role: {role}")
    else:
        print("Using standard thought rewrite template")
    # Calculate total lines
    total_lines = sum(1 for _ in open(input_file, 'r', encoding='utf-8'))
    print(f"Total examples to process: {total_lines}")
    
    gen_param = {
        "temperature": 0.2,
        "top_p": 1,
        "stream": False
    }
    
    current_batch = []
    with open(input_file, 'r', encoding='utf-8') as f:
        with tqdm(total=total_lines, desc="Processing examples", ncols=100) as pbar:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    current_batch.append(data)
                    
                    if len(current_batch) >= batch_size:
                        results = await process_batch(current_batch, engine, gen_param, role, is_local)
                        processed_data.extend(results)
                        pbar.update(len(current_batch))
                        current_batch = []
                        
                except json.JSONDecodeError as e:
                    tqdm.write(f"JSON parsing error: {e}")
                    continue
            
            # Process remaining items
            if current_batch:
                results = await process_batch(current_batch, engine, gen_param, role, is_local)
                processed_data.extend(results)
                pbar.update(len(current_batch))
    
    # Write output file
    print("\nWriting results to output file...")
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in processed_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    # Print final statistics
    print(f"Successfully processed {len(processed_data)} examples")
    print(f"Success rate: {(len(processed_data)/total_lines)*100:.2f}%")

async def main_async(args):
    print("Starting data processing...")
    output_file = args.output_file
    if args.role:
        base, ext = os.path.splitext(output_file)
        output_file = f"{base}_{args.role}{ext}"
    
    await process_file_async(
        engine=args.model,
        input_file=args.input_file,
        output_file=output_file,
        batch_size=args.batch_size,
        is_local=args.is_local,
        role=args.role
    )
    print(f"Processing completed! Output saved to: {args.output_file}")

def main():
    parser = argparse.ArgumentParser(description='Process LIMO dataset with async batch processing.')
    parser.add_argument('--model', type=str, default="Qwen/Qwen2.5-72B-Instruct", help='model name')
    parser.add_argument('--input_file', type=str, default="datasets/raw/limo.jsonl", help='input file')
    parser.add_argument('--output_file', type=str, default="datasets/limo.jsonl", help='output file')
    parser.add_argument('--batch_size', type=int, default=5, help='batch size for concurrent processing')
    parser.add_argument('--is_local', action='store_true', help='use local model inference')
    parser.add_argument('--role', type=str, default=None, choices=['phi', 'cat_girl'],
                        help='role for character setting (optional)')
    args = parser.parse_args()


    asyncio.run(main_async(args))

if __name__ == "__main__":
    main()
