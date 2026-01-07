# S16 Predictor 使用指南 (Quick Start)

## 📖 简介

`s16_predictor.py` 是基于 16S rRNA 扩增子数据预测昆虫共生菌功能的工具。

**v2.0 新特性**:
- ✨ 宿主匹配打分系统（Host-Context Scoring）
- ✨ 证据等级整合（Evidence-Level Weighting）
- ✨ 更准确的功能预测结果

---

## 🚀 快速开始

### 基础用法（不指定宿主）

```bash
python isympred/predictors/s16_predictor.py \
    -i your_otu_table.tsv \
    -d isympred/database/symbiont_record/record_db.tsv \
    -o output_results.tsv
```

### 推荐用法（指定宿主）

```bash
python isympred/predictors/s16_predictor.py \
    -i your_otu_table.tsv \
    -d isympred/database/symbiont_record/record_db.tsv \
    -o output_results.tsv \
    --host "Apis mellifera"
```

---

## 📝 参数说明

| 参数 | 必需 | 说明 | 示例 |
|------|------|------|------|
| `-i, --input` | ✅ | 输入 OTU 表（TSV 格式） | `otu_table.tsv` |
| `-d, --db` | ✅ | 共生菌数据库路径 | `record_db.tsv` |
| `-o, --output` | ✅ | 输出文件路径 | `results.tsv` |
| `--host` | ❌ | 宿主物种拉丁名 | `"Drosophila melanogaster"` |
| `--host-db` | ❌ | 宿主分类数据库路径 | `insect_taxonomy.db` |

**注意**:
- 如果指定 `--host` 但不指定 `--host-db`，程序会自动查找默认路径
- 宿主名称必须使用标准拉丁学名（带引号）

---

## 📊 输入文件格式

### OTU 表格式（TSV）

```
Taxon	Abundance
d__Bacteria; p__Pseudomonadota; c__Gammaproteobacteria; o__Enterobacterales; f__Enterobacteriaceae; g__Buchnera; s__Buchnera aphidicola	15000
d__Bacteria; p__Pseudomonadota; c__Gammaproteobacteria; o__Enterobacterales; f__Enterobacteriaceae; g__Serratia; s__Serratia symbiotica	8500
d__Bacteria; p__Pseudomonadota; c__Alphaproteobacteria; o__Rickettsiales; f__Anaplasmataceae; g__Wolbachia; s__*	3200
```

**要求**:
- 第一列: `Taxon`（QIIME 2 格式分类字符串）
- 第二列: `Abundance`（reads 数量）
- 制表符分隔（TSV）

---

## 📈 输出文件说明

### 1. 功能预测汇总表 (`output_results.tsv`)

**主要列**:
- `Function`: 预测的功能类别
- `Final_Score_Sum`: 最终总分（整合所有权重）
- `Total_RA_Pct`: 该功能的总相对丰度（%）
- `Mean_Host_Match`: 平均宿主匹配权重（1.0 = 通用，>1.0 = 宿主特异性）
- `Mean_Evidence_Weight`: 平均证据等级权重（>1.0 = 高质量证据）
- `Taxa_Count`: 贡献该功能的分类单元数量
- `Dominant_Contributor`: 主要贡献者

**示例**:
```
Function	Final_Score_Sum	Total_RA_Pct	Mean_Host_Match	Mean_Evidence_Weight	Taxa_Count
Nutrition	450.2	25.3	1.35	1.42	12
Defense	320.5	18.7	1.15	1.28	8
```

### 2. 潜在共生菌明细表 (`output_results_potential_symbionts.tsv`)

**主要列**:
- `Symbiont_Taxon`: 共生菌分类名称
- `Predicted_Function`: 预测功能
- `Final_Score`: 最终得分
- `Base_Score`: 基础得分（仅考虑丰度和分类匹配）
- `Host_Match_Weight`: 宿主匹配权重（0.8-1.5）
- `Host_Match_Level`: 宿主匹配等级（Species/Genus/Family/Order/General/Mismatch）
- `Evidence_Level`: 证据等级（1-5）
- `Evidence_Weight`: 证据等级权重（0.8-1.5）

**示例**:
```
Symbiont_Taxon	Predicted_Function	Final_Score	Host_Match_Level	Evidence_Level
Buchnera aphidicola	Nutrition	234.5	Species	5
Wolbachia (sp.)	Reproduction	89.3	General	3
```

---

## 🎯 使用场景

### 场景 1: 探索性分析（不知道宿主）

```bash
python s16_predictor.py -i sample.tsv -d record_db.tsv -o results.tsv
```

**适用于**:
- 初步筛选潜在功能
- 宿主信息未知
- 混合样本分析

### 场景 2: 宿主特异性分析（推荐）

```bash
python s16_predictor.py -i sample.tsv -d record_db.tsv -o results.tsv \
    --host "Acyrthosiphon pisum"
```

**适用于**:
- 研究特定宿主的共生菌功能
- 需要区分宿主特异性和通用功能
- 提高预测准确性

### 场景 3: 批量分析多个样本

```bash
for sample in sample1 sample2 sample3; do
    python s16_predictor.py \
        -i ${sample}_otu.tsv \
        -d record_db.tsv \
        -o ${sample}_results.tsv \
        --host "Apis mellifera"
done
```

---

## 📊 结果解读

### 如何判断预测可信度？

**高可信度预测**:
- ✅ `Final_Score_Sum` > 200
- ✅ `Mean_Host_Match` > 1.2（宿主特异性强）
- ✅ `Mean_Evidence_Weight` > 1.3（高质量文献支持）
- ✅ `Evidence_Level` = 4 或 5（有基因组数据）

**中等可信度预测**:
- ⚠️ `Final_Score_Sum` = 100-200
- ⚠️ `Mean_Host_Match` = 1.0-1.2
- ⚠️ `Mean_Evidence_Weight` = 1.0-1.3
- ⚠️ `Evidence_Level` = 2 或 3

**低可信度预测**:
- ❌ `Final_Score_Sum` < 100
- ❌ `Mean_Host_Match` < 1.0（宿主不匹配）
- ❌ `Evidence_Level` = 1

### Host_Match_Level 含义

| 等级 | 含义 | 可信度 |
|------|------|--------|
| **Species** | 物种级精确匹配 | ⭐⭐⭐⭐⭐ |
| **Genus** | 属级匹配 | ⭐⭐⭐⭐ |
| **Family** | 科级匹配 | ⭐⭐⭐ |
| **Order** | 目级匹配 | ⭐⭐ |
| **General** | 通用记录（无宿主特异性） | ⭐ |
| **Mismatch** | 宿主不匹配 | ⚠️ 需谨慎解读 |

---

## 🔍 常见问题

### Q1: 为什么指定宿主后分数变低了？

**A**: 这是正常现象。宿主匹配打分会降低不匹配记录的权重（×0.8），提高匹配记录的权重（×1.1-1.5）。总体分数可能降低，但**预测更准确**。

### Q2: 宿主名称找不到怎么办？

**A**:
1. 确认使用标准拉丁学名（如 `"Apis mellifera"` 而非 `"honeybee"`）
2. 检查宿主是否在昆虫纲（Insecta）范围内
3. 如果宿主不在数据库中，程序会警告并继续运行（不使用宿主打分）

### Q3: Evidence_Level 是如何计算的？

**A**: 基于三个因素：
- Record Type = "Symbiont": +1 分
- 有 Genome ID: +2 分
- 顶级期刊（Nature/Science/Cell 等）: +1 分
- 总分范围: 1-5

### Q4: 如何选择合适的阈值？

**A**: 建议根据研究目的调整：
- **保守策略**（高精度）: `Final_Score_Sum` > 200, `Evidence_Level` ≥ 4
- **平衡策略**（推荐）: `Final_Score_Sum` > 100, `Evidence_Level` ≥ 3
- **宽松策略**（高召回）: `Final_Score_Sum` > 50, `Evidence_Level` ≥ 2

---

## 📚 更多信息

- **详细更新日志**: 查看 `s16_predictor_CHANGELOG.md`
- **算法原理**: 查看 CHANGELOG 中的"评分公式"部分
- **数据库构建**: 查看 `database/format_database_record.py`

---

## 💡 最佳实践

1. **始终指定宿主**（如果已知）以提高预测准确性
2. **关注 Evidence_Level ≥ 4 的记录**（有基因组支持）
3. **结合 Host_Match_Level 和 Evidence_Level 综合判断**
4. **对于 Mismatch 的记录，需要额外验证**
5. **使用明细表追溯每个预测的来源**

---

**最后更新**: 2026-01-07
