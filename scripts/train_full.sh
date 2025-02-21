MODEL_PATH="<MODEL PATH>"

DATASET_PATH="<DATASET PATH>"
COLUMNS='{"question":"query","answer":"response"}' # TODO: change the columns to the actual columns

SWANLAB_PROJECT="<SWANLAB PROJECT>"
EXP_NAME="<EXPERIMENT NAME>"
mkdir -p /mnt/workspace/train/model_output/$EXP_NAME/runs

nohup swift sft \
    --tuner_backend unsloth \
    --torch_dtype bfloat16 \
    --train_type full \
    --model $MODEL_PATH \
    --num_train_epochs 10 \
    --warmup_ratio 0.05 \
    --model_type qwen2_5 \
    --template qwen2_5 \
    --dataset $DATASET_PATH \
    --columns $COLUMNS \
    --system "<SYSTEM PROMPT>" \
    --max_length 8192 \
    --learning_rate 1e-5 \
    --attn_impl flash_attn \
    --gradient_accumulation_steps 16 \
    --eval_steps 500 \
    --add_version False \
    --output_dir /mnt/workspace/train/model_output/$EXP_NAME \
    --logging_dir /mnt/workspace/train/model_output/$EXP_NAME/runs \
    --ignore_args_error True \
    --report_to swanlab \
    --swanlab_project $SWANLAB_PROJECT \
    --swanlab_exp_name $EXP_NAME \
    > /mnt/workspace/train/model_output/$EXP_NAME/runs/run.log 2>&1 &
