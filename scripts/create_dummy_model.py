"""
Creates and saves a dummy scikit-learn model for FreqAI integration testing.
"""
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification
import os

def create_model():
    """Trains a simple classifier and saves it."""
    print("Generating dummy data...")
    X, y = make_classification(
        n_samples=100,
        n_features=10,
        n_informative=5,
        n_redundant=5,
        random_state=42
    )

    print("Training dummy model...")
    model = RandomForestClassifier(random_state=42)
    model.fit(X, y)

    model_path = os.path.join(os.path.dirname(__file__), '..', 'freqai_model.joblib')
    print(f"Saving model to {model_path}...")
    joblib.dump(model, model_path)
    print("Model saved successfully.")

if __name__ == "__main__":
    create_model()
