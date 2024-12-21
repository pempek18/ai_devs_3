import requests
import os
import json
import sys
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_devs import Agent
load_dotenv()

personal_api_key = os.getenv("PERSONAL_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
password_url = "https://rafal.ag3nts.org/b46c3"
agent = Agent(1)



# Step 1: Send password to get hash
with open("./S05E03/source.html", "r") as file:
    source = file.read()
password_response, status_code = agent.ai_rafal_endpoint_tool(password_url, "NONOMNISMORIAR")
password_response_json = json.loads(password_response)  # Convert string to JSON
hash_token = password_response_json["message"]

# Step 2: Send hash to get timestamp, signature and URLs
sign_response , status_code = agent.ai_rafal_computer_tool(hash_token)
sign_data = json.loads(sign_response)['message']
print(json.dumps(sign_data, indent=4))

# Step 3: Fetch data from both URLs concurrently using async
challenge_data = {
  "apikey":personal_api_key,
  "timestamp": sign_data["timestamp"],
  "signature": sign_data["signature"],
  "answer": "Twoja odpowiedź w dowolnym formacie"
}

urls = [sign_data["challenges"][0], sign_data["challenges"][1]]
print(urls)
responses = []
for url in urls:
    response = requests.get(url, json=challenge_data)
    response_json = response.json()
    # print(json.dumps(response_json, indent=4))
    if ".html" in response_json["task"].lower():
        response_json["task"] = source
    response = agent.answer_multi_question(response_json["task"], response_json['data'])
    response = eval(response.replace("'", ""))
    for answer in response: 
        responses.append(answer)
    # responses.append(response)

# print(responses)
challenge_data["answer"] = responses
print(json.dumps(challenge_data, indent=4))
# Step 4: Submit final answer
final_response = requests.post(password_url, json=challenge_data)
print(json.dumps(final_response.json(), indent=4))


# %%
"""
Nie wiemy, jak to się stało, ale Rafał uzyskał dostęp do super komputerów nieznanych w 2024 roku. Wykorzystywał je do uruchamiania lokalnych modeli językowych, które generowały dane w niewyobrażalnym — jak na czasy, w których jesteś — tempie.

Nasi technicy zauważyli, że wykorzystał on tę technologię do zabezpieczenia dostępu do swojego komputera. Znasz już hasło do pierwszej warstwy zabezpieczeń. Druga natomiast to zamek czasowy, na którego otwarcie masz tylko 6 sekund.

Współczesne modele językowe są zbyt wolne, aby temu podołać i właśnie dlatego Rafał jako jedyny człowiek z dostępem do takich modeli i sprzętu do ich uruchomienia, użył ich jako zabezpieczenia do swojego komputera.

Zadanie polega na pobraniu aktualnego tokena dostępowego z endpointa odkrytego w jednej z poprzedniej misji. To ten hash, który ma 32 znaki. Wyślij go z powrotem do tego samego endpointa w polu “sign”. Zostanie on podpisany. Otrzymasz nowy klucz oraz timestamp, a do tego dwa adresy URL z pytaniami, na które trzeba odpowiedzieć. Kolejność i zbiór pytań zmienia się co pewien czas.

Twoim zadaniem jest odpowiedzieć na nie wszystkie w dowolnym formacie. Ważne, aby to było SZYBKIE rozwiązanie.

Oczekiwana forma odpowiedzi wysłanej do endpointa Rafała (nie do centrali!)

{
  "apikey":TWÓJ KLUCZ API",
  "timestamp": znacznik-czas-pobrany-od-Rafałą,
  "signature": "podpis cyfrowy znacznika czasu",
  "answer": "Twoja odpowiedź w dowolnym formacie"
}


UWAGA: wszystkie odpowiedzi musza być odesłane w języku polskim.

Co należy zrobić w zadaniu?

Przypomnij sobie jaki był poprawny adres URL do API na komputerze Rafała (rafal.ag3nts.org)

Wyślij tam hasło pozyskane w poprzedniej misji (NONOMNISMORIAR) w polu “password”

Zapamiętaj otrzymany HASH

Wyślij HASH w polu “sign” do tego samego adresu URL. Otrzymasz timestamp, sygnaturę oraz dwa adresy URL, których zawartość dość często się zmienia.

Przeczytaj zawartość podanych adresów URL i wykonaj na danych z pola “data” polecenie zawarte w polu “task”

Scal wyniki z obu zadań (source0 + source1) i wyslij je w dowolnej formie (string, tablica, obiekt JSON - jak zechcesz) w polu “answer”

Zadbaj o to, aby cała procedura zajęła nie więcej jak 6 sekund.

Jeśli zmieścisz się w czasie, poprawnie odpowiesz na wszystkie pytania, a jednocześnie nie wyślesz odpowiedzi nadmiarowych (np. pytania z poprzedniego wywołania, o które system nie zapytał tym razem), to w odpowiedzi otrzymasz flagę.

Wraz z flagą otrzymasz jeszcze notatkę od Rafała 🚩

🚨 UWAGA 🚨

Ze względu na to, że jest to zadanie polegające na skrajnej optymalizacji szybkości działania modelu, obawiamy się, że modele lokalne mogą nie podołać temu zadaniu. Sugerujemy posługiwanie się modelami chmurowymi. Samo sprytne pisanie promptów może nie pozwolić na zaliczenie tego zadania. Prawdopodobnie przyda się tutaj także umiejętność tworzenia efektywnej architektury aplikacji. Nie oczekuj w tym zadaniu deterministycznego działania Twojego mechanizmu. To jest walka z czasem.
"""