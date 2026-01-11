"""
Anti-LLM Detection for Text Material
"""
import torch
import torch.nn as nn
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import numpy as np
from typing import Dict, List, Union, Optional
import pickle
import os
import json


class TextAuditor:
    """Detects AI-generated vs Human-written text"""
    
    def __init__(self, model_path: Optional[str] = None):
        if model_path is None:
            model_path = "./models/ai_detector"
        
        self.model_path = model_path
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.tokenizer = None
        self.is_synthetic = False
        self.load_model()
        
        # Dataset options
        self.dataset_sources = {
            'hc3': 'Hello-SimpleAI/HC3',
            'gpt2_output': 'GPT-2 Generated Text Dataset',
            'mgtbench': 'MGTBench (Contact authors)'
        }
    
    def load_model(self):
        """Load pre-trained AI detection model"""
        try:
            # Check if model directory exists
            if not os.path.exists(self.model_path):
                print(f"⚠️ Model not found at {self.model_path}")
                print("   Please train the model first.")
                print("   Run: python train_model.py")
                return
            
            # Check if it's a synthetic model
            config_path = os.path.join(self.model_path, "config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.is_synthetic = config.get("is_synthetic", False)
            
            print(f"⏳ Loading model from {self.model_path}...")
            self.tokenizer = DistilBertTokenizer.from_pretrained(self.model_path)
            self.model = DistilBertForSequenceClassification.from_pretrained(self.model_path)
            self.model.to(self.device)
            self.model.eval()  # Set to evaluation mode
            
            if self.is_synthetic:
                print("⚠️ Loaded synthetic model (accuracy may be low)")
                print("   Train with real data for production use.")
            else:
                print(f"✅ Text Auditor Model loaded successfully!")
                
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            print("\n💡 Solutions:")
            print("1. Train the model: python train_model.py")
            print("2. Check if model files exist in ./models/ai_detector/")
            print("3. Verify model files: pytorch_model.bin, config.json, vocab.txt")
    
    def analyze_text(self, text: str) -> Dict:
        """Analyze text for AI generation probability"""
        if not self.model or not self.tokenizer:
            return {
                "error": "Model not loaded",
                "verdict": "Model Error",
                "ai_confidence": 0,
                "human_confidence": 0,
                "is_ai_generated": False,
                "details": {
                    "error": "Please train the model first (run train_model.py)",
                    "model_loaded": False
                }
            }
        
        try:
            # Tokenize
            inputs = self.tokenizer(
                text, 
                return_tensors="pt", 
                truncation=True, 
                max_length=512,
                padding=True
            ).to(self.device)
            
            # Predict
            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = torch.softmax(outputs.logits, dim=1)
            
            # Get results
            ai_prob = probs[0][1].item() * 100
            human_prob = probs[0][0].item() * 100
            
            verdict = "🤖 AI-Generated" if ai_prob > 50 else "👤 Human-Written"
            
            if self.is_synthetic:
                verdict += " (Synthetic Model)"
            
            return {
                "is_ai_generated": ai_prob > 50,
                "ai_confidence": ai_prob,
                "human_confidence": human_prob,
                "verdict": verdict,
                "details": {
                    "model_used": "DistilBERT",
                    "model_type": "Synthetic" if self.is_synthetic else "Fine-tuned",
                    "dataset_trained_on": "HC3 Corpus" if not self.is_synthetic else "Synthetic",
                    "threshold": 50,
                    "warning": "Low accuracy" if self.is_synthetic else None
                }
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "verdict": "Analysis Error",
                "ai_confidence": 0,
                "human_confidence": 0,
                "is_ai_generated": False
            }
    
    def batch_analyze(self, texts: List[str]) -> List[Dict]:
        """Analyze multiple texts"""
        return [self.analyze_text(text) for text in texts]
    
    def get_detection_report(self, text: str) -> str:
        """Generate detailed report"""
        analysis = self.analyze_text(text)
        
        if "error" in analysis:
            return f"""
            ❌ ERROR IN ANALYSIS
            {'='*40}
            Error: {analysis['error']}
            {'='*40}
            Please train the model first:
            python train_model.py
            """
        
        report = f"""
        📝 TEXT INTEGRITY REPORT
        {'='*40}
        Verdict: {analysis['verdict']}
        AI Confidence: {analysis['ai_confidence']:.2f}%
        Human Confidence: {analysis['human_confidence']:.2f}%
        {'='*40}
        Text Sample: {text[:100]}...
        {'='*40}
        Model Info: {analysis['details']['model_type']} Model
        Dataset: {analysis['details']['dataset_trained_on']}
        {'='*40}
        """
        
        if analysis['details'].get('warning'):
            report += f"⚠️  Note: {analysis['details']['warning']}\n"
        
        return report