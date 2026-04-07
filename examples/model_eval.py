import torch
from transformers import BertTokenizer, BertForSequenceClassification
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score
import pandas as pd
import logging
from pycsghub.snapshot_download import snapshot_download

# pip install -U scikit-learn

def DownloadModel(local_path: str):
    # token = "your access token"
    token = None
    endpoint = "https://hub.opencsg.com"
    repo_type = "model"
    repo_id = "wanghh2000/Erlangshen-RoBERTa-110M-Sentiment"
    local_dir = local_path

    # set log level
    logging.basicConfig(
        level=getattr(logging, "INFO"),
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[logging.StreamHandler()]
    )

    result = snapshot_download(
        repo_id, 
        repo_type=repo_type, 
        local_dir=local_dir, 
        endpoint=endpoint, 
        token=token)

    print(f"Save model to {result}")

class BERTEvaluator:
    def __init__(self, model_path):
        """
        Initialize the Evaluator
        model_path: Path to the trained model
        """
        # model_name='bert-base-chinese'
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.tokenizer = BertTokenizer.from_pretrained(model_path)
        self.model = BertForSequenceClassification.from_pretrained(model_path)
        print(f"Model loaded from {model_path}")
        self.model.to(self.device)
        self.model.eval()
        print(f"Set model to evaluation mode")
    
    def predict_single(self, text, max_length=128):
        """Predict a single text"""
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding=True,
            max_length=max_length,
            return_tensors='pt'
        )
        
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)
        
        with torch.no_grad():
            outputs = self.model(input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            prediction = torch.argmax(logits, dim=-1).item()
            probabilities = torch.softmax(logits, dim=-1).cpu().numpy()[0]
        
        return prediction, probabilities
    
    def evaluate_batch(self, texts, true_labels, batch_size=16):
        """Evaluate the model on a batch of texts"""
        all_predictions = []
        
        # Process the batch of texts in batches
        for i in range(0, len(texts), batch_size):
            print(f"Processing batch {i//batch_size+1}/{len(texts)//batch_size+1}")
            batch_texts = texts[i:i+batch_size]
            # batch_labels = true_labels[i:i+batch_size]
            
            # Encode the batch of texts
            encodings = self.tokenizer(
                batch_texts,
                truncation=True,
                padding=True,
                max_length=128,
                return_tensors='pt'
            )
            
            input_ids = encodings['input_ids'].to(self.device)
            attention_mask = encodings['attention_mask'].to(self.device)
            
            # Predict the batch of texts
            with torch.no_grad():
                outputs = self.model(input_ids, attention_mask=attention_mask)
                predictions = torch.argmax(outputs.logits, dim=-1)
                all_predictions.extend(predictions.cpu().numpy())
        
        print(f"Processed {len(texts)} texts and started calculating metrics")
        # Calculate metrics
        accuracy = accuracy_score(true_labels, all_predictions)
        precision = precision_score(true_labels, all_predictions, average='binary')
        recall = recall_score(true_labels, all_predictions, average='binary')
        f1 = f1_score(true_labels, all_predictions, average='binary')
        
        # Generate a detailed classification report
        report = classification_report(true_labels, all_predictions, target_names=['negative', 'positive'])
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'predictions': all_predictions,
            'classification_report': report
        }

if __name__ == "__main__":
    model_path = "/Users/hhwang/temp/Erlangshen-RoBERTa-110M-Sentiment"
    DownloadModel(local_path=model_path)

    # Initialize the Evaluator
    # model_path: Path to the trained model
    evaluator = BERTEvaluator(model_path=model_path)
    # Prepare test data
    test_texts = [
        "This movie is great!",
        "This service is terrible!",
        "The product quality is good, I recommend recommend it!",
        "The delivery is slow, I am not satisfied with it.",
    ]
    test_labels = [1, 0, 1, 0]  # 1: positive, 0: negative
    # Evaluate the model on the test data in batches
    results = evaluator.evaluate_batch(test_texts, test_labels)
    # Print the results
    print("\n" + "="*60)
    print("BERT Model Evaluation Results ")
    print("="*60)
    # Accuracy: The proportion of correct predictions among all predictions. Measures the overall correctness rate.
    print(f"Accuracy (Accuracy):  {results['accuracy']:.4f}")
    # Among all samples predicted as positive by the model, how many are truly positive. Measures how accurate the model is when it predicts positive.
    print(f"Precision (Precision): {results['precision']:.4f}")
    # Among all samples that are truly positive, how many are correctly predicted as positive. Measures how complete the model is when it predicts positive.
    print(f"Recall (Recall):    {results['recall']:.4f}")
    # Used to balance precision and recall. Measures whether the model's performance is balanced between positive and negative classes.
    print(f"F1-Score (F1-Score):  {results['f1_score']:.4f}")
    print("\nDetailed Classification Report:")
    print(results['classification_report'])
