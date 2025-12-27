"""
Unit tests for embedding generation (embeddings/embedder.py)

Coverage:
- Embedding output shape (384-dim for MiniLM)
- Consistency (same input → same output)
- Numerical stability (no NaN/Inf)
- Edge cases (empty text, very long text)
"""
import pytest
import numpy as np
import torch
from unittest.mock import Mock, patch, MagicMock
from embeddings.embedder import ClinicalEmbedder


class TestEmbeddingShape:
    """Test embedding output shape and dimensions."""

    @pytest.fixture
    def embedder(self):
        """Initialize embedder for tests."""
        try:
            embedder = ClinicalEmbedder(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                device="cpu"
            )
            return embedder
        except Exception as e:
            pytest.skip(f"Could not load model: {e}")

    @pytest.mark.unit
    @pytest.mark.embedding
    def test_embedding_dimension(self, embedder):
        """Test that embedding has correct dimension."""
        text = "The patient has hypertension."
        embedding = embedder.get_embedding(text)
        
        assert isinstance(embedding, list), "Embedding should be a list"
        assert len(embedding) == 384, f"Embedding should be 384-dim, got {len(embedding)}"

    @pytest.mark.unit
    @pytest.mark.embedding
    def test_embedding_is_float(self, embedder):
        """Test that embedding values are floats."""
        text = "Patient vital signs are normal."
        embedding = embedder.get_embedding(text)
        
        for value in embedding:
            assert isinstance(value, (float, np.floating)), "Embedding values should be floats"

    @pytest.mark.unit
    @pytest.mark.embedding
    def test_batch_embeddings_shape(self, embedder):
        """Test batch processing of embeddings."""
        texts = [
            "Patient has fever",
            "Blood pressure elevated",
            "Lab results normal",
        ]
        
        embeddings = [embedder.get_embedding(text) for text in texts]
        
        assert len(embeddings) == 3, "Should have 3 embeddings"
        for emb in embeddings:
            assert len(emb) == 384, "Each embedding should be 384-dim"

    @pytest.mark.unit
    @pytest.mark.embedding
    def test_embedding_normalized(self, embedder):
        """Test that embeddings are normalized (L2 norm ≈ 1)."""
        text = "Clinical note about patient condition"
        embedding = embedder.get_embedding(text)
        
        # Calculate L2 norm
        norm = np.linalg.norm(embedding)
        
        # Should be close to 1.0 (with small tolerance)
        assert 0.99 <= norm <= 1.01, f"Embedding should be normalized, norm={norm}"


class TestEmbeddingConsistency:
    """Test consistency of embeddings."""

    @pytest.fixture
    def embedder(self):
        """Initialize embedder for tests."""
        try:
            embedder = ClinicalEmbedder(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                device="cpu"
            )
            return embedder
        except Exception as e:
            pytest.skip(f"Could not load model: {e}")

    @pytest.mark.unit
    @pytest.mark.embedding
    def test_same_input_same_output(self, embedder):
        """Test that same input produces same output."""
        text = "The patient presents with symptoms of influenza."
        
        embedding1 = embedder.get_embedding(text)
        embedding2 = embedder.get_embedding(text)
        
        # Should be exactly the same (or very close due to floating point)
        assert np.allclose(embedding1, embedding2, rtol=1e-5), \
            "Same input should produce identical embeddings"

    @pytest.mark.unit
    @pytest.mark.embedding
    def test_similar_texts_similar_embeddings(self, embedder):
        """Test that similar texts produce similar embeddings."""
        text1 = "Patient has high blood pressure"
        text2 = "Patient has elevated blood pressure"
        text3 = "The weather is sunny today"  # Dissimilar
        
        emb1 = np.array(embedder.get_embedding(text1))
        emb2 = np.array(embedder.get_embedding(text2))
        emb3 = np.array(embedder.get_embedding(text3))
        
        # Cosine similarity
        similarity_similar = np.dot(emb1, emb2)
        similarity_dissimilar = np.dot(emb1, emb3)
        
        # Similar texts should have higher similarity
        assert similarity_similar > similarity_dissimilar, \
            "Similar texts should have higher cosine similarity"

    @pytest.mark.unit
    @pytest.mark.embedding
    def test_embedding_with_different_cases(self, embedder):
        """Test that case doesn't significantly affect embeddings."""
        text_lower = "patient has hypertension"
        text_upper = "PATIENT HAS HYPERTENSION"
        
        emb_lower = np.array(embedder.get_embedding(text_lower))
        emb_upper = np.array(embedder.get_embedding(text_upper))
        
        # Should be reasonably similar (not exact due to tokenization)
        similarity = np.dot(emb_lower, emb_upper)
        assert similarity > 0.9, "Case variation should not significantly affect embedding"

    @pytest.mark.unit
    @pytest.mark.embedding
    def test_different_texts_different_embeddings(self, embedder):
        """Test that different texts produce different embeddings."""
        text1 = "Patient has hypertension"
        text2 = "Patient has diabetes"
        
        emb1 = np.array(embedder.get_embedding(text1))
        emb2 = np.array(embedder.get_embedding(text2))
        
        # Should be different
        assert not np.allclose(emb1, emb2, rtol=0.1), \
            "Different texts should produce different embeddings"


class TestNumericalStability:
    """Test numerical stability of embeddings."""

    @pytest.fixture
    def embedder(self):
        """Initialize embedder for tests."""
        try:
            embedder = ClinicalEmbedder(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                device="cpu"
            )
            return embedder
        except Exception as e:
            pytest.skip(f"Could not load model: {e}")

    @pytest.mark.unit
    @pytest.mark.embedding
    def test_no_nan_values(self, embedder):
        """Test that embeddings don't contain NaN values."""
        text = "Patient with multiple conditions and symptoms"
        embedding = embedder.get_embedding(text)
        
        assert not np.any(np.isnan(embedding)), "Embedding should not contain NaN values"

    @pytest.mark.unit
    @pytest.mark.embedding
    def test_no_inf_values(self, embedder):
        """Test that embeddings don't contain Inf values."""
        text = "Clinical observation and assessment"
        embedding = embedder.get_embedding(text)
        
        assert not np.any(np.isinf(embedding)), "Embedding should not contain Inf values"

    @pytest.mark.unit
    @pytest.mark.embedding
    def test_numeric_range(self, embedder):
        """Test that embedding values are in reasonable range."""
        text = "Patient assessment and evaluation"
        embedding = embedder.get_embedding(text)
        
        # Normalized vectors should be in [-1, 1]
        assert np.all(np.array(embedding) >= -1.5), "Values should not be too negative"
        assert np.all(np.array(embedding) <= 1.5), "Values should not be too positive"

    @pytest.mark.unit
    @pytest.mark.embedding
    def test_very_long_text_stability(self, embedder):
        """Test stability with very long text."""
        # Create very long text
        text = "Patient health status and medical history. " * 100
        
        embedding = embedder.get_embedding(text)
        
        assert len(embedding) == 384, "Should still produce 384-dim embedding"
        assert not np.any(np.isnan(embedding)), "No NaN values in long text"
        assert not np.any(np.isinf(embedding)), "No Inf values in long text"

    @pytest.mark.unit
    @pytest.mark.embedding
    def test_repeated_embeddings_stability(self, embedder):
        """Test stability when generating multiple embeddings."""
        text = "Standard patient clinical note"
        embeddings = [embedder.get_embedding(text) for _ in range(10)]
        
        # All should be identical
        for i in range(1, len(embeddings)):
            assert np.allclose(embeddings[0], embeddings[i], rtol=1e-5), \
                "Repeated embeddings should be identical"


class TestEdgeCases:
    """Test edge cases in embedding generation."""

    @pytest.fixture
    def embedder(self):
        """Initialize embedder for tests."""
        try:
            embedder = ClinicalEmbedder(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                device="cpu"
            )
            return embedder
        except Exception as e:
            pytest.skip(f"Could not load model: {e}")

    @pytest.mark.unit
    @pytest.mark.embedding
    def test_empty_text(self, embedder):
        """Test embedding of empty text."""
        embedding = embedder.get_embedding("")
        
        # Should return zero vector or handle gracefully
        assert len(embedding) == 384, "Should still return 384-dim"
        assert not np.any(np.isnan(embedding)), "Should not have NaN"

    @pytest.mark.unit
    @pytest.mark.embedding
    def test_whitespace_only(self, embedder):
        """Test embedding of whitespace-only text."""
        embedding = embedder.get_embedding("   \n\t  ")
        
        assert len(embedding) == 384, "Should handle whitespace"

    @pytest.mark.unit
    @pytest.mark.embedding
    def test_single_character(self, embedder):
        """Test embedding of single character."""
        embedding = embedder.get_embedding("a")
        
        assert len(embedding) == 384, "Should handle single character"
        assert not np.any(np.isnan(embedding)), "Should not have NaN"

    @pytest.mark.unit
    @pytest.mark.embedding
    def test_special_characters(self, embedder):
        """Test embedding with special characters."""
        text = "!@#$%^&*()[]{}|;:,.<>?/~`"
        embedding = embedder.get_embedding(text)
        
        assert len(embedding) == 384, "Should handle special characters"
        assert not np.any(np.isnan(embedding)), "Should not have NaN"

    @pytest.mark.unit
    @pytest.mark.embedding
    def test_unicode_characters(self, embedder):
        """Test embedding with unicode characters."""
        text = "患者 مريض пациент 환자 ผู้ป่วย"
        embedding = embedder.get_embedding(text)
        
        assert len(embedding) == 384, "Should handle unicode"
        assert not np.any(np.isnan(embedding)), "Should not have NaN"

    @pytest.mark.unit
    @pytest.mark.embedding
    def test_very_long_text_truncation(self, embedder):
        """Test that very long text is handled (truncated)."""
        # Create text longer than max_length
        text = "Clinical note. " * 100
        embedding = embedder.get_embedding(text)
        
        assert len(embedding) == 384, "Should handle truncation"

    @pytest.mark.unit
    @pytest.mark.embedding
    def test_numbers_only(self, embedder):
        """Test embedding of numbers-only text."""
        text = "123 456 789 101112"
        embedding = embedder.get_embedding(text)
        
        assert len(embedding) == 384, "Should handle numbers"
        assert not np.any(np.isnan(embedding)), "Should not have NaN"


class TestEmbeddingPerformance:
    """Test performance characteristics of embedding generation."""

    @pytest.fixture
    def embedder(self):
        """Initialize embedder for tests."""
        try:
            embedder = ClinicalEmbedder(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                device="cpu"
            )
            return embedder
        except Exception as e:
            pytest.skip(f"Could not load model: {e}")

    @pytest.mark.unit
    @pytest.mark.embedding
    def test_embedding_speed(self, embedder):
        """Test that embedding generation is reasonably fast."""
        import time
        
        text = "Patient with hypertension and elevated blood pressure"
        
        start = time.time()
        embedding = embedder.get_embedding(text)
        elapsed = time.time() - start
        
        # Should complete in reasonable time (< 1 second on CPU)
        assert elapsed < 1.0, f"Embedding too slow: {elapsed:.2f}s"

    @pytest.mark.unit
    @pytest.mark.embedding
    def test_batch_embedding_efficiency(self, embedder):
        """Test efficiency of batch embeddings."""
        import time
        
        texts = ["Patient condition " + str(i) for i in range(5)]
        
        start = time.time()
        embeddings = [embedder.get_embedding(text) for text in texts]
        elapsed = time.time() - start
        
        # Should complete in reasonable time
        assert elapsed < 5.0, "Batch embedding too slow"
        assert len(embeddings) == 5, "Should produce 5 embeddings"


class TestEmbeddingIntegration:
    """Integration tests for embedding pipeline."""

    @pytest.fixture
    def embedder(self):
        """Initialize embedder for tests."""
        try:
            embedder = ClinicalEmbedder(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                device="cpu"
            )
            return embedder
        except Exception as e:
            pytest.skip(f"Could not load model: {e}")

    @pytest.mark.unit
    @pytest.mark.embedding
    def test_embedding_test_cases(self, embedder, embedding_test_cases):
        """Test all embedding test cases."""
        for case in embedding_test_cases:
            text = case["text"]
            description = case["description"]
            
            embedding = embedder.get_embedding(text)
            
            # Verify shape and numerical stability
            assert len(embedding) == 384, f"Failed for {description}"
            assert not np.any(np.isnan(embedding)), f"NaN in {description}"
            assert not np.any(np.isinf(embedding)), f"Inf in {description}"

    @pytest.mark.unit
    @pytest.mark.embedding
    def test_clinical_notes_embedding(self, embedder):
        """Test embedding realistic clinical notes."""
        notes = [
            "Patient presents with acute respiratory infection. Temperature 101F.",
            "Cardiovascular exam: regular rate and rhythm, no murmurs.",
            "Lab results: WBC 7.2, RBC 4.8, HGB 14.2",
        ]
        
        embeddings = [embedder.get_embedding(note) for note in notes]
        
        for emb in embeddings:
            assert len(emb) == 384
            assert not np.any(np.isnan(emb))
            assert not np.any(np.isinf(emb))
