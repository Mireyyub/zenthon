# AI System Architecture

This document describes the architecture of the **AI System** - a comprehensive platform for building, training, evaluating, and deploying machine learning and deep learning models.

---

## 📌 Table of Contents

1. [Overview](#-overview)
2. [System Architecture](#-system-architecture)
3. [Core Module](#-core-module)
4. [Data Module](#-data-module)
5. [Models Module](#-models-module)
6. [Training Module](#-training-module)
7. [Inference Module](#-inference-module)
8. [Interfaces Module](#-interfaces-module)
9. [Utils Module](#-utils-module)
10. [Tests Module](#-tests-module)
11. [Dependencies](#-dependencies)

---

## 📌 Overview

The **AI System** is designed as a modular, extensible platform for machine learning and deep learning workflows. It provides:

- **Modular Design**: Each component (data preprocessing, model training, inference) is separated into its own module.
- **Extensibility**: Easy to add new models, preprocessing steps, or training algorithms.
- **Multiple Interfaces**: CLI, GUI, and REST API for interacting with the system.
- **Comprehensive Testing**: Unit, integration, and performance tests.
- **Documentation**: Complete documentation for all components.

---

## 🏗️ System Architecture

```
AI_System/
│
├── core/                          # Core system components
│   ├── config.py                 # Configuration management
│   ├── logger.py                 # Logging utilities
│   └── kernel.py                 # System resource management
│
├── data/                          # Data handling components
│   ├── datasets/                 # Dataset storage
│   ├── preprocessing/             # Data preprocessing
│   │   ├── clean.py              # Data cleaning (missing values, duplicates, outliers)
│   │   ├── normalize.py          # Data normalization (min-max, z-score, robust, L2)
│   │   └── augment.py            # Data augmentation (images, text)
│   └── storage/                  # Data storage
│       └── database.py           # Database operations (SQLite, CSV)
│
├── models/                       # Machine learning and deep learning models
│   ├── ml/                       # Machine learning models
│   │   ├── supervised/           # Supervised learning
│   │   │   ├── linear_regression.py
│   │   │   └── random_forest.py
│   │   ├── unsupervised/         # Unsupervised learning
│   │   │   └── kmeans.py
│   │   └── reinforcement/        # Reinforcement learning
│   │
│   └── dl/                       # Deep learning models
│       ├── nn/                   # Neural networks
│       │   └── simple_nn.py       # Simple feedforward networks
│       ├── cnn/                  # Convolutional neural networks
│       │   └── simple_cnn.py      # Simple CNN for images
│       ├── rnn/                  # Recurrent neural networks
│       │   └── simple_rnn.py      # Simple RNN, LSTM, GRU
│       └── transformer/          # Transformer models
│           └── simple_transformer.py
│
├── training/                     # Training components
│   ├── trainers/                 # Model trainers
│   │   └── supervised_trainer.py # Supervised learning trainer
│   ├── optimizers/               # Optimization algorithms
│   │   └── custom_optimizers.py # AdamW, SGDW, RAdam
│   ├── loss_functions/          # Loss functions
│   │   └── custom_losses.py      # Focal Loss, Contrastive Loss, etc.
│   └── metrics/                 # Evaluation metrics
│       └── classification_metrics.py
│
├── inference/                    # Inference components
│   ├── predictors/               # Prediction utilities
│   │   └── model_predictor.py    # Universal predictor
│   ├── explainers/               # Explainable AI
│   │   ├── lime_explainer.py     # LIME explainer
│   │   └── shap_explainer.py     # SHAP explainer
│   └── api/                      # API interfaces
│       └── fastapi_app.py        # FastAPI REST API
│
├── interfaces/                   # User interfaces
│   ├── cli/                      # Command-line interface
│   │   └── main_cli.py           # Main CLI application
│   ├── gui/                      # Graphical user interface
│   │   └── main_gui.py           # Tkinter GUI application
│   └── web/                      # Web interface
│       └── web_interface.py      # Flask web application
│
├── utils/                        # Utility functions
│   ├── math/                     # Mathematical utilities
│   │   ├── linear_algebra.py    # Linear algebra operations
│   │   └── statistics.py        # Statistical functions
│   ├── visualization/             # Data visualization
│   │   └── plotting.py           # Plotting utilities (Matplotlib, Seaborn)
│   └── helpers/                 # Helper functions
│       └── file_utils.py         # File operations
│
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   │   ├── test_core.py         # Core module tests
│   │   ├── test_data.py         # Data module tests
│   │   └── test_models.py       # Models module tests
│   ├── integration/              # Integration tests
│   │   └── test_training_pipeline.py
│   └── performance/              # Performance tests
│       └── test_model_performance.py
│
├── docs/                         # Documentation
│   ├── architecture.md           # Architecture documentation
│   ├── api_reference.md          # API reference
│   └── tutorials/                # Tutorials and examples
│
└── README.md                     # Main documentation
```

---

## 🔧 Core Module

The **Core Module** provides the foundation for the AI System:

### `config.py`
- **Purpose**: Manages system-wide configuration
- **Key Classes**:
  - `PathConfig`: Manages file and directory paths
  - `ModelConfig`: Configuration for machine learning models
  - `TrainingConfig`: Configuration for training processes
  - `SystemConfig`: Main system configuration
- **Features**:
  - Default configurations for common use cases
  - Support for loading/saving configurations from files
  - Environment variable support

### `logger.py`
- **Purpose**: Provides logging utilities for tracking system operations
- **Key Classes**:
  - `AILogger`: Custom logger with file and console output
- **Features**:
  - Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - Automatic log file creation with timestamps
  - Metrics logging for tracking training progress

### `kernel.py`
- **Purpose**: Manages system resources and environment
- **Key Classes**:
  - `SystemKernel`: System resource manager
- **Features**:
  - System information collection (CPU, memory, GPU)
  - Resource monitoring
  - Device management (CPU/GPU selection)
  - Dependency checking

---

## 📊 Data Module

The **Data Module** handles all aspects of data management:

### `preprocessing/`

#### `clean.py` - DataCleaner
- **Purpose**: Handles missing values, duplicates, and outliers
- **Methods**:
  - `handle_missing_values()`: Drop, fill, or interpolate missing values
  - `remove_duplicates()`: Remove duplicate rows
  - `handle_outliers()`: Handle outliers using z-score or IQR
- **Supported Data Types**: NumPy arrays, Pandas DataFrames

#### `normalize.py` - DataNormalizer
- **Purpose**: Provides various normalization techniques
- **Methods**:
  - `min_max_normalize()`: Min-max scaling to a specified range
  - `z_score_normalize()`: Standardization (mean=0, std=1)
  - `robust_normalize()`: Robust scaling using median and IQR
  - `l2_normalize()`: L2 normalization (unit norm)
- **Supported Data Types**: NumPy arrays, Pandas DataFrames

#### `augment.py` - Data Augmentation
- **Purpose**: Provides data augmentation for images and text
- **Classes**:
  - `ImageAugmenter`: Image augmentation (rotation, flip, resize, noise, crop)
  - `TextAugmenter`: Text augmentation (synonym replacement, random deletion, swap, insertion)
- **Features**:
  - Random augmentation combinations
  - Support for PIL Images and NumPy arrays

### `storage/`

#### `database.py`
- **Purpose**: Database operations for data persistence
- **Classes**:
  - `SQLiteDatabase`: SQLite database handler
  - `CSVStorage`: CSV file storage handler
- **Features**:
  - Table creation and management
  - CRUD operations (Create, Read, Update, Delete)
  - CSV file read/write operations
  - Context manager support for automatic connection handling

---

## 🤖 Models Module

The **Models Module** contains machine learning and deep learning models:

### Machine Learning Models (`ml/`)

#### Supervised Learning (`supervised/`)

##### `linear_regression.py` - LinearRegression
- **Purpose**: Linear regression using ordinary least squares
- **Features**:
  - Normal equation (closed-form solution)
  - Gradient descent optimization
  - R-squared score calculation
  - Support for intercept (bias) term

##### `random_forest.py` - RandomForest
- **Purpose**: Random Forest classifier
- **Features**:
  - Bootstrap sampling
  - Multiple decision trees
  - Majority voting for classification
  - Feature importance calculation

#### Unsupervised Learning (`unsupervised/`)

##### `kmeans.py` - KMeans
- **Purpose**: K-Means clustering algorithm
- **Features**:
  - K-means++ initialization
  - Euclidean distance metric
  - Inertia calculation
  - Cluster assignment

### Deep Learning Models (`dl/`)

#### Neural Networks (`nn/`)

##### `simple_nn.py` - SimpleNN, MLP
- **Purpose**: Feedforward neural networks
- **Classes**:
  - `SimpleNN`: Basic feedforward network
  - `MLP`: Multi-layer perceptron
  - `SimpleNNFactory`: Factory for creating pre-configured networks
- **Features**:
  - Configurable architecture (input, hidden, output layers)
  - Multiple activation functions (ReLU, Sigmoid, Tanh, Leaky ReLU)
  - Dropout for regularization
  - Batch normalization
  - Weight initialization (Xavier, He)

#### Convolutional Neural Networks (`cnn/`)

##### `simple_cnn.py` - SimpleCNN
- **Purpose**: CNN for image classification
- **Classes**:
  - `SimpleCNN`: Basic CNN architecture
  - `CNNFactory`: Factory for common CNN configurations
- **Features**:
  - Configurable convolutional layers
  - Max pooling
  - Fully connected layers
  - Dropout
  - Pre-configured architectures for MNIST, CIFAR-10

#### Recurrent Neural Networks (`rnn/`)

##### `simple_rnn.py` - SimpleRNN, Seq2SeqRNN
- **Purpose**: RNN for sequence processing
- **Classes**:
  - `SimpleRNN`: Basic RNN, LSTM, or GRU
  - `Seq2SeqRNN`: Sequence-to-sequence model with attention
  - `RNNFactory`: Factory for common RNN configurations
- **Features**:
  - Support for RNN, LSTM, GRU
  - Bidirectional RNNs
  - Attention mechanism (basic implementation)
  - Pre-configured for text classification and time series prediction

#### Transformer Models (`transformer/`)

##### `simple_transformer.py` - SimpleTransformer
- **Purpose**: Transformer model for sequence processing
- **Classes**:
  - `PositionalEncoding`: Positional encoding for transformers
  - `MultiHeadAttention`: Multi-head attention layer
  - `TransformerBlock`: Transformer block with residual connections
  - `SimpleTransformer`: Complete transformer model
  - `TransformerFactory`: Factory for common transformer configurations
- **Features**:
  - Multi-head attention
  - Positional encoding
  - Layer normalization
  - Feed-forward networks
  - Pre-configured for text classification and language modeling

---

## 🎓 Training Module

The **Training Module** provides tools for training models:

### `trainers/`

#### `supervised_trainer.py` - SupervisedTrainer
- **Purpose**: Trainer for supervised learning models
- **Features**:
  - Support for both scikit-learn and PyTorch models
  - Batch training with DataLoader
  - Validation during training
  - Early stopping
  - Metrics tracking
  - Model saving/loading
  - Callback support

### `optimizers/`

#### `custom_optimizers.py`
- **Purpose**: Custom optimization algorithms
- **Classes**:
  - `AdamW`: Adam with decoupled weight decay
  - `SGDW`: SGD with weight decay
  - `RAdam`: Rectified Adam optimizer
  - `OptimizerFactory`: Factory for creating optimizers
- **Features**:
  - Decoupled weight decay
  - AMSGrad support
  - Nesterov momentum

### `loss_functions/`

#### `custom_losses.py`
- **Purpose**: Custom loss functions
- **Classes**:
  - `FocalLoss`: Focal loss for imbalanced classification
  - `ContrastiveLoss`: Contrastive loss for siamese networks
  - `TripletLoss`: Triplet loss for metric learning
  - `DiceLoss`: Dice loss for segmentation
  - `LabelSmoothingLoss`: Label smoothing loss for classification
  - `LossFunctionFactory`: Factory for creating loss functions
- **Features**:
  - Support for classification and regression tasks
  - Customizable parameters

### `metrics/`

#### `classification_metrics.py`
- **Purpose**: Classification evaluation metrics
- **Classes**:
  - `ClassificationMetrics`: Collection of classification metrics
  - `BinaryClassificationMetrics`: Metrics for binary classification
  - `MultiClassClassificationMetrics`: Metrics for multi-class classification
- **Features**:
  - Accuracy, Precision, Recall, F1-score
  - ROC AUC, Average Precision
  - Confusion matrix
  - Classification report
  - Sensitivity, Specificity
  - Per-class metrics

---

## 🔮 Inference Module

The **Inference Module** provides tools for making predictions and explaining them:

### `predictors/`

#### `model_predictor.py` - ModelPredictor, ImagePredictor, TextPredictor
- **Purpose**: Universal predictor for trained models
- **Classes**:
  - `ModelPredictor`: Base predictor for any model type
  - `ImagePredictor`: Predictor for image classification models
  - `TextPredictor`: Predictor for text classification models
- **Features**:
  - Support for PyTorch, scikit-learn, and Keras models
  - Batch prediction
  - Preprocessing and postprocessing hooks
  - Image-specific preprocessing (resizing, normalization)
  - Text tokenization support

### `explainers/`

#### `lime_explainer.py` - LIMEExplainer, LIMEImageExplainer
- **Purpose**: Local Interpretable Model-agnostic Explanations
- **Classes**:
  - `LIMEExplainer`: LIME for tabular data
  - `LIMEImageExplainer`: LIME for image data
- **Features**:
  - Local model approximation
  - Feature importance calculation
  - Text and image visualization

#### `shap_explainer.py` - KernelSHAP, DeepSHAP
- **Purpose**: SHapley Additive exPlanations
- **Classes**:
  - `KernelSHAP`: Kernel SHAP for any model
  - `DeepSHAP`: SHAP for deep learning models
- **Features**:
  - Shapley value calculation
  - Feature importance ranking
  - Visualization of explanations

### `api/`

#### `fastapi_app.py`
- **Purpose**: REST API for model serving
- **Features**:
  - Model registration and management
  - Prediction endpoints
  - Explanation endpoints
  - File upload support
  - CORS support
  - Health check endpoint
  - Automatic model loading on startup

---

## 🖥️ Interfaces Module

The **Interfaces Module** provides different ways to interact with the AI System:

### `cli/` - Command Line Interface

#### `main_cli.py` - CLIController
- **Purpose**: Command-line interface for the AI System
- **Features**:
  - Model training from CSV files
  - Prediction on new data
  - Model evaluation
  - System information display
  - Model listing
- **Usage**:
  ```bash
  # Train a model
  python -m interfaces.cli.main_cli train --model linear_regression --data train.csv --target y

  # Make predictions
  python -m interfaces.cli.main_cli predict --model linear_regression --data test.csv

  # Evaluate a model
  python -m interfaces.cli.main_cli evaluate --model linear_regression --data test.csv --target y

  # Show system info
  python -m interfaces.cli.main_cli info
  ```

### `gui/` - Graphical User Interface

#### `main_gui.py` - AIApp
- **Purpose**: Graphical user interface using Tkinter
- **Features**:
  - Data loading and preview
  - Model training configuration
  - Prediction interface
  - Explanation generation
  - Logs display
  - Status bar
- **Tabs**:
  - Data: Load and preview datasets
  - Train: Configure and start training
  - Predict: Make predictions on new data
  - Explain: Generate explanations for predictions
  - Logs: View system logs

### `web/` - Web Interface

#### `web_interface.py`
- **Purpose**: Web-based interface using Flask
- **Features**:
  - Home page with system overview
  - Training page for model configuration
  - Prediction page for making predictions
  - Explanation page for generating explanations
  - REST API endpoints
- **Pages**:
  - `/`: Home page
  - `/train`: Training page
  - `/predict`: Prediction page
  - `/explain`: Explanation page
- **API Endpoints**:
  - `GET /api/models`: List all models
  - `POST /api/train`: Train a model
  - `POST /api/predict`: Make a prediction
  - `POST /api/explain`: Generate explanation
  - `POST /api/upload`: Upload a file

---

## 🛠️ Utils Module

The **Utils Module** provides utility functions:

### `math/`

#### `linear_algebra.py` - LinearAlgebraUtils
- **Purpose**: Linear algebra operations
- **Methods**:
  - Matrix operations (multiplication, inverse, transpose)
  - Vector operations (dot product, norm, normalization)
  - Decompositions (SVD, QR, Cholesky)
  - Solvers (linear systems, least squares)
  - Distance metrics (cosine, Euclidean, Manhattan)

#### `statistics.py` - StatisticsUtils
- **Purpose**: Statistical functions
- **Methods**:
  - Central tendency (mean, median, mode)
  - Dispersion (std, var, range, IQR)
  - Shape (skewness, kurtosis)
  - Correlation and covariance
  - Z-score calculation
  - Percentiles and histograms
  - Statistical tests (t-test, chi-square, normality test)
  - Descriptive statistics

### `visualization/`

#### `plotting.py` - Plotter
- **Purpose**: Data visualization utilities
- **Methods**:
  - Line plots (single and multiple)
  - Bar plots (single and grouped)
  - Histograms and distribution plots
  - Scatter plots (with and without regression line)
  - Box plots
  - Heatmaps
  - Correlation matrices
  - Pair plots
  - Confusion matrices
  - ROC curves
  - Training curves
- **Features**:
  - Matplotlib and Seaborn support
  - Automatic plot saving
  - Customizable styles and colors

### `helpers/`

#### `file_utils.py` - FileUtils
- **Purpose**: File and directory operations
- **Methods**:
  - Directory creation and management
  - File copying, moving, deletion
  - File reading and writing (text, JSON, pickle, CSV)
  - File metadata (size, modification time, hash)
  - File comparison
  - File searching and listing

---

## 🧪 Tests Module

The **Tests Module** contains comprehensive tests:

### `unit/` - Unit Tests
- **Purpose**: Test individual components in isolation
- **Files**:
  - `test_core.py`: Tests for core module
  - `test_data.py`: Tests for data module
  - `test_models.py`: Tests for models module
- **Features**:
  - Configuration tests
  - Logging tests
  - Data cleaning and normalization tests
  - Model training and prediction tests
  - Database operation tests

### `integration/` - Integration Tests
- **Purpose**: Test interactions between components
- **Files**:
  - `test_training_pipeline.py`: Tests for complete training workflows
- **Features**:
  - End-to-end training pipeline tests
  - Data preprocessing to prediction workflow
  - Model saving and loading
  - Custom optimizer and loss function integration

### `performance/` - Performance Tests
- **Purpose**: Benchmark tests for performance
- **Files**:
  - `test_model_performance.py`: Performance tests for models
- **Features**:
  - Training speed tests
  - Prediction latency tests
  - Memory usage tests
  - Batch size impact tests
  - Model size impact tests

---

## 📦 Dependencies

The AI System has the following dependencies:

### Core Dependencies
- Python 3.8+
- NumPy
- Pandas
- Scikit-learn
- PyTorch
- Torchvision (optional, for vision tasks)
- Pillow (PIL)
- OpenCV (cv2)
- SQLite3 (built-in)

### Optional Dependencies
- TensorFlow/Keras (for Keras model support)
- FastAPI (for REST API)
- Uvicorn (for FastAPI server)
- Flask (for web interface)
- Tkinter (built-in, for GUI)
- Matplotlib (for visualization)
- Seaborn (for visualization)
- Scipy (for statistical functions)
- GPUtil (for GPU monitoring)
- psutil (for system monitoring)

### Development Dependencies
- pytest (for testing)
- black (for code formatting)
- flake8 (for linting)
- mypy (for type checking)

---

## 📝 Summary

The AI System provides a **comprehensive, modular, and extensible** platform for machine learning and deep learning workflows. With its well-organized architecture, it supports:

1. **Flexible Data Handling**: From raw data to preprocessed features
2. **Diverse Model Support**: From traditional ML to state-of-the-art DL
3. **Comprehensive Training**: With custom optimizers, loss functions, and metrics
4. **Powerful Inference**: With prediction, explanation, and API serving
5. **Multiple Interfaces**: CLI, GUI, and Web for different use cases
6. **Robust Utilities**: Math, visualization, and file operations
7. **Thorough Testing**: Unit, integration, and performance tests

This architecture ensures that the AI System is **scalable, maintainable, and production-ready** for a wide range of machine learning applications.
