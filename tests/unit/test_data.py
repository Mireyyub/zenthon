"""
Unit Tests for Data Module
Tests for preprocessing and storage components.
"""

import os
import unittest
import tempfile
import shutil
import numpy as np
import pandas as pd

# Add the project root to the path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from data.preprocessing.clean import DataCleaner
from data.preprocessing.normalize import DataNormalizer
from data.storage.database import SQLiteDatabase, CSVStorage


class TestDataCleaner(unittest.TestCase):
    """Tests for DataCleaner."""

    def setUp(self):
        """Set up test fixtures."""
        self.cleaner = DataCleaner(verbose=False)

    def test_handle_missing_values_drop(self):
        """Test dropping missing values."""
        # Test with numpy array
        data = np.array([[1, 2, 3], [4, np.nan, 6], [7, 8, 9]])
        cleaned = self.cleaner.handle_missing_values(data, strategy="drop")
        self.assertEqual(cleaned.shape[0], 2)  # One row with NaN should be dropped

        # Test with pandas DataFrame
        df = pd.DataFrame({"a": [1, 2, np.nan], "b": [4, np.nan, 6]})
        cleaned = self.cleaner.handle_missing_values(df, strategy="drop")
        self.assertEqual(len(cleaned), 1)  # Only one complete row

    def test_handle_missing_values_fill(self):
        """Test filling missing values."""
        # Test with numpy array
        data = np.array([[1, 2, 3], [4, np.nan, 6], [7, 8, 9]])
        cleaned = self.cleaner.handle_missing_values(data, strategy="fill", fill_value=0)
        self.assertFalse(np.isnan(cleaned).any())
        self.assertEqual(cleaned[1, 1], 0)

        # Test with pandas DataFrame
        df = pd.DataFrame({"a": [1, 2, np.nan], "b": [4, np.nan, 6]})
        cleaned = self.cleaner.handle_missing_values(df, strategy="fill", fill_value=0)
        self.assertFalse(cleaned.isna().any().any())

    def test_remove_duplicates(self):
        """Test removing duplicates."""
        # Test with numpy array
        data = np.array([[1, 2], [1, 2], [3, 4]])
        cleaned = self.cleaner.remove_duplicates(data)
        self.assertEqual(cleaned.shape[0], 2)  # One duplicate removed

        # Test with pandas DataFrame
        df = pd.DataFrame({"a": [1, 1, 2], "b": [3, 3, 4]})
        cleaned = self.cleaner.remove_duplicates(df)
        self.assertEqual(len(cleaned), 2)  # One duplicate removed

    def test_handle_outliers_zscore(self):
        """Test handling outliers using z-score."""
        data = np.array([[1, 2, 3], [4, 5, 6], [100, 200, 300]])  # Last row is an outlier
        cleaned = self.cleaner.handle_outliers(data, method="zscore", threshold=2.0)
        # Outliers should be replaced with median
        self.assertTrue(np.all(cleaned < 10))  # Outliers should be capped

    def test_handle_outliers_iqr(self):
        """Test handling outliers using IQR."""
        data = np.array([[1, 2, 3], [4, 5, 6], [100, 200, 300]])  # Last row is an outlier
        cleaned = self.cleaner.handle_outliers(data, method="iqr")
        # Outliers should be replaced with median
        self.assertTrue(np.all(cleaned < 10))  # Outliers should be capped


class TestDataNormalizer(unittest.TestCase):
    """Tests for DataNormalizer."""

    def setUp(self):
        """Set up test fixtures."""
        self.normalizer = DataNormalizer(verbose=False)

    def test_min_max_normalize(self):
        """Test min-max normalization."""
        # Test with numpy array
        data = np.array([[1, 2, 3], [4, 5, 6]])
        normalized = self.normalizer.min_max_normalize(data)
        self.assertTrue(np.all(normalized >= 0))
        self.assertTrue(np.all(normalized <= 1))

        # Test with pandas DataFrame
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        normalized = self.normalizer.min_max_normalize(df)
        self.assertTrue(np.all(normalized.values >= 0))
        self.assertTrue(np.all(normalized.values <= 1))

    def test_z_score_normalize(self):
        """Test z-score normalization."""
        # Test with numpy array
        data = np.array([[1, 2, 3], [4, 5, 6]])
        normalized = self.normalizer.z_score_normalize(data)
        # Mean should be close to 0, std should be close to 1
        self.assertAlmostEqual(np.mean(normalized), 0, places=10)
        self.assertAlmostEqual(np.std(normalized), 1, places=10)

        # Test with pandas DataFrame
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        normalized = self.normalizer.z_score_normalize(df)
        self.assertAlmostEqual(np.mean(normalized.values), 0, places=10)

    def test_robust_normalize(self):
        """Test robust normalization."""
        data = np.array([[1, 2, 3], [4, 5, 6], [100, 200, 300]])  # With outliers
        normalized = self.normalizer.robust_normalize(data)
        # Should handle outliers well
        self.assertTrue(np.all(np.abs(normalized) < 10))

    def test_l2_normalize(self):
        """Test L2 normalization."""
        data = np.array([[1, 2, 3], [4, 5, 6]])
        normalized = self.normalizer.l2_normalize(data)
        # Each row should have norm 1
        norms = np.linalg.norm(normalized, axis=1)
        self.assertTrue(np.allclose(norms, 1))


class TestSQLiteDatabase(unittest.TestCase):
    """Tests for SQLiteDatabase."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.db = SQLiteDatabase(db_path=self.db_path)

    def tearDown(self):
        """Clean up test fixtures."""
        self.db.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_table(self):
        """Test creating a table."""
        schema = {
            "id": "INTEGER PRIMARY KEY",
            "name": "TEXT",
            "value": "REAL",
        }
        self.db.create_table("test_table", schema)

        # Verify table was created
        result = self.db._execute("SELECT name FROM sqlite_master WHERE type='table'", fetch=True)
        table_names = [row[0] for row in result]
        self.assertIn("test_table", table_names)

    def test_insert_and_select(self):
        """Test inserting and selecting data."""
        # Create table
        schema = {"id": "INTEGER PRIMARY KEY", "name": "TEXT", "value": "REAL"}
        self.db.create_table("test_table", schema)

        # Insert data
        data = [{"id": 1, "name": "test1", "value": 1.0}]
        self.db.insert("test_table", data)

        # Select data
        result = self.db.select("test_table")
        self.assertEqual(len(result), 1)
        self.assertEqual(result["name"].iloc[0], "test1")

    def test_update(self):
        """Test updating data."""
        # Create table
        schema = {"id": "INTEGER PRIMARY KEY", "name": "TEXT", "value": "REAL"}
        self.db.create_table("test_table", schema)

        # Insert data
        data = [{"id": 1, "name": "test1", "value": 1.0}]
        self.db.insert("test_table", data)

        # Update data
        self.db.update("test_table", {"name": "updated"}, where="id = 1")

        # Verify update
        result = self.db.select("test_table", where="id = 1")
        self.assertEqual(result["name"].iloc[0], "updated")

    def test_delete(self):
        """Test deleting data."""
        # Create table
        schema = {"id": "INTEGER PRIMARY KEY", "name": "TEXT"}
        self.db.create_table("test_table", schema)

        # Insert data
        data = [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}]
        self.db.insert("test_table", data)

        # Delete data
        self.db.delete("test_table", where="id = 1")

        # Verify deletion
        result = self.db.select("test_table")
        self.assertEqual(len(result), 1)


class TestCSVStorage(unittest.TestCase):
    """Tests for CSVStorage."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = CSVStorage(base_dir=self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_and_load(self):
        """Test saving and loading CSV files."""
        # Create test data
        data = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        filename = "test.csv"

        # Save data
        self.storage.save(data, filename)

        # Verify file exists
        self.assertTrue(self.storage.exists(filename))

        # Load data
        loaded = self.storage.load(filename)
        pd.testing.assert_frame_equal(data, loaded)

    def test_exists(self):
        """Test checking if a file exists."""
        # File doesn't exist
        self.assertFalse(self.storage.exists("nonexistent.csv"))

        # Create and save a file
        data = pd.DataFrame({"a": [1, 2, 3]})
        self.storage.save(data, "test.csv")

        # File exists
        self.assertTrue(self.storage.exists("test.csv"))


if __name__ == "__main__":
    unittest.main()
