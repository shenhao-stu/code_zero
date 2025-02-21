import os
os.system('pip install gradio==4.44.0')
from threading import Thread
from typing import Iterator
import torch
import gradio as gr
from modelscope import AutoTokenizer, AutoModelForCausalLM
from transformers import TextIteratorStreamer

# 定义常量
MAX_MAX_NEW_TOKENS = 2048
DEFAULT_MAX_NEW_TOKENS = 1024
MAX_INPUT_TOKEN_LENGTH = int(os.getenv("MAX_INPUT_TOKEN_LENGTH", "4096"))


# 加载模型
model_name_or_path = 'anine09/MeowPilot_by_PowerBankPirates'
if torch.cuda.is_available():
    model = AutoModelForCausalLM.from_pretrained(
        model_name_or_path,
        torch_dtype=torch.float16,
        device_map="auto")
else:
    model = AutoModelForCausalLM.from_pretrained(
        model_name_or_path,
        torch_dtype=torch.float16,
        device_map="cpu")

tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
tokenizer.use_default_system_prompt = False

# 生成函数
def generate(
    message: str,
    chat_history: list[tuple[str, str]],
    system_prompt: str,
    max_new_tokens: int = 1024,
    temperature: float = 0.6,
    top_p: float = 0.9,
    top_k: int = 50,
    repetition_penalty: float = 1.2,
) -> Iterator[str]:
    conversation = []
    if system_prompt:
        conversation.append({"role": "system", "content": system_prompt})
    for user, assistant in chat_history:
        conversation.extend([{"role": "user", "content": user}, {"role": "assistant", "content": assistant}])
    conversation.append({"role": "user", "content": message})

    input_ids = tokenizer.apply_chat_template(conversation, tokenize=False, add_generation_prompt=True)
    input_ids = tokenizer([input_ids], return_tensors="pt").to(model.device)

    streamer = TextIteratorStreamer(tokenizer, timeout=10.0, skip_prompt=True, skip_special_tokens=True)
    generate_kwargs = dict(
        input_ids=input_ids.input_ids,
        streamer=streamer,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        top_p=top_p,
        top_k=top_k,
        temperature=temperature,
        repetition_penalty=repetition_penalty,
    )
    
    t = Thread(target=model.generate, kwargs=generate_kwargs)
    t.start()

    outputs = []
    for text in streamer:
        outputs.append(text)
        yield "".join(outputs)
    
    #outputs = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    print(outputs)
    #yield outputs

# 创建聊天界面
chat_interface = gr.ChatInterface(
    fn=generate,
    additional_inputs=[
        gr.Textbox(
            label="System Prompt",
            value="You are MeowPilot, an helpful AI cat-girl assistant.",
            lines=3
        ),
        gr.Slider(
            label="Max new tokens",
            minimum=1,
            maximum=MAX_MAX_NEW_TOKENS,
            value=DEFAULT_MAX_NEW_TOKENS,
            step=1
        ),
        gr.Slider(
            label="Temperature",
            minimum=0.1,
            maximum=4.0,
            value=0.6,
            step=0.1
        ),
        gr.Slider(
            label="Top-p",
            minimum=0.05,
            maximum=1.0,
            value=0.9,
            step=0.05
        ),
        gr.Slider(
            label="Top-k",
            minimum=1,
            maximum=1000,
            value=50,
            step=1
        ),
        gr.Slider(
            label="Repetition Penalty",
            minimum=1.0,
            maximum=2.0,
            value=1.2,
            step=0.05
        ),
    ],
    stop_btn=None,
    examples=[
        ["你好！你是谁？"],
        ["一个数的2倍加上3等于11，这个数是多少？"],
        ["x^2-4x+3=0的解是多少？"],
        ["求方程 $\\sqrt{1995}x^{\\log_{1995}x}=x^2$ 的正根的乘积的最后三位数字。"]
    ],
)

# 创建主界面
with gr.Blocks(css="style.css") as demo:
    gr.Markdown("""<p align="center"><img src="https://modelscope.cn/api/v1/studio/shenhao23/MeowPilot/repo?Revision=master&FilePath=logo.png&View=true" style="height: 200px"/><p>""")
    gr.Markdown("""<center><font size=8>MeowPilot Bot🥳</center>""")
    gr.Markdown("""<center><font size=4>赛博喵娘(≧◡≦) MeowPilot（Qwen2.5-1.5B-Instruct） 是夺宝奇兵团队研发的一款有趣的，逻辑能力很强的助手。</center>""")
    chat_interface.render()

if __name__ == "__main__":
    demo.queue(max_size=20).launch()