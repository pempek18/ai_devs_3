import aiohttp
import json
import asyncio
import os
from dotenv import load_dotenv
from typing import Set, Dict, List

class AgentsService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://centrala.ag3nts.org"
        self.visited_names: Set[str] = set()
        self.visited_places: Set[str] = set()
        self.connections: Dict[str, List[str]] = {}

    async def get_barbara_note(self) -> str:
        """Download Barbara's note from the server"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/dane/barbara.txt") as response:
                return await response.text()

    async def query_people(self, name: str) -> List[str]:
        """Query the people API for locations"""
        async with aiohttp.ClientSession() as session:
            data = {
                "apikey": self.api_key,
                "query": name
            }
            async with session.post(f"{self.base_url}/people", json=data) as response:
                result = await response.json()
                return result.get("places", [])

    async def query_places(self, city: str) -> List[str]:
        """Query the places API for people"""
        async with aiohttp.ClientSession() as session:
            data = {
                "apikey": self.api_key,
                "query": city
            }
            async with session.post(f"{self.base_url}/places", json=data) as response:
                result = await response.json()
                return result.get("people", [])

    def extract_names_and_places(self, text: str) -> tuple[set[str], set[str]]:
        """Extract names and places from text - this is a placeholder, 
        you'll need to implement proper extraction logic"""
        # This is a simple implementation - you might need more sophisticated text processing
        words = text.split()
        names = {word for word in words if word.istitle() and len(word) > 2}
        # You might want to add known cities manually or use NLP
        print(f"names: {names}")
        return names, set()

    async def process_name(self, name: str):
        """Process a single name recursively"""
        if name in self.visited_names:
            return
        
        print(f"Processing name: {name}")
        self.visited_names.add(name)
        
        # Get places for this person
        places = await self.query_people(name)
        self.connections[name] = places
        
        # Process each new place
        for place in places:
            if place not in self.visited_places:
                await self.process_place(place)

    async def process_place(self, place: str):
        """Process a single place recursively"""
        if place in self.visited_places:
            return
        
        print(f"Processing place: {place}")
        self.visited_places.add(place)
        
        # Get people in this place
        people = await self.query_places(place)
        
        # Process each new person
        for person in people:
            if person not in self.visited_names:
                await self.process_name(person)

    async def report_location(self, location: str) -> bool:
        """Report Barbara's location to the central system"""
        async with aiohttp.ClientSession() as session:
            data = {
                "apikey": self.api_key,
                "answer": location
            }
            async with session.post(f"{self.base_url}/report", json=data) as response:
                result = await response.json()
                return result.get("success", False)

    async def find_barbara(self):
        """Main function to find Barbara"""
        # Get Barbara's note
        note = await self.get_barbara_note()
        print("Barbara's note:", note)

        # Extract initial names and places
        names, places = self.extract_names_and_places(note)
        
        # Process initial names
        for name in names:
            await self.process_name(name)

        # Process initial places
        for place in places:
            await self.process_place(place)

        # Print all connections found
        print("\nConnections found:")
        for person, locations in self.connections.items():
            print(f"{person}: {locations}")

async def main():
    load_dotenv()
    api_key = os.getenv("PERSON_API_KEY")
    service = AgentsService(api_key)
    await service.find_barbara()

if __name__ == "__main__":
    asyncio.run(main())