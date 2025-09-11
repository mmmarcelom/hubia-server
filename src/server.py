#!/usr/bin/env python3
"""
HubIA Workflow Server
Servidor para processamento de tarefas distribuídas usando Ollama e modelos locais
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
sys.path.append(str(Path(__file__).parent))
from config import Config
from client import WorkflowClient
from processors.audio_processor import AudioProcessor

load_dotenv()

async def main():
    """Função principal do servidor"""
    try:
        print("\n")
        print("🚀 Iniciando HubIA Workflow Server...")
        
        # Load configuration
        config = Config()
        print(f"🌐 {config.api_url}\n")
        
        # Verifica se temos SERVER_KEY antes de prosseguir
        if not config.server_key or config.server_key.strip() == "":
            print("❌ SERVER_KEY está vazia ou não definida.")
            print("📝 É necessário fazer o registro do servidor primeiro.")
            print("💡 Execute o script de registro para obter uma SERVER_KEY válida.")
            return
        
        # Verificar e instalar FFmpeg se necessário
        audio_processor = AudioProcessor(config)
        audio_processor.ensure_ffmpeg_available()
        
        # Initialize workflow client
        client = WorkflowClient(config)
        
        await client.start()
        
    except KeyboardInterrupt:
        print("⏹️ Servidor interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro fatal no servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
