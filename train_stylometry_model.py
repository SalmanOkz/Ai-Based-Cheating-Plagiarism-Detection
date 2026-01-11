"""
Train Stylometry Model for Author Identification
Uses PAN-style features
"""
from integrity_auditor.stylometry import StylometryAnalyzer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import numpy as np
import joblib
import os

class StylometryTrainer:
    """Train stylometry model"""
    
    def __init__(self, model_save_path='models/stylometry_model.pkl'):
        self.model_save_path = model_save_path
        self.analyzer = StylometryAnalyzer()
        self.model = None
        
    def create_sample_dataset(self):
        """
        Create sample dataset with different writing styles
        In production, use PAN at CLEF dataset
        """
        print("📝 Creating sample dataset...")
        
        # Sample texts from different "authors"
        # In real scenario, load from PAN dataset
        samples = {
            'Author_A': [
                "Hey! What's up? I'm totally loving this new game. It's super fun and the graphics are awesome. Can't wait to play more!",
                "OMG, did you see that movie? I was literally crying at the end. So emotional! Best film ever, hands down.",
                "Yo, check out this cool website I found. It's got tons of free resources. You should totally bookmark it!"
            ],
            'Author_B': [
                "The implementation of this algorithm demonstrates significant computational efficiency. The time complexity is O(n log n), which is optimal for this class of problems.",
                "Furthermore, the empirical results validate our theoretical predictions. The observed performance metrics align closely with the expected values.",
                "In conclusion, the proposed methodology exhibits superior characteristics when compared to existing approaches in the literature."
            ],
            'Author_C': [
                "I think that maybe we could consider this option. Perhaps it would be beneficial to explore alternative solutions as well.",
                "It seems like a good idea, but I'm not entirely certain. We might want to discuss this further before making a decision.",
                "Personally, I would probably suggest taking a more cautious approach. However, I understand if others have different perspectives."
            ]
        }
        
        texts = []
        authors = []
        
        for author, author_texts in samples.items():
            for text in author_texts:
                texts.append(text)
                authors.append(author)
        
        print(f"✅ Created {len(texts)} samples from {len(samples)} authors")
        return texts, authors
    
    def extract_features_batch(self, texts):
        """Extract features from multiple texts"""
        print("🔧 Extracting features...")
        
        features = []
        for text in texts:
            feature_dict = self.analyzer.extract_features(text)
            # Convert dict to feature vector
            feature_vector = list(feature_dict.values())
            features.append(feature_vector)
        
        return np.array(features)
    
    def train(self, texts, authors):
        """Train stylometry model"""
        print("🚀 Training model...")
        
        # Extract features
        X = self.extract_features_batch(texts)
        y = np.array(authors)
        
        # Split dataset
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y
        )
        
        # Train Random Forest
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
        print("⏳ Training in progress...")
        self.model.fit(X_train, y_train)
        
        # Evaluate
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)
        
        y_pred = self.model.predict(X_test)
        
        print("\n" + "="*50)
        print("RESULTS:")
        print("="*50)
        print(f"Training Accuracy: {train_score:.3f}")
        print(f"Testing Accuracy: {test_score:.3f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        print("="*50 + "\n")
        
        return self.model
    
    def save_model(self):
        """Save trained model"""
        print(f"💾 Saving model to {self.model_save_path}...")
        
        os.makedirs(os.path.dirname(self.model_save_path), exist_ok=True)
        
        model_data = {
            'model': self.model,
            'feature_names': list(self.analyzer.extract_features("test").keys())
        }
        
        joblib.dump(model_data, self.model_save_path)
        print("✅ Model saved successfully!")
    
    def test_model(self):
        """Test the trained model"""
        print("\n🧪 Testing model...")
        
        test_texts = [
            "Hey, what's going on? This is so cool!",
            "The algorithmic complexity demonstrates optimal performance characteristics.",
            "I think maybe we should probably consider this option carefully."
        ]
        
        for i, text in enumerate(test_texts):
            features = self.analyzer.extract_features(text)
            feature_vector = np.array([list(features.values())])
            
            prediction = self.model.predict(feature_vector)[0]
            proba = self.model.predict_proba(feature_vector)[0]
            
            print(f"\nTest {i+1}:")
            print(f"Text: {text[:50]}...")
            print(f"Predicted Author: {prediction}")
            print(f"Confidence: {max(proba):.2%}")


def main():
    """Main training pipeline"""
    print("="*50)
    print("STYLOMETRY MODEL TRAINING")
    print("="*50)
    print("NOTE: This is a demo with sample data.")
    print("For production, use PAN at CLEF dataset.")
    print("="*50 + "\n")
    
    trainer = StylometryTrainer()
    
    # Create dataset
    texts, authors = trainer.create_sample_dataset()
    
    # Train
    trainer.train(texts, authors)
    
    # Save
    trainer.save_model()
    
    # Test
    trainer.test_model()
    
    print("\n✅ TRAINING COMPLETE!")


if __name__ == "__main__":
    main()