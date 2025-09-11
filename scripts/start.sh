#!/bin/bash

# Script de inicialização do HubIA Workflow API Server
echo "🚀 Iniciando HubIA Workflow API Server..."

# Função para aguardar serviço ficar disponível
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Aguardando $service_name ficar disponível..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo "✅ $service_name está disponível!"
            return 0
        fi
        
        echo "🔄 Tentativa $attempt/$max_attempts - $service_name ainda não disponível..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name não ficou disponível após $max_attempts tentativas"
    return 1
}

# Iniciar Ollama em background
echo "🔧 Iniciando Ollama..."
ollama serve &
OLLAMA_PID=$!

# Aguardar Ollama ficar disponível
if ! wait_for_service "http://ollama:11434/api/tags" "Ollama"; then
    echo "❌ Falha ao iniciar Ollama"
    exit 1
fi

# Verificar se os modelos necessários estão disponíveis
echo "📋 Verificando modelos Ollama..."
MODELS=("llava:7b" "gemma2:9b" "nomic-embed-text")

for model in "${MODELS[@]}"; do
    # Verificar se o modelo existe via API
    if curl -s "http://ollama:11434/api/tags" | grep -q "\"name\":\"$model\""; then
        echo "✅ Modelo $model está disponível"
    else
        echo "⚠️ Modelo $model não encontrado - baixando..."
        curl -X POST "http://ollama:11434/api/pull" -H "Content-Type: application/json" -d "{\"name\":\"$model\"}" || {
            echo "❌ Falha ao baixar modelo $model"
            exit 1
        }
    fi
done

# Aguardar um pouco mais para garantir que tudo está estável
echo "⏳ Aguardando estabilização dos serviços..."
sleep 5

# Registrar o servidor na API (se necessário)
echo "🔧 Verificando registro do servidor na API..."
cd /app
if [ -z "$SERVER_KEY" ] || [ "$SERVER_KEY" = "sk_meu_servidor_001" ]; then
    echo "📝 Servidor não registrado - registrando agora..."
    python scripts/register.py || {
        echo "⚠️ Falha no registro - continuando sem registro"
        echo "💡 Execute manualmente: python scripts/register.py"
    }
else
    echo "✅ Servidor já registrado (SERVER_KEY: $SERVER_KEY)"
fi

# Iniciar o servidor Python
echo "🐍 Iniciando servidor Python..."
exec python src/main.py
