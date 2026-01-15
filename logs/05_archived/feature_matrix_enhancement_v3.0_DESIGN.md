# Feature Matrix Enhancement v3.0 - Design Document

**Date:** 2026-01-08
**Author:** Claude Code Assistant
**Purpose:** Design comprehensive feature matrix for Random Forest training to identify key symbionts

---

## 1. Overview

### 1.1 Objective
Extract a high-dimensional numerical feature matrix from the prediction workflow to enable machine learning models (Random Forest, etc.) to identify key symbiont taxa based on multiple evidence dimensions.

### 1.2 Design Principles
1. **Robustness:** Handle edge cases including single-row input
2. **Efficiency:** Use numpy/pandas vectorized operations
3. **Backward Compatibility:** Do NOT modify existing Probability and Final_Score calculations
4. **Comprehensiveness:** Extract all relevant numerical features from the prediction process
5. **Interpretability:** Each feature should have clear biological/statistical meaning

---

## 2. Current Implementation Analysis (Lines 641-767)

### 2.1 Existing Features (26 features)
The current implementation extracts features at the **Symbiont_Taxon** level:

#### Basic Features (2)
- `Relative_Abundance_Pct`: Relative abundance percentage
- `Match_Level_Score`: Taxonomic match level (1.0=Species, 0.6=Genus)

#### Aggregated Score Features (6)
- `Function_Count`: Number of unique functions matched
- `Mean_Adjusted_Score`: Average adjusted score across all records
- `Max_Adjusted_Score`: Maximum adjusted score
- `Std_Adjusted_Score`: Standard deviation of adjusted scores
- `Mean_Quality_Score`: Average quality score
- `Max_Quality_Score`: Maximum quality score

#### Host Match Features (8)
- `Mean_Host_Match_Weight`: Average host match weight
- `Max_Host_Match_Weight`: Maximum host match weight
- `Has_Species_Match`: Binary flag for species-level host match
- `Has_Genus_Match`: Binary flag for genus-level host match
- `Has_Family_Match`: Binary flag for family-level host match
- `Has_Order_Match`: Binary flag for order-level host match
- `Has_General_Match`: Binary flag for general host match
- `Has_Mismatch`: Binary flag for host mismatch

#### Evidence Quality Features (6)
- `Mean_Evidence_Level`: Average evidence level (1-5)
- `Max_Evidence_Level`: Maximum evidence level
- `Mean_Evidence_Weight`: Average evidence weight
- `Has_Evidence_Level_5`: Binary flag for level 5 evidence
- `Has_Evidence_Level_4`: Binary flag for level 4 evidence
- `Has_Evidence_Level_3`: Binary flag for level 3 evidence

#### Composite Features (4)
- `Weighted_Avg_Score`: Quality-weighted average score
- `Score_CV`: Coefficient of variation (stability metric)
- `High_Host_Match_Ratio`: Proportion of high-quality host matches
- `High_Evidence_Ratio`: Proportion of high-quality evidence

### 2.2 Identified Gaps

The current implementation is good but missing several important dimensions:

1. **Function Diversity Metrics:** No quantification of functional breadth
2. **Rank-Based Features:** No information about relative importance ranking
3. **Database Coverage:** No metrics about how well-represented the taxon is
4. **Score Distribution:** Limited statistical characterization
5. **Interaction Features:** No cross-dimensional feature engineering
6. **Probability-Related Features:** Not leveraging the probability calculation
7. **Taxonomic Context:** No genus-level aggregation features
8. **Temporal/Spatial Features:** No journal quality or genome availability flags

---

## 3. Enhanced Feature Matrix Design

### 3.1 New Feature Categories

#### Category A: Function Diversity & Specificity (8 features)
- `Function_Entropy`: Shannon entropy of function distribution (diversity)
- `Function_Dominance`: Proportion of records in most common function
- `Unique_Function_Ratio`: Function_Count / Total_Records
- `Has_Nutrition_Function`: Binary flag for nutrition-related functions
- `Has_Defense_Function`: Binary flag for defense-related functions
- `Has_Reproduction_Function`: Binary flag for reproduction-related functions
- `Has_Metabolism_Function`: Binary flag for metabolism-related functions
- `Has_Other_Function`: Binary flag for "other" functions

#### Category B: Score Distribution & Ranking (7 features)
- `Score_Percentile_25`: 25th percentile of adjusted scores
- `Score_Percentile_75`: 75th percentile of adjusted scores
- `Score_IQR`: Interquartile range (robustness metric)
- `Score_Skewness`: Distribution skewness
- `Score_Range`: Max - Min score
- `Rank_By_Abundance`: Rank among all taxa by abundance
- `Rank_By_Score`: Rank among all taxa by weighted average score

#### Category C: Database Coverage & Confidence (6 features)
- `Total_DB_Records`: Total number of database records matched
- `Records_Per_Function`: Average records per function
- `Host_Specificity_Index`: Diversity of host contexts matched
- `Evidence_Diversity`: Number of unique evidence levels present
- `Has_Genome_Data`: Binary flag for genome availability
- `Has_Top_Journal`: Binary flag for top-tier journal publication

#### Category D: Probability-Derived Features (5 features)
- `Max_Function_Probability`: Highest probability among matched functions
- `Mean_Function_Probability`: Average probability across functions
- `High_Prob_Function_Count`: Number of functions with Probability > 0.7
- `Probability_Weighted_Score`: Score weighted by function probabilities
- `Confidence_Probability_Product`: Mean_Confidence × Max_Function_Probability

#### Category E: Interaction & Composite Features (8 features)
- `Abundance_Score_Product`: Relative_Abundance × Weighted_Avg_Score
- `Evidence_Host_Synergy`: Mean_Evidence_Weight × Mean_Host_Match_Weight
- `Quality_Consistency_Index`: (1 - Score_CV) × Mean_Quality_Score
- `Comprehensive_Quality_Score`: Weighted combination of all quality metrics
- `Symbiont_Potential_Index`: Integrated metric for symbiont likelihood
- `Taxonomic_Confidence_Index`: Match_Level_Score × Mean_Confidence
- `Multi_Evidence_Bonus`: Bonus for having multiple evidence types
- `Specialization_Index`: Function specificity × Host specificity

#### Category F: Taxonomic & Contextual Features (4 features)
- `Genus_Level_Abundance`: Total abundance at genus level
- `Species_Level_Resolution`: Binary flag for species-level identification
- `Is_Known_Symbiont_Genus`: Binary flag for well-known symbiont genera
- `Cross_Host_Generalist`: Binary flag for taxa found in multiple host orders

### 3.2 Total Feature Count
- **Current:** 26 features
- **New:** 38 features
- **Total:** 64 features

---

## 4. Implementation Strategy

### 4.1 Code Structure
```python
# Step 1: Collect intermediate data during prediction loop
# - Store function-level probabilities
# - Track database record counts
# - Collect journal and genome metadata

# Step 2: Build enhanced feature matrix
# - Compute all existing features (unchanged)
# - Add new feature categories A-F
# - Handle edge cases (single row, missing data)

# Step 3: Output enhanced matrix
# - Save to {base}_feature_matrix_enhanced.tsv
# - Maintain backward compatibility with existing output
```

### 4.2 Edge Case Handling
1. **Single Row Input:**
   - Rank features: Set to 1
   - Percentiles: Use min/max values
   - Std/CV: Set to 0
   - All features should compute without errors

2. **Missing Data:**
   - Use default values (0 for counts, 1.0 for weights)
   - Document assumptions in code comments

3. **Division by Zero:**
   - Add epsilon (1e-10) to denominators
   - Use numpy's safe division functions

### 4.3 Performance Optimization
- Pre-compute genus-level aggregations
- Use pandas groupby for efficient aggregation
- Vectorize all operations (no explicit loops)
- Cache function probability lookups

---

## 5. Feature Importance for Random Forest

### 5.1 Expected High-Importance Features
Based on biological knowledge:
1. `Relative_Abundance_Pct`: Core indicator
2. `Weighted_Avg_Score`: Integrated quality metric
3. `Mean_Host_Match_Weight`: Host specificity
4. `Max_Evidence_Level`: Evidence quality
5. `Function_Count`: Functional versatility
6. `Symbiont_Potential_Index`: Composite metric
7. `Max_Function_Probability`: Prediction confidence

### 5.2 Feature Engineering Rationale
- **Interaction terms:** Capture synergistic effects
- **Rank features:** Provide relative context
- **Diversity metrics:** Quantify functional breadth
- **Composite indices:** Integrate multiple dimensions

---

## 6. Output Format

### 6.1 File Naming
- **Enhanced Matrix:** `{base}_feature_matrix_enhanced.tsv`
- **Original Matrix:** `{base}_feature_matrix.tsv` (unchanged for compatibility)

### 6.2 Column Order
1. Identifier: `Symbiont_Taxon`
2. Basic features (2)
3. Existing aggregated features (24)
4. New features (38)
5. Total: 65 columns (1 ID + 64 features)

### 6.3 Data Types
- Binary flags: 0/1 (integer)
- Counts: Integer
- Ratios/Percentages: Float (rounded to 4 decimals)
- Scores: Float (rounded to 2 decimals)
- Indices: Float (rounded to 3 decimals)

---

## 7. Validation & Testing

### 7.1 Test Cases
1. **Normal Input:** 20+ taxa with diverse functions
2. **Single Row:** 1 taxon with 1 function
3. **Edge Case:** All taxa have same abundance
4. **Missing Data:** Some taxa lack host/evidence info

### 7.2 Validation Checks
- No NaN values in output
- All features within expected ranges
- Backward compatibility: existing outputs unchanged
- Performance: <5 seconds for 1000 taxa

---

## 8. Documentation Requirements

### 8.1 Code Comments
- Each feature: biological/statistical meaning
- Edge case handling: explicit documentation
- Formula: mathematical definition

### 8.2 User Documentation
- Feature glossary with descriptions
- Usage examples for ML training
- Interpretation guidelines

---

## 9. Future Enhancements (Out of Scope)

1. **Network Features:** Co-occurrence patterns
2. **Phylogenetic Features:** Evolutionary distance metrics
3. **Temporal Features:** Publication year trends
4. **Meta-Features:** Feature importance from previous models

---

## 10. Implementation Checklist

- [ ] Design review and approval
- [ ] Implement enhanced feature extraction
- [ ] Add robust error handling
- [ ] Test with edge cases
- [ ] Verify backward compatibility
- [ ] Create user documentation
- [ ] Update CHANGELOG
- [ ] Performance benchmarking

---

**End of Design Document**
