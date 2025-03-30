# import os
# os.environ['HF_ENDPOINT'] = 'https://hub.opencsg.com/hf'
# from transformers import AutoTokenizer, AutoModelForCausalLM

from pycsghub.repo_reader import AutoModelForCausalLM, AutoTokenizer

# mid = '/Users/hhwang/code/jihulab/opencsg/csghub-sdk/mind'
mid = 'wanghh2000/MyMind-0.05B'
tokenizer = AutoTokenizer.from_pretrained(mid)
model = AutoModelForCausalLM.from_pretrained(mid, trust_remote_code=True)
print(f'MyMind参数量: {sum(p.numel() for p in model.parameters() if p.requires_grad) / 1e6:.2f} M(illion)')

messages = []
messages.append({"role": "user", "content": "你擅长哪一个学科？"})

new_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)[-8191:]

inputs = tokenizer.encode(new_prompt, return_tensors="pt")
outputs = model.generate(inputs)
result = tokenizer.batch_decode(outputs)
# print('<<< result >>>')
print(result[0])
