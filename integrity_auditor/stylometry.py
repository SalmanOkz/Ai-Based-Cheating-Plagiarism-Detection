"""
Stylometry Analysis for Author Identification
Based on PAN/CLEF datasets methodology
"""
import re
import numpy as np
from collections import Counter
from typing import Dict, List, Optional
import os


class StylometryAnalyzer:
    """Analyzes writing style for author identification"""
    
    def __init__(self, model_path: Optional[str] = None):
        if model_path is None:
            model_path = "./models/stylometry_model.pkl"
        
        self.model_path = model_path
        self.model = None
        self.author_profiles = {}
        
        print("📝 Stylometry Analyzer Initialized")
        print("   Note: Model needs to be trained with author data")
    
    def extract_features(self, text: str) -> Dict:
        """Extract stylometric features from text (simplified version)"""
        features = {}
        
        # Clean text
        text = str(text).strip()
        
        # Basic text statistics
        features['char_count'] = len(text)
        features['word_count'] = len(text.split())
        
        # Simple sentence counting (count punctuation)
        features['sentence_count'] = text.count('.') + text.count('!') + text.count('?')
        if features['sentence_count'] == 0:
            features['sentence_count'] = 1  # Avoid division by zero
        
        # Average word length
        words = text.split()
        if words:
            features['avg_word_length'] = sum(len(word) for word in words) / len(words)
        else:
            features['avg_word_length'] = 0
        
        # Punctuation frequency
        features['comma_freq'] = text.count(',') / max(len(text), 1) * 1000
        features['period_freq'] = text.count('.') / max(len(text), 1) * 1000
        features['question_freq'] = text.count('?') / max(len(text), 1) * 1000
        features['exclamation_freq'] = text.count('!') / max(len(text), 1) * 1000
        
        # Word length distribution
        word_lengths = [len(word) for word in words]
        for i in range(1, 11):
            count = word_lengths.count(i)
            features[f'words_len_{i}'] = (count / len(word_lengths) * 100) if word_lengths else 0
        
        # Vocabulary richness (type-token ratio)
        unique_words = set(words)
        features['vocab_richness'] = (len(unique_words) / len(words) * 100) if words else 0
        
        # Common word frequencies
        common_words = ['the', 'and', 'to', 'of', 'a', 'in', 'that', 'it', 'is', 'was']
        text_lower = text.lower()
        for word in common_words:
            features[f'common_{word}'] = text_lower.count(word) / max(len(words), 1) * 100
        
        return features
    
    def train(self, texts: List[str], authors: List[str]) -> bool:
        """Train author identification model (simplified)"""
        if len(texts) != len(authors):
            print("❌ Error: Number of texts must match number of authors")
            return False
        
        if len(texts) < 5:
            print("⚠️ Warning: Very few samples for training")
        
        print(f"Training stylometry model on {len(texts)} documents...")
        
        # In a real implementation, you would:
        # 1. Extract features for each text
        # 2. Train a classifier (SVM, Random Forest, etc.)
        # 3. Save the model
        
        print("⚠️ Note: Training not implemented in this demo version")
        print("   For production, implement proper ML training")
        
        # Create a placeholder model file
        try:
            import joblib
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            # Create a simple dummy model
            dummy_model = {
                'trained': True,
                'num_samples': len(texts),
                'authors': list(set(authors)),
                'note': 'This is a placeholder model. Implement proper training.'
            }
            
            joblib.dump(dummy_model, self.model_path)
            print(f"✅ Placeholder model saved to {self.model_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save model: {e}")
            return False
    
    def predict_author(self, text: str) -> Dict:
        """Predict author of given text (demo version)"""
        # Check if model exists
        if not os.path.exists(self.model_path):
            return {
                "error": "Model not trained",
                "message": "Please train the model first with author data",
                "suggestion": "Collect writing samples from different authors and call train() method"
            }
        
        # Extract features
        features = self.extract_features(text)
        
        # Demo prediction (random for now)
        # In production, this would use the trained model
        import random
        demo_authors = ["Author_A", "Author_B", "Author_C", "Unknown"]
        
        return {
            "predicted_author": random.choice(demo_authors),
            "confidence": random.uniform(50, 90),
            "features_extracted": len(features),
            "note": "This is a demo prediction. Train with real data for accurate results.",
            "sample_features": {
                "word_count": features.get('word_count', 0),
                "vocab_richness": f"{features.get('vocab_richness', 0):.1f}%",
                "avg_word_length": f"{features.get('avg_word_length', 0):.2f}"
            }
        }
    
    def analyze_writing_style(self, text: str) -> str:
        """Generate writing style analysis report"""
        features = self.extract_features(text)
        
        # Determine writing style characteristics
        style_notes = []
        
        if features['avg_word_length'] > 6:
            style_notes.append("Uses longer words (academic/formal)")
        elif features['avg_word_length'] < 4:
            style_notes.append("Uses shorter words (conversational)")
        
        if features['vocab_richness'] > 70:
            style_notes.append("Rich vocabulary (diverse word choice)")
        elif features['vocab_richness'] < 30:
            style_notes.append("Simple vocabulary (repetitive word choice)")
        
        if features['sentence_count'] > 0:
            avg_sent_length = features['word_count'] / features['sentence_count']
            if avg_sent_length > 20:
                style_notes.append("Long sentences (complex structure)")
            elif avg_sent_length < 10:
                style_notes.append("Short sentences (simple structure)")
        
        report = f"""
        📊 WRITING STYLE ANALYSIS
        {'='*40}
        📝 Text Statistics:
          Characters: {features['char_count']}
          Words: {features['word_count']}
          Sentences: {features['sentence_count']}
          Avg Word Length: {features['avg_word_length']:.2f}
          Vocabulary Richness: {features['vocab_richness']:.1f}%
        {'='*40}
        🔍 Style Characteristics:
          {', '.join(style_notes) if style_notes else 'Neutral writing style'}
        {'='*40}
        📈 Punctuation (per 1000 chars):
          Commas: {features['comma_freq']:.1f}
          Periods: {features['period_freq']:.1f}
          Questions: {features['question_freq']:.1f}
          Exclamations: {features['exclamation_freq']:.1f}
        {'='*40}
        💡 Note: For author identification, collect writing samples
              from different authors and train the model.
        """
        
        return report