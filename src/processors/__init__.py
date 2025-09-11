"""
Processadores de mídia para o sistema de workflow
"""

from processors.base_processor import BaseProcessor
from processors.audio_processor import AudioProcessor
from processors.image_processor import ImageProcessor
from processors.document_processor import DocumentProcessor
from processors.text_processor import TextProcessor
from processors.prompt_processor import PromptProcessor

__all__ = [
    "BaseProcessor",
    "AudioProcessor", 
    "ImageProcessor",
    "DocumentProcessor",
    "TextProcessor",
    "PromptProcessor"
]
