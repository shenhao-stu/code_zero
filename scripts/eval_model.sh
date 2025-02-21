MODEL_PATH="<MODEL PATH>"
MODEL_NAME="<MODEL SERVICE NAME>"

swift deploy \
--model $MODEL_PATH \
--infer_backend vllm \
--served_model_name $MODEL_NAME \
--gpu-memory-utilization 0.9 \
--port 8801
