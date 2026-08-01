"""
Custom Loss Functions Module
Implements custom loss functions for various machine learning tasks.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple
import numpy as np

from core.logger import logger


class FocalLoss(nn.Module):
    """
    Focal Loss for imbalanced classification.
    
    As described in: "Focal Loss for Dense Object Detection" (Lin et al., 2017).
    
    FL(p_t) = -alpha_t * (1 - p_t)^gamma * log(p_t)
    """

    def __init__(
        self,
        alpha: Optional[torch.Tensor] = None,
        gamma: float = 2.0,
        reduction: str = "mean",
    ):
        """
        Initialize FocalLoss.

        Args:
            alpha: Weighting factor for each class. If None, all classes have weight 1.
            gamma: Focusing parameter.
            reduction: Specifies the reduction to apply to the output ('none', 'mean', 'sum').
        """
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction

        if isinstance(alpha, (float, int)):
            self.alpha = torch.Tensor([alpha, 1 - alpha])
        elif isinstance(alpha, list):
            self.alpha = torch.Tensor(alpha)

    def forward(self, inputs: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """
        Compute the focal loss.

        Args:
            inputs: Predicted probabilities (batch_size, num_classes) or logits.
            targets: Ground truth labels (batch_size,) or one-hot (batch_size, num_classes).

        Returns:
            Focal loss.
        """
        # Convert targets to one-hot if needed
        if targets.dim() == 1:
            targets = F.one_hot(targets.long(), num_classes=inputs.size(1)).float()

        # Convert inputs to probabilities if they are logits
        if inputs.size(1) > 1:
            p = F.softmax(inputs, dim=1)
        else:
            p = torch.sigmoid(inputs)

        # Compute p_t
        p_t = (p * targets) + ((1 - p) * (1 - targets))

        # Compute focal loss
        alpha_t = self.alpha[targets.long()] if self.alpha is not None else 1.0
        focal_loss = -alpha_t * (1 - p_t) ** self.gamma * torch.log(p_t + 1e-12)

        # Apply reduction
        if self.reduction == "mean":
            return focal_loss.mean()
        elif self.reduction == "sum":
            return focal_loss.sum()
        else:
            return focal_loss


class ContrastiveLoss(nn.Module):
    """
    Contrastive Loss for siamese networks.
    
    As described in: "Siamese Neural Networks for One-shot Image Recognition" (Koch et al., 2015).
    """

    def __init__(self, margin: float = 1.0):
        """
        Initialize ContrastiveLoss.

        Args:
            margin: Margin for the contrastive loss.
        """
        super(ContrastiveLoss, self).__init__()
        self.margin = margin

    def forward(
        self,
        output1: torch.Tensor,
        output2: torch.Tensor,
        label: torch.Tensor,
    ) -> torch.Tensor:
        """
        Compute the contrastive loss.

        Args:
            output1: Embedding of first sample.
            output2: Embedding of second sample.
            label: Label indicating whether the samples are similar (1) or dissimilar (0).

        Returns:
            Contrastive loss.
        """
        # Compute Euclidean distance
        euclidean_distance = F.pairwise_distance(output1, output2)

        # Compute contrastive loss
        loss_contrastive = torch.mean(
            (1 - label) * torch.pow(euclidean_distance, 2) +
            (label) * torch.pow(torch.clamp(self.margin - euclidean_distance, min=0.0), 2)
        )

        return loss_contrastive


class TripletLoss(nn.Module):
    """
    Triplet Loss for metric learning.
    
    As described in: "FaceNet: A Unified Embedding for Face Recognition and Clustering" (Schroff et al., 2015).
    """

    def __init__(self, margin: float = 1.0):
        """
        Initialize TripletLoss.

        Args:
            margin: Margin for the triplet loss.
        """
        super(TripletLoss, self).__init__()
        self.margin = margin

    def forward(
        self,
        anchor: torch.Tensor,
        positive: torch.Tensor,
        negative: torch.Tensor,
    ) -> torch.Tensor:
        """
        Compute the triplet loss.

        Args:
            anchor: Embedding of the anchor sample.
            positive: Embedding of the positive sample (same class as anchor).
            negative: Embedding of the negative sample (different class from anchor).

        Returns:
            Triplet loss.
        """
        # Compute distances
        pos_dist = F.pairwise_distance(anchor, positive)
        neg_dist = F.pairwise_distance(anchor, negative)

        # Compute triplet loss
        loss = torch.clamp(pos_dist - neg_dist + self.margin, min=0.0)
        return loss.mean()


class DiceLoss(nn.Module):
    """
    Dice Loss for segmentation tasks.
    
    As described in: "V-Net: Fully Convolutional Neural Networks for Volumetric Medical Image Segmentation" (Milletari et al., 2016).
    """

    def __init__(self, smooth: float = 1.0):
        """
        Initialize DiceLoss.

        Args:
            smooth: Smoothing factor to avoid division by zero.
        """
        super(DiceLoss, self).__init__()
        self.smooth = smooth

    def forward(self, inputs: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """
        Compute the Dice loss.

        Args:
            inputs: Predicted probabilities (batch_size, num_classes, *).
            targets: Ground truth labels (batch_size, num_classes, *).

        Returns:
            Dice loss.
        """
        # Flatten inputs and targets
        inputs = inputs.view(inputs.size(0), -1)
        targets = targets.view(targets.size(0), -1)

        # Compute intersection and union
        intersection = (inputs * targets).sum(dim=1)
        union = inputs.sum(dim=1) + targets.sum(dim=1)

        # Compute Dice coefficient
        dice = (2.0 * intersection + self.smooth) / (union + self.smooth)

        # Compute Dice loss
        dice_loss = 1.0 - dice.mean()

        return dice_loss


class LabelSmoothingLoss(nn.Module):
    """
    Label Smoothing Loss for classification.
    
    As described in: "Rethinking the Inception Architecture for Computer Vision" (Szegedy et al., 2016).
    """

    def __init__(self, smoothing: float = 0.1):
        """
        Initialize LabelSmoothingLoss.

        Args:
            smoothing: Smoothing factor (0 <= smoothing < 1).
        """
        super(LabelSmoothingLoss, self).__init__()
        self.smoothing = smoothing

    def forward(self, inputs: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """
        Compute the label smoothing loss.

        Args:
            inputs: Predicted logits (batch_size, num_classes).
            targets: Ground truth labels (batch_size,) or one-hot (batch_size, num_classes).

        Returns:
            Label smoothing loss.
        """
        # Convert targets to one-hot if needed
        if targets.dim() == 1:
            targets = F.one_hot(targets.long(), num_classes=inputs.size(1)).float()

        # Apply label smoothing
        targets = targets * (1.0 - self.smoothing) + \
                 (1.0 - targets) * self.smoothing / (inputs.size(1) - 1)

        # Compute cross-entropy loss
        log_probs = F.log_softmax(inputs, dim=1)
        loss = -torch.sum(targets * log_probs, dim=1)

        return loss.mean()


class LossFunctionFactory:
    """Factory for creating loss functions with common configurations."""

    @staticmethod
    def create_loss(
        loss_name: str,
        **kwargs,
    ) -> nn.Module:
        """
        Create a loss function.

        Args:
            loss_name: Name of the loss function.
            **kwargs: Additional arguments for the loss function.

        Returns:
            Loss function instance.
        """
        loss_name = loss_name.lower()

        if loss_name == "cross_entropy":
            return nn.CrossEntropyLoss(**kwargs)
        elif loss_name == "mse":
            return nn.MSELoss(**kwargs)
        elif loss_name == "bce":
            return nn.BCELoss(**kwargs)
        elif loss_name == "bce_with_logits":
            return nn.BCEWithLogitsLoss(**kwargs)
        elif loss_name == "focal":
            return FocalLoss(**kwargs)
        elif loss_name == "contrastive":
            return ContrastiveLoss(**kwargs)
        elif loss_name == "triplet":
            return TripletLoss(**kwargs)
        elif loss_name == "dice":
            return DiceLoss(**kwargs)
        elif loss_name == "label_smoothing":
            return LabelSmoothingLoss(**kwargs)
        else:
            raise ValueError(f"Unknown loss function: {loss_name}")
