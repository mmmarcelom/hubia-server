"""
Processador base para todos os tipos de mídia
"""

import base64
import tempfile
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from config import Config


class BaseProcessor(ABC):
    """Classe base para todos os processadores"""
    
    def __init__(self, config: Config):
        self.config = config
        self.temp_dir = tempfile.mkdtemp()
    
    def decode_base64_data(self, data: str, file_extension: str) -> str:
        """Decodifica dados base64 e salva em arquivo temporário"""
        try:
            # Remove data URL prefix if present
            if data.startswith('data:'):
                data = data.split(',')[1]
            
            # Decode base64
            file_data = base64.b64decode(data)
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(
                suffix=f".{file_extension}",
                delete=False,
                dir=self.temp_dir
            )
            temp_file.write(file_data)
            temp_file.close()
            
            print(f"📄 Arquivo temporário criado: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            print(f"❌ Erro ao decodificar dados base64: {e}")
            raise ValueError(f"Erro ao decodificar dados: {e}")
    
    def validate_file_size(self, file_size: int, max_size_bytes: int) -> None:
        """Valida o tamanho do arquivo"""
        if file_size > max_size_bytes:
            max_size_mb = max_size_bytes / (1024 * 1024)
            file_size_mb = file_size / (1024 * 1024)
            raise ValueError(f"Arquivo muito grande: {file_size_mb:.2f}MB (máximo: {max_size_mb:.2f}MB)")
    
    def validate_mime_type(self, mime_type: str, allowed_types: list) -> None:
        """Valida o tipo MIME do arquivo"""
        if mime_type not in allowed_types:
            raise ValueError(f"Tipo MIME não suportado: {mime_type}. Tipos permitidos: {allowed_types}")
    
    @abstractmethod
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa os dados e retorna o resultado"""
        pass
    
    def cleanup_temp_file(self, file_path: str) -> None:
        """Remove arquivo temporário"""
        try:
            import os
            if os.path.exists(file_path):
                os.unlink(file_path)
                print(f"🗑️ Arquivo temporário removido: {file_path}")
        except Exception as e:
            print(f"⚠️ Erro ao remover arquivo temporário {file_path}: {e}")
    
    def __del__(self):
        """Limpa arquivos temporários ao destruir o objeto"""
        try:
            import shutil
            if hasattr(self, 'temp_dir') and self.temp_dir:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            print(f"⚠️ Erro ao remover diretório temporário: {e}")
