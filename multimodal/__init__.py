"""
Leon multimodal – image processing + optional VLM describe + procedural generation.

Honest limits:
- Full photoreal generation requires external models (not claimed).
- Vision describe needs Ollama vision model (e.g. llava, moondream).
- Classic ops work with Pillow when installed.
"""

from multimodal.image_ops import image_info, process_image, list_supported
from multimodal.vision import describe_image, vision_available
from multimodal.generate import generate_image, generate_card

__all__ = [
    "image_info",
    "process_image",
    "list_supported",
    "describe_image",
    "vision_available",
    "generate_image",
    "generate_card",
]
