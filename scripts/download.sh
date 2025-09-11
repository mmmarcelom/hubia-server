#!/bin/bash

# Script para configurar modelos Ollama necessários
echo "🚀 Configurando modelos Ollama para HubIA Workflow Server..."

# Verificar se Ollama está rodando
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Ollama não está rodando. Inicie o Ollama primeiro."
    echo "💡 Execute: docker-compose up -d ollama"
    exit 1
fi

echo "📥 Verificando e baixando modelos necessários..."

# Lista de modelos necessários (apenas modelos disponíveis no Ollama)
MODELS=("llava:7b" "gemma2:9b" "nomic-embed-text")

for model in "${MODELS[@]}"; do
    if ollama list | grep -q "$model"; then
        echo "✅ Modelo $model já está disponível"
    else
        echo "📥 Baixando modelo $model..."
        ollama pull "$model" || {
            echo "❌ Falha ao baixar modelo $model"
            exit 1
        }
    fi
done

echo "✅ Todos os modelos foram baixados com sucesso!"
echo ""
echo "📋 Modelos disponíveis:"
ollama list

echo ""
echo "🎯 Modelos configurados com sucesso!"
echo "💡 Agora você pode iniciar o servidor: docker-compose up -d"
