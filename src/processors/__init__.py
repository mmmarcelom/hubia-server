"""
Processadores de mídia para o sistema de workflow
"""

from processors.base64_processor import Base64Processor
from processors.audio_processor import AudioProcessor
from processors.image_processor import ImageProcessor
from processors.document_processor import DocumentProcessor
from processors.embedding_processor import EmbeddingProcessor
from processors.prompt_processor import PromptProcessor

__all__ = [
    "Base64Processor",
    "AudioProcessor", 
    "ImageProcessor",
    "DocumentProcessor",
    "EmbeddingProcessor",
    "PromptProcessor"
]
