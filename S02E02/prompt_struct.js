{
    "model": "gpt-4o",
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": "image/png;base64,..."
                },
                {
                    "type": "text",
                    "text": "What is this image?"
                }
            ]
        }
    ],
    "max_tokens": 300
}