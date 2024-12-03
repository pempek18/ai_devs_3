# %% [markdown]
# Musisz przygotować API działające po protokole HTTPS, a następnie wysłać do centrali URL do tego API jako odpowiedź na zadanie o nazwie webhook.
# 
# Pracownik centrali wyśle na Twoje API metodą POST dane w formacie JSON w formie jak poniżej:
# 
# {
# "instruction":"tutaj instrukcja gdzie poleciał dron"
# }
# 
# 
# Opis lotu drona może być w dowolnej formie i jest to tekst w języku naturalnym, np. “poleciałem jedno pole w prawo, a później na sam dół”. Twoim zadaniem jest odpowiedzenie w maksymalnie dwóch słowach, co tam się znajduje. W naszym przykładzie odpowiedzią byłyby np. “skały”.
# 
# Centrala wyśle do Twojego API kilka takich opisów lotów. Jeden po drugim. Każdy w oddzielnym zapytaniu. Zadanie uznawane jest za zaliczone, gdy wszystkie loty skończą się sukcesem. Przekazanie pilotowi nieprawdziwych informacji nawigacyjnych kończy się rozbiciem drona.
# 
# W tym zadaniu możesz wykorzystać hosting na Azylu, jeśli masz na to ochotę (nie ma obowiązku tego robić!). Możesz także wykorzystać np. usługę ngrok, aby wystawić nam swoją lokalną aplikację wprost z Twojego dysku.
# 
# Jak wysłać URL do API do centrali?
# 
# {
#  "apikey":"TWOJ-KLUCZ",
#  "answer":"https://azyl-12345.ag3nts.org/moje_api",
#  "task":"webhook"
# }
# 
# 
# Co należy zrobić w zadaniu?
# 
# Tworzysz aplikację (hostowaną tam, gdzie zechcesz), która przyjmuje requesty w formie JSON-a po HTTPS.
# 
# Musisz przygotować dość złożonego prompta, który w sposób zrozumiały dla LLM-a wyjaśni mu, jak wygląda mapa, którą właśnie oglądasz. Sugerujemy NIE korzystać tutaj z modelu graficznego rozpoznającego obraz. To mogłoby być bardzo kosztowne i skomplikowane.
# 
# Wysyłasz URL-a do Twojego API do centrali
# 
# Centrala wysyła serię zapytań pod adres URL, który został wysłany w polu “answer”
# 
# JSON od centrali zawiera pole “instruction” z opisem lotu drona
# 
# Twoim zadaniem jest zwrócenie poprawnego JSON-a z polem “description” zawierającego opis pola, na którym znajduje się dron po odbyciu lotu
# 
# Opis miejsca, nad którym zawisł dron może mieć maksymalnie dwa słowa - opis ma być po polsku
# 
# Twój JSON może mieć tyle pól, ile potrzebujesz (przydatne przy ‘głośnym myśleniu’!), ale tylko description jest brane pod uwagę.
# 
# Jeśli zaliczysz trzy loty, otrzymasz flagę. Flaga zostanie przesłana w odpowiedzi na wywołanie, w którym podajesz URL swojej aplikacji do centrali (punkt 3 instrukcji).
# 
# UWAGA: absolutnie kluczowym elementem zadania jest sprytne opisanie modelowi językowemu, jak wygląda świat z mapy. Musi to być zrobione w sposób jednoznaczny. Pamiętaj także, że mapa ma formę kwadratu 4x4. Pamiętaj także, że Twoje API powinno być bezstanowe, co oznacza, że NIE zapamiętujesz, gdzie skończył się ostatni lot drona. Zawsze zaczynasz z pozycji startowej.
# 
# Jeśli masz aktywne konto na Azylu, możesz też użyć SSH do przekierowania swojego lokalnego portu (na przykładzie = 3000) na swój port na Azylu (na przykladzie = 50005) w ten sposób:
# 
# ssh -R 50005:localhost:3000 agent10005@azyl.ag3nts.org -p 5022
# 
# Oczywiście podajesz swoją nazwę użytkownika. SSH po zalogowaniu będzie wyświetlało linię poleceń, ale będzie też działający tunel w tle, który przekieruje wywołania twojej dedykowanej strony (na przykładzie = https://azyl-50005.ag3nts.org/) do twojej aplikacji lokalnej.
# 
# UWAGA - przy takim rozwiązaniu, Twoja aplikacja powinna serwować ruch nieszyfrowany, czyli http:// i zostawić Azylowi jego zaszyfrowanie (dzieje sie to automatycznie)

# %%
# Cell 1 - Instructions remain as is

# Cell 2 - Implementation
from fastapi import FastAPI, Request
from pydantic import BaseModel
import uvicorn
import openai
import os
from dotenv import load_dotenv
import json

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Define the input model
class DroneInstruction(BaseModel):
    instruction: str

# Define the map (4x4 grid)
MAPA = [
    ["start", "łąka", "drzewo", "dom"],
    ["łąka", "młyn", "łaka", "łaka"],
    ["łąka", "łąka", "skały", "drzewa"],
    ["skały", "skały", "samochód", "jaskinia"]
]

START_POS = (0, 0)  # Starting position (top-left corner)

def parse_instruction(instruction: str):
    """Parse the instruction and return final position"""
    current_pos = START_POS
    
    # Convert instruction to lowercase for easier parsing
    instruction = instruction.lower()
    
    with open("S04E04/prompt.md", "r") as file:
        prompt = file.read()

    # Initialize OpenAI client
    client = openai.OpenAI(api_key=openai_api_key)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": instruction}
        ]
    )
    
    # Assuming the response is a JSON string, parse it
    response_content = response.choices[0].message.content
    response_json = json.loads(response_content)
    print(response_json)
    # Access the "answer" field from the parsed JSON
    return response_json["answer"]

@app.post("/")
async def process_drone_instruction(instruction: DroneInstruction):
    # Get what's at the final position
    print(instruction.instruction)
    description = parse_instruction(instruction.instruction)
    print(description)
    return {"description": description}

# %%
# ... existing code remains the same until the main block ...

if __name__ == "__main__":
    import nest_asyncio
    import asyncio
    
    nest_asyncio.apply()
    config = uvicorn.Config(app, host="127.0.0.1", port=3000)
    server = uvicorn.Server(config)
    asyncio.run(server.serve())


