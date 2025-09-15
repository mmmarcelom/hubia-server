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
            
            # Extract text from content field
            if 'content' in data:
                text_content = data['content']
            elif 'text' in data:
                text_content = data['text']
            else:
                raise ValueError("Campo 'content' ou 'text' não encontrado nos dados")
            
            # Validate text length
            if len(text_content) > self.config.max_text_length:
                raise ValueError(f"Texto muito longo: {len(text_content)} caracteres (máximo: {self.config.max_text_length})")
            
            # Generate embedding using Ollama
            result = await self._generate_embedding_with_ollama(text_content)
            
            # Convert to dict
            return result
            
        except Exception as e:
            print(f"❌ Erro no processamento de texto: {e}")
            raise
    
    async def _generate_embedding_with_ollama(self, text_content: str) -> Dict[str, Any]:
        """Gera embedding usando Ollama"""
        try:
            
            ollama_url = f"{self.config.ollama_base_url}/api/embeddings"
            payload = { 
                "model": self.config.ollama_model_embeddings, 
                "prompt": text_content,
                "options": {
                    "dimensions": 1536
                }
            }
                        
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(ollama_url, json=payload)
                
                print(f"🔍 Status da resposta: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"❌ Erro HTTP: {response.status_code}")
                    print(f"❌ Resposta: {response.text}")
                    raise ValueError(f"Erro HTTP {response.status_code}: {response.text}")
                
                result = response.json()
                
                print(f"🔍 Resposta do Ollama: {result}")
                
                embedding = result.get("embedding", [])
                
                if not embedding:
                    print(f"❌ Embedding vazio. Resposta completa: {result}")
                    raise ValueError("Embedding vazio retornado pelo modelo")
                
                # Validate dimensions - accept 768 or 1536
                if len(embedding) not in [768, 1536]:
                    print(f"❌ Dimensões incorretas: {len(embedding)} (esperado: 768 ou 1536)")
                    raise ValueError(f"Embedding com dimensões incorretas: {len(embedding)} (esperado: 768 ou 1536)")
                
                # If 768 dimensions, pad to 1536
                if len(embedding) == 768:
                    print(f"⚠️ Embedding com 768 dimensões, preenchendo para 1536")
                    # Pad with zeros to reach 1536 dimensions
                    embedding = embedding + [0.0] * (1536 - 768)
                
                # Get model info
                model_name = result.get("model", self.config.ollama_model_embeddings)
                
                # Estimate tokens (rough approximation)
                tokens = len(text_content.split()) * 1.3  # Rough estimate
                
                print(f"✅ Embedding final com {len(embedding)} dimensões")
                
                return {
                    "embedding": embedding,
                    "model": model_name,
                    "dimensions": 1536,  # Always 1536
                    "tokens": int(tokens),
                    "success": True
                }
                
        except httpx.HTTPError as e:
            print(f"❌ Erro HTTP na geração de embedding: {e}")
            raise ValueError(f"Erro na comunicação com Ollama: {e}")
        except Exception as e:
            print(f"❌ Erro na geração de embedding: {e}")
            raise ValueError(f"Erro na geração de embedding: {e}")
