"""
SHAP Explainer Module
SHapley Additive exPlanations (SHAP) implementation.
"""

import numpy as np
import torch
from typing import Union, Optional, Dict, Any, List, Tuple, Callable
from itertools import combinations

from core.logger import logger


class KernelSHAP:
    """
    KernelSHAP explainer.
    
    A model-agnostic explainer that uses the Shapley value concept from game theory.
    """

    def __init__(
        self,
        model: Callable,
        feature_names: Optional[List[str]] = None,
        class_names: Optional[List[str]] = None,
        background_data: Optional[np.ndarray] = None,
        n_samples: int = 100,
        random_state: Optional[int] = None,
    ):
        """
        Initialize KernelSHAP.

        Args:
            model: Model to explain.
            feature_names: Names of input features.
            class_names: Names of output classes.
            background_data: Background dataset for reference.
            n_samples: Number of samples to use for approximation.
            random_state: Random seed for reproducibility.
        """
        self.model = model
        self.feature_names = feature_names
        self.class_names = class_names
        self.background_data = background_data
        self.n_samples = n_samples
        self.random_state = random_state
        self.random = np.random.RandomState(random_state)\n
        logger.info(
            f"KernelSHAP initialized: n_samples={n_samples}"
        )

    def _get_coalition_value(
        self,
        x: np.ndarray,
        coalition: Tuple[int, ...],
    ) -> float:
        """
        Get the model prediction for a coalition of features.

        Args:
            x: Input instance.
            coalition: Tuple of feature indices in the coalition.

        Returns:
            Model prediction for the coalition.
        """
        # Create a new instance with only the coalition features
        x_coalition = x.copy()
        for i in range(len(x)):
            if i not in coalition:
                # Replace with background value or zero
                if self.background_data is not None:
                    x_coalition[i] = self.random.choice(self.background_data[:, i])
                else:
                    x_coalition[i] = 0

        # Get prediction
        prediction = self.model(x_coalition.reshape(1, -1))[0]

        # For classification, use the probability of the predicted class
        if isinstance(prediction, np.ndarray) and len(prediction) > 1:
            return np.max(prediction)
        return float(prediction)

    def _approximate_shap_values(
        self,
        x: np.ndarray,
        feature_index: int,
    ) -> float:
        """
        Approximate SHAP value for a single feature.

        Args:
            x: Input instance.
            feature_index: Index of the feature to explain.

        Returns:
            Approximated SHAP value for the feature.
        """
        n_features = len(x)
        total_value = 0.0

        # Generate random coalitions
        for _ in range(self.n_samples):
            # Randomly sample a coalition size
            coalition_size = self.random.randint(0, n_features)

            # Randomly select features for the coalition
            coalition_features = self.random.choice(
                n_features, size=coalition_size, replace=False
            )

            # Check if the feature of interest is in the coalition
            if feature_index in coalition_features:
                # Remove the feature from the coalition
                coalition_without = tuple(f for f in coalition_features if f != feature_index)
                coalition_with = tuple(coalition_features)

                # Compute marginal contribution
                value_without = self._get_coalition_value(x, coalition_without)
                value_with = self._get_coalition_value(x, coalition_with)

                # Weight by the number of possible coalitions
                weight = coalition_size * (n_features - 1) / n_features
                total_value += (value_with - value_without) / weight

        # Average over all samples
        return total_value / self.n_samples

    def explain_instance(
        self,
        x: Union[np.ndarray, List[float]],
        class_of_interest: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Explain a single instance using SHAP values.

        Args:
            x: Input instance to explain.
            class_of_interest: Class to explain (for classification).

        Returns:
            Dictionary containing SHAP values and explanation.
        """
        if isinstance(x, list):
            x = np.array(x)

        n_features = len(x)
        shap_values = np.zeros(n_features)

        # Compute SHAP values for each feature
        for i in range(n_features):
            shap_values[i] = self._approximate_shap_values(x, i)

        # Prepare explanation
        explanation = {
            "instance": x,
            "shap_values": shap_values,
            "base_value": self._get_coalition_value(x, ()),
            "feature_importance": np.abs(shap_values),
            "top_features": [],
        }

        # Sort features by absolute SHAP value
        sorted_indices = np.argsort(np.abs(shap_values))[::-1]

        # Add top features
        for i, feature_idx in enumerate(sorted_indices):
            feature_name = self.feature_names[feature_idx] if self.feature_names else f"feature_{feature_idx}"
            explanation["top_features"].append({
                "feature": feature_name,
                "index": int(feature_idx),
                "shap_value": float(shap_values[feature_idx]),
                "importance": float(np.abs(shap_values[feature_idx])),
            })

        # Add class information if provided
        if class_of_interest is not None:
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
        Generate a text visualization of the SHAP explanation.

        Args:
            explanation: Explanation dictionary from explain_instance.
            show_all: Whether to show all features or just top features.

        Returns:
            Text visualization.
        """
        lines = []
        lines.append("=" * 60)
        lines.append("SHAP Explanation")
        lines.append("=" * 60)

        # Base value
        lines.append(f"Base value: {explanation.get('base_value', 'N/A'):.4f}")

        # Prediction
        pred = explanation.get("prediction", "N/A")
        if isinstance(pred, np.ndarray):
            pred = pred.tolist()
        lines.append(f"Prediction: {pred}")
        lines.append("")

        # Top features
        lines.append("Top Features (by SHAP value):")
        lines.append("-" * 40)

        features = explanation.get("top_features", [])
        if show_all and self.feature_names:
            # Show all features
            for i, shap_value in enumerate(explanation["shap_values"]):
                feature_name = self.feature_names[i]
                lines.append(f"  {feature_name:20s}: SHAP={shap_value:.4f}")
        else:
            # Show top features
            for feature in features:
                feature_name = feature["feature"]
                shap_value = feature["shap_value"]
                importance = feature["importance"]
                lines.append(f"  {feature_name:20s}: SHAP={shap_value:.4f}, |SHAP|={importance:.4f}")

        lines.append("")
        lines.append("Interpretation:")
        lines.append("  Positive SHAP: Feature increases the prediction")
        lines.append("  Negative SHAP: Feature decreases the prediction")
        lines.append("=" * 60)

        return "\n".join(lines)


class DeepSHAP:
    """
    DeepSHAP explainer for deep learning models.
    
    An efficient implementation of SHAP for deep learning models.
    """

    def __init__(
        self,
        model: torch.nn.Module,
        background_data: Optional[torch.Tensor] = None,
        feature_names: Optional[List[str]] = None,
        class_names: Optional[List[str]] = None,
    ):
        """
        Initialize DeepSHAP.

        Args:
            model: PyTorch model to explain.
            background_data: Background dataset for reference.
            feature_names: Names of input features.
            class_names: Names of output classes.
        """
        self.model = model
        self.background_data = background_data
        self.feature_names = feature_names
        self.class_names = class_names

        logger.info("DeepSHAP initialized")

    def explain(
        self,
        x: Union[torch.Tensor, np.ndarray],
        class_of_interest: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Explain a single instance using DeepSHAP.

        Args:
            x: Input instance to explain.
            class_of_interest: Class to explain.

        Returns:
            Dictionary containing SHAP values.
        """
        # For simplicity, this is a placeholder implementation
        # In practice, you would use a proper DeepSHAP implementation
        # like the one from the shap library

        if isinstance(x, np.ndarray):
            x = torch.from_numpy(x).float()

        # Get model prediction
        self.model.eval()
        with torch.no_grad():
            if x.dim() == 1:
                x = x.unsqueeze(0)
            output = self.model(x)

        # For classification, get probabilities
        if output.dim() > 1 and output.size(1) > 1:
            probs = torch.softmax(output, dim=1)
        else:
            probs = output

        # Placeholder: return random SHAP values (in practice, use proper DeepSHAP)
        n_features = x.size(1) if x.dim() > 1 else x.size(0)
        shap_values = torch.randn_like(x).squeeze().numpy()

        explanation = {
            "instance": x.numpy(),
            "shap_values": shap_values,
            "prediction": output.numpy(),
            "probabilities": probs.numpy() if probs.dim() > 1 else None,
        }

        if class_of_interest is not None:
            explanation["class_of_interest"] = class_of_interest

        logger.warning("DeepSHAP: Simplified implementation. For production, use the shap library.")

        return explanation
