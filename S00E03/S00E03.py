import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

ai_devs_api_key = os.getenv('PERSONAL_API_KEY')

request_url = f"https://poligon.aidevs.pl/dane.txt"
answer_url = f"https://poligon.aidevs.pl/verify"

request = requests.get(request_url)

answer = []
for line in request.text.splitlines():
    answer.append(line)

print(request.text)

json_data = {
    "task": "POLIGON",
    "apikey": ai_devs_api_key,
    "answer": answer
}

print(json_data)

response = requests.post(answer_url, json=json_data)
print(response.text)
