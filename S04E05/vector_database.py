import json
import sys
import os

# load modules
# Go up one directory to the AI_DEVS root
parent_dir = os.path.dirname(os.getcwd())
sys.path.append(parent_dir)

# Verify the path
print("Added to Python path:", parent_dir)
print("Python path now includes:", sys.path)

# Then import
from ai_devs.OpenAIService import OpenAIService
from ai_devs.VectorService import VectorService
from ai_devs.TextService import TextSplitter

#initialize services
openai = OpenAIService();
vector_service = VectorService(openai);
text_splitter = TextSplitter();

class QuestionAnalyzer:
    def __init__(self, openai: OpenAIService, vector_service: VectorService, text_splitter: TextSplitter):
        self.openai = openai
        self.vector_service = vector_service
        self.text_splitter = text_splitter
        self.COLLECTION_NAME = "S04E05"
        
    async def initialize_data(self, data_json) -> None:
        points = []
        for item in data_json:
            doc = await self.text_splitter.document(item["text"], "gpt-4o", {"name": item["name"]})
            points.append(doc)
        # print(json.dumps(points, indent=4, ensure_ascii=False))
        await self.vector_service.initialize_collection_with_data(self.COLLECTION_NAME, points)

    async def process_question(self, query: str, data_json: list) -> dict:
        # Determine relevant reports
        prompt_pick = open("./prompt_pick.md", "r").read()
        determine_raport_date = self.openai.completion(
            messages=[
                {"role": "system", "content": prompt_pick + f" Pick between {data_json}. just with name."},
                {"role": "user", "content": query}
            ]
        )
        
        page_names = determine_raport_date.choices[0].message.content.split(',') if determine_raport_date.choices[0].message.content else []
        page_names = [page_name.strip() for page_name in page_names]

        # Create filter
        filter_dict = {
            "must": [
                {
                    "key": "name",
                    "match": {
                        "value": page_name
                    }
                } for page_name in page_names
            ]
        }

        # Search and check relevance
        search_results = await self.vector_service.perform_search(self.COLLECTION_NAME, query, filter_dict, 3)
        relevance_checks = []
        with open("./prompt_relevent.md", "r") as file:
            prompt_relevent = file.read()
        for result in search_results:
            content = f"Query: {query}\nText: {result.payload.get('text', '')}"
            relevance_check = self.openai.completion(
                messages=[
                    {"role": "system", "content": prompt_relevent},
                    {"role": "user", "content": content}
                ]
            )
            is_relevant = float(relevance_check.choices[0].message.content) == 1 or result.score > 0.1
            result_dict = dict(result)
            result_dict["is_relevant"] = is_relevant
            relevance_checks.append(result_dict)
                    # Create table-like output
        print("\n{:<20} {:<50} {:<10}".format("name", "text", "score"))
        print("-" * 80)
        for result in relevance_checks:
            name = result["payload"]["name"].replace("_", "-").replace(".txt", "")
            text = result["payload"]["text"][:47] + "..." if len(result["payload"]["text"]) > 50 else result["payload"]["text"]
            text = text.replace("\n", " ")
            score = f"{result['score']:.3f}"
            print("{:<20} {:<50} {:<10}".format(name, text, score))
        
        # Sort by score and mark highest scoring result as relevant
        relevance_checks.sort(key=lambda x: x["score"], reverse=True)
        if relevance_checks:
            relevance_checks[0]["is_relevant"] = True
            for i in range(1, len(relevance_checks)):
                relevance_checks[i]["is_relevant"] = False

        relevant_results = [result for result in relevance_checks if result["is_relevant"]]
        print(relevant_results)
        print(f"Query: {query}")

        # Add check for empty results
        if not relevant_results:
            return {
                "query": query,
                "answer": {"error": "No relevant results found"},
                "relevant_results": []
            }        

        # Get final answer
        content = f"Query: {query}\nText: {relevant_results[0]['payload']['text']}"
        prompt = open("./prompt.md", "r").read()
        response = self.openai.completion(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": content},
            ],
        )
        
        return {
            "query": query,
            "answer": response.choices[0].message.content,
        }

    async def process_all_questions(self, questions: dict, data_json: list) -> list:
        # Initialize data once
        await self.initialize_data(data_json)
        
        results = []
        for question_id, question in questions.items():
            print(f"\nProcessing question {question_id}...")
            result = await self.process_question(question, data_json)
            results.append({
                "question_id": question_id,
                **result
            })
        return results

# Usage example:
"""
# Initialize services
openai = OpenAIService()
vector_service = VectorService(openai)
text_splitter = TextSplitter()

# Create analyzer instance
analyzer = QuestionAnalyzer(openai, vector_service, text_splitter)

# Process all questions
results = await analyzer.process_all_questions(questions, data_json)

# Print results
for result in results:
    print(f"\nQuestion {result['question_id']}:")
    print(f"Query: {result['query']}")
    print(f"Answer: {result['answer']}")
"""