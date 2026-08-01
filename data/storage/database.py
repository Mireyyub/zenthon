"""
Database Storage Module
Provides interfaces for SQL and NoSQL database operations.
"""

import os
import sqlite3
from typing import Optional, Union, List, Dict, Any
import pandas as pd

from core.logger import logger
from core.config import config


class SQLiteDatabase:
    """SQLite database handler for storing and retrieving data."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.path.join(config.path.data_dir, "ai_system.db")
        self.connection = None
        self._connect()

    def _connect(self) -> None:
        """Establish database connection."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            logger.info(f"Connected to SQLite database at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to SQLite database: {e}")
            raise

    def _execute(self, query: str, params: tuple = (), fetch: bool = False) -> Optional[List[tuple]]:
        """
        Execute a SQL query.

        Args:
            query: SQL query string.
            params: Query parameters.
            fetch: Whether to fetch results.

        Returns:
            Query results if fetch=True, else None.
        """
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
            self.connection.commit()
        except sqlite3.Error as e:
            logger.error(f"SQL query failed: {e}")
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def create_table(self, table_name: str, schema: Dict[str, str]) -> None:
        """
        Create a new table in the database.

        Args:
            table_name: Name of the table.
            schema: Dictionary of column names and their types.
        """
        columns = ", ".join([f"{col_name} {col_type}" for col_name, col_type in schema.items()])
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})"
        self._execute(query)
        logger.info(f"Created table {table_name} with schema: {schema}")

    def insert(self, table_name: str, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> None:
        """
        Insert data into a table.

        Args:
            table_name: Name of the table.
            data: Single row or list of rows to insert.
        """
        if isinstance(data, dict):
            data = [data]

        if not data:
            return

        columns = ", ".join(data[0].keys())
        placeholders = ", ".join(["?"] * len(data[0]))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        params_list = [tuple(row[col] for col in data[0].keys()) for row in data]

        try:
            cursor = self.connection.cursor()
            cursor.executemany(query, params_list)
            self.connection.commit()
            logger.info(f"Inserted {len(data)} rows into {table_name}")
        except sqlite3.Error as e:
            logger.error(f"Failed to insert data: {e}")
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def select(
        self,
        table_name: str,
        columns: List[str] = None,
        where: Optional[str] = None,
        params: tuple = (),
    ) -> pd.DataFrame:
        """
        Select data from a table.

        Args:
            table_name: Name of the table.
            columns: List of columns to select (None for all).
            where: WHERE clause (without the WHERE keyword).
            params: Parameters for the WHERE clause.

        Returns:
            DataFrame containing the query results.
        """
        cols = "*" if columns is None else ", ".join(columns)
        query = f"SELECT {cols} FROM {table_name}"
        if where:
            query += f" WHERE {where}"

        results = self._execute(query, params, fetch=True)
        if not results:
            return pd.DataFrame()

        df = pd.DataFrame(results)
        if columns is not None:
            df.columns = columns
        else:
            # Get column names from cursor description
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            df.columns = [desc[0] for desc in cursor.description]
            cursor.close()

        return df

    def update(
        self,
        table_name: str,
        updates: Dict[str, Any],
        where: Optional[str] = None,
        params: tuple = (),
    ) -> None:
        """
        Update data in a table.

        Args:
            table_name: Name of the table.
            updates: Dictionary of column-value pairs to update.
            where: WHERE clause (without the WHERE keyword).
            params: Parameters for the WHERE clause.
        """
        set_clause = ", ".join([f"{col} = ?" for col in updates.keys()])
        query = f"UPDATE {table_name} SET {set_clause}"
        if where:
            query += f" WHERE {where}"

        all_params = tuple(updates.values()) + params
        self._execute(query, all_params)
        logger.info(f"Updated rows in {table_name}")

    def delete(self, table_name: str, where: Optional[str] = None, params: tuple = ()) -> None:
        """
        Delete data from a table.

        Args:
            table_name: Name of the table.
            where: WHERE clause (without the WHERE keyword).
            params: Parameters for the WHERE clause.
        """
        query = f"DELETE FROM {table_name}"
        if where:
            query += f" WHERE {where}"

        self._execute(query, params)
        logger.info(f"Deleted rows from {table_name}")

    def close(self) -> None:
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Closed SQLite database connection")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class CSVStorage:
    """CSV file storage handler."""

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or config.path.datasets_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def save(self, data: pd.DataFrame, filename: str, index: bool = False) -> None:
        """
        Save DataFrame to CSV file.

        Args:
            data: DataFrame to save.
            filename: Name of the CSV file.
            index: Whether to save the index.
        """
        filepath = os.path.join(self.base_dir, filename)
        data.to_csv(filepath, index=index)
        logger.info(f"Saved DataFrame to {filepath}")

    def load(self, filename: str) -> pd.DataFrame:
        """
        Load DataFrame from CSV file.

        Args:
            filename: Name of the CSV file.

        Returns:
            Loaded DataFrame.
        """
        filepath = os.path.join(self.base_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"CSV file not found: {filepath}")

        data = pd.read_csv(filepath)
        logger.info(f"Loaded DataFrame from {filepath}")
        return data

    def exists(self, filename: str) -> bool:
        """Check if a CSV file exists."""
        filepath = os.path.join(self.base_dir, filename)
        return os.path.exists(filepath)


# Global storage instances
sqlite_db = SQLiteDatabase()
csv_storage = CSVStorage()
