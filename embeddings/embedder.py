import os
import logging
import requests
from typing import List
import numpy as np

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClinicalEmbedder:
    """
    Clinical Embedder using Hugging Face Inference API
    This version uses HF's API instead of loading models locally,
    making it suitable for deployment on low-memory environments (Render free tier)
    """
    
    def __init__(self, model_name="sentence-transformers/all-mpnet-base-v2", max_length=512, device="cpu"):
        """
        Initialize Clinical Embedder with Hugging Face Inference API
        
        Args:
            model_name: HuggingFace model to use
            max_length: Maximum token length (not used for API but kept for compatibility)
            device: Not used for API but kept for compatibility
        """
        self.max_length = max_length
        self.model_name = model_name
        self.embedding_dim = 768  # all-mpnet-base-v2 produces 768-dim embeddings
        
        # Get API key from environment
        self.api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "HUGGINGFACE_API_KEY not found in environment variables. "
                "Please set it in your .env file or Render environment variables."
            )
        
        # Hugging Face Inference API endpoint - use /models/ path for text embeddings
        # This endpoint works with feature-extraction models
        self.api_url = f"https://api-inference.huggingface.co/models/{model_name}"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        
        logger.info(f"✓ Initialized HF Inference API embedder: {model_name} (dim: {self.embedding_dim})")
        logger.info("  Using Hugging Face API - no local model loading required")
        
    def get_embedding(self, text: str) -> List[float]:
        """
        Generates embedding for a single text string using HF Inference API.
        
        Args:
            text: Input text to embed
            
        Returns:
            768-dimensional embedding vector as list of floats
        """
        if not text or not text.strip():
            logger.warning("Empty text provided, returning zero vector")
            return [0.0] * self.embedding_dim
        
        # Truncate text if too long (API has limits)
        if len(text) > 5000:  # Conservative limit
            text = text[:5000]
            logger.debug(f"Truncated text to 5000 characters")
        
        try:
            # Call Hugging Face Inference API
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={"inputs": text, "options": {"wait_for_model": True}},
                timeout=30  # 30 second timeout
            )
            
            if response.status_code == 200:
                # API returns embeddings as nested list
                result = response.json()
                
                # Handle different response formats
                if isinstance(result, list):
                    if isinstance(result[0], list):
                        # Mean pooling over token embeddings
                        embedding = np.mean(result, axis=0)
                    else:
                        # Already pooled
                        embedding = np.array(result)
                else:
                    raise ValueError(f"Unexpected response format: {type(result)}")
                
                # Normalize (L2 normalization for cosine similarity)
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm
                
                return embedding.tolist()
                
            elif response.status_code == 503:
                # Model is loading, wait and retry once
                logger.warning("Model is loading on HF servers, waiting 20s and retrying...")
                import time
                time.sleep(20)
                
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json={"inputs": text, "options": {"wait_for_model": True}},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list):
                        if isinstance(result[0], list):
                            embedding = np.mean(result, axis=0)
                        else:
                            embedding = np.array(result)
                    else:
                        raise ValueError(f"Unexpected response format: {type(result)}")
                    
                    norm = np.linalg.norm(embedding)
                    if norm > 0:
                        embedding = embedding / norm
                    
                    return embedding.tolist()
                else:
                    raise Exception(f"HF API error after retry: {response.status_code} - {response.text}")
                    
            else:
                raise Exception(f"HF API error: {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            logger.error("HF API request timed out after 30 seconds")
            raise Exception("Embedding request timed out. Please try again.")
            
        except Exception as e:
            logger.error(f"Error getting embedding from HF API: {e}")
            raise Exception(f"Failed to generate embedding: {str(e)}")
    
    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        Note: Calls API sequentially to avoid rate limits.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of 768-dimensional embedding vectors
        """
        embeddings = []
        for i, text in enumerate(texts):
            if i > 0 and i % 10 == 0:
                logger.info(f"Processed {i}/{len(texts)} embeddings...")
            
            try:
                embedding = self.get_embedding(text)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Failed to embed text {i}: {e}")
                # Return zero vector on failure
                embeddings.append([0.0] * self.embedding_dim)
        
        return embeddings
