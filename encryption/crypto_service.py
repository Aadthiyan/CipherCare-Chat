import os
import json
import base64
import logging
from typing import Tuple, Dict, Any
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KeyManager:
    """
    Simulates a secure Key Management Service (KMS).
    In a real deployment, this would interface with AWS KMS or HashiCorp Vault.
    For this hackathon, we use a local Master Key stored securely (simulated).
    """
    def __init__(self, key_path="encryption/master.key"):
        self.key_path = key_path
        self._load_or_create_master_key()

    def _load_or_create_master_key(self):
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.key_path), exist_ok=True)
        
        if os.path.exists(self.key_path):
            with open(self.key_path, 'rb') as f:
                self.master_key = f.read()
        else:
            logger.info("Generating new Master Key...")
            # Generate 256-bit AES key (32 bytes)
            self.master_key = AESGCM.generate_key(bit_length=256)
            with open(self.key_path, 'wb') as f:
                f.write(self.master_key)
            # Secure permissions (Windows ACL would be applied here in real world, or chmod 600 on Linux)

    def generate_data_key(self) -> Tuple[bytes, bytes]:
        """
        Generates a new Data Key.
        Returns: (Wrapped Data Key, Plaintext Data Key)
        """
        # 1. Generate Plaintext Data Key
        data_key = AESGCM.generate_key(bit_length=256)
        
        # 2. Encrypt Data Key with Master Key (Envelope Encryption)
        aesgcm = AESGCM(self.master_key)
        nonce = os.urandom(12)
        encrypted_data_key = aesgcm.encrypt(nonce, data_key, None)
        
        # Format wrapped key: nonce + ciphertext
        wrapped_key = nonce + encrypted_data_key
        
        return wrapped_key, data_key

    def decrypt_data_key(self, wrapped_key: bytes) -> bytes:
        """
        Decrypts a wrapped Data Key using the Master Key.
        """
        aesgcm = AESGCM(self.master_key)
        nonce = wrapped_key[:12]
        ciphertext = wrapped_key[12:]
        return aesgcm.decrypt(nonce, ciphertext, None)


class EncryptionService:
    def __init__(self, key_manager: KeyManager):
        self.kms = key_manager

    def encrypt_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypts a vector record using a fresh Data Key (Envelope Encryption).
        """
        # 1. Get a fresh Data Key
        wrapped_key, data_key = self.kms.generate_data_key()
        
        # 2. Serialize payload to bytes
        # We encrypt the sensitive parts: vectors + metadata + text snippet
        # ID and Parent ID remain plaintext for routing/indexing (but could be hashed if strictly private)
        sensitive_payload = {
            "values": record['values'],
            "metadata": record['metadata'],
            "text_snippet": record.get('text_snippet', '')
        }
        payload_bytes = json.dumps(sensitive_payload).encode('utf-8')
        
        # 3. Encrypt payload with Data Key
        aesgcm = AESGCM(data_key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, payload_bytes, None) # Additional data could be context
        
        # 4. Construct Encrypted Envelope
        encrypted_record = {
            "id": record['id'],
            "parent_id": record['parent_id'],
            "version": "v1",
            "algo": "AES-256-GCM",
            "wrapped_key": base64.b64encode(wrapped_key).decode('utf-8'),
            "iv": base64.b64encode(nonce).decode('utf-8'),
            "ciphertext": base64.b64encode(ciphertext).decode('utf-8')
        }
        
        return encrypted_record

    def decrypt_record(self, encrypted_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypts a record.
        """
        # 1. Decode fields
        wrapped_key = base64.b64decode(encrypted_record['wrapped_key'])
        nonce = base64.b64decode(encrypted_record['iv'])
        ciphertext = base64.b64decode(encrypted_record['ciphertext'])
        
        # 2. Unwrap Data Key
        data_key = self.kms.decrypt_data_key(wrapped_key)
        
        # 3. Decrypt Payload
        aesgcm = AESGCM(data_key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        
        # 4. Parse JSON
        payload = json.loads(plaintext.decode('utf-8'))
        
        # Merge back with public ID
        return {
            "id": encrypted_record['id'],
            "parent_id": encrypted_record['parent_id'],
            **payload
        }

if __name__ == "__main__":
    # Test Workflows
    kms = KeyManager()
    svc = EncryptionService(kms)
    
    # Process Embeddings
    input_path = "embeddings/generated/vectors.json"
    output_path = "embeddings/encrypted/vectors_enc.json"
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if os.path.exists(input_path):
        with open(input_path, 'r', encoding='utf-8') as f:
            vectors = json.load(f)
            
        encrypted_vectors = []
        for v in vectors:
            enc = svc.encrypt_record(v)
            encrypted_vectors.append(enc)
            
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(encrypted_vectors, f, indent=2)
            
        logger.info(f"Encrypted {len(encrypted_vectors)} records. Saved to {output_path}")
        
        # Verify Decryption of first record
        dec = svc.decrypt_record(encrypted_vectors[0])
        assert dec['id'] == vectors[0]['id']
        assert dec['values'] == vectors[0]['values']
        logger.info("Verification Decryption Successful.")
    else:
        logger.warning("Input file not found. Ensure Embedding step ran.")
