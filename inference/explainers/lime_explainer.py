"""
LIME Explainer Module
Local Interpretable Model-agnostic Explanations (LIME) implementation.
"""

import numpy as np
import torch
from typing import Union, Optional, Dict, Any, List, Tuple, Callable
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.utils import check_random_state

from core.logger import logger


class LIMEExplainer:
    """
    LIME (Local Interpretable Model-agnostic Explanations) explainer.
    
    Explains individual predictions by approximating the model locally with an interpretable model.
    """

    def __init__(
        self,
        model: Callable,
        feature_names: Optional[List[str]] = None,
        class_names: Optional[List[str]] = None,
        n_samples: int = 5000,
        kernel_width: float = 0.75,
        random_state: Optional[int] = None,
    ):
        """
        Initialize LIMEExplainer.

        Args:
            model: Model to explain (function that takes input and returns predictions).
            feature_names: Names of input features.
            class_names: Names of output classes.
            n_samples: Number of samples to generate for explanation.
            kernel_width: Width of the kernel for weighting samples.
            random_state: Random seed for reproducibility.
        """
        self.model = model
        self.feature_names = feature_names
        self.class_names = class_names
        self.n_samples = n_samples
        self.kernel_width = kernel_width
        self.random_state = random_state
        self.random = check_random_state(random_state)

        logger.info(
            f"LIMEExplainer initialized: n_samples={n_samples}, "
            f"kernel_width={kernel_width}"
        )

    def _generate_samples(
        self,
        x: np.ndarray,
        feature_selection: str = "auto",
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate perturbed samples around the input instance.

        Args:
            x: Input instance to explain.
            feature_selection: Method for selecting features to perturb.

        Returns:
            Tuple of (perturbed_samples, weights).
        """
        n_features = x.shape[0]

        if feature_selection == "auto":
            # Use all features
            features_to_sample = list(range(n_features))
        elif isinstance(feature_selection, list):
            features_to_sample = feature_selection
        else:
            raise ValueError(f"Unknown feature_selection: {feature_selection}")

        # Generate perturbed samples
        samples = np.zeros((self.n_samples, n_features))
        for i in range(self.n_samples):
            # Create a binary vector indicating which features to perturb
            z = self.random.binomial(1, 0.5, size=n_features)

            # Only perturb selected features
            for feature in features_to_sample:
                if z[feature] == 1:
                    # Sample from normal distribution centered at x[feature]
                    samples[i, feature] = self.random.normal(
                        loc=x[feature],
                        scale=np.std(x) * 0.1 if np.std(x) > 0 else 0.1,
                    )
                else:
                    samples[i, feature] = x[feature]

        # Compute weights using kernel
        distances = np.sqrt(np.sum((samples - x) ** 2, axis=1))
        weights = np.exp(-(distances ** 2) / (self.kernel_width ** 2))

        return samples, weights

    def _get_local_model(
        self,
        samples: np.ndarray,
        predictions: np.ndarray,
        weights: np.ndarray,
    ) -> Tuple[LinearRegression, float]:
        """
        Fit a local linear model to the perturbed samples.

        Args:
            samples: Perturbed samples.
            predictions: Model predictions on perturbed samples.
            weights: Weights for each sample.

        Returns:
            Tuple of (local_model, intercept).
        """
        # Standardize samples
        scaler = StandardScaler()
        samples_scaled = scaler.fit_transform(samples)

        # Fit weighted linear regression
        local_model = LinearRegression()
        local_model.fit(samples_scaled, predictions, sample_weight=weights)

        # Get intercept
        intercept = local_model.intercept_

        return local_model, intercept

    def explain_instance(
        self,
        x: Union[np.ndarray, List[float]],
        predict_fn: Optional[Callable] = None,
        top_labels: Optional[int] = None,
        num_features: int = 10,
    ) -> Dict[str, Any]:
        """
        Explain a single instance.

        Args:
            x: Input instance to explain.
            predict_fn: Function to get predictions (overrides self.model if provided).
            top_labels: Number of top labels to explain.
            num_features: Number of top features to return.

        Returns:
            Dictionary containing explanation.
        """
        if isinstance(x, list):
            x = np.array(x)

        # Use provided predict_fn or self.model
        if predict_fn is not None:
            model_fn = predict_fn
        else:
            model_fn = self.model

        # Generate perturbed samples
        samples, weights = self._generate_samples(x)

        # Get predictions for perturbed samples
        predictions = np.array([model_fn(sample.reshape(1, -1))[0] for sample in samples])

        # Fit local model
        local_model, intercept = self._get_local_model(samples, predictions, weights)

        # Get feature coefficients
        feature_coeffs = local_model.coef_

        # Sort features by absolute coefficient value
        feature_importance = np.abs(feature_coeffs)
        sorted_indices = np.argsort(feature_importance)[::-1]

        # Prepare explanation
        explanation = {
            "instance": x,
            "prediction": model_fn(x.reshape(1, -1))[0],
            "intercept": intercept,
            "feature_coefficients": feature_coeffs,
            "feature_importance": feature_importance,
            "top_features": [],
        }

        # Add top features
        for i in range(min(num_features, len(sorted_indices))):
            feature_idx = sorted_indices[i]
            feature_name = self.feature_names[feature_idx] if self.feature_names else f"feature_{feature_idx}"
            explanation["top_features"].append({
                "feature": feature_name,
                "index": int(feature_idx),
                "coefficient": float(feature_coeffs[feature_idx]),
                "importance": float(feature_importance[feature_idx]),
            })

        return explanation

    def explain_class(
        self,
        x: Union[np.ndarray, List[float]],
        class_of_interest: int,
        predict_proba_fn: Optional[Callable] = None,
        num_features: int = 10,
    ) -> Dict[str, Any]:
        """
        Explain the prediction for a specific class.

        Args:
            x: Input instance to explain.
            class_of_interest: Class to explain.
            predict_proba_fn: Function to get class probabilities.
            num_features: Number of top features to return.

        Returns:
            Dictionary containing explanation for the class.
        """
        if isinstance(x, list):
            x = np.array(x)

        if predict_proba_fn is None:
            raise ValueError("predict_proba_fn must be provided for class explanation")

        # Create a wrapper function that returns probabilities for the class of interest
        def class_predict_fn(input_data):
            probas = predict_proba_fn(input_data)
            return probas[:, class_of_interest]

        # Explain the instance for this class
        explanation = self.explain_instance(
            x,
            predict_fn=class_predict_fn,
            num_features=num_features,
        )

        # Add class information
        explanation["class_of_interest"] = class_of_interest
        if self.class_names:
            explanation["class_name"] = self.class_names[class_of_interest]

        return explanation

    def visualize_explanation(
        self,
        explanation: Dict[str, Any],
        show_all: bool = False,
    ) -> str:
        """
        Generate a text visualization of the explanation.

        Args:
            explanation: Explanation dictionary from explain_instance.
            show_all: Whether to show all features or just top features.

        Returns:
            Text visualization.
        """
        lines = []
        lines.append("=" * 60)
        lines.append("LIME Explanation")
        lines.append("=" * 60)

        # Prediction
        pred = explanation.get("prediction", "N/A")
        if isinstance(pred, np.ndarray):
            pred = pred.tolist()
        lines.append(f"Prediction: {pred}")

        # Intercept
        lines.append(f"Intercept: {explanation.get('intercept', 'N/A'):.4f}")
        lines.append("")

        # Top features
        lines.append("Top Features:")
        lines.append("-" * 40)

        features = explanation.get("top_features", [])
        if show_all and self.feature_names:
            # Show all features
            for i, (coef, importance) in enumerate(
                zip(explanation["feature_coefficients"], explanation["feature_importance"])
            ):
                feature_name = self.feature_names[i]
                lines.append(f"  {feature_name:20s}: coef={coef:.4f}, importance={importance:.4f}")
        else:
            # Show top features
            for feature in features:
                feature_name = feature["feature"]
                coef = feature["coefficient"]
                importance = feature["importance"]
                lines.append(f"  {feature_name:20s}: coef={coef:.4f}, importance={importance:.4f}")

        lines.append("=" * 60)

        return "\n".join(lines)


class LIMEImageExplainer:
    """
    LIME explainer for image classification models.
    """

    def __init__(
        self,
        model: Callable,
        n_samples: int = 5000,
        kernel_width: float = 0.75,
        random_state: Optional[int] = None,
    ):
        """
        Initialize LIMEImageExplainer.

        Args:
            model: Image classification model.
            n_samples: Number of samples to generate.
            kernel_width: Width of the kernel for weighting samples.
            random_state: Random seed for reproducibility.
        """
        self.model = model
        self.n_samples = n_samples
        self.kernel_width = kernel_width
        self.random = check_random_state(random_state)

    def explain_image(
        self,
        image: np.ndarray,
        predict_fn: Optional[Callable] = None,
        num_superpixels: int = 100,
        top_labels: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Explain an image classification prediction.

        Args:
            image: Input image (H, W, C).
            predict_fn: Function to get predictions (overrides self.model if provided).
            num_superpixels: Number of superpixels to use for segmentation.
            top_labels: Number of top labels to explain.

        Returns:
            Dictionary containing explanation.
        """
        # For simplicity, this is a placeholder implementation
        # In practice, you would use a proper image segmentation algorithm
        # like SLIC (Simple Linear Iterative Clustering)

        # Generate random superpixels (simplified)
        h, w, c = image.shape
        superpixel_indices = self.random.randint(0, num_superpixels, size=(h, w))

        # Create explanation (simplified)
        explanation = {
            "image_shape": (h, w, c),
            "num_superpixels": num_superpixels,
            "superpixel_weights": {},
        }

        logger.warning("LIMEImageExplainer: Simplified implementation. For production, use a proper image segmentation algorithm.")

        return explanation
