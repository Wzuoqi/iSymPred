#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Database builder for iSymPred.

This module converts raw reference data (Excel/Fasta files from assets/)
into optimized internal database formats for fast querying.

Key Responsibilities:
1. Parse raw reference data from various formats (Excel, CSV, FASTA)
2. Validate and clean taxonomy names and gene annotations
3. Build taxonomy-to-function mapping tables
4. Build gene-to-function mapping tables
5. Create DIAMOND database index from reference gene sequences
6. Generate functional ontology hierarchy (JSON)
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from pathlib import Path
import subprocess
import json

from ..config import Config
from ..utils.taxonomy import TaxonomyCleaner


class DatabaseBuilder:
    """
    Builder for converting raw reference data into internal databases.
    """

    def __init__(self, input_dir: str, output_dir: str):
        """
        Initialize database builder.

        Args:
            input_dir: Directory containing raw reference data (assets/)
            output_dir: Directory for output databases (data/)
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.taxonomy_cleaner = TaxonomyCleaner()

    def build_all(self) -> None:
        """
        Build all databases (taxonomy, gene, ontology).
        """
        print("Building all databases...")
        self.build_taxonomy_db()
        self.build_gene_db()
        self.build_ontology()
        print("All databases built successfully!")

    def build_taxonomy_db(self) -> None:
        """
        Build taxonomy-to-function mapping database.

        Expected input format (Excel/CSV):
        - Columns: Genus, Host, Function, Confidence, Evidence, Reference
        - Genus: Bacterial genus name
        - Host: Insect host name (or "General")
        - Function: Functional annotation
        - Confidence: Confidence score (0-1)
        - Evidence: Evidence type (experimental, predicted, literature)
        - Reference: Citation or source

        Output:
        - TSV file: data/taxonomy_db/taxonomy_function_mapping.tsv
        """
        print("Building taxonomy database...")

        # TODO: Implement taxonomy database building
        # 1. Find and read Excel/CSV files from input_dir
        # 2. Parse and validate taxonomy data
        # 3. Clean taxonomy names using TaxonomyCleaner
        # 4. Standardize host names
        # 5. Validate functional annotations
        # 6. Write to output TSV file

        output_dir = self.output_dir / "taxonomy_db"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / Config.TAXONOMY_MAPPING_FILE
        print(f"Taxonomy database will be saved to: {output_file}")

        # Placeholder: Create empty database structure
        taxonomy_df = pd.DataFrame(
            columns=["Genus", "Host", "Function", "Confidence", "Evidence", "Reference"]
        )
        taxonomy_df.to_csv(output_file, sep="\t", index=False)

        print(f"Taxonomy database built: {len(taxonomy_df)} entries")

    def build_gene_db(self) -> None:
        """
        Build gene-to-function mapping database and DIAMOND index.

        Expected input format:
        1. Gene annotation file (Excel/CSV):
           - Columns: GeneID, GeneName, Function, Pathway, Description, Sequence
        2. Gene sequence file (FASTA):
           - Header: >GeneID|GeneName
           - Sequence: Protein sequence

        Output:
        1. TSV file: data/gene_db/gene_function_mapping.tsv
        2. DIAMOND index: data/gene_db/gene_reference.dmnd
        """
        print("Building gene database...")

        # TODO: Implement gene database building
        # 1. Find and read gene annotation files
        # 2. Parse and validate gene data
        # 3. Extract or load gene sequences
        # 4. Build gene-to-function mapping table
        # 5. Create FASTA file for DIAMOND indexing
        # 6. Run DIAMOND makedb to create index

        output_dir = self.output_dir / "gene_db"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Build gene mapping table
        output_file = output_dir / Config.GENE_MAPPING_FILE
        print(f"Gene mapping will be saved to: {output_file}")

        # Placeholder: Create empty database structure
        gene_df = pd.DataFrame(
            columns=["GeneID", "GeneName", "Function", "Pathway", "Description"]
        )
        gene_df.to_csv(output_file, sep="\t", index=False)

        print(f"Gene mapping built: {len(gene_df)} entries")

        # Build DIAMOND index
        # self._build_diamond_index(output_dir)

    def build_ontology(self) -> None:
        """
        Build functional ontology hierarchy.

        Creates a hierarchical tree structure of functional categories
        for organizing and aggregating predictions.

        Expected input format (JSON or custom):
        - Hierarchical structure of functional categories
        - Example: KEGG pathways, COG categories, custom ontologies

        Output:
        - JSON file: data/ontology/function_hierarchy.json
        """
        print("Building functional ontology...")

        # TODO: Implement ontology building
        # 1. Parse ontology definition files
        # 2. Build hierarchical tree structure
        # 3. Validate ontology consistency
        # 4. Export to JSON format

        output_dir = self.output_dir / "ontology"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / Config.ONTOLOGY_TREE_FILE
        print(f"Ontology will be saved to: {output_file}")

        # Placeholder: Create empty ontology structure
        ontology = {
            "version": "1.0",
            "categories": [],
            "hierarchy": {},
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(ontology, f, indent=2, ensure_ascii=False)

        print("Functional ontology built")

    def _build_diamond_index(self, output_dir: Path) -> None:
        """
        Build DIAMOND database index from gene sequences.

        Args:
            output_dir: Directory containing gene FASTA file

        Raises:
            RuntimeError: If DIAMOND execution fails
        """
        fasta_file = output_dir / "gene_reference.fasta"
        diamond_index = output_dir / Config.DIAMOND_INDEX_FILE

        if not fasta_file.exists():
            print(f"Warning: Gene FASTA file not found: {fasta_file}")
            print("Skipping DIAMOND index creation.")
            return

        print(f"Building DIAMOND index from {fasta_file}...")

        cmd = [
            "diamond",
            "makedb",
            "--in",
            str(fasta_file),
            "--db",
            str(diamond_index.with_suffix("")),  # DIAMOND adds .dmnd automatically
        ]

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"DIAMOND index created: {diamond_index}")
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"DIAMOND makedb failed: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError(
                "DIAMOND not found. Please install DIAMOND and ensure it's in your PATH."
            )

    def validate_input_files(self) -> Dict[str, List[Path]]:
        """
        Validate and list available input files.

        Returns:
            Dictionary mapping file types to file paths
        """
        input_files = {
            "taxonomy": [],
            "gene_annotation": [],
            "gene_sequence": [],
            "ontology": [],
        }

        if not self.input_dir.exists():
            print(f"Warning: Input directory not found: {self.input_dir}")
            return input_files

        # Find taxonomy files
        for pattern in ["*taxonomy*.xlsx", "*taxonomy*.csv", "*16s*.xlsx"]:
            input_files["taxonomy"].extend(self.input_dir.glob(pattern))

        # Find gene annotation files
        for pattern in ["*gene*.xlsx", "*gene*.csv", "*annotation*.xlsx"]:
            input_files["gene_annotation"].extend(self.input_dir.glob(pattern))

        # Find gene sequence files
        for pattern in ["*.fasta", "*.fa", "*.faa"]:
            input_files["gene_sequence"].extend(self.input_dir.glob(pattern))

        # Find ontology files
        for pattern in ["*ontology*.json", "*hierarchy*.json"]:
            input_files["ontology"].extend(self.input_dir.glob(pattern))

        return input_files

    def print_summary(self) -> None:
        """
        Print summary of available input files and database status.
        """
        print("\n" + "=" * 60)
        print("Database Builder Summary")
        print("=" * 60)

        print(f"\nInput directory: {self.input_dir}")
        print(f"Output directory: {self.output_dir}")

        input_files = self.validate_input_files()
        print("\nAvailable input files:")
        for file_type, files in input_files.items():
            print(f"  {file_type}: {len(files)} file(s)")
            for f in files:
                print(f"    - {f.name}")

        print("\nDatabase status:")
        for db_name, db_path in [
            ("Taxonomy DB", self.output_dir / "taxonomy_db" / Config.TAXONOMY_MAPPING_FILE),
            ("Gene DB", self.output_dir / "gene_db" / Config.GENE_MAPPING_FILE),
            ("DIAMOND Index", self.output_dir / "gene_db" / Config.DIAMOND_INDEX_FILE),
            ("Ontology", self.output_dir / "ontology" / Config.ONTOLOGY_TREE_FILE),
        ]:
            status = "✓ Exists" if db_path.exists() else "✗ Not found"
            print(f"  {db_name}: {status}")

        print("=" * 60 + "\n")
