"""
Processador de prompt para geração de resposta usando Ollama Gemma
"""

import httpx
from typing import Dict, Any, List
from .base64_processor import Base64Processor
# TaskType enum values
PROMPT = "prompt"

class PromptProcessor(Base64Processor):
    """Processador de prompt para geração de resposta"""
    
    def __init__(self, config):
        super().__init__(config)
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa prompt e retorna resposta"""
        try:
            # Extract prompt from content field
            if 'content' not in data:
                raise ValueError("Campo 'content' não encontrado nos dados")
            
            prompt = data['content']
            
            # Validate text length
            if len(prompt) > self.config.max_text_length:
                raise ValueError(f"Prompt muito longo: {len(prompt)} caracteres (máximo: {self.config.max_text_length})")
            
            # Generate response using Ollama
            result = await self._generate_response_with_ollama(prompt)
            
            return result
            
        except Exception as e:
            print(f"❌ Erro no processamento de prompt: {e}")
            raise
    
    async def _generate_response_with_ollama(self, prompt: str) -> Dict[str, Any]:
        """Gera resposta usando Ollama Gemma"""
        try:
            print(f"💬 Gerando resposta com Ollama Gemma...")
            
            # Ollama API request
            ollama_url = f"{self.config.ollama_base_url}/api/generate"
            
            payload = {
                "model": self.config.ollama_model_conversacao,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 1000
                }
            }
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(ollama_url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                response_text = result.get("response", "").strip()
                
                if not response_text:
                    raise ValueError("Resposta vazia retornada pelo modelo")
                
                # Get model info
                model_name = result.get("model", self.config.ollama_model_conversacao)
                
                # Estimate tokens
                tokens = len(response_text.split()) * 1.3  # Rough estimate
                
                print(f"✅ Resposta gerada: {len(response_text)} caracteres")
                
                return {
                    "response": response_text,
                    "confidence": 0.8,  # Base confidence
                    "sources": [],  # No sources for simple prompt
                    "tokens": int(tokens),
                    "model": model_name,
                    "success": True
                }
                
        except httpx.HTTPError as e:
            print(f"❌ Erro HTTP na geração de resposta: {e}")
            raise ValueError(f"Erro na comunicação com Ollama: {e}")
        except Exception as e:
            print(f"❌ Erro na geração de resposta: {e}")
            raise ValueError(f"Erro na geração de resposta: {e}")
