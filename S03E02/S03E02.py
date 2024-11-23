# %%
import asyncio
import os
import requests
import json
from dotenv import load_dotenv

# %%
load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
personal_api_key = os.getenv("PERSONAL_API_KEY")

# %%
#create json with data
data = []
files_names = []
for file in os.listdir("pliki_z_fabryki/do-not-share"):
    files_names.append(file)
    with open(f"pliki_z_fabryki/do-not-share/{file}", "rb") as f:
        text = f.read()
        text = text.decode("utf-8")
        text = text.replace("\n", " ")
        data.append( {"name": file, "text": text})
print(files_names)
print(json.dumps(data, indent=4, ensure_ascii=False))

# %%
from OpenAIService import OpenAIService
from VectorService import VectorService
from TextService import TextSplitter

openai = OpenAIService();
vector_service = VectorService(openai);
text_splitter = TextSplitter();


# %%
COLLECTION_NAME = "s03e02"
async def initialize_data(openai: OpenAIService, 
                        vector_service: VectorService, 
                        text_splitter: TextSplitter) -> None:
    points = []
    for item in data:
        doc = await text_splitter.document(item["text"], "gpt-4o", {"name": item["name"]})
        points.append(doc)
    print(json.dumps(points, indent=4, ensure_ascii=False))
    await vector_service.initialize_collection_with_data(COLLECTION_NAME, points)

# %%
asyncio.run(initialize_data(openai, vector_service, text_splitter))

# %%
query = "Kradzież prototypu, kradzież broni"
determine_raport_date = openai.completion(  
    messages=[
        {"role": "system", "content": f"""You are a helpful assistant that determines the name of the raport.
                                        Pick between {files_names}. just with name. If both are relevant, list them comma-separated. Write back with the name(s) and nothing else."""},
        {"role": "user", "content": query}
    ]
)   
print(determine_raport_date)
raportNames = determine_raport_date.choices[0].message.content.split(',') if determine_raport_date.choices[0].message.content else []
raportNames = [raportName.strip() for raportName in raportNames]
print(raportNames)

# %%
# Create filter based on authors
filter_dict = {
    "should": [
        {
            "key": "name",
            "match": {"value": raportName}
        } for raportName in raportNames
    ]
} if raportNames else None

# Perform search
async def perform_search(vector_service: VectorService, query: str, filter_dict: dict, count: int) -> list:
    return await vector_service.perform_search(COLLECTION_NAME, query, filter_dict, count)

search_results = asyncio.run(perform_search(vector_service, query, filter_dict, 3))
print(search_results)

# %%
# Check relevance
relevance_checks = []
for result in search_results:
    content = f"Query: {query}\nText: {result.payload.get('text', '')}"
    print(content)
    relevance_check = openai.completion(
        messages=[
            {"role": "system", "content": "You are a helpful assistant that determines if a given text is relevant to a query. Respond with 1 if relevant, 0 if not relevant."},
            {"role": "user", "content": content}
        ]
    )
    print(relevance_check)
    is_relevant = relevance_check.choices[0].message.content == "1"
    result_dict = dict(result)
    result_dict["is_relevant"] = is_relevant
    relevance_checks.append(result_dict)

relevant_results = [result for result in relevance_checks if result["is_relevant"]]
print(relevant_results)

# %%
# Print results
print(f"Query: {query}")
print(f"raportName(s): {', '.join(raportNames)}")

# Create table-like output
print("\n{:<20} {:<50} {:<10}".format("name", "text", "score"))
print("-" * 80)

# %% [markdown]
# # Dotąd zrobiłem ten przykład ale nie mogę dokończyć 

# %%
answer = raportNames[0].replace("_", "-").replace(".txt", "")
answer_json = {
    "task": "wektory",
    "apikey": personal_api_key,
    "answer": answer
}

# %%
answer_url = "https://centrala.ag3nts.org/report"
answer_response = requests.post(answer_url, json=answer_json)
print(answer_response.request.body)  # Displays the request body

# Assuming `login_response` is the response object from the login request
print("Status Code:", answer_response.status_code)  # Displays the status code (e.g., 200)
print("Response Body:", answer_response.text.encode('utf-8'))       # Displays the response content as a string

# %%



