# Record Predictor v5.1 - Fuzzy Matching Update

**Date:** 2025-01-15
**Module:** `isympred/predictors/record_predictor.py`
**Version:** v5.1

## Summary

Added fuzzy matching support to automatically clean taxonomy name suffixes in both input data and database records. This ensures consistent matching even when taxonomy names contain detailed classification suffixes.

## Problem

Input data from certain databases (e.g., GTDB, SILVA) may contain detailed classification suffixes in taxonomy names:
- `s__Akkermansia muciniphila_D_776786`
- `g__Bacteroides_A`
- `s__Lactobacillus_12345`

These suffixes prevent exact matching with the symbiont database, causing valid matches to be missed.

## Solution

### 1. New Method: `_clean_taxonomy_name()`

Added a new method to clean taxonomy name suffixes using regex pattern matching:

```python
# Pattern matches:
# - _[A-Z]_[digits] suffix (e.g., _D_776786, _A_123456)
# - _[digits] suffix (e.g., _12345)
TAXONOMY_SUFFIX_PATTERN = re.compile(r'_[A-Z]_\d+$|_\d+$')
```

**Examples:**
| Input | Output |
|-------|--------|
| `Akkermansia muciniphila_D_776786` | `Akkermansia muciniphila` |
| `Bacteroides_A_123` | `Bacteroides` |
| `Lactobacillus_12345` | `Lactobacillus` |
| `Genus species_A_1_B_2` | `Genus species` |

### 2. Updated Methods

#### `_parse_input_taxon()` (line 719-741)
- Now applies `_clean_taxonomy_name()` to both genus and species extracted from input OTU table
- Ensures input taxonomy names are cleaned before database lookup

#### `_load_database()` (line 666-717)
- Now applies `_clean_taxonomy_name()` to both genus and species when building the database index
- Ensures database keys are standardized for consistent matching

## Changes

| File | Lines | Change |
|------|-------|--------|
| `record_predictor.py` | 18-29 | Added class docstring and `TAXONOMY_SUFFIX_PATTERN` |
| `record_predictor.py` | 95-127 | Added `_clean_taxonomy_name()` method |
| `record_predictor.py` | 697-702 | Updated `_load_database()` to use fuzzy matching |
| `record_predictor.py` | 727-732 | Updated `_parse_input_taxon()` to use fuzzy matching |

## Backward Compatibility

- Fully backward compatible
- No changes to input/output formats
- No changes to CLI arguments
- Existing workflows will continue to work

## Testing

To verify the fuzzy matching works correctly:

```bash
# Test with sample data containing suffixes
python isympred/predictors/record_predictor.py \
    -i tests/data/test_data.tsv \
    -d isympred/database/symbiont_record/record_db.tsv \
    -o tmp/fuzzy_test_output.tsv
```

## Notes

- The regex pattern is designed to be conservative, only matching common suffix patterns
- Multiple consecutive suffixes are handled (e.g., `_A_1_B_2` -> cleaned iteratively)
- Original taxonomy names are preserved in the output for traceability
