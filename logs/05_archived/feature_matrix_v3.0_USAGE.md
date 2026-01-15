# Feature Matrix v3.0 - Usage Guide

**Date:** 2026-01-08
**Version:** 3.0
**Target Audience:** Researchers, Data Scientists, Bioinformaticians

---

## Table of Contents
1. [Quick Start](#quick-start)
2. [Feature Glossary](#feature-glossary)
3. [Machine Learning Workflow](#machine-learning-workflow)
4. [Interpretation Guidelines](#interpretation-guidelines)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Running the Predictor
```bash
python isympred/predictors/record_predictor.py \
    -i your_otu_table.tsv \
    -d isympred/database/symbiont_record/record_db.tsv \
    -o output/results.tsv \
    --host "Your Host Species" \
    --host-db isympred/database/host_taxonomy/insect_taxonomy.db
```

### Output Files
Three files will be generated:
1. **`results_functions.tsv`** - Function-level predictions
2. **`results_match_records.tsv`** - Detailed match records
3. **`results_feature_matrix.tsv`** - **64-feature matrix for ML** ⭐

---

## Feature Glossary

### Basic Features (2)

#### `Relative_Abundance_Pct`
- **Type:** Float (0-100)
- **Description:** Relative abundance percentage of the taxon in the sample
- **Interpretation:** Higher values indicate more abundant taxa
- **ML Importance:** ⭐⭐⭐⭐⭐ (Critical)

#### `Match_Level_Score`
- **Type:** Float (0.6 or 1.0)
- **Description:** Taxonomic resolution of the match
  - 1.0 = Species-level match
  - 0.6 = Genus-level match
- **Interpretation:** Higher values indicate more precise taxonomic identification
- **ML Importance:** ⭐⭐⭐⭐

---

### Aggregated Features (6)

#### `Function_Count`
- **Type:** Integer (≥1)
- **Description:** Number of unique functions matched for this taxon
- **Interpretation:** Higher values suggest functional versatility
- **ML Importance:** ⭐⭐⭐⭐

#### `Mean_Adjusted_Score`
- **Type:** Float
- **Description:** Average adjusted score across all matched records
- **Formula:** Mean of (Base_Score × Host_Match_Weight² × Evidence_Weight^1.5)
- **Interpretation:** Higher values indicate stronger evidence
- **ML Importance:** ⭐⭐⭐⭐⭐

#### `Max_Adjusted_Score`
- **Type:** Float
- **Description:** Maximum adjusted score among all records
- **Interpretation:** Peak evidence strength
- **ML Importance:** ⭐⭐⭐

#### `Std_Adjusted_Score`
- **Type:** Float (≥0)
- **Description:** Standard deviation of adjusted scores
- **Interpretation:** Lower values indicate consistent evidence
- **ML Importance:** ⭐⭐⭐

#### `Mean_Quality_Score`
- **Type:** Float
- **Description:** Average quality score combining host match, evidence, and taxonomic match
- **Formula:** (Host_Match_Weight × 40) + (Evidence_Weight × 30) + (Match_Level_Score × 20) + (Normalized_RA × 10)
- **Interpretation:** Composite quality metric (0-100 scale)
- **ML Importance:** ⭐⭐⭐⭐

#### `Max_Quality_Score`
- **Type:** Float
- **Description:** Maximum quality score among all records
- **Interpretation:** Peak quality evidence
- **ML Importance:** ⭐⭐⭐

---

### Host Match Features (8)

#### `Mean_Host_Match_Weight`
- **Type:** Float (0.8-1.5)
- **Description:** Average host match weight
- **Scale:**
  - 1.5 = Species-level host match
  - 1.3 = Genus-level host match
  - 1.2 = Family-level host match
  - 1.1 = Order-level host match
  - 1.0 = General (no host specificity)
  - 0.8 = Mismatch
- **Interpretation:** Higher values indicate better host context match
- **ML Importance:** ⭐⭐⭐⭐⭐

#### `Max_Host_Match_Weight`
- **Type:** Float (0.8-1.5)
- **Description:** Best host match weight among all records
- **ML Importance:** ⭐⭐⭐

#### `Has_Species_Match`, `Has_Genus_Match`, `Has_Family_Match`, `Has_Order_Match`, `Has_General_Match`, `Has_Mismatch`
- **Type:** Binary (0/1)
- **Description:** One-hot encoding of host match levels present
- **Interpretation:** Indicates diversity of host context matches
- **ML Importance:** ⭐⭐

---

### Evidence Quality Features (6)

#### `Mean_Evidence_Level`
- **Type:** Float (1-5)
- **Description:** Average evidence level
- **Scale:**
  - 5 = Symbiont + Genome + Top Journal
  - 4 = Symbiont + Genome
  - 3 = Symbiont + Top Journal
  - 2 = Symbiont only
  - 1 = Low evidence
- **Interpretation:** Higher values indicate stronger scientific evidence
- **ML Importance:** ⭐⭐⭐⭐

#### `Max_Evidence_Level`
- **Type:** Integer (1-5)
- **Description:** Highest evidence level among all records
- **ML Importance:** ⭐⭐⭐⭐

#### `Mean_Evidence_Weight`
- **Type:** Float (0.8-1.5)
- **Description:** Average evidence weight
- **Interpretation:** Reflects overall evidence quality
- **ML Importance:** ⭐⭐⭐⭐

#### `Has_Evidence_Level_5`, `Has_Evidence_Level_4`, `Has_Evidence_Level_3`
- **Type:** Binary (0/1)
- **Description:** Flags for high-quality evidence presence
- **Interpretation:** Indicates availability of top-tier evidence
- **ML Importance:** ⭐⭐⭐

---

### Composite Features (4)

#### `Weighted_Avg_Score`
- **Type:** Float
- **Description:** Quality-weighted average score
- **Formula:** Σ(Adjusted_Score × Quality_Score) / Σ(Quality_Score)
- **Interpretation:** Integrated quality metric
- **ML Importance:** ⭐⭐⭐⭐⭐

#### `Score_CV`
- **Type:** Float (≥0)
- **Description:** Coefficient of variation (Std / Mean)
- **Interpretation:** Lower values indicate more consistent evidence
- **ML Importance:** ⭐⭐⭐

#### `High_Host_Match_Ratio`
- **Type:** Float (0-1)
- **Description:** Proportion of records with Host_Match_Weight ≥ 1.2
- **Interpretation:** Indicates host specificity strength
- **ML Importance:** ⭐⭐⭐

#### `High_Evidence_Ratio`
- **Type:** Float (0-1)
- **Description:** Proportion of records with Evidence_Level ≥ 4
- **Interpretation:** Indicates evidence quality consistency
- **ML Importance:** ⭐⭐⭐

---

### Function Diversity Features (8)

#### `Function_Entropy`
- **Type:** Float (≥0)
- **Description:** Shannon entropy of function distribution
- **Formula:** -Σ(p_i × log2(p_i))
- **Interpretation:**
  - 0 = Single function (specialist)
  - High = Multiple functions (generalist)
- **ML Importance:** ⭐⭐⭐⭐

#### `Function_Dominance`
- **Type:** Float (0-1)
- **Description:** Proportion of records in most common function
- **Interpretation:** Higher values indicate functional specialization
- **ML Importance:** ⭐⭐⭐

#### `Unique_Function_Ratio`
- **Type:** Float (0-1)
- **Description:** Ratio of unique functions to total records
- **Interpretation:** Measures functional diversity per record
- **ML Importance:** ⭐⭐

#### `Has_Nutrition_Function`, `Has_Defense_Function`, `Has_Reproduction_Function`, `Has_Metabolism_Function`, `Has_Other_Function`
- **Type:** Binary (0/1)
- **Description:** Flags for major function categories
- **Keywords:**
  - Nutrition: nutrition, amino acid, vitamin, nutrient
  - Defense: defense, pathogen, antimicrobial, resistance, immune
  - Reproduction: fertility, reproduction, cytoplasmic incompatibility
  - Metabolism: metabolism, carbohydrate, cellulose, nitrogen, detoxification
- **Interpretation:** Indicates functional role categories
- **ML Importance:** ⭐⭐⭐

---

### Score Distribution Features (7)

#### `Score_Percentile_25`, `Score_Percentile_75`
- **Type:** Float
- **Description:** 25th and 75th percentiles of adjusted scores
- **Interpretation:** Characterizes score distribution
- **ML Importance:** ⭐⭐

#### `Score_IQR`
- **Type:** Float (≥0)
- **Description:** Interquartile range (P75 - P25)
- **Interpretation:** Robust measure of score variability
- **ML Importance:** ⭐⭐

#### `Score_Skewness`
- **Type:** Float
- **Description:** Distribution skewness
- **Interpretation:**
  - Positive = Right-skewed (few high scores)
  - Negative = Left-skewed (few low scores)
  - ~0 = Symmetric
- **ML Importance:** ⭐⭐

#### `Score_Range`
- **Type:** Float (≥0)
- **Description:** Max - Min score
- **Interpretation:** Total score variability
- **ML Importance:** ⭐⭐

#### `Rank_By_Abundance`
- **Type:** Integer (≥1)
- **Description:** Rank among all taxa by abundance (1 = highest)
- **Interpretation:** Relative abundance position
- **ML Importance:** ⭐⭐⭐⭐

#### `Rank_By_Score`
- **Type:** Integer (≥1)
- **Description:** Rank among all taxa by weighted average score (1 = highest)
- **Interpretation:** Relative quality position
- **ML Importance:** ⭐⭐⭐⭐

---

### Database Coverage Features (6)

#### `Total_DB_Records`
- **Type:** Integer (≥1)
- **Description:** Total number of database records matched
- **Interpretation:** Higher values indicate well-studied taxa
- **ML Importance:** ⭐⭐⭐

#### `Records_Per_Function`
- **Type:** Float (≥1)
- **Description:** Average records per function
- **Interpretation:** Indicates evidence depth per function
- **ML Importance:** ⭐⭐

#### `Host_Specificity_Index`
- **Type:** Integer (≥1)
- **Description:** Number of unique host contexts matched
- **Interpretation:**
  - 1 = Host specialist
  - High = Host generalist
- **ML Importance:** ⭐⭐⭐

#### `Evidence_Diversity`
- **Type:** Integer (1-5)
- **Description:** Number of unique evidence levels present
- **Interpretation:** Higher values indicate diverse evidence sources
- **ML Importance:** ⭐⭐

#### `Has_Genome_Data`
- **Type:** Binary (0/1)
- **Description:** Flag for genome availability (checks for "GISB" or "genome" in evidence)
- **Interpretation:** 1 = Genome sequenced
- **ML Importance:** ⭐⭐⭐

#### `Has_Top_Journal`
- **Type:** Binary (0/1)
- **Description:** Flag for top-tier journal publication
- **Journals:** Nature, Science, Cell, PNAS, ISME
- **Interpretation:** 1 = Published in high-impact journal
- **ML Importance:** ⭐⭐⭐

---

### Probability-Derived Features (5)

#### `Max_Function_Probability`
- **Type:** Float (0-1)
- **Description:** Highest probability among matched functions
- **Interpretation:** Peak prediction confidence
- **ML Importance:** ⭐⭐⭐⭐⭐

#### `Mean_Function_Probability`
- **Type:** Float (0-1)
- **Description:** Average probability across functions
- **Interpretation:** Overall prediction confidence
- **ML Importance:** ⭐⭐⭐⭐

#### `High_Prob_Function_Count`
- **Type:** Integer (≥0)
- **Description:** Number of functions with Probability > 0.7
- **Interpretation:** Count of high-confidence predictions
- **ML Importance:** ⭐⭐⭐

#### `Probability_Weighted_Score`
- **Type:** Float
- **Description:** Score weighted by function probabilities
- **Formula:** Σ(Probability × Score) / Σ(Probability)
- **Interpretation:** Confidence-adjusted quality metric
- **ML Importance:** ⭐⭐⭐⭐

#### `Confidence_Probability_Product`
- **Type:** Float (0-1)
- **Description:** Match_Level_Score × Max_Function_Probability
- **Interpretation:** Combined taxonomic and functional confidence
- **ML Importance:** ⭐⭐⭐⭐

---

### Interaction Features (8)

#### `Abundance_Score_Product`
- **Type:** Float
- **Description:** Relative_Abundance × Weighted_Avg_Score
- **Interpretation:** Combines abundance and quality
- **ML Importance:** ⭐⭐⭐⭐⭐

#### `Evidence_Host_Synergy`
- **Type:** Float
- **Description:** Mean_Evidence_Weight × Mean_Host_Match_Weight
- **Interpretation:** Synergistic effect of evidence and host match
- **ML Importance:** ⭐⭐⭐⭐

#### `Quality_Consistency_Index`
- **Type:** Float
- **Description:** (1 - Score_CV) × Mean_Quality_Score
- **Interpretation:** Quality adjusted for consistency
- **ML Importance:** ⭐⭐⭐⭐

#### `Comprehensive_Quality_Score`
- **Type:** Float
- **Description:** Weighted combination of all quality dimensions
- **Formula:** 0.3×Quality + 0.25×(Host×50) + 0.25×(Evidence×50) + 0.2×(Match×100)
- **Interpretation:** Holistic quality metric (0-100 scale)
- **ML Importance:** ⭐⭐⭐⭐⭐

#### `Symbiont_Potential_Index`
- **Type:** Float
- **Description:** Integrated metric for symbiont likelihood
- **Formula:** log10(RA+1)×20 + Score×0.5 + Prob×50 + (1-CV)×20
- **Interpretation:** **Primary composite metric for symbiont identification**
- **ML Importance:** ⭐⭐⭐⭐⭐ (Highest)

#### `Taxonomic_Confidence_Index`
- **Type:** Float
- **Description:** Match_Level_Score × Mean_Host_Match_Weight
- **Interpretation:** Combined taxonomic and host confidence
- **ML Importance:** ⭐⭐⭐

#### `Multi_Evidence_Bonus`
- **Type:** Float
- **Description:** Evidence_Diversity×10 + (Level5×20 + Level4×10)
- **Interpretation:** Bonus for multiple high-quality evidence types
- **ML Importance:** ⭐⭐⭐

#### `Specialization_Index`
- **Type:** Float
- **Description:** (1/(Entropy+1)) × (1/(Host_Specificity+1)) × 100
- **Interpretation:** Measures functional and host specialization
- **ML Importance:** ⭐⭐⭐

---

### Taxonomic Context Features (4)

#### `Genus_Level_Abundance`
- **Type:** Float (0-100)
- **Description:** Total abundance at genus level
- **Interpretation:** Genus-wide abundance (useful for genus-level matches)
- **ML Importance:** ⭐⭐⭐

#### `Species_Level_Resolution`
- **Type:** Binary (0/1)
- **Description:** Flag for species-level identification
- **Interpretation:** 1 = Species identified, 0 = Genus only
- **ML Importance:** ⭐⭐⭐

#### `Is_Known_Symbiont_Genus`
- **Type:** Binary (0/1)
- **Description:** Flag for well-known symbiont genera
- **Known Genera:** Wolbachia, Buchnera, Wigglesworthia, Sodalis, Blattabacterium, Candidatus, Spiroplasma, Rickettsia, Serratia, Hamiltonella
- **Interpretation:** 1 = Recognized symbiont genus
- **ML Importance:** ⭐⭐⭐⭐

#### `Cross_Host_Generalist`
- **Type:** Binary (0/1)
- **Description:** Flag for taxa found in multiple host orders
- **Interpretation:** 1 = Generalist (>3 hosts or has general match)
- **ML Importance:** ⭐⭐⭐

---

## Machine Learning Workflow

### Step 1: Load Feature Matrix
```python
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Load feature matrix
features = pd.read_csv('output_feature_matrix.tsv', sep='\t')

# Separate features and taxon names
X = features.drop('Symbiont_Taxon', axis=1)
taxa_names = features['Symbiont_Taxon']

print(f"Loaded {len(X)} samples with {len(X.columns)} features")
```

### Step 2: Create Labels (Manual Annotation Required)
```python
# Example: Manually label key symbionts
# You need to create this based on your biological knowledge
labels = pd.Series([
    1 if 'Wolbachia' in name or 'Buchnera' in name else 0
    for name in taxa_names
])

# Or load from external file
# labels = pd.read_csv('manual_labels.tsv', sep='\t')['Is_Key_Symbiont']
```

### Step 3: Train Random Forest
```python
# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, labels, test_size=0.2, random_state=42, stratify=labels
)

# Train model
rf = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    min_samples_split=5,
    random_state=42,
    class_weight='balanced'  # Handle imbalanced data
)

rf.fit(X_train, y_train)

# Evaluate
from sklearn.metrics import classification_report, roc_auc_score

y_pred = rf.predict(X_test)
y_prob = rf.predict_proba(X_test)[:, 1]

print(classification_report(y_test, y_pred))
print(f"ROC-AUC: {roc_auc_score(y_test, y_prob):.3f}")
```

### Step 4: Feature Importance Analysis
```python
# Get feature importances
importances = pd.DataFrame({
    'Feature': X.columns,
    'Importance': rf.feature_importances_
}).sort_values('Importance', ascending=False)

print("Top 10 Most Important Features:")
print(importances.head(10))

# Visualize
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
plt.barh(importances.head(20)['Feature'], importances.head(20)['Importance'])
plt.xlabel('Importance')
plt.title('Top 20 Feature Importances')
plt.tight_layout()
plt.savefig('feature_importance.png', dpi=300)
```

### Step 5: Predict on New Data
```python
# Predict on all taxa
all_predictions = rf.predict_proba(X)[:, 1]

# Create results dataframe
results = pd.DataFrame({
    'Symbiont_Taxon': taxa_names,
    'Symbiont_Probability': all_predictions,
    'Relative_Abundance': X['Relative_Abundance_Pct'],
    'Symbiont_Potential_Index': X['Symbiont_Potential_Index']
}).sort_values('Symbiont_Probability', ascending=False)

print("\nTop 10 Predicted Key Symbionts:")
print(results.head(10))

# Save results
results.to_csv('predicted_key_symbionts.tsv', sep='\t', index=False)
```

---

## Interpretation Guidelines

### Identifying Key Symbionts

#### High-Confidence Indicators
A taxon is likely a key symbiont if:
1. **Symbiont_Potential_Index > 100** ⭐⭐⭐
2. **Max_Function_Probability > 0.7** ⭐⭐⭐
3. **Is_Known_Symbiont_Genus = 1** ⭐⭐
4. **Mean_Host_Match_Weight > 1.2** ⭐⭐⭐
5. **Relative_Abundance_Pct > 1%** ⭐⭐
6. **Has_Evidence_Level_5 = 1 OR Has_Evidence_Level_4 = 1** ⭐⭐⭐

#### Example Decision Rule
```python
def is_likely_key_symbiont(row):
    score = 0
    if row['Symbiont_Potential_Index'] > 100: score += 3
    if row['Max_Function_Probability'] > 0.7: score += 3
    if row['Is_Known_Symbiont_Genus'] == 1: score += 2
    if row['Mean_Host_Match_Weight'] > 1.2: score += 3
    if row['Relative_Abundance_Pct'] > 1.0: score += 2
    if row['Has_Evidence_Level_5'] == 1 or row['Has_Evidence_Level_4'] == 1: score += 3

    return score >= 10  # Threshold: 10/16 points

features['Is_Likely_Key_Symbiont'] = features.apply(is_likely_key_symbiont, axis=1)
```

### Functional Role Interpretation

#### Nutrition Providers
- `Has_Nutrition_Function = 1`
- High `Function_Entropy` (multiple nutrition functions)
- High `Relative_Abundance_Pct` (>5%)

#### Defense Specialists
- `Has_Defense_Function = 1`
- Low `Function_Entropy` (specialized)
- High `Evidence_Host_Synergy`

#### Reproductive Manipulators
- `Has_Reproduction_Function = 1`
- Often: `Is_Known_Symbiont_Genus = 1` (e.g., Wolbachia)
- May have lower abundance

---

## Best Practices

### 1. Data Quality
- **Minimum Sample Size:** ≥20 taxa for meaningful ML training
- **Abundance Threshold:** Consider filtering taxa with <0.01% abundance
- **Taxonomic Resolution:** Prefer species-level identification when possible

### 2. Feature Selection
- **Start with all 64 features** for initial exploration
- **Use feature importance** to identify top predictors
- **Remove highly correlated features** (correlation > 0.95) if needed
- **Consider domain knowledge** when selecting features

### 3. Model Training
- **Handle class imbalance:** Use `class_weight='balanced'` or SMOTE
- **Cross-validation:** Use stratified k-fold (k=5 or 10)
- **Hyperparameter tuning:** Use GridSearchCV or RandomizedSearchCV
- **Ensemble methods:** Combine Random Forest with XGBoost or LightGBM

### 4. Validation
- **Biological validation:** Check predictions against literature
- **Host specificity:** Verify host-symbiont relationships
- **Functional coherence:** Ensure predicted functions make biological sense

---

## Troubleshooting

### Issue 1: All Features are NaN
**Cause:** No taxa matched in database
**Solution:** Check taxonomy format in input file (should be GTDB format)

### Issue 2: Single Feature Dominates
**Cause:** Feature scaling issues
**Solution:** Apply StandardScaler or MinMaxScaler before ML training

### Issue 3: Low Model Performance
**Possible Causes:**
- Insufficient training data (need more labeled examples)
- Class imbalance (too few positive examples)
- Feature redundancy (highly correlated features)

**Solutions:**
- Collect more labeled data
- Use SMOTE or class weighting
- Perform feature selection

### Issue 4: Scipy Import Error
**Cause:** scipy not installed
**Solution:** Install scipy (`pip install scipy`) or ignore (manual skewness calculation used as fallback)

---

## Example Analysis Script

```python
#!/usr/bin/env python3
"""
Complete workflow for identifying key symbionts using feature matrix
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Load data
features = pd.read_csv('output_feature_matrix.tsv', sep='\t')
X = features.drop('Symbiont_Taxon', axis=1)
taxa = features['Symbiont_Taxon']

# 2. Exploratory analysis
print("=== Feature Matrix Summary ===")
print(f"Samples: {len(X)}")
print(f"Features: {len(X.columns)}")
print(f"\nTop 10 Taxa by Symbiont_Potential_Index:")
print(features.nlargest(10, 'Symbiont_Potential_Index')[
    ['Symbiont_Taxon', 'Symbiont_Potential_Index', 'Relative_Abundance_Pct']
])

# 3. Feature correlation analysis
corr_matrix = X.corr()
plt.figure(figsize=(20, 16))
sns.heatmap(corr_matrix, cmap='coolwarm', center=0,
            square=True, linewidths=0.5, cbar_kws={"shrink": 0.8})
plt.title('Feature Correlation Matrix')
plt.tight_layout()
plt.savefig('feature_correlation.png', dpi=300)

# 4. Identify highly correlated features
high_corr = np.where(np.abs(corr_matrix) > 0.95)
high_corr_pairs = [(corr_matrix.index[x], corr_matrix.columns[y], corr_matrix.iloc[x, y])
                   for x, y in zip(*high_corr) if x != y and x < y]
print(f"\nHighly correlated feature pairs (>0.95): {len(high_corr_pairs)}")

# 5. Create simple rule-based labels (for demonstration)
# In practice, use manual annotation
labels = (
    (features['Symbiont_Potential_Index'] > 100) &
    (features['Max_Function_Probability'] > 0.7) &
    (features['Relative_Abundance_Pct'] > 0.5)
).astype(int)

print(f"\nRule-based labels: {labels.sum()} positive, {len(labels) - labels.sum()} negative")

# 6. Train model (if enough positive examples)
if labels.sum() >= 5:
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train Random Forest
    rf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')

    # Cross-validation
    cv_scores = cross_val_score(rf, X_scaled, labels, cv=5, scoring='roc_auc')
    print(f"\nCross-validation ROC-AUC: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

    # Train on all data
    rf.fit(X_scaled, labels)

    # Feature importance
    importances = pd.DataFrame({
        'Feature': X.columns,
        'Importance': rf.feature_importances_
    }).sort_values('Importance', ascending=False)

    print("\nTop 15 Most Important Features:")
    print(importances.head(15))

    # Predict probabilities
    predictions = rf.predict_proba(X_scaled)[:, 1]

    # Create results
    results = pd.DataFrame({
        'Symbiont_Taxon': taxa,
        'ML_Probability': predictions,
        'Rule_Based_Label': labels,
        'Symbiont_Potential_Index': features['Symbiont_Potential_Index'],
        'Relative_Abundance_Pct': features['Relative_Abundance_Pct'],
        'Max_Function_Probability': features['Max_Function_Probability']
    }).sort_values('ML_Probability', ascending=False)

    print("\nTop 10 Predicted Key Symbionts:")
    print(results.head(10))

    # Save results
    results.to_csv('key_symbiont_predictions.tsv', sep='\t', index=False)
    importances.to_csv('feature_importances.tsv', sep='\t', index=False)

    print("\n✅ Analysis complete! Check output files:")
    print("  - key_symbiont_predictions.tsv")
    print("  - feature_importances.tsv")
    print("  - feature_correlation.png")
else:
    print("\n⚠️  Not enough positive examples for ML training")
    print("   Consider manual annotation or adjust rule-based criteria")
```

---

## Additional Resources

- **Design Document:** `logs/feature_matrix_enhancement_v3.0_DESIGN.md`
- **Changelog:** `logs/feature_matrix_v3.0_CHANGELOG.md`
- **Update Summary:** `logs/feature_matrix_v3.0_UPDATE_SUMMARY.md`
- **GitHub Issues:** Report bugs or request features

---

**End of Usage Guide**
