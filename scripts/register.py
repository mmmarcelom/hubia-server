#!/usr/bin/env python3
"""
Script para registrar o servidor na API HubIA Workflow
"""

import os
import sys
import json
import requests
from pathlib import Path
from dotenv import load_dotenv, set_key

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Removed unused imports - using direct dict structure

def register_server():
    """Registra o servidor na API e atualiza o .env"""
    
    # Carrega variáveis do .env
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
    
    # Obtém configurações do .env
    api_url = os.getenv("API_URL")
    server_name = os.getenv("SERVER_NAME")
    slug = os.getenv("SLUG")
    
    if not all([api_url, server_name, slug]):
        print("❌ Erro: Variáveis API_URL, SERVER_NAME e SLUG devem estar definidas no .env")
        return False
    
    # Monta a URL completa
    register_url = f"{api_url}/workflow/register"
    
    # Payload para registro
    payload = {
        "slug": slug,
        "serverName": server_name
    }
    
    print("🔧 Registrando servidor na API...")
    print(f"   URL: {register_url}")
    print(f"   Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Faz a requisição
        response = requests.post(
            register_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Servidor registrado com sucesso!")
            
            # Extrai dados da resposta (estrutura da API real)
            server_data = data.get('server', {})
            server_id = server_data.get('id')
            server_key = server_data.get('server_key')
            message = data.get('message')
            
            print(f"   Server ID: {server_id}")
            print(f"   Server Key: {server_key}")
            print(f"   Message: {message}")
            
            # Atualiza o .env com a nova server key
            if server_key:
                set_key(env_path, "SERVER_KEY", server_key)
                print(f"✅ Arquivo .env atualizado com nova SERVER_KEY: {server_key}")
                return True
            else:
                print("❌ Erro: Server key não encontrada na resposta")
                return False
                
        else:
            print(f"❌ Erro no registro: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 Script de Registro de Servidor HubIA Workflow")
    print("=" * 50)
    
    success = register_server()
    
    if success:
        print("\n✅ Registro concluído com sucesso!")
        print("   O servidor está pronto para processar tarefas.")
    else:
        print("\n❌ Falha no registro do servidor.")
        sys.exit(1)

if __name__ == "__main__":
    main()
