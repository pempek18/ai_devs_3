import requests
import os
import json
from bs4    import BeautifulSoup
from dotenv import load_dotenv
import sys 
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 
import chatGpt
# Step 0 get information from envs

# Load environment variables from .env file
load_dotenv()

# Access the username and password
ai_devs_api_key = os.getenv('PERSONAL_API_KEY')

# Print to check if variables are loaded (remove in production)

# download json file
txt_url = f"https://centrala.ag3nts.org/data/{ai_devs_api_key}/cenzura.txt"  # Replace with the correct login endpoint
session = requests.Session()
content = session.get(txt_url)

# Save the content as an HTML file
# script_name = os.path.basename(__file__).replace('.py', '_content.html')
# with open(script_name, 'w', encoding='utf-8', errors='ignore') as file:
#     file.write(str(content.headers))
#     file.write(str(content.text))


print(content.headers)
print(content.text.encode('utf-8').decode('unicode-escape'))

chat_context = open(f"{currentdir}/context.md", "r").read()

chatGpt = chatGpt.ChatGpt()
response = chatGpt.get_response(chat_context, content.text.encode('utf-8').decode('unicode-escape'))

print("chat respond: " + response.choices[0].message.content)

response_json_url = 'https://centrala.ag3nts.org/report'
answer_json = {
    "task": "CENZURA",
    "apikey": ai_devs_api_key,
    "answer": response.choices[0].message.content.encode('utf-8').decode('unicode-escape')
}
answer_response = session.post(response_json_url, json=answer_json, data=json.dumps(answer_json).encode('utf-8').decode('unicode-escape'))
print(answer_response.request.body)  # Displays the request body

# Assuming `login_response` is the response object from the login request
print("Status Code:", answer_response.status_code)  # Displays the status code (e.g., 200)
print("Response Body:", answer_response.text.encode('utf-8').decode('unicode-escape'))       # Displays the response content as a string

# Check if the login was successful
if answer_response.ok:  # or you can check for a specific status code
    # Save the response as an HTML file
    script_name = os.path.basename(__file__).replace('.py', '.html')
    with open(script_name, 'w', encoding='utf-8') as file:
        file.write(answer_response.text)
    print(f"Response saved as {script_name}")
else:
    print("Login failed with status code:", answer_response.status_code)