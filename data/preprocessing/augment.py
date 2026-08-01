"""
Data Augmentation Module
Provides data augmentation techniques for images, text, and tabular data.
"""

import numpy as np
import random
from typing import Union, List, Optional, Tuple
from PIL import Image
import cv2

from core.logger import logger


class ImageAugmenter:
    """Provides image augmentation techniques."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def rotate(
        self,
        image: Union[np.ndarray, Image.Image],
        angle: float = 15.0,
    ) -> Union[np.ndarray, Image.Image]:
        """
        Rotate an image by a specified angle.

        Args:
            image: Input image (numpy array or PIL Image).
            angle: Rotation angle in degrees.

        Returns:
            Rotated image.
        """
        if isinstance(image, Image.Image):
            rotated = image.rotate(angle)
        else:
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(image, M, (w, h))

        if self.verbose:
            logger.info(f"Rotated image by {angle} degrees.")

        return rotated

    def flip(
        self,
        image: Union[np.ndarray, Image.Image],
        mode: str = "horizontal",
    ) -> Union[np.ndarray, Image.Image]:
        """
        Flip an image horizontally or vertically.

        Args:
            image: Input image.
            mode: Flip mode ('horizontal', 'vertical', 'both').

        Returns:
            Flipped image.
        """
        if isinstance(image, Image.Image):
            if mode == "horizontal":
                flipped = image.transpose(Image.FLIP_LEFT_RIGHT)
            elif mode == "vertical":
                flipped = image.transpose(Image.FLIP_TOP_BOTTOM)
            elif mode == "both":
                flipped = image.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.FLIP_TOP_BOTTOM)
            else:
                raise ValueError(f"Unknown flip mode: {mode}")
        else:
            if mode == "horizontal":
                flipped = cv2.flip(image, 1)
            elif mode == "vertical":
                flipped = cv2.flip(image, 0)
            elif mode == "both":
                flipped = cv2.flip(cv2.flip(image, 1), 0)
            else:
                raise ValueError(f"Unknown flip mode: {mode}")

        if self.verbose:
            logger.info(f"Flipped image {mode}ly.")

        return flipped

    def resize(
        self,
        image: Union[np.ndarray, Image.Image],
        size: Tuple[int, int],
    ) -> Union[np.ndarray, Image.Image]:
        """
        Resize an image to specified dimensions.

        Args:
            image: Input image.
            size: Target size as (width, height).

        Returns:
            Resized image.
        """
        if isinstance(image, Image.Image):
            resized = image.resize(size)
        else:
            resized = cv2.resize(image, (size[0], size[1]))

        if self.verbose:
            logger.info(f"Resized image to {size}.")

        return resized

    def add_noise(
        self,
        image: Union[np.ndarray, Image.Image],
        noise_type: str = "gaussian",
        intensity: float = 0.1,
    ) -> Union[np.ndarray, Image.Image]:
        """
        Add noise to an image.

        Args:
            image: Input image.
            noise_type: Type of noise ('gaussian', 'salt_pepper').
            intensity: Intensity of the noise.

        Returns:
            Noisy image.
        """
        if isinstance(image, Image.Image):
            image = np.array(image)

        if noise_type == "gaussian":
            noise = np.random.normal(0, intensity, image.shape)
            noisy = np.clip(image + noise, 0, 255).astype(np.uint8)
        elif noise_type == "salt_pepper":
            noisy = image.copy()
            num_salt = int(np.prod(image.shape) * intensity)
            coords = [np.random.randint(0, i - 1, num_salt) for i in image.shape]
            noisy[coords[0], coords[1], :] = 255
            num_pepper = int(np.prod(image.shape) * intensity)
            coords = [np.random.randint(0, i - 1, num_pepper) for i in image.shape]
            noisy[coords[0], coords[1], :] = 0
        else:
            raise ValueError(f"Unknown noise type: {noise_type}")

        if self.verbose:
            logger.info(f"Added {noise_type} noise with intensity {intensity}.")

        return noisy

    def random_crop(
        self,
        image: Union[np.ndarray, Image.Image],
        crop_size: Tuple[int, int],
    ) -> Union[np.ndarray, Image.Image]:
        """
        Randomly crop an image to specified dimensions.

        Args:
            image: Input image.
            crop_size: Target crop size as (width, height).

        Returns:
            Cropped image.
        """
        if isinstance(image, Image.Image):
            image = np.array(image)

        h, w = image.shape[:2]
        crop_w, crop_h = crop_size

        if crop_w > w or crop_h > h:
            raise ValueError(f"Crop size {crop_size} is larger than image size {(w, h)}.")

        x = np.random.randint(0, w - crop_w)
        y = np.random.randint(0, h - crop_h)

        cropped = image[y:y + crop_h, x:x + crop_w]

        if self.verbose:
            logger.info(f"Randomly cropped image to {crop_size}.")

        return cropped

    def apply_random_augmentations(
        self,
        image: Union[np.ndarray, Image.Image],
        num_augmentations: int = 3,
    ) -> Union[np.ndarray, Image.Image]:
        """
        Apply a random set of augmentations to an image.

        Args:
            image: Input image.
            num_augmentations: Number of augmentations to apply.

        Returns:
            Augmented image.
        """
        augmentations = [
            ("rotate", {"angle": random.uniform(-30, 30)}),
            ("flip", {"mode": random.choice(["horizontal", "vertical", "both"])}),
            ("add_noise", {"noise_type": random.choice(["gaussian", "salt_pepper"]), "intensity": random.uniform(0.05, 0.2)}),
        ]

        for _ in range(num_augmentations):
            aug_name, params = random.choice(augmentations)
            aug_method = getattr(self, aug_name)
            image = aug_method(image, **params)

        if self.verbose:
            logger.info(f"Applied {num_augmentations} random augmentations.")

        return image


class TextAugmenter:
    """Provides text augmentation techniques."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def synonym_replacement(self, text: str, n: int = 1) -> str:
        """
        Replace words with their synonyms.

        Args:
            text: Input text.
            n: Number of words to replace.

        Returns:
            Augmented text.
        """
        # TODO: Implement synonym replacement using WordNet or similar
        if self.verbose:
            logger.info(f"Applied synonym replacement to text.")
        return text

    def random_deletion(self, text: str, p: float = 0.1) -> str:
        """
        Randomly delete words from the text.

        Args:
            text: Input text.
            p: Probability of deleting a word.

        Returns:
            Augmented text.
        """
        words = text.split()
        if len(words) == 0:
            return text

        new_words = []
        for word in words:
            if random.random() > p:
                new_words.append(word)

        augmented_text = " ".join(new_words)

        if self.verbose:
            logger.info(f"Applied random deletion to text.")

        return augmented_text

    def random_swap(self, text: str, n: int = 1) -> str:
        """
        Randomly swap words in the text.

        Args:
            text: Input text.
            n: Number of swaps to perform.

        Returns:
            Augmented text.
        """
        words = text.split()
        if len(words) < 2:
            return text

        for _ in range(n):
            idx1, idx2 = random.sample(range(len(words)), 2)
            words[idx1], words[idx2] = words[idx2], words[idx1]

        augmented_text = " ".join(words)

        if self.verbose:
            logger.info(f"Applied random swap to text.")

        return augmented_text

    def random_insertion(self, text: str, n: int = 1) -> str:
        """
        Randomly insert words into the text.

        Args:
            text: Input text.
            n: Number of words to insert.

        Returns:
            Augmented text.
        """
        words = text.split()
        if len(words) == 0:
            return text

        for _ in range(n):
            idx = random.randint(0, len(words))
            synonym = words[random.randint(0, len(words) - 1)]  # Simple approach: use existing word
            words.insert(idx, synonym)

        augmented_text = " ".join(words)

        if self.verbose:
            logger.info(f"Applied random insertion to text.")

        return augmented_text

    def apply_random_augmentations(self, text: str, num_augmentations: int = 2) -> str:
        """
        Apply a random set of augmentations to the text.

        Args:
            text: Input text.
            num_augmentations: Number of augmentations to apply.

        Returns:
            Augmented text.
        """
        augmentations = [
            ("synonym_replacement", {"n": 1}),
            ("random_deletion", {"p": 0.1}),
            ("random_swap", {"n": 1}),
            ("random_insertion", {"n": 1}),
        ]

        for _ in range(num_augmentations):
            aug_name, params = random.choice(augmentations)
            aug_method = getattr(self, aug_name)
            text = aug_method(text, **params)

        if self.verbose:
            logger.info(f"Applied {num_augmentations} random text augmentations.")

        return text


# Global augmenter instances
image_augmenter = ImageAugmenter()
text_augmenter = TextAugmenter()
