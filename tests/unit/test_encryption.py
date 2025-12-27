"""
Unit tests for encryption/decryption (encryption/crypto_service.py)

Coverage:
- AES-256-GCM encryption and decryption
- Key generation and rotation
- Authentication tag verification
- Edge cases (empty data, large data)
"""
import pytest
import os
import json
import tempfile
import shutil
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from encryption.crypto_service import EncryptionService, KeyManager


class TestKeyGeneration:
    """Test key generation and management."""

    def setup_method(self):
        """Setup for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.key_path = os.path.join(self.temp_dir, "master.key")

    def teardown_method(self):
        """Cleanup after each test."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @pytest.mark.unit
    @pytest.mark.encryption
    def test_master_key_generation(self):
        """Test master key is generated."""
        kms = KeyManager(key_path=self.key_path)
        
        assert kms.master_key is not None, "Master key should be generated"
        assert len(kms.master_key) == 32, "Master key should be 256 bits (32 bytes)"

    @pytest.mark.unit
    @pytest.mark.encryption
    def test_master_key_persistence(self):
        """Test master key is persisted to file."""
        kms = KeyManager(key_path=self.key_path)
        original_key = kms.master_key
        
        # Key file should exist
        assert os.path.exists(self.key_path), "Key file should exist"
        
        # Create new instance and verify same key is loaded
        kms2 = KeyManager(key_path=self.key_path)
        assert kms2.master_key == original_key, "Key should be persisted"

    @pytest.mark.unit
    @pytest.mark.encryption
    def test_data_key_generation(self):
        """Test data key generation."""
        kms = KeyManager(key_path=self.key_path)
        
        wrapped_key, plaintext_key = kms.generate_data_key()
        
        assert wrapped_key is not None, "Wrapped key should be generated"
        assert plaintext_key is not None, "Plaintext key should be generated"
        assert len(plaintext_key) == 32, "Data key should be 256 bits (32 bytes)"
        assert len(wrapped_key) > 32, "Wrapped key should be larger (includes nonce)"

    @pytest.mark.unit
    @pytest.mark.encryption
    def test_multiple_data_keys_different(self):
        """Test that multiple data keys are unique."""
        kms = KeyManager(key_path=self.key_path)
        
        keys1 = [kms.generate_data_key() for _ in range(5)]
        keys2 = [kms.generate_data_key() for _ in range(5)]
        
        # All keys should be unique
        plaintext_keys = [k[1] for k in keys1 + keys2]
        assert len(set(plaintext_keys)) == 10, "All data keys should be unique"

    @pytest.mark.unit
    @pytest.mark.encryption
    def test_key_format_aes_256(self):
        """Test that generated keys are valid AES-256 keys."""
        kms = KeyManager(key_path=self.key_path)
        
        wrapped_key, plaintext_key = kms.generate_data_key()
        
        # Should be valid AES key
        assert len(plaintext_key) * 8 == 256, "Key should be 256 bits"


class TestEncryptionDecryption:
    """Test encryption and decryption operations."""

    def setup_method(self):
        """Setup for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.key_path = os.path.join(self.temp_dir, "master.key")
        self.kms = KeyManager(key_path=self.key_path)
        self.crypto = EncryptionService(self.kms)

    def teardown_method(self):
        """Cleanup after each test."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @pytest.mark.unit
    @pytest.mark.encryption
    def test_encrypt_simple_text(self):
        """Test encryption of simple text."""
        plaintext = "Patient confidential data"
        
        wrapped_key, data_key = self.kms.generate_data_key()
        aesgcm = AESGCM(data_key)
        nonce = os.urandom(12)
        
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
        
        assert ciphertext is not None, "Ciphertext should be generated"
        assert ciphertext != plaintext.encode(), "Plaintext should be encrypted"

    @pytest.mark.unit
    @pytest.mark.encryption
    def test_decrypt_simple_text(self):
        """Test decryption of simple text."""
        plaintext = "Patient confidential data"
        
        wrapped_key, data_key = self.kms.generate_data_key()
        aesgcm = AESGCM(data_key)
        nonce = os.urandom(12)
        
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
        decrypted = aesgcm.decrypt(nonce, ciphertext, None)
        
        assert decrypted.decode() == plaintext, "Decrypted text should match plaintext"

    @pytest.mark.unit
    @pytest.mark.encryption
    def test_encrypt_decrypt_record(self):
        """Test encryption and decryption of records."""
        record = {
            "patient_id": "P123",
            "vector": [0.1, 0.2, 0.3],
            "text": "Patient clinical note",
        }
        
        encrypted = self.crypto.encrypt_record(record)
        
        assert "encrypted_data" in encrypted, "Encrypted record should have encrypted_data"
        assert "wrapped_key" in encrypted, "Encrypted record should have wrapped_key"

    @pytest.mark.unit
    @pytest.mark.encryption
    def test_json_data_encryption(self):
        """Test encryption of JSON data."""
        plaintext_json = json.dumps({
            "patient": "P001",
            "vector": [0.1, 0.2, 0.3],
        })
        
        wrapped_key, data_key = self.kms.generate_data_key()
        aesgcm = AESGCM(data_key)
        nonce = os.urandom(12)
        
        ciphertext = aesgcm.encrypt(nonce, plaintext_json.encode(), None)
        decrypted = aesgcm.decrypt(nonce, ciphertext, None)
        
        parsed = json.loads(decrypted.decode())
        assert parsed["patient"] == "P001"

    @pytest.mark.unit
    @pytest.mark.encryption
    def test_large_data_encryption(self):
        """Test encryption of large data."""
        plaintext = "x" * 1000000  # 1MB
        
        wrapped_key, data_key = self.kms.generate_data_key()
        aesgcm = AESGCM(data_key)
        nonce = os.urandom(12)
        
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
        decrypted = aesgcm.decrypt(nonce, ciphertext, None)
        
        assert decrypted.decode() == plaintext


class TestAuthenticationTag:
    """Test authentication tag verification."""

    def setup_method(self):
        """Setup for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.key_path = os.path.join(self.temp_dir, "master.key")
        self.kms = KeyManager(key_path=self.key_path)

    def teardown_method(self):
        """Cleanup after each test."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @pytest.mark.unit
    @pytest.mark.encryption
    def test_auth_tag_verification_valid(self):
        """Test authentication tag verification with valid tag."""
        plaintext = "Patient data"
        wrapped_key, data_key = self.kms.generate_data_key()
        aesgcm = AESGCM(data_key)
        nonce = os.urandom(12)
        
        # Encrypt (includes auth tag)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
        
        # Should decrypt successfully
        decrypted = aesgcm.decrypt(nonce, ciphertext, None)
        assert decrypted.decode() == plaintext

    @pytest.mark.unit
    @pytest.mark.encryption
    def test_auth_tag_verification_tampered(self):
        """Test authentication tag verification with tampered data."""
        plaintext = "Patient data"
        wrapped_key, data_key = self.kms.generate_data_key()
        aesgcm = AESGCM(data_key)
        nonce = os.urandom(12)
        
        # Encrypt
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
        
        # Tamper with ciphertext
        tampered = bytearray(ciphertext)
        tampered[0] ^= 0xFF
        
        # Should fail to decrypt
        with pytest.raises(Exception):
            aesgcm.decrypt(nonce, bytes(tampered), None)

    @pytest.mark.unit
    @pytest.mark.encryption
    def test_wrong_key_decryption_fails(self):
        """Test that wrong key fails to decrypt."""
        plaintext = "Patient confidential"
        
        # Encrypt with key1
        wrapped_key1, key1 = self.kms.generate_data_key()
        aesgcm1 = AESGCM(key1)
        nonce = os.urandom(12)
        ciphertext = aesgcm1.encrypt(nonce, plaintext.encode(), None)
        
        # Try to decrypt with different key
        wrapped_key2, key2 = self.kms.generate_data_key()
        aesgcm2 = AESGCM(key2)
        
        with pytest.raises(Exception):
            aesgcm2.decrypt(nonce, ciphertext, None)

    @pytest.mark.unit
    @pytest.mark.encryption
    def test_wrong_nonce_decryption_fails(self):
        """Test that wrong nonce fails to decrypt."""
        plaintext = "Patient data"
        wrapped_key, data_key = self.kms.generate_data_key()
        aesgcm = AESGCM(data_key)
        nonce1 = os.urandom(12)
        nonce2 = os.urandom(12)
        
        # Encrypt with nonce1
        ciphertext = aesgcm.encrypt(nonce1, plaintext.encode(), None)
        
        # Try to decrypt with nonce2
        with pytest.raises(Exception):
            aesgcm.decrypt(nonce2, ciphertext, None)


class TestKeyRotation:
    """Test key rotation functionality."""

    def setup_method(self):
        """Setup for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.key_path = os.path.join(self.temp_dir, "master.key")

    def teardown_method(self):
        """Cleanup after each test."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @pytest.mark.unit
    @pytest.mark.encryption
    def test_data_key_rotation(self):
        """Test data key rotation."""
        kms = KeyManager(key_path=self.key_path)
        
        # Generate multiple data keys
        keys = [kms.generate_data_key() for _ in range(3)]
        
        # All should be unique
        plaintext_keys = [k[1] for k in keys]
        assert len(set(plaintext_keys)) == 3, "Data keys should be unique"

    @pytest.mark.unit
    @pytest.mark.encryption
    def test_decrypt_with_wrapped_key(self):
        """Test decryption using wrapped key."""
        kms = KeyManager(key_path=self.key_path)
        plaintext = "Patient confidential data"
        
        # Generate and wrap key
        wrapped_key, plaintext_key = kms.generate_data_key()
        
        # Encrypt
        aesgcm = AESGCM(plaintext_key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
        
        # Decrypt with wrapped key
        recovered_key = kms.decrypt_data_key(wrapped_key)
        aesgcm2 = AESGCM(recovered_key)
        decrypted = aesgcm2.decrypt(nonce, ciphertext, None)
        
        assert decrypted.decode() == plaintext


class TestEncryptionEdgeCases:
    """Test edge cases in encryption."""

    def setup_method(self):
        """Setup for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.key_path = os.path.join(self.temp_dir, "master.key")
        self.kms = KeyManager(key_path=self.key_path)

    def teardown_method(self):
        """Cleanup after each test."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @pytest.mark.unit
    @pytest.mark.encryption
    def test_encrypt_empty_data(self):
        """Test encryption of empty data."""
        plaintext = ""
        wrapped_key, data_key = self.kms.generate_data_key()
        aesgcm = AESGCM(data_key)
        nonce = os.urandom(12)
        
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
        decrypted = aesgcm.decrypt(nonce, ciphertext, None)
        
        assert decrypted.decode() == plaintext

    @pytest.mark.unit
    @pytest.mark.encryption
    def test_encrypt_binary_data(self):
        """Test encryption of binary data."""
        plaintext = b"Binary data \x00\x01\x02"
        wrapped_key, data_key = self.kms.generate_data_key()
        aesgcm = AESGCM(data_key)
        nonce = os.urandom(12)
        
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        decrypted = aesgcm.decrypt(nonce, ciphertext, None)
        
        assert decrypted == plaintext

    @pytest.mark.unit
    @pytest.mark.encryption
    def test_encryption_test_vectors(self, encryption_test_vectors):
        """Test encryption with various test vectors."""
        for vector in encryption_test_vectors:
            text = vector["text"]
            plaintext = text.encode() if isinstance(text, str) else text
            
            wrapped_key, data_key = self.kms.generate_data_key()
            aesgcm = AESGCM(data_key)
            nonce = os.urandom(12)
            
            ciphertext = aesgcm.encrypt(nonce, plaintext, None)
            decrypted = aesgcm.decrypt(nonce, ciphertext, None)
            
            assert decrypted == plaintext, f"Failed for {vector['description']}"

    @pytest.mark.unit
    @pytest.mark.encryption
    def test_nonce_uniqueness(self):
        """Test that nonces are unique for encryption."""
        nonces = set()
        
        for _ in range(1000):
            nonce = os.urandom(12)
            nonce_hex = nonce.hex()
            assert nonce_hex not in nonces, "Nonces should be unique"
            nonces.add(nonce_hex)


class TestEncryptionIntegration:
    """Integration tests for encryption."""

    def setup_method(self):
        """Setup for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.key_path = os.path.join(self.temp_dir, "master.key")
        self.kms = KeyManager(key_path=self.key_path)
        self.crypto = EncryptionService(self.kms)

    def teardown_method(self):
        """Cleanup after each test."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @pytest.mark.unit
    @pytest.mark.encryption
    def test_record_encryption_full_workflow(self):
        """Test full encryption workflow."""
        record = {
            "patient_id": "P001",
            "vector": [0.1, 0.2, 0.3],
            "text": "Clinical note about patient",
            "metadata": {"type": "observation", "date": "2024-01-10"},
        }
        
        # Encrypt
        encrypted_record = self.crypto.encrypt_record(record)
        
        assert "encrypted_data" in encrypted_record
        assert "wrapped_key" in encrypted_record
        assert encrypted_record["patient_id"] == "P001"  # ID not encrypted

    @pytest.mark.unit
    @pytest.mark.encryption
    def test_multiple_records_different_keys(self):
        """Test that multiple records use different keys."""
        records = [
            {"patient_id": f"P{i:03d}", "vector": [float(i)] * 3}
            for i in range(5)
        ]
        
        encrypted_records = [self.crypto.encrypt_record(r) for r in records]
        
        # Each should have different wrapped key
        wrapped_keys = [r["wrapped_key"] for r in encrypted_records]
        assert len(set(wrapped_keys)) == 5, "Each record should have unique wrapped key"
