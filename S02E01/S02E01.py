import requests
import os  
import dotenv
import groq
import openai
dotenv.load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')
elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
groq_api_key = os.getenv('GROQ_API_KEY')
person_api_key = os.getenv('PERSONAL_API_KEY')
answer_url = "https://centrala.ag3nts.org/report"

answer_json = {
    "task": "mp3",
    "apikey": person_api_key,
    "answer": "test"
}
#1 load the content of voice file to ai and translate to text and save to file
def transcribe_audio(audio_file_path: str):
    groq_client = groq.Groq(api_key=groq_api_key)
    response = groq_client.audio.transcriptions.create(
        file=(audio_file_path, open(audio_file_path, "rb")),
        language="pl",
        model="whisper-large-v3"
    )
    return response.text
sum_transcription = ""
audio_files_dir = "S02E01/przesluchania"        
for audio_file in os.listdir(audio_files_dir):
    if os.path.exists(f"{audio_files_dir}/{audio_file}.txt"):
        continue
    else:
        if audio_file.endswith(".m4a"):
            transcription = transcribe_audio(f"{audio_files_dir}/{audio_file}")
            with open(f"{audio_files_dir}/{audio_file}.txt", "w") as file:
                file.write(transcription)
            sum_transcription += transcription
            print(f"Transcription of {audio_file}: {transcription}") 
if not os.path.exists(f"{audio_files_dir}/sum.txt"):
    with open(f"{audio_files_dir}/sum.txt", "w") as file:
        file.write(sum_transcription)

# send the text to the answer url
with open("S02E01/context.md", "r") as file:
    context = file.read()
with open(f"{audio_files_dir}/sum.txt", "r") as file:
    sum_transcription = file.read()
openai_client = openai.OpenAI(api_key=openai_api_key)
response = openai_client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "system", "content": context}, {"role": "user", "content": sum_transcription}]
)
print(response.choices[0].message.content)

# send the answer to the answer url
answer_json["answer"] = response.choices[0].message.content
response = requests.post(answer_url, json=answer_json)
print(response.json())