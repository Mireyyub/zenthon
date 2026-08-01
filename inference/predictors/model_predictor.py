"""
Model Predictor Module
Provides utilities for making predictions with trained models.
"""

import os
import json
import numpy as np
import torch
from typing import Union, Optional, Dict, Any, List, Tuple
from PIL import Image
import cv2

from core.logger import logger
from core.config import config
from core.kernel import kernel


class ModelPredictor:
    """
    Universal predictor for trained models.
    
    Supports both scikit-learn style models and PyTorch models.
    """

    def __init__(
        self,
        model: Any,
        model_type: str = "pytorch",
        device: Optional[str] = None,
        preprocess_fn: Optional[Callable] = None,
        postprocess_fn: Optional[Callable] = None,
    ):
        """
        Initialize ModelPredictor.

        Args:
            model: Trained model.
            model_type: Type of model ('pytorch', 'sklearn', 'keras').
            device: Device to use for PyTorch models ('cpu' or 'cuda').
            preprocess_fn: Function to preprocess input data.
            postprocess_fn: Function to postprocess model output.
        """
        self.model = model
        self.model_type = model_type
        self.device = device or kernel.set_device()
        self.preprocess_fn = preprocess_fn
        self.postprocess_fn = postprocess_fn

        # Set device for PyTorch models
        if model_type == "pytorch" and hasattr(model, "to"):
            self.model.to(self.device)
            self.model.eval()

        logger.info(
            f"ModelPredictor initialized: model_type={model_type}, device={self.device}"
        )

    def predict(
        self,
        input_data: Union[np.ndarray, torch.Tensor, List, Dict, str],
        **kwargs,
    ) -> Any:
        """
        Make predictions with the model.

        Args:
            input_data: Input data for prediction.
            **kwargs: Additional arguments for preprocessing.

        Returns:
            Model predictions.
        """
        # Preprocess input
        if self.preprocess_fn is not None:
            input_data = self.preprocess_fn(input_data, **kwargs)

        # Make prediction based on model type
        if self.model_type == "pytorch":
            predictions = self._predict_pytorch(input_data)
        elif self.model_type == "sklearn":
            predictions = self._predict_sklearn(input_data)
        elif self.model_type == "keras":
            predictions = self._predict_keras(input_data)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

        # Postprocess output
        if self.postprocess_fn is not None:
            predictions = self.postprocess_fn(predictions)

        return predictions

    def _predict_pytorch(self, input_data: Union[np.ndarray, torch.Tensor]) -> Any:
        """Make predictions with PyTorch model."""
        # Convert to tensor if needed
        if isinstance(input_data, np.ndarray):
            input_data = torch.from_numpy(input_data).float()

        # Move to device
        input_data = input_data.to(self.device)

        # Make prediction
        with torch.no_grad():
            if hasattr(self.model, "output_size") and self.model.output_size > 1:
                # Classification: return probabilities and class indices
                outputs = self.model(input_data)
                probs = torch.softmax(outputs, dim=1)
                preds = torch.argmax(outputs, dim=1)
                return {
                    "logits": outputs.cpu().numpy(),
                    "probabilities": probs.cpu().numpy(),
                    "predictions": preds.cpu().numpy(),
                }
            else:
                # Regression: return raw outputs
                outputs = self.model(input_data)
                return outputs.cpu().numpy()

    def _predict_sklearn(self, input_data: Union[np.ndarray, List]) -> Any:
        """Make predictions with scikit-learn model."""
        if isinstance(input_data, list):
            input_data = np.array(input_data)

        if hasattr(self.model, "predict_proba"):
            # Classification: return probabilities and class indices
            probs = self.model.predict_proba(input_data)
            preds = self.model.predict(input_data)
            return {
                "probabilities": probs,
                "predictions": preds,
            }
        else:
            # Regression: return raw outputs
            return self.model.predict(input_data)

    def _predict_keras(self, input_data: Union[np.ndarray, List]) -> Any:
        """Make predictions with Keras model."""
        if isinstance(input_data, list):
            input_data = np.array(input_data)

        outputs = self.model.predict(input_data)
        if outputs.shape[1] > 1:
            # Classification
            return {
                "probabilities": outputs,
                "predictions": np.argmax(outputs, axis=1),
            }
        else:
            # Regression
            return outputs.flatten()

    def batch_predict(
        self,
        input_data: Union[np.ndarray, List],
        batch_size: int = 32,
        **kwargs,
    ) -> Any:
        """
        Make batch predictions for large datasets.

        Args:
            input_data: Input data for prediction.
            batch_size: Batch size for processing.
            **kwargs: Additional arguments for preprocessing.

        Returns:
            Model predictions.
        """
        if isinstance(input_data, list):
            input_data = np.array(input_data)

        predictions = []
        for i in range(0, len(input_data), batch_size):
            batch = input_data[i:i + batch_size]
            batch_pred = self.predict(batch, **kwargs)
            predictions.append(batch_pred)

        # Concatenate predictions
        if isinstance(batch_pred, dict):
            result = {}
            for key, value in batch_pred.items():
                if isinstance(value, np.ndarray):
                    result[key] = np.concatenate([p[key] for p in predictions], axis=0)
                else:
                    result[key] = predictions[0][key]
            return result
        else:
            return np.concatenate(predictions, axis=0)


class ImagePredictor(ModelPredictor):
    """
    Predictor for image classification models.
    """

    def __init__(
        self,
        model: Any,
        model_type: str = "pytorch",
        device: Optional[str] = None,
        input_size: Tuple[int, int] = (224, 224),
        normalize: bool = True,
        mean: List[float] = [0.485, 0.456, 0.406],
        std: List[float] = [0.229, 0.224, 0.225],
    ):
        """
        Initialize ImagePredictor.

        Args:
            model: Trained model.
            model_type: Type of model ('pytorch', 'keras').
            device: Device to use for PyTorch models.
            input_size: Expected input size (height, width).
            normalize: Whether to normalize the image.
            mean: Mean values for normalization.
            std: Standard deviation values for normalization.
        """
        self.input_size = input_size
        self.normalize = normalize
        self.mean = np.array(mean)
        self.std = np.array(std)

        super(ImagePredictor, self).__init__(
            model=model,
            model_type=model_type,
            device=device,
            preprocess_fn=self._preprocess_image,
        )

    def _preprocess_image(
        self,
        image: Union[str, np.ndarray, Image.Image],
        **kwargs,
    ) -> np.ndarray:
        """
        Preprocess an image for prediction.

        Args:
            image: Input image (file path, numpy array, or PIL Image).

        Returns:
            Preprocessed image as numpy array.
        """
        # Load image if it's a file path
        if isinstance(image, str):
            if not os.path.exists(image):
                raise FileNotFoundError(f"Image file not found: {image}")
            image = Image.open(image)

        # Convert to numpy array
        if isinstance(image, Image.Image):
            image = np.array(image)

        # Convert BGR to RGB if needed (OpenCV loads as BGR)
        if len(image.shape) == 3 and image.shape[2] == 3:
            if image.dtype == 'float32' and image.max() <= 1.0:
                # Already normalized
                pass
            else:
                # Convert to float and normalize to [0, 1]
                image = image.astype(np.float32) / 255.0

        # Convert grayscale to RGB if needed
        if len(image.shape) == 2:
            image = np.stack([image] * 3, axis=-1)
        elif image.shape[2] == 1:
            image = np.concatenate([image] * 3, axis=-1)

        # Resize image
        image = cv2.resize(image, (self.input_size[1], self.input_size[0]))

        # Normalize
        if self.normalize:
            image = (image - self.mean) / self.std

        # Add batch dimension and transpose to (1, C, H, W)
        image = np.transpose(image, (2, 0, 1))
        image = np.expand_dims(image, axis=0)

        return image

    def predict_image(
        self,
        image: Union[str, np.ndarray, Image.Image],
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Predict on a single image.

        Args:
            image: Input image (file path, numpy array, or PIL Image).

        Returns:
            Dictionary containing prediction results.
        """
        return self.predict(image, **kwargs)

    def predict_batch(
        self,
        images: List[Union[str, np.ndarray, Image.Image]],
        batch_size: int = 8,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Predict on a batch of images.

        Args:
            images: List of input images.
            batch_size: Batch size for processing.

        Returns:
            Dictionary containing prediction results for all images.
        """
        # Preprocess all images first
        preprocessed_images = []
        for image in images:
            preprocessed = self._preprocess_image(image, **kwargs)
            preprocessed_images.append(preprocessed)

        # Stack into a single batch
        batch = np.concatenate(preprocessed_images, axis=0)

        # Make prediction
        return self.predict(batch)


class TextPredictor(ModelPredictor):
    """
    Predictor for text classification models.
    """

    def __init__(
        self,
        model: Any,
        model_type: str = "pytorch",
        device: Optional[str] = None,
        tokenizer: Optional[Any] = None,
        max_length: int = 512,
    ):
        """
        Initialize TextPredictor.

        Args:
            model: Trained model.
            model_type: Type of model ('pytorch', 'sklearn').
            device: Device to use for PyTorch models.
            tokenizer: Tokenizer for text preprocessing.
            max_length: Maximum sequence length.
        """
        self.tokenizer = tokenizer
        self.max_length = max_length

        super(TextPredictor, self).__init__(
            model=model,
            model_type=model_type,
            device=device,
            preprocess_fn=self._preprocess_text,
        )

    def _preprocess_text(
        self,
        text: Union[str, List[str]],
        **kwargs,
    ) -> Any:
        """
        Preprocess text for prediction.

        Args:
            text: Input text or list of texts.

        Returns:
            Preprocessed text as model input.
        """
        if isinstance(text, str):
            text = [text]

        if self.tokenizer is not None:
            # Use tokenizer if available
            return self.tokenizer(
                text,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt",
            )
        else:
            # Simple preprocessing: convert to numerical features
            # This is a placeholder - in practice, you'd use proper text vectorization
            from sklearn.feature_extraction.text import TfidfVectorizer
            vectorizer = TfidfVectorizer()
            return vectorizer.fit_transform(text).toarray()

    def predict_text(
        self,
        text: Union[str, List[str]],
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Predict on text input.

        Args:
            text: Input text or list of texts.

        Returns:
            Dictionary containing prediction results.
        """
        return self.predict(text, **kwargs)
