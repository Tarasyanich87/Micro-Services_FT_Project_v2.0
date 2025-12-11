import logging
import joblib
import numpy as np
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PredictionService:
    """Service for FreqAI model predictions"""

    def __init__(self, model_dir: str = "freqai_server/models"):
        # Use absolute path relative to project root
        project_root = Path(__file__).parent.parent.parent
        self.model_dir = project_root / model_dir
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self._model_cache = {}  # Cache loaded models

    async def load_model(self, model_name: str) -> Optional[Any]:
        """Load model from disk with caching"""
        if model_name in self._model_cache:
            return self._model_cache[model_name]

        model_path = self.model_dir / f"{model_name}.joblib"

        if not model_path.exists():
            logger.warning(f"Model {model_name} not found at {model_path}")
            return None

        try:
            model = joblib.load(model_path)
            self._model_cache[model_name] = model
            logger.info(f"Model {model_name} loaded and cached")
            return model
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            return None

    async def predict(
        self, model_name: str, features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make prediction using loaded model"""
        model = await self.load_model(model_name)

        if model is None:
            return {"error": "model_not_found"}

        try:
            # Prepare features for prediction
            feature_vector = self._prepare_features(features)

            # Make prediction
            if hasattr(model, "predict_proba"):
                # Classification with probabilities
                probabilities = model.predict_proba([feature_vector])[0]
                prediction = np.argmax(probabilities)

                result = {
                    "prediction": float(prediction),
                    "confidence": float(np.max(probabilities)),
                    "probabilities": probabilities.tolist(),
                }
            else:
                # Regression
                prediction = model.predict([feature_vector])[0]
                result = {
                    "prediction": float(prediction),
                    "confidence": 1.0,  # No confidence for regression
                }

            # Add feature importance if available
            if hasattr(model, "feature_importances_"):
                result["feature_importance"] = model.feature_importances_.tolist()

            return result

        except Exception as e:
            logger.error(f"Prediction failed for model {model_name}: {e}")
            return {"error": str(e)}

    def _prepare_features(self, features: Dict[str, Any]) -> List[float]:
        """Prepare features for model input"""
        # This should match the feature engineering in training
        # Implementation depends on your specific feature set

        feature_order = [
            "rsi",
            "macd",
            "macd_signal",
            "macd_hist",
            "bb_upper",
            "bb_middle",
            "bb_lower",
            "bb_width",
            "volume_mean",
            "price_change",
            "trend_strength",
        ]

        feature_vector = []
        for feature_name in feature_order:
            value = features.get(feature_name, 0.0)
            feature_vector.append(float(value))

        return feature_vector

    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a model"""
        model_path = self.model_dir / f"{model_name}.joblib"

        if not model_path.exists():
            return {"error": "model_not_found"}

        try:
            # Get file info
            stat = model_path.stat()

            # Load model to get metadata
            model = await self.load_model(model_name)

            info = {
                "name": model_name,
                "size_bytes": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "model_type": type(model).__name__,
            }

            # Add model-specific info
            if model is not None:
                if hasattr(model, "n_features_"):
                    info["n_features"] = model.n_features_

                if hasattr(model, "classes_"):
                    info["classes"] = model.classes_.tolist()

            return info

        except Exception as e:
            logger.error(f"Failed to get model info for {model_name}: {e}")
            return {"error": str(e)}

    async def unload_model(self, model_name: str):
        """Unload model from cache"""
        if model_name in self._model_cache:
            del self._model_cache[model_name]
            logger.info(f"Model {model_name} unloaded from cache")

    async def cleanup_cache(self, max_cache_size: int = 10):
        """Clean up model cache (LRU)"""
        if len(self._model_cache) > max_cache_size:
            # Remove oldest models (simple implementation)
            models_to_remove = list(self._model_cache.keys())[:-max_cache_size]
            for model_name in models_to_remove:
                await self.unload_model(model_name)

            logger.info(f"Cleaned up {len(models_to_remove)} models from cache")
