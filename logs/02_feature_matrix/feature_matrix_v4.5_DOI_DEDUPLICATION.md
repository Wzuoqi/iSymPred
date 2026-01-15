# Feature Matrix v4.5 - DOI-Based Literature Count

**Date:** 2026-01-13
**Version:** v4.5
**Module:** `isympred/predictors/record_predictor.py`
**Update Type:** Feature Optimization (Scientific Accuracy Improvement)

---

## 更新概述

### 核心改进
将 `DB_Record_Count`（数据库记录数）优化为 `DB_Literature_Count`（文献数量），**基于 DOI 去重统计**，更准确地反映文献支持度。

##问题背景
在 v4.4 中，`DB_Record_Count` 统计的是数据库记录数。但同一篇文献可能在不同宿主中报道了同一个 Taxon-Function 组合，这会导致：
- **虚高问题**：同一篇文献的多条记录被重复计数
- **不准确**：无法真实反映有多少篇独立文献支持该预测
- **误导性**：多宿主研究会人为提高支持度

### 解决方案
**基于 DOI 去重**：同一篇文献（相同 DOI）在不同宿主中的记录只算 1 次。

---

## 实现细节

### 代码逻辑

```python
# v4.4 (旧版本) - 简单计数记录数
db_record_count = len(group)  # 所有记录数

# v4.5 (新版本) - 基于 DOI 去重
dois = []
for _, rec in group.iterrows():
    doi = str(rec.get('DB_Evidence', '')).strip()
    # 过滤空值和无效 DOI
    if doi and doi.lower() not in ['', 'nan', 'none', 'n/a', '-']:
        dois.append(doi)

# 去重统计唯一 DOI 数量
unique_dois = set(dois)
db_literature_count = len(unique_dois) if unique_dois else len(group)
# 如果没有有效 DOI，则回退到记录数（保守估计）
```

### 数据来源
- **DOI 字段**：`DB_Evidence` 列（来自数据库的 `evidence` 字段）
- **格式示例**：`10.1038/s41467-024-54439-z`
- **去重策略**：使用 Python `set()` 对 DOI 去重

### 回退机制
如果某个 Taxon-Function 组合的所有记录都没有有效 DOI，则回退到记录数统计（保守估计）。

---

## 效果对比

### 案例分析

#### 案例 1: Acinetobacter (sp.) - plant defense modulation
```
v4.4 (记录数): 5 条记录
v4.5 (文献数): 1 篇文献

解释：
- 数据库中有 5 条记录
- 但这 5 条记录都来自同一篇文献（相同 DOI）
- 该文献在 5 个不同宿主中报道了这个功能
- v4.5 正确识别为 1 篇文献支持
```

#### 案例 2: Enterobacter (sp.) - plant defense modulation
```
v4.4 (记录数): 5 条记录
v4.5 (文献数): 2 篇文献

解释：
- 数据库中有 5 条记录
- 这 5 条记录来自 2 篇不同的文献（2 个不同 DOI）
- 第 1 篇文献：3 条记录（3 个宿主）
- 第 2 篇文献：2 条记录（2 个宿主）
- v4.5 正确识别为 2 篇文献支持
```

#### 案例 3: Sphingobacterium (sp.) - plant defense modulation
```
v4.4 (记录数): 5 条记录
v4.5 (文献数): 1 篇文献

解释：
- 同案例 1，所有记录来自同一篇文献
```

---

## 统计对比

### 分布变化

| 支持度 | v4.4 (记录数) | v4.5 (文献数) | 变化 |
|-------|--------------|--------------|------|
| 1 | 53 (49.5%) | 96 (89.7%) | ✅ +43 |
| 2 | 28 (26.2%) | 10 (9.3%) | ⬇️ -18 |
| 3 | 7 (6.5%) | 0 (0%) | ⬇️ -7 |
| 4 | 2 (1.9%) | 1 (0.9%) | ⬇️ -1 |
| 5 | 17 (15.9%) | 0 (0%) | ⬇️ -17 |
| **总计** | **107** | **107** | ✅ 保持 |

### 关键指标

| 指标 | v4.4 | v4.5 | 改进 |
|-----|------|------|------|
| **平均支持度** | 2.08 | 1.12 | ✅ -46% (更真实) |
| **单一支持比例** | 49.5% | 89.7% | ✅ +40.2% (更准确) |
| **多重支持比例** | 50.5% | 10.3% | ✅ -40.2% (去除虚高) |
| **最大支持度** | 5 | 4 | ✅ 去除虚高 |

---

## 科学意义

### 1. 更准确的文献支持度
**问题**：v4.4 的 `DB_Record_Count` 会因为多宿主研究而虚高
```
示例：一篇文献研究了 5 个宿主
v4.4: 计数为 5（误导）
v4.5: 计数为 1（准确）
```

**改进**：v4.5 的 `DB_Literature_Count` 真实反映有多少篇独立文献支持该预测

### 2. 避免多宿主研究的偏差
**问题**：多宿主研究会人为提高某些功能的支持度
```
场景：某功能在 10 个宿主中被同一篇文献报道
v4.4: 支持度 = 10（虚高）
v4.5: 支持度 = 1（真实）
```

**改进**：消除多宿主研究带来的统计偏差

### 3. 更公平的功能比较
**问题**：不同功能的研究策略不同
- 功能 A：10 篇文献，每篇研究 1 个宿主 → v4.4 计数 10
- 功能 B：1 篇文献，研究 10 个宿主 → v4.4 计数 10

**改进**：v4.5 正确识别功能 A 有 10 篇文献支持，功能 B 只有 1 篇

### 4. 符合科学评估标准
在科学研究中，文献支持度的评估标准是：
- ✅ **独立研究的数量**（不同文献）
- ❌ **不是记录的数量**（同一文献的多条记录）

v4.5 的 `DB_Literature_Count` 符合科学评估标准。

---

## 生物学案例

### 案例：Wolbachia 的生殖调控功能

**背景**：
- Wolbachia 是一种广泛分布的内共生菌
- 在多种昆虫中都能引起生殖调控（细胞质不亲和）
- 可能有一篇综述文献报道了 20 个宿主的案例

**v4.4 的问题**：
```
数据库记录：
- Wolbachia - reproductive manipulation - Host A (DOI: 10.1038/xxx)
- Wolbachia - reproductive manipulation - Host B (DOI: 10.1038/xxx)
- Wolbachia - reproductive manipulation - Host C (DOI: 10.1038/xxx)
- ... (共 20 条记录，同一 DOI)

DB_Record_Count = 20 ❌ (虚高)
```

**v4.5 的改进**：
```
去重后：
- 唯一 DOI: 10.1038/xxx

DB_Literature_Count = 1 ✅ (准确)
```

**科学解释**：
- 虽然有 20 条记录，但它们都来自同一篇文献
- 这只能算作 1 篇文献的支持，而非 20 篇
- v4.5 正确反映了真实的文献支持度

---

## 特征列名变更

### v4.4 → v4.5

| v4.4 | v4.5 | 变更原因 |
|------|------|---------|
| `DB_Record_Count` | `DB_Literature_Count` | 更准确反映含义 |

**命名理由**：
- `Record` → `Literature`：强调统计的是文献数，而非记录数
- 更符合科学术语习惯
- 避免误解

---

## 使用建议

### 1. 文献支持度阈值

**基于 v4.5 的新阈值**：
```python
# 高可信度：至少 2 篇独立文献支持
high_confidence = feature_df[feature_df['DB_Literature_Count'] >= 2]

# 中等可信度：1 篇文献支持
medium_confidence = feature_df[feature_df['DB_Literature_Count'] == 1]

# 低可信度：无有效文献（回退到记录数）
# 注意：如果 DB_Literature_Count 很大但都是同一 DOI，v4.5 会正确识别为 1
```

### 2. 质量评分更新

**v4.4 的质量评分**：
```python
quality_score = (
    feature_df['DB_Record_Count'] * 0.3 +  # 记录数权重
    feature_df['Host_Match_Weight_Max'] * 0.3 +
    feature_df['Evidence_Level_Max'] * 0.2 +
    feature_df['Adjusted_Score_Max'] * 0.2
)
```

**v4.5 的质量评分（推荐）**：
```python
quality_score = (
    feature_df['DB_Literature_Count'] * 0.4 +  # 文献数权重提升
    feature_df['Host_Match_Weight_Max'] * 0.3 +
    feature_df['Evidence_Level_Max'] * 0.2 +
    feature_df['Adjusted_Score_Max'] * 0.1
)
```

**理由**：
- 文献数更可靠，权重从 0.3 提升到 0.4
- Adjusted_Score_Max 已整合多个因素，权重降低到 0.1

### 3. 机器学习特征重要性预测

**预测特征重要性排序（v4.5）**：

| 排名 | 特征 | 预测重要性 | 理由 |
|-----|------|-----------|------|
| 1 | **DB_Literature_Count** | ⭐⭐⭐⭐⭐ | 文献支持度是最可靠的指标 |
| 2 | **Host_Match_Weight_Max** | ⭐⭐⭐⭐⭐ | 宿主特异性是核心创新点 |
| 3 | **Evidence_Level_Max** | ⭐⭐⭐⭐ | 证据质量影响可信度 |
| 4 | **Log_Abundance** | ⭐⭐⭐⭐ | 丰度是基础指标 |
| 5 | **Adjusted_Score_Max** | ⭐⭐⭐ | 综合指标 |
| 6 | **Match_Level_Score** | ⭐⭐⭐ | 分类置信度 |
| 7 | **Rank_By_Abundance** | ⭐⭐ | 相对排名 |

**变化**：`DB_Literature_Count` 的重要性可能进一步提升（因为更准确）

---

## 向后兼容性

### ⚠️ 不兼容变更

**列名变化**：
```
v4.4: DB_Record_Count
v4.5: DB_Literature_Count
```

**数值变化**：
```
v4.4: 平均值 2.08
v4.5: 平均值 1.12 (降低 46%)
```

### 迁移指南

**如果使用 v4.4 训练的模型**：
1. ✅ **推荐**：使用 v4.5 重新训练模型（更准确的特征）
2. ⚠️ **不推荐**：继续使用 v4.4 模型（特征含义已变化）

**如果需要兼容旧版本**：
```python
# 无法从 v4.5 恢复 v4.4 的 DB_Record_Count
# 因为 DOI 去重是不可逆的
# 建议：保留 v4.4 的输出文件作为备份
```

---

## 测试结果

### 数据统计

**测试数据**：`tests/data/test_data.tsv`
**宿主**：Leptinotarsa decemlineata (Colorado potato beetle)

| 指标 | v4.4 | v4.5 | 变化 |
|-----|------|------|------|
| 唯一 Taxon-Function 对 | 107 | 107 | ✅ 保持一致 |
| 平均支持度 | 2.08 | 1.12 | ✅ -46% |
| 单一支持比例 | 49.5% | 89.7% | ✅ +40.2% |
| 最大支持度 | 5 | 4 | ✅ 去除虚高 |

### 验证命令

```bash
# 查看 DB_Literature_Count 分布
awk -F'\t' 'NR>1 {print $8}' tmp/test_output_v4.5_feature_matrix.tsv | sort -n | uniq -c

# 对比 v4.4 和 v4.5
paste <(awk -F'\t' 'NR>1 {print $1"\t"$2"\t"$8}' tmp/test_output_v4.4_feature_matrix.tsv) \
      <(awk -F'\t' 'NR>1 {print $8}' tmp/test_output_v4.5_feature_matrix.tsv) | \
      awk '$3 != $4 {print $1"\t"$2"\tv4.4:"$3"\tv4.5:"$4}' | head -10
```

---

## 实际案例验证

### 示例：plant defense modulation 功能

| Taxon | v4.4 记录数 | v4.5 文献数 | 差异 | 解释 |
|-------|-----------|-----------|------|------|
| Acinetobacter (s | -4 | 5 条记录来自 1 篇文献 |
| Enterobacter (sp.) | 5 | 2 | -3 | 5 条记录来自 2 篇文献 |
| Sphingobacterium (sp.) | 5 | 1 | -4 | 5 条记录来自 1 篇文献 |
| Stenotrophomonas (sp.) | 5 | 1 | -4 | 5 条记录来自 1 篇文献 |
| Pseudomonas (sp.) | 5 | 1 | -4 | 5 条记录来自 1 篇文献 |

**发现**：
- 大部分 "5 条记录" 的情况实际上只有 1 篇文献支持
- 只有 Enterobacter 有 2 篇独立文献支持
- v4.5 正确识别了真实的文献支持度

---

## 总结

### 主要改进

1. ✅ **科学准确性**：基于 DOI 去重，真实反映文献支持度
2. ✅ **消除虚高**：同一文献的多条记录只算 1 次
3. ✅ **公平比较**：不同功能的支持度可公平比较
4. ✅ **符合标准**：符合科学研究的文献评估标准
5. ✅ **更可靠**：文献数比记录数更可靠

### 科学价值

- **更准确的可靠性评估**：文献数是独立研究的数量
- **避免多宿主研究偏差**：消除统计偏差
- **提升特征质量**：更可靠的特征用于机器学习
- **符合科学规范**：与文献综述的评估标准一致

### 下一步工作

- [ ] 基于 v4.5 特征矩阵训练随机森林模型
- [ ] 评估 `DB_Literature_Count` 的特征重要性
- [ ] 与 v4.4 模型性能对比
- [ ] 开发文献支持度可视化工具
- [ ] 添加文献来源追溯功能

---

**更新人员**：Claude (AI Assistant)
**审核状态**：待用户确认
**相关文档**：
- `logs/feature_matrix_v4.4_STREAMLINED.md` - v4.4 特征精简
- `logs/feature_matrix_v4.3_DEDUPLICATION.md` - v4.3 去重更新
- `logs/iSymPred_DESIGN_OVERVIEW.md` - 软件设计概览
