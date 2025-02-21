import os
from evalscope.collections.sampler import WeightedSampler
from evalscope.collections.schema import CollectionSchema, DatasetInfo
from evalscope.utils.io_utils import dump_jsonl_data

model_name = 'meow_pilot'
output_dir = 'eval'
api_url = 'http://127.0.0.1:8801/v1/chat/completions'
api_key = 'EMPTY'

## construct the eval dataset ##
schema = CollectionSchema(name=model_name, datasets=[
            CollectionSchema(name='Math', datasets=[
                    DatasetInfo(name='math_500', weight=1, task_type='math', tags=['en'], args={'few_shot_num': 0}),
                    DatasetInfo(name='gpqa', weight=1, task_type='math', tags=['en'],  args={'subset_list': ['gpqa_diamond'], 'few_shot_num': 0}),
                    DatasetInfo(name='gsm8k', weight=1, task_type='math', tags=['en'],  args={'few_shot_num': 0}),
            ])
        ])

print(schema.to_dict())
print(schema.flatten())

## get the mixed data ##
mixed_data = WeightedSampler(schema).sample(100000)  # set a large number to ensure all datasets are sampled
os.makedirs(output_dir, exist_ok=True)
dump_jsonl_data(mixed_data, f'{output_dir}/{model_name}.jsonl')

## start the task ##
from evalscope import TaskConfig, run_task
from evalscope.constants import EvalType

task_cfg = TaskConfig(
    model=model_name,
    api_url=api_url,
    api_key=api_key,
    eval_type=EvalType.SERVICE,
    datasets=[
        'data_collection',
    ],
    dataset_args={
        'data_collection': {
            'local_path': f'{output_dir}/{model_name}.jsonl'
        }
    },
    chat_template="Please reason step by step, and put your final answer within \boxed{}.",
    eval_batch_size=16,
    generation_config={
        'max_tokens': 28000,  # avoid exceed max length
        'temperature': 0.6,
        'top_p': 0.95,
    },
)

run_task(task_cfg=task_cfg)
