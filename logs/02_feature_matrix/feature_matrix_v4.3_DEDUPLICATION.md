# Feature Matrix v4.3 - Deduplication Update

**Date:** 2026-01-12
**Version:** v4.3
**Module:** `isympred/predictors/record_predictor.py`
**Update Type:** Bug Fix + Feature Enhancement

---

## 问题描述

### 原始问题
在 v4.2 版本中，特征矩阵存在严重的重复问题：
- **现象**：同一个 Taxon-Function 组合出现多次（例如 `Acinetobacter (sp.) - plant defense modulation` 出现 5 次）
- **原因**：代码直接遍历 `match_records` 表中的每一条记录，未对同一 Taxon-Function 组合进行去重
- **影响**：
  - 特征矩阵中有大量完全重复的行（数值完全相同）
  - 数据冗余率高达 51.7%（224 行 → 108 行去重后）
  - 无法反映数据库支持度信息
  - 影响机器学习模型训练效果

### 数据示例（v4.2 旧版本）
```
Taxon                    Function                  Relative_Abundance_Pct  ...
Acinetobacter (sp.)      plant defense modulation  6.7426                  ...
Acinetobacter (sp.)      plant defense modulation  6.7426                  ...  (重复)
Acinetobacter (sp.)      plant defense modulation  6.7426                  ...  (重复)
Acinetobacter (sp.)      plant defense modulation  6.7426                  ...  (重复)
Acinetobacter (sp.)      plant defense modulation  6.7426                  ...  (重复)
```

---

## 解决方案

### 核心策略：按 Taxon-Function 分组聚合

**实现逻辑**：
```python
# 按 Taxon-Function 分组聚合
grouped = taxa_df.groupby(['Symbiont_Taxon', 'Predicted_Function'])

for (taxon, function), group in grouped:
    # 聚合策略：
    # 1. 丰度、分类匹配：取第一条（同一 taxon 的所有记录相同）
    # 2. 宿主匹配、证据等级：取最大值（最佳匹配）
    # 3. 分数：取最大值（最高质量）
    # 4. 记录数：统计该组合有多少条数据库记录支持
```

### 聚合规则

| 特征类型 | 聚合方法 | 理由 |
|---------|---------|------|
| **丰度特征** (Relative_Abundance_Pct, Log_Abundance) | 取第一条 | 同一 taxon 的所有记录丰度相同 |
| **分类匹配** (Match_Level_Score) | 取第一条 | 同一 taxon 的分类等级固定 |
| **宿主匹配** (Host_Match_Weight) | 取最大值 (MAX) | 选择最佳宿主匹配 |
| **证据等级** (Evidence_Level) | 取最大值 (MAX) | 选择最高质量证据 |
| **综合分数** (Adjusted_Score) | 取最大值 (MAX) | 选择最高质量预测 |
| **分类学距离** (Taxonomic_Distance) | 取最小值 (MIN) | 选择最近的宿主 |
| **数据库支持度** (DB_Record_Count) | 计数 (COUNT) | 统计支持该预测的记录数 |

---

## 新增特征

### 1. Host_Match_Weight_Max (F4)
- **定义**：该 Taxon-Function 组合中最佳的宿主匹配权重
- **取值范围**：0.8 - 1.5
- **生物学意义**：反映该功能预测与用户宿主的最佳匹配程度

### 2. Host_Match_Weight_Mean (F5)
- **定义**：该 Taxon-Function 组合中所有记录的平均宿主匹配权重
- **取值范围**：0.8 - 1.5
- **生物学意义**：反映该功能预测的整体宿主特异性

### 3. Evidence_Level_Max (F6)
- **定义**：该 Taxon-Function 组合中最高的证据等级
- **取值范围**：1 - 5
- **生物学意义**：反映该功能预测的最佳证据质量

### 4. Evidence_Level_Mean (F7)
- **定义**：该 Taxon-Function 组合中所有记录的平均证据等级
- **取值范围**：1.0 - 5.0
- **生物学意义**：反映该功能预测的整体证据质量

### 5. DB_Record_Count (F11) ⭐ 核心新增
- **定义**：数据库中支持该 Taxon-Function 组合的记录数量
- **取值范围**：1 - N
- **生物学意义**：
  - 反映该功能预测的数据库支持度
  - 值越大，说明该功能在不同研究/宿主中被多次报道
  - 可用于评估预测的可靠性
- **示例**：
  - `DB_Record_Count = 1`：仅有 1 条数据库记录支持
  - `DB_Record_Count = 5`：有 5 条数据库记录支持（更可靠）

### 6. Taxonomic_Distance_Min (F13)
- **定义**：该 Taxon-Function 组合中最近的宿主分类学距离
- **取值范围**：0 (同种) - 6 (不同门), 999 (无法计算)
- **生物学意义**：反映该功能预测与用户宿主的进化距离

---

## 特征列表对比

### v4.2 (旧版本 - 10 个特征)
```
1. Relative_Abundance_Pct
2. Log_Abundance
3. Match_Level_Score
4. Host_Match_Weight          (单一值)
5. Evidence_Level             (单一值)
6. Bottleneck_Score
7. Adjusted_Score             (单一值)
8. Function_Support_Count
9. Rank_By_Abundance
10. Taxonomic_Distance        (单一值)
```

### v4.3 (新版本 - 13 个特征)
```
1. Relative_Abundance_Pct
2. Log_Abundance
3. Match_Level_Score
4. Host_Match_Weight_Max      (最大值) ⭐
5. Host_Match_Weight_Mean     (平均值) ⭐ 新增
6. Evidence_Level_Max         (最大值) ⭐
7. Evidence_Level_Mean        (平均值) ⭐ 新增
8. Bottleneck_Score
9. Adjusted_Score_Max         (最大值) ⭐
10. Function_Support_Count
11. DB_Record_Count           ⭐ 新增（核心）
12. Rank_By_Abundance
13. Taxonomic_Distance_Min    (最小值) ⭐
```

**关键改进**：
- ✅ 每个特征都有明确的聚合策略（MAX/MEAN/MIN/COUNT）
- ✅ 新增 `DB_Record_Count` 反映数据库支持度
- ✅ 区分最大值和平均值，提供更丰富的信息

---

## 效果验证

### 数据统计对比

| 指标 | v4.2 (旧版本) | v4.3 (新版本) | 改进 |
|-----|--------------|--------------|------|
| **总行数** | 224 | 108 | ✅ 减少 51.7% |
| **唯一 Taxon-Function 对** | 107 | 107 | ✅ 保持一致 |
| **重复行数** | 117 | 0 | ✅ 完全去重 |
| **特征数量** | 10 | 13 | ✅ 增加 3 个 |
| **数据冗余率** | 52.2% | 0% | ✅ 完全消除 |

### 示例对比

**旧版本（v4.2）**：
```
Taxon                    Function                  DB_Record_Count
Acinetobacter (sp.)      plant defense modulation  (无此特征)
Acinetobacter (sp.)      plant defense modulation  (无此特征)  重复
Acinetobacter (sp.)      plant defense modulation  (无此特征)  重复
Acinetobacter (sp.)      plant defense modulation  (无此特征)  重复
Acinetobacter (sp.)      plant defense modulation  (无此特征)  重复
```

**新版本（v4.3）**：
```
Taxon                    Function                  DB_Record_Count  Host_Match_Weight_Max  Evidence_Level_Max
Acinetobacter (sp.)      plant defense modulation  5                1.5                    3
```

**解读**：
- ✅ 5 条重复记录聚合为 1 行
- ✅ `DB_Record_Count = 5` 表示数据库中有 5 条记录支持该预测
- ✅ `Host_Match_Weight_Max = 1.5` 表示最佳宿主匹配为物种级
- ✅ `Evidence_Level_Max = 3` 表示最高证据等级为 3

---

## DB_Record_Count 分布分析

基于测试数据（Leptinotarsa decemlineata）：

| DB_Record_Count | Taxon-Function 对数量 | 占比 | 解释 |
|----------------|---------------------|------|------|
| 1 | 53 | 49.5% | 单一数据库记录支持 |
| 2 | 28 | 26.2% | 2 条记录支持 |
| 3 | 7 | 6.5% | 3 条记录支持 |
| 4 | 2 | 1.9% | 4 条记录支持 |
| 5 | 17 | 15.9% | 5 条记录支持（高支持度） |

**生物学意义**：
- 约 50% 的功能预测仅有单一数据库记录支持（需谨慎对待）
- 约 16% 的功能预测有 5 条记录支持（高可信度）
- `DB_Record_Count` 可作为预测可靠性的重要指标

---

## 代码变更位置

**文件**：`isympred/predictors/record_predictor.py`

**主要修改**：
1. **第 777-894 行**：特征矩阵生成逻辑
   - 从逐行遍历改为按 Taxon-Function 分组聚合
   - 添加聚合策略（MAX/MEAN/MIN/COUNT）
   - 新增 `DB_Record_Count` 等特征

2. **第 896-933 行**：输出信息更新
   - 更新特征列表说明
   - 添加聚合策略说明
   - 更新版本号为 v4.3

3. **第 763-767 行**：版本说明更新
   - 更新设计说明为 "v4.3 - aggregated"
   - 强调去重和聚合策略

---

## 使用建议

### 1. 机器学习特征选择
推荐使用以下特征组合：

**核心特征（必选）**：
- `Relative_Abundance_Pct` - 丰度
- `Host_Match_Weight_Max` - 宿主匹配
- `Evidence_Level_Max` - 证据质量
- `DB_Record_Count` - 数据库支持度 ⭐
- `Adjusted_Score_Max` - 综合质量分数

**辅助特征（可选）**：
- `Host_Match_Weight_Mean` - 平均宿主匹配（评估一致性）
- `Evidence_Level_Mean` - 平均证据质量（评估一致性）
- `Function_Support_Count` - 功能支持度
- `Taxonomic_Distance_Min` - 宿主距离

### 2. 数据过滤建议
根据 `DB_Record_Count` 进行质量控制：

```python
# 高可信度预测（推荐用于下游分析）
high_confidence = feature_df[feature_df['DB_Record_Count'] >= 3]

# 中等可信度预测（需结合其他证据）
medium_confidence = feature_df[feature_df['DB_Record_Count'] == 2]

# 低可信度预测（需谨慎对待）
low_confidence = feature_df[feature_df['DB_Record_Count'] == 1]
```

### 3. 质量评估指标
综合评估预测质量：

```python
# 质量分数 = (DB_Record_Count × 0.3) + (Host_Match_Weight_Max × 0.3) +
#            (Evidence_Level_Max × 0.2) + (Adjusted_Score_Max × 0.2)
quality_score = (
    feature_df['DB_Record_Count'] * 0.3 +
    feature_df['Host_Match_Weight_Max'] * 0.3 +
    feature_df['Evidence_Level_Max'] * 0.2 +
    feature_df['Adjusted_Score_Max'] * 0.2
)
```

---

## 向后兼容性

**⚠️ 不兼容变更**：
- 特征列名变更（例如 `Host_Match_Weight` → `Host_Match_Weight_Max`）
- 特征数量变化（10 → 13）
- 行数显著减少（去重后）

**迁移建议**：
- 如果使用旧版本特征矩阵训练的模型，需要重新训练
- 更新特征提取代码以适配新的列名
- 利用新增的 `DB_Record_Count` 特征提升模型性能

---

## 测试结果

**测试数据**：`tests/data/test_data.tsv`
**宿主**：Leptinotarsa decemlineata (Colorado potato beetle)

**输出文件**：
- `tmp/test_output_v4.3_functions.tsv` - 功能汇总表
- `tmp/test_output_v4.3_match_records.tsv` - 匹配记录明细（223 条）
- `tmp/test_output_v4.3_feature_matrix.tsv` - 特征矩阵（108 条，无重复）✅

**验证命令**：
```bash
# 检查重复（应无输出）
awk -F'\t' 'NR>1 {print $1"\t"$2}' tmp/test_output_v4.3_feature_matrix.tsv | sort | uniq -c | awk '$1 > 1'

# 统计 DB_Record_Count 分布
awk -F'\t' 'NR>1 {print $13}' tmp/test_output_v4.3_feature_matrix.tsv | sort -n | uniq -c
```

---

## 总结

### 主要改进
1. ✅ **完全消除重复**：每个 Taxon-Function 组合仅保留一行
2. ✅ **新增数据库支持度特征**：`DB_Record_Count` 反映预测可靠性
3. ✅ **区分最大值和平均值**：提供更丰富的质量评估维度
4. ✅ **数据冗余率降低 51.7%**：提升数据质量和模型训练效率
5. ✅ **保持生物学意义**：所有聚合策略符合生物学逻辑

### 科学价值
- 更准确地反映数据库支持度
- 更合理的特征聚合策略
- 更适合机器学习模型训练
- 更清晰的预测质量评估

### 下一步工作
- [ ] 基于新特征矩阵训练随机森林模型
- [ ] 评估 `DB_Record_Count` 对预测准确性的影响
- [ ] 开发基于多特征的综合质量评分系统
- [ ] 添加特征重要性分析工具

---

**更新人员**：Claude (AI Assistant)
**审核状态**：待用户确认
**相关文档**：
- `logs/s16_predictor_CHANGELOG.md` - 完整更新历史
- `logs/s16_predictor_v2.1_PROBABILITY.md` - 概率计算逻辑
