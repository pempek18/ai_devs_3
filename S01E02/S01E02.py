import requests
import os
from bs4    import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
# Step 0 get information from envs

# Load environment variables from .env file
load_dotenv()

# Access the username and password
login       = os.getenv('LOGIN')
password    = os.getenv('PASSWORD')
openai_api  = os.getenv('OPENAI_API_KEY')

login = login.strip()
password = password.strip()

# Print to check if variables are loaded (remove in production)
print("Username:", login)
print("Password:", password)
print('OpenAi_api:', openai_api)

# Step 1: Set up the URLs and session
login_url = "http://xyz.ag3nts.org/verify"  # Replace with the correct login endpoint
session = requests.Session()

send_auth = session.put('http://xyz.ag3nts.org/verify', json={
    'text':'READY',
    "msgID" : "0"
    })

response_json = send_auth.json()
print(f"mshID: {response_json['msgID']}, text: {response_json['text']}")
question = response_json['text'] 
messageId = response_json['msgID']
# Load the OpenAI API key (make sure you have set it as an environment variable or replace directly)
client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get('OPENAI_API_KEY'),
)
# Read the content of S01E02_chat_content.md
with open('/home/pempek18/Desktop/AI_DEVS/S01E02_chat_content.md', 'r', encoding='utf-8') as file:
    chat_content = file.read()

# print("Chat Content:", chat_content)
# Send the question as a prompt to the ChatGPT API
response = client.chat.completions.create(
    model="gpt-3.5-turbo",  # or 'gpt-4' if available
    messages=[
        {"role": "system", "content": chat_content},
        {"role": "user", "content": question}
    ]
)

# print('chatGPT full response: ', response)   

# Extract and print the response from the API
answer = response.choices[0].message.content.strip()
print("Answer:", answer)

# Use these variables in your login or other logic
message = {
    'text': answer,
    "msgID" : messageId
}

# Step 7: Submit the login form
answer_response = session.post(login_url, json=message)
print(answer_response.request.body)  # Displays the request body

# Assuming `login_response` is the response object from the login request
print("Status Code:", answer_response.status_code)  # Displays the status code (e.g., 200)
print("Response Body:", answer_response.text)       # Displays the response content as a string

# Check if the login was successful
if answer_response.ok:  # or you can check for a specific status code
    # Save the response as an HTML file
    with open('S01E02.html', 'w', encoding='utf-8') as file:
        file.write(answer_response.text)
    print("Response saved as 'login_response.html'")
else:
    print("Login failed with status code:", answer_response.status_code)
