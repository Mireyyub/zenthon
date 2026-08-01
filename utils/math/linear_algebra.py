"""
Linear Algebra Utilities Module
Provides linear algebra operations and utilities.
"""

import numpy as np
from typing import Union, Optional, Tuple

from core.logger import logger


class LinearAlgebraUtils:
    """
    Collection of linear algebra utilities.
    """

    @staticmethod
    def matrix_multiply(
        A: np.ndarray,
        B: np.ndarray,
    ) -> np.ndarray:
        """
        Multiply two matrices.

        Args:
            A: First matrix (m, n).
            B: Second matrix (n, p).

        Returns:
            Resulting matrix (m, p).
        """
        if A.shape[1] != B.shape[0]:
            raise ValueError(
                f"Matrix dimensions incompatible for multiplication: "
                f"A.shape={A.shape}, B.shape={B.shape}"
            )
        return np.dot(A, B)

    @staticmethod
    def matrix_inverse(
        A: np.ndarray,
    ) -> np.ndarray:
        """
        Compute the inverse of a square matrix.

        Args:
            A: Square matrix (n, n).

        Returns:
            Inverse matrix (n, n).
        """
        if A.shape[0] != A.shape[1]:
            raise ValueError(f"Matrix must be square. Got shape: {A.shape}")
        if np.linalg.det(A) == 0:
            raise ValueError("Matrix is singular, cannot compute inverse")
        return np.linalg.inv(A)

    @staticmethod
    def matrix_transpose(
        A: np.ndarray,
    ) -> np.ndarray:
        """
        Compute the transpose of a matrix.

        Args:
            A: Input matrix (m, n).

        Returns:
            Transposed matrix (n, m).
        """
        return A.T

    @staticmethod
    def vector_dot(
        a: np.ndarray,
        b: np.ndarray,
    ) -> float:
        """
        Compute the dot product of two vectors.

        Args:
            a: First vector (n,).
            b: Second vector (n,).

        Returns:
            Dot product (scalar).
        """
        if a.shape[0] != b.shape[0]:
            raise ValueError(
                f"Vector dimensions must match. Got: {a.shape[0]} and {b.shape[0]}"
            )
        return np.dot(a, b)

    @staticmethod
    def vector_norm(
        a: np.ndarray,
        ord: int = 2,
    ) -> float:
        """
        Compute the norm of a vector.

        Args:
            a: Input vector.
            ord: Order of the norm (1 for L1, 2 for L2, etc.).

        Returns:
            Norm of the vector.
        """
        return np.linalg.norm(a, ord=ord)

    @staticmethod
    def vector_normalize(
        a: np.ndarray,
        ord: int = 2,
    ) -> np.ndarray:
        """
        Normalize a vector to unit norm.

        Args:
            a: Input vector.
            ord: Order of the norm to use for normalization.

        Returns:
            Normalized vector.
        """
        norm = np.linalg.norm(a, ord=ord)
        if norm == 0:
            return a.copy()
        return a / norm

    @staticmethod
    def matrix_rank(
        A: np.ndarray,
        tol: float = 1e-10,
    ) -> int:
        """
        Compute the rank of a matrix.

        Args:
            A: Input matrix.
            tol: Tolerance for singular value decomposition.

        Returns:
            Rank of the matrix.
        """
        return np.linalg.matrix_rank(A, tol=tol)

    @staticmethod
    def matrix_determinant(
        A: np.ndarray,
    ) -> float:
        """
        Compute the determinant of a square matrix.

        Args:
            A: Square matrix (n, n).

        Returns:
            Determinant of the matrix.
        """
        if A.shape[0] != A.shape[1]:
            raise ValueError(f"Matrix must be square. Got shape: {A.shape}")
        return np.linalg.det(A)

    @staticmethod
    def eigenvalues(
        A: np.ndarray,
    ) -> np.ndarray:
        """
        Compute the eigenvalues of a square matrix.

        Args:
            A: Square matrix (n, n).

        Returns:
            Array of eigenvalues.
        """
        if A.shape[0] != A.shape[1]:
            raise ValueError(f"Matrix must be square. Got shape: {A.shape}")
        return np.linalg.eigvals(A)

    @staticmethod
    def eigenvectors(
        A: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute the eigenvalues and eigenvectors of a square matrix.

        Args:
            A: Square matrix (n, n).

        Returns:
            Tuple of (eigenvalues, eigenvectors).
        """
        if A.shape[0] != A.shape[1]:
            raise ValueError(f"Matrix must be square. Got shape: {A.shape}")
        eigenvalues, eigenvectors = np.linalg.eig(A)
        return eigenvalues, eigenvectors

    @staticmethod
    def svd(
        A: np.ndarray,
        full_matrices: bool = True,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Perform Singular Value Decomposition (SVD).

        Args:
            A: Input matrix (m, n).
            full_matrices: If True, return full matrices.

        Returns:
            Tuple of (U, s, Vh) where U and Vh are unitary matrices and s is a singular values vector.
        """
        return np.linalg.svd(A, full_matrices=full_matrices)

    @staticmethod
    def qr_decomposition(
        A: np.ndarray,
        mode: str = "reduced",
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Perform QR decomposition.

        Args:
            A: Input matrix (m, n).
            mode: Mode of decomposition ('reduced', 'complete', 'r', 'raw').

        Returns:
            Tuple of (Q, R) where Q is orthogonal and R is upper triangular.
        """
        return np.linalg.qr(A, mode=mode)

    @staticmethod
    def cholesky_decomposition(
        A: np.ndarray,
    ) -> np.ndarray:
        """
        Perform Cholesky decomposition.

        Args:
            A: Symmetric positive definite matrix (n, n).

        Returns:
            Upper triangular matrix L such that A = L * L.T.
        """
        if A.shape[0] != A.shape[1]:
            raise ValueError(f"Matrix must be square. Got shape: {A.shape}")
        return np.linalg.cholesky(A)

    @staticmethod
    def solve_linear_system(
        A: np.ndarray,
        b: np.ndarray,
    ) -> np.ndarray:
        """
        Solve a linear system Ax = b.

        Args:
            A: Coefficient matrix (n, n).
            b: Right-hand side vector (n,).

        Returns:
            Solution vector x (n,).
        """
        if A.shape[0] != A.shape[1]:
            raise ValueError(f"Matrix A must be square. Got shape: {A.shape}")
        if A.shape[0] != b.shape[0]:
            raise ValueError(
                f"Matrix A and vector b must have compatible dimensions. "
                f"Got: {A.shape[0]} and {b.shape[0]}"
            )
        return np.linalg.solve(A, b)

    @staticmethod
    def least_squares(
        A: np.ndarray,
        b: np.ndarray,
    ) -> np.ndarray:
        """
        Solve a least squares problem.

        Args:
            A: Coefficient matrix (m, n).
            b: Right-hand side vector (m,).

        Returns:
            Solution vector x (n,) that minimizes ||Ax - b||^2.
        """
        return np.linalg.lstsq(A, b, rcond=None)[0]

    @staticmethod
    def cosine_similarity(
        a: np.ndarray,
        b: np.ndarray,
    ) -> float:
        """
        Compute cosine similarity between two vectors.

        Args:
            a: First vector.
            b: Second vector.

        Returns:
            Cosine similarity (between -1 and 1).
        """
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    @staticmethod
    def euclidean_distance(
        a: np.ndarray,
        b: np.ndarray,
    ) -> float:
        """
        Compute Euclidean distance between two vectors.

        Args:
            a: First vector.
            b: Second vector.

        Returns:
            Euclidean distance.
        """
        return np.linalg.norm(a - b)

    @staticmethod
    def manhattan_distance(
        a: np.ndarray,
        b: np.ndarray,
    ) -> float:
        """
        Compute Manhattan distance between two vectors.

        Args:
            a: First vector.
            b: Second vector.

        Returns:
            Manhattan distance.
        """
        return np.sum(np.abs(a - b))
