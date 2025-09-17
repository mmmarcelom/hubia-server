"""
Processador de embeddings para geração de vetores usando Ollama
"""

import httpx
from typing import Dict, Any, List
from .base64_processor import Base64Processor
# TaskType enum values
EMBEDDING = "embedding"

class EmbeddingProcessor(Base64Processor):
    """Processador de embeddings para geração de vetores"""
    
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
            
            # Determine dimensions based on action type
            dimensions = 768 if data.get('action') == 'knowledge' else 1536
            
            # Generate embedding using Ollama
            result = await self._generate_embedding_with_ollama(text_content, dimensions)
            
            # Convert to dict
            return result
            
        except Exception as e:
            print(f"❌ Erro no processamento de embedding: {e}")
            raise
    
    async def _generate_embedding_with_ollama(self, text_content: str, dimensions: int = 1536) -> Dict[str, Any]:
        """Gera embedding usando Ollama"""
        try:
            
            ollama_url = f"{self.config.ollama_base_url}/api/embeddings"
            payload = { 
                "model": self.config.ollama_model_embeddings, 
                "prompt": text_content,
                "options": { "dimensions": dimensions }
            }
                        
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(ollama_url, json=payload)
                
                print(f"🔍 Status da resposta: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"❌ Erro HTTP: {response.status_code}")
                    print(f"❌ Resposta: {response.text}")
                    raise ValueError(f"Erro HTTP {response.status_code}: {response.text}")
                
                result = response.json()
                
                embedding = result.get("embedding", [])
                
                if not embedding:
                    print(f"❌ Embedding vazio. Resposta completa: {result}")
                    raise ValueError("Embedding vazio retornado pelo modelo")
                
                # Validate dimensions - accept original dimensions from model
                if len(embedding) <= 0:
                    print(f"❌ Embedding inválido: {len(embedding)} dimensões")
                    raise ValueError(f"Embedding inválido: {len(embedding)} dimensões")
                
                # Log if dimensions don't match expected
                if len(embedding) != dimensions:
                    print(f"⚠️ Embedding recebido com {len(embedding)} dimensões, esperado {dimensions}")
                
                print(f"✅ Embedding recebido com {len(embedding)} dimensões")
                
                # Get model info
                model_name = result.get("model", self.config.ollama_model_embeddings)
                
                # Estimate tokens (rough approximation)
                tokens = len(text_content.split()) * 1.3  # Rough estimate
                
                print(f"✅ Embedding final com {len(embedding)} dimensões")
                
                return {
                    "embedding": embedding,
                    "model": model_name,
                    "dimensions": len(embedding),  # Real dimensions from model
                    "tokens": int(tokens),
                    "success": True
                }
                
        except httpx.HTTPError as e:
            print(f"❌ Erro HTTP na geração de embedding: {e}")
            raise ValueError(f"Erro na comunicação com Ollama: {e}")
        except Exception as e:
            print(f"❌ Erro na geração de embedding: {e}")
            raise ValueError(f"Erro na geração de embedding: {e}")
