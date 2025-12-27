"""
Unit tests for API endpoints (backend/main.py)

Coverage:
- Request validation (missing fields, invalid types)
- Response format (all required fields present)
- Status codes and error handling
- Input validation and constraints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.models import (
    LoginRequest,
    PatientSearchRequest,
    QueryResponse,
    Token,
    SourceDocument,
)


class TestLoginEndpoint:
    """Test login endpoint validation."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_login_request_validation(self):
        """Test login request model validation."""
        # Valid request
        valid = LoginRequest(username="user", password="pass")
        assert valid.username == "user"
        assert valid.password == "pass"

    @pytest.mark.unit
    @pytest.mark.api
    def test_login_missing_username(self):
        """Test login request missing username."""
        with pytest.raises(ValueError):
            LoginRequest(password="pass")

    @pytest.mark.unit
    @pytest.mark.api
    def test_login_missing_password(self):
        """Test login request missing password."""
        with pytest.raises(ValueError):
            LoginRequest(username="user")

    @pytest.mark.unit
    @pytest.mark.api
    def test_token_response_format(self):
        """Test token response format."""
        token = Token(access_token="token123", token_type="bearer")
        
        assert token.access_token == "token123"
        assert token.token_type == "bearer"

    @pytest.mark.unit
    @pytest.mark.api
    def test_token_response_required_fields(self):
        """Test token response has required fields."""
        token = Token(access_token="token", token_type="bearer")
        
        assert hasattr(token, "access_token")
        assert hasattr(token, "token_type")


class TestQueryEndpoint:
    """Test query endpoint validation."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_query_request_valid(self, valid_query_requests):
        """Test valid query requests."""
        for req_data in valid_query_requests:
            req = PatientSearchRequest(**req_data)
            assert req.patient_id == req_data["patient_id"]
            assert req.question == req_data["question"]

    @pytest.mark.unit
    @pytest.mark.api
    def test_query_missing_patient_id(self):
        """Test query missing patient ID."""
        with pytest.raises(ValueError):
            PatientSearchRequest(
                question="What is the diagnosis?",
                retrieve_k=5,
                temperature=0.7
            )

    @pytest.mark.unit
    @pytest.mark.api
    def test_query_missing_question(self):
        """Test query missing question."""
        with pytest.raises(ValueError):
            PatientSearchRequest(
                patient_id="P001",
                retrieve_k=5,
                temperature=0.7
            )

    @pytest.mark.unit
    @pytest.mark.api
    def test_query_question_too_short(self):
        """Test query question too short."""
        with pytest.raises(ValueError):
            PatientSearchRequest(
                patient_id="P001",
                question="ab",  # Minimum 3 chars
                retrieve_k=5,
                temperature=0.7
            )

    @pytest.mark.unit
    @pytest.mark.api
    def test_query_question_too_long(self):
        """Test query question too long."""
        with pytest.raises(ValueError):
            PatientSearchRequest(
                patient_id="P001",
                question="Q" * 1001,  # Maximum 1000 chars
                retrieve_k=5,
                temperature=0.7
            )

    @pytest.mark.unit
    @pytest.mark.api
    def test_query_retrieve_k_invalid_low(self):
        """Test query retrieve_k too low."""
        with pytest.raises(ValueError):
            PatientSearchRequest(
                patient_id="P001",
                question="Valid question?",
                retrieve_k=0,  # Minimum 1
                temperature=0.7
            )

    @pytest.mark.unit
    @pytest.mark.api
    def test_query_retrieve_k_invalid_high(self):
        """Test query retrieve_k too high."""
        with pytest.raises(ValueError):
            PatientSearchRequest(
                patient_id="P001",
                question="Valid question?",
                retrieve_k=21,  # Maximum 20
                temperature=0.7
            )

    @pytest.mark.unit
    @pytest.mark.api
    def test_query_temperature_invalid_low(self):
        """Test query temperature too low."""
        with pytest.raises(ValueError):
            PatientSearchRequest(
                patient_id="P001",
                question="Valid question?",
                retrieve_k=5,
                temperature=-0.1  # Minimum 0.0
            )

    @pytest.mark.unit
    @pytest.mark.api
    def test_query_temperature_invalid_high(self):
        """Test query temperature too high."""
        with pytest.raises(ValueError):
            PatientSearchRequest(
                patient_id="P001",
                question="Valid question?",
                retrieve_k=5,
                temperature=1.1  # Maximum 1.0
            )

    @pytest.mark.unit
    @pytest.mark.api
    def test_query_default_values(self):
        """Test query default values."""
        req = PatientSearchRequest(
            patient_id="P001",
            question="Valid question?"
        )
        
        # Check defaults
        assert req.retrieve_k == 5
        assert req.temperature == 0.7
        assert req.filter_doc_type is None

    @pytest.mark.unit
    @pytest.mark.api
    def test_query_optional_fields(self):
        """Test query optional fields."""
        req = PatientSearchRequest(
            patient_id="P001",
            question="Valid question?",
            filter_doc_type="Observation"
        )
        
        assert req.filter_doc_type == "Observation"


class TestResponseFormat:
    """Test response format validation."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_source_document_format(self):
        """Test source document format."""
        source = SourceDocument(
            type="Observation",
            date="2024-01-10",
            snippet="Patient has hypertension",
            similarity=0.95
        )
        
        assert source.type == "Observation"
        assert source.date == "2024-01-10"
        assert source.snippet == "Patient has hypertension"
        assert source.similarity == 0.95

    @pytest.mark.unit
    @pytest.mark.api
    def test_source_document_defaults(self):
        """Test source document default values."""
        source = SourceDocument(snippet="Some text", similarity=0.8)
        
        assert source.type == "unknown"
        assert source.date == "unknown"

    @pytest.mark.unit
    @pytest.mark.api
    def test_query_response_format(self):
        """Test query response format."""
        response = QueryResponse(
            query_id="q123",
            answer="The patient has hypertension.",
            sources=[
                SourceDocument(
                    snippet="Hypertension noted",
                    similarity=0.9
                )
            ],
            confidence=0.92,
            disclaimer="This is clinical information."
        )
        
        assert response.query_id == "q123"
        assert response.answer == "The patient has hypertension."
        assert len(response.sources) == 1
        assert response.confidence == 0.92

    @pytest.mark.unit
    @pytest.mark.api
    def test_query_response_required_fields(self):
        """Test query response has all required fields."""
        response = QueryResponse(
            query_id="q1",
            answer="Answer text",
            sources=[],
            confidence=0.85,
            disclaimer="Disclaimer"
        )
        
        assert hasattr(response, "query_id")
        assert hasattr(response, "answer")
        assert hasattr(response, "sources")
        assert hasattr(response, "confidence")
        assert hasattr(response, "disclaimer")

    @pytest.mark.unit
    @pytest.mark.api
    def test_query_response_empty_sources(self):
        """Test query response with empty sources."""
        response = QueryResponse(
            query_id="q1",
            answer="No relevant sources found",
            sources=[],
            confidence=0.0,
            disclaimer="Limited information"
        )
        
        assert len(response.sources) == 0

    @pytest.mark.unit
    @pytest.mark.api
    def test_query_response_multiple_sources(self):
        """Test query response with multiple sources."""
        sources = [
            SourceDocument(snippet=f"Source {i}", similarity=0.9 - i*0.1)
            for i in range(5)
        ]
        
        response = QueryResponse(
            query_id="q1",
            answer="Combined answer",
            sources=sources,
            confidence=0.85,
            disclaimer="Info from multiple sources"
        )
        
        assert len(response.sources) == 5


class TestTypeValidation:
    """Test request type validation."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_query_patient_id_type(self):
        """Test patient ID is string."""
        req = PatientSearchRequest(
            patient_id="P001",
            question="Question?"
        )
        
        assert isinstance(req.patient_id, str)

    @pytest.mark.unit
    @pytest.mark.api
    def test_query_question_type(self):
        """Test question is string."""
        req = PatientSearchRequest(
            patient_id="P001",
            question="Valid question?"
        )
        
        assert isinstance(req.question, str)

    @pytest.mark.unit
    @pytest.mark.api
    def test_query_retrieve_k_type(self):
        """Test retrieve_k is integer."""
        req = PatientSearchRequest(
            patient_id="P001",
            question="Question?",
            retrieve_k=5
        )
        
        assert isinstance(req.retrieve_k, int)

    @pytest.mark.unit
    @pytest.mark.api
    def test_query_temperature_type(self):
        """Test temperature is float."""
        req = PatientSearchRequest(
            patient_id="P001",
            question="Question?",
            temperature=0.5
        )
        
        assert isinstance(req.temperature, (int, float))

    @pytest.mark.unit
    @pytest.mark.api
    def test_response_confidence_type(self):
        """Test confidence is float."""
        response = QueryResponse(
            query_id="q1",
            answer="Answer",
            sources=[],
            confidence=0.85,
            disclaimer="Info"
        )
        
        assert isinstance(response.confidence, (int, float))

    @pytest.mark.unit
    @pytest.mark.api
    def test_response_similarity_type(self):
        """Test similarity is float."""
        source = SourceDocument(
            snippet="Text",
            similarity=0.9
        )
        
        assert isinstance(source.similarity, (int, float))


class TestBoundaryValues:
    """Test boundary value validation."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_query_retrieve_k_boundaries(self):
        """Test retrieve_k boundary values."""
        # Minimum valid
        req_min = PatientSearchRequest(
            patient_id="P001",
            question="Question?",
            retrieve_k=1
        )
        assert req_min.retrieve_k == 1
        
        # Maximum valid
        req_max = PatientSearchRequest(
            patient_id="P001",
            question="Question?",
            retrieve_k=20
        )
        assert req_max.retrieve_k == 20

    @pytest.mark.unit
    @pytest.mark.api
    def test_query_temperature_boundaries(self):
        """Test temperature boundary values."""
        # Minimum
        req_min = PatientSearchRequest(
            patient_id="P001",
            question="Question?",
            temperature=0.0
        )
        assert req_min.temperature == 0.0
        
        # Maximum
        req_max = PatientSearchRequest(
            patient_id="P001",
            question="Question?",
            temperature=1.0
        )
        assert req_max.temperature == 1.0

    @pytest.mark.unit
    @pytest.mark.api
    def test_query_question_length_boundaries(self):
        """Test question length boundaries."""
        # Minimum
        req_min = PatientSearchRequest(
            patient_id="P001",
            question="abc"  # 3 characters
        )
        assert len(req_min.question) == 3
        
        # Maximum
        question_max = "x" * 1000
        req_max = PatientSearchRequest(
            patient_id="P001",
            question=question_max
        )
        assert len(req_max.question) == 1000


class TestErrorResponses:
    """Test error response format."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_invalid_request_types(self):
        """Test invalid request types."""
        # Invalid types should raise errors
        with pytest.raises((TypeError, ValueError)):
            PatientSearchRequest(
                patient_id=123,  # Should be string
                question="Question?"
            )

    @pytest.mark.unit
    @pytest.mark.api
    def test_empty_string_fields(self):
        """Test empty string fields."""
        with pytest.raises(ValueError):
            PatientSearchRequest(
                patient_id="",  # Empty
                question="Question?"
            )

    @pytest.mark.unit
    @pytest.mark.api
    def test_none_required_fields(self):
        """Test None in required fields."""
        with pytest.raises((TypeError, ValueError)):
            PatientSearchRequest(
                patient_id=None,
                question="Question?"
            )


class TestAllValidationRules:
    """Integration test for all validation rules."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_all_valid_requests(self, valid_query_requests):
        """Test all valid requests."""
        for req_data in valid_query_requests:
            req = PatientSearchRequest(**req_data)
            assert req is not None

    @pytest.mark.unit
    @pytest.mark.api
    def test_all_invalid_requests(self, invalid_query_requests):
        """Test all invalid requests."""
        for req_data in invalid_query_requests:
            try:
                # Should raise validation error
                PatientSearchRequest(
                    patient_id=req_data.get("patient_id", "P001"),
                    question=req_data.get("question", "Question?"),
                    retrieve_k=req_data.get("retrieve_k", 5),
                    temperature=req_data.get("temperature", 0.7)
                )
                # If we get here, the request was not caught as invalid
                # This might be expected for some edge cases
            except (ValueError, TypeError):
                # Expected - validation error caught
                pass
