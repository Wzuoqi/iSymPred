#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configuration management for iSymPred.
"""

import os
from pathlib import Path


class Config:
    """Global configuration for iSymPred."""

    # Project root directory
    PROJECT_ROOT = Path(__file__).parent.parent

    # Data directories
    ASSETS_DIR = PROJECT_ROOT / "assets"
    DATA_DIR = PROJECT_ROOT / "data"
    TAXONOMY_DB_DIR = DATA_DIR / "taxonomy_db"
    GENE_DB_DIR = DATA_DIR / "gene_db"
    ONTOLOGY_DIR = DATA_DIR / "ontology"

    # Database file names
    TAXONOMY_MAPPING_FILE = "taxonomy_function_mapping.tsv"
    GENE_MAPPING_FILE = "gene_function_mapping.tsv"
    DIAMOND_INDEX_FILE = "gene_reference.dmnd"
    ONTOLOGY_TREE_FILE = "function_hierarchy.json"

    # DIAMOND parameters
    DIAMOND_EVALUE_DEFAULT = 1e-5
    DIAMOND_THREADS_DEFAULT = 4
    DIAMOND_MAX_TARGET_SEQS = 1

    # Taxonomy levels
    TAXONOMY_LEVELS = [
        "Kingdom",
        "Phylum",
        "Class",
        "Order",
        "Family",
        "Genus",
        "Species",
    ]

    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist."""
        for directory in [
            cls.ASSETS_DIR,
            cls.DATA_DIR,
            cls.TAXONOMY_DB_DIR,
            cls.GENE_DB_DIR,
            cls.ONTOLOGY_DIR,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_taxonomy_db_path(cls):
        """Get full path to taxonomy mapping file."""
        return cls.TAXONOMY_DB_DIR / cls.TAXONOMY_MAPPING_FILE

    @classmethod
    def get_gene_db_path(cls):
        """Get full path to gene mapping file."""
        return cls.GENE_DB_DIR / cls.GENE_MAPPING_FILE

    @classmethod
    def get_diamond_index_path(cls):
        """Get full path to DIAMOND index file."""
        return cls.GENE_DB_DIR / cls.DIAMOND_INDEX_FILE

    @classmethod
    def get_ontology_path(cls):
        """Get full path to ontology tree file."""
        return cls.ONTOLOGY_DIR / cls.ONTOLOGY_TREE_FILE
