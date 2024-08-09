import os 
from pycsghub.repo_reader import AutoModelForCausalLM, AutoTokenizer

os.environ['CSG_TOKEN'] = '3b77c98077b415ca381ded189b86d5df226e3776'

mid = 'OpenCSG/csg-wukong-1B'
model = AutoModelForCausalLM.from_pretrained(mid)
tokenizer = AutoTokenizer.from_pretrained(mid)

inputs = tokenizer.encode("Write a short story", return_tensors="pt")
outputs = model.generate(inputs)
print('result: ',tokenizer.batch_decode(outputs))
