import os
import openai
from typing import Optional, List, Dict, Any, AsyncIterable, Union, Tuple, Literal
import elevenlabs
import groq
from tiktoken import encoding_for_model
import json
import aiohttp
import math

class OpenAIService:
    IM_START = "<|im_start|>"
    IM_END = "<|im_end|>"
    IM_SEP = "<|im_sep|>"

    def __init__(self):
        self.openai = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.elevenlabs = elevenlabs.ElevenLabs(api_key=os.getenv('ELEVENLABS_API_KEY'))
        self.groq = groq.Groq(api_key=os.getenv('GROQ_API_KEY'))
        self.tokenizers = {}
        self.JINA_API_KEY = os.getenv('JINA_API_KEY')

    async def get_tokenizer(self, model_name: str):
        if model_name not in self.tokenizers:
            special_tokens = {
                self.IM_START: 100264,
                self.IM_END: 100265,
                self.IM_SEP: 100266,
            }
            tokenizer = await encoding_for_model(model_name)
            self.tokenizers[model_name] = tokenizer(special_tokens=special_tokens)
        return self.tokenizers[model_name]

    async def count_tokens(self, messages: List[Dict[str, str]], model: str = 'gpt-4o') -> int:
        tokenizer = await self.get_tokenizer(model)
        formatted_content = ''
        
        for message in messages:
            formatted_content += f"{self.IM_START}{message['role']}{self.IM_SEP}{message.get('content', '')}{self.IM_END}"
        formatted_content += f"{self.IM_START}assistant{self.IM_SEP}"

        tokens = tokenizer.encode(formatted_content, [self.IM_START, self.IM_END, self.IM_SEP])
        return len(tokens)
    
    def completion(self, 
                messages: List[Dict[str, str]], # List of message dictionaries containing role and content
                model: str = "gpt-4o",         # Model name, defaults to gpt-4o
                stream: bool = False,          # Whether to stream responses
                json_mode: bool = False,       # Whether to force JSON output format
                max_tokens: int = 4096         # Maximum tokens in response
                ) -> Union[Dict[str, Any], AsyncIterable]:  # Returns either a dict or async stream
        try:
            # Initialize basic parameters that work for all models
            params = {
                "messages": messages,  # The conversation messages
                "model": model,        # The model to use
            }
            
            # Add additional parameters for models that support them
            # o1-mini and o1-preview have limited parameter support
            if model not in ['o1-mini', 'o1-preview']:
                params.update({
                    "stream": stream,      # Enable/disable streaming
                    "max_tokens": max_tokens,  # Set max response length
                    # Set response format - either JSON or plain text
                    "response_format": {"type": "json_object"} if json_mode else {"type": "text"}
                })

            # Create and return the chat completion
            # Create a chat completion using OpenAI's API
            # This generates an AI response based on the conversation history in params["messages"]
            # Returns a ChatCompletion object containing the model's response
            chat_completion = self.openai.chat.completions.create(**params)
            return chat_completion
        except Exception as error:
            print("Error in OpenAI completion:", str(error))
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

    async def create_jina_embedding(self, text: str) -> List[float]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.jina.ai/v1/embeddings',
                    headers={
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {self.JINA_API_KEY}'
                    },
                    json={
                        'model': 'jina-embeddings-v3',
                        'task': 'text-matching',
                        'dimensions': 1024,
                        'late_chunking': False,
                        'embedding_type': 'float',
                        'input': [text]
                    }
                ) as response:
                    if not response.ok:
                        raise ValueError(f"HTTP error! status: {response.status}")
                    
                    data = await response.json()
                    return data['data'][0]['embedding']
        except Exception as error:
            print("Error creating Jina embedding:", str(error))
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

    async def transcribe_groq(self, audio_buffer: bytes) -> str:
        try:
            transcription = await self.groq.audio.transcriptions.create(
                file=('speech.mp3', audio_buffer),
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

    def calculate_image_tokens(self, 
                             width: int, 
                             height: int, 
                             detail: Literal['low', 'high']) -> int:
        token_cost = 0

        if detail == 'low':
            token_cost += 85
            return token_cost

        MAX_DIMENSION = 2048
        SCALE_SIZE = 768

        # Resize to fit within MAX_DIMENSION x MAX_DIMENSION
        if width > MAX_DIMENSION or height > MAX_DIMENSION:
            aspect_ratio = width / height
            if aspect_ratio > 1:
                width = MAX_DIMENSION
                height = round(MAX_DIMENSION / aspect_ratio)
            else:
                height = MAX_DIMENSION
                width = round(MAX_DIMENSION * aspect_ratio)

        # Scale the shortest side to SCALE_SIZE
        if width >= height and height > SCALE_SIZE:
            width = round((SCALE_SIZE / height) * width)
            height = SCALE_SIZE
        elif height > width and width > SCALE_SIZE:
            height = round((SCALE_SIZE / width) * height)
            width = SCALE_SIZE

        # Calculate the number of 512px squares
        num_squares = math.ceil(width / 512) * math.ceil(height / 512)

        # Calculate the token cost
        token_cost += (num_squares * 170) + 85

        return token_cost