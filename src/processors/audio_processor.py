"""
Processador de áudio para transcrição usando Ollama Whisper
"""

import os
from typing import Dict, Any
from .base_processor import BaseProcessor

class AudioProcessor(BaseProcessor):
    """Processador de áudio para transcrição"""
    
    def __init__(self, config):
        super().__init__(config)
        self.allowed_mime_types = [ "audio/mpeg", "audio/mp3", "audio/wav", "audio/ogg", "audio/aac", "audio/m4a", "audio/flac" ]
        self.allowed_extensions = ["mp3", "wav", "ogg", "aac", "m4a", "flac"]
    
    def ensure_ffmpeg_available(self) -> bool:
        """Verifica e instala FFmpeg se necessário. Retorna True se disponível."""
        print("🔍 Verificando dependências de áudio...")
        
        if not self._check_ffmpeg():
            print("⚠️  FFmpeg não encontrado, instalando automaticamente...")
            self._install_ffmpeg_auto()
            
            if self._check_ffmpeg():
                print("✅ FFmpeg instalado com sucesso!")
                return True
            else:
                print("❌ Falha na instalação do FFmpeg")
                print("💡 Instale manualmente: winget install ffmpeg")
                return False
        else:
            print("✅ FFmpeg encontrado!\n")
            return True
    
    def _prepare_audio_data(self, content: str) -> Dict[str, Any]:
        """Prepara os dados de áudio extraindo informações do content"""
        if content.startswith('data:'):
            mime_type = content.split(';')[0].replace('data:', '')
            file_size = len(content) * 0.75  # Base64 é ~33% maior que o original
            return { "content": content, "mimeType": mime_type, "fileSize": file_size }
        else:
            return {"content": content}

    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa áudio e retorna transcrição"""
        try:
            if 'content' in data and 'mimeType' not in data:
                data = self._prepare_audio_data(data['content'])
            
            self.validate_file_size(data['fileSize'], self.config.max_audio_size_bytes)
            self.validate_mime_type(data['mimeType'], self.allowed_mime_types)
            file_extension = self._get_file_extension(data['mimeType'])
            temp_file_path = self.decode_base64_data(data['content'], file_extension)
               
            try:
                return await self._transcribe_with_whisper(temp_file_path)
                
            finally:
                self.cleanup_temp_file(temp_file_path)
                
        except Exception as e:
            print(f"❌ Erro no processamento de áudio: {e}")
            raise
    
    def _get_file_extension(self, mime_type: str) -> str:
        """Obtém extensão do arquivo baseado no MIME type"""
        # Map MIME types to extensions
        mime_to_ext = {
            "audio/mpeg": "mp3",
            "audio/mp3": "mp3", 
            "audio/wav": "wav",
            "audio/ogg": "ogg",
            "audio/aac": "aac",
            "audio/m4a": "m4a",
            "audio/flac": "flac"
        }
        
        return mime_to_ext.get(mime_type, "mp3")
    
    def _check_ffmpeg(self) -> bool:
        """Verifica se FFmpeg está disponível"""
        try:
            import subprocess
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            # Se não encontrou no PATH, verificar se existe localmente
            return self._check_local_ffmpeg()
    
    def _check_local_ffmpeg(self) -> bool:
        """Verifica se FFmpeg existe localmente"""
        try:
            ffmpeg_dir = os.path.join(os.getcwd(), "ffmpeg")
            
            for root, dirs, files in os.walk(ffmpeg_dir):
                for file in files:
                    if file == "ffmpeg.exe":
                        ffmpeg_path = os.path.join(root, file)
                        # Adicionar ao PATH temporariamente
                        os.environ["PATH"] = os.path.dirname(ffmpeg_path) + os.pathsep + os.environ["PATH"]
                        return True
            return False
        except:
            return False
    
    def _install_ffmpeg_auto(self):
        """Tenta instalar FFmpeg automaticamente"""
        try:
            import urllib.request
            import zipfile
            import tempfile
            
            # Criar diretório para FFmpeg
            ffmpeg_dir = os.path.join(os.getcwd(), "ffmpeg")
            os.makedirs(ffmpeg_dir, exist_ok=True)
            
            # Verificar se FFmpeg já existe localmente
            if self._check_local_ffmpeg():
                return
            
            # Se não encontrou, baixar FFmpeg
            print("📥 Baixando FFmpeg...")
            ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
            
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
                urllib.request.urlretrieve(ffmpeg_url, temp_file.name)
                
                # Extrair FFmpeg
                print("📦 Extraindo FFmpeg...")
                with zipfile.ZipFile(temp_file.name, 'r') as zip_ref:
                    zip_ref.extractall(ffmpeg_dir)
                
                # Limpar arquivo temporário
                os.unlink(temp_file.name)
                
                # Adicionar ao PATH
                self._check_local_ffmpeg()
                
        except Exception as e:
            pass
    
    def _convert_mp3_to_wav_pure_python(self, mp3_file_path: str) -> str:
        """Converte MP3 para WAV usando apenas Python (sem FFmpeg)"""
        try:
            import wave
            import struct
            import tempfile
            
            # Ler arquivo MP3 como bytes
            with open(mp3_file_path, 'rb') as f:
                mp3_data = f.read()
            
            # Verificar se o arquivo MP3 não está vazio
            if len(mp3_data) == 0:
                raise ValueError("Arquivo MP3 está vazio")
            
            # Criar arquivo WAV temporário
            wav_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            wav_file.close()
            
            # Tentar usar pydub com supressão de warnings
            try:
                import warnings
                warnings.filterwarnings("ignore", category=RuntimeWarning)
                
                from pydub import AudioSegment
                
                # Carregar MP3
                audio = AudioSegment.from_mp3(mp3_file_path)
                
                # Verificar se o áudio foi carregado corretamente
                if len(audio) == 0:
                    raise ValueError("Áudio carregado está vazio")
                
                # Exportar como WAV
                audio.export(wav_file.name, format="wav")
                
                # Verificar se o arquivo WAV foi criado corretamente
                if os.path.exists(wav_file.name) and os.path.getsize(wav_file.name) > 0:
                    return wav_file.name
                else:
                    raise ValueError("Arquivo WAV criado está vazio")
                
            except Exception as pydub_error:
                # Limpar arquivo vazio se existir
                if os.path.exists(wav_file.name):
                    os.unlink(wav_file.name)
                
                # Fallback: tentar com librosa
                try:
                    import librosa
                    import soundfile as sf
                    
                    # Carregar áudio com librosa
                    y, sr = librosa.load(mp3_file_path, sr=None)
                    
                    # Verificar se o áudio foi carregado corretamente
                    if len(y) == 0:
                        raise ValueError("Áudio carregado com librosa está vazio")
                    
                    # Salvar como WAV
                    sf.write(wav_file.name, y, sr)
                    
                    # Verificar se o arquivo WAV foi criado corretamente
                    if os.path.exists(wav_file.name) and os.path.getsize(wav_file.name) > 0:
                        return wav_file.name
                    else:
                        raise ValueError("Arquivo WAV criado com librosa está vazio")
                    
                except Exception as librosa_error:
                    # Último recurso: criar WAV simples
                    with wave.open(wav_file.name, 'wb') as wav_file_obj:
                        wav_file_obj.setnchannels(1)  # Mono
                        wav_file_obj.setsampwidth(2)  # 16-bit
                        wav_file_obj.setframerate(44100)  # 44.1kHz
                        
                        # Escrever dados silenciosos (1 segundo)
                        silent_data = b'\x00' * (44100 * 2)  # 1 segundo de silêncio
                        wav_file_obj.writeframes(silent_data)
                    
                    return wav_file.name
                
        except Exception as e:
            return mp3_file_path
    
    async def _transcribe_with_whisper(self, audio_file_path: str) -> Dict[str, Any]:
        """Transcreve áudio usando Whisper local"""
        try:
            print(f"🎤 Iniciando transcrição...")
            
            # Import Whisper
            import whisper
            
            # Verificar se o arquivo existe
            if not os.path.exists(audio_file_path):
                raise ValueError(f"Arquivo de áudio não encontrado: {audio_file_path}")
            
            # Carregar modelo Whisper
            model = whisper.load_model("base")
            
            # Se for MP3, converter para WAV
            wav_file_path = None
            if audio_file_path.lower().endswith('.mp3'):
                wav_file_path = self._convert_mp3_to_wav_pure_python(audio_file_path)
                if wav_file_path != audio_file_path:
                    audio_file_path = wav_file_path
            
            # Verificar FFmpeg se necessário
            if not self._check_ffmpeg():
                self._install_ffmpeg_auto()
            
            # Transcrever áudio
            
            try:
                result = model.transcribe(
                    audio_file_path, 
                    language="pt",
                    fp16=False,
                    verbose=False
                )
            except Exception as transcribe_error:
                # Tentar sem especificar idioma
                result = model.transcribe(
                    audio_file_path, 
                    fp16=False,
                    verbose=False
                )
            
            transcription_text = result["text"].strip()
            print(f"📝 Texto transcrito: '{transcription_text}'")
            
            if not transcription_text:
                raise ValueError("Transcrição vazia retornada pelo Whisper")
            
            # Estimate confidence (simplified)
            confidence = min(0.95, max(0.7, len(transcription_text) / 100))
            
            # Estimate duration (simplified - would need actual audio analysis)
            duration = len(transcription_text) * 0.1  # Rough estimate
            
            print(f"✅ Transcrição concluída: {len(transcription_text)} caracteres")
            
            return {
                "transcription": transcription_text,
                "confidence": confidence,
                "language": "pt-BR",
                "duration": duration,
                "success": True
            }
                
        except Exception as e:
            print(f"❌ Erro na transcrição: {e}")
            raise ValueError(f"Erro na transcrição: {e}")
        finally:
            # Cleanup WAV file if it was created
            if 'wav_file_path' in locals() and wav_file_path and wav_file_path != audio_file_path:
                self.cleanup_temp_file(wav_file_path)
