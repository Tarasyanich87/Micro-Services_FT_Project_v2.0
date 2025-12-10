#!/usr/bin/env python3
"""
Create a test FreqAI model for testing purposes
"""

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.datasets import make_regression

# Create sample data
X, y = make_regression(n_samples=1000, n_features=20, noise=0.1, random_state=42)

# Train a simple model
model = RandomForestRegressor(n_estimators=10, random_state=42)
model.fit(X, y)

# Save the model
model_data = {
    "model": model,
    "features": [f"feature_{i}" for i in range(20)],
    "metadata": {
        "model_type": "RandomForestRegressor",
        "n_estimators": 10,
        "random_state": 42,
        "accuracy": 0.85,
        "features_count": 20,
    },
}

joblib.dump(model_data, "test_freqai_model.joblib")
print("✅ Test FreqAI model created: test_freqai_model.joblib")
