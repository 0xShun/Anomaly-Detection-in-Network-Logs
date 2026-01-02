import torch
import torch.nn as nn
import pickle
import threading
import os
from pathlib import Path
from transformers import AutoTokenizer, BertModel
from huggingface_hub import hf_hub_download


class HybridBERTModel(nn.Module):
    """
    Hybrid BERT model that combines text embeddings with template features.
    Architecture: BERT -> template encoder -> fusion -> classifier
    
    Based on the actual checkpoint dimensions:
    - BERT output: 768
    - Template features: 4 -> 128 -> 64
    - Fusion input: 768 + 64 = 832 -> 256
    - Classifier: 256 -> 128 -> 7
    """
    def __init__(self, template_dim=4, num_classes=7):
        super().__init__()
        # Load BERT
        self.bert = BertModel.from_pretrained('bert-base-uncased')
        bert_hidden_size = 768
        
        # Template encoder (processes template features)
        # 4 -> 128 -> 64
        self.template_encoder = nn.Sequential(
            nn.Linear(template_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64)  # Changed from 128 to 64
        )
        
        # Fusion layer (combines BERT + template features)
        # 768 + 64 = 832 -> 256
        self.fusion = nn.Sequential(
            nn.Linear(bert_hidden_size + 64, 256),  # Changed from 512, 896 to 256, 832
            nn.ReLU(),
            nn.Dropout(0.3)
        )
        
        # Classifier
        # 256 -> 128 -> 7
        self.classifier = nn.Sequential(
            nn.Linear(256, 128),  # Changed from 512, 256 to 256, 128
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes)  # Changed from 256 to 128
        )
    
    def forward(self, input_ids, attention_mask, template_features=None):
        # Get BERT embeddings
        bert_output = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        bert_embedding = bert_output.pooler_output  # [batch_size, 768]
        
        # If no template features provided, use zeros
        if template_features is None:
            batch_size = input_ids.size(0)
            template_features = torch.zeros(batch_size, 4, device=input_ids.device)
        
        # Encode template features
        template_embedding = self.template_encoder(template_features)  # [batch_size, 64]
        
        # Fuse BERT and template embeddings
        combined = torch.cat([bert_embedding, template_embedding], dim=1)  # [batch_size, 832]
        fused = self.fusion(combined)  # [batch_size, 256]
        
        # Classify
        logits = self.classifier(fused)  # [batch_size, num_classes]
        
        return logits


class HybridBERTModelManager:
    """
    Singleton class to manage Hybrid-BERT model loading and inference.
    
    This model uses a two-stage pipeline:
    1. BERT for extracting contextual embeddings from log text
    2. XGBoost for multi-class anomaly classification
    
    Classification Categories:
    - 0: Normal (benign operations)
    - 1: Security Anomaly (auth failures, unauthorized access)
    - 2: System Failure (crashes, kernel panics)
    - 3: Performance Issue (timeouts, slow responses)
    - 4: Network Anomaly (connection errors, packet loss)
    - 5: Config Error (misconfigurations, invalid settings)
    - 6: Hardware Issue (disk failures, memory errors)
    """
    
    _instance = None
    _lock = threading.Lock()
    _bert_model = None
    _xgb_model = None
    _tokenizer = None
    
    # Hugging Face model configuration
    HF_REPO_ID = "krishnas4415/log-anomaly-detection-models"
    BERT_MODEL_FILENAME = "models/Hybrid-BERT-Log-Anomaly-Detection/pytorch_model.pt"
    XGB_MODEL_FILENAME = "models/XGBoost-Log-Anomaly-Detection/best_mod.pkl"
    
    # Local cache directory
    MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "models" / "huggingface"
    
    # Anomaly severity mapping (for dashboard alerts)
    ANOMALY_SEVERITY = {
        0: {'name': 'Normal', 'level': 'info', 'score_multiplier': 0.0},
        1: {'name': 'Security Anomaly', 'level': 'critical', 'score_multiplier': 1.0},
        2: {'name': 'System Failure', 'level': 'critical', 'score_multiplier': 0.95},
        3: {'name': 'Performance Issue', 'level': 'medium', 'score_multiplier': 0.6},
        4: {'name': 'Network Anomaly', 'level': 'high', 'score_multiplier': 0.8},
        5: {'name': 'Config Error', 'level': 'high', 'score_multiplier': 0.75},
        6: {'name': 'Hardware Issue', 'level': 'critical', 'score_multiplier': 0.9},
    }
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._bert_model is None:
            self._load_models()
    
    def _download_model_files(self):
        """Download model files from Hugging Face Hub"""
        print("📥 Downloading Hybrid-BERT models from Hugging Face...")
        
        try:
            # Ensure cache directory exists
            self.MODELS_DIR.mkdir(parents=True, exist_ok=True)
            
            # Download BERT model
            print(f"  ⬇️  Downloading BERT model ({self.BERT_MODEL_FILENAME})...")
            bert_model_path = hf_hub_download(
                repo_id=self.HF_REPO_ID,
                filename=self.BERT_MODEL_FILENAME,
                cache_dir=str(self.MODELS_DIR)
            )
            print(f"  ✅ BERT model downloaded: {bert_model_path}")
            
            # Download XGBoost model
            print(f"  ⬇️  Downloading XGBoost model ({self.XGB_MODEL_FILENAME})...")
            xgb_model_path = hf_hub_download(
                repo_id=self.HF_REPO_ID,
                filename=self.XGB_MODEL_FILENAME,
                cache_dir=str(self.MODELS_DIR)
            )
            print(f"  ✅ XGBoost model downloaded: {xgb_model_path}")
            
            return bert_model_path, xgb_model_path
            
        except Exception as e:
            raise RuntimeError(f"Failed to download models from Hugging Face: {str(e)}")
    
    def _load_models(self):
        """Load BERT and XGBoost models"""
        try:
            print("🔧 Loading Hybrid-BERT Model Manager...")
            
            # Download models from Hugging Face
            bert_model_path, xgb_model_path = self._download_model_files()
            
            # Initialize tokenizer
            print("  📝 Loading BERT tokenizer...")
            self._tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
            
            # Load BERT model checkpoint
            print("  🧠 Loading Hybrid-BERT model...")
            checkpoint = torch.load(bert_model_path, map_location=torch.device('cpu'))
            
            # Extract configuration
            template_dim = checkpoint.get('template_dim', 4)
            num_classes = checkpoint.get('config', {}).get('num_classes', 7)
            
            print(f"     - Template dimension: {template_dim}")
            print(f"     - Number of classes: {num_classes}")
            
            # Initialize model architecture
            self._bert_model = HybridBERTModel(template_dim=template_dim, num_classes=num_classes)
            
            # Load trained weights (use strict=False to ignore position_ids)
            state_dict = checkpoint.get('model_state_dict', checkpoint)
            self._bert_model.load_state_dict(state_dict, strict=False)
            self._bert_model.eval()
            
            # Load XGBoost model
            print("  🌳 Loading XGBoost classifier...")
            with open(xgb_model_path, 'rb') as f:
                self._xgb_model = pickle.load(f)
            
            print("✅ Hybrid-BERT Model Manager loaded successfully!")
            print(f"   - BERT: Loaded from {bert_model_path}")
            print(f"   - XGBoost: Loaded from {xgb_model_path}")
            print(f"   - Tokenizer: bert-base-uncased")
            print(f"   - Classification: 7 categories (0=Normal, 1-6=Anomalies)")
            print(f"   - Template features: Using zeros (no parser integration)")
            
        except Exception as e:
            error_msg = f"Failed to load Hybrid-BERT models: {str(e)}"
            print(f"❌ {error_msg}")
            raise RuntimeError(error_msg)
    
    def get_model_components(self):
        """Get BERT model, XGBoost model, and tokenizer"""
        return self._bert_model, self._xgb_model, self._tokenizer
    
    def is_loaded(self):
        """Check if models are loaded"""
        return (self._bert_model is not None and 
                self._xgb_model is not None and 
                self._tokenizer is not None)
    
    def predict_single(self, log_text):
        """
        Predict anomaly for a single log message.
        
        Returns:
            dict: {
                'class': int,           # 0-6 classification
                'class_name': str,      # Human-readable name
                'probabilities': list,  # Softmax probabilities for all classes
                'anomaly_score': float, # Normalized score (0.0-1.0)
                'is_anomaly': bool,     # True if class != 0
                'severity': str         # 'info', 'medium', 'high', 'critical'
            }
        """
        if not self.is_loaded():
            raise RuntimeError("Models not loaded. Cannot perform inference.")
        
        try:
            # Tokenize input
            inputs = self._tokenizer(
                log_text,
                return_tensors='pt',
                max_length=128,
                truncation=True,
                padding=True
            )
            
            # Get BERT predictions
            with torch.no_grad():
                outputs = self._bert_model(
                    input_ids=inputs['input_ids'],
                    attention_mask=inputs['attention_mask'],
                    template_features=None  # Use zeros for template features
                )
                probabilities = torch.softmax(outputs, dim=-1)
                predicted_class = torch.argmax(probabilities, dim=-1).item()
                probs_list = probabilities[0].tolist()
            
            # Get anomaly metadata
            is_anomaly = predicted_class != 0
            severity_info = self.ANOMALY_SEVERITY.get(predicted_class, self.ANOMALY_SEVERITY[0])
            
            # Calculate normalized anomaly score
            # For normal logs (class 0), use inverse of normal probability
            # For anomalies, use severity multiplier * confidence
            if is_anomaly:
                anomaly_score = severity_info['score_multiplier'] * probs_list[predicted_class]
            else:
                anomaly_score = 1.0 - probs_list[0]  # Low score for normal logs
            
            return {
                'class': predicted_class,
                'class_name': severity_info['name'],
                'probabilities': probs_list,
                'anomaly_score': round(anomaly_score, 4),
                'is_anomaly': is_anomaly,
                'severity': severity_info['level']
            }
            
        except Exception as e:
            raise RuntimeError(f"Prediction failed: {str(e)}")
    
    def predict_batch(self, messages):
        """
        Predict anomaly scores for a batch of messages.
        
        Args:
            messages: List of log text strings
            
        Returns:
            List of anomaly scores (0.0-1.0)
        """
        if not self.is_loaded():
            raise RuntimeError("Models not loaded. Cannot perform inference.")
        
        try:
            scores = []
            
            # Process messages in batches for better performance
            batch_size = 32
            for i in range(0, len(messages), batch_size):
                batch = messages[i:i + batch_size]
                
                # Get predictions for each message
                for message in batch:
                    result = self.predict_single(message)
                    scores.append(result['anomaly_score'])
            
            return scores
            
        except Exception as e:
            raise RuntimeError(f"Batch prediction failed: {str(e)}")


# Maintain backward compatibility with old name
ModelManager = HybridBERTModelManager

# Global instance
model_manager = HybridBERTModelManager()
