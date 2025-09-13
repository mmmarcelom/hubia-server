"""
Processador de imagem para descrição usando Ollama LLaVA
"""

import base64
import io
from typing import Dict, Any, List
import httpx
from PIL import Image
from .base_processor import BaseProcessor
# TaskType enum values
DESCRIBE = "describe"

class ImageProcessor(BaseProcessor):
    """Processador de imagem para descrição"""
    
    def __init__(self, config):
        super().__init__(config)
        self.allowed_mime_types = [
            "image/jpeg", "image/jpg", "image/png", "image/gif", 
            "image/bmp", "image/webp", "image/tiff"
        ]
        self.allowed_extensions = ["jpg", "jpeg", "png", "gif", "bmp", "webp", "tiff"]
    
    def _prepare_image_data(self, content: str) -> Dict[str, Any]:
        """Prepara dados de imagem a partir de data URL base64"""
        try:
            # Extract MIME type and base64 data
            if content.startswith('data:'):
                header, data = content.split(',', 1)
                mime_type = header.split(';')[0].replace('data:', '')
            else:
                # Assume it's raw base64 data
                mime_type = "image/jpeg"  # Default fallback
                data = content
            
            # Decode base64 to get file size
            image_data = base64.b64decode(data)
            file_size = len(image_data)
            
            return {
                "image_data": data,
                "mime_type": mime_type,
                "file_size": file_size,
                "file_name": None  # Base64 data doesn't have filename
            }
            
        except Exception as e:
            raise ValueError(f"Erro ao processar dados de imagem: {e}")
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa imagem e retorna descrição"""
        try:
            # Extract image data from content field
            if 'content' in data:
                # The image data is in the content field
                data = self._prepare_image_data(data['content'])
            elif 'image_data' in data and ('mime_type' not in data or 'file_size' not in data):
                # Fallback for direct image_data
                data = self._prepare_image_data(data['image_data'])
            
            # Validate file size
            self.validate_file_size(data['file_size'], self.config.max_image_size_bytes)
            
            # Validate MIME type
            self.validate_mime_type(data['mime_type'], self.allowed_mime_types)
            
            # Get file extension
            file_extension = self._get_file_extension(data['mime_type'], data.get('file_name'))
            
            # Decode and save image file
            temp_file_path = self.decode_base64_data(data['image_data'], file_extension)
            
            try:
                # Process image with Ollama LLaVA
                result = await self._describe_with_ollama(temp_file_path, data)
                
                # Convert to dict
                return result
                
            finally:
                # Cleanup temp file
                self.cleanup_temp_file(temp_file_path)
                
        except Exception as e:
            print(f"❌ Erro no processamento de imagem: {e}")
            raise
    
    def _get_file_extension(self, mime_type: str, filename: str = None) -> str:
        """Obtém extensão do arquivo"""
        # Try to get from filename first
        if filename and '.' in filename:
            return filename.split('.')[-1].lower()
        
        # Map MIME types to extensions
        mime_to_ext = {
            "image/jpeg": "jpg",
            "image/jpg": "jpg",
            "image/png": "png",
            "image/gif": "gif",
            "image/bmp": "bmp",
            "image/webp": "webp",
            "image/tiff": "tiff"
        }
        
        return mime_to_ext.get(mime_type, "jpg")
    
    async def _describe_with_ollama(self, image_file_path: str, describe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Descreve imagem usando Ollama LLaVA"""
        try:
            print(f"🖼️ Iniciando descrição de imagem com Ollama LLaVA...")
            
            # Load and process image
            with Image.open(image_file_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large (max 1024x1024)
                max_size = 1024
                if img.width > max_size or img.height > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # Convert to base64
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Ollama API request
            ollama_url = f"{self.config.ollama_base_url}/api/generate"
            
            prompt = """Descreva esta imagem em português brasileiro. Inclua:
1. Uma descrição geral da imagem
2. Objetos principais visíveis
3. Cores predominantes
4. Qualquer texto visível na imagem

Seja detalhado mas conciso."""
            
            payload = {
                "model": self.config.ollama_model_visao,
                "prompt": prompt,
                "images": [image_base64],
                "stream": False
            }
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(ollama_url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                description_text = result.get("response", "").strip()
                
                if not description_text:
                    raise ValueError("Descrição vazia retornada pelo modelo")
                
                # Parse the response to extract structured information
                parsed_result = self._parse_description(description_text)
                
                print(f"✅ Descrição de imagem concluída")
                
                return {
                    "description": parsed_result["description"],
                    "confidence": parsed_result["confidence"],
                    "objects": parsed_result["objects"],
                    "colors": parsed_result["colors"],
                    "text": parsed_result.get("text"),
                    "success": True
                }
                
        except httpx.HTTPError as e:
            print(f"❌ Erro HTTP na descrição: {e}")
            raise ValueError(f"Erro na comunicação com Ollama: {e}")
        except Exception as e:
            print(f"❌ Erro na descrição: {e}")
            raise ValueError(f"Erro na descrição: {e}")
    
    def _parse_description(self, description_text: str) -> Dict[str, Any]:
        """Parse a descrição estruturada do texto retornado"""
        try:
            # Simple parsing - in a real implementation, you might use more sophisticated NLP
            lines = description_text.split('\n')
            
            description = ""
            objects = []
            colors = []
            text = None
            
            # Common color words in Portuguese
            color_words = [
                "vermelho", "azul", "verde", "amarelo", "preto", "branco", "cinza",
                "rosa", "roxo", "laranja", "marrom", "bege", "dourado", "prateado"
            ]
            
            # Common object words
            object_words = [
                "pessoa", "carro", "casa", "árvore", "cachorro", "gato", "mesa", "cadeira",
                "computador", "telefone", "livro", "papel", "caneta", "logo", "texto",
                "imagem", "foto", "desenho", "gráfico", "botão", "ícone"
            ]
            
            for line in lines:
                line = line.strip().lower()
                if line:
                    description += line + " "
                    
                    # Extract colors
                    for color in color_words:
                        if color in line:
                            colors.append(color)
                    
                    # Extract objects
                    for obj in object_words:
                        if obj in line:
                            objects.append(obj)
                    
                    # Look for text indicators
                    if any(word in line for word in ["texto", "escrito", "palavra", "letra"]):
                        # Try to extract actual text (simplified)
                        if ":" in line:
                            text = line.split(":")[-1].strip()
            
            # Remove duplicates
            colors = list(set(colors))
            objects = list(set(objects))
            
            # Estimate confidence based on response length and structure
            confidence = min(0.95, max(0.7, len(description) / 200))
            
            return {
                "description": description.strip(),
                "confidence": confidence,
                "objects": objects[:10],  # Limit to 10 objects
                "colors": colors[:5],     # Limit to 5 colors
                "text": text
            }
            
        except Exception as e:
            print(f"⚠️ Erro ao fazer parse da descrição: {e}")
            # Fallback to simple description
            return {
                "description": description_text,
                "confidence": 0.8,
                "objects": [],
                "colors": [],
                "text": None
            }
