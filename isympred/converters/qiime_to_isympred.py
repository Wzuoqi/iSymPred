#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QIIME Taxonomy to iSymPred Format Converter

This script converts QIIME2 taxonomy output format to iSymPred input format.

QIIME format (input):
    Feature ID                  Taxon                                           Confidence
    SRR27445304_2;size=813      d__Bacteria; p__Proteobacteria; ...             0.7914

iSymPred format (output):
    Taxon                                           Abundance
    d__Bacteria; p__Proteobacteria; ...             813

Usage:
    python qiime_to_isympred.py -i input.qiime.taxonomy.tsv -o output.tsv
    python qiime_to_isympred.py -i input.tsv -o output.tsv --abundance-col Abundance
"""

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def extract_abundance_from_feature_id(feature_id: str) -> Tuple[str, int]:
    """
    Extract abundance (size) from QIIME Feature ID.

    Args:
        feature_id: Feature ID string, e.g., "SRR27445304_2;size=813"

    Returns:
        Tuple of (clean_feature_id, abundance)

    Examples:
        >>> extract_abundance_from_feature_id("SRR27445304_2;size=813")
        ('SRR27445304_2', 813)
        >>> extract_abundance_from_feature_id("ASV_001")
        ('ASV_001', 1)
    """
    # Pattern to match ";size=<number>" at the end
    size_pattern = r";size=(\d+)$"
    match = re.search(size_pattern, str(feature_id))

    if match:
        abundance = int(match.group(1))
        clean_id = re.sub(size_pattern, "", str(feature_id))
        return clean_id, abundance
    else:
        # If no size info, default to 1
        logger.debug(f"No size info found in Feature ID: {feature_id}, defaulting to 1")
        return str(feature_id), 1


def convert_qiime_taxonomy(
    input_file: Path,
    output_file: Path,
    abundance_col: Optional[str] = None,
    feature_id_col: str = "Feature ID",
    taxon_col: str = "Taxon",
    confidence_col: str = "Confidence",
    min_confidence: float = 0.0,
    aggregate_duplicates: bool = True
) -> pd.DataFrame:
    """
    Convert QIIME taxonomy format to iSymPred format.

    Args:
        input_file: Path to input QIIME taxonomy TSV file
        output_file: Path to output iSymPred format TSV file
        abundance_col: Column name for abundance (if separate from Feature ID)
        feature_id_col: Column name for Feature ID
        taxon_col: Column name for taxonomy
        confidence_col: Column name for confidence score
        min_confidence: Minimum confidence threshold (0.0-1.0)
        aggregate_duplicates: Whether to aggregate duplicate taxa

    Returns:
        Converted DataFrame

    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If required columns are missing
    """
    input_path = Path(input_file)
    output_path = Path(output_file)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Reading input file: {input_path}")

    # Read input file
    df = pd.read_csv(input_path, sep="\t")
    logger.info(f"Loaded {len(df)} records")
    logger.info(f"Columns found: {list(df.columns)}")

    # Validate required columns
    required_cols = [taxon_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Extract abundance
    if abundance_col and abundance_col in df.columns:
        # Use explicit abundance column
        logger.info(f"Using abundance column: {abundance_col}")
        df["Abundance"] = pd.to_numeric(df[abundance_col], errors="coerce").fillna(0).astype(int)
    elif feature_id_col in df.columns:
        # Extract from Feature ID
        logger.info(f"Extracting abundance from Feature ID column: {feature_id_col}")
        abundances = df[feature_id_col].apply(extract_abundance_from_feature_id)
        df["Abundance"] = abundances.apply(lambda x: x[1])
    else:
        # Default to 1
        logger.warning("No abundance information found, defaulting to 1")
        df["Abundance"] = 1

    # Filter by confidence if specified
    if min_confidence > 0 and confidence_col in df.columns:
        original_count = len(df)
        df = df[pd.to_numeric(df[confidence_col], errors="coerce").fillna(0) >= min_confidence]
        filtered_count = original_count - len(df)
        logger.info(f"Filtered {filtered_count} records with confidence < {min_confidence}")

    # Create output DataFrame
    result_df = df[[taxon_col, "Abundance"]].copy()
    result_df.columns = ["Taxon", "Abundance"]

    # Aggregate duplicates if requested
    if aggregate_duplicates:
        original_count = len(result_df)
        result_df = result_df.groupby("Taxon", as_index=False)["Abundance"].sum()
        if len(result_df) < original_count:
            logger.info(f"Aggregated {original_count} records to {len(result_df)} unique taxa")

    # Sort by abundance (descending)
    result_df = result_df.sort_values("Abundance", ascending=False).reset_index(drop=True)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write output
    result_df.to_csv(output_path, sep="\t", index=False)
    logger.info(f"Output written to: {output_path}")
    logger.info(f"Total taxa: {len(result_df)}, Total abundance: {result_df['Abundance'].sum()}")

    return result_df


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Convert QIIME taxonomy format to iSymPred format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic conversion (extract abundance from Feature ID)
    python qiime_to_isympred.py -i input.qiime.taxonomy.tsv -o output.tsv

    # Use explicit abundance column
    python qiime_to_isympred.py -i input.tsv -o output.tsv --abundance-col Count

    # Filter by confidence threshold
    python qiime_to_isympred.py -i input.tsv -o output.tsv --min-confidence 0.7

    # Keep duplicates (don't aggregate)
    python qiime_to_isympred.py -i input.tsv -o output.tsv --no-aggregate
        """
    )

    parser.add_argument(
        "-i", "--input",
        type=Path,
        required=True,
        help="Input QIIME taxonomy TSV file"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        required=True,
        help="Output iSymPred format TSV file"
    )
    parser.add_argument(
        "--abundance-col",
        type=str,
        default=None,
        help="Column name for abundance (if not in Feature ID)"
    )
    parser.add_argument(
        "--feature-id-col",
        type=str,
        default="Feature ID",
        help="Column name for Feature ID (default: 'Feature ID')"
    )
    parser.add_argument(
        "--taxon-col",
        type=str,
        default="Taxon",
        help="Column name for taxonomy (default: 'Taxon')"
    )
    parser.add_argument(
        "--confidence-col",
        type=str,
        default="Confidence",
        help="Column name for confidence score (default: 'Confidence')"
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.0,
        help="Minimum confidence threshold (0.0-1.0, default: 0.0)"
    )
    parser.add_argument(
        "--no-aggregate",
        action="store_true",
        help="Don't aggregate duplicate taxa"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        convert_qiime_taxonomy(
            input_file=args.input,
            output_file=args.output,
            abundance_col=args.abundance_col,
            feature_id_col=args.feature_id_col,
            taxon_col=args.taxon_col,
            confidence_col=args.confidence_col,
            min_confidence=args.min_confidence,
            aggregate_duplicates=not args.no_aggregate
        )
        logger.info("Conversion completed successfully!")
        return 0
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
