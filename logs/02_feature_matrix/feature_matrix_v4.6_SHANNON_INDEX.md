# Feature Matrix v4.6 - Shannon Index (α-Diversity)

**Date:** 2026-01-13
**Version:** v4.6
**Module:** `isympred/predictors/record_predictor.py`
**Update Type:** Feature Enhancement (Community Context)

---

## 更新概述

### 核心改进
新增 **Shannon Index** 特征，用于反映微生物组的 **α 多样性**（群落均匀度），为功能预测提供群落级别的上下文信息。

### 特征数量
- v4.5: 7 个特征
- v4.6: 8 个特征（新增 Shannon_Index）

---

## Shannon Index 简介

### 定义
Shannon Index（香农指数）是生态学中最常用的α多样性指标，用于衡量群落的物种多样性和均匀度。

### 计算公式
```
Shannon Index (H') = -Σ(pi × ln(pi))

其中:
- pi = 第 i 个物种的相对丰度
- ln = 自然对数
- Σ = 对所有物种求和
```

### 取值范围
- **最小值**: 0（只有一个物种，完全不均匀）
- **最大值**: ln(S)，其中 S 是物种数（所有物种丰度完全相等）
- **典型值**: 1.5 - 3.5（大多数自然群落）

### 生物学意义
- **高 Shannon Index (> 3.0)**：群落多样性高，物种分布均匀
- **中等 Shannon Index (2.0 - 3.0)**：群落多样性中等
- **低 Shannon Index (< 2.0)**：群落多样性低，少数物种占主导

---

## 为什么添加 Shannon Index？

### 1. 群落上下文影响功能表达
**生物学假设**：
- 高多样性群落：竞争激烈，共生菌功能表达可能受抑制
- 低多样性群落：少数优势菌主导，功能表达可能更强

**示例**：
```
场景 A: Shannon Index = 1.5 (低多样性)
- Wolbachia 占 80% 丰度（优势菌）
- 其生殖调控功能可能表达强烈

场景 B: Shannon Index = 3.5 (高多样性)
- Wolbachia 占 5% 丰度（非优势菌）
- 其功能表达可能受其他菌竞争抑制
```

### 2. 补充个体级别特征
**现有特征**：主要关注单个 Taxon-Function 对
- Log_Abundance：单个菌的丰度
- Match_Level_Score：单个菌的分类置信度
- Host_Match_Weight_Max：单个菌的宿主匹配

**Shannon Index**：提供群落级别的背景信息
- 反映整个微生物组的结构
- 所有 Taxon-Function 对共享同一个值
- 补充个体特征，提供生态学上下文

### 3. 机器学习特征工程
**特征交互潜力**：
```python
# 可能的交互特征
Interaction_1 = Log_Abundance × Shannon_Index
# 解释：在高多样性群落中，高丰度菌的功能可能更重要

Interaction_2 = (1 / Shannon_Index) × Adjusted_Score_Max
# 解释：在低多样性群落中，高质量预测的可信度更高
```

### 4. 跨样本比较
**应用场景**：
- 比较不同处理组的微生物组功能
- 评估多样性对共生菌功能的影响
- 识别多样性依赖的功能模式

---

## 实现细节

### 代码逻辑

```python
# 在 predict() 函数开始时计算 Shannon Index
shannon_index = 0.0
for _, row in input_df.iterrows():
    abundance = float(row['Abundance'])
    if abundance > 0:
        pi = abundance / total_reads
        shannon_index += -pi * np.log(pi)

print(f"Shannon Index (α-diversity): {shannon_index:.4f}")

# 在特征矩阵中添加 Shannon Index
feature_rows.append({
    'Taxon': taxon,
    'Function': function,
    # ... 其他特征 ...
    'Shannon_Index': round(shannon_index, 4),  # 新增
    'Rank_By_Abundance': rank_by_abundance
})
```

### 特征属性
- **类型**：连续型特征
- **取值范围**：0 - ln(S)
- **样本级别**：所有 Taxon-Function 对的 Shannon Index 相同
- **计算时机**：在读取 OTU 表后立即计算

---

## 测试结果

### 测试数据
**样本**：Leptinotarsa decemlineata (Colorado potato beetle)
**OTU 数量**：55 个分类单元
**总 reads**：538,623

### Shannon Index 计算结果
```
Shannon Index = 3.7589

解释：
• 理论最大值: ln(55) ≈ 4.01
• 实际值: 3.76
• 占最大值比例: 94%
• 结论: 群落多样性较高，物种分布较均匀
```

### 特征矩阵验证
```bash
# 验证所有行的 Shannon Index 是否相同
$ awk -F'\t' 'NR>1 {print $9}' tmp/test_output_v4.6_feature_matrix.tsv | sort -u
3.7589

# 结果：所有 107 行的 Shannon Index 都是 3.7589 ✅
```

---

## 特征列表更新

### v4.6 最终特征集（8 个特征）

| # | 特征名称 | 类型 | 取值范围 | 生物学意义 | 级别 |
|---|---------|------|---------|-----------|------|
| 1 | **Log_Abundance** | 连续 | 0 - ~2 | 对数丰度 | Taxon |
| 2 | **Match_Level_Score** | 分类 | 0.6, 1.0 | 分类置信度 | Taxon |
| 3 | **Host_Match_Weight_Max** | 连续 | 0.8 - 1.5 | 最佳宿主匹配 | Taxon-Function |
| 4 | **Evidence_Level_Max** | 离散 | 1 - 5 | 最高证据质量 | Taxon-Function |
| 5 | **Adjusted_Score_Max** | 连续 | 0 - ~200 | 综合质量分数 | Taxon-Function |
| 6 | **DB_Literature_Count** | 离散 | 1 - N | 文献数量（DOI 去重） | Taxon-Function |
| 7 | **Shannon_Index** ⭐ | 连续 | 0 - ln(S) | α 多样性 | **Sample** |
| 8 | **Rank_By_Abundance** | 离散 | 1 - N | 丰度排名 | Taxon |

### 特征层级
- **Sample 级别**（1 个）：Shannon_Index
- **Taxon 级别**（3 个）：Log_Abundance, Match_Level_Score, Rank_By_Abundance
- **Taxon-Function 级别**（4 个）：Host_Match_Weight_Max, Evidence_Level_Max, Adjusted_Score_Max, DB_Literature_Count

---

## 生物学应用场景

### 场景 1: 多样性依赖的功能识别
**问题**：哪些共生菌功能在高多样性群落中更活跃？

**分析方法**：
```python
# 按 Shannon Index 分组
high_diversity = feature_df[feature_df['Shannon_Index'] > 3.5]
low_diversity = feature_df[feature_df['Shannon_Index'] < 2.5]

# 比较功能分布
high_div_functions = high_diversity['Function'].value_counts()
low_div_functions = low_diversity['Function'].value_counts()
```

### 场景 2: 多样性对功能表达的影响
**问题**：群落多样性是否影响特定功能的表达强度？

**分析方法**：
```python
# 针对特定功能（如 nitrogen fixation）
nf_data = feature_df[feature_df['Function'] == 'nitrogen fixation']

# 分析 Shannon Index 与 Adjusted_Score_Max 的关系
correlation = nf_data[['Shannon_Index', 'Adjusted_Score_Max']].corr()
```

### 场景 3: 跨样本功能比较
**问题**：不同处理组的微生物组功能差异是否与多样性相关？

**分析方法**：
```python
# 合并多个样本的特征矩阵
all_samples = pd.concat([sample1_df, sample2_df, sample3_df])

# 按 Shannon Index 和 Function 分组
grouped = all_samples.groupby(['Shannon_Index', 'Function'])['Adjusted_Score_Max'].mean()
```

---

## 机器学习应用

### 1. 特征重要性预测

**预测排序（v4.6）**：

| 排名 | 特征 | 预测重要性 | 理由 |
|-----|------|-----------|------|
| 1 | **DB_Literature_Count** | ⭐⭐⭐⭐⭐ | 文献支持度最可靠 |
| 2 | **Host_Match_Weight_Max** | ⭐⭐⭐⭐⭐ | 宿主特异性核心 |
| 3 | **Log_Abundance** | ⭐⭐⭐⭐ | 丰度基础指标 |
| 4 | **Evidence_Level_Max** | ⭐⭐⭐⭐ | 证据质量重要 |
| 5 | **Shannon_Index** | ⭐⭐⭐ | 群落上下文（新增） |
| 6 | **Adjusted_Score_Max** | ⭐⭐⭐ | 综合指标 |
| 7 | **Match_Level_Score** | ⭐⭐⭐ | 分类置信度 |
| 8 | **Rank_By_Abundance** | ⭐⭐ | 相对排名 |

**Shannon_Index 的重要性**：
- 可能中等重要（⭐⭐⭐）
- 提供群落级别的上下文信息
- 与其他特征的交互可能更重要

### 2. 特征交互探索

**推荐的交互特征**：
```python
# 交互 1: 丰度 × 多样性
feature_df['Abundance_Diversity'] = (
    feature_df['Log_Abundance'] * feature_df['Shannon_Index']
)

# 交互 2: 质量分数 / 多样性
feature_df['Score_Per_Diversity'] = (
    feature_df['Adjusted_Score_Max'] / (feature_df['Shannon_Index'] + 1)
)

# 交互 3: 多样性归一化的丰度排名
feature_df['Normalized_Rank'] = (
    feature_df['Rank_By_Abundance'] / feature_df['Shannon_Index']
)
```

### 3. 模型训练建议

**随机森林**：
```python
from sklearn.ensemble import RandomForestClassifier

X = feature_df[['Log_Abundance', 'Match_Level_Score', 'Host_Match_Weight_Max',
                'Evidence_Level_Max', 'Adjusted_Score_Max', 'DB_Literature_Count',
                'Shannon_Index', 'Rank_By_Abundance']]
y = feature_df['Label']

rf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
rf.fit(X, y)

# 评估 Shannon_Index 的特征重要性
importances = pd.DataFrame({
    'Feature': X.columns,
    'Importance': rf.feature_importances_
}).sort_values('Importance', ascending=False)
```

---

## Shannon Index 的生态学解释

### 典型值范围

| Shannon Index | 生态学解释 | 示例 |
|--------------|-----------|------|
| **0 - 1.0** | 极低多样性 | 单一优势菌主导（如抗生素处理后）|
| **1.0 - 2.0** | 低多样性 | 少数菌占主导（如特定共生系统）|
| **2.0 - 3.0** | 中等多样性 | 典型的肠道微生物组 |
| **3.0 - 4.0** | 高多样性 | 健康的土壤/环境微生物组 |
| **> 4.0** | 极高多样性 | 复杂的环境样本 |

### 本研究样本
```
Shannon Index = 3.7589
• 分类: 高多样性
• 解释: 昆虫肠道微生物组，物种分布较均匀
• 生态学意义: 群落结构稳定，功能冗余度高
```

---

## 与其他多样性指标的比较

### 常见α多样性指标

| 指标 | 公式 | 优点 | 缺点 | 是否采用 |
|-----|------|------|------|---------|
| **Shannon Index** | -Σ(pi×ln(pi)) | 同时考虑丰富度和均匀度 | 对稀有种敏感 | ✅ 采用 |
| Simpson Index | 1-Σ(pi²) | 对优势种敏感 | 忽略稀有种 | ❌ 未采用 |
| Richness (S) | 物种数 | 简单直观 | 忽略丰度信息 | ❌ 未采用 |
| Pielou's Evenness | H'/ln(S) | 标准化均匀度 | 需要额外计算 | ❌ 未采用 |

**选择 Shannon Index 的理由**：
1. ✅ 最常用的多样性指标（标准化）
2. ✅ 同时考虑物种丰富度和均匀度
3. ✅ 对中等丰度物种敏感（符合共生菌研究）
4. ✅ 取值范围合理，易于解释

---

## 向后兼容性

### ⚠️ 不兼容变更

**特征数量变化**：
```
v4.5: 7 个特征
v4.6: 8 个特征（新增 Shannon_Index）
```

**列顺序变化**：
```
v4.5: ..., DB_Literature_Count, Rank_By_Abundance
v4.6: ..., DB_Literature_Count, Shannon_Index, Rank_By_Abundance
```

### 迁移指南

**如果使用 v4.5 训练的模型**：
1. ✅ **推荐**：使用 v4.6 重新训练模型（新增有价值的特征）
2. ⚠️ **不推荐**：继续使用 v4.5 模型（缺少群落上下文信息）

**如果需要兼容旧版本**：
```python
# 从 v4.6 移除 Shannon_Index 以兼容 v4.5
feature_df_v45 = feature_df.drop('Shannon_Index', axis=1)
```

---

## 总结

### 主要改进

1. ✅ **新增 Shannon Index**：反映微生物组α多样性
2. ✅ **群落级别上下文**：补充个体级别特征
3. ✅ **生态学意义**：符合微生物生态学原理
4. ✅ **特征交互潜力**：可与其他特征组合
5. ✅ **跨样本比较**：支持多样性相关分析

### 科学价值

- **更全面的特征集**：个体 + 群落双层次
- **生态学合理性**：符合微生物生态学理论
- **机器学习友好**：提供额外的预测维度
- **应用场景丰富**：支持多样性相关研究

### 下一步工作

- [ ] 评估 Shannon_Index 的特征重要性
- [ ] 探索 Shannon_Index 与其他特征的交互
- [ ] 分析多样性对功能预测准确性的影响
- [ ] 开发多样性依赖的功能识别工具
- [ ] 添加其他α多样性指标（Simpson, Pielou's）

---

**更新人员**：Claude (AI Assistant)
**审核状态**：待用户确认
**相关文档**：
- `logs/feature_matrix_v4.5_DOI_DEDUPLICATION.md` - v4.5 DOI 去重
- `logs/feature_matrix_v4.4_STREAMLINED.md` - v4.4 特征精简
- `logs/iSymPred_DESIGN_OVERVIEW.md` - 软件设计概览
