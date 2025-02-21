MODEL_PATH="<MODEL PATH>"
DATASET_PATH="AI-MO/NuminaMath-TIR#5000"

SWANLAB_PROJECT="<SWANLAB PROJECT>"
EXP_NAME="<EXPERIMENT NAME>"
mkdir -p /mnt/workspace/train/model_output/$EXP_NAME/runs

# nproc_per_node is one less than the number of GPUs, as vLLM is deployed on the last GPU (GPU 7) by default
CUDA_VISIBLE_DEVICES=0,1,2,3 \
NPROC_PER_NODE=3 \
swift rlhf \
    --rlhf_type grpo \
    --model $MODEL_PATH \
    --reward_funcs accuracy format \
    --use_vllm true \
    --vllm_device auto \
    --vllm_gpu_memory_utilization 0.7 \
    --vllm_max_model_len 8192 \
    --train_type full \
    --torch_dtype bfloat16 \
    --dataset $DATASET_PATH \
    --max_completion_length 2048 \
    --num_train_epochs 1 \
    --per_device_train_batch_size 1 \
    --per_device_eval_batch_size 1 \
    --learning_rate 1e-6 \
    --gradient_accumulation_steps 2 \
    --eval_steps 200 \
    --save_steps 200 \
    --save_total_limit 2 \
    --logging_steps 5 \
    --max_length 4096 \
    --output_dir /mnt/workspace/train/model_output/$EXP_NAME \
    --warmup_ratio 0.05 \
    --dataloader_num_workers 4 \
    --dataset_num_proc 4 \
    --num_generations 3 \
    --temperature 0.9 \
    --system 'scripts/grpo_prompt.txt' \
    --deepspeed zero2 \
    --log_completions true \
    --report_to swanlab \
    --swanlab_project $SWANLAB_PROJECT \
    --swanlab_exp_name $EXP_NAME \