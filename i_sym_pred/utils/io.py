#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File I/O utilities for iSymPred.

Handles reading and writing various bioinformatics file formats:
- BIOM format (OTU tables)
- FASTA/FASTQ (sequences)
- TSV/CSV (tabular data)
- Excel files
"""

from typing import Dict, Any, Optional, Union
import pandas as pd
from pathlib import Path
from Bio import SeqIO


class FileReader:
    """
    Unified file reader for various bioinformatics formats.
    """

    @staticmethod
    def read_fasta(file_path: str) -> Dict[str, str]:
        """
        Read FASTA file and return sequences as dictionary.

        Args:
            file_path: Path to FASTA file

        Returns:
            Dictionary mapping sequence IDs to sequences
        """
        sequences = {}
        for record in SeqIO.parse(file_path, "fasta"):
            sequences[record.id] = str(record.seq)
        return sequences

    @staticmethod
    def read_biom(file_path: str) -> pd.DataFrame:
        """
        Read BIOM format file and convert to DataFrame.

        Args:
            file_path: Path to BIOM file

        Returns:
            DataFrame with OTU table (samples as columns, OTUs as rows)

        Note:
            Requires biom-format package to be installed
        """
        try:
            import biom

            table = biom.load_table(file_path)
            df = table.to_dataframe()
            return df
        except ImportError:
            raise ImportError(
                "biom-format package not installed. "
                "Install with: pip install biom-format"
            )

    @staticmethod
    def read_tsv(file_path: str, **kwargs) -> pd.DataFrame:
        """
        Read TSV file into DataFrame.

        Args:
            file_path: Path to TSV file
            **kwargs: Additional arguments for pd.read_csv

        Returns:
            DataFrame
        """
        return pd.read_csv(file_path, sep="\t", **kwargs)

    @staticmethod
    def read_csv(file_path: str, **kwargs) -> pd.DataFrame:
        """
        Read CSV file into DataFrame.

        Args:
            file_path: Path to CSV file
            **kwargs: Additional arguments for pd.read_csv

        Returns:
            DataFrame
        """
        return pd.read_csv(file_path, **kwargs)

    @staticmethod
    def read_excel(file_path: str, sheet_name: Union[str, int] = 0, **kwargs) -> pd.DataFrame:
        """
        Read Excel file into DataFrame.

        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name or index (default: 0)
            **kwargs: Additional arguments for pd.read_excel

        Returns:
            DataFrame
        """
        return pd.read_excel(file_path, sheet_name=sheet_name, **kwargs)

    @staticmethod
    def auto_read(file_path: str, **kwargs) -> Union[pd.DataFrame, Dict[str, str]]:
        """
        Automatically detect file format and read accordingly.

        Args:
            file_path: Path to input file
            **kwargs: Additional arguments for specific readers

        Returns:
            DataFrame or dictionary depending on file type
        """
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix in [".fasta", ".fa", ".faa", ".fna"]:
            return FileReader.read_fasta(file_path)
        elif suffix == ".biom":
            return FileReader.read_biom(file_path)
        elif suffix == ".tsv":
            return FileReader.read_tsv(file_path, **kwargs)
        elif suffix == ".csv":
            return FileReader.read_csv(file_path, **kwargs)
        elif suffix in [".xlsx", ".xls"]:
            return FileReader.read_excel(file_path, **kwargs)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")


class FileWriter:
    """
    Unified file writer for various bioinformatics formats.
    """

    @staticmethod
    def write_fasta(sequences: Dict[str, str], file_path: str) -> None:
        """
        Write sequences to FASTA file.

        Args:
            sequences: Dictionary mapping sequence IDs to sequences
            file_path: Output FASTA file path
        """
        with open(file_path, "w") as f:
            for seq_id, seq in sequences.items():
                f.write(f">{seq_id}\n")
                # Write sequence in lines of 80 characters
                for i in range(0, len(seq), 80):
                    f.write(f"{seq[i:i+80]}\n")

    @staticmethod
    def write_tsv(df: pd.DataFrame, file_path: str, **kwargs) -> None:
        """
        Write DataFrame to TSV file.

        Args:
            df: DataFrame to write
            file_path: Output TSV file path
            **kwargs: Additional arguments for df.to_csv
        """
        df.to_csv(file_path, sep="\t", index=False, **kwargs)

    @staticmethod
    def write_csv(df: pd.DataFrame, file_path: str, **kwargs) -> None:
        """
        Write DataFrame to CSV file.

        Args:
            df: DataFrame to write
            file_path: Output CSV file path
            **kwargs: Additional arguments for df.to_csv
        """
        df.to_csv(file_path, index=False, **kwargs)

    @staticmethod
    def write_excel(df: pd.DataFrame, file_path: str, sheet_name: str = "Sheet1", **kwargs) -> None:
        """
        Write DataFrame to Excel file.

        Args:
            df: DataFrame to write
            file_path: Output Excel file path
            sheet_name: Sheet name (default: "Sheet1")
            **kwargs: Additional arguments for df.to_excel
        """
        df.to_excel(file_path, sheet_name=sheet_name, index=False, **kwargs)

    @staticmethod
    def write_biom(df: pd.DataFrame, file_path: str) -> None:
        """
        Write DataFrame to BIOM format file.

        Args:
            df: DataFrame with OTU table (samples as columns, OTUs as rows)
            file_path: Output BIOM file path

        Note:
            Requires biom-format package to be installed
        """
        try:
            import biom

            table = biom.Table(
                df.values,
                observation_ids=df.index.tolist(),
                sample_ids=df.columns.tolist(),
            )
            with biom.util.biom_open(file_path, "w") as f:
                table.to_hdf5(f, "iSymPred generated")
        except ImportError:
            raise ImportError(
                "biom-format package not installed. "
                "Install with: pip install biom-format"
            )


def validate_file_exists(file_path: str) -> bool:
    """
    Check if file exists.

    Args:
        file_path: Path to file

    Returns:
        True if file exists, False otherwise
    """
    return Path(file_path).exists()


def get_file_format(file_path: str) -> str:
    """
    Get file format from file extension.

    Args:
        file_path: Path to file

    Returns:
        File format string (lowercase)
    """
    return Path(file_path).suffix.lower().lstrip(".")
