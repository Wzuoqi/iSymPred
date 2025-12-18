#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Unit tests for metagenomic predictor.
"""

import pytest
import pandas as pd
from pathlib import Path

from i_sym_pred.predictors import MetaPredictor


class TestMetaPredictor:
    """Test cases for MetaPredictor."""

    def test_predictor_initialization_sequence_mode(self):
        """Test predictor initialization in sequence mode."""
        predictor = MetaPredictor(db_path="data/gene_db", mode="sequence")
        assert predictor.db_path == Path("data/gene_db")
        assert predictor.mode == "sequence"
        assert predictor.threads == 4
        assert predictor.evalue == 1e-5

    def test_predictor_initialization_id_mode(self):
        """Test predictor initialization in ID mode."""
        predictor = MetaPredictor(db_path="data/gene_db", mode="id")
        assert predictor.mode == "id"

    def test_predictor_custom_parameters(self):
        """Test predictor initialization with custom parameters."""
        predictor = MetaPredictor(
            db_path="data/gene_db",
            mode="sequence",
            threads=8,
            evalue=1e-10,
        )
        assert predictor.threads == 8
        assert predictor.evalue == 1e-10

    def test_load_model_file_not_found(self):
        """Test load_model raises error when database file not found."""
        predictor = MetaPredictor(db_path="nonexistent_path")
        with pytest.raises(FileNotFoundError):
            predictor.load_model()

    def test_predict_without_model(self):
        """Test predict raises error when model not loaded."""
        predictor = MetaPredictor(db_path="data/gene_db")
        with pytest.raises(RuntimeError):
            predictor.predict("input.fasta")

    def test_predict_invalid_mode(self):
        """Test predict raises error with invalid mode."""
        predictor = MetaPredictor(db_path="data/gene_db", mode="invalid")
        predictor.model = pd.DataFrame()  # Mock loaded model

        with pytest.raises(ValueError):
            predictor.predict("input.fasta")

    def test_validate_input_sequence_mode(self):
        """Test input validation for sequence mode."""
        predictor = MetaPredictor(db_path="data/gene_db", mode="sequence")

        # Valid FASTA file path (mock)
        assert predictor.validate_input("test.fasta") is False  # File doesn't exist

    def test_validate_input_id_mode(self):
        """Test input validation for ID mode."""
        predictor = MetaPredictor(db_path="data/gene_db", mode="id")

        # Valid DataFrame
        valid_df = pd.DataFrame({"GeneID": ["gene1", "gene2"]})
        assert predictor.validate_input(valid_df) is True

        # Invalid DataFrame (missing GeneID column)
        invalid_df = pd.DataFrame({"Gene": ["gene1"]})
        assert predictor.validate_input(invalid_df) is False

    def test_run_diamond_without_index(self):
        """Test run_diamond raises error when index not loaded."""
        predictor = MetaPredictor(db_path="data/gene_db", mode="sequence")
        with pytest.raises(RuntimeError):
            predictor.run_diamond("query.fasta", "output.txt")

    def test_get_model_info(self):
        """Test get_model_info returns correct information."""
        predictor = MetaPredictor(
            db_path="data/gene_db",
            mode="sequence",
            threads=8,
        )
        info = predictor.get_model_info()

        assert "db_path" in info
        assert "config" in info
        assert "model_loaded" in info
        assert info["model_loaded"] is False


# Integration tests (require actual database)
class TestMetaPredictorIntegration:
    """Integration tests for MetaPredictor (require database)."""

    @pytest.fixture
    def sample_gene_db(self, tmp_path):
        """Create a sample gene database for testing."""
        db_dir = tmp_path / "gene_db"
        db_dir.mkdir()

        # Create sample gene mapping file
        data = {
            "GeneID": ["gene001", "gene002", "gene003"],
            "GeneName": ["nifH", "amoA", "mcrA"],
            "Function": ["Nitrogen fixation", "Ammonia oxidation", "Methanogenesis"],
            "Pathway": ["Nitrogen metabolism", "Nitrogen metabolism", "Methane metabolism"],
            "Description": [
                "Nitrogenase iron protein",
                "Ammonia monooxygenase subunit A",
                "Methyl-coenzyme M reductase alpha subunit",
            ],
        }
        df = pd.DataFrame(data)
        df.to_csv(db_dir / "gene_function_mapping.tsv", sep="\t", index=False)

        return db_dir

    def test_load_model_success(self, sample_gene_db):
        """Test successful model loading."""
        predictor = MetaPredictor(db_path=str(sample_gene_db), mode="id")
        predictor.load_model()

        assert predictor.model is not None
        assert len(predictor.gene_mapping) == 3

    def test_predict_id_mode(self, sample_gene_db):
        """Test prediction in ID mode."""
        predictor = MetaPredictor(db_path=str(sample_gene_db), mode="id")
        predictor.load_model()

        # Create sample input
        input_df = pd.DataFrame({
            "GeneID": ["gene001", "gene002"],
            "Abundance": [100, 50],
        })

        result = predictor.predict(input_df)

        assert "predictions" in result
        assert "metadata" in result
        assert "statistics" in result
        assert result["metadata"]["mode"] == "id"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
