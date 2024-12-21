# %% [markdown]
# Dotarliśmy do logów pochodzących z agenta, który niegdyś wykorzystywany był przez Centralę. Rozwiązanie to było przejęte od sił robotów, jednak teraz straciliśmy do niego dostęp, a jest nam ono nadal potrzebne. Na podstawie analizy logów, trzeba wywnioskować, jak ten agent do tej pory działał i do czego służył. Twoim zadaniem jest odtworzenie od zera tego agenta we własnym środowisku. Oczywiście nie musi on zwracać tych samych komunikatów na ekran, co oryginał, ale byłoby super, gdyby zwracał te same wyniki co soft, którego niegdyś używaliśmy. Przeprowadź niezbędną analizę, zapoznaj się z pytaniem Centrali i zwróć potrzebne dane w ramach zadania o nazwie ‘gps’.
# 
# Oto wspomniane logi:
# 
# https://centrala.ag3nts.org/data/TUTAJ-KLUCZ/gps.txt
# 
# Tutaj pytanie od centrali:
# 
# https://centrala.ag3nts.org/data/TUTAJ-KLUCZ/gps_question.json
# 
# Do wykonania tego zadanie będziesz potrzebować API do bazy danych z S03E03 oraz API do sprawdzania lokalizacji osób z S03E04.
# 
# Co należy zrobić w zadaniu?
# 
# Przeczytaj logi z niedziałającego agenta
# 
# Spróbuj wywnioskować, jaki był cel istnienia tego agenta i co on tak naprawdę robił
# 
# Wczytaj dane wejściowe (pytanie) z pliku JSON dostarczonego przez Centralę
# 
# Zaklasyfikuj, jakiego rodzaju informacje trzeba pobrać i skąd (masz do dyspozycji dwa API)
# 
# Odwołaj się do odpowiednich API, połącz wymagane dane i odeślij je do Centrali jako task ‘gps’.
# 
# Jeśli wszystkie dane zostaną przesłane poprawnie, Centrala odpowie flagą.
# 
# Oczekiwany format odpowiedzi:
# 
# {
#     "imie": {
#         "lat": 12.345,
#         "lon": 65.431
#     },
#     "kolejne-imie": {
#         "lat": 19.433,
#         "lon": 12.123
#     }
# }
# 
# 

# %%
import requests
import os
import json
import sys
from dotenv import load_dotenv

load_dotenv()

# %%
personal_api_key = os.getenv("PERSONAL_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")


# %%
logs = requests.get(f"https://centrala.ag3nts.org/data/{personal_api_key}/gps.txt").text
question = requests.get(f"https://centrala.ag3nts.org/data/{personal_api_key}/gps_question.json").json()

with open("logs.txt", "w") as f:
    f.write(logs)

with open("question.json", "w") as f:
    json.dump(question, f, indent=2)

print(logs)
print(question)

# %%
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_devs import Agent

# Initialize services
agent = Agent(1)


# %%
agent.run(question, logs)



