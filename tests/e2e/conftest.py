"""
E2E Testing Configuration and Fixtures
Provides shared fixtures for end-to-end testing scenarios
"""

import pytest
import requests
import json
import time
from datetime import datetime
from typing import Dict, Optional, Generator
from unittest.mock import Mock, patch, MagicMock
import logging

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestEnvironment:
    """Test environment configuration"""
    BACKEND_URL = "http://localhost:8000"
    FRONTEND_URL = "http://localhost:3000"
    API_TIMEOUT = 10
    
    # Test credentials
    TEST_CLINICIAN_A = {
        "username": "clinician_a@test.com",
        "password": "SecurePassword123!",
        "clinic_id": "clinic_001"
    }
    
    TEST_CLINICIAN_B = {
        "username": "clinician_b@test.com", 
        "password": "SecurePassword123!",
        "clinic_id": "clinic_002"
    }
    
    # Test patients
    TEST_PATIENT_A = {
        "patient_id": "patient_001",
        "name": "John Doe",
        "dob": "1975-05-15",
        "assigned_to": "clinician_a@test.com"
    }
    
    TEST_PATIENT_B = {
        "patient_id": "patient_002", 
        "name": "Jane Smith",
        "dob": "1982-08-22",
        "assigned_to": "clinician_b@test.com"
    }
    
    # Clinical test questions
    TEST_QUESTIONS = [
        "What is the patient's current medication list?",
        "What are the patient's allergies?",
        "What is the patient's recent diagnosis?",
        "What is the recommended treatment plan?",
        "What is the patient's BMI and vital signs?"
    ]


@pytest.fixture(scope="session")
def test_env():
    """Provide test environment configuration"""
    return TestEnvironment()


@pytest.fixture(scope="session")
def session_token():
    """Get session token for test execution"""
    return {
        "token": None,
        "created_at": None,
        "expires_at": None
    }


class APIClient:
    """HTTP client for API testing"""
    
    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.auth_token = None
        self.response_history = []
        
    def set_auth_token(self, token: str):
        """Set authentication token for requests"""
        self.auth_token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
    def get_headers(self, extra: Optional[Dict] = None) -> Dict:
        """Get request headers"""
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        if extra:
            headers.update(extra)
        return headers
    
    def log_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                   response: Optional[requests.Response] = None):
        """Log request for audit trail verification"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "method": method,
            "endpoint": endpoint,
            "request_data": data,
            "status_code": response.status_code if response else None,
            "response_time": response.elapsed.total_seconds() if response else None
        }
        self.response_history.append(log_entry)
        return log_entry
    
    def login(self, username: str, password: str) -> Dict:
        """Authenticate user"""
        endpoint = f"{self.base_url}/auth/login"
        payload = {"username": username, "password": password}
        
        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers=self.get_headers(),
                timeout=self.timeout
            )
            self.log_request("POST", "/auth/login", payload, response)
            
            if response.status_code == 200:
                data = response.json()
                self.set_auth_token(data.get("token"))
                return {
                    "success": True,
                    "token": data.get("token"),
                    "user": data.get("user"),
                    "status_code": response.status_code
                }
            else:
                return {
                    "success": False,
                    "error": response.text,
                    "status_code": response.status_code
                }
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status_code": None
            }
    
    def logout(self) -> Dict:
        """Logout user"""
        endpoint = f"{self.base_url}/auth/logout"
        
        try:
            response = requests.post(
                endpoint,
                headers=self.get_headers(),
                timeout=self.timeout
            )
            self.log_request("POST", "/auth/logout", None, response)
            self.auth_token = None
            
            return {
                "success": response.status_code in [200, 204],
                "status_code": response.status_code
            }
        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_patients(self) -> Dict:
        """Get list of patients accessible to clinician"""
        endpoint = f"{self.base_url}/patients"
        
        try:
            response = requests.get(
                endpoint,
                headers=self.get_headers(),
                timeout=self.timeout
            )
            self.log_request("GET", "/patients", None, response)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "patients": response.json(),
                    "status_code": response.status_code
                }
            else:
                return {
                    "success": False,
                    "error": response.text,
                    "status_code": response.status_code
                }
        except Exception as e:
            logger.error(f"Get patients failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_patient_data(self, patient_id: str) -> Dict:
        """Get patient medical data"""
        endpoint = f"{self.base_url}/patients/{patient_id}"
        
        try:
            response = requests.get(
                endpoint,
                headers=self.get_headers(),
                timeout=self.timeout
            )
            self.log_request("GET", f"/patients/{patient_id}", None, response)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json(),
                    "status_code": response.status_code
                }
            else:
                return {
                    "success": False,
                    "error": response.text,
                    "status_code": response.status_code
                }
        except Exception as e:
            logger.error(f"Get patient data failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def query(self, patient_id: str, question: str) -> Dict:
        """Execute clinical query"""
        endpoint = f"{self.base_url}/query"
        payload = {
            "patient_id": patient_id,
            "question": question
        }
        
        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers=self.get_headers(),
                timeout=self.timeout
            )
            self.log_request("POST", "/query", payload, response)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "answer": data.get("answer"),
                    "sources": data.get("sources", []),
                    "disclaimer": data.get("disclaimer"),
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                return {
                    "success": False,
                    "error": response.text,
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds()
                }
        except Exception as e:
            logger.error(f"Query failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response_time": None
            }
    
    def get_audit_log(self, patient_id: Optional[str] = None,
                      user: Optional[str] = None,
                      limit: int = 100) -> Dict:
        """Retrieve audit log"""
        endpoint = f"{self.base_url}/audit-log"
        params = {"limit": limit}
        if patient_id:
            params["patient_id"] = patient_id
        if user:
            params["user"] = user
        
        try:
            response = requests.get(
                endpoint,
                params=params,
                headers=self.get_headers(),
                timeout=self.timeout
            )
            self.log_request("GET", f"/audit-log?{params}", None, response)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "log": response.json(),
                    "status_code": response.status_code
                }
            else:
                return {
                    "success": False,
                    "error": response.text,
                    "status_code": response.status_code
                }
        except Exception as e:
            logger.error(f"Get audit log failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_response_history(self) -> list:
        """Get history of all requests made"""
        return self.response_history
    
    def clear_history(self):
        """Clear request history"""
        self.response_history = []


@pytest.fixture
def api_client(test_env) -> Generator[APIClient, None, None]:
    """Provide API client for testing"""
    client = APIClient(test_env.BACKEND_URL)
    yield client
    # Cleanup: logout if authenticated
    if client.auth_token:
        client.logout()


@pytest.fixture
def authenticated_client_a(api_client, test_env) -> Generator[APIClient, None, None]:
    """Provide authenticated client for Clinician A"""
    result = api_client.login(
        test_env.TEST_CLINICIAN_A["username"],
        test_env.TEST_CLINICIAN_A["password"]
    )
    assert result["success"], f"Failed to login: {result}"
    yield api_client
    api_client.logout()


@pytest.fixture
def authenticated_client_b(test_env) -> Generator[APIClient, None, None]:
    """Provide authenticated client for Clinician B"""
    client = APIClient(test_env.BACKEND_URL)
    result = client.login(
        test_env.TEST_CLINICIAN_B["username"],
        test_env.TEST_CLINICIAN_B["password"]
    )
    assert result["success"], f"Failed to login: {result}"
    yield client
    client.logout()


class MockBackendService:
    """Mock backend service for testing error scenarios"""
    
    def __init__(self):
        self.is_healthy = True
        self.responses = {}
    
    def set_unhealthy(self):
        """Simulate service outage"""
        self.is_healthy = False
    
    def set_healthy(self):
        """Restore service"""
        self.is_healthy = True
    
    def get_health(self) -> Dict:
        """Get service health"""
        if not self.is_healthy:
            return {"status": "unhealthy", "error": "Service unavailable"}
        return {"status": "healthy"}


@pytest.fixture
def mock_backend():
    """Provide mock backend service"""
    return MockBackendService()


class AuditTrailValidator:
    """Validate audit trail completeness and accuracy"""
    
    @staticmethod
    def validate_audit_entry(entry: Dict, 
                            expected_action: str,
                            expected_user: str,
                            expected_patient: Optional[str] = None) -> Dict:
        """Validate individual audit log entry"""
        errors = []
        
        # Check required fields
        required_fields = ["timestamp", "action", "user_id", "status"]
        for field in required_fields:
            if field not in entry:
                errors.append(f"Missing required field: {field}")
        
        # Check action matches
        if entry.get("action") != expected_action:
            errors.append(f"Action mismatch: expected {expected_action}, got {entry.get('action')}")
        
        # Check user matches
        if entry.get("user_id") != expected_user:
            errors.append(f"User mismatch: expected {expected_user}, got {entry.get('user_id')}")
        
        # Check patient if expected
        if expected_patient and entry.get("patient_id") != expected_patient:
            errors.append(f"Patient mismatch: expected {expected_patient}, got {entry.get('patient_id')}")
        
        # Verify timestamp format
        try:
            datetime.fromisoformat(entry.get("timestamp", ""))
        except (ValueError, TypeError):
            errors.append(f"Invalid timestamp format: {entry.get('timestamp')}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "entry": entry
        }
    
    @staticmethod
    def validate_audit_trail(log_entries: list, 
                            expected_sequence: list) -> Dict:
        """Validate complete audit trail follows expected sequence"""
        if len(log_entries) < len(expected_sequence):
            return {
                "valid": False,
                "error": f"Insufficient audit entries: expected {len(expected_sequence)}, got {len(log_entries)}"
            }
        
        missing_actions = []
        for expected_action in expected_sequence:
            found = any(entry.get("action") == expected_action for entry in log_entries)
            if not found:
                missing_actions.append(expected_action)
        
        return {
            "valid": len(missing_actions) == 0,
            "missing_actions": missing_actions,
            "total_entries": len(log_entries)
        }


@pytest.fixture
def audit_validator():
    """Provide audit trail validator"""
    return AuditTrailValidator()


class EncryptionValidator:
    """Validate encryption and data security"""
    
    @staticmethod
    def check_plaintext_in_storage(storage_path: str, search_terms: list) -> Dict:
        """Check if plaintext data exists in storage (should not)"""
        try:
            with open(storage_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            found_plaintext = []
            for term in search_terms:
                if term.lower() in content.lower():
                    found_plaintext.append(term)
            
            return {
                "file": storage_path,
                "is_encrypted": len(found_plaintext) == 0,
                "plaintext_found": found_plaintext
            }
        except Exception as e:
            return {
                "file": storage_path,
                "error": str(e)
            }
    
    @staticmethod
    def verify_search_results(query: str, results: list, 
                             expected_keywords: list) -> Dict:
        """Verify search returns correct results without decrypting"""
        all_found = all(any(keyword.lower() in str(result).lower() 
                          for result in results) 
                       for keyword in expected_keywords)
        
        return {
            "query": query,
            "expected_keywords": expected_keywords,
            "results_count": len(results),
            "all_keywords_found": all_found
        }


@pytest.fixture
def encryption_validator():
    """Provide encryption validator"""
    return EncryptionValidator()
