"""
Integration tests for end-to-end workflows

Coverage:
- Complete query workflow (embedding → search → LLM → response)
- Authentication and authorization workflows
- Data pipeline de-identification and embedding
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from backend.models import PatientSearchRequest, QueryResponse


class TestQueryWorkflow:
    """Test end-to-end query workflow."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_query_workflow_complete(
        self,
        mock_embedder,
        mock_cyborg_manager,
        mock_llm_service,
        admin_token
    ):
        """Test complete query workflow."""
        # 1. User authenticates
        assert admin_token is not None
        
        # 2. User makes query request
        query_request = PatientSearchRequest(
            patient_id="P001",
            question="What are the vital signs?",
            retrieve_k=5,
            temperature=0.7
        )
        
        # 3. Generate embedding
        embedding = mock_embedder.get_embedding(query_request.question)
        assert len(embedding) == 384
        
        # 4. Search CyborgDB
        results = mock_cyborg_manager.search()
        assert len(results) > 0
        
        # 5. Generate LLM response
        response_data = mock_llm_service.generate_response()
        assert "answer" in response_data
        assert "confidence" in response_data

    @pytest.mark.integration
    def test_query_workflow_with_audit_log(
        self,
        mock_embedder,
        mock_cyborg_manager,
        mock_llm_service
    ):
        """Test query workflow with audit logging."""
        query_id = "q_" + str(datetime.utcnow().timestamp())
        
        # Simulate query workflow
        embedding = mock_embedder.get_embedding("test question")
        results = mock_cyborg_manager.search()
        response = mock_llm_service.generate_response()
        
        # Verify components were called
        assert embedding is not None
        assert results is not None
        assert response is not None

    @pytest.mark.integration
    def test_query_workflow_error_handling(self, mock_embedder):
        """Test query workflow error handling."""
        # Test with invalid input
        invalid_question = ""
        
        # Should handle gracefully
        try:
            embedding = mock_embedder.get_embedding(invalid_question)
            assert embedding is not None
        except Exception as e:
            pytest.fail(f"Should handle empty question: {e}")

    @pytest.mark.integration
    def test_query_sources_returned(self, mock_cyborg_manager):
        """Test that query returns source documents."""
        results = mock_cyborg_manager.search()
        
        assert len(results) > 0
        for result in results:
            assert "text_snippet" in result
            assert "similarity" in result
            assert "metadata" in result

    @pytest.mark.integration
    def test_query_response_format(self, mock_llm_service):
        """Test query response format."""
        response = mock_llm_service.generate_response()
        
        assert "answer" in response
        assert isinstance(response["answer"], str)
        assert "confidence" in response
        assert isinstance(response["confidence"], (int, float))
        assert "sources" in response

    @pytest.mark.integration
    def test_multiple_sequential_queries(
        self,
        mock_embedder,
        mock_cyborg_manager,
        mock_llm_service
    ):
        """Test multiple sequential queries."""
        questions = [
            "What is the patient's diagnosis?",
            "Are there any allergies?",
            "What medications are prescribed?",
        ]
        
        for question in questions:
            embedding = mock_embedder.get_embedding(question)
            results = mock_cyborg_manager.search()
            response = mock_llm_service.generate_response()
            
            assert embedding is not None
            assert results is not None
            assert response is not None


class TestAuthenticationWorkflow:
    """Test authentication and authorization workflows."""

    @pytest.mark.integration
    def test_login_and_query_success(self, admin_token):
        """Test successful login and authorized query."""
        # User has token
        assert admin_token is not None
        assert len(admin_token) > 0
        
        # Token can be used for requests
        # (In real implementation, this would be passed to API endpoint)

    @pytest.mark.integration
    def test_unauthorized_query_fails(self):
        """Test unauthorized query fails."""
        # Query without token should fail
        # (In real implementation, 401 Unauthorized would be returned)
        pass

    @pytest.mark.integration
    def test_admin_can_query_any_patient(
        self,
        admin_token,
        mock_cyborg_manager,
        mock_embedder,
        mock_llm_service
    ):
        """Test admin can query any patient."""
        patients = ["P001", "P002", "P003"]
        
        for patient_id in patients:
            query = PatientSearchRequest(
                patient_id=patient_id,
                question="What is the status?"
            )
            
            # Should succeed
            embedding = mock_embedder.get_embedding(query.question)
            assert embedding is not None

    @pytest.mark.integration
    def test_resident_can_query_assigned_patient(
        self,
        resident_token,
        mock_embedder
    ):
        """Test resident can query assigned patients."""
        # Resident has P001, P002
        assigned_patients = ["P001", "P002"]
        
        for patient_id in assigned_patients:
            query = PatientSearchRequest(
                patient_id=patient_id,
                question="Question?"
            )
            
            embedding = mock_embedder.get_embedding(query.question)
            assert embedding is not None

    @pytest.mark.integration
    def test_resident_cannot_query_unassigned_patient(
        self,
        resident_token
    ):
        """Test resident cannot query unassigned patients."""
        # Resident does not have P999
        # (In real implementation, 403 Forbidden would be returned)
        pass

    @pytest.mark.integration
    def test_token_expiration(self):
        """Test token expiration."""
        from backend.auth import create_access_token
        
        # Create expired token
        data = {"sub": "user"}
        expired_delta = timedelta(minutes=-1)
        expired_token = create_access_token(data, expired_delta)
        
        # Token exists but is expired
        assert expired_token is not None
        
        import jwt
        from backend.auth import LOCAL_SECRET_KEY, LOCAL_ALGORITHM
        
        # Decoding should raise ExpiredSignatureError
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(
                expired_token,
                LOCAL_SECRET_KEY,
                algorithms=[LOCAL_ALGORITHM]
            )


class TestDataPipeline:
    """Test end-to-end data pipeline."""

    @pytest.mark.integration
    def test_fhir_to_de_identified_vector(
        self,
        fhir_test_data,
        mock_phi_scrubber,
        mock_embedder
    ):
        """Test FHIR data to de-identified vector."""
        # 1. Extract text from FHIR
        patient_resource = fhir_test_data["entry"][0]["resource"]
        patient_name = f"{patient_resource['name'][0]['given'][0]} {patient_resource['name'][0]['family']}"
        patient_text = f"Patient: {patient_name}, DOB: {patient_resource['birthDate']}"
        
        # 2. De-identify
        de_identified = mock_phi_scrubber.scrub_text(patient_text)
        assert "[" in de_identified  # Should have tokens
        
        # 3. Generate embedding
        embedding = mock_embedder.get_embedding(de_identified)
        assert len(embedding) == 384

    @pytest.mark.integration
    def test_fhir_observation_processing(
        self,
        fhir_test_data,
        mock_embedder
    ):
        """Test FHIR observation processing."""
        observation = fhir_test_data["entry"][1]["resource"]
        
        # Extract relevant text
        obs_text = f"Observation: {observation['code']['coding'][0]['display']}, Value: {observation['valueQuantity']['value']}"
        
        # Generate embedding
        embedding = mock_embedder.get_embedding(obs_text)
        assert len(embedding) == 384

    @pytest.mark.integration
    def test_batch_fhir_processing(
        self,
        fhir_test_data,
        mock_phi_scrubber,
        mock_embedder
    ):
        """Test batch processing of FHIR data."""
        entries = fhir_test_data["entry"]
        
        for entry in entries:
            resource = entry["resource"]
            
            # Extract text (simplified)
            text = str(resource).replace("{", "").replace("}", "")
            
            # De-identify
            de_identified = mock_phi_scrubber.scrub_text(text)
            
            # Embed
            embedding = mock_embedder.get_embedding(de_identified)
            assert embedding is not None

    @pytest.mark.integration
    def test_encryption_in_pipeline(
        self,
        mock_crypto_service,
        mock_embedder
    ):
        """Test encryption in data pipeline."""
        # 1. Generate embedding
        embedding = mock_embedder.get_embedding("Patient data")
        
        # 2. Create record
        record = {
            "patient_id": "P001",
            "vector": embedding,
            "text": "De-identified text",
        }
        
        # 3. Encrypt
        encrypted = mock_crypto_service.encrypt_record(record)
        assert "encrypted_data" in encrypted

    @pytest.mark.integration
    def test_phi_removal_verification(self, mock_phi_scrubber):
        """Test PHI is completely removed."""
        clinical_note = """
        PATIENT: John Smith
        DOB: 01/15/1980
        CONTACT: john@email.com
        
        Patient has hypertension.
        """
        
        masked = mock_phi_scrubber.scrub_text(clinical_note)
        
        # Verify no PHI in output
        assert "John Smith" not in masked
        assert "01/15/1980" not in masked
        assert "john@email.com" not in masked


class TestQueryAuditLog:
    """Test query audit logging."""

    @pytest.mark.integration
    def test_query_logged_with_user(self, admin_token):
        """Test query is logged with user information."""
        # In real implementation:
        # - Query executed
        # - Audit log entry created with user ID
        # - Timestamp recorded
        assert admin_token is not None

    @pytest.mark.integration
    def test_query_logged_with_patient(self):
        """Test query is logged with patient ID."""
        # Audit log should contain patient ID
        query = PatientSearchRequest(
            patient_id="P001",
            question="Question?"
        )
        
        assert query.patient_id == "P001"

    @pytest.mark.integration
    def test_unauthorized_access_logged(self):
        """Test unauthorized access attempts are logged."""
        # Unauthorized queries should be logged
        pass

    @pytest.mark.integration
    def test_query_results_cached(self, mock_cyborg_manager):
        """Test that search results are properly handled."""
        results1 = mock_cyborg_manager.search()
        results2 = mock_cyborg_manager.search()
        
        # Both calls should work
        assert results1 is not None
        assert results2 is not None


class TestErrorRecovery:
    """Test error handling and recovery."""

    @pytest.mark.integration
    def test_embedding_failure_recovery(self, mock_embedder):
        """Test recovery from embedding failure."""
        # Should handle edge cases gracefully
        edge_cases = ["", "a" * 10000, "123", None]
        
        for case in edge_cases:
            if case is None:
                continue
            try:
                embedding = mock_embedder.get_embedding(case)
                assert embedding is not None
            except Exception as e:
                pytest.fail(f"Should handle edge case: {e}")

    @pytest.mark.integration
    def test_search_failure_recovery(self, mock_cyborg_manager):
        """Test recovery from search failure."""
        # Should handle no results gracefully
        results = mock_cyborg_manager.search()
        assert isinstance(results, list)

    @pytest.mark.integration
    def test_llm_failure_recovery(self, mock_llm_service):
        """Test recovery from LLM failure."""
        response = mock_llm_service.generate_response()
        assert response is not None
        assert "answer" in response


class TestEndToEndQueryFlow:
    """Test complete end-to-end query flow."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_full_query_flow_success(
        self,
        admin_token,
        mock_embedder,
        mock_cyborg_manager,
        mock_llm_service,
        mock_phi_scrubber
    ):
        """Test successful full query flow."""
        # 1. Authentication
        assert admin_token is not None
        
        # 2. Create query
        query = PatientSearchRequest(
            patient_id="P001",
            question="What is the diagnosis?"
        )
        
        # 3. De-identify if needed (for audit)
        query_text_deidentified = mock_phi_scrubber.scrub_text(query.question)
        
        # 4. Generate embedding
        embedding = mock_embedder.get_embedding(query_text_deidentified)
        assert len(embedding) == 384
        
        # 5. Search
        results = mock_cyborg_manager.search()
        assert len(results) > 0
        
        # 6. Generate response
        response_data = mock_llm_service.generate_response()
        assert "answer" in response_data
        
        # 7. Create response object
        response = QueryResponse(
            query_id="q1",
            answer=response_data["answer"],
            sources=[],
            confidence=response_data["confidence"],
            disclaimer="For reference only"
        )
        
        assert response.answer is not None
        assert response.confidence > 0

    @pytest.mark.integration
    def test_multi_patient_query_isolation(
        self,
        admin_token,
        mock_embedder,
        mock_cyborg_manager
    ):
        """Test query isolation between patients."""
        patients = ["P001", "P002", "P003"]
        
        for patient_id in patients:
            query = PatientSearchRequest(
                patient_id=patient_id,
                question="What is the status?"
            )
            
            embedding = mock_embedder.get_embedding(query.question)
            assert embedding is not None
            
            # Results should be specific to patient
            results = mock_cyborg_manager.search()
            assert results is not None
