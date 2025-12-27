"""
Pytest configuration and shared fixtures for all tests.
Provides reusable test data, mocks, and utility functions.
"""
import os
import sys
import json
import pytest
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ============================================================================
# FIXTURES: Test Data and Configuration
# ============================================================================

@pytest.fixture(scope="session")
def test_config():
    """Session-scoped test configuration."""
    return {
        "debug": True,
        "db_url": "postgresql://test:test@localhost/test_db",
        "jwt_secret": "test_secret_key_12345",
        "jwt_algorithm": "HS256",
        "access_token_expire_minutes": 30,
        "embedder_model": "sentence-transformers/all-MiniLM-L6-v2",
        "embedder_device": "cpu",
        "embedding_dim": 384,  # MiniLM is 384-dim
    }


@pytest.fixture(scope="session")
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# ============================================================================
# FIXTURES: Authentication & Users
# ============================================================================

@pytest.fixture
def test_users():
    """Test user database."""
    return {
        "attending": {
            "username": "attending",
            "full_name": "Dr. Smith",
            "email": "smith@cipercare.com",
            "hashed_password": "password123",
            "roles": ["attending", "admin"],
            "assigned_patients": ["any"],
        },
        "resident": {
            "username": "resident",
            "full_name": "Dr. Doe",
            "email": "doe@cipercare.com",
            "hashed_password": "password123",
            "roles": ["resident"],
            "assigned_patients": ["P123", "P456"],
        },
        "nurse": {
            "username": "nurse",
            "full_name": "Jane Nurse",
            "email": "nurse@cipercare.com",
            "hashed_password": "password123",
            "roles": ["nurse"],
            "assigned_patients": ["P123"],
        },
    }


@pytest.fixture
def admin_token():
    """Generate a valid admin token."""
    from backend.auth import create_access_token
    from datetime import timedelta

    token_data = {
        "sub": "attending",
        "roles": ["admin", "attending"],
        "iat": datetime.utcnow(),
    }
    return create_access_token(token_data, timedelta(minutes=30))


@pytest.fixture
def resident_token():
    """Generate a valid resident token."""
    from backend.auth import create_access_token
    from datetime import timedelta

    token_data = {
        "sub": "resident",
        "roles": ["resident"],
        "iat": datetime.utcnow(),
    }
    return create_access_token(token_data, timedelta(minutes=30))


@pytest.fixture
def nurse_token():
    """Generate a valid nurse token."""
    from backend.auth import create_access_token
    from datetime import timedelta

    token_data = {
        "sub": "nurse",
        "roles": ["nurse"],
        "iat": datetime.utcnow(),
    }
    return create_access_token(token_data, timedelta(minutes=30))


# ============================================================================
# FIXTURES: PHI Test Data
# ============================================================================

@pytest.fixture
def phi_test_cases():
    """Comprehensive PHI test cases."""
    return [
        {
            "text": "John Smith called on 01/15/2024",
            "expected_entities": ["PERSON", "DATE_TIME"],
            "should_mask": True,
            "description": "Person name and date",
        },
        {
            "text": "Email: john.smith@example.com, Phone: 555-123-4567",
            "expected_entities": ["EMAIL_ADDRESS", "PHONE_NUMBER"],
            "should_mask": True,
            "description": "Email and phone number",
        },
        {
            "text": "Patient lives in New York City, NY 10001",
            "expected_entities": ["LOCATION"],
            "should_mask": True,
            "description": "Address and location",
        },
        {
            "text": "DOB: 1990-05-15, SSN: 123-45-6789",
            "expected_entities": ["DATE_TIME"],
            "should_mask": True,
            "description": "Date of birth and SSN",
        },
        {
            "text": "Contact Dr. Michael Johnson at 2024-01-10",
            "expected_entities": ["PERSON", "DATE_TIME"],
            "should_mask": True,
            "description": "Doctor name and ISO date",
        },
        {
            "text": "The patient has hypertension and diabetes.",
            "expected_entities": [],
            "should_mask": False,
            "description": "No PHI - medical conditions only",
        },
        {
            "text": "Patient ID: P12345 admitted on Jan 1 2024",
            "expected_entities": ["DATE_TIME"],
            "should_mask": True,
            "description": "Pseudonymized ID and date",
        },
        {
            "text": "MRN: 987654321, Date: 2023/12/25",
            "expected_entities": ["DATE_TIME"],
            "should_mask": True,
            "description": "Medical record number and date",
        },
        {
            "text": "Please contact Sarah.Wilson@hospital.org (ext. 1234) on 03/10/2024",
            "expected_entities": ["PERSON", "EMAIL_ADDRESS", "DATE_TIME"],
            "should_mask": True,
            "description": "Name, email, and date",
        },
        {
            "text": "Patient age 45, male, from Boston",
            "expected_entities": ["LOCATION"],
            "should_mask": True,
            "description": "Age, gender, location",
        },
    ]


@pytest.fixture
def fhir_test_data():
    """Sample FHIR bundle with PHI for testing."""
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "P001",
                    "name": [{"given": ["John"], "family": "Smith"}],
                    "birthDate": "1980-05-15",
                    "contact": [
                        {
                            "telecom": [
                                {"system": "phone", "value": "555-123-4567"},
                                {"system": "email", "value": "john@example.com"},
                            ]
                        }
                    ],
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "id": "O001",
                    "subject": {"reference": "Patient/P001"},
                    "effectiveDateTime": "2024-01-10",
                    "valueQuantity": {"value": 98.6, "unit": "F"},
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "8867-4",
                                "display": "Heart rate",
                            }
                        ]
                    },
                }
            },
        ],
    }


# ============================================================================
# FIXTURES: Embedding Test Data
# ============================================================================

@pytest.fixture
def embedding_test_cases():
    """Test cases for embedding generation."""
    return [
        {
            "text": "The patient presents with hypertension and elevated blood pressure.",
            "description": "Clinical note",
        },
        {
            "text": "Vital signs: BP 140/90, HR 75, Temp 98.6F",
            "description": "Vital signs",
        },
        {
            "text": "Diagnosis: Type 2 Diabetes Mellitus, well-controlled",
            "description": "Diagnosis",
        },
        {
            "text": "",
            "description": "Empty text",
        },
        {
            "text": "A" * 1000,  # Very long text
            "description": "Very long text",
        },
        {
            "text": "123.456 789.012 345.678 901.234",
            "description": "Numerical values",
        },
        {
            "text": "The quick brown fox jumps over the lazy dog. " * 20,
            "description": "Repetitive text",
        },
        {
            "text": "Cardiac assessment: Normal S1, S2, no murmurs, rubs or gallops.",
            "description": "Physical exam",
        },
        {
            "text": "Patient reports pain 7/10, localized to left lower extremity",
            "description": "Symptom description",
        },
        {
            "text": "Laboratory values: WBC 7.2, RBC 4.8, HGB 14.2, PLT 250",
            "description": "Lab values",
        },
    ]


# ============================================================================
# FIXTURES: Encryption Test Data
# ============================================================================

@pytest.fixture
def encryption_test_vectors():
    """Test data for encryption."""
    return [
        {
            "text": "Sample patient record",
            "description": "Simple text",
        },
        {
            "text": '{"patient_id": "P123", "notes": "Clinical notes here"}',
            "description": "JSON data",
        },
        {
            "text": "a" * 10000,  # Large text
            "description": "Large data",
        },
        {
            "text": "",  # Empty
            "description": "Empty data",
        },
        {
            "text": "Special chars: !@#$%^&*()",
            "description": "Special characters",
        },
        {
            "text": "UTF-8: 你好 مرحبا Привет",
            "description": "Unicode characters",
        },
    ]


# ============================================================================
# FIXTURES: RBAC Test Data
# ============================================================================

@pytest.fixture
def rbac_test_cases():
    """Test cases for RBAC."""
    return [
        {
            "user_role": "admin",
            "required_role": "admin",
            "allowed": True,
            "description": "Admin can access admin resources",
        },
        {
            "user_role": "resident",
            "required_role": "admin",
            "allowed": False,
            "description": "Resident cannot access admin resources",
        },
        {
            "user_role": "resident",
            "required_role": "resident",
            "allowed": True,
            "description": "Resident can access resident resources",
        },
        {
            "user_role": "nurse",
            "required_role": "nurse",
            "allowed": True,
            "description": "Nurse can access nurse resources",
        },
        {
            "user_role": "nurse",
            "required_role": "admin",
            "allowed": False,
            "description": "Nurse cannot access admin resources",
        },
    ]


@pytest.fixture
def patient_relationships():
    """Test patient-user relationships."""
    return {
        "attending_user": {
            "username": "attending",
            "assigned_patients": ["any"],  # Can access any patient
            "accessible_patients": ["P001", "P002", "P003"],
        },
        "resident_user": {
            "username": "resident",
            "assigned_patients": ["P001", "P002"],
            "accessible_patients": ["P001", "P002"],
            "not_accessible": ["P003"],
        },
        "nurse_user": {
            "username": "nurse",
            "assigned_patients": ["P001"],
            "accessible_patients": ["P001"],
            "not_accessible": ["P002", "P003"],
        },
    }


# ============================================================================
# FIXTURES: API Test Data
# ============================================================================

@pytest.fixture
def valid_query_requests():
    """Valid query requests for API testing."""
    return [
        {
            "patient_id": "P001",
            "question": "What are the patient's vital signs?",
            "retrieve_k": 5,
            "temperature": 0.7,
            "description": "Standard query",
        },
        {
            "patient_id": "P002",
            "question": "List all medications",
            "retrieve_k": 10,
            "temperature": 0.5,
            "description": "Higher retrieve_k",
        },
        {
            "patient_id": "P003",
            "question": "Summarize recent lab results",
            "retrieve_k": 1,
            "temperature": 0.0,
            "description": "Lowest temperature (deterministic)",
        },
    ]


@pytest.fixture
def invalid_query_requests():
    """Invalid query requests for API testing."""
    return [
        {
            "patient_id": "",
            "question": "What are the vital signs?",
            "error": "patient_id required",
            "description": "Empty patient ID",
        },
        {
            "patient_id": "P001",
            "question": "ab",  # Too short
            "error": "question too short",
            "description": "Question too short",
        },
        {
            "patient_id": "P001",
            "question": "Q" * 1001,  # Too long
            "error": "question too long",
            "description": "Question too long",
        },
        {
            "patient_id": "P001",
            "question": "Valid question?",
            "retrieve_k": 0,  # Invalid
            "error": "retrieve_k must be >= 1",
            "description": "retrieve_k too low",
        },
        {
            "patient_id": "P001",
            "question": "Valid question?",
            "temperature": 1.5,  # Invalid
            "error": "temperature must be <= 1.0",
            "description": "temperature too high",
        },
    ]


# ============================================================================
# FIXTURES: Mocked Services
# ============================================================================

@pytest.fixture
def mock_cyborg_manager():
    """Mocked CyborgDBManager."""
    manager = MagicMock()
    manager.search.return_value = [
        {
            "id": "doc1",
            "text_snippet": "Patient has hypertension",
            "similarity": 0.95,
            "metadata": {"doc_type": "Observation", "date": "2024-01-10"},
        },
        {
            "id": "doc2",
            "text_snippet": "BP reading 140/90",
            "similarity": 0.87,
            "metadata": {"doc_type": "Vital Signs", "date": "2024-01-10"},
        },
    ]
    manager.insert.return_value = True
    manager.delete.return_value = True
    manager.connect.return_value = None
    return manager


@pytest.fixture
def mock_llm_service():
    """Mocked LLMService."""
    service = MagicMock()
    service.generate_response.return_value = {
        "answer": "Based on the clinical records, the patient has hypertension with BP readings of 140/90.",
        "confidence": 0.92,
        "sources": ["doc1", "doc2"],
    }
    return service


@pytest.fixture
def mock_crypto_service():
    """Mocked EncryptionService."""
    service = MagicMock()
    service.encrypt_record.return_value = {
        "encrypted_data": "encrypted_bytes_here",
        "wrapped_key": "wrapped_key_here",
        "nonce": "nonce_here",
    }
    service.decrypt_record.return_value = {"data": "decrypted data"}
    service.encrypt.return_value = b"encrypted_bytes"
    service.decrypt.return_value = b"decrypted_bytes"
    return service


@pytest.fixture
def mock_embedder():
    """Mocked ClinicalEmbedder."""
    embedder = MagicMock()

    def mock_get_embedding(text):
        # Return consistent 384-dim vector for MiniLM
        return [0.1] * 384

    def mock_process_dataset(input_path, output_path):
        # Create mock output
        with open(output_path, "w") as f:
            json.dump({"embeddings": []}, f)

    embedder.get_embedding.side_effect = mock_get_embedding
    embedder.process_dataset.side_effect = mock_process_dataset
    return embedder


@pytest.fixture
def mock_phi_scrubber():
    """Mocked PHIScrubber."""
    scrubber = MagicMock()

    def mock_scrub_text(text):
        # Simple mock: replace names with tokens
        result = text.replace("John Smith", "[PATIENT_NAME_ABC123]")
        result = result.replace("555-123-4567", "[PHONE_DEF456]")
        return result

    scrubber.scrub_text.side_effect = mock_scrub_text
    scrubber.token_map = {}
    return scrubber


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_test_token(username: str, roles: List[str]) -> str:
    """Create a test JWT token."""
    from backend.auth import create_access_token
    from datetime import timedelta

    token_data = {"sub": username, "roles": roles}
    return create_access_token(token_data, timedelta(minutes=30))


def generate_test_fhir_patient(patient_id: str, name: str, dob: str):
    """Generate a test FHIR patient resource."""
    return {
        "resourceType": "Patient",
        "id": patient_id,
        "name": [{"given": [name.split()[0]], "family": name.split()[1]}],
        "birthDate": dob,
        "contact": [
            {
                "telecom": [
                    {"system": "phone", "value": "555-000-0000"},
                    {"system": "email", "value": f"{patient_id}@patient.com"},
                ]
            }
        ],
    }


def generate_test_embedding_vector(seed: int = 0, dimension: int = 384) -> List[float]:
    """Generate a deterministic test embedding."""
    import numpy as np

    np.random.seed(seed)
    return np.random.randn(dimension).tolist()


# ============================================================================
# CLEANUP FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Auto-cleanup test files after each test."""
    yield
    # Cleanup logic here if needed
