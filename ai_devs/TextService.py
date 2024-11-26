from typing import Dict, List, TypedDict, Optional, Tuple
import tiktoken
import re
import asyncio

class Metadata(TypedDict):
    tokens: int
    headers: Dict[str, List[str]]
    urls: List[str]
    images: List[str]

class Doc(TypedDict):
    text: str
    metadata: Metadata

class TextSplitter:
    def __init__(self, model_name: str = 'gpt-4'):
        self.MODEL_NAME = model_name
        self.SPECIAL_TOKENS = {
            '<|im_start|>': 100264,
            '<|im_end|>': 100265,
            '<|im_sep|>': 100266,
        }
        self.tokenizer = None
        self.url_index = 0

    async def initialize_tokenizer(self) -> None:
        if not self.tokenizer:
            self.tokenizer = tiktoken.encoding_for_model(self.MODEL_NAME)

    def count_tokens(self, text: str) -> int:
        if not self.tokenizer:
            raise RuntimeError('Tokenizer not initialized')
        formatted_content = self.format_for_tokenization(text)
        tokens = self.tokenizer.encode(formatted_content)
        return len(tokens)

    def format_for_tokenization(self, text: str) -> str:
        return f"<|im_start|>user\n{text}<|im_end|>\n<|im_start|>assistant<|im_end|>"

    async def split(self, text: str, limit: int) -> List[Doc]:
        print(f"Starting split process with limit: {limit} tokens")
        await self.initialize_tokenizer()
        chunks: List[Doc] = []
        position = 0
        total_length = len(text)
        current_headers: Dict[str, List[str]] = {}

        while position < total_length:
            print(f"Processing chunk starting at position: {position}")
            chunk_text, chunk_end = self.get_chunk(text, position, limit)
            tokens = self.count_tokens(chunk_text)
            print(f"Chunk tokens: {tokens}")

            headers_in_chunk = self.extract_headers(chunk_text)
            self.update_current_headers(current_headers, headers_in_chunk)

            content, urls, images = self.extract_urls_and_images(chunk_text)

            chunks.append({
                'text': content,
                'metadata': {
                    'tokens': tokens,
                    'headers': dict(current_headers),
                    'urls': urls,
                    'images': images,
                }
            })

            print(f"Chunk processed. New position: {chunk_end}")
            position = chunk_end

        print(f"Split process completed. Total chunks: {len(chunks)}")
        return chunks

    def get_chunk(self, text: str, start: int, limit: int) -> Tuple[str, int]:
        print(f"Getting chunk starting at {start} with limit {limit}")
        
        # Account for token overhead due to formatting
        overhead = self.count_tokens(self.format_for_tokenization('')) - self.count_tokens('')
        
        # Initial tentative end position
        end = min(start + int((len(text) - start) * limit / self.count_tokens(text[start:])), len(text))
        
        # Adjust end to avoid exceeding token limit
        chunk_text = text[start:end]
        tokens = self.count_tokens(chunk_text)
        
        while tokens + overhead > limit and end > start:
            print(f"Chunk exceeds limit with {tokens + overhead} tokens. Adjusting end position...")
            end = self.find_new_chunk_end(text, start, end)
            chunk_text = text[start:end]
            tokens = self.count_tokens(chunk_text)

        # Adjust chunk end to align with newlines
        end = self.adjust_chunk_end(text, start, end, tokens + overhead, limit)

        chunk_text = text[start:end]
        tokens = self.count_tokens(chunk_text)
        print(f"Final chunk end: {end}")
        return chunk_text, end

    def adjust_chunk_end(self, text: str, start: int, end: int, current_tokens: int, limit: int) -> int:
        min_chunk_tokens = int(limit * 0.8)  # Minimum chunk size is 80% of limit

        next_newline = text.find('\n', end)
        prev_newline = text.rfind('\n', start, end)

        # Try extending to next newline
        if next_newline != -1 and next_newline < len(text):
            extended_end = next_newline + 1
            chunk_text = text[start:extended_end]
            tokens = self.count_tokens(chunk_text)
            if tokens <= limit and tokens >= min_chunk_tokens:
                print(f"Extending chunk to next newline at position {extended_end}")
                return extended_end

        # Try reducing to previous newline
        if prev_newline > start:
            reduced_end = prev_newline + 1
            chunk_text = text[start:reduced_end]
            tokens = self.count_tokens(chunk_text)
            if tokens <= limit and tokens >= min_chunk_tokens:
                print(f"Reducing chunk to previous newline at position {reduced_end}")
                return reduced_end

        return end

    def find_new_chunk_end(self, text: str, start: int, end: int) -> int:
        new_end = end - int((end - start) / 10)  # Reduce by 10% each iteration
        if new_end <= start:
            new_end = start + 1  # Ensure at least one character is included
        return new_end

    def extract_headers(self, text: str) -> Dict[str, List[str]]:
        headers: Dict[str, List[str]] = {}
        header_regex = r'(^|\n)(#{1,6})\s+(.*)'
        
        for match in re.finditer(header_regex, text, re.MULTILINE):
            level = len(match.group(2))
            content = match.group(3).strip()
            key = f'h{level}'
            if key not in headers:
                headers[key] = []
            headers[key].append(content)

        return headers

    def update_current_headers(self, current: Dict[str, List[str]], extracted: Dict[str, List[str]]) -> None:
        for level in range(1, 7):
            key = f'h{level}'
            if key in extracted:
                current[key] = extracted[key]
                self.clear_lower_headers(current, level)

    def clear_lower_headers(self, headers: Dict[str, List[str]], level: int) -> None:
        for l in range(level + 1, 7):
            headers.pop(f'h{l}', None)

    def extract_urls_and_images(self, text: str) -> Tuple[str, List[str], List[str]]:
        urls: List[str] = []
        images: List[str] = []
        url_index = 0
        image_index = 0

        def replace_image(match):
            nonlocal image_index
            alt_text = match.group(1)
            image_url = match.group(2)
            images.append(image_url)
            return f'![{alt_text}]($img{len(images)-1})'

        def replace_url(match):
            nonlocal url_index
            link_text = match.group(1)
            url = match.group(2)
            current_index = url_index
            url_index += 1
            return f'[{link_text}]($url{current_index})'

        content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_image, text)
        content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_url, content)

        return content, urls, images 
    
    async def document(self, text: str, model: Optional[str] = None, additional_metadata: Optional[Dict[str, any]] = None) -> Doc:
        await self.initialize_tokenizer()
        tokens = self.count_tokens(text)
        headers = self.extract_headers(text)
        content, urls, images = self.extract_urls_and_images(text)

        metadata = {
            'tokens': tokens,
            'headers': headers,
            'urls': urls,
            'images': images
        }
        if additional_metadata:
            metadata.update(additional_metadata)

        return {
            'text': content,
            'metadata': metadata
        }