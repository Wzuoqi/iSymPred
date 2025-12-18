#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Taxonomy name cleaning and standardization utilities for iSymPred.

Handles various taxonomy string formats and standardizes them
for consistent database queries.
"""

import re
from typing import Dict, List, Optional, Tuple


class TaxonomyCleaner:
    """
    Utility class for cleaning and standardizing taxonomy names.
    """

    # Common taxonomy prefixes used in different formats
    TAXONOMY_PREFIXES = {
        "k": "Kingdom",
        "p": "Phylum",
        "c": "Class",
        "o": "Order",
        "f": "Family",
        "g": "Genus",
        "s": "Species",
    }

    def __init__(self):
        """Initialize taxonomy cleaner."""
        self.cache = {}

    def parse_taxonomy_string(self, taxonomy_str: str) -> Dict[str, str]:
        """
        Parse taxonomy string into structured dictionary.

        Supports multiple formats:
        - Greengenes: k__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;...
        - SILVA: Bacteria;Proteobacteria;Gammaproteobacteria;...
        - NCBI: cellular organisms;Bacteria;Proteobacteria;...

        Args:
            taxonomy_str: Taxonomy string to parse

        Returns:
            Dictionary mapping taxonomy levels to names
        """
        if taxonomy_str in self.cache:
            return self.cache[taxonomy_str]

        taxonomy = {}

        # Handle Greengenes format (k__Bacteria;p__Proteobacteria;...)
        if "__" in taxonomy_str:
            parts = taxonomy_str.split(";")
            for part in parts:
                part = part.strip()
                if "__" in part:
                    prefix, name = part.split("__", 1)
                    level = self.TAXONOMY_PREFIXES.get(prefix.lower())
                    if level and name:
                        taxonomy[level] = self.clean_name(name)

        # Handle simple semicolon-separated format
        else:
            parts = [p.strip() for p in taxonomy_str.split(";")]
            levels = ["Kingdom", "Phylum", "Class", "Order", "Family", "Genus", "Species"]

            for i, part in enumerate(parts):
                if i < len(levels) and part:
                    taxonomy[levels[i]] = self.clean_name(part)

        self.cache[taxonomy_str] = taxonomy
        return taxonomy

    def extract_genus(self, taxonomy_str: str) -> Optional[str]:
        """
        Extract genus name from taxonomy string.

        Args:
            taxonomy_str: Taxonomy string

        Returns:
            Genus name or None if not found
        """
        taxonomy = self.parse_taxonomy_string(taxonomy_str)
        return taxonomy.get("Genus")

    def extract_species(self, taxonomy_str: str) -> Optional[str]:
        """
        Extract species name from taxonomy string.

        Args:
            taxonomy_str: Taxonomy string

        Returns:
            Species name or None if not found
        """
        taxonomy = self.parse_taxonomy_string(taxonomy_str)
        return taxonomy.get("Species")

    def clean_name(self, name: str) -> str:
        """
        Clean and standardize a taxonomy name.

        Removes:
        - Leading/trailing whitespace
        - Special characters (except hyphens and underscores)
        - Uncultured/unclassified prefixes
        - Strain/isolate suffixes

        Args:
            name: Taxonomy name to clean

        Returns:
            Cleaned name
        """
        if not name:
            return ""

        # Remove leading/trailing whitespace
        name = name.strip()

        # Remove common prefixes
        prefixes_to_remove = [
            "uncultured",
            "unclassified",
            "unidentified",
            "unknown",
            "environmental",
            "bacterium",
            "organism",
        ]

        name_lower = name.lower()
        for prefix in prefixes_to_remove:
            if name_lower.startswith(prefix):
                name = name[len(prefix):].strip()
                name_lower = name.lower()

        # Remove strain/isolate information (e.g., "Genus sp. strain ABC")
        name = re.sub(r"\s+(strain|isolate|sp\.|spp\.).*$", "", name, flags=re.IGNORECASE)

        # Remove special characters except hyphens and underscores
        name = re.sub(r"[^\w\s\-]", "", name)

        # Normalize whitespace
        name = " ".join(name.split())

        # Capitalize first letter
        if name:
            name = name[0].upper() + name[1:]

        return name

    def standardize_host_name(self, host_name: str) -> str:
        """
        Standardize insect host name.

        Args:
            host_name: Host name to standardize

        Returns:
            Standardized host name
        """
        if not host_name:
            return "General"

        # Clean the name
        host_name = host_name.strip()

        # Common host name mappings
        host_mappings = {
            "drosophila": "Drosophila",
            "fruit fly": "Drosophila",
            "aphid": "Aphid",
            "bee": "Bee",
            "honeybee": "Honeybee",
            "termite": "Termite",
            "ant": "Ant",
            "mosquito": "Mosquito",
            "beetle": "Beetle",
            "cockroach": "Cockroach",
        }

        host_lower = host_name.lower()
        for key, value in host_mappings.items():
            if key in host_lower:
                return value

        # Capitalize first letter of each word
        return " ".join(word.capitalize() for word in host_name.split())

    def is_valid_taxonomy(self, taxonomy_str: str) -> bool:
        """
        Check if taxonomy string is valid and parseable.

        Args:
            taxonomy_str: Taxonomy string to validate

        Returns:
            True if valid, False otherwise
        """
        if not taxonomy_str or not isinstance(taxonomy_str, str):
            return False

        taxonomy = self.parse_taxonomy_string(taxonomy_str)
        return len(taxonomy) > 0

    def get_taxonomy_level(self, taxonomy_str: str, level: str) -> Optional[str]:
        """
        Get specific taxonomy level from taxonomy string.

        Args:
            taxonomy_str: Taxonomy string
            level: Taxonomy level (Kingdom, Phylum, Class, Order, Family, Genus, Species)

        Returns:
            Taxonomy name at specified level or None if not found
        """
        taxonomy = self.parse_taxonomy_string(taxonomy_str)
        return taxonomy.get(level)

    def format_taxonomy(self, taxonomy_dict: Dict[str, str], format_type: str = "greengenes") -> str:
        """
        Format taxonomy dictionary into string.

        Args:
            taxonomy_dict: Dictionary mapping levels to names
            format_type: Output format ('greengenes', 'silva', 'simple')

        Returns:
            Formatted taxonomy string
        """
        levels = ["Kingdom", "Phylum", "Class", "Order", "Family", "Genus", "Species"]

        if format_type == "greengenes":
            parts = []
            prefix_map = {v: k for k, v in self.TAXONOMY_PREFIXES.items()}
            for level in levels:
                if level in taxonomy_dict:
                    prefix = prefix_map.get(level, level[0].lower())
                    parts.append(f"{prefix}__{taxonomy_dict[level]}")
            return ";".join(parts)

        elif format_type in ["silva", "simple"]:
            parts = [taxonomy_dict.get(level, "") for level in levels]
            return ";".join(p for p in parts if p)

        else:
            raise ValueError(f"Unsupported format type: {format_type}")

    def clear_cache(self) -> None:
        """Clear the taxonomy parsing cache."""
        self.cache.clear()
