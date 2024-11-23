import requests
import os
import json
from dotenv import load_dotenv

class Answer:
    def __init__(self, task):
        self.task = task
        self.answer_url = "https://centrala.ag3nts.org/report"   
        load_dotenv()
        self.personal_api_key = os.getenv("PERSONAL_API_KEY")
        self.answer_json = {
            "task": self.task,
            "apikey": self.personal_api_key,
            "answer": {}
        }

    def send_answer(self, answer):
        print(answer)
        self.answer_json["answer"] = answer
        answer_response = requests.post(self.answer_url, json=self.answer_json)
        print("Status Code:", answer_response.status_code)  # Displays the status code (e.g., 200)
        print("Response Body:", answer_response.text.encode('utf-8').decode('unicode-escape'))       # Displays the response content as a string

if __name__ == "__main__":
    with open("S02E04/answer_modified.json", "r") as f:
        answer_json = json.load(f)
    answer = Answer(task="kategorie")
    answer.send_answer(answer=answer_json)