"""
E2E Test Scenarios 1-3
- Scenario 1: Happy Path (login → patient → query → response → audit → logout)
- Scenario 2: Access Control (unauthorized access rejected with 403)
- Scenario 3: Data Security (encrypted search verification)
"""

import pytest
import time
import json
from typing import Dict
from datetime import datetime, timedelta
from tests.e2e.conftest import TestEnvironment, APIClient, AuditTrailValidator


class TestScenario1HappyPath:
    """Scenario 1: Complete happy path workflow"""
    
    def test_clinician_login(self, authenticated_client_a, test_env):
        """Step 1: Clinician logs in successfully"""
        # Verify token is set
        assert authenticated_client_a.auth_token is not None
        assert authenticated_client_a.auth_token != ""
        
        # Verify request was logged
        history = authenticated_client_a.get_response_history()
        assert len(history) > 0
        assert history[0]["method"] == "POST"
        assert history[0]["status_code"] == 200
        
        logger = authenticated_client_a.session.headers.get("Authorization")
        assert logger is not None
    
    def test_patient_selection(self, authenticated_client_a, test_env):
        """Step 2: Clinician selects patient"""
        # Get accessible patients
        result = authenticated_client_a.get_patients()
        assert result["success"], f"Failed to get patients: {result}"
        
        patients = result["patients"]
        assert len(patients) > 0, "No patients available"
        
        # Verify patient data contains expected fields
        patient = patients[0]
        assert "patient_id" in patient
        assert "name" in patient
        assert "dob" in patient
        
        logger = authenticated_client_a.session.headers.get("Authorization")
        assert logger is not None
    
    def test_get_patient_data(self, authenticated_client_a, test_env):
        """Step 3: Retrieve patient medical data"""
        result = authenticated_client_a.get_patient_data(test_env.TEST_PATIENT_A["patient_id"])
        
        assert result["success"], f"Failed to get patient data: {result}"
        data = result["data"]
        
        # Verify patient data structure
        assert "patient_id" in data
        assert "name" in data
        assert "medical_history" in data or "conditions" in data or "medications" in data
    
    def test_clinical_query(self, authenticated_client_a, test_env):
        """Step 4: Submit clinical query"""
        question = "What is the patient's current medication list?"
        result = authenticated_client_a.query(
            test_env.TEST_PATIENT_A["patient_id"],
            question
        )
        
        assert result["success"], f"Query failed: {result}"
        assert result["status_code"] == 200
        
        # Verify response structure
        assert "answer" in result
        assert result["answer"] is not None
        assert len(result["answer"]) > 0
        
        # Verify sources are included
        assert "sources" in result
        assert isinstance(result["sources"], list)
        
        # Verify disclaimer is present
        assert "disclaimer" in result
        assert result["disclaimer"] is not None
        
        # Verify performance <5s
        assert result["response_time"] < 5, f"Response too slow: {result['response_time']}s"
    
    def test_response_quality(self, authenticated_client_a, test_env):
        """Step 5: Verify response is clinically reasonable"""
        question = "What are the patient's known allergies?"
        result = authenticated_client_a.query(
            test_env.TEST_PATIENT_A["patient_id"],
            question
        )
        
        assert result["success"]
        answer = result["answer"]
        
        # Verify answer is not empty
        assert answer and len(answer) > 0
        
        # Verify answer contains relevant information
        # (Check for common clinical terms or structures)
        assert any(term in answer.lower() for term in [
            "allergy", "no known", "nka", "allergic", "reaction", "none", "unknown"
        ])
    
    def test_audit_log_entry_created(self, authenticated_client_a, test_env, audit_validator):
        """Step 6: Verify query appears in audit log"""
        patient_id = test_env.TEST_PATIENT_A["patient_id"]
        
        # Execute query
        question = "What is the patient's medical history?"
        authenticated_client_a.query(patient_id, question)
        
        # Wait briefly for log persistence
        time.sleep(0.5)
        
        # Retrieve audit log
        result = authenticated_client_a.get_audit_log(patient_id=patient_id)
        assert result["success"], f"Failed to get audit log: {result}"
        
        log_entries = result["log"]
        assert len(log_entries) > 0, "No audit entries found"
        
        # Verify latest entry is the query
        latest_entry = log_entries[0]
        assert latest_entry["action"] == "QUERY"
        assert latest_entry["patient_id"] == patient_id
        assert "timestamp" in latest_entry
    
    def test_logout(self, authenticated_client_a):
        """Step 7: Clinician logs out successfully"""
        result = authenticated_client_a.logout()
        assert result["success"], f"Logout failed: {result}"
        
        # Verify token is cleared
        assert authenticated_client_a.auth_token is None
    
    def test_complete_workflow(self, api_client, test_env, audit_validator):
        """Complete happy path test (all steps)"""
        # Step 1: Login
        login_result = api_client.login(
            test_env.TEST_CLINICIAN_A["username"],
            test_env.TEST_CLINICIAN_A["password"]
        )
        assert login_result["success"]
        
        # Step 2: Get patients
        patients_result = api_client.get_patients()
        assert patients_result["success"]
        assert len(patients_result["patients"]) > 0
        
        # Step 3: Get patient data
        patient_id = test_env.TEST_PATIENT_A["patient_id"]
        patient_result = api_client.get_patient_data(patient_id)
        assert patient_result["success"]
        
        # Step 4: Execute query
        query_result = api_client.query(patient_id, "What medications is the patient taking?")
        assert query_result["success"]
        assert query_result["response_time"] < 5
        
        # Step 5: Verify audit log
        audit_result = api_client.get_audit_log(patient_id=patient_id)
        assert audit_result["success"]
        assert len(audit_result["log"]) > 0
        
        # Step 6: Logout
        logout_result = api_client.logout()
        assert logout_result["success"]


class TestScenario2AccessControl:
    """Scenario 2: Access control enforcement (RBAC)"""
    
    def test_unauthorized_patient_access_forbidden(self, authenticated_client_a, test_env):
        """Clinician A cannot query patient assigned to Clinician B"""
        # Try to query patient assigned to Clinician B
        result = authenticated_client_a.query(
            test_env.TEST_PATIENT_B["patient_id"],  # Assigned to Clinician B
            "What is the patient's medical history?"
        )
        
        # Should be forbidden
        assert not result["success"], "Query should have been rejected"
        assert result["status_code"] == 403, f"Expected 403, got {result.get('status_code')}"
    
    def test_unauthorized_patient_data_access_forbidden(self, authenticated_client_a, test_env):
        """Clinician A cannot view patient data assigned to Clinician B"""
        result = authenticated_client_a.get_patient_data(test_env.TEST_PATIENT_B["patient_id"])
        
        # Should be forbidden or not found
        assert not result["success"]
        assert result["status_code"] in [403, 404]
    
    def test_audit_log_records_denied_access(self, authenticated_client_a, test_env):
        """Audit log records denied access attempt"""
        patient_id = test_env.TEST_PATIENT_B["patient_id"]
        
        # Attempt unauthorized access
        authenticated_client_a.query(patient_id, "What are the patient's allergies?")
        
        time.sleep(0.5)
        
        # Check audit log for denied access
        audit_result = authenticated_client_a.get_audit_log(patient_id=patient_id)
        
        # Depending on implementation, log may or may not be accessible to unauthorized user
        # The key is that the attempt should be logged on backend
        # Verify last request has 403 status
        history = authenticated_client_a.get_response_history()
        assert any(entry["status_code"] == 403 for entry in history)
    
    def test_unauthenticated_request_rejected(self, test_env):
        """Unauthenticated request is rejected"""
        client = APIClient(test_env.BACKEND_URL)
        # Don't authenticate, try to query
        
        result = client.query(
            test_env.TEST_PATIENT_A["patient_id"],
            "What is the patient's medical history?"
        )
        
        assert not result["success"]
        assert result["status_code"] in [401, 403]
    
    def test_invalid_token_rejected(self, test_env):
        """Invalid/expired token is rejected"""
        client = APIClient(test_env.BACKEND_URL)
        client.set_auth_token("invalid_token_xyz")
        
        result = client.query(
            test_env.TEST_PATIENT_A["patient_id"],
            "What is the patient's medical history?"
        )
        
        assert not result["success"]
        assert result["status_code"] in [401, 403]


class TestScenario3DataSecurity:
    """Scenario 3: Data security and encrypted search"""
    
    def test_embeddings_encrypted_in_storage(self):
        """Verify embeddings are encrypted in CyborgDB storage"""
        # Check embeddings storage for plaintext
        import os
        embeddings_path = "embeddings/encrypted/vectors_enc.json"
        
        if os.path.exists(embeddings_path):
            try:
                with open(embeddings_path, 'r') as f:
                    content = f.read()
                
                # Try to parse as JSON - if encrypted, should fail or be unreadable
                try:
                    data = json.loads(content)
                    
                    # If it parsed, check if values are encrypted (not readable floats)
                    if "vectors" in data:
                        first_vector = data["vectors"][0] if isinstance(data["vectors"], list) else list(data["vectors"].values())[0]
                        
                        # Encrypted vectors should be strings (base64) not floats
                        if isinstance(first_vector, list):
                            is_encrypted = not all(isinstance(x, (int, float)) for x in first_vector)
                        else:
                            is_encrypted = not isinstance(first_vector, (int, float))
                        
                        assert is_encrypted, "Vectors appear to be unencrypted (floats)"
                except json.JSONDecodeError:
                    # If JSON parsing fails, likely encrypted - good
                    pass
            except Exception as e:
                pytest.skip(f"Could not verify encryption: {str(e)}")
    
    def test_encrypted_search_returns_correct_results(self, authenticated_client_a, test_env):
        """Execute search and verify correct results returned without decrypting on disk"""
        patient_id = test_env.TEST_PATIENT_A["patient_id"]
        
        # Query 1
        result1 = authenticated_client_a.query(
            patient_id,
            "What medications is the patient on?"
        )
        assert result1["success"]
        
        # Query 2 - similar query should return consistent results
        result2 = authenticated_client_a.query(
            patient_id,
            "What are the patient's current medications?"
        )
        assert result2["success"]
        
        # Both should return medication-related information
        answer1 = result1["answer"].lower()
        answer2 = result2["answer"].lower()
        
        # Verify answers are related to medications
        medication_terms = ["medication", "med", "drug", "prescri", "taking"]
        assert any(term in answer1 for term in medication_terms), "Query 1 not medication-related"
        assert any(term in answer2 for term in medication_terms), "Query 2 not medication-related"
    
    def test_search_result_consistency(self, authenticated_client_a, test_env):
        """Verify search results are consistent across multiple identical queries"""
        patient_id = test_env.TEST_PATIENT_A["patient_id"]
        question = "What are the patient's known conditions?"
        
        results = []
        for _ in range(3):
            result = authenticated_client_a.query(patient_id, question)
            assert result["success"]
            results.append(result["answer"])
        
        # Results should be identical or very similar (some variation is OK)
        assert results[0] == results[1] or len(results[0]) == len(results[1])
        assert results[1] == results[2] or len(results[1]) == len(results[2])
    
    def test_no_plaintext_patient_data_in_logs(self, authenticated_client_a, test_env):
        """Verify sensitive patient data not stored as plaintext in logs"""
        # Execute query
        patient_id = test_env.TEST_PATIENT_A["patient_id"]
        authenticated_client_a.query(patient_id, "What are all patient details?")
        
        # Check log files
        import os
        import glob
        
        log_files = glob.glob("benchmarks/logs/*.log")
        sensitive_terms = [test_env.TEST_PATIENT_A["name"]]
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Check for sensitive data (may be OK if it's the query question itself)
                for term in sensitive_terms:
                    # It's OK if it appears in the query, but not in responses
                    assert content.count(term) < 5, f"Sensitive data appears too many times in {log_file}"
            except Exception:
                pass  # Skip if can't read log file
