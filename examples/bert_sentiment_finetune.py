import os

os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
current_dir = os.getcwd()

from datasets import load_dataset
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification,
    Trainer, 
    TrainingArguments
)
from pycsghub.snapshot_download import snapshot_download

# 下载数据集
dataset_id = "wanghh2000/sentiment-train-data"
print(f'\n开始下载数据集 {dataset_id}')
result = snapshot_download(dataset_id, repo_type="dataset", local_dir="./sentiment-train-data")

# 下载模型
model_id = "wanghh2000/bert-base-chinese"
print(f'\n开始下载模型 {model_id}')
result = snapshot_download(model_id, repo_type="model", local_dir="./bert-base-chinese")

# 加载数据
dataset = load_dataset("json", data_dir="./sentiment-train-data")

# 查看数据meta信息
print('\n训练数据集meta信息:', dataset)

# 查看前2条示例数据
print('\n数据集前2条示例数据:', dataset["train"][:2])

# 划分训练集和测试集（80%训练，20%测试）
dataset = dataset["train"].train_test_split(test_size=0.2, seed=42)

# 加载分词器和模型
model_name = os.path.join(current_dir, 'bert-base-chinese')
print('\n加载模型:', model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

# 分词处理, 训练时会自动使用label列作为监督信号
def tokenize_function(examples):
    return tokenizer(
        examples["text"], # 指定训练文本列
        padding="max_length", # 文本按最大长度对齐
        truncation=True, # 截断超长文本
        max_length=256 # 最大文本长度
    )

tokenized_dataset = dataset.map(tokenize_function, batched=True)

# 设置训练参数
training_args = TrainingArguments(
    output_dir="./model-checkpoints",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    eval_strategy="epoch",  # 注意旧版本是evaluation_strategy
    save_strategy="epoch",
    logging_steps=5,
    load_best_model_at_end=True,
    metric_for_best_model="accuracy",
    dataloader_pin_memory=False,
)

# 定义评估指标
from sklearn.metrics import accuracy_score

def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    acc = accuracy_score(labels, preds)
    return {"accuracy": acc}

# 创建 Trainer 并训练
trainer = Trainer(
    model=model, # 指定微调的模型
    args=training_args, # 指定微调训练参数
    train_dataset=tokenized_dataset["train"], # 指定训练集
    eval_dataset=tokenized_dataset["test"], # 指定测试集
    compute_metrics=compute_metrics, # 指定微调评估指标
)

# 开始微调训练
print('\n开始微调训练...')
trainer.train()

# 保存模型权重
model.save_pretrained("./chs-sentiment-model")
tokenizer.save_pretrained("./chs-sentiment-model")
print('\n模型微调完成保存到目录:{}'.format(os.path.join(current_dir, 'chs-sentiment-model')))

# 测试推理
test_text = "这家店的奶茶超级好喝，珍珠也很Q弹！"
device = model.device
inputs = tokenizer(test_text, return_tensors="pt", truncation=True, max_length=256)
inputs = {k: v.to(device) for k, v in inputs.items()}
outputs = model(**inputs)
pred = outputs.logits.argmax().item()
print('\n测试文本:[{}]'.format(test_text), '预测结果:{}'.format("正面" if pred == 1 else "负面"))

# 上传微调后的模型

print('\n开始上传微调后的模型...')
from pycsghub.upload_large_folder.main import upload_large_folder_internal
upload_large_folder_internal(
    repo_id="wanghh2000/chs-sentiment-model",
    local_path=os.path.join(current_dir, 'chs-sentiment-model'),
    repo_type="model",
    revision="main",
    endpoint="https://hub.opencsg.com",
    token=None,
    allow_patterns=None,
    ignore_patterns=None,
    num_workers=1,
    print_report=False,
    print_report_every=1,
)
