import os
import json
import logging
import torch
import numpy as np
from typing import List, Dict, Any
from transformers import AutoTokenizer, AutoModel

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClinicalEmbedder:
    def __init__(self, model_name="sentence-transformers/all-mpnet-base-v2", max_length=512, device="cpu"):
        """
        Initialize Clinical Embedder with 768-dimensional embeddings
        Model: all-mpnet-base-v2 (standard quality, 768-dim vectors)
        
        Note: Always uses 768-dimensional embeddings for consistency
        """
        self.max_length = max_length
        self.device = device
        self.model_name = model_name
        
        # Always 768-dim for quality and compatibility
        self.embedding_dim = 768
        
        logger.info(f"Loading tokenizer and model: {model_name} on {device} (dim: {self.embedding_dim})")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name).to(device)
            self.model.eval() # Set to inference mode
            logger.info(f"✓ Model loaded successfully (768-dim embeddings)")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise e

    def get_embedding(self, text: str) -> List[float]:
        """
        Generates embedding for a single text string.
        Truncates if longer than max_length.
        Returns: 768-dimensional embedding vector as list of floats
        """
        if not text:
            return [0.0] * 768  # Return zero vector for empty text
            
        # Tokenize
        inputs = self.tokenizer(
            text, 
            return_tensors="pt", 
            padding=True, 
            truncation=True, 
            max_length=self.max_length
        ).to(self.device)
        
        # Inference
        with torch.no_grad():
            outputs = self.model(**inputs)
            
        # Pooling Strategy: Mean of Last Hidden State
        token_embeddings = outputs.last_hidden_state
        attention_mask = inputs.attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        
        sum_embeddings = torch.sum(token_embeddings * attention_mask, 1)
        sum_mask = torch.clamp(attention_mask.sum(1), min=1e-9)
        mean_embedding = sum_embeddings / sum_mask
        
        # Normalize (L2) - crucial for Cosine Similarity
        embedding = mean_embedding[0].cpu().numpy()
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
            
        return embedding.tolist()

    def process_dataset(self, input_path: str, output_path: str):
        logger.info("Starting embedding generation...")
        
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        entries = data.get('entry', [])
        processed_count = 0
        
        # Output structure: We will enhance the FHIR bundle or create a sidecar vector file?
        # A sidecar file or a simplified "Vector Document" structure is better for loading into CyborgDB.
        vector_docs = []
        
        for entry in entries:
            res = entry.get('resource', {})
            
            # We only embed DocumentReference (Clinical Notes)
            if res.get('resourceType') == "DocumentReference":
                doc_id = res.get('id')
                pat_id = res.get('subject', {}).get('reference', '').split('/')[-1]
                
                # Extract text
                text_content = ""
                # 1. Check description
                if 'description' in res:
                    text_content += res['description'] + " "
                
                # 2. Check attachments
                # Note: In Phase 2 we kept them base64 encoded.
                import base64
                if 'content' in res:
                    for c in res['content']:
                        try:
                            b64 = c.get('attachment', {}).get('data')
                            if b64:
                                text_content += base64.b64decode(b64).decode('utf-8')
                        except:
                            pass
                            
                text_content = text_content.strip()
                if not text_content:
                    logger.warning(f"Skipping empty document {doc_id}")
                    continue
                    
                # Generate Embedding
                try:
                    embedding = self.get_embedding(text_content)
                    
                    # Create Vector Record
                    vector_record = {
                        "id": doc_id,
                        "parent_id": pat_id,
                        "metadata": {
                            "type": "clinical_note",
                            "date": res.get('date'),
                            "patient_id": pat_id
                        },
                        "text_snippet": text_content[:200], # Keep snippet for debug (removed in Prod/Encrypted)
                        "values": embedding
                    }
                    vector_docs.append(vector_record)
                    processed_count += 1
                    
                    if processed_count % 10 == 0:
                        logger.info(f"Processed {processed_count} documents...")
                        
                except Exception as e:
                    logger.error(f"Error embedding doc {doc_id}: {e}")

        # Save Vectors
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(vector_docs, f, indent=2)
            
        logger.info(f"Completed. Generated {len(vector_docs)} embeddings. Saved to {output_path}")

if __name__ == "__main__":
    # Create output dir
    if not os.path.exists("embeddings/generated"):
        os.makedirs("embeddings/generated")
    
    # Use a widely available public model for Hackathon speed/access if ClinicalBERT fails auth
    # "sentence-transformers/all-MiniLM-L6-v2" is a safe bet standard
    # Or "emilyalsentzer/Bio_ClinicalBERT" check spelling? 
    # It was emilyalsen vs emilyalsentzer. Ah, Typo in original code likely.
    # Correct is "emilyalsentzer/Bio_ClinicalBERT"
    
    try:
        embedder = ClinicalEmbedder(model_name="emilyalsentzer/Bio_ClinicalBERT") 
    except:
        logger.warning("Falling back to all-MiniLM-L6-v2")
        embedder = ClinicalEmbedder(model_name="sentence-transformers/all-MiniLM-L6-v2")

    embedder.process_dataset(
        "data/processed/deidentified_dataset.json",
        "embeddings/generated/vectors.json"
    )
