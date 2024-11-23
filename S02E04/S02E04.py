import os
import openai
import groq
import requests
import json
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
personal_api_key = os.getenv("PERSONAL_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")



with open('S02E04/context.md', 'r') as file:
    context = file.read()

def encode_image_to_base64(image_path):
    import base64
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
    
# Initialize OpenAI client
client = openai.OpenAI(api_key=openai_api_key)

# Get base64 encoded image
def analyze_image(image_path: str):
    base64_image = encode_image_to_base64(image_path)

    # Create message with image
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are an expert in image analysis. You are given an image and you need to respond with text written on the image."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    },
                    {
                        "type": "text", 
                        "text": "What is written on the image?"
                    }
                ]
            }
        ],
        max_tokens=3000
    )
    return response.choices[0].message.content    

#1 load the content of voice file to ai and translate to text and save to file
def transcribe_audio(audio_file_path: str):
    groq_client = groq.Groq(api_key=groq_api_key)
    response = groq_client.audio.transcriptions.create(
        file=(audio_file_path, open(audio_file_path, "rb")),
        language="pl",
        model="whisper-large-v3"
    )
    return response.text

answer = {
    "people": [],
    "hardware": [],
    "unknown": [] 
}

# transcribe all audio files in the directory
files_dir = "pliki_z_fabryki"        
files_transcriptions_dir = "S02E04/files_transcriptions"
for file in os.listdir(files_dir):
    if os.path.exists(f"{files_transcriptions_dir}/{file}.txt"):
        continue
    transcription = None
    if file.endswith(".mp3"):
        transcription = transcribe_audio(f"{files_dir}/{file}")
    elif file.endswith(".png"):
        transcription = analyze_image(f"{files_dir}/{file}")
    elif file.endswith(".txt"):
        with open(f"{files_dir}/{file}", "r") as f:
            transcription = f.read()
    if transcription is not None:
        with open(f"{files_transcriptions_dir}/{file}.txt", "w") as f:
            f.write(transcription)

for file in os.listdir(files_transcriptions_dir):
    if file.endswith(".txt"):
        with open(f"{files_transcriptions_dir}/{file}", "r") as f:
            transcription = f.read()
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": context
                    },
                    {
                        "role": "user",
                        "content": transcription
                    }
                ]
            )
            print(f"{response.choices[0].message.content} : {file}") 
            filename = file.removesuffix('.txt')
            if response.choices[0].message.content == "person": 
                answer["people"].append(filename)
            elif response.choices[0].message.content == "machine":
                answer["hardware"].append(filename)
            else:
                answer["unknown"].append(filename)

print("People: ", len(answer["people"]), "  ", answer["people"])
print("Hardware: ", len(answer["hardware"]), "  ", answer["hardware"])
print("Unknown: ", len(answer["unknown"]), "  ", answer["unknown"])

answer.pop("unknown")
with open("S02E04/answer.json", "w") as f:
    json.dump(answer, f)

answer_json = {
    "task": "kategorie",
    "apikey": personal_api_key,
    "answer": answer
}
answer_url = "https://centrala.ag3nts.org/report"
answer_response = requests.post(answer_url, json=answer_json)
print(answer_response.request.body)  # Displays the request body

# Assuming `login_response` is the response object from the login request
print("Status Code:", answer_response.status_code)  # Displays the status code (e.g., 200)
print("Response Body:", answer_response.text.encode('utf-8').decode('unicode-escape'))       # Displays the response content as a string