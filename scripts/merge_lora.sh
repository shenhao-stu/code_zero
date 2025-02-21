MODEL_PATH="<CHECKPOINT PATH>"
TOKEN="<MODELSCOPE SDK TOKEN>"
MODEL_ID="<USER NAME>/<MODEL NAME>"
USE_HF=0 # 0: push to modelscope, 1: push to huggingface

swift export \
    --adapters $MODEL_PATH \
    --merge_lora true \
    --push_to_hub true \
    --hub_model_id $MODEL_ID \
    --hub_token $TOKEN
