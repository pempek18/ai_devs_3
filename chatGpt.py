import os
from openai import OpenAI
from dotenv import load_dotenv

class ChatGpt:
    def __init__(self):
        self.client = OpenAI(
            # This is the default and can be omitted
            load_dotenv(),
            api_key=os.environ.get('OPENAI_API_KEY'),
        )

    def get_response(self, chat_content, question):
        # Send the question as a prompt to the ChatGPT API
        response = self.client.chat.completions.create(
            model="gpt-4o",  # or 'gpt-4' if available
            messages=[
                {"role": "system", "content": chat_content},
                {"role": "user", "content": question, "type": "json"},
            ]
        )
        return response