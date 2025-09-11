# 🚀 HubIA Workflow Server

Servidor Python para processamento distribuído de tarefas usando Ollama com modelos locais (Gemma2, LLaVA, Nomic-Embed-Text) e PyTorch com suporte CUDA.

## 📋 Funcionalidades

- **Worker Distribuído**: Polling de API na nuvem para receber tarefas
- **Transcrição de Áudio**: Usando Gemma2 9B (processamento de texto de áudio)
- **Descrição de Imagens**: Usando LLaVA 7B  
- **Sumarização de Documentos**: Usando Gemma2 9B
- **Geração de Embeddings**: Usando Nomic-Embed-Text
- **Geração de Respostas**: Usando Gemma2 9B (otimizado para português)
- **Suporte CUDA**: PyTorch, TorchAudio, TorchVision com GPU
- **Container Docker**: Pronto para produção

## 🛠️ Tecnologias

- **Python 3.11**
- **Ollama** - Modelos de IA locais
- **PyTorch + CUDA** - Processamento com GPU
- **httpx** - Cliente HTTP assíncrono
- **Docker** - Containerização
- **Loguru** - Logging avançado

## 🚀 Instalação e Uso

### 1. Pré-requisitos

- Docker com suporte NVIDIA GPU
- NVIDIA Driver instalado
- Ollama instalado localmente (opcional)

### 2. Configuração

```bash
# Clone o repositório
git clone <seu-repositorio>
cd hubia-workflow-server

# Copie o arquivo de configuração
cp .env.example .env

# Edite as configurações se necessário
nano .env
```

### 3. Configurar Modelos Ollama

```bash
# Torne o script executável
chmod +x scripts/download.sh

# Execute o script de download
./scripts/download.sh
```

### 4. Iniciar o Servidor

```bash
# Usando Docker Compose (recomendado)
docker-compose up --build

# Ou usando docker-compose diretamente
docker-compose up --build
```

### 5. Verificar Status

```bash
# Ver logs do servidor
docker-compose logs -f hubia-workflow-server

# Verificar status dos containers
docker-compose ps

# Verificar status do processo
docker exec hubia-workflow-server pgrep -f "python src/main.py"
```

## 📡 API Endpoints

O servidor implementa o protocolo de workflow descrito na documentação:

### Polling para Trabalho
```http
GET /api/v1/workflow/next
Headers:
  x-server-token: sk_meu_servidor_001
```

### Envio de Resposta
```http
POST /api/v1/workflow/responses
Headers:
  x-server-token: sk_meu_servidor_001
  Content-Type: application/json
```

## ⚙️ Configuração

### Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|---------|
| `API_URL` | URL da API de workflow | `https://api.hubia.com` |
| `SERVER_KEY` | Token de autenticação (x-server-token) | `sk_meu_servidor_001` |
| `SERVER_NAME` | Nome do servidor na API | `Servidor Local HubIA` |
| `SLUG` | Nome curto proprietário do servidor | `servidor-local-001` |
| `OLLAMA_BASE_URL` | URL do Ollama | `http://localhost:11434` |
| `OLLAMA_MODEL_TRANSCRICAO` | Modelo para transcrição | `whisper` |
| `OLLAMA_MODEL_VISAO` | Modelo para descrição de imagens | `llava:7b` |
| `OLLAMA_MODEL_RESUMO` | Modelo para sumarização | `gemma2:9b` |
| `OLLAMA_MODEL_EMBEDDINGS` | Modelo para embeddings | `nomic-embed-text` |
| `OLLAMA_MODEL_CONVERSACAO` | Modelo para respostas | `gemma2:9b` |
| `MAX_AUDIO_SIZE_MB` | Tamanho máximo de áudio | `50` |
| `MAX_IMAGE_SIZE_MB` | Tamanho máximo de imagem | `20` |
| `MAX_DOCUMENT_SIZE_MB` | Tamanho máximo de documento | `10` |
| `POLLING_INTERVAL_SECONDS` | Intervalo de polling | `5` |

## 📚 Documentação

- **[Estrutura do Projeto](docs/PROJECT_STRUCTURE.md)** - Organização de pastas e módulos
- **[Workflow API](docs/README_WORKFLOW.md)** - Guia completo do workflow
- **[Docker](docs/README_DOCKER.md)** - Execução com Docker
- **[API Development Guide](docs/WORKFLOW_API_DEVELOPMENT_GUIDE.md)** - Guia de desenvolvimento da API

## 🔧 Desenvolvimento

### Estrutura do Projeto

```
hubia-workflow-server/
├── src/
│   ├── main.py                 # Ponto de entrada
│   ├── core/                   # Módulo core
│   │   ├── config.py          # Configurações
│   │   └── (removido)         # Modelos de dados não necessários
│   ├── workflow/              # Módulo workflow
│   │   └── workflow_client.py # Cliente de workflow
│   └── processors/            # Processadores de mídia
│       ├── base_processor.py
│       ├── audio_processor.py
│       ├── image_processor.py
│       ├── document_processor.py
│       ├── text_processor.py
│       └── prompt_processor.py
├── scripts/
│   ├── download.sh            # Download de modelos
│   ├── start.sh               # Script de inicialização (Docker)
│   ├── register.py            # Registro de servidor
│   └── test_workflow.py       # Teste do workflow
├── docs/                      # Documentação
├── docker-compose.yml         # Orquestração Docker
├── Dockerfile                 # Imagem Docker
├── requirements.txt           # Dependências Python
└── .env.example              # Configuração de exemplo
```

### Executar em Desenvolvimento

```bash
# Instalar PyTorch com CUDA separadamente (melhor prática)
pip install torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu128

# Instalar outras dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
export API_URL=https://api.hubia.com
export SERVER_KEY=sk_meu_servidor_001
export SERVER_NAME="Servidor Local HubIA"
export SLUG=servidor-local-001

# Executar servidor
python src/main.py
```

### Scripts de Configuração

```bash
# Configurar modelos Ollama
./scripts/download.sh
```

## 📊 Monitoramento

### Logs

Os logs são salvos em:
- Console: Saída padrão
- Arquivo: `/app/logs/workflow_server.log`

### Monitoramento

```bash
# Verificar se o processo está rodando
docker exec hubia-workflow-server pgrep -f "python src/main.py"

# Verificar logs para status
docker-compose logs hubia-workflow-server | tail -20

# Verificar trabalhos processados
docker-compose logs hubia-workflow-server | grep "Trabalho encontrado"
```

### Métricas

O servidor registra métricas de:
- Trabalhos processados
- Tempo de processamento
- Erros e falhas
- Uso de recursos
- Status de conectividade com a API

## 🐛 Troubleshooting

### Problemas Comuns

1. **Erro de CUDA**: Verifique se o driver NVIDIA está instalado
2. **Ollama não responde**: Verifique se o Ollama está rodando na porta 11434
3. **Modelos não encontrados**: Execute `./scripts/download.sh`
4. **Erro de permissão**: Verifique permissões dos diretórios `logs/`, `temp/`

### Logs de Debug

```bash
# Ver logs detalhados
docker-compose logs -f hubia-workflow-server

# Logs com nível DEBUG
export LOG_LEVEL=DEBUG
docker-compose up --build
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🆘 Suporte

Para suporte e dúvidas:
- Abra uma issue no GitHub
- Consulte a documentação da API
- Verifique os logs do servidor
