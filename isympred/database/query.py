#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Database query module for iSymPred.

This module provides efficient query interfaces for the internal databases.

Key Features:
- Fast taxonomy-to-function lookups
- Gene-to-function mapping queries
- Support for fuzzy matching and hierarchical queries
- Caching for frequently accessed data
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from pathlib import Path

from ..config import Config


class DatabaseQuery:
    """
    Query interface for iSymPred databases.
    """

    def __init__(self, db_dir: str):
        """
        Initialize database query interface.

        Args:
            db_dir: Root directory containing all databases
        """
        self.db_dir = Path(db_dir)
        self.taxonomy_db = None
        self.gene_db = None
        self._cache = {}

    def load_taxonomy_db(self) -> None:
        """
        Load taxonomy database into memory.

        Raises:
            FileNotFoundError: If database file not found
        """
        db_file = self.db_dir / "taxonomy_db" / Config.TAXONOMY_MAPPING_FILE

        if not db_file.exists():
            raise FileNotFoundError(f"Taxonomy database not found: {db_file}")

        self.taxonomy_db = pd.read_csv(db_file, sep="\t")
        print(f"Loaded taxonomy database: {len(self.taxonomy_db)} entries")

    def load_gene_db(self) -> None:
        """
        Load gene database into memory.

        Raises:
            FileNotFoundError: If database file not found
        """
        db_file = self.db_dir / "gene_db" / Config.GENE_MAPPING_FILE

        if not db_file.exists():
            raise FileNotFoundError(f"Gene database not found: {db_file}")

        self.gene_db = pd.read_csv(db_file, sep="\t")
        print(f"Loaded gene database: {len(self.gene_db)} entries")

    def query_taxonomy(
        self,
        genus: str,
        host: Optional[str] = None,
        exact_match: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Query taxonomy database for functional annotations.

        Args:
            genus: Bacterial genus name
            host: Insect host name (optional)
            exact_match: Use exact string matching (default: True)

        Returns:
            List of matching records as dictionaries
        """
        if self.taxonomy_db is None:
            self.load_taxonomy_db()

        # Build query conditions
        if exact_match:
            mask = self.taxonomy_db["Genus"] == genus
        else:
            mask = self.taxonomy_db["Genus"].str.contains(genus, case=False, na=False)

        # Add host filter if provided
        if host:
            mask &= (self.taxonomy_db["Host"] == host) | (
                self.taxonomy_db["Host"] == "General"
            )

        results = self.taxonomy_db[mask].to_dict("records")
        return results

    def query_gene(
        self,
        gene_id: Optional[str] = None,
        gene_name: Optional[str] = None,
        function: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query gene database for functional annotations.

        Args:
            gene_id: Gene ID (exact match)
            gene_name: Gene name (can use partial match)
            function: Function category (partial match)

        Returns:
            List of matching records as dictionaries
        """
        if self.gene_db is None:
            self.load_gene_db()

        mask = pd.Series([True] * len(self.gene_db))

        if gene_id:
            mask &= self.gene_db["GeneID"] == gene_id

        if gene_name:
            mask &= self.gene_db["GeneName"].str.contains(
                gene_name, case=False, na=False
            )

        if function:
            mask &= self.gene_db["Function"].str.contains(
                function, case=False, na=False
            )

        results = self.gene_db[mask].to_dict("records")
        return results

    def get_all_genera(self) -> List[str]:
        """
        Get list of all genera in taxonomy database.

        Returns:
            Sorted list of unique genus names
        """
        if self.taxonomy_db is None:
            self.load_taxonomy_db()

        return sorted(self.taxonomy_db["Genus"].unique().tolist())

    def get_all_hosts(self) -> List[str]:
        """
        Get list of all hosts in taxonomy database.

        Returns:
            Sorted list of unique host names
        """
        if self.taxonomy_db is None:
            self.load_taxonomy_db()

        return sorted(self.taxonomy_db["Host"].unique().tolist())

    def get_all_functions(self, db_type: str = "taxonomy") -> List[str]:
        """
        Get list of all functions in specified database.

        Args:
            db_type: Database type ('taxonomy' or 'gene')

        Returns:
            Sorted list of unique function names
        """
        if db_type == "taxonomy":
            if self.taxonomy_db is None:
                self.load_taxonomy_db()
            return sorted(self.taxonomy_db["Function"].unique().tolist())
        elif db_type == "gene":
            if self.gene_db is None:
                self.load_gene_db()
            return sorted(self.gene_db["Function"].unique().tolist())
        else:
            raise ValueError(f"Invalid db_type: {db_type}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary containing database statistics
        """
        stats = {}

        if self.taxonomy_db is not None:
            stats["taxonomy"] = {
                "total_entries": len(self.taxonomy_db),
                "unique_genera": self.taxonomy_db["Genus"].nunique(),
                "unique_hosts": self.taxonomy_db["Host"].nunique(),
                "unique_functions": self.taxonomy_db["Function"].nunique(),
            }

        if self.gene_db is not None:
            stats["gene"] = {
                "total_entries": len(self.gene_db),
                "unique_genes": self.gene_db["GeneID"].nunique(),
                "unique_functions": self.gene_db["Function"].nunique(),
            }

        return stats

    def clear_cache(self) -> None:
        """Clear query cache."""
        self._cache.clear()
