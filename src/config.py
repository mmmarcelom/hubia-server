"""
Configurações do servidor HubIA Workflow
"""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """Configurações do servidor"""
    
    # Server Configuration
    api_url: str
    server_name: str
    slug: str
    server_id: str
    server_key: Optional[str]
    
    # Ollama Configuration
    ollama_base_url: str
    ollama_model_transcricao: str
    ollama_model_visao: str
    ollama_model_conversacao: str
    ollama_model_embeddings: str
    ollama_model_resumo: str
    
    # Processing Configuration
    max_audio_size_mb: int
    max_image_size_mb: int
    max_document_size_mb: int
    max_text_length: int
    
    # Logging
    log_level: str
    log_file: str
    
    # GPU Configuration
    cuda_visible_devices: str
    torch_device: str
    
    # Polling Configuration
    polling_interval_seconds: int
    max_retries: int
    retry_delay_seconds: int
    
    def __init__(self):
        """Inicializa configurações a partir das variáveis de ambiente"""
        # Server Configuration
        self.api_url = os.getenv("API_URL", "http://localhost:3000")
        self.server_name = os.getenv("SERVER_NAME", "Servidor Local HubIA")
        self.slug = os.getenv("SLUG", "mvml")
        self.server_key = os.getenv("SERVER_KEY")
        
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
        self.ollama_model_transcricao = os.getenv("OLLAMA_MODEL_TRANSCRICAO", "gemma2:9b")
        self.ollama_model_visao = os.getenv("OLLAMA_MODEL_VISAO", "llava:7b")
        self.ollama_model_conversacao = os.getenv("OLLAMA_MODEL_CONVERSACAO", "gemma2:9b")
        self.ollama_model_embeddings = os.getenv("OLLAMA_MODEL_EMBEDDINGS", "nomic-embed-text")
        self.ollama_model_resumo = os.getenv("OLLAMA_MODEL_RESUMO", "gemma2:9b")
        
        self.max_audio_size_mb = int(os.getenv("MAX_AUDIO_SIZE_MB", "50"))
        self.max_image_size_mb = int(os.getenv("MAX_IMAGE_SIZE_MB", "20"))
        self.max_document_size_mb = int(os.getenv("MAX_DOCUMENT_SIZE_MB", "10"))
        self.max_text_length = int(os.getenv("MAX_TEXT_LENGTH", "10000"))
        
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE", "/app/logs/workflow_server.log")
        
        self.cuda_visible_devices = os.getenv("CUDA_VISIBLE_DEVICES", "0")
        self.torch_device = os.getenv("TORCH_DEVICE", "cuda")
        
        self.polling_interval_seconds = int(os.getenv("POLLING_INTERVAL_SECONDS", "5"))
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.retry_delay_seconds = int(os.getenv("RETRY_DELAY_SECONDS", "10"))
    
    @property
    def max_audio_size_bytes(self) -> int:
        """Retorna o tamanho máximo de áudio em bytes"""
        return self.max_audio_size_mb * 1024 * 1024
    
    @property
    def max_image_size_bytes(self) -> int:
        """Retorna o tamanho máximo de imagem em bytes"""
        return self.max_image_size_mb * 1024 * 1024
    
    @property
    def max_document_size_bytes(self) -> int:
        """Retorna o tamanho máximo de documento em bytes"""
        return self.max_document_size_mb * 1024 * 1024
