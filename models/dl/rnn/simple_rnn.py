"""
Simple RNN Model
Recurrent Neural Network implementation for sequence processing.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, List, Tuple

from core.logger import logger


class SimpleRNN(nn.Module):
    """
    Simple Recurrent Neural Network for sequence processing.
    
    Can be used for tasks like time series prediction, text generation, etc.
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        output_size: int,
        num_layers: int = 1,
        rnn_type: str = "lstm",
        dropout: float = 0.0,
        bidirectional: bool = False,
    ):
        """
        Initialize SimpleRNN.

        Args:
            input_size: Size of input features.
            hidden_size: Size of hidden state.
            output_size: Size of output.
            num_layers: Number of RNN layers.
            rnn_type: Type of RNN ('rnn', 'lstm', 'gru').
            dropout: Dropout rate (applied between layers if num_layers > 1).
            bidirectional: Whether to use bidirectional RNN.
        """
        super(SimpleRNN, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.num_layers = num_layers
        self.rnn_type = rnn_type
        self.dropout = dropout
        self.bidirectional = bidirectional

        # Create RNN layer
        self.rnn = self._create_rnn_layer()

        # Fully connected layer
        self.fc = nn.Linear(
            hidden_size * (2 if bidirectional else 1),
            output_size
        )

        # Dropout layer
        self.dropout_layer = nn.Dropout(dropout)

        # Initialize weights
        self._initialize_weights()

        logger.info(
            f"SimpleRNN initialized: input={input_size}, hidden={hidden_size}, "
            f"output={output_size}, layers={num_layers}, type={rnn_type}, "
            f"bidirectional={bidirectional}, dropout={dropout}"
        )

    def _create_rnn_layer(self) -> nn.Module:
        """Create the appropriate RNN layer based on rnn_type."""
        if self.rnn_type == "rnn":
            return nn.RNN(
                input_size=self.input_size,
                hidden_size=self.hidden_size,
                num_layers=self.num_layers,
                dropout=self.dropout if self.num_layers > 1 else 0.0,
                bidirectional=self.bidirectional,
                batch_first=True,
            )
        elif self.rnn_type == "lstm":
            return nn.LSTM(
                input_size=self.input_size,
                hidden_size=self.hidden_size,
                num_layers=self.num_layers,
                dropout=self.dropout if self.num_layers > 1 else 0.0,
                bidirectional=self.bidirectional,
                batch_first=True,
            )
        elif self.rnn_type == "gru":
            return nn.GRU(
                input_size=self.input_size,
                hidden_size=self.hidden_size,
                num_layers=self.num_layers,
                dropout=self.dropout if self.num_layers > 1 else 0.0,
                bidirectional=self.bidirectional,
                batch_first=True,
            )
        else:
            raise ValueError(f"Unknown RNN type: {self.rnn_type}")

    def _initialize_weights(self) -> None:
        """Initialize weights using Xavier initialization."""
        for name, param in self.rnn.named_parameters():
            if 'weight' in name:
                nn.init.xavier_uniform_(param)
            elif 'bias' in name:
                nn.init.zeros_(param)

        nn.init.xavier_uniform_(self.fc.weight)
        nn.init.zeros_(self.fc.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass of the network.

        Args:
            x: Input tensor (batch_size, seq_len, input_size).

        Returns:
            Output tensor (batch_size, output_size).
        """
        # RNN layer
        rnn_out, _ = self.rnn(x)

        # Apply dropout
        rnn_out = self.dropout_layer(rnn_out)

        # Get the last time step's output
        last_out = rnn_out[:, -1, :]

        # Fully connected layer
        out = self.fc(last_out)

        return out


class Seq2SeqRNN(nn.Module):
    """
    Sequence-to-Sequence RNN for tasks like machine translation.
    
    Uses an encoder-decoder architecture with attention.
    """

    def __init__(
        self,
        encoder_input_size: int,
        decoder_input_size: int,
        hidden_size: int,
        output_size: int,
        num_layers: int = 1,
        rnn_type: str = "lstm",
        dropout: float = 0.0,
        use_attention: bool = False,
    ):
        """
        Initialize Seq2SeqRNN.

        Args:
            encoder_input_size: Input size for encoder.
            decoder_input_size: Input size for decoder.
            hidden_size: Hidden state size.
            output_size: Output size.
            num_layers: Number of RNN layers.
            rnn_type: Type of RNN ('rnn', 'lstm', 'gru').
            dropout: Dropout rate.
            use_attention: Whether to use attention mechanism.
        """
        super(Seq2SeqRNN, self).__init__()
        self.encoder_input_size = encoder_input_size
        self.decoder_input_size = decoder_input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.num_layers = num_layers
        self.rnn_type = rnn_type
        self.dropout = dropout
        self.use_attention = use_attention

        # Encoder
        self.encoder = self._create_rnn_layer(
            encoder_input_size, hidden_size, num_layers, rnn_type, dropout, False
        )

        # Decoder
        self.decoder = self._create_rnn_layer(
            decoder_input_size, hidden_size, num_layers, rnn_type, dropout, False
        )

        # Attention layer
        if use_attention:
            self.attention = nn.Linear(hidden_size * 2, hidden_size)
            self.attention_v = nn.Linear(hidden_size, 1, bias=False)

        # Fully connected layer
        self.fc = nn.Linear(hidden_size, output_size)

        # Dropout layer
        self.dropout_layer = nn.Dropout(dropout)

        logger.info(
            f"Seq2SeqRNN initialized: enc_in={encoder_input_size}, dec_in={decoder_input_size}, "
            f"hidden={hidden_size}, output={output_size}, layers={num_layers}, "
            f"type={rnn_type}, attention={use_attention}"
        )

    def _create_rnn_layer(
        self,
        input_size: int,
        hidden_size: int,
        num_layers: int,
        rnn_type: str,
        dropout: float,
        bidirectional: bool,
    ) -> nn.Module:
        """Create an RNN layer."""
        if rnn_type == "rnn":
            return nn.RNN(
                input_size=input_size,
                hidden_size=hidden_size,
                num_layers=num_layers,
                dropout=dropout if num_layers > 1 else 0.0,
                bidirectional=bidirectional,
                batch_first=True,
            )
        elif rnn_type == "lstm":
            return nn.LSTM(
                input_size=input_size,
                hidden_size=hidden_size,
                num_layers=num_layers,
                dropout=dropout if num_layers > 1 else 0.0,
                bidirectional=bidirectional,
                batch_first=True,
            )
        elif rnn_type == "gru":
            return nn.GRU(
                input_size=input_size,
                hidden_size=hidden_size,
                num_layers=num_layers,
                dropout=dropout if num_layers > 1 else 0.0,
                bidirectional=bidirectional,
                batch_first=True,
            )
        else:
            raise ValueError(f"Unknown RNN type: {rnn_type}")

    def forward(
        self,
        encoder_input: torch.Tensor,
        decoder_input: torch.Tensor,
    ) -> torch.Tensor:
        """
        Forward pass of the seq2seq network.

        Args:
            encoder_input: Input tensor for encoder (batch_size, enc_seq_len, enc_input_size).
            decoder_input: Input tensor for decoder (batch_size, dec_seq_len, dec_input_size).

        Returns:
            Output tensor (batch_size, dec_seq_len, output_size).
        """
        batch_size = encoder_input.size(0)
        dec_seq_len = decoder_input.size(1)

        # Encoder
        encoder_output, (hidden, cell) = self.encoder(encoder_input)

        # Initialize decoder hidden state with encoder's final state
        if self.rnn_type == "lstm":
            decoder_hidden = (hidden, cell)
        else:
            decoder_hidden = hidden

        # Decoder outputs
        decoder_outputs = []

        for t in range(dec_seq_len):
            # Get current decoder input
            dec_input_t = decoder_input[:, t:t+1, :]

            # Decoder forward pass
            if self.rnn_type == "lstm":
                dec_output, decoder_hidden = self.decoder(dec_input_t, decoder_hidden)
            else:
                dec_output, decoder_hidden = self.decoder(dec_input_t, decoder_hidden)

            # Apply attention if enabled
            if self.use_attention and self.rnn_type != "lstm":
                # For simplicity, we'll use a basic attention mechanism
                # In practice, you'd want a more sophisticated implementation
                attention_weights = F.softmax(
                    torch.bmm(dec_output, encoder_output.transpose(1, 2)),
                    dim=2
                )
                context = torch.bmm(attention_weights, encoder_output)
                dec_output = torch.cat([dec_output, context], dim=2)
                dec_output = F.relu(self.attention(dec_output))

            # Apply dropout
            dec_output = self.dropout_layer(dec_output)

            # Fully connected layer
            output_t = self.fc(dec_output.squeeze(1))
            decoder_outputs.append(output_t.unsqueeze(1))

        # Concatenate all decoder outputs
        decoder_outputs = torch.cat(decoder_outputs, dim=1)

        return decoder_outputs


class RNNFactory:
    """Factory for creating RNN models with common configurations."""

    @staticmethod
    def create_text_classifier(
        vocab_size: int,
        embed_dim: int = 128,
        hidden_size: int = 256,
        num_classes: int = 2,
        num_layers: int = 2,
        rnn_type: str = "lstm",
    ) -> SimpleRNN:
        """
        Create an RNN for text classification.

        Args:
            vocab_size: Size of vocabulary.
            embed_dim: Embedding dimension.
            hidden_size: Hidden state size.
            num_classes: Number of classes.
            num_layers: Number of RNN layers.
            rnn_type: Type of RNN.

        Returns:
            SimpleRNN model for text classification.
        """
        # Note: This is a simplified version. In practice, you'd want to add
        # an embedding layer for text classification.
        return SimpleRNN(
            input_size=embed_dim,
            hidden_size=hidden_size,
            output_size=num_classes,
            num_layers=num_layers,
            rnn_type=rnn_type,
            dropout=0.5,
            bidirectional=True,
        )

    @staticmethod
    def create_time_series_predictor(
        input_size: int,
        hidden_size: int = 64,
        output_size: int = 1,
        num_layers: int = 1,
        rnn_type: str = "lstm",
    ) -> SimpleRNN:
        """
        Create an RNN for time series prediction.

        Args:
            input_size: Number of input features.
            hidden_size: Hidden state size.
            output_size: Number of output features.
            num_layers: Number of RNN layers.
            rnn_type: Type of RNN.

        Returns:
            SimpleRNN model for time series prediction.
        """
        return SimpleRNN(
            input_size=input_size,
            hidden_size=hidden_size,
            output_size=output_size,
            num_layers=num_layers,
            rnn_type=rnn_type,
            dropout=0.2,
            bidirectional=False,
        )
