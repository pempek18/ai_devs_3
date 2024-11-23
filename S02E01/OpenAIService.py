import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from typing import Optional, List, Dict, Any, AsyncIterable, Union, Tuple
import elevenlabs
import groq
# from microsoft.tiktokenizer import create_by_model_name
import json
import tiktoken
class OpenAIService:
    IM_START = "<|im_start|>"
    IM_END = "<|im_end|>"
    IM_SEP = "<|im_sep|>"

    def __init__(self):
        # Load .env from parent directory
        parent_dir = Path(__file__).parent.parent
        env_exist = load_dotenv(parent_dir / '.env')
        if not env_exist:
            raise ValueError("No .env file found")
        
        self.openai = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.elevenlabs = elevenlabs.ElevenLabs(api_key=os.getenv('ELEVENLABS_API_KEY'))
        self.groq = groq.Groq(api_key=os.getenv('GROQ_API_KEY'))
        self.tokenizers = {}

    async def get_tokenizer(self, model_name: str):
        if model_name not in self.tokenizers:
            special_tokens = {
                self.IM_START: 100264,
                self.IM_END: 100265,
                self.IM_SEP: 100266,
            }
            # tokenizer = await create_by_model_name(model_name, special_tokens)
            tokenizer = tiktoken.encoding_for_model(model_name, special_tokens=special_tokens)
            self.tokenizers[model_name] = tokenizer
        return self.tokenizers[model_name]

    async def count_tokens(self, messages: List[Dict[str, str]], model: str = 'gpt-4o') -> int:
        tokenizer = await self.get_tokenizer(model)
        formatted_content = ''
        
        for message in messages:
            formatted_content += f"{self.IM_START}{message['role']}{self.IM_SEP}{message.get('content', '')}{self.IM_END}"
        formatted_content += f"{self.IM_START}assistant{self.IM_SEP}"

        tokens = tokenizer.encode(formatted_content, [self.IM_START, self.IM_END, self.IM_SEP])
        return len(tokens)

    async def completion(self, 
                        messages: List[Dict[str, str]], 
                        model: str = "gpt-4o",
                        stream: bool = False,
                        temperature: float = 0,
                        json_mode: bool = False,
                        max_tokens: int = 4096) -> Union[Dict[str, Any], AsyncIterable]:
        try:
            response = await self.openai.chat.completions.create(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                response_format={"type": "json_object"} if json_mode else None
            )
            return response
        except Exception as e:
            print("Error in OpenAI completion:", str(e))
            raise

    def parse_json_response(self, response) -> Union[Dict[str, Any], Dict[str, Union[str, bool]]]:
        try:
            content = response.choices[0].message.content
            if not content:
                raise ValueError('Invalid response structure')
            return json.loads(content)
        except Exception as e:
            print('Error parsing JSON response:', str(e))
            return {'error': 'Failed to process response', 'result': False}

    async def create_embedding(self, text: str) -> List[float]:
        try:
            response = await self.openai.embeddings.create(
                model="text-embedding-3-large",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print("Error creating embedding:", str(e))
            raise

    async def speak(self, text: str) -> bytes:
        try:
            response = await self.openai.audio.speech.create(
                model='tts-1',
                voice='alloy',
                input=text
            )
            return response.content
        except Exception as e:
            print("Error in text to speech:", str(e))
            raise

    async def transcribe(self, audio_buffer: bytes) -> str:
        try:
            transcription = await self.openai.audio.transcriptions.create(
                file=('speech.mp3', audio_buffer),
                language='pl',
                model='whisper-1'
            )
            return transcription.text
        except Exception as e:
            print("Error transcribing audio:", str(e))
            raise

    async def transcribe_groq(self, audio_buffer: bytes, file_name: str) -> str:
        try:
            transcription = await self.groq.audio.transcriptions.create(
                file=(file_name, audio_buffer),
                language='pl',
                model='whisper-large-v3'
            )
            return transcription.text
        except Exception as e:
            print("Error in Groq transcription:", str(e))
            raise

    async def speak_eleven(self,
                          text: str,
                          voice: str = "21m00Tcm4TlvDq8ikWAM",
                          model_id: str = "eleven_turbo_v2_5") -> bytes:
        try:
            audio_stream = await self.elevenlabs.generate(
                text=text,
                voice_id=voice,
                model_id=model_id,
                stream=True
            )
            return audio_stream
        except Exception as e:
            print("Error in ElevenLabs speech generation:", str(e))
            raise 