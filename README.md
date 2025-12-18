# iSymPred - Insect Symbiont Predictor

**iSymPred** (Insect Symbiont Predictor) is a bioinformatics CLI tool for predicting insect symbiont functions from 16S amplicon data or metagenomic data.

Similar to FAPROTAX, iSymPred provides functional annotation of microbial communities, but with enhanced support for:
- **Insect host context**: Context-aware predictions considering host-symbiont relationships
- **Metagenomic gene functions**: Direct functional annotation from metagenomic gene sequences

## Features

- 🦟 **Host-aware predictions**: Incorporates insect host information for more accurate functional predictions
- 🧬 **Dual input support**: Works with both 16S amplicon data and metagenomic sequences
- ⚡ **Fast alignment**: Uses DIAMOND for rapid protein sequence alignment
- 📊 **Multiple formats**: Supports BIOM, TSV, FASTA, and other common bioinformatics formats
- 🔍 **Hierarchical annotations**: Provides functional predictions at multiple levels

## Installation

### From source

```bash
git clone https://github.com/yourusername/iSymPred.git
cd iSymPred
pip install -e .
```

### Requirements

- Python >= 3.8
- DIAMOND (for metagenomic predictions)

Install Python dependencies:
```bash
pip install -r requirements.txt
```

Install DIAMOND (optional, for metagenomic mode):
```bash
# Ubuntu/Debian
sudo apt-get install diamond-aligner

# macOS
brew install diamond

# Or download from: https://github.com/bbuchfink/diamond
```

## Quick Start

### 1. Build Database

First, prepare your reference data in the `assets/` directory, then build the internal database:

```bash
isympred build-db --input-dir assets/ --output-dir data/ --db-type all
```

**Options:**
- `--input-dir, -i`: Directory containing raw reference data (Excel/Fasta files)
- `--output-dir, -o`: Output directory for built database (default: `data/`)
- `--db-type, -t`: Database type to build: `taxonomy`, `gene`, or `all` (default: `all`)

### 2. Predict from 16S Data

Predict symbiont functions from 16S amplicon data:

```bash
isympred predict-16s \
  --input otu_table.tsv \
  --output functional_predictions.tsv \
  --host Drosophila \
  --format tsv
```

**Options:**
- `--input, -i`: Input OTU table (BIOM/TSV) or taxonomy assignment file
- `--output, -o`: Output file for functional predictions
- `--host, -h`: Insect host name for context-aware prediction (optional)
- `--db-path, -d`: Path to taxonomy database (default: `data/taxonomy_db`)
- `--format, -f`: Input file format: `biom` or `tsv` (default: `tsv`)

**Example with host context:**
```bash
# Predict Wolbachia functions in Drosophila
isympred predict-16s -i drosophila_16s.tsv -o functions.tsv --host Drosophila

# General prediction without host context
isympred predict-16s -i general_16s.tsv -o functions.tsv
```

### 3. Predict from Metagenomic Data

Predict functions from metagenomic gene sequences or gene IDs:

**Sequence mode** (FASTA input, uses DIAMOND alignment):
```bash
isympred predict-meta \
  --input genes.fasta \
  --output functional_predictions.tsv \
  --mode sequence \
  --threads 8 \
  --evalue 1e-5
```

**ID mode** (direct gene ID mapping):
```bash
isympred predict-meta \
  --input gene_abundance.tsv \
  --output functional_predictions.tsv \
  --mode id
```

**Options:**
- `--input, -i`: Input file (FASTA for sequence mode, TSV for ID mode)
- `--output, -o`: Output file for functional predictions
- `--mode, -m`: Prediction mode: `sequence` or `id` (default: `sequence`)
- `--db-path, -d`: Path to gene database (default: `data/gene_db`)
- `--threads, -t`: Number of threads for DIAMOND (default: 4)
- `--evalue, -e`: E-value threshold for DIAMOND (default: 1e-5)

## Input Formats

### 16S Amplicon Data

**OTU Table (TSV format):**
```
OTU_ID          Taxonomy                                    Sample1  Sample2
OTU_001         k__Bacteria;g__Wolbachia;s__pipientis      100      150
OTU_002         k__Bacteria;g__Buchnera;s__aphidicola      50       80
```

**BIOM format:**
```bash
isympred predict-16s -i otu_table.biom -o output.tsv --format biom
```

### Metagenomic Data

**Gene sequences (FASTA):**
```
>gene001
MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQFEVVHSLAKWKRQTLGQHDFSAGEGLYTHMKALRPDEDRLSPLHSVYVDQWDWERVMGDGERQFSTLKSTVEAIWAGIKATEAAVSEEFGLAPFLPDQIHFVHSQELLSRYPDLDAKGRERAIAKDLGAVFLVGIGGKLSDGHRHDVRAPDYDDWSTPSELGHAGLNGDILVWNPVLEDAFELSSMGIRVDADTLKHQLALTGDEDRLELEWHQALLRGEMPQTIGGGIGQSRLTMLLLQLPHIGQVQAGVWPAAVRESVPSLL
```

**Gene abundance table (TSV):**
```
GeneID      Sample1  Sample2
gene001     100      150
gene002     50       80
```

## Output Format

Functional prediction output (TSV):
```
Feature         Function                    Abundance   Confidence  Evidence
OTU_001         Reproduction manipulation   100         0.90        experimental
OTU_002         Amino acid synthesis        50          0.95        experimental
```

## Project Structure

```
iSymPred/
├── assets/                     # Raw reference data (user-provided)
├── i_sym_pred/                 # Main Python package
│   ├── cli.py                  # CLI interface
│   ├── config.py               # Configuration
│   ├── database/               # Database management
│   │   ├── builder.py          # Database builder
│   │   └── query.py            # Database query interface
│   ├── predictors/             # Prediction modules
│   │   ├── base.py             # Base predictor class
│   │   ├── s16_predictor.py    # 16S predictor
│   │   └── meta_predictor.py   # Metagenomic predictor
│   └── utils/                  # Utility functions
│       ├── io.py               # File I/O
│       └── taxonomy.py         # Taxonomy utilities
├── data/                       # Built databases
│   ├── taxonomy_db/            # 16S taxonomy mappings
│   ├── gene_db/                # Gene function mappings
│   └── ontology/               # Functional hierarchies
├── tests/                      # Unit tests
├── requirements.txt            # Python dependencies
├── setup.py                    # Installation script
└── README.md                   # This file
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Style

```bash
# Format code
black i_sym_pred/

# Check style
flake8 i_sym_pred/
```

## Citation

If you use iSymPred in your research, please cite:

```
[Citation information to be added]
```

## License

MIT License

## Contact

For questions and support, please open an issue on GitHub or contact:
- Email: [your-email@example.com]
- GitHub: [https://github.com/yourusername/iSymPred]

## Acknowledgments

- Inspired by FAPROTAX for functional annotation
- Uses DIAMOND for fast sequence alignment
- Built with BioPython, pandas, and Click
