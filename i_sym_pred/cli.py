#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CLI interface for iSymPred using Click framework.
"""

import click
from i_sym_pred import __version__


@click.group()
@click.version_option(version=__version__)
def main():
    """
    iSymPred - Insect Symbiont Predictor

    Predict symbiont functions from 16S amplicon or metagenomic data
    with insect host context support.
    """
    pass


@main.command("build-db")
@click.option(
    "--input-dir",
    "-i",
    type=click.Path(exists=True),
    required=True,
    help="Directory containing raw reference data (Excel/Fasta files from assets/)",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default="data",
    help="Output directory for built database (default: data/)",
)
@click.option(
    "--db-type",
    "-t",
    type=click.Choice(["taxonomy", "gene", "all"], case_sensitive=False),
    default="all",
    help="Type of database to build: taxonomy (16S), gene (metagenomic), or all",
)
def build_db(input_dir, output_dir, db_type):
    """
    Build internal database from raw reference data.

    Converts Excel/Fasta files from assets/ into optimized internal
    database format for fast querying.
    """
    click.echo(f"Building {db_type} database...")
    click.echo(f"Input directory: {input_dir}")
    click.echo(f"Output directory: {output_dir}")

    # TODO: Implement database building logic
    click.echo("Database building not yet implemented.")


@main.command("predict-16s")
@click.option(
    "--input",
    "-i",
    type=click.Path(exists=True),
    required=True,
    help="Input file: OTU table (BIOM/TSV) or taxonomy assignment file",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    required=True,
    help="Output file for functional predictions",
)
@click.option(
    "--host",
    "-h",
    type=str,
    default=None,
    help="Insect host name for context-aware prediction (optional)",
)
@click.option(
    "--db-path",
    "-d",
    type=click.Path(exists=True),
    default="data/taxonomy_db",
    help="Path to taxonomy database (default: data/taxonomy_db)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["biom", "tsv"], case_sensitive=False),
    default="tsv",
    help="Input file format (default: tsv)",
)
def predict_16s(input, output, host, db_path, format):
    """
    Predict symbiont functions from 16S amplicon data.

    Uses taxonomy-to-function mapping with optional insect host context
    to predict functional profiles of microbial communities.
    """
    click.echo("Running 16S-based prediction...")
    click.echo(f"Input file: {input}")
    click.echo(f"Output file: {output}")
    click.echo(f"Host context: {host if host else 'None (general prediction)'}")
    click.echo(f"Database: {db_path}")
    click.echo(f"Format: {format}")

    # TODO: Implement 16S prediction logic
    click.echo("16S prediction not yet implemented.")


@main.command("predict-meta")
@click.option(
    "--input",
    "-i",
    type=click.Path(exists=True),
    required=True,
    help="Input file: gene sequences (FASTA) or gene IDs (TSV)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    required=True,
    help="Output file for functional predictions",
)
@click.option(
    "--mode",
    "-m",
    type=click.Choice(["sequence", "id"], case_sensitive=False),
    default="sequence",
    help="Input mode: sequence (FASTA for DIAMOND search) or id (direct gene ID mapping)",
)
@click.option(
    "--db-path",
    "-d",
    type=click.Path(exists=True),
    default="data/gene_db",
    help="Path to gene database (default: data/gene_db)",
)
@click.option(
    "--threads",
    "-t",
    type=int,
    default=4,
    help="Number of threads for DIAMOND search (default: 4)",
)
@click.option(
    "--evalue",
    "-e",
    type=float,
    default=1e-5,
    help="E-value threshold for DIAMOND search (default: 1e-5)",
)
def predict_meta(input, output, mode, db_path, threads, evalue):
    """
    Predict symbiont functions from metagenomic data.

    Uses gene sequence alignment (DIAMOND) or direct gene ID mapping
    to predict functional profiles from metagenomic datasets.
    """
    click.echo("Running metagenomic prediction...")
    click.echo(f"Input file: {input}")
    click.echo(f"Output file: {output}")
    click.echo(f"Mode: {mode}")
    click.echo(f"Database: {db_path}")

    if mode == "sequence":
        click.echo(f"DIAMOND threads: {threads}")
        click.echo(f"E-value threshold: {evalue}")

    # TODO: Implement metagenomic prediction logic
    click.echo("Metagenomic prediction not yet implemented.")


if __name__ == "__main__":
    main()
