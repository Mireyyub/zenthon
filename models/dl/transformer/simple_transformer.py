"""
Simple Transformer Model
Transformer implementation for sequence processing tasks.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, List, Tuple
import math

from core.logger import logger


class PositionalEncoding(nn.Module):
    """
    Positional Encoding for Transformer models.
    
    Adds positional information to input embeddings.
    """

    def __init__(self, d_model: int, max_len: int = 5000):
        """
        Initialize PositionalEncoding.

        Args:
            d_model: Dimension of the model.
            max_len: Maximum sequence length.
        """
        super(PositionalEncoding, self).__init__()
        self.d_model = d_model

        # Create positional encoding matrix
        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model))
        pe = torch.zeros(max_len, d_model)
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Add positional encoding to input.

        Args:
            x: Input tensor (batch_size, seq_len, d_model).

        Returns:
            Output tensor with positional encoding.
        """
        return x + self.pe[:, :x.size(1)]


class MultiHeadAttention(nn.Module):
    """
    Multi-Head Attention layer.
    
    Implements scaled dot-product attention with multiple heads.
    """

    def __init__(
        self,
        d_model: int,
        num_heads: int = 8,
        dropout: float = 0.1,
    ):
        """
        Initialize MultiHeadAttention.

        Args:
            d_model: Dimension of the model.
            num_heads: Number of attention heads.
            dropout: Dropout rate.
        """
        super(MultiHeadAttention, self).__init__()
        assert d_model % num_heads == 0, "d_model must be divisible by num_heads"

        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads

        # Linear layers for Q, K, V
        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)

        # Output linear layer
        self.W_o = nn.Linear(d_model, d_model)

        # Dropout layer
        self.dropout = nn.Dropout(dropout)

        # Scale factor
        self.scale = torch.sqrt(torch.FloatTensor([self.d_k]))

    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Forward pass of multi-head attention.

        Args:
            query: Query tensor (batch_size, seq_len, d_model).
            key: Key tensor (batch_size, seq_len, d_model).
            value: Value tensor (batch_size, seq_len, d_model).
            mask: Optional mask tensor.

        Returns:
            Output tensor (batch_size, seq_len, d_model).
        """
        batch_size = query.size(0)

        # Linear projections
        Q = self.W_q(query).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        K = self.W_k(key).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        V = self.W_v(value).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)

        # Scaled dot-product attention
        scores = torch.matmul(Q, K.transpose(-2, -1)) / self.scale.to(query.device)

        # Apply mask if provided
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)

        # Softmax
        attention = F.softmax(scores, dim=-1)
        attention = self.dropout(attention)

        # Apply attention to values
        output = torch.matmul(attention, V)

        # Concatenate heads
        output = output.transpose(1, 2).contiguous().view(
            batch_size, -1, self.d_model
        )

        # Output linear layer
        output = self.W_o(output)

        return output


class TransformerBlock(nn.Module):
    """
    Transformer Block.
    
    Contains multi-head attention and feed-forward network with residual connections.
    """

    def __init__(
        self,
        d_model: int,
        num_heads: int = 8,
        ff_dim: int = 2048,
        dropout: float = 0.1,
    ):
        """
        Initialize TransformerBlock.

        Args:
            d_model: Dimension of the model.
            num_heads: Number of attention heads.
            ff_dim: Dimension of feed-forward network.
            dropout: Dropout rate.
        """
        super(TransformerBlock, self).__init__()
        self.d_model = d_model

        # Multi-head attention
        self.attention = MultiHeadAttention(d_model, num_heads, dropout)

        # Layer normalization
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)

        # Feed-forward network
        self.ffn = nn.Sequential(
            nn.Linear(d_model, ff_dim),
            nn.ReLU(),
            nn.Linear(ff_dim, d_model),
        )

        # Dropout layers
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Forward pass of transformer block.

        Args:
            x: Input tensor (batch_size, seq_len, d_model).
            mask: Optional mask tensor.

        Returns:
            Output tensor (batch_size, seq_len, d_model).
        """
        # Multi-head attention with residual connection
        attn_output = self.attention(x, x, x, mask)
        x = x + self.dropout1(attn_output)
        x = self.norm1(x)

        # Feed-forward network with residual connection
        ffn_output = self.ffn(x)
        x = x + self.dropout2(ffn_output)
        x = self.norm2(x)

        return x


class SimpleTransformer(nn.Module):
    """
    Simple Transformer Model.
    
    A basic transformer model for sequence processing tasks.
    """

    def __init__(
        self,
        vocab_size: int,
        d_model: int = 512,
        num_heads: int = 8,
        num_layers: int = 6,
        ff_dim: int = 2048,
        max_len: int = 5000,
        dropout: float = 0.1,
        num_classes: Optional[int] = None,
    ):
        """
        Initialize SimpleTransformer.

        Args:
            vocab_size: Size of vocabulary.
            d_model: Dimension of the model.
            num_heads: Number of attention heads.
            num_layers: Number of transformer layers.
            ff_dim: Dimension of feed-forward network.
            max_len: Maximum sequence length.
            dropout: Dropout rate.
            num_classes: Number of output classes (for classification).
        """
        super(SimpleTransformer, self).__init__()
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.num_heads = num_heads
        self.num_layers = num_layers
        self.ff_dim = ff_dim
        self.max_len = max_len
        self.dropout = dropout
        self.num_classes = num_classes

        # Embedding layer
        self.embedding = nn.Embedding(vocab_size, d_model)

        # Positional encoding
        self.pos_encoding = PositionalEncoding(d_model, max_len)

        # Dropout layer
        self.emb_dropout = nn.Dropout(dropout)

        # Transformer layers
        self.transformer_layers = nn.ModuleList([
            TransformerBlock(d_model, num_heads, ff_dim, dropout)
            for _ in range(num_layers)
        ])

        # Output layer (for classification)
        if num_classes is not None:
            self.output_layer = nn.Linear(d_model, num_classes)

        logger.info(
            f"SimpleTransformer initialized: vocab={vocab_size}, d_model={d_model}, "
            f"heads={num_heads}, layers={num_layers}, ff_dim={ff_dim}, "
            f"max_len={max_len}, dropout={dropout}"
        )

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Forward pass of the transformer.

        Args:
            x: Input tensor (batch_size, seq_len).
            mask: Optional mask tensor.

        Returns:
            Output tensor.
        """
        # Embedding
        x = self.embedding(x)
        x = self.pos_encoding(x)
        x = self.emb_dropout(x)

        # Transformer layers
        for layer in self.transformer_layers:
            x = layer(x, mask)

        # For classification, use the first token's output
        if self.num_classes is not None:
            x = x[:, 0, :]  # Take the first token
            x = self.output_layer(x)

        return x


class TransformerFactory:
    """Factory for creating Transformer models with common configurations."""

    @staticmethod
    def create_text_classifier(
        vocab_size: int,
        d_model: int = 256,
        num_heads: int = 8,
        num_layers: int = 4,
        num_classes: int = 2,
    ) -> SimpleTransformer:
        """
        Create a Transformer for text classification.

        Args:
            vocab_size: Size of vocabulary.
            d_model: Dimension of the model.
            num_heads: Number of attention heads.
            num_layers: Number of transformer layers.
            num_classes: Number of classes.

        Returns:
            SimpleTransformer model for text classification.
        """
        return SimpleTransformer(
            vocab_size=vocab_size,
            d_model=d_model,
            num_heads=num_heads,
            num_layers=num_layers,
            num_classes=num_classes,
        )

    @staticmethod
    def create_language_model(
        vocab_size: int,
        d_model: int = 512,
        num_heads: int = 8,
        num_layers: int = 6,
    ) -> SimpleTransformer:
        """
        Create a Transformer for language modeling.

        Args:
            vocab_size: Size of vocabulary.
            d_model: Dimension of the model.
            num_heads: Number of attention heads.
            num_layers: Number of transformer layers.

        Returns:
            SimpleTransformer model for language modeling.
        """
        return SimpleTransformer(
            vocab_size=vocab_size,
            d_model=d_model,
            num_heads=num_heads,
            num_layers=num_layers,
            num_classes=vocab_size,  # Output size equals vocab size for LM
        )
