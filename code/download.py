from modelscope.msdatasets import MsDataset
from modelscope import snapshot_download
from datasets import load_dataset

# 'GAIR/LIMO'
# 'AI-ModelScope/SWE-bench_Verified'
# 'hkust-nlp/CodeIO-PyEdu-Reasoning'
# 'open-thoughts/OpenThoughts-114k'

model_dir = snapshot_download('Qwen/Qwen2.5-72B-Instruct', cache_dir='./eval_model/extra')
ds =  MsDataset.load('AI-ModelScope/SWE-bench', subset_name='default', split='train', cache_dir='./datasets/raw')
ds = load_dataset("princeton-nlp/SWE-bench_Lite_oracle", cache_dir='./datasets/raw')
