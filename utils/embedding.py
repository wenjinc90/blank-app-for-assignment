"""
Embedding utilities for processing and generating embeddings using OpenAI API.
"""

import openai
import numpy as np
from typing import List, Dict, Any, Optional

class EmbeddingProcessor:
    """Class for handling text embeddings and similarity search."""
    
    AVAILABLE_MODELS = {
        "text-embedding-3-small": "Newest, most efficient model (1536 dimensions)",
        "text-embedding-3-large": "Most capable model (3072 dimensions)",
        "text-embedding-ada-002": "Legacy model (1536 dimensions)"
    }

    def __init__(self):
        self.api_key: Optional[str] = None
        self.model: str = "text-embedding-3-small"
        self.embeddings: List[List[float]] = []
        self.texts: List[str] = []

    def set_api_key(self, api_key: str) -> None:
        """Set the OpenAI API key."""
        self.api_key = api_key
        openai.api_key = api_key

    def set_model(self, model: str) -> None:
        """Set the embedding model to use."""
        if model in self.AVAILABLE_MODELS:
            self.model = model
        else:
            raise ValueError(f"Model {model} not supported. Choose from {list(self.AVAILABLE_MODELS.keys())}")

    def generate_embeddings(self, texts: List[str], progress_callback=None) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        if not self.api_key:
            raise ValueError("API key not set. Call set_api_key first.")

        embeddings = []
        for i, text in enumerate(texts):
            response = openai.embeddings.create(
                input=text,
                model=self.model
            )
            embeddings.append(response.data[0].embedding)
            
            if progress_callback:
                progress_callback((i + 1) / len(texts))

        self.embeddings = embeddings
        self.texts = texts
        return embeddings

    def find_most_similar(self, query: str) -> Dict[str, Any]:
        """Find the most similar text to a query."""
        if not self.embeddings or not self.texts:
            raise ValueError("No embeddings generated yet. Call generate_embeddings first.")

        query_response = openai.embeddings.create(
            input=query,
            model=self.model
        )
        query_embedding = np.array(query_response.data[0].embedding)
        doc_embeddings = np.array(self.embeddings)
        
        # Calculate similarities using dot product and normalization
        similarities = np.dot(doc_embeddings, query_embedding) / (
            np.linalg.norm(doc_embeddings, axis=1) * np.linalg.norm(query_embedding) + 1e-8
        )
        
        top_idx = int(np.argmax(similarities))
        return {
            'text': self.texts[top_idx],
            'similarity_score': float(similarities[top_idx]),
            'index': top_idx
        }

    @classmethod
    def get_available_models(cls) -> Dict[str, str]:
        """Get dictionary of available embedding models and their descriptions."""
        return cls.AVAILABLE_MODELS.copy()
