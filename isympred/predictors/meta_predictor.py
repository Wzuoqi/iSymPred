#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Metagenomic predictor for iSymPred.

This module implements functional prediction based on metagenomic data
using gene sequence alignment or direct gene ID mapping.

Key Features:
- Supports two prediction modes:
  1. Sequence mode: Uses DIAMOND for fast protein sequence alignment
  2. ID mode: Direct gene name/ID to function mapping
- Handles various input formats: FASTA (sequences), TSV (gene IDs)
- Provides abundance-weighted functional profiles

Implementation Notes:
- Sequence mode workflow:
  1. Run DIAMOND blastp against reference gene database
  2. Parse alignment results (best hit or top N hits)
  3. Map aligned genes to functional annotations
  4. Aggregate results by function categories

- ID mode workflow:
  1. Parse input gene IDs (e.g., from gene abundance tables)
  2. Direct lookup in gene-to-function mapping table
  3. Calculate functional profiles based on gene abundances

- The predictor supports hierarchical functional annotations
  (e.g., KEGG pathways, COG categories, custom ontologies)
"""

from typing import Dict, Any, Optional, List
import pandas as pd
from pathlib import Path
import subprocess

from .base import BasePredictor
from ..config import Config


class MetaPredictor(BasePredictor):
    """
    Predictor for metagenomic data.

    Uses gene sequence alignment (DIAMOND) or direct gene ID mapping
    to predict functional profiles from metagenomic datasets.
    """

    def __init__(
        self,
        db_path: str,
        mode: str = "sequence",
        threads: int = 4,
        evalue: float = 1e-5,
        **kwargs,
    ):
        """
        Initialize metagenomic predictor.

        Args:
            db_path: Path to gene database directory
            mode: Prediction mode ('sequence' or 'id')
            threads: Number of threads for DIAMOND (sequence mode only)
            evalue: E-value threshold for DIAMOND (sequence mode only)
            **kwargs: Additional parameters
        """
        super().__init__(db_path, **kwargs)
        self.mode = mode
        self.threads = threads
        self.evalue = evalue
        self.gene_mapping = None
        self.diamond_index = None

    def load_model(self) -> None:
        """
        Load gene-to-function mapping database and DIAMOND index.

        Expected database files:
        1. Gene mapping file (TSV):
           - Columns: GeneID, GeneName, Function, Pathway, Description
        2. DIAMOND index file (.dmnd):
           - Pre-built DIAMOND database for sequence alignment

        Raises:
            FileNotFoundError: If required database files not found
            ValueError: If database format is invalid
        """
        # Load gene mapping table
        mapping_file = self.db_path / Config.GENE_MAPPING_FILE

        if not mapping_file.exists():
            raise FileNotFoundError(
                f"Gene mapping file not found: {mapping_file}\n"
                f"Please run 'isympred build-db' first to create the database."
            )

        try:
            self.gene_mapping = pd.read_csv(mapping_file, sep="\t")
            required_columns = ["GeneID", "Function"]
            missing_columns = set(required_columns) - set(self.gene_mapping.columns)

            if missing_columns:
                raise ValueError(
                    f"Missing required columns in gene database: {missing_columns}"
                )

            print(f"Loaded gene mapping database: {len(self.gene_mapping)} entries")

        except Exception as e:
            raise ValueError(f"Failed to load gene mapping database: {e}")

        # Load DIAMOND index (sequence mode only)
        if self.mode == "sequence":
            diamond_index = self.db_path / Config.DIAMOND_INDEX_FILE

            if not diamond_index.exists():
                raise FileNotFoundError(
                    f"DIAMOND index not found: {diamond_index}\n"
                    f"Please run 'isympred build-db' to create the DIAMOND index."
                )

            self.diamond_index = diamond_index
            print(f"DIAMOND index loaded: {diamond_index}")

        self.model = self.gene_mapping

    def predict(
        self, input_data: Any, output_format: str = "table", **kwargs
    ) -> Dict[str, Any]:
        """
        Predict functions from metagenomic data.

        Args:
            input_data: Input data (FASTA file path for sequence mode,
                       DataFrame or TSV path for ID mode)
            output_format: Output format ('table', 'summary', 'detailed')
            **kwargs: Additional parameters

        Returns:
            Dictionary containing:
            - predictions: DataFrame with functional predictions
            - metadata: Prediction metadata (mode, parameters)
            - statistics: Summary statistics

        Raises:
            ValueError: If input format is invalid
            RuntimeError: If prediction fails
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        if self.mode == "sequence":
            return self._predict_by_sequence(input_data, output_format, **kwargs)
        elif self.mode == "id":
            return self._predict_by_id(input_data, output_format, **kwargs)
        else:
            raise ValueError(f"Invalid prediction mode: {self.mode}")

    def _predict_by_sequence(
        self, fasta_file: str, output_format: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Predict functions using DIAMOND sequence alignment.

        Args:
            fasta_file: Path to input FASTA file
            output_format: Output format
            **kwargs: Additional parameters

        Returns:
            Prediction results dictionary
        """
        # TODO: Implement DIAMOND-based prediction
        # 1. Run DIAMOND blastp against reference database
        # 2. Parse alignment results
        # 3. Map aligned genes to functions
        # 4. Aggregate functional profiles

        predictions = pd.DataFrame()  # Placeholder

        return {
            "predictions": predictions,
            "metadata": {
                "mode": "sequence",
                "db_path": str(self.db_path),
                "diamond_params": {
                    "threads": self.threads,
                    "evalue": self.evalue,
                },
            },
            "statistics": {
                "total_sequences": 0,
                "aligned_sequences": 0,
                "unaligned_sequences": 0,
                "unique_functions": 0,
            },
        }

    def _predict_by_id(
        self, input_data: Any, output_format: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Predict functions using direct gene ID mapping.

        Args:
            input_data: Input gene IDs (DataFrame or file path)
            output_format: Output format
            **kwargs: Additional parameters

        Returns:
            Prediction results dictionary
        """
        # TODO: Implement ID-based prediction
        # 1. Parse input gene IDs and abundances
        # 2. Query gene mapping database
        # 3. Calculate abundance-weighted functional profiles

        predictions = pd.DataFrame()  # Placeholder

        return {
            "predictions": predictions,
            "metadata": {
                "mode": "id",
                "db_path": str(self.db_path),
            },
            "statistics": {
                "total_genes": 0,
                "mapped_genes": 0,
                "unmapped_genes": 0,
                "unique_functions": 0,
            },
        }

    def run_diamond(
        self, query_file: str, output_file: str, **kwargs
    ) -> subprocess.CompletedProcess:
        """
        Run DIAMOND blastp alignment.

        Args:
            query_file: Path to query FASTA file
            output_file: Path to output alignment file
            **kwargs: Additional DIAMOND parameters

        Returns:
            CompletedProcess object from subprocess

        Raises:
            RuntimeError: If DIAMOND execution fails
        """
        if self.diamond_index is None:
            raise RuntimeError("DIAMOND index not loaded.")

        cmd = [
            "diamond",
            "blastp",
            "--db",
            str(self.diamond_index),
            "--query",
            query_file,
            "--out",
            output_file,
            "--threads",
            str(self.threads),
            "--evalue",
            str(self.evalue),
            "--outfmt",
            "6",  # Tabular format
            "--max-target-seqs",
            str(Config.DIAMOND_MAX_TARGET_SEQS),
        ]

        # Add additional parameters
        for key, value in kwargs.items():
            cmd.extend([f"--{key}", str(value)])

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return result
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"DIAMOND execution failed: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError(
                "DIAMOND not found. Please install DIAMOND and ensure it's in your PATH."
            )

    def validate_input(self, input_data: Any) -> bool:
        """
        Validate input data format based on prediction mode.

        Args:
            input_data: Input data to validate

        Returns:
            True if valid, False otherwise
        """
        if self.mode == "sequence":
            # Check if it's a valid FASTA file path
            if isinstance(input_data, (str, Path)):
                path = Path(input_data)
                return path.exists() and path.suffix in [".fasta", ".fa", ".faa"]

        elif self.mode == "id":
            # Check if it's a DataFrame with required columns
            if isinstance(input_data, pd.DataFrame):
                return "GeneID" in input_data.columns

        return super().validate_input(input_data)
