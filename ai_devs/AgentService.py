import requests
import openai
import io
import os
import json
import base64
import groq
from PIL import Image
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, Any
from .DatabaseService import DatabaseService
from .SearchPeopleAndCityService import SearchPeopleAndCityService

class Agent:
    def __init__(self, max_trials: int = 10):
        load_dotenv()
        self.max_trials = max_trials
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.personal_api_key = os.getenv("PERSONAL_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.db_service = DatabaseService()
        self.search_service = SearchPeopleAndCityService()
        self.client = openai.OpenAI(api_key=self.openai_api_key)
        self.memory = {}
        self.memory_key = 0 
        self._tools = [
            {
                "name": "ai_rafal_endpoint",
                "description": "Use this tool to get the flag from the AI Rafal endpoint.",
                "parameters": "password"
            },
            {
                "name": "ai_rafal_computer",
                "description": "Use this tool to get the flag from the AI Rafal computer.",
                "parameters": "hash_token"
            },
            {
                "name" : "set_to_memory",
                "description": "Use this tool to save information in memory of the agent.",
                "parameters": "memory"
            },
            {
                "name" : "get_from_memory",
                "description": "Use this tool to get information from memory of the agent.",
                "parameters": "memory"
            },
            {
                "name": "image_to_text",
                "description": "Use this tool to generate text from an image.",
                "parameters": "image"
            },
            {
                "name": "audio_to_text",
                "description": "Use this tool to convert audio to text.",
                "parameters": "audio"
            },            
            {
                "name": "final_answer",
                "description": "Use this tool to provide a final answer.",
                "parameters": "answer"
            }
        ]
    def run(self, question, context: str):
        trials = 0
        last_response = None
        while trials < self.max_trials:
            try:             
                # Process the data and prepare response
                response = self._process_question(question, context, last_response)

                # update last response
                last_response = response
                
                # Submit answer to Centrala
                result = self._submit_answer(response)
                
                # If successful, break the loop
                if "FLG" in result:
                    print("Task completed successfully!")
                    break
                    
                trials += 1
                
            except Exception as e:
                print(f"Error occurred: {str(e)}")
                trials += 1
                
            if trials == self.max_trials:
                print("Max trials reached without success")
    def tools(self, question):
        prompt = f'''
            Decide which tool to use based on the question.
            Answer only with the tools name.
            Answer in this JSON format:
            {{
                "tools": ["tool_name1", "tool_name2"]
            }}
            Do not answer any questions.
            Only job is to decide which tool to use.
            <TOOLS>
            {", ".join([t["name"] for t in self._tools]) if self._tools else "No tools available"}
            </TOOLS>
        '''
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(question)}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content or "{}")
    def plan(self, question):
        prompt = f'''
            Analyze the conversation and determine the most appropriate next step. Focus on making progress towards the overall goal while remaining adaptable to new information or changes in context.
            <prompt_objective>
            Determine the single most effective next action based on the current context, user needs, and overall progress. Return the decision as a concise JSON object.
            </prompt_objective>

            <prompt_rules>
            - ALWAYS focus on determining only the next immediate step
            - ONLY choose from the available tools listed in the context
            - ASSUME previously requested information is available unless explicitly stated otherwise
            - NEVER provide or assume actual content for actions not yet taken
            - ALWAYS respond in the specified JSON format
            - CONSIDER the following factors when deciding:
            1. Relevance to the current user need or query
            2. Potential to provide valuable information or progress
            3. Logical flow from previous actions
            - ADAPT your approach if repeated actions don't yield new results
            - USE the "final_answer" tool when you have sufficient information or need user input
            - OVERRIDE any default behaviors that conflict with these rules
            </prompt_rules>

            <context>
                <current_date>Current date: {datetime.now().isoformat()}</current_date>
                <last_message>Last message: "{question["question"]}"</last_message>
                <available_tools>Available tools: {", ".join([tool["name"] for tool in question["tools"]]) if question["tools"] else "No tools available"}</available_tools>
                <actions_taken>Actions taken: {
                "\n".join([
                    f'<action name="{action["name"]}" params="{action["parameters"]}" description="{action["description"]}">\n' +
                    ("\n".join([
                        f'<result name="{result["metadata"]["name"]}" url="{result["metadata"].get("urls", ["no-url"])[0]}">\n'
                        f'{result["text"]}\n'
                        '</result>'
                        for result in action["results"]
                    ]) if action["results"] else "No results for this action") +
                    '\n</action>'
                    for action in question["actions"]
                ]) if question["actions"] else "No actions taken"}
            </context>

            Respond with the next action in this JSON format:
            {{
                "_reasoning": "Brief explanation of why this action is the most appropriate next step",
                "tool": "tool_name",
                "query": "Precise description of what needs to be done, including any necessary context"
            }}
            If you have sufficient information to provide a final answer or need user input, use the "final_answer" tool.
            '''

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(question)}
            ],
            json_mode=True
        )

        return json.loads(response.choices[0].message.content or "{}")
    def set_to_memory(self, remember):
        self.memory[self.memory_key] = remember
        self.memory_key += 1
        return remember
    def get_from_memory(self):
        return self.memory
    def image_to_text(self, image):
        if isinstance(image, str) and 'http' in image:
            # Extract audio URL from string if it contains other text
            if isinstance(image, str):
                import re
                url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                urls = re.findall(url_pattern, image)
                if urls:
                    image = urls[0]
                    # Download image from URL
                    response = requests.get(image)
                    img_data = response.content

                    response = self.client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {
                                "role": "system", 
                                "content": "You get a image and need to response with a text description of the image."
                            },
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": image  # Use direct URL instead of base64
                                        }
                                    },
                                    {
                                        "type": "text",
                                        "text": "Describe this image."
                                    }
                                ]
                            }
                        ],
                        max_tokens=300
                    )
                    return response.choices[0].message.content
        elif isinstance(image, str) and '.png' in image:
            with open(image, "rb") as f:
                img_data = f.read()
                img_base64 = base64.b64encode(img_data).decode('utf-8')

                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system", 
                            "content": "You get a image and need to response with a text description of the image. If there is a text in the image, return the original text insted of description."
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{img_base64}"
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": "return the original text in the image"
                                }
                            ]
                        }
                    ],
                    max_tokens=300
                )
                return response.choices[0].message.content
    def audio_to_text(self, audio):
        groq_client = groq.Groq(api_key=self.groq_api_key)
        # Download audio from URL if provided
        if isinstance(audio, str) and 'http' in audio:
            # Extract audio URL from string if it contains other text
            if isinstance(audio, str):
                import re
                url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                urls = re.findall(url_pattern, audio)
                if urls:
                    audio = urls[0]
            response = requests.get(audio)
            # Save audio data to a temporary file
            temp_file = "temp_audio.wav"
            with open(temp_file, "wb") as f:
                f.write(response.content)
            audio = temp_file
        response = groq_client.audio.transcriptions.create(
            file=open(audio, "rb"),
            language="pl", 
            model="whisper-large-v3"
        )
        return response.text
    def ai_rafal_endpoint_tool(self, endpoint, password):
        response = requests.post(endpoint, json={"password": password})
        return response.text, response.status_code
    def ai_rafal_computer_tool(self, hash_token):
        response = requests.post("https://rafal.ag3nts.org/b46c3", json={"sign": hash_token})
        print(response.text)
        return response.text, response.status_code

    def _analyze_context(self, question: Dict[str, str], context: str, last_response: Dict[str, Any]):
        """Analyze the context and extract relevant information"""
        prompt = f"""
        Analyze this question and extract all person names that need to be located, excluding Barbara:
        {question['question']}
        
        Return only a Python list of names in uppercase, e.g.: ["NAME1", "NAME2"]
        """

        if last_response:
            prompt += f"\n\nHere is the last response from the Centrala: {last_response}"

        if context:
            prompt += f"\n\nHere is the context: {context}"
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts names from text."},
                {"role": "user", "content": prompt}
            ]
        )
        return context
    def answer_multi_question(self, task: str, questions: list):
        prompt = f"""
        Answer the question in short and concise way.
        Respond in these same format as the questions.
        Oldest polish anthem is Bogurodzica.
        Task: {task}
        """

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(questions)}
            ]
        )
        return response.choices[0].message.content
    def _analyze_city_or_person(self, name, print_response: bool = False):
        """Analyze if the name is a city or a person"""
        prompt = f"""
        - Analyze name and determine if name is a city or a person
        - respond only with "city" or "person" or "unknown"
        - city names are in polish language
        - AZAZEL is a person name
        """

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": name}
            ]
        )
        if print_response:
            print(response.choices[0].message.content)
        return response.choices[0].message.content
    
    def _analyze_question(self, question: Dict[str, str]) -> list:
        """Use OpenAI to analyze the question and extract relevant names"""
        prompt = f"""
        WIEMY is not a person name.
        Answer only with polish names.
        If NAME have polish letters, replace them with latin letters. 
        example : Ł replace with L.
        Analyze this question and extract all person names that need to be located, excluding Barbara:
        {question['question']}
        
        Return only a Python list of names in uppercase, e.g.: ["NAME1", "NAME2"]
        """
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts names from text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        try:
            # Safely evaluate the response to get the list
            names = eval(response.choices[0].message.content)
            return names if isinstance(names, list) else []
        except:
            return []
    
    def _process_question(self, question: Dict[str, str], context: str, last_response: Dict[str, Any]) -> Dict[str, Any]:
        """Process the question and prepare response"""
        result = {}
        
        # Extract names using OpenAI
        names = self._analyze_question(question)
        
        # Process each person in the list
        for name in names:
            print(f"Processing {name}")
            try:
                # Skip Barbara as mentioned in the requirements
                if name.upper() == "BARBARA":
                    continue

                city_or_person = self._analyze_city_or_person(name, print_response=True)
                if city_or_person == "city":
                    # Get cities
                    persons = self.search_service.search_place(name, print_response=True)
                    persons = persons.split(" ")
                    for person in persons:
                        if person not in names:
                            names.append(person)
                    continue
                elif city_or_person == "person":
                    # Get person's details from database
                    person_data = self.db_service._execute_query(f"SELECT * FROM users WHERE username = '{name}'")
                    # Get location data using search service
                    location = self.search_service.get_location(person_data['reply'][0]['id'], print_response=True)

                result[name] = location
                
            except Exception as e:
                print(f"Error processing {name}: {str(e)}")
                continue
            
        return result
    
    def _submit_answer(self, answer):
        """Submit answer to Centrala"""
        answer_json = {
            "task": "gps",
            "apikey": self.personal_api_key,
            "answer": answer
        }
        answer_url = f"https://centrala.ag3nts.org/report"
        answer_response = requests.post(answer_url, json=answer_json)
        print(answer_response.request.body)  # Displays the request body

        # Assuming `login_response` is the response object from the login request
        print("Status Code:", answer_response.status_code)  # Displays the status code (e.g., 200)
        print("Response Body:", answer_response.text.encode('utf-8'))       # Displays the response content as a string    ``        
        return answer_response.json()
