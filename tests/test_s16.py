#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Unit tests for 16S predictor.
"""

import pytest
import pandas as pd
from pathlib import Path

from isympred.predictors import S16Predictor


class TestS16Predictor:
    """Test cases for S16Predictor."""

    def test_predictor_initialization(self):
        """Test predictor initialization."""
        predictor = S16Predictor(db_path="data/taxonomy_db")
        assert predictor.db_path == Path("data/taxonomy_db")
        assert predictor.host is None
        assert predictor.model is None

    def test_predictor_with_host(self):
        """Test predictor initialization with host context."""
        predictor = S16Predictor(db_path="data/taxonomy_db", host="Drosophila")
        assert predictor.host == "Drosophila"

    def test_load_model_file_not_found(self):
        """Test load_model raises error when database file not found."""
        predictor = S16Predictor(db_path="nonexistent_path")
        with pytest.raises(FileNotFoundError):
            predictor.load_model()

    def test_predict_without_model(self):
        """Test predict raises error when model not loaded."""
        predictor = S16Predictor(db_path="data/taxonomy_db")
        with pytest.raises(RuntimeError):
            predictor.predict(pd.DataFrame())

    def test_validate_input_dataframe(self):
        """Test input validation for DataFrame."""
        predictor = S16Predictor(db_path="data/taxonomy_db")

        # Valid input
        valid_df = pd.DataFrame({"Taxonomy": ["k__Bacteria;g__Wolbachia"]})
        assert predictor.validate_input(valid_df) is True

        # Invalid input (missing Taxonomy column)
        invalid_df = pd.DataFrame({"OTU_ID": ["OTU1"]})
        assert predictor.validate_input(invalid_df) is False

    def test_query_by_genus_without_model(self):
        """Test query_by_genus raises error when model not loaded."""
        predictor = S16Predictor(db_path="data/taxonomy_db")
        with pytest.raises(RuntimeError):
            predictor.query_by_genus("Wolbachia")

    def test_get_model_info(self):
        """Test get_model_info returns correct information."""
        predictor = S16Predictor(db_path="data/taxonomy_db", host="Drosophila")
        info = predictor.get_model_info()

        assert "db_path" in info
        assert "config" in info
        assert "model_loaded" in info
        assert info["model_loaded"] is False


# Integration tests (require actual database)
class TestS16PredictorIntegration:
    """Integration tests for S16Predictor (require database)."""

    @pytest.fixture
    def sample_taxonomy_db(self, tmp_path):
        """Create a sample taxonomy database for testing."""
        db_dir = tmp_path / "taxonomy_db"
        db_dir.mkdir()

        # Create sample taxonomy mapping file
        data = {
            "Genus": ["Wolbachia", "Wolbachia", "Buchnera"],
            "Host": ["Drosophila", "General", "Aphid"],
            "Function": ["Reproduction manipulation", "Endosymbiont", "Amino acid synthesis"],
            "Confidence": [0.9, 0.8, 0.95],
            "Evidence": ["experimental", "literature", "experimental"],
        }
        df = pd.DataFrame(data)
        df.to_csv(db_dir / "taxonomy_function_mapping.tsv", sep="\t", index=False)

        return db_dir

    def test_load_model_success(self, sample_taxonomy_db):
        """Test successful model loading."""
        predictor = S16Predictor(db_path=str(sample_taxonomy_db))
        predictor.load_model()

        assert predictor.model is not None
        assert len(predictor.taxonomy_mapping) == 3

    def test_query_by_genus_with_host(self, sample_taxonomy_db):
        """Test querying by genus with host context."""
        predictor = S16Predictor(db_path=str(sample_taxonomy_db), host="Drosophila")
        predictor.load_model()

        results = predictor.query_by_genus("Wolbachia")
        assert len(results) >= 1
        assert any(r["Host"] == "Drosophila" for r in results)

    def test_query_by_genus_without_host(self, sample_taxonomy_db):
        """Test querying by genus without host context."""
        predictor = S16Predictor(db_path=str(sample_taxonomy_db))
        predictor.load_model()

        results = predictor.query_by_genus("Wolbachia")
        assert len(results) >= 1
        assert any(r["Host"] == "General" for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
