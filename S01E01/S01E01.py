import requests
import os
from bs4    import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
import webbrowser
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
login_url = "http://xyz.ag3nts.org"  # Replace with the correct login endpoint
session = requests.Session()

# Step 2: Perform a GET request to fetch the login page
response = session.get(login_url)
soup = BeautifulSoup(response.text, 'html.parser')

# Step 3: Extract any CSRF tokens or hidden fields (if necessary)
csrf_token = soup.find('input', {'name': 'csrf_token'})['value'] if soup.find('input', {'name': 'csrf_token'}) else None

# Step 4: Extract the question text from the third textbox
# Locate the <p> tag containing the question
question_field = soup.find('p', {'id': 'human-question'})

# Extract the text, handling <br> tags by replacing them with newline characters or spaces
if question_field:
    question = question_field.get_text(separator=' ').strip()  # Replaces <br> with a space and trims whitespace
    question = question.replace("Question: ","").strip()
    print("Extracted Question:", question)
else:
    print("Question not found")
# Step 6: Prepare payload for login

# Load the OpenAI API key (make sure you have set it as an environment variable or replace directly)
client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get('OPENAI_API_KEY'),
)

# Send the question as a prompt to the ChatGPT API
response = client.chat.completions.create(
    model="gpt-3.5-turbo",  # or 'gpt-4' if available
    messages=[
        {"role": "system", "content": "You are an expert in historical facts. You need to answear only with one number"},
        {"role": "user", "content": question}
    ]
)

print('chatGPT full response: ', response)   

# Extract and print the response from the API
answer = int(response.choices[0].message.content.strip())
print("Answer:", answer)

# Use these variables in your login or other logic
login_payload = {
    'username': login,
    'password': password,
    'answer': answer
    # 'csrf_token': csrf_token  # Include if applicable
}

# Step 7: Submit the login form
login_response = session.post(login_url, data=login_payload, allow_redirects=True)

# Assuming `login_response` is the response object from the login request
print("Status Code:", login_response.status_code)  # Displays the status code (e.g., 200)
print("Response Body:", login_response.text)       # Displays the response content as a string

# Check if the login was successful
if login_response.ok:  # or you can check for a specific status code
    # Save the response as an HTML file
    with open('S01E01.html', 'w', encoding='utf-8') as file:
        file.write(login_response.text)
    print("Response saved as 'S01E01.html'")
else:
    print("Login failed with status code:", login_response.status_code)
