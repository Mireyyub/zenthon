"""
Unit Tests for Core Module
Tests for config, logger, and kernel components.
"""

import os
import unittest
import tempfile
import shutil
from unittest.mock import patch

# Add the project root to the path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from core.config import SystemConfig, PathConfig, ModelConfig, TrainingConfig
from core.logger import AILogger
from core.kernel import SystemKernel


class TestPathConfig(unittest.TestCase):
    """Tests for PathConfig."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_default_paths(self):
        """Test default path configuration."""
        config = PathConfig()
        self.assertTrue(os.path.isabs(config.base_dir))
        self.assertTrue(config.data_dir.startswith(config.base_dir))
        self.assertTrue(config.models_dir.startswith(config.base_dir))
        self.assertTrue(config.logs_dir.startswith(config.base_dir))

    def test_custom_base_dir(self):
        """Test custom base directory."""
        custom_dir = "/custom/path"
        config = PathConfig(base_dir=custom_dir)
        self.assertEqual(config.base_dir, custom_dir)


class TestModelConfig(unittest.TestCase):
    """Tests for ModelConfig."""

    def test_default_values(self):
        """Test default model configuration values."""
        config = ModelConfig()
        self.assertEqual(config.input_size, 784)
        self.assertEqual(config.hidden_size, 128)
        self.assertEqual(config.output_size, 10)
        self.assertEqual(config.learning_rate, 0.001)
        self.assertEqual(config.batch_size, 32)
        self.assertEqual(config.epochs, 10)
        self.assertEqual(config.dropout, 0.2)
        self.assertEqual(config.activation, "relu")

    def test_custom_values(self):
        """Test custom model configuration values."""
        config = ModelConfig(
            input_size=100,
            hidden_size=64,
            output_size=5,
            learning_rate=0.01,
            batch_size=64,
            epochs=20,
            dropout=0.5,
            activation="sigmoid",
        )
        self.assertEqual(config.input_size, 100)
        self.assertEqual(config.hidden_size, 64)
        self.assertEqual(config.output_size, 5)
        self.assertEqual(config.learning_rate, 0.01)
        self.assertEqual(config.batch_size, 64)
        self.assertEqual(config.epochs, 20)
        self.assertEqual(config.dropout, 0.5)
        self.assertEqual(config.activation, "sigmoid")


class TestTrainingConfig(unittest.TestCase):
    """Tests for TrainingConfig."""

    def test_default_values(self):
        """Test default training configuration values."""
        config = TrainingConfig()
        self.assertIn(config.device, ["cpu", "cuda"])
        self.assertTrue(config.mixed_precision)
        self.assertEqual(config.gradient_clip, 1.0)
        self.assertEqual(config.early_stopping_patience, 5)


class TestSystemConfig(unittest.TestCase):
    """Tests for SystemConfig."""

    def test_default_values(self):
        """Test default system configuration values."""
        config = SystemConfig()
        self.assertIsInstance(config.path, PathConfig)
        self.assertIsInstance(config.model, ModelConfig)
        self.assertIsInstance(config.training, TrainingConfig)
        self.assertTrue(config.debug)
        self.assertEqual(config.log_level, "INFO")


class TestAILogger(unittest.TestCase):
    """Tests for AILogger."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.logger = AILogger(log_dir=self.temp_dir, verbose=False)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_logging_levels(self):
        """Test different logging levels."""
        self.logger.debug("Debug message")
        self.logger.info("Info message")
        self.logger.warning("Warning message")
        self.logger.error("Error message")
        self.logger.critical("Critical message")

        # Check that log file was created
        log_files = [f for f in os.listdir(self.temp_dir) if f.endswith(".log")]
        self.assertGreater(len(log_files), 0)

    def test_log_metrics(self):
        """Test logging metrics."""
        metrics = {"accuracy": 0.95, "loss": 0.05, "f1": 0.93}
        self.logger.log_metrics(metrics)
        self.logger.log_metrics(metrics, prefix="Training")


class TestSystemKernel(unittest.TestCase):
    """Tests for SystemKernel."""

    def test_kernel_initialization(self):
        """Test kernel initialization."""
        kernel = SystemKernel()
        self.assertIsNotNone(kernel.config)

    @patch("core.kernel.psutil")
    @patch("core.kernel.GPUtil")
    def test_get_system_resources(self, mock_gputil, mock_psutil):
        """Test getting system resources."""
        # Mock psutil
        mock_psutil.virtual_memory.return_value = type(
            "obj",
            (object,),
            {
                "total": 1024 ** 3,
                "available": 512 * 1024 ** 2,
                "used": 512 * 1024 ** 2,
                "percent": 50.0,
            },
        )()
        mock_psutil.cpu_percent.return_value = 25.0

        # Mock GPUtil
        mock_gputil.getGPUs.return_value = []

        kernel = SystemKernel()
        resources = kernel.get_system_resources()

        self.assertIn("cpu_percent", resources)
        self.assertIn("memory", resources)
        self.assertIn("gpu", resources)

    def test_check_gpu_available(self):
        """Test GPU availability check."""
        kernel = SystemKernel()
        # This will return False if CUDA is not available
        result = kernel.check_gpu_available()
        self.assertIsInstance(result, bool)

    def test_set_device(self):
        """Test setting device."""
        kernel = SystemKernel()
        device = kernel.set_device()
        self.assertIn(device, ["cpu", "cuda"])

        # Test with explicit device
        device_cpu = kernel.set_device("cpu")
        self.assertEqual(device_cpu, "cpu")


if __name__ == "__main__":
    unittest.main()
