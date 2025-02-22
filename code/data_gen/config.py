from openai import OpenAI
import time

MAX_RETRY = 5

DEFAULT_API_KEY = 'API_KEY'
DEFAULT_API_URL = 'https://api-inference.modelscope.cn/v1/'

LOCAL_API_KEY = 'EMPTY'
LOCAL_API_URL = 'http://localhost:8000/v1' # TODO: localhost:8000 needs to be changed to the actual ip:port


def MODEL_request_by_API(engine, msg, gen_param, is_local=False, is_token_count = False, is_reason=False):
    retry = MAX_RETRY
    if is_local:
        api_url = LOCAL_API_URL
        api_key = LOCAL_API_KEY
    else:
        api_url = DEFAULT_API_URL
        api_key = DEFAULT_API_KEY
    
    client = OpenAI(base_url=api_url, api_key=api_key)

    while retry > 0:
        try:
            response = client.chat.completions.create(
                model = engine,
                messages = [
                    {
                        "role": "user",
                        "content": msg
                    }
                    ],
                **gen_param
            )
            
            # Handle streaming response
            if gen_param.get('stream', False):
                full_content = ''
                full_reasoning = ''
                done_reasoning = False
                
                for chunk in response:
                    if is_reason:
                        # Processing for reasoning model
                        reasoning_chunk = chunk.choices[0].delta.reasoning_content
                        answer_chunk = chunk.choices[0].delta.content
                        
                        if reasoning_chunk:
                            full_reasoning += reasoning_chunk
                            print(reasoning_chunk, end='', flush=True)
                        elif answer_chunk:
                            if not done_reasoning:
                                print('\n\n === Final Answer ===\n')
                                done_reasoning = True
                            full_content += answer_chunk
                            print(answer_chunk, end='', flush=True)
                    else:
                        # Processing for non-reasoning model
                        content = chunk.choices[0].delta.content
                        if content:
                            full_content += content
                            print(content, end='', flush=True)
                
                if is_token_count:
                    return (full_reasoning, full_content, 0, 0) if is_reason else (full_content, 0, 0)
                else:
                    return (full_reasoning, full_content) if is_reason else full_content
            
            # Handle non-streaming response
            inp_tokens = response.usage.prompt_tokens
            out_tokens = response.usage.completion_tokens
            if is_token_count:
                if not is_reason:
                    return response.choices[0].message.content, inp_tokens, out_tokens
                else:
                    return response.choices[0].message.reasoning_content, response.choices[0].message.content, inp_tokens, out_tokens
            else:
                if not is_reason:
                    return response.choices[0].message.content
                else:
                    return response.choices[0].message.reasoning_content, response.choices[0].message.content

        except Exception as e:
            print(f"API call error: {e}\nRetrying {MAX_RETRY + 1 - retry} time(s)...")
            retry -= 1
            time.sleep(10)
            continue
    
    return None

def main():
    engine = "Qwen/Qwen2.5-72B-Instruct"
    msg = "hello, who are u?"
    gen_param = {"max_tokens": 2000, "temperature": 1, "top_p": 0.8, "stream": False}

    response = MODEL_request_by_API(engine, msg, gen_param)
    print(response)

if __name__ == "__main__":
    main()