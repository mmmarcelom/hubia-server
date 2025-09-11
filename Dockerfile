# Use uma imagem PyTorch oficial disponível
FROM pytorch/pytorch:2.8.0-cuda12.6-cudnn9-devel

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    python3.11-venv \
    build-essential \
    wget \
    curl \
    git \
    ffmpeg \
    libsndfile1 \
    libsndfile1-dev \
    libasound2-dev \
    portaudio19-dev \
    libportaudio2 \
    libportaudiocpp0 \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    libavfilter-dev \
    libsm6 \
    libxext6 \
    libfontconfig1 \
    libxrender1 \
    libgl1-mesa-glx \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic link for python
RUN ln -s /usr/bin/python3.11 /usr/bin/python

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY .env.example .env

# Note: .env real será copiado pelo docker-compose

# Create directories for temporary files
RUN mkdir -p /app/temp /app/logs

# Make scripts executable
RUN chmod +x /app/scripts/*.py /app/scripts/*.sh

# Expose ports
EXPOSE 11434

# Copy and make startup script executable
COPY scripts/start.sh /start.sh
RUN chmod +x /start.sh

# Start with custom script
CMD ["/start.sh"]