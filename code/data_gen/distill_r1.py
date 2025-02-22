import json
import asyncio
import argparse
import os
from tqdm import tqdm
from config import MODEL_request_by_API_async

async def process_record(record, engine, gen_param, is_reason):
    # Build prompt
    prompt = record["question"]
    
    try:
        output_record = record.copy()
        if is_reason:
            thought, response = await MODEL_request_by_API_async(
                engine=engine,
                msg=prompt,
                gen_param=gen_param,
                is_reason=is_reason
            )
            output_record["thought"] = thought
        else:
            response = await MODEL_request_by_API_async(
                engine=engine,
                msg=prompt,
                gen_param=gen_param,
                is_reason=is_reason
            )
            output_record["thought"] = ""
        # Build output record        
        output_record["response"] = response
        return output_record
    except Exception as e:
        print(f"Error processing record: {e}")
        return None

async def process_batch(batch, engine, gen_param, is_reason):
    tasks = [process_record(record, engine, gen_param, is_reason) for record in batch]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]

def process_input_record(record, file_ext):
    """Process different input record formats and convert to {"question": question, "answer": answer} format"""
    if file_ext == '.jsonl':
        # Already in correct format, return directly
        return {"question": record["text"], "answer": record.get("answer", "")}
    elif file_ext == '.json':
        # Process array format dialogue data
        try:
            # Get question (human's value field)
            question = next(item['value'] for item in record if item['from'] == 'human')
            # Get answer (assistant's ground_truth.value field)
            answer = next(item['ground_truth']['value'] for item in record if item['from'] == 'assistant')
            return {
                "question": question,
                "answer": answer
            }
        except (KeyError, StopIteration) as e:
            print(f"Error processing record format: {e}")
            return None
    else:
        print(f"Unsupported file format: {file_ext}")
        return None

async def process_file_async(engine, input_file, output_file, batch_size=5, is_reason=True):
    processed_data = []
    
    # Get file extension
    _, file_ext = os.path.splitext(input_file)
    
    # Print dataset and model information
    print(f"\nProcessing dataset: {input_file}")
    print(f"Using model: {engine}")
    print(f"Batch size: {batch_size}")
    
    # Read data based on file type
    if file_ext == '.json':
        with open(input_file, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
        total_lines = len(all_data)
    else:  # .jsonl
        total_lines = sum(1 for _ in open(input_file, 'r', encoding='utf-8'))
    
    print(f"Total samples to process: {total_lines}")
    
    gen_param = {
        "temperature": 0.6,
        "top_p": 0.8,
        "max_tokens": 16384,
        "stream": True
    }
    
    current_batch = []
    
    with open(output_file, 'w', encoding='utf-8') as output_f:
        if file_ext == '.json':
            # Process JSON array format
            with tqdm(total=total_lines, desc="Processing samples", ncols=100) as pbar:
                for record in all_data:
                    processed_record = process_input_record(record, file_ext)
                    if processed_record:
                        current_batch.append(processed_record)
                        
                        if len(current_batch) >= batch_size:
                            results = await process_batch(current_batch, engine, gen_param, is_reason)
                            # 直接写入文件并flush
                            for item in results:
                                output_f.write(json.dumps(item, ensure_ascii=False) + '\n')
                                output_f.flush()
                            processed_data.extend(results)
                            pbar.update(len(current_batch))
                            current_batch = []
        else:
            # Process JSONL format
            with open(input_file, 'r', encoding='utf-8') as f:
                with tqdm(total=total_lines, desc="Processing samples", ncols=100) as pbar:
                    for line in f:
                        try:
                            record = json.loads(line.strip())
                            processed_record = process_input_record(record, file_ext)
                            if processed_record:
                                current_batch.append(processed_record)
                                
                                if len(current_batch) >= batch_size:
                                    results = await process_batch(current_batch, engine, gen_param, is_reason)
                                    # 直接写入文件并flush
                                    for item in results:
                                        output_f.write(json.dumps(item, ensure_ascii=False) + '\n')
                                        output_f.flush()
                                    processed_data.extend(results)
                                    pbar.update(len(current_batch))
                                    current_batch = []
                                    
                        except json.JSONDecodeError as e:
                            tqdm.write(f"JSON parsing error: {e}")
                            continue
        
        # Process remaining samples
        if current_batch:
            results = await process_batch(current_batch, engine, gen_param, is_reason)
            for item in results:
                output_f.write(json.dumps(item, ensure_ascii=False) + '\n')
                output_f.flush()
            processed_data.extend(results)
            pbar.update(len(current_batch))
    
    # Print final statistics
    print(f"Successfully processed {len(processed_data)} samples")
    print(f"Success rate: {(len(processed_data)/total_lines)*100:.2f}%")

async def main_async(args):
    print("Starting data processing...")
    
    # Generate output_file from input_file, replace '/' with '_' in model name
    base, ext = os.path.splitext(args.input_file)
    model_name = args.model.replace('/', '_')
    output_file = f"{base}_{model_name}{ext}"
    
    await process_file_async(
        engine=args.model,
        input_file=args.input_file,
        output_file=output_file,
        batch_size=args.batch_size,
        is_reason=args.is_reason
    )
    print(f"Processing completed! Output saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Process dataset using DeepSeek-R1')
    parser.add_argument('--model', type=str, default="deepseek-ai/DeepSeek-R1", help='Model name')
    parser.add_argument('--input_file', type=str, default="datasets/raw/orz_math_57k_format.json", help='Input file')
    parser.add_argument('--batch_size', type=int, default=4, help='Batch size for concurrent processing')
    parser.add_argument('--is_reason', type=bool, default=True, help='Whether reasoning is needed')
    args = parser.parse_args()

    asyncio.run(main_async(args))

if __name__ == "__main__":
    main()
