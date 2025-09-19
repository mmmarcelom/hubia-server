"""
Cliente de workflow para polling e processamento de tarefas
"""

import asyncio
import json
from typing import Dict, Any, Optional
import httpx

# TaskType enum values
EMBEDDING = "embedding"
TRANSCRIBE = "transcribe"
DESCRIBE = "describe"
SUMMARIZE = "summarize"
PROMPT = "prompt"
KNOWLEDGE = "knowledge"

from processors import (AudioProcessor, ImageProcessor, DocumentProcessor, EmbeddingProcessor, PromptProcessor)
from config import Config

class WorkflowClient:
    """Cliente para comunicação com o sistema de workflow do HubIA"""
    
    def __init__(self, config: Config):
        self.config = config
        self.is_running = False
        self.server_key = None
        
        # Initialize processors
        self.processors = {
            TRANSCRIBE: AudioProcessor(config),
            DESCRIBE: ImageProcessor(config),
            SUMMARIZE: DocumentProcessor(config),
            EMBEDDING: EmbeddingProcessor(config),
            PROMPT: PromptProcessor(config),
            KNOWLEDGE: EmbeddingProcessor(config)
        }
    
    async def start(self):
        """Inicia o loop de polling para trabalho"""
        self.is_running = True
        self.server_key = self.config.server_key
        
        try:
            
            # Inicia o loop de polling
            while self.is_running:
                try:
                    await self._polling()
                except asyncio.CancelledError:
                    print("🛑 Cliente cancelado")
                    break
                except Exception as e:
                    print(f"❌ Erro no polling: {e}")
                    try:
                        await self._sleep(self.config.retry_delay_seconds)
                    except asyncio.CancelledError:
                        print("🛑 Cliente cancelado durante sleep")
                        break
        except KeyboardInterrupt:
            print("⏹️ Cliente interrompido pelo usuário")
        except asyncio.CancelledError:
            print("🛑 Cliente cancelado")
        finally:
            self.is_running = False
    
    async def _polling(self):
        """Faz polling para buscar trabalho disponível"""
        try:
            # Etapa 1: Fazer a requisição
            response = await self._polling_request()
            if response is None:
                return
            
            # Etapa 2: Processar a resposta
            await self._process_polling_response(response)
            
        except Exception as e:
            print(f"❌ Erro inesperado no polling: {e}")
            try:
                await self._sleep(self.config.retry_delay_seconds)
            except asyncio.CancelledError:
                print("🛑 Polling cancelado")
                raise
    
    async def _polling_request(self):
        """Etapa 1: Faz a requisição para buscar trabalho"""
        try:
            print("🔍 Pooling:", end=" ")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{self.config.api_url}/workflow/tasks"
                headers = {"x-server-token": self.server_key}
                response = await client.get(url, headers=headers)
                
                response.raise_for_status()
                return response

        except httpx.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                if status_code == 500:
                    print("⚠️  Erro 500")
                    print(e.response.json()['message'])
                elif status_code == 404:
                    print("⚠️ Erro 404")
                    print("Endpoint não encontrado")
                elif status_code == 401:
                    print("❌ Token de servidor inválido (erro 401)")
                    return None
                else:
                    print(f"❌ Erro HTTP {status_code} no polling: {e}")
            else:
                print(f"❌ Erro de conexão: {e}")

            await self._sleep(self.config.retry_delay_seconds)
            return None
    
    async def _process_polling_response(self, response):
        """Etapa 2: Processa a resposta e chama o processamento da tarefa"""
        try:

            json_response = response.json()
            
            if json_response['success'] == False:
                print(f"⚠️ API retornou sucesso=false: {json_response['message']}")
                await self._sleep(self.config.retry_delay_seconds)
                return
                
            if json_response['data'] == None:
                print("😴 Nenhuma tarefa disponível")
                await self._sleep(self.config.polling_interval_seconds)
                return
            
            task_data = json_response['data']
            
            print(f'📋 {task_data['action']}\n')

            await self._process_task(task_data)
                
        except Exception as e:
            print(f"❌ Erro ao processar resposta: {e}")
            await self._sleep(self.config.retry_delay_seconds)
    
    async def _process_task(self, task: Dict[str, Any]):
        """Processa uma tarefa específica"""
        try:
            print(f"⚙️  Processando tarefa: {task['action']} (ID: {task['task_id']})")
            if task.get('message_id'):
                print(f"📨 Message ID: {task['message_id']}")
            
            # Get the appropriate processor
            processor = self.processors.get(task['action'])
            if not processor:
                raise ValueError(f"Processador não encontrado para tipo: {task['action']}")
            
            # Process the task - pass the entire task data
            result = await processor.process(task)
            
            # Send successful response
            await self._send_response(task['task_id'], task['action'], True, result, None, task)
            print(f"✅ Tarefa {task['task_id']} concluída com sucesso")
            
        except Exception as e:
            print(f"❌ Erro no processamento da tarefa {task['task_id']}: {e}")
            
            # Send error response
            error_detail = { "code": "PROCESSING_ERROR", "message": str(e), "details": f"Erro no processamento de {task['action']}" }
            
            await self._send_response(task['task_id'], task['action'], False, None, error_detail, task)
    
    async def _send_response(self, task_id: str, task_type: str, success: bool, result: Optional[Dict[str, Any]], error: Optional[Dict[str, Any]], task_data: Optional[Dict[str, Any]] = None):
        """Envia resposta de processamento para o HubIA"""
        try:

            payload = { 
                "task_id": task_id, 
                "type": task_type,
                "server_id": task_data.get('server_id') if task_data else None,
                "conversation_id": task_data.get('conversation_id') if task_data else None,
                "client_id": task_data.get('client_id') if task_data else None,
                "channel_id": task_data.get('channel_id') if task_data else None,
                "message_id": task_data.get('message_id') if task_data else None,
                "metadata": task_data.get('metadata', {}) if task_data else {}
            }

            # Prepara o resultado baseado no tipo de tarefa
            if success and result:
                if task_type == EMBEDDING:
                    payload['success'] = True
                    payload['data'] = result.get("embedding", [])
                    # Add embedding metadata
                    payload['metadata'].update({
                        'dimensions': result.get('dimensions', 0),
                        'model': result.get('model', ''),
                        'tokens': result.get('tokens', 0)
                    })

                elif task_type == TRANSCRIBE:
                    payload['success'] = True
                    payload['data'] = result.get("transcription", "")
                    
                elif task_type == DESCRIBE:
                    payload['success'] = True
                    payload['data'] = result.get("description", "")
                    
                elif task_type == SUMMARIZE:
                    payload['success'] = True
                    payload['data'] = result.get("summary", "")
                    
                elif task_type == PROMPT:
                    payload['success'] = True
                    payload['data'] = result.get("response", "")
                    
                elif task_type == KNOWLEDGE:
                    payload['success'] = True
                    payload['data'] = result.get("embedding", [])
                    # Add knowledge embedding metadata
                    payload['metadata'].update({
                        'dimensions': result.get('dimensions', 0),
                        'model': result.get('model', ''),
                        'tokens': result.get('tokens', 0)
                    })
                    
            else:
                payload['success'] = False
                payload['data'] = None
            
            result_to_log = payload.copy()
            if result_to_log.get('data'):
                if isinstance(result_to_log['data'], str):
                    result_to_log['data'] = result_to_log['data'][:100]
                elif isinstance(result_to_log['data'], list) and len(result_to_log['data']) > 10:
                    result_to_log['data'] = result_to_log['data'][:10]
            print(f"📤 Enviando resposta para API: {result_to_log}")

        except Exception as e:
            print(f"❌ Erro ao preparar payload: {e}")
            return

        try:

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.config.api_url}/workflow/tasks",
                    headers={
                        "x-server-token": self.server_key,
                        "Content-Type": "application/json"
                    },
                    json=payload
                )

                if response.status_code == 200:
                    print(f"📤 Resposta enviada com sucesso para tarefa {task_id}")
                    return

                if response.status_code == 401:
                    print("❌ Token de servidor inválido ao enviar resposta")
                    return

                print(f"❌ Erro ao enviar resposta...")
                print(f"Status code: {response.status_code}")
                print(f"Response: {response.json()}")
                return

        except Exception as e:
            print(f"Erro: {e}")
    
    async def _sleep(self, seconds: int):
        """Aguarda o tempo especificado"""
        await asyncio.sleep(seconds)
    
    def stop(self):
        """Para o cliente de workflow"""
        print("⏹️ Parando cliente de workflow...")
        self.is_running = False
