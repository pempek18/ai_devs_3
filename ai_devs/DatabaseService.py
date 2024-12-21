import os
import requests
import json
from dotenv import load_dotenv
from .OpenAIService import OpenAIService

class DatabaseService:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("PERSONAL_API_KEY")
        self.base_url = "https://centrala.ag3nts.org/apidb"
        self.openai = OpenAIService()
        self.tables_structure = {}
    
    def _execute_query(self, query):
        """Execute SQL query and return response"""
        payload = {
            "task": "database",
            "apikey": self.api_key,
            "query": query
        }
        response = requests.post(self.base_url, json=payload)
        return response.json()

    def get_tables(self):
        """Get list of all tables in database"""
        return self._execute_query("show tables")

    def get_tables_structure(self):
        """Get structure of all tables in database"""
        tables = self.get_tables()
        for table in tables["reply"]:
            table_name = table["Tables_in_banan"]
            query = f"show create table {table_name}"
            self.tables_structure[table_name] = self._execute_query(query)
        return self.tables_structure
    def get_data_from_table(self, query):
        """Get data from a table"""
        return self._execute_query(query)

    def generate_query(self, question):
        """Generate SQL query using AI based on the question"""
        if not self.tables_structure:
            self.get_tables_structure()
            
        response = self.openai.completion(messages=[
            {
                "role": "system",
                "content": f'''You are a helpful assistant that helps to find answer in database.
                          You are given a query and a structure of database.
                          You need to prepare a SQL query that will answer the question.
                          datacenter struct : {self.tables_structure}.
                          answer only with SQL query
                          think twice if the name of the table is correct'''
            },
            {"role": "user", "content": question}
        ])
        
        query = response.choices[0].message.content.replace("```sql", "").replace("```", "")
        return query

    def execute_ai_query(self, question):
        """Generate and execute query based on the question"""
        query = self.generate_query(question)
        return self._execute_query(query)
    
    def get_person_details(self, question):
        """Get details of a person from database"""
        query = self.generate_query(question)
        print(query)
        result = self._execute_query(query)
        print(result)
        return result
    
