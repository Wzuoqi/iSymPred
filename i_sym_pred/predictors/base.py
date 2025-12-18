#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Base predictor abstract class for iSymPred.

All predictor implementations should inherit from BasePredictor
and implement the required abstract methods.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional


class BasePredictor(ABC):
    """
    Abstract base class for all predictors in iSymPred.

    This class defines the interface that all predictor implementations
    must follow, ensuring consistency across different prediction methods.
    """

    def __init__(self, db_path: str, **kwargs):
        """
        Initialize the predictor.

        Args:
            db_path: Path to the database directory
            **kwargs: Additional predictor-specific parameters
        """
        self.db_path = Path(db_path)
        self.config = kwargs
        self.model = None

    @abstractmethod
    def load_model(self) -> None:
        """
        Load the prediction model/database.

        This method should load all necessary data structures,
        mapping tables, or reference databases required for prediction.

        Raises:
            FileNotFoundError: If required database files are not found
            ValueError: If database format is invalid
        """
        pass

    @abstractmethod
    def predict(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform functional prediction on input data.

        Args:
            input_data: Input data for prediction (format varies by predictor)
            **kwargs: Additional prediction parameters

        Returns:
            Dictionary containing prediction results with the following structure:
            {
                'predictions': [...],  # List of predicted functions
                'metadata': {...},     # Prediction metadata
                'statistics': {...}    # Summary statistics
            }

        Raises:
            ValueError: If input data format is invalid
            RuntimeError: If prediction fails
        """
        pass

    def validate_input(self, input_data: Any) -> bool:
        """
        Validate input data format.

        Args:
            input_data: Input data to validate

        Returns:
            True if input is valid, False otherwise
        """
        # Default implementation - can be overridden by subclasses
        return input_data is not None

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model/database.

        Returns:
            Dictionary containing model metadata
        """
        return {
            "db_path": str(self.db_path),
            "config": self.config,
            "model_loaded": self.model is not None,
        }
