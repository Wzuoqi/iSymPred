#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
16S rRNA-based predictor for iSymPred.

This module implements functional prediction based on 16S amplicon data
using taxonomy-to-function mapping.

Key Features:
- Supports dual-condition querying: bacterial genus + insect host name
- Enables context-aware prediction considering host-symbiont relationships
- Falls back to genus-only prediction when host context is not available
- Handles various input formats: OTU tables (BIOM/TSV), taxonomy assignments

Implementation Notes:
- The predictor queries the taxonomy database using genus-level classification
- When host name is provided, it prioritizes host-specific functional annotations
- For generalist symbionts, it returns general functional predictions
- Supports hierarchical taxonomy matching (genus -> family -> order if needed)
"""

from typing import Dict, Any, Optional, List
import pandas as pd
from pathlib import Path

from .base import BasePredictor
from ..config import Config


class S16Predictor(BasePredictor):
    """
    Predictor for 16S amplicon data.

    Uses taxonomy-to-function mapping with optional insect host context
    to predict functional profiles of microbial communities.
    """

    def __init__(self, db_path: str, host: Optional[str] = None, **kwargs):
        """
        Initialize 16S predictor.

        Args:
            db_path: Path to taxonomy database directory
            host: Insect host name for context-aware prediction (optional)
            **kwargs: Additional parameters
        """
        super().__init__(db_path, **kwargs)
        self.host = host
        self.taxonomy_mapping = None

    def load_model(self) -> None:
        """
        Load taxonomy-to-function mapping database.

        Expected database format (TSV):
        - Columns: Genus, Host, Function, Confidence, Evidence
        - Genus: Bacterial genus name
        - Host: Insect host name (or "General" for non-specific)
        - Function: Functional annotation
        - Confidence: Confidence score (0-1)
        - Evidence: Evidence type (experimental, predicted, etc.)

        Raises:
            FileNotFoundError: If taxonomy mapping file not found
            ValueError: If database format is invalid
        """
        mapping_file = self.db_path / Config.TAXONOMY_MAPPING_FILE

        if not mapping_file.exists():
            raise FileNotFoundError(
                f"Taxonomy mapping file not found: {mapping_file}\n"
                f"Please run 'isympred build-db' first to create the database."
            )

        try:
            self.taxonomy_mapping = pd.read_csv(mapping_file, sep="\t")
            required_columns = ["Genus", "Host", "Function"]
            missing_columns = set(required_columns) - set(self.taxonomy_mapping.columns)

            if missing_columns:
                raise ValueError(
                    f"Missing required columns in taxonomy database: {missing_columns}"
                )

            self.model = self.taxonomy_mapping
            print(f"Loaded taxonomy database: {len(self.taxonomy_mapping)} entries")

        except Exception as e:
            raise ValueError(f"Failed to load taxonomy database: {e}")

    def predict(
        self, input_data: Any, output_format: str = "table", **kwargs
    ) -> Dict[str, Any]:
        """
        Predict functions from 16S taxonomy data.

        Args:
            input_data: Input taxonomy data (DataFrame or file path)
                Expected columns: OTU_ID, Taxonomy, Abundance (optional)
            output_format: Output format ('table', 'summary', 'detailed')
            **kwargs: Additional parameters

        Returns:
            Dictionary containing:
            - predictions: DataFrame with functional predictions
            - metadata: Prediction metadata (host, database info)
            - statistics: Summary statistics

        Raises:
            ValueError: If input format is invalid
            RuntimeError: If prediction fails
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # TODO: Implement prediction logic
        # 1. Parse input taxonomy data
        # 2. Extract genus-level classification
        # 3. Query database with genus + host (if provided)
        # 4. Aggregate functional predictions
        # 5. Calculate abundance-weighted functional profiles

        predictions = pd.DataFrame()  # Placeholder

        return {
            "predictions": predictions,
            "metadata": {
                "host": self.host,
                "db_path": str(self.db_path),
                "prediction_mode": "host-specific" if self.host else "general",
            },
            "statistics": {
                "total_otus": 0,
                "mapped_otus": 0,
                "unmapped_otus": 0,
                "unique_functions": 0,
            },
        }

    def query_by_genus(
        self, genus: str, host: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query functions for a specific genus with optional host context.

        Args:
            genus: Bacterial genus name
            host: Insect host name (optional, uses self.host if not provided)

        Returns:
            List of functional annotations with metadata
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        host = host or self.host
        results = []

        # Query with host context if available
        if host:
            host_specific = self.taxonomy_mapping[
                (self.taxonomy_mapping["Genus"] == genus)
                & (self.taxonomy_mapping["Host"] == host)
            ]
            results.extend(host_specific.to_dict("records"))

        # Fall back to general predictions
        general = self.taxonomy_mapping[
            (self.taxonomy_mapping["Genus"] == genus)
            & (self.taxonomy_mapping["Host"] == "General")
        ]
        results.extend(general.to_dict("records"))

        return results

    def validate_input(self, input_data: Any) -> bool:
        """
        Validate input taxonomy data format.

        Args:
            input_data: Input data to validate

        Returns:
            True if valid, False otherwise
        """
        if isinstance(input_data, pd.DataFrame):
            required_columns = ["Taxonomy"]
            return all(col in input_data.columns for col in required_columns)

        return super().validate_input(input_data)
