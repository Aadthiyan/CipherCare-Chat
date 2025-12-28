import os
import logging
import time
from typing import List
import numpy as np
from huggingface_hub import InferenceClient

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Embedding Service using Hugging Face Inference API
    Supports both remote API (low-memory) and future local model loading
    
    Configuration via environment variables:
        HUGGINGFACE_API_KEY: API key for HF Inference API
        HUGGINGFACE_MODEL_NAME: Model identifier (default: sentence-transformers/all-mpnet-base-v2)
        EMBEDDING_DIMENSION: Output dimension (default: 768)
    """
    
    def __init__(self, model_name: str = None, embedding_dim: int = None):
        """
        Initialize Embedding Service with configuration from environment or parameters
        
        Args:
            model_name: HuggingFace model to use (overrides HUGGINGFACE_MODEL_NAME env var)
            embedding_dim: Output embedding dimension (overrides EMBEDDING_DIMENSION env var)
        """
        # Get configuration from environment with sensible defaults
        self.model_name = model_name or os.getenv("HUGGINGFACE_MODEL_NAME", "sentence-transformers/all-mpnet-base-v2")
        self.embedding_dim = embedding_dim or int(os.getenv("EMBEDDING_DIMENSION", "768"))
        
        # Get API key
        self.api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "HUGGINGFACE_API_KEY not found in environment variables. "
                "Please set it in your .env file or Render environment variables."
            )
        
        # Initialize HF Inference Client
        self.client = InferenceClient(api_key=self.api_key, timeout=30)
        
        logger.info(f"✓ Initialized HF Inference API embedder")
        logger.info(f"  Model: {self.model_name}")
        logger.info(f"  Dimension: {self.embedding_dim}")
        logger.info(f"  Mode: Remote Inference API (low-memory)")
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text string using HF Inference API
        
        Args:
            text: Input text to embed
            
        Returns:
            Embedding vector as list of floats (768-dimensional by default)
            
        Raises:
            ValueError: If text is empty
            Exception: If embedding generation fails
        """
        if not text or not text.strip():
            logger.warning("Empty text provided, returning zero vector")
            return [0.0] * self.embedding_dim
        
        # Truncate text if too long (API has limits)
        if len(text) > 5000:
            text = text[:5000]
            logger.debug("Truncated text to 5000 characters")
        
        try:
            # Call HF Inference API using official client
            # feature_extraction() returns embeddings for the input text
            result = self.client.feature_extraction(
                text=text,
                model=self.model_name
            )
            
            # Handle different response formats
            # The API returns a list of embeddings (one per token or pooled)
            if isinstance(result, list) and len(result) > 0:
                # If result is list of lists (token embeddings), apply mean pooling
                if isinstance(result[0], (list, np.ndarray)):
                    embedding = np.mean(result, axis=0)
                else:
                    embedding = np.array(result)
            elif isinstance(result, (np.ndarray, list)):
                # Already a vector
                embedding = np.array(result)
            else:
                logger.warning("Empty or unexpected embedding result, returning zero vector")
                return [0.0] * self.embedding_dim
            
            # Normalize for cosine similarity
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            return embedding.tolist()
                
        except Exception as e:
            error_msg = str(e)
            
            # Check for specific HF API errors
            if "410" in error_msg or "no longer supported" in error_msg:
                logger.error(f"HF API endpoint error (410): {error_msg}")
                logger.info("Using correct endpoint via InferenceClient")
            elif "503" in error_msg or "loading" in error_msg.lower():
                logger.warning(f"Model loading on HF servers, will retry: {error_msg}")
                # Wait and retry once
                time.sleep(20)
                try:
                    result = self.client.feature_extraction(
                        text=text,
                        model=self.model_name
                    )
                    if isinstance(result, list) and len(result) > 0:
                        if isinstance(result[0], (list, np.ndarray)):
                            embedding = np.mean(result, axis=0)
                        else:
                            embedding = np.array(result)
                    else:
                        embedding = np.array(result)
                    norm = np.linalg.norm(embedding)
                    if norm > 0:
                        embedding = embedding / norm
                    return embedding.tolist()
                except Exception as retry_error:
                    logger.error(f"Retry failed: {retry_error}")
                    raise
            
            logger.error(f"Embedding generation failed: {error_msg}")
            raise Exception(f"Failed to generate embedding: {error_msg}")
    
    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch
        Calls API sequentially to avoid rate limits
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
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
        
        logger.info(f"✓ Generated {len(embeddings)} embeddings (dim: {self.embedding_dim})")
        return embeddings


class ClinicalEmbedder(EmbeddingService):
    """
    Backwards-compatible wrapper for existing code using ClinicalEmbedder
    Inherits all functionality from EmbeddingService
    """
    
    def __init__(self, model_name="sentence-transformers/all-mpnet-base-v2", max_length=512, device="cpu"):
        """
        Initialize Clinical Embedder (legacy interface)
        
        Args:
            model_name: HuggingFace model to use
            max_length: Maximum token length (kept for compatibility, not used)
            device: Device to use (kept for compatibility, not used)
        """
        super().__init__(model_name=model_name, embedding_dim=768)
        self.max_length = max_length
        self.device = device
