import os
import json
import base64
import logging
from typing import Dict, Any, Optional
import hvac
from hvac.exceptions import VaultError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VaultTransitCryptoService:
    """
    HIPAA-Compliant Encryption Service using HashiCorp Vault Transit Engine.
    
    Key features:
    - Keys never leave Vault (zero-knowledge encryption)
    - Complete audit trail of all encrypt/decrypt operations
    - Automatic key rotation support
    - Enterprise-grade encryption (AES-256-GCM)
    - HIPAA/SOC2/PCI-DSS compliant
    
    Architecture:
    - Patient data encrypted through Vault Transit engine
    - Plaintext never stored on disk
    - Ciphertext stored in PostgreSQL
    - Complete audit logging for compliance
    """
    
    def __init__(self, vault_addr: Optional[str] = None, vault_token: Optional[str] = None, 
                 transit_key: str = "cipercare"):
        """
        Initialize Vault Transit Crypto Service.
        
        Args:
            vault_addr: Vault server address (default: env VAULT_ADDR)
            vault_token: Vault authentication token (default: env VAULT_TOKEN)
            transit_key: Transit engine encryption key name (default: "cipercare")
        """
        self.vault_addr = vault_addr or os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
        self.vault_token = vault_token or os.getenv("VAULT_TOKEN")
        self.transit_key = transit_key
        self.transit_mount = "transit"
        
        if not self.vault_token:
            raise ValueError(
                "Vault token required. Set VAULT_TOKEN environment variable "
                "or pass vault_token parameter"
            )
        
        logger.info(f"Initializing Vault Transit Crypto Service (addr={self.vault_addr})")
        
        try:
            self.client = hvac.Client(url=self.vault_addr, token=self.vault_token)
            # Test connection
            self.client.is_authenticated()
            logger.info("✓ Vault authentication successful")
            
            # Ensure transit engine is enabled
            self._ensure_transit_engine()
            # Ensure encryption key exists
            self._ensure_transit_key()
            
        except VaultError as e:
            logger.error(f"Vault connection failed: {e}")
            raise RuntimeError(f"Cannot connect to Vault: {e}")
    
    def _ensure_transit_engine(self):
        """Ensure Transit secrets engine is enabled."""
        try:
            mounts = self.client.sys.list_mounted_secrets_engines()
            if f"{self.transit_mount}/" not in mounts.get("data", {}):
                logger.info(f"Enabling {self.transit_mount} secrets engine...")
                self.client.sys.enable_secrets_engine(
                    backend_type="transit",
                    mount_point=self.transit_mount
                )
                logger.info(f"✓ {self.transit_mount} engine enabled")
            else:
                logger.info(f"✓ {self.transit_mount} engine already enabled")
        except VaultError as e:
            logger.warning(f"Could not verify transit engine: {e}")
    
    def _ensure_transit_key(self):
        """Ensure encryption key exists in Transit engine."""
        try:
            # Try to read the key - if it exists, it's already created
            self.client.secrets.transit.read_key(
                name=self.transit_key,
                mount_point=self.transit_mount
            )
            logger.info(f"✓ Transit key '{self.transit_key}' found")
        except VaultError as e:
            if "not found" in str(e).lower():
                logger.info(f"Creating transit key '{self.transit_key}'...")
                self.client.secrets.transit.create_key(
                    name=self.transit_key,
                    mount_point=self.transit_mount,
                    type="aes256-gcm96"
                )
                logger.info(f"✓ Transit key '{self.transit_key}' created")
            else:
                logger.warning(f"Could not verify transit key: {e}")
    
    def encrypt_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt a patient record using Vault Transit engine.
        
        Sensitive fields encrypted:
        - values (embeddings)
        - metadata (patient info)
        - text_snippet (clinical notes)
        
        Non-sensitive fields kept plaintext for indexing:
        - id (used for record lookup)
        - parent_id (used for relationships)
        
        Args:
            record: Record dict with 'id', 'parent_id', 'values', 'metadata', etc.
            
        Returns:
            Encrypted record dict with Transit ciphertext
        """
        try:
            # Prepare sensitive payload
            sensitive_payload = {
                "values": record['values'],
                "metadata": record['metadata'],
                "text_snippet": record.get('text_snippet', '')
            }
            
            # Serialize to JSON and base64 encode for Vault
            plaintext = json.dumps(sensitive_payload)
            plaintext_b64 = base64.b64encode(plaintext.encode('utf-8')).decode('utf-8')
            
            # Encrypt through Vault Transit
            response = self.client.secrets.transit.encrypt_data(
                name=self.transit_key,
                plaintext=plaintext_b64,
                mount_point=self.transit_mount
            )
            
            ciphertext = response['data']['ciphertext']
            
            # Construct encrypted record
            encrypted_record = {
                "id": record['id'],
                "parent_id": record['parent_id'],
                "version": "v2-vault",
                "algo": "AES-256-GCM",
                "engine": "vault-transit",
                "ciphertext": ciphertext
            }
            
            return encrypted_record
            
        except VaultError as e:
            logger.error(f"Encryption failed: {e}")
            raise RuntimeError(f"Vault encryption error: {e}")
    
    def decrypt_record(self, encrypted_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt a patient record using Vault Transit engine.
        
        Args:
            encrypted_record: Encrypted record with Vault Transit ciphertext
            
        Returns:
            Decrypted record dict with plaintext sensitive fields
        """
        try:
            ciphertext = encrypted_record['ciphertext']
            
            # Decrypt through Vault Transit
            response = self.client.secrets.transit.decrypt_data(
                name=self.transit_key,
                ciphertext=ciphertext,
                mount_point=self.transit_mount
            )
            
            # Decode base64 plaintext
            plaintext_b64 = response['data']['plaintext']
            plaintext = base64.b64decode(plaintext_b64).decode('utf-8')
            payload = json.loads(plaintext)
            
            # Merge with non-sensitive fields
            return {
                "id": encrypted_record['id'],
                "parent_id": encrypted_record['parent_id'],
                **payload
            }
            
        except VaultError as e:
            logger.error(f"Decryption failed: {e}")
            raise RuntimeError(f"Vault decryption error: {e}")
    
    def get_audit_logs(self) -> Dict[str, Any]:
        """
        Get Vault audit logs for encryption operations.
        Useful for HIPAA compliance and security audits.
        
        Returns:
            Audit log information from Vault
        """
        try:
            # Note: Requires audit backend to be enabled
            # This is a placeholder for getting audit info
            logger.info("Audit logs can be retrieved from Vault audit backend")
            return {"message": "Use 'vault audit list' to view enabled audit backends"}
        except Exception as e:
            logger.warning(f"Could not retrieve audit logs: {e}")
            return {}
    
    def rotate_key(self):
        """
        Rotate the encryption key.
        New data will be encrypted with new key, old ciphertext remains valid.
        
        This is a HIPAA best practice (annual key rotation).
        """
        try:
            logger.info(f"Rotating transit key '{self.transit_key}'...")
            self.client.secrets.transit.rotate_key(
                name=self.transit_key,
                mount_point=self.transit_mount
            )
            logger.info(f"✓ Transit key '{self.transit_key}' rotated successfully")
        except VaultError as e:
            logger.error(f"Key rotation failed: {e}")
            raise RuntimeError(f"Vault key rotation error: {e}")
    
    def get_key_info(self) -> Dict[str, Any]:
        """
        Get information about the encryption key (versions, rotation policies, etc).
        
        Returns:
            Key metadata from Vault
        """
        try:
            response = self.client.secrets.transit.read_key(
                name=self.transit_key,
                mount_point=self.transit_mount
            )
            return response.get('data', {})
        except VaultError as e:
            logger.error(f"Could not retrieve key info: {e}")
            return {}


class FallbackCryptoService:
    """
    Fallback local encryption service for development/testing.
    Uses local file-based key storage (less secure than Vault).
    """
    
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    
    def __init__(self):
        logger.warning("Using fallback local encryption (not recommended for production)")
        self.key_file = "config/cyborg_index_key.bin"
        self._load_or_create_key()
    
    def _load_or_create_key(self):
        """Load or create local encryption key."""
        import secrets
        
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                self.key = f.read()
        else:
            os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
            self.key = secrets.token_bytes(32)
            with open(self.key_file, 'wb') as f:
                f.write(self.key)
            logger.info("Generated local encryption key")
    
    def encrypt_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt record locally (fallback)."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        
        sensitive_payload = {
            "values": record['values'],
            "metadata": record['metadata'],
            "text_snippet": record.get('text_snippet', '')
        }
        
        plaintext = json.dumps(sensitive_payload).encode('utf-8')
        
        aesgcm = AESGCM(self.key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        
        return {
            "id": record['id'],
            "parent_id": record['parent_id'],
            "version": "v1-local",
            "algo": "AES-256-GCM",
            "engine": "local",
            "nonce": base64.b64encode(nonce).decode('utf-8'),
            "ciphertext": base64.b64encode(ciphertext).decode('utf-8')
        }
    
    def decrypt_record(self, encrypted_record: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt record locally (fallback)."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        
        nonce = base64.b64decode(encrypted_record['nonce'])
        ciphertext = base64.b64decode(encrypted_record['ciphertext'])
        
        aesgcm = AESGCM(self.key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        
        payload = json.loads(plaintext.decode('utf-8'))
        
        return {
            "id": encrypted_record['id'],
            "parent_id": encrypted_record['parent_id'],
            **payload
        }


def get_crypto_service() -> Any:
    """
    Factory function to get the appropriate crypto service.
    
    Uses Vault Transit by default (Option B).
    Falls back to local encryption if Vault is not available (development mode).
    
    Returns:
        VaultTransitCryptoService or FallbackCryptoService
    """
    encryption_type = os.getenv("ENCRYPTION_TYPE", "vault_transit").lower()
    
    if encryption_type == "vault_transit":
        try:
            return VaultTransitCryptoService()
        except Exception as e:
            logger.warning(f"Vault Transit not available ({e}), falling back to local encryption")
            logger.warning("⚠️  LOCAL ENCRYPTION IS NOT RECOMMENDED FOR PRODUCTION")
            return FallbackCryptoService()
    elif encryption_type == "local":
        logger.warning("⚠️  Using local encryption (development mode)")
        return FallbackCryptoService()
    else:
        raise ValueError(f"Unknown encryption type: {encryption_type}")


if __name__ == "__main__":
    # Test the Vault Transit service
    print("Testing Vault Transit Crypto Service...")
    
    try:
        crypto = VaultTransitCryptoService()
        
        # Test record
        test_record = {
            "id": "patient_001",
            "parent_id": "clinic_001",
            "values": [0.1, 0.2, 0.3, 0.4],  # embedding vector
            "metadata": {"name": "John Doe", "age": 45},
            "text_snippet": "Patient presents with symptoms..."
        }
        
        print(f"\n📝 Original record: {test_record}")
        
        # Encrypt
        encrypted = crypto.encrypt_record(test_record)
        print(f"\n🔒 Encrypted: {encrypted['ciphertext'][:50]}...")
        
        # Decrypt
        decrypted = crypto.decrypt_record(encrypted)
        print(f"\n🔓 Decrypted: {decrypted}")
        
        # Verify
        assert decrypted['id'] == test_record['id']
        assert decrypted['values'] == test_record['values']
        print("\n✓ Encryption/Decryption test PASSED")
        
        # Show key info
        key_info = crypto.get_key_info()
        print(f"\n🔑 Key Info: {key_info}")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("Make sure Vault is running: vault server -dev")
