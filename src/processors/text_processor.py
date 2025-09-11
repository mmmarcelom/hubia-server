"""
Processador de texto para geração de embeddings usando Ollama
"""

import httpx
from typing import Dict, Any, List
from .base_processor import BaseProcessor
# TaskType enum values
EMBEDDING = "embedding"

class TextProcessor(BaseProcessor):
    """Processador de texto para geração de embeddings"""
    
    def __init__(self, config):
        super().__init__(config)
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa texto e retorna embedding"""
        try:
            # Validate text length
            if len(data['text']) > self.config.max_text_length:
                raise ValueError(f"Texto muito longo: {len(data['text'])} caracteres (máximo: {self.config.max_text_length})")
            
            # Generate embedding using Ollama
            result = await self._generate_embedding_with_ollama(data)
            
            # Convert to dict
            return result
            
        except Exception as e:
            print(f"❌ Erro no processamento de texto: {e}")
            raise
    
    async def _generate_embedding_with_ollama(self, embedding_data: Dict[str, Any]) -> Dict[str, Any]:
        """Gera embedding usando Ollama"""
        try:
            print(f"🔍 Gerando embedding com Ollama...")
            
            # Ollama API request for embeddings
            ollama_url = f"{self.config.ollama_base_url}/api/embeddings"
            
            payload = {
                "model": self.config.ollama_model_embeddings,
                "prompt": embedding_data.content
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(ollama_url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                embedding = result.get("embedding", [])
                
                if not embedding:
                    raise ValueError("Embedding vazio retornado pelo modelo")
                
                # Get model info
                model_name = result.get("model", self.config.ollama_model_embedding)
                dimensions = len(embedding)
                
                # Estimate tokens (rough approximation)
                tokens = len(embedding_data.content.split()) * 1.3  # Rough estimate
                
                print(f"✅ Embedding gerado: {dimensions} dimensões")
                
                return {
                    "embedding": embedding,
                    "model": model_name,
                    "dimensions": dimensions,
                    "tokens": int(tokens),
                    "success": True
                }
                
        except httpx.HTTPError as e:
            print(f"❌ Erro HTTP na geração de embedding: {e}")
            raise ValueError(f"Erro na comunicação com Ollama: {e}")
        except Exception as e:
            print(f"❌ Erro na geração de embedding: {e}")
            raise ValueError(f"Erro na geração de embedding: {e}")
