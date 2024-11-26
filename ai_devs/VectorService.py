import os
from qdrant_client import QdrantClient
from qdrant_client.http import models
from uuid import uuid4
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import OpenAIService

class VectorService:
    def __init__(self, openai_service: OpenAIService):
        self.client = QdrantClient(
            url=os.getenv('QDRANT_URL'),
            api_key=os.getenv('QDRANT_API_KEY')
        )
        self.openai_service = openai_service

    async def ensure_collection(self, name: str) -> None:
        """Ensure a collection exists, create it if it doesn't."""
        collections = self.client.get_collections()
        if not any(c.name == name for c in collections.collections):
            self.client.create_collection(
                collection_name=name,
                vectors_config=models.VectorParams(
                    size=1024,
                    distance=models.Distance.COSINE
                )
            )

    async def initialize_collection_with_data(self, name: str, points: List[Dict[str, Any]]) -> None:
        """Initialize a collection with data if it doesn't exist."""
        collections = self.client.get_collections()
        if not any(c.name == name for c in collections.collections):
            await self.ensure_collection(name)
            await self.add_points(name, points)

    async def add_points(self, collection_name: str, points: List[Dict[str, Any]]) -> None:
        """Add points to the collection.
        
        Args:
            collection_name (str): Name of the collection to add points to
            points (List[Dict[str, Any]]): List of points to add, each containing text and optional metadata
            
        Returns:
            None: This method doesn't return anything, it just performs the operations
            
        The -> None in the function signature indicates this methdo performs actions but doesn't 
        return any value. It:
        1. Creates embeddings for each point
        2. Saves the points to a JSON file
        3. Uploads the points to Qdrant
        But has no return value
        """
        points_to_upsert = []
        
        for point in points:
            embedding = await self.openai_service.create_jina_embedding(point['text'])
            
            point_data = {
                'id': point.get('id', str(uuid4())),
                'vector': embedding,
                'payload': {
                    'text': point['text'],
                    **(point.get('metadata', {}))
                }
            }
            points_to_upsert.append(point_data)

        # Save points to JSON file
        points_file_path = Path(__file__).parent / 'points.json'
        with open(points_file_path, 'w') as f:
            json.dump(points_to_upsert, f, indent=2)
            print("file save")

        # Upsert points to Qdrant
        self.client.upsert(
            collection_name=collection_name,
            wait=True,
            points=[
                models.PointStruct(
                    id=p['id'],
                    vector=p['vector'],
                    payload=p['payload']
                ) for p in points_to_upsert
            ]
        )
    async def perform_search(self, 
                           collection_name: str, 
                           query: str, 
                           filter: Optional[Dict[str, Any]] = None, 
                           limit: int = 5) -> List[Dict[str, Any]]:
        """Perform a search in the collection."""
        query_embedding = await self.openai_service.create_jina_embedding(query)
        
        search_result = self.client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=limit,
            query_filter=filter if filter else None,
            with_payload=True
        )
        
        return search_result 