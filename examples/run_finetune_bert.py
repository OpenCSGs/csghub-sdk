from typing import Any
import pandas as pd

from transformers import DataCollatorWithPadding
from transformers import TrainingArguments
from transformers import Trainer

from pycsghub.repo_reader import load_dataset
from pycsghub.repo_reader import AutoModelForSequenceClassification, AutoTokenizer, AutoConfig

model_id_or_path = "wanghh2000/bert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_id_or_path, trust_remote_code=True)
model = AutoModelForSequenceClassification.from_pretrained(model_id_or_path)

dsPath = "wanghh2000/glue"
dsName = "mrpc"
# access_token = "your_access_token"
access_token = None
raw_datasets = load_dataset(dsPath, dsName, token=access_token)

def get_data_proprocess() -> Any:
    def preprocess_function(examples: pd.DataFrame):            
        ret = tokenizer(examples["sentence1"], examples["sentence2"], truncation=True, max_length=100)
        ret = {**examples, **ret}
        return pd.DataFrame.from_dict(ret)
    return preprocess_function

train_dataset = raw_datasets["train"].select(range(20)).map(get_data_proprocess(), batched=True)
eval_dataset = raw_datasets["validation"].select(range(20)).map(get_data_proprocess(), batched=True)

def data_collator() -> Any:
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
    return data_collator

outputDir = "/Users/hhwang/temp/ff"
args = TrainingArguments(
    outputDir,
    eval_strategy="steps",
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

trainer = Trainer(
    model,
    args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    data_collator=data_collator(),
)

trainResult = trainer.train()
trainer.save_model()
print(f"save model to {outputDir}")
