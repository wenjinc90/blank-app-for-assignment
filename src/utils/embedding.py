"""
Embedding utilities for processing and generating embeddings using OpenAI API.
"""

import json
import pickle
import openai
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

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

        # Enhance text descriptions with additional context
        enhanced_texts = []
        for text in texts:
            # Add more context for walls
            if "IfcWall" in text:
                # Include keywords that might help identify loadbearing walls
                context = " This wall has properties that may indicate if it's loadbearing: "
                context += text
                enhanced_texts.append(context)
            else:
                enhanced_texts.append(text)

        embeddings = []
        for i, text in enumerate(enhanced_texts):
            response = openai.embeddings.create(
                input=text,
                model=self.model
            )
            embeddings.append(response.data[0].embedding)
            
            if progress_callback:
                progress_callback((i + 1) / len(texts))

        self.embeddings = embeddings
        self.texts = texts  # Store original texts
        return embeddings

    def find_most_similar(self, query: str) -> Dict[str, Any]:
        """Find the most similar text to a query."""
        return self.find_top_similar(query, top_k=1)[0]

    def find_top_similar(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Find exactly K most similar texts, regardless of similarity score."""
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
        
        # Get top K indices
        top_k = min(top_k, len(similarities))  # Make sure we don't exceed array length
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Create result list
        results = []
        for idx in top_indices:
            results.append({
                'text': self.texts[idx],
                'similarity_score': float(similarities[idx]),
                'index': int(idx)
            })
        
        return results
    
    def find_similar_by_threshold(self, query: str, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Find all texts with similarity above the given threshold."""
        if not self.embeddings or not self.texts:
            raise ValueError("No embeddings or texts found. Please generate embeddings first.")
            
        # Debug print
        print(f"Number of embeddings: {len(self.embeddings)}")
        print(f"Number of texts: {len(self.texts)}")
        
        query_response = openai.embeddings.create(
            input=query,
            model=self.model
        )
        query_embedding = np.array(query_response.data[0].embedding)
        doc_embeddings = np.array(self.embeddings)
        
        # Calculate similarities
        similarities = np.dot(doc_embeddings, query_embedding) / (
            np.linalg.norm(doc_embeddings, axis=1) * np.linalg.norm(query_embedding) + 1e-8
        )
        
        # Filter by threshold and sort by similarity
        results = []
        for idx, score in enumerate(similarities):
            if score >= threshold:
                results.append({
                    'text': self.texts[idx],
                    'similarity_score': float(score),
                    'index': int(idx)
                })
        
        # Sort by similarity score (highest first)
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return results

    @classmethod
    def get_available_models(cls) -> Dict[str, str]:
        """Get dictionary of available embedding models and their descriptions."""
        return cls.AVAILABLE_MODELS.copy()
        
    def save_embeddings(self, file_path: str, format: str = 'pickle') -> None:
        """Save embeddings and texts to a file.
        
        Args:
            file_path: Path to save the embeddings file
            format: 'pickle' or 'json' format for saving
        """
        data = {
            'embeddings': self.embeddings,
            'texts': self.texts,
            'model': self.model
        }
        
        try:
            if format == 'pickle':
                with open(file_path, 'wb') as f:
                    pickle.dump(data, f)
            elif format == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f)
            else:
                raise ValueError("Format must be either 'pickle' or 'json'")
        except Exception as e:
            raise ValueError(f"Error saving embeddings: {e}")
    
    def load_embeddings(self, file_path: str, format: str = 'pickle') -> None:
        """Load embeddings and texts from a file.
        
        Args:
            file_path: Path to the embeddings file
            format: 'pickle' or 'json' format for loading
        """
        try:
            if format == 'pickle':
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
            elif format == 'json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                raise ValueError("Format must be either 'pickle' or 'json'")
            
            self.embeddings = data['embeddings']
            self.texts = data['texts']
            self.model = data['model']
        except Exception as e:
            raise ValueError(f"Error loading embeddings: {e}")
