"""
Processador de prompt para geração de resposta usando Ollama Gemma
"""

import httpx
from typing import Dict, Any, List
from .base_processor import BaseProcessor
# TaskType enum values
PROMPT = "prompt"

class PromptProcessor(BaseProcessor):
    """Processador de prompt para geração de resposta"""
    
    def __init__(self, config):
        super().__init__(config)
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa prompt e retorna resposta"""
        try:
            # Extract message from content field or message field
            if 'content' in data:
                message = data['content']
            elif 'message' in data:
                message = data['message']
            else:
                raise ValueError("Campo 'content' ou 'message' não encontrado nos dados")
            
            # Validate text length
            total_text_length = len(message)
            if 'context' in data and data['context']:
                for context_item in data['context']:
                    total_text_length += len(context_item['content'])
            
            if total_text_length > self.config.max_text_length:
                raise ValueError(f"Prompt muito longo: {total_text_length} caracteres (máximo: {self.config.max_text_length})")
            
            # Prepare data for prompt processing
            prompt_data = data.copy()
            prompt_data['message'] = message
            prompt_data['userMessage'] = message  # For compatibility
            
            # Generate response using Ollama
            result = await self._generate_response_with_ollama(prompt_data)
            
            # Convert to dict
            return result
            
        except Exception as e:
            print(f"❌ Erro no processamento de prompt: {e}")
            raise
    
    async def _generate_response_with_ollama(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Gera resposta usando Ollama Gemma"""
        try:
            print(f"💬 Gerando resposta com Ollama Gemma...")
            
            # Build the complete prompt
            full_prompt = self._build_prompt(prompt_data)
            
            # Ollama API request
            ollama_url = f"{self.config.ollama_base_url}/api/generate"
            
            payload = {
                "model": self.config.ollama_model_conversacao,
                "prompt": full_prompt,
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
                
                # Parse response and extract sources
                parsed_result = self._parse_response(response_text, prompt_data.context)
                
                # Get model info
                model_name = result.get("model", self.config.ollama_model_prompt)
                
                # Estimate tokens
                tokens = len(response_text.split()) * 1.3  # Rough estimate
                
                print(f"✅ Resposta gerada: {len(response_text)} caracteres")
                
                return {
                    "response": parsed_result["response"],
                    "confidence": parsed_result["confidence"],
                    "sources": parsed_result["sources"],
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
    
    def _build_prompt(self, prompt_data: Dict[str, Any]) -> str:
        """Constrói o prompt completo para o modelo"""
        
        # System prompt
        system_prompt = f"""Você é um assistente virtual especializado. {prompt_data.clientPrompt}

Instruções:
- Responda sempre em português brasileiro
- Seja útil, preciso e amigável
- Use as informações de contexto fornecidas
- Se não souber algo, seja honesto sobre isso
- Mantenha respostas concisas mas completas"""
        
        # Context information
        context_text = ""
        if prompt_data.context:
            context_text = "\n\nINFORMAÇÕES DE CONTEXTO:\n"
            for i, context_item in enumerate(prompt_data.context, 1):
                context_text += f"{i}. {context_item.content} (Relevância: {context_item.relevance:.2f})\n"
        
        # Conversation history
        history_text = ""
        if prompt_data.conversationHistory:
            history_text = "\n\nHISTÓRICO DA CONVERSA:\n"
            for msg in prompt_data.conversationHistory[-5:]:  # Last 5 messages
                role = "Usuário" if msg.role == "user" else "Assistente"
                history_text += f"{role}: {msg.content}\n"
        
        # Current user message
        user_message = f"\n\nMENSAGEM ATUAL DO USUÁRIO:\n{prompt_data.userMessage}"
        
        # Final instruction
        final_instruction = "\n\nPor favor, responda à mensagem do usuário de forma útil e contextualizada:"
        
        # Combine all parts
        full_prompt = (
            system_prompt +
            context_text +
            history_text +
            user_message +
            final_instruction
        )
        
        return full_prompt
    
    def _parse_response(self, response_text: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse a resposta e identifica fontes utilizadas"""
        try:
            # Simple source identification based on content similarity
            used_sources = []
            
            # Check which context items were likely used
            response_lower = response_text.lower()
            
            for context_item in context:
                # Simple keyword matching (in a real implementation, you'd use more sophisticated NLP)
                context_words = set(context_item.content.lower().split())
                response_words = set(response_lower.split())
                
                # Calculate overlap
                overlap = len(context_words.intersection(response_words))
                total_context_words = len(context_words)
                
                if total_context_words > 0:
                    overlap_ratio = overlap / total_context_words
                    
                    # If significant overlap, consider this source used
                    if overlap_ratio > 0.1:  # 10% overlap threshold
                        used_sources.append(context_item)
            
            # Estimate confidence based on response quality indicators
            confidence = 0.8  # Base confidence
            
            # Increase confidence if response is substantial
            if len(response_text) > 50:
                confidence += 0.1
            
            # Increase confidence if sources were used
            if used_sources:
                confidence += 0.05
            
            # Decrease confidence if response seems incomplete
            if response_text.endswith("...") or len(response_text) < 20:
                confidence -= 0.1
            
            confidence = min(0.95, max(0.5, confidence))
            
            return {
                "response": response_text,
                "confidence": confidence,
                "sources": used_sources[:3]  # Limit to top 3 sources
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao fazer parse da resposta: {e}")
            # Fallback
            return {
                "response": response_text,
                "confidence": 0.8,
                "sources": []
            }
