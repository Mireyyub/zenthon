"""
File Utilities Module
Provides file and directory operations.
"""

import os
import shutil
import json
import pickle
import csv
from typing import Optional, Union, List, Dict, Any
import glob

from core.logger import logger


class FileUtils:
    """
    Collection of file utilities.
    """

    @staticmethod
    def ensure_directory_exists(directory: str) -> None:
        """
        Ensure a directory exists, create if it doesn't.

        Args:
            directory: Path to the directory.
        """
        os.makedirs(directory, exist_ok=True)

    @staticmethod
    def get_file_extension(filename: str) -> str:
        """
        Get the file extension.

        Args:
            filename: Name of the file.

        Returns:
            File extension (without the dot).
        """
        return os.path.splitext(filename)[1][1:].lower()

    @staticmethod
    def get_filename_without_extension(filename: str) -> str:
        """
        Get the filename without extension.

        Args:
            filename: Name of the file.

        Returns:
            Filename without extension.
        """
        return os.path.splitext(filename)[0]

    @staticmethod
    def get_file_size(filename: str) -> int:
        """
        Get the size of a file in bytes.

        Args:
            filename: Path to the file.

        Returns:
            File size in bytes.
        """
        return os.path.getsize(filename)

    @staticmethod
    def get_file_size_mb(filename: str) -> float:
        """
        Get the size of a file in megabytes.

        Args:
            filename: Path to the file.

        Returns:
            File size in MB.
        """
        return os.path.getsize(filename) / (1024 * 1024)

    @staticmethod
    def list_files(
        directory: str,
        extension: Optional[str] = None,
        recursive: bool = False,
    ) -> List[str]:
        """
        List files in a directory.

        Args:
            directory: Path to the directory.
            extension: File extension to filter by (without the dot).
            recursive: Whether to search recursively.

        Returns:
            List of file paths.
        """
        if not os.path.exists(directory):
            return []

        files = []
        if recursive:
            for root, _, filenames in os.walk(directory):
                for filename in filenames:
                    if extension is None or FileUtils.get_file_extension(filename) == extension:
                        files.append(os.path.join(root, filename))
        else:
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath):
                    if extension is None or FileUtils.get_file_extension(filename) == extension:
                        files.append(filepath)

        return files

    @staticmethod
    def find_files(
        directory: str,
        pattern: str,
        recursive: bool = True,
    ) -> List[str]:
        """
        Find files matching a pattern.

        Args:
            directory: Path to the directory.
            pattern: Glob pattern to match.
            recursive: Whether to search recursively.

        Returns:
            List of matching file paths.
        """
        if not os.path.exists(directory):
            return []

        pattern_path = os.path.join(directory, pattern)
        if recursive:
            return glob.glob(pattern_path, recursive=True)
        else:
            return glob.glob(pattern_path)

    @staticmethod
    def copy_file(
        src: str,
        dst: str,
        overwrite: bool = False,
    ) -> None:
        """
        Copy a file.

        Args:
            src: Source file path.
            dst: Destination file path.
            overwrite: Whether to overwrite if destination exists.
        """
        if os.path.exists(dst) and not overwrite:
            raise FileExistsError(f"Destination file already exists: {dst}")

        # Ensure destination directory exists
        dst_dir = os.path.dirname(dst)
        if dst_dir:
            FileUtils.ensure_directory_exists(dst_dir)

        shutil.copy2(src, dst)
        logger.info(f"Copied file: {src} -> {dst}")

    @staticmethod
    def move_file(
        src: str,
        dst: str,
        overwrite: bool = False,
    ) -> None:
        """
        Move a file.

        Args:
            src: Source file path.
            dst: Destination file path.
            overwrite: Whether to overwrite if destination exists.
        """
        if os.path.exists(dst) and not overwrite:
            raise FileExistsError(f"Destination file already exists: {dst}")

        # Ensure destination directory exists
        dst_dir = os.path.dirname(dst)
        if dst_dir:
            FileUtils.ensure_directory_exists(dst_dir)

        shutil.move(src, dst)
        logger.info(f"Moved file: {src} -> {dst}")

    @staticmethod
    def delete_file(filepath: str) -> None:
        """
        Delete a file.

        Args:
            filepath: Path to the file.
        """
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Deleted file: {filepath}")
        else:
            logger.warning(f"File not found: {filepath}")

    @staticmethod
    def delete_directory(directory: str, recursive: bool = True) -> None:
        """
        Delete a directory.

        Args:
            directory: Path to the directory.
            recursive: Whether to delete recursively.
        """
        if os.path.exists(directory):
            if recursive:
                shutil.rmtree(directory)
            else:
                os.rmdir(directory)
            logger.info(f"Deleted directory: {directory}")
        else:
            logger.warning(f"Directory not found: {directory}")

    @staticmethod
    def read_text_file(filepath: str) -> str:
        """
        Read a text file.

        Args:
            filepath: Path to the file.

        Returns:
            File contents as string.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def write_text_file(filepath: str, content: str, overwrite: bool = True) -> None:
        """
        Write to a text file.

        Args:
            filepath: Path to the file.
            content: Content to write.
            overwrite: Whether to overwrite if file exists.
        """
        if os.path.exists(filepath) and not overwrite:
            raise FileExistsError(f"File already exists: {filepath}")

        # Ensure directory exists
        directory = os.path.dirname(filepath)
        if directory:
            FileUtils.ensure_directory_exists(directory)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Wrote file: {filepath}")

    @staticmethod
    def read_json_file(filepath: str) -> Dict[str, Any]:
        """
        Read a JSON file.

        Args:
            filepath: Path to the file.

        Returns:
            Parsed JSON data.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def write_json_file(
        filepath: str,
        data: Dict[str, Any],
        indent: int = 4,
        overwrite: bool = True,
    ) -> None:
        """
        Write to a JSON file.

        Args:
            filepath: Path to the file.
            data: Data to write.
            indent: Indentation level.
            overwrite: Whether to overwrite if file exists.
        """
        if os.path.exists(filepath) and not overwrite:
            raise FileExistsError(f"File already exists: {filepath}")

        # Ensure directory exists
        directory = os.path.dirname(filepath)
        if directory:
            FileUtils.ensure_directory_exists(directory)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)

        logger.info(f"Wrote JSON file: {filepath}")

    @staticmethod
    def read_pickle_file(filepath: str) -> Any:
        """
        Read a pickle file.

        Args:
            filepath: Path to the file.

        Returns:
            Unpickled data.
        """
        with open(filepath, "rb") as f:
            return pickle.load(f)

    @staticmethod
    def write_pickle_file(filepath: str, data: Any, overwrite: bool = True) -> None:
        """
        Write to a pickle file.

        Args:
            filepath: Path to the file.
            data: Data to pickle.
            overwrite: Whether to overwrite if file exists.
        """
        if os.path.exists(filepath) and not overwrite:
            raise FileExistsError(f"File already exists: {filepath}")

        # Ensure directory exists
        directory = os.path.dirname(filepath)
        if directory:
            FileUtils.ensure_directory_exists(directory)

        with open(filepath, "wb") as f:
            pickle.dump(data, f)

        logger.info(f"Wrote pickle file: {filepath}")

    @staticmethod
    def read_csv_file(
        filepath: str,
        delimiter: str = ",",
    ) -> List[Dict[str, str]]:
        """
        Read a CSV file.

        Args:
            filepath: Path to the file.
            delimiter: Delimiter character.

        Returns:
            List of dictionaries (each representing a row).
        """
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            return list(reader)

    @staticmethod
    def write_csv_file(
        filepath: str,
        data: List[Dict[str, Any]],
        fieldnames: Optional[List[str]] = None,
        delimiter: str = ",",
        overwrite: bool = True,
    ) -> None:
        """
        Write to a CSV file.

        Args:
            filepath: Path to the file.
            data: List of dictionaries (each representing a row).
            fieldnames: Column names.
            delimiter: Delimiter character.
            overwrite: Whether to overwrite if file exists.
        """
        if os.path.exists(filepath) and not overwrite:
            raise FileExistsError(f"File already exists: {filepath}")

        # Ensure directory exists
        directory = os.path.dirname(filepath)
        if directory:
            FileUtils.ensure_directory_exists(directory)

        if not data:
            return

        if fieldnames is None:
            fieldnames = list(data[0].keys())

        with open(filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(data)

        logger.info(f"Wrote CSV file: {filepath}")

    @staticmethod
    def get_file_modification_time(filepath: str) -> float:
        """
        Get the modification time of a file.

        Args:
            filepath: Path to the file.

        Returns:
            Modification time as timestamp.
        """
        return os.path.getmtime(filepath)

    @staticmethod
    def get_file_creation_time(filepath: str) -> float:
        """
        Get the creation time of a file.

        Args:
            filepath: Path to the file.

        Returns:
            Creation time as timestamp.
        """
        return os.path.getctime(filepath)

    @staticmethod
    def is_file_empty(filepath: str) -> bool:
        """
        Check if a file is empty.

        Args:
            filepath: Path to the file.

        Returns:
            True if the file is empty, False otherwise.
        """
        return os.path.getsize(filepath) == 0

    @staticmethod
    def count_lines(filepath: str) -> int:
        """
        Count the number of lines in a file.

        Args:
            filepath: Path to the file.

        Returns:
            Number of lines.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            return sum(1 for _ in f)

    @staticmethod
    def get_file_hash(filepath: str, algorithm: str = "md5") -> str:
        """
        Get the hash of a file.

        Args:
            filepath: Path to the file.
            algorithm: Hash algorithm ('md5', 'sha1', 'sha256').

        Returns:
            Hash string.
        """
        import hashlib

        hash_func = getattr(hashlib, algorithm)()

        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)

        return hash_func.hexdigest()

    @staticmethod
    def compare_files(file1: str, file2: str) -> bool:
        """
        Compare two files.

        Args:
            file1: Path to the first file.
            file2: Path to the second file.

        Returns:
            True if files are identical, False otherwise.
        """
        return FileUtils.get_file_hash(file1) == FileUtils.get_file_hash(file2)
