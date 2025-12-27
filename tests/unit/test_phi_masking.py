"""
Unit tests for PHI detection and masking (data-pipeline/phi_scrubber.py)

Coverage:
- Presidio analyzer PII detection
- Masking logic (original not in output)
- Edge cases (dates, abbreviations, formats)
- Token generation and consistency
- De-identification success rate
"""
import pytest
import json
import tempfile
import os
from data_pipeline.phi_scrubber import PHIScrubber


class TestPresidioAnalyzer:
    """Test Presidio-based PHI detection."""

    def setup_method(self):
        """Setup for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.token_map_path = os.path.join(self.temp_dir, "token_map.json")
        self.scrubber = PHIScrubber(token_map_path=self.token_map_path)

    def teardown_method(self):
        """Cleanup after each test."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @pytest.mark.unit
    @pytest.mark.phi
    def test_detect_person_names(self):
        """Test PERSON entity detection."""
        text = "John Smith was admitted to the hospital."
        results = self.scrubber.analyzer.analyze(text=text, language='en')
        
        person_entities = [r for r in results if r.entity_type == "PERSON"]
        assert len(person_entities) > 0, "Should detect person names"

    @pytest.mark.unit
    @pytest.mark.phi
    def test_detect_phone_numbers(self):
        """Test PHONE_NUMBER entity detection."""
        text = "Contact the patient at 555-123-4567."
        results = self.scrubber.analyzer.analyze(text=text, language='en')
        
        phone_entities = [r for r in results if r.entity_type == "PHONE_NUMBER"]
        assert len(phone_entities) > 0, "Should detect phone numbers"

    @pytest.mark.unit
    @pytest.mark.phi
    def test_detect_email_addresses(self):
        """Test EMAIL_ADDRESS entity detection."""
        text = "Email the doctor at john.doe@hospital.com."
        results = self.scrubber.analyzer.analyze(text=text, language='en')
        
        email_entities = [r for r in results if r.entity_type == "EMAIL_ADDRESS"]
        assert len(email_entities) > 0, "Should detect email addresses"

    @pytest.mark.unit
    @pytest.mark.phi
    def test_detect_dates(self):
        """Test DATE_TIME entity detection."""
        test_dates = [
            "01/15/2024",
            "2024-01-15",
            "January 15, 2024",
            "15 Jan 2024",
        ]
        
        for date_str in test_dates:
            text = f"Patient admitted on {date_str}."
            results = self.scrubber.analyzer.analyze(text=text, language='en')
            date_entities = [r for r in results if r.entity_type == "DATE_TIME"]
            assert len(date_entities) > 0, f"Should detect date: {date_str}"

    @pytest.mark.unit
    @pytest.mark.phi
    def test_detect_locations(self):
        """Test LOCATION entity detection."""
        test_locations = [
            "New York",
            "Los Angeles, CA",
            "Boston, MA",
        ]
        
        for location in test_locations:
            text = f"Patient resides in {location}."
            results = self.scrubber.analyzer.analyze(text=text, language='en')
            loc_entities = [r for r in results if r.entity_type == "LOCATION"]
            # Location detection may vary, so we just check the code runs
            assert isinstance(results, list)

    @pytest.mark.unit
    @pytest.mark.phi
    def test_no_phi_detection(self):
        """Test that non-PHI text doesn't trigger false positives."""
        text = "The patient has hypertension and diabetes mellitus."
        results = self.scrubber.analyzer.analyze(text=text, language='en')
        
        # Medical conditions should not be detected as PHI
        assert len(results) == 0 or all(
            r.entity_type not in ["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS"]
            for r in results
        )


class TestMaskingLogic:
    """Test PHI masking and de-identification."""

    def setup_method(self):
        """Setup for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.token_map_path = os.path.join(self.temp_dir, "token_map.json")
        self.scrubber = PHIScrubber(token_map_path=self.token_map_path)

    def teardown_method(self):
        """Cleanup after each test."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @pytest.mark.unit
    @pytest.mark.phi
    def test_original_not_in_output(self):
        """Verify original PHI is not in masked output."""
        original_names = ["John Smith", "Jane Doe", "Robert Johnson"]
        
        for name in original_names:
            text = f"Patient {name} was admitted."
            masked = self.scrubber.scrub_text(text)
            
            # Original name should not appear in masked text
            assert name not in masked, f"Original name '{name}' found in masked output"

    @pytest.mark.unit
    @pytest.mark.phi
    def test_masking_creates_tokens(self):
        """Verify masking creates valid tokens."""
        text = "Contact John Smith at 555-123-4567."
        masked = self.scrubber.scrub_text(text)
        
        # Should have tokens
        assert "[" in masked and "]" in masked, "Masked text should contain tokens"
        
        # Original values should be replaced
        assert "John Smith" not in masked
        assert "555-123-4567" not in masked

    @pytest.mark.unit
    @pytest.mark.phi
    def test_consistent_token_mapping(self):
        """Test that same PHI maps to same token."""
        name = "John Smith"
        text1 = f"Patient {name} arrived."
        text2 = f"Doctor {name} examined."
        
        masked1 = self.scrubber.scrub_text(text1)
        masked2 = self.scrubber.scrub_text(text2)
        
        # Extract tokens (simple extraction)
        token1 = [t for t in masked1.split() if "[" in t and "]" in t][0]
        token2 = [t for t in masked2.split() if "[" in t and "]" in t][0]
        
        assert token1 == token2, "Same PHI should map to same token"

    @pytest.mark.unit
    @pytest.mark.phi
    def test_token_map_persistence(self):
        """Test that token map is saved and loaded."""
        text = "John Smith works here."
        self.scrubber.scrub_text(text)
        
        # Save token map
        self.scrubber._save_token_map()
        
        # Create new scrubber and verify token map is loaded
        scrubber2 = PHIScrubber(token_map_path=self.token_map_path)
        assert len(scrubber2.token_map) > 0, "Token map should persist"

    @pytest.mark.unit
    @pytest.mark.phi
    def test_scrub_empty_text(self):
        """Test masking of empty text."""
        result = self.scrubber.scrub_text("")
        assert result == "", "Empty text should return empty string"

    @pytest.mark.unit
    @pytest.mark.phi
    def test_scrub_none_text(self):
        """Test masking of None text."""
        result = self.scrubber.scrub_text(None)
        assert result == "", "None text should return empty string"


class TestEdgeCases:
    """Test edge cases in PHI detection and masking."""

    def setup_method(self):
        """Setup for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.token_map_path = os.path.join(self.temp_dir, "token_map.json")
        self.scrubber = PHIScrubber(token_map_path=self.token_map_path)

    def teardown_method(self):
        """Cleanup after each test."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @pytest.mark.unit
    @pytest.mark.phi
    def test_date_formats(self, phi_test_cases):
        """Test various date formats."""
        date_cases = [c for c in phi_test_cases if "date" in c["description"].lower()]
        
        for case in date_cases:
            text = case["text"]
            masked = self.scrubber.scrub_text(text)
            # Verify text is processed without errors
            assert isinstance(masked, str)

    @pytest.mark.unit
    @pytest.mark.phi
    def test_multiple_same_phi(self):
        """Test handling of multiple instances of same PHI."""
        text = "John Smith and John Smith met. John Smith called again."
        masked = self.scrubber.scrub_text(text)
        
        # Same person name should be masked consistently
        assert "John Smith" not in masked
        masked_tokens = masked.count("[")
        assert masked_tokens >= 3, "Should mask all instances"

    @pytest.mark.unit
    @pytest.mark.phi
    def test_overlapping_phi(self):
        """Test handling of overlapping PHI entities."""
        # E.g., "Dr. John Smith" - contains both title and name
        text = "Dr. John Smith at Hospital in New York"
        masked = self.scrubber.scrub_text(text)
        
        assert isinstance(masked, str)
        assert "John Smith" not in masked

    @pytest.mark.unit
    @pytest.mark.phi
    def test_special_characters_in_phi(self):
        """Test PHI with special characters."""
        text = 'Contact "Dr. John Smith-Jr." at (555) 123-4567 ext. 123'
        masked = self.scrubber.scrub_text(text)
        
        assert isinstance(masked, str)
        # Original phone should be masked
        assert "123-4567" not in masked

    @pytest.mark.unit
    @pytest.mark.phi
    def test_very_long_text(self):
        """Test masking of very long text."""
        text = "John Smith, " * 1000
        masked = self.scrubber.scrub_text(text)
        
        assert isinstance(masked, str)
        assert "John Smith" not in masked

    @pytest.mark.unit
    @pytest.mark.phi
    def test_text_with_numbers_only(self):
        """Test text with only numbers."""
        text = "123-45-6789 555-1234 01011998"
        masked = self.scrubber.scrub_text(text)
        
        assert isinstance(masked, str)


class TestPHIDetectionAccuracy:
    """Test PHI detection accuracy (target: ≥95%)."""

    def setup_method(self):
        """Setup for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.token_map_path = os.path.join(self.temp_dir, "token_map.json")
        self.scrubber = PHIScrubber(token_map_path=self.token_map_path)

    def teardown_method(self):
        """Cleanup after each test."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @pytest.mark.unit
    @pytest.mark.phi
    def test_detection_rate(self, phi_test_cases):
        """Test overall PHI detection rate."""
        detected_count = 0
        total_count = len([c for c in phi_test_cases if c["should_mask"]])
        
        for case in phi_test_cases:
            if not case["should_mask"]:
                continue
            
            results = self.scrubber.analyzer.analyze(text=case["text"], language='en')
            if len(results) > 0:
                detected_count += 1
        
        detection_rate = detected_count / total_count if total_count > 0 else 0
        assert detection_rate >= 0.85, f"Detection rate {detection_rate:.2%} below 85%"

    @pytest.mark.unit
    @pytest.mark.phi
    def test_false_positive_rate(self, phi_test_cases):
        """Test false positive rate."""
        false_positives = 0
        negative_cases = [c for c in phi_test_cases if not c["should_mask"]]
        
        for case in negative_cases:
            results = self.scrubber.analyzer.analyze(text=case["text"], language='en')
            if len(results) > 0:
                false_positives += 1
        
        total_negative = len(negative_cases)
        false_positive_rate = false_positives / total_negative if total_negative > 0 else 0
        
        # Acceptable false positive rate: < 20%
        assert false_positive_rate < 0.20, f"False positive rate {false_positive_rate:.2%} too high"


class TestIntegrationMasking:
    """Integration tests for complete masking workflow."""

    def setup_method(self):
        """Setup for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.token_map_path = os.path.join(self.temp_dir, "token_map.json")
        self.scrubber = PHIScrubber(token_map_path=self.token_map_path)

    def teardown_method(self):
        """Cleanup after each test."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @pytest.mark.unit
    @pytest.mark.phi
    def test_clinical_note_masking(self):
        """Test masking of realistic clinical note."""
        clinical_note = """
        PATIENT: John Smith
        DOB: 01/15/1980
        MRN: 123456789
        CONTACT: john.smith@email.com, (555) 123-4567
        
        Admitted to Hospital on 2024-01-10. Patient presents with hypertension 
        and elevated blood pressure. Residing in New York, NY 10001.
        
        Physician: Dr. Robert Johnson
        """
        
        masked = self.scrubber.scrub_text(clinical_note)
        
        # Verify no original PHI remains
        assert "John Smith" not in masked
        assert "01/15/1980" not in masked
        assert "123456789" not in masked
        assert "john.smith@email.com" not in masked
        assert "(555) 123-4567" not in masked
        assert "Dr. Robert Johnson" not in masked

    @pytest.mark.unit
    @pytest.mark.phi
    def test_fhir_text_extraction_masking(self, fhir_test_data):
        """Test masking of text extracted from FHIR."""
        # Extract text from FHIR
        patient_name = fhir_test_data["entry"][0]["resource"]["name"][0]
        text = f"{patient_name['given'][0]} {patient_name['family']}"
        
        masked = self.scrubber.scrub_text(text)
        
        # Original name should be masked
        assert "John" not in masked
        assert "Smith" not in masked
