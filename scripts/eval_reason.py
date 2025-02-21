from evalscope import TaskConfig, run_task
from evalscope.constants import EvalType

model_name = ''    
api_url = 'http://127.0.0.1:8001/v1/chat/completions'
api_key = 'EMPTY'

task_cfg = TaskConfig(
    model=model_name,   # Model name (must match the deployed model name)
    api_url=api_url,  # Inference service URL
    api_key=api_key,
    eval_type=EvalType.SERVICE,   # Evaluation type, SERVICE means evaluating inference service
    datasets=[
        'data_collection',  # Dataset name (fixed as data_collection for using mixed dataset)
    ],
    dataset_args={
        'data_collection': {
            'dataset_id': 'modelscope/R1-Distill-Math-Test'  # Dataset ID or local dataset path
        }
    },
    chat_template="Please reason step by step, and put your final answer within \\boxed{}. The reasoning process and answer are enclosed within <think> </think> and <answer> </answer> tags, respectively, i.e., <think> reasoning process here </think> <answer> answer here </answer>.",
    eval_batch_size=32,       # Number of concurrent requests
    generation_config={       # Model inference configuration
        'max_tokens': 20000,  # Maximum number of tokens to generate, set large to avoid truncation
        'temperature': 0.6,   # Sampling temperature (recommended value from deepseek report)
        'top_p': 0.95,        # Top-p sampling (recommended value from deepseek report) 
        'n': 5                # Number of responses per request (note: lmdeploy currently only supports n=1)
    },
)

run_task(task_cfg=task_cfg)