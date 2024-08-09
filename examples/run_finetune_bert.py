
# export HF_ENDPOINT=http://127.0.0.1:8080/hf
# export CSGHUB_DOMAIN=http://127.0.0.1:8080

from typing import Any
import pandas as pd

from transformers import DataCollatorWithPadding
from transformers import TrainingArguments
from transformers import Trainer

# print(f"=============== load model and dataset by HF SDK ==============")
# from datasets.load import load_dataset
# from transformers import AutoModelForSequenceClassification, AutoTokenizer, AutoConfig, AutoModel

# model_id_or_path = "/Users/hhwang/models/bert-base-uncased"
# config = AutoConfig.from_pretrained(model_id_or_path, trust_remote_code=True)
# model = AutoModelForSequenceClassification.from_pretrained(model_id_or_path, config=config)

print(f"=============== load model and dataset by OpenCSG SDK ==============")
from pycsghub.repo_reader import load_dataset
from pycsghub.repo_reader import AutoModelForSequenceClassification, AutoTokenizer, AutoConfig

model_id_or_path = "wanghh2003/bert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_id_or_path, trust_remote_code=True)
model = AutoModelForSequenceClassification.from_pretrained(model_id_or_path)

dsPath = "wanghh2003/datasset1"
dsName = None
# dsPath = "wanghh2003/glue"
# dsName = "mrpc"
# access_token = "f9fd525960ed86c4024d7f73f955df3c8b416434"
access_token = None
raw_datasets = load_dataset(dsPath, dsName, token=access_token)

def get_data_proprocess() -> Any:
    def preprocess_function(examples: pd.DataFrame):            
        # examples = examples.to_dict("list")
        ret = tokenizer(examples["sentence1"], examples["sentence2"], truncation=True, max_length=100)
        # Add back the original columns
        ret = {**examples, **ret}
        return pd.DataFrame.from_dict(ret)
    return preprocess_function

print(f"=============== raw_datasets ==============")
print(raw_datasets)
# train_dataset = raw_datasets["train"].map(get_data_proprocess(), batched=True)
# eval_dataset = raw_datasets["validation"].map(get_data_proprocess(), batched=True)
train_dataset = raw_datasets["train"].select(range(20)).map(get_data_proprocess(), batched=True)
eval_dataset = raw_datasets["validation"].select(range(20)).map(get_data_proprocess(), batched=True)
print(f"=============== train_dataset ==============")
print(train_dataset)
print(f"=============== eval_dataset ==============")
print(eval_dataset)

def data_collator() -> Any:
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
    return data_collator

print(f"=============== build TrainingArguments ==============")
outputDir = "/Users/hhwang/temp/ff"
args = TrainingArguments(
    outputDir,
    evaluation_strategy="steps",
    save_strategy="steps",
    logging_strategy="steps",
    logging_steps = 2,
    save_steps = 10,
    eval_steps = 2,
    learning_rate=2e-5,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    num_train_epochs=2,
    weight_decay=0.01,
    push_to_hub=False,
    disable_tqdm=False,  # declutter the output a little
    use_cpu=True,  # you need to explicitly set no_cuda if you want CPUs
    remove_unused_columns=True,
)

print(f"=============== build Trainer ==============")
trainer = Trainer(
    model,
    args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    tokenizer=tokenizer,
)

print(f"=============== start training ==============")
trainResult = trainer.train()
print(f"=============== end training ==============")
trainer.save_model()
print(f"=============== saved model ==============")
print(f"save model to {outputDir}")
