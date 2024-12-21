import os
import requests
import json
from dotenv import load_dotenv

class SearchPeopleAndCityService:
    def __init__(self):
        load_dotenv()
        self.personal_api_key = os.getenv("PERSONAL_API_KEY")
        self.base_url = "https://centrala.ag3nts.org"
        self.anti_spam_list = ['no data', '"QUERY"', 'Ł', '[', ']', '**', 'query', 'should', '[**RESTRICTED DATA**]']
        self.list_of_people = []

    def get_location(self, person_id, print_response: bool = False):
        """Get location of a person"""
        if person_id in self.anti_spam_list:
            return None
            
        json_query = {
            "userID": person_id,
            "apikey": self.personal_api_key
        }
        response = requests.post(f"{self.base_url}/gps", json=json_query)
        if print_response:
            print(response.json().get("message"))
        return response.json().get("message")

    def search_person(self, person_name, print_response: bool = False):
        """Search for information about a person"""
        if person_name in self.anti_spam_list:
            return None
            
        json_query = {
            "apikey": self.personal_api_key,
            "query": person_name
        }
        response = requests.post(f"{self.base_url}/people", json=json_query)
        if print_response:
            print(response.json().get("message"))
        return response.json().get("message")

    def search_place(self, city_name, print_response: bool = False):
        """Search for information about a place"""
        if city_name in self.anti_spam_list:
            return None
            
        json_query = {
            "apikey": self.personal_api_key,
            "query": city_name
        }
        response = requests.post(f"{self.base_url}/places", json=json_query)
        if print_response:
            print(response.json().get("message"))
        return response.json().get("message")

    def report_answer(self, city):
        """Submit an answer for the task"""
        answer_json = {
            "task": "loop",
            "apikey": self.personal_api_key,
            "answer": city
        }
        response = requests.post(f"{self.base_url}/report", json=answer_json)
        return response

    def save_data(self, data, filename):
        """Save data to a JSON file"""
        with open(filename, "w") as file:
            json.dump(data, file, indent=4)

    def load_data(self, filename):
        """Load data from a JSON file"""
        if os.path.exists(filename):
            with open(filename, "r") as file:
                return json.load(file)
        return None

    def get_people_from_message(self, message):
        """Extract people names from a message"""
        if not message or message in self.anti_spam_list:
            return []
        return [person for person in message.split() if person.isupper() and person not in self.anti_spam_list]

    def get_cities_from_message(self, message):
        """Extract city names from a message"""
        if not message or message in self.anti_spam_list:
            return []
        return [word for word in message.split() if word not in self.anti_spam_list]


