import torch
import pickle
import threading
from transformers import BertTokenizer
from bert_pytorch.model.bert import BERTModel


class ModelManager:
    """Singleton class to manage ML model loading and inference"""
    _instance = None
    _lock = threading.Lock()
    _model = None
    _tokenizer = None
    _vocab_size = None
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._model is None:
            self._load_model()
    
    def _load_model(self):
        """Load model and tokenizer once"""
        try:
            # Model paths
            MODEL_PATH = "../output/university_logs/bert/best_bert.pth"
            VOCAB_PATH = "../output/university_logs/vocab.pkl"
            
            # Initialize BERT tokenizer
            self._tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
            
            # Load vocab
            with open(VOCAB_PATH, "rb") as f:
                vocab = pickle.load(f)
            self._vocab_size = len(vocab)
            
            # Initialize BERT model
            self._model = BERTModel(vocab_size=self._vocab_size)
            
            # Load trained weights
            state_dict = torch.load(MODEL_PATH, map_location=torch.device('cpu'))
            self._model.load_state_dict(state_dict)
            self._model.eval()
            
            print("✅ ML Model loaded successfully")
            
        except Exception as e:
            print(f"❌ ML Model Load Error: {str(e)}")
            self._model = None
            self._tokenizer = None
    
    def get_model_components(self):
        """Get model and tokenizer"""
        return self._model, self._tokenizer
    
    def is_loaded(self):
        """Check if model is loaded"""
        return self._model is not None and self._tokenizer is not None
    
    def predict_batch(self, messages):
        """Predict anomaly scores for a batch of messages"""
        if not self.is_loaded():
            return [0.5] * len(messages)  # Default scores
        
        try:
            scores = []
            
            # Process messages in batches for better performance
            batch_size = 32
            for i in range(0, len(messages), batch_size):
                batch = messages[i:i + batch_size]
                
                # Tokenize batch
                inputs = self._tokenizer(
                    batch,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=512
                )
                
                with torch.no_grad():
                    outputs = self._model(
                        input_ids=inputs['input_ids'],
                        attention_mask=inputs['attention_mask']
                    )
                    
                    # Convert model output to anomaly scores
                    batch_scores = torch.sigmoid(outputs.logits[:, 0]).tolist()
                    scores.extend(batch_scores)
            
            return scores
            
        except Exception as e:
            print(f"Prediction error: {str(e)}")
            return [0.5] * len(messages)  # Default scores
    
    def predict_single(self, message):
        """Predict anomaly score for a single message"""
        return self.predict_batch([message])[0]


# Global instance
model_manager = ModelManager()
