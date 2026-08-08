"""Multimodal: vision, image ops, generate, understand, audio/speech."""

from multimodal.image_ops import image_info, process_image, list_supported
from multimodal.vision import describe_image, vision_available
from multimodal.generate import generate_image
from multimodal.understand import understand_image

try:
    from multimodal.audio import (
        audio_info,
        audio_available,
        understand_speech,
        generate_speech,
        make_tone_wav,
    )
except Exception:  # pragma: no cover
    audio_info = audio_available = understand_speech = generate_speech = make_tone_wav = None  # type: ignore

__all__ = [
    "image_info",
    "process_image",
    "list_supported",
    "describe_image",
    "vision_available",
    "generate_image",
    "understand_image",
    "audio_info",
    "audio_available",
    "understand_speech",
    "generate_speech",
    "make_tone_wav",
]
