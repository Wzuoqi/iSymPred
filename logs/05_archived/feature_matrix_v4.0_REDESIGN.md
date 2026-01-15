# Feature Matrix v4.0 - Redesign for Small Sample Training

**Date:** 2026-01-08
**Version:** 4.0 (Redesign)
**Target:** Small sample Random Forest training
**Output Level:** Taxon-Function pair (not Taxon aggregation)

---

## Problem Analysis

### Issues with v3.0
1. **Too many features (64):** Causes overfitting in small sample training
2. **Wrong granularity:** Taxon-level aggregation loses function-specific information
3. **Feature redundancy:** Many features are highly correlated
4. **Biological relevance:** Some features lack clear biological interpretation

### Requirements for v4.0
1. **Small feature set:** 10-15 features maximum (suitable for small samples)
2. **Taxon-Function pairs:** Each row = one Taxon match record
3. **Biologically meaningful:** Features directly related to symbiont function prediction
4. **Interpretable:** Clear biological meaning for each feature

---

## Core Biological Principles

### What Makes a True Symbiont Function?
1. **Abundance:** High relative abundance suggests ecological importance
2. **Host Specificity:** Match between symbiont's known host and current host
3. **Taxonomic Confidence:** Species-level match > Genus-level match
4. **Evidence Quality:** High-quality scientific evidence (genjournals)
5. **Function Probability:** Prediction confidence from the model
6. **Consistency:** Multiple records supporting the same function

---

## Redesigned Feature Matrix (12 Features)

### Output Format
**Granularity:** Taxon-Function pair (one row per match record)
**Example:**
```
Taxon                    Function              Feature1  Feature2  ...
Wolbachia pipientis     cytoplasmic_incomp    100.0     1.5       ...
Wolbachia pipientis     virus_interaction     100.0     1.3       ...
Buchnera aphidicola     amino_acid_provision  5.2       1.5       ...
```

### Feature List (12 Core Features)

#### 1. Abundance Features (2)
- **`Relative_Abundance_Pct`** (Float, 0-100)
  - Relative abundance of the taxon in the sample
  - **Biological meaning:** Abundant taxa are more likely to be functionally important

- **`Log_Abundance`** (Float)
  - log10(Relative_Abundance_Pct + 1)
  - **Biological meaning:** Linearizes abundance for ML models

#### 2. Taxonomic Confidence (2)
- **`Match_Level_Score`** (Float, 0.6 or 1.0)
  - 1.0 = Species-level match, 0.6 = Genus-level match
  - **Biological meaning:** Species-level identification is more reliable

- **`Is_Known_Symbiont`** (Binary, 0/1)
  - 1 if genus is in known symbiont list (Wolbachia, Buchnera, etc.)
  - **Biological meaning:** Prior knowledge of symbiont status

#### 3. Host Context (3)
- **`Host_Match_Weight`** (Float, 0.8-1.5)
  - Weight based on host context match level
  - **Biological meaning:** Host-specific symbionts are more likely to be functional

- **`Host_Match_Level`** (Categorical → One-hot, 6 levels)
  - Species, Genus, Family, Order, General, Mismatch
  - **Biological meaning:** Degree of host specificity
  - **Note:** Will be one-hot encoded for ML (5 binary features)

#### 4. Evidence Quality (2)
- **`Evidence_Level`** (Integer, 1-5)
  - 5 = Symbiont + Genome + Top Journal
  - **Biological meaning:** Higher evidence = more reliable prediction

- **`Has_Genome_Data`** (Binary, 0/1)
  - 1 if genome sequenced
  - **Biological meaning:** Genome availability indicates well-studied symbiont

#### 5. Prediction Confidence (2)
- **`Function_Probability`** (Float, 0-1)
  - Probability of function existence (from functions table)
  - **Biological meaning:** Model's confidence in function prediction

- **`Adjusted_Score`** (Float)
  - Base_Score × Host_Match_Weight² × Evidence_Weight^1.5
  - **Biological meaning:** Integrated quality metric

#### 6. Function Context (1)
- **`Function_Support_Count`** (Integer)
  - Number of taxa supporting this function in the sample
  - **Biological meaning:** Functions supported by multiple taxa are more robust

---

## Total Features: 12 Core Features
(Or 16 if Host_Match_Level is one-hot encoded)

This is suitable for small samplrule of thumb: 5-10 samples per feature).

---

## Implementation Strategy

### Step 1: Extract Taxon-Function Pairs
Instead of aggregating by Taxon, keep each Taxon-Function match record as a separate row.

### Step 2: Compute Features
For each Taxon-Function pair:
1. Get taxon abundance (from input)
2. Get host match weight (from prediction)
3. Get evidence level (from database)
4. Get function probability (from functions table)
5. Compute derived features (log abundance, adjusted score)

### Step 3: Add Function-Level Context
For each function, count how many taxa support it in the sample.

### Step 4: Output Format
```
Taxon,Function,Relative_Abundance_Pct,Log_Abundance,Match_Level_Score,Is_Known_Symbiont,Host_Match_Weight,Host_Match_Level,Evidence_Level,Has_Genome_Data,Function_Probability,Adjusted_Score,Function_Support_Count
```

---

## Example Output

```tsv
Taxon	Function	Relative_Abundance_Pct	Log_Abundance	Match_Level_Score	Is_Known_Symbiont	Host_Match_Weight	Host_Match_Level	Evidence_Level	Has_Genome_Data	Function_Probability	Adjusted_Score	Function_Support_Count
Wolbachia pipientis	cytoplasmic incompatibility	100.0	2.0	1.0	1	1.5	Species	5	1	0.855	556.1	1
Wolbachia pipientis	virus interaction	100.0	2.0	1.0	1	1.3	Genus	3	1	0.725	450.9	2
Buchnera aphidicola	amino acid provision	5.2	0.72	1.0	1	1.5	Species	5	1	0.823	125.3	5
Acinetobacter sp.	antimicrobial activity	6.7	0.83	0.6	0	1.1	Order	3	0	0.735	79.5	198
```

---

## Machine Learning Workflow

### Training Data Preparation
```python
import pandas as pd

# Load feature matrix (Taxon-Function pairs)
features = pd.read_csv('output_feature_matrix.tsv', sep='\t')

# Manual annotation: Label key Taxon-Function pairs
# 1 = This is a true/important symbiont function
# 0 = This is not a key function (or false positive)
features['Is_Key_Function'] = [...]  # Manual annotation required

# Prepare features
X = features[['Relative_Abundance_Pct', 'Log_Abundance', 'Match_Level_Score',
              'Is_Known_Symbiont', 'Host_Match_Weight', 'Evidence_Level',
              'Has_Genome_Data', 'Function_Probability', 'Adjusted_Score',
              'Function_Support_Count']]

# One-hot encode Host_Match_Level if needed
X = pd.get_dummies(X, columns=['Host_Match_Level'])

y = features['Is_Key_Function']
```

### Model Training
```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

# Train with small sample
rf = RandomForestClassifier(
    n_estimators=50,  # Fewer trees for small samples
    max_depth=5,      # Limit depth to prevent overfitting
    min_samples_split=5,
    class_weight='balanced',
    random_state=42
)

# Cross-validation
scores = cross_val_score(rf, X, y, cv=5, scoring='roc_auc')
print(f"CV ROC-AUC: {scores.mean():.3f} ± {scores.std():.3f}")

# Train final model
rf.fit(X, y)

# Feature importance
importances = pd.DataFrame({
    'Feature': X.columns,
    'Importance': rf.feature_importances_
}).sort_values('Importance', ascending=False)

print(importances)
```

---

## Advantages of This Design

### 1. Suitable for Small Samples
- **12-16 features** (vs 64 in v3.0)
- Rule of thumb: Need 5-10 samples per feature
- With 12 features, need ~60-120 labeled Taxon-Function pairs

### 2. Biologically Meaningful
- Every feature has clear biological interpretation
- Features directly related to symbiont function prediction
- No redundant or derived features

### 3. Correct Granularity
- **Taxon-Function pairs** (not Taxon aggregation)
- Allows predicting which specific functions are real
- More training data (multiple rows per taxon)

### 4. Interpretable Results
- Can identify which Taxon-Function pairs are key
- Can explain why (feature importance)
- Can validate against literature

---

## Comparison: v3.0 vs v4.0

| Aspect | v3.0 | v4.0 |
|--------|------|------|
| Features | 64 | 12-16 |
| Granularity | Taxon-level | Taxon-Function pair |
| Sample size | Large (>500) | Small (50-200) |
| Overfitting risk | High | Low |
| Biological meaning | Mixed | High |
| Interpretability | Moderate | High |
| Training data | 55 rows (taxa) | 200+ rows (pairs) |

---

## Next Steps

1. Implement Taxon-Function pair extraction
2. Compute 12 core features for each pair
3. Test with existing data
4. Update documentation
5. Provide example ML workflow

---

**End of Redesign Document**
