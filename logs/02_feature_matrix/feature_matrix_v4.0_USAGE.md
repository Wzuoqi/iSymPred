# Feature Matrix v4.0 - 使用指南

**日期:** 2026-01-08
**版本:** 4.0 (精简版，适用于小样本训练)
**输出级别:** Taxon-Function 配对
**特征数量:** 12个核心生物学特征

---

## 概述

v4.0 是专为**小样本随机森林训练**设计的精简特征矩阵。相比v3.0的64个特征，v4.0只保留了12个最有生物学意义的核心特征，并且输出粒度从Taxon级别改为**Taxon-Function配对级别**。

### 关键改进
1. **特征精简:** 64 → 12 特征（减少81%）
2. **输出粒度:** Taxon聚合 → Taxon-Function配对
3. **训练数据:** 55行（taxa）→ 223行（pairs），增加4倍训练样本
4. **生物学意义:** 每个特征都有明确的生物学解释
5. **小样本友好:** 适合50-200个标注样本的训练

---

## 输出格式

### 示例数据
```tsv
Taxon                    Function                      Relative_Abundance_Pct  Log_Abundance  Match_Level_Score  Is_Known_Symbiont  Host_Match_Weight  Host_Match_Level  Evidence_Level  Has_Genome_Data  Function_Probability  Adjusted_Score  Function_Support_Count  Rank_By_Abundance
Lactococcus lactis      pesticide metabolization      3.9881                  0.6979         1.0                0                  1.1                Order             3               0                0.522                 104.2           150                     6
Wolbachia (sp.)         cytoplasmic incompatibility   1.124                   0.3272         0.6                1                  1.3                Genus             5               0                0.051                 60.9            4                       16
Buchnera aphidicola     amino acid provision          5.2                     0.7202         1.0                1                  1.5                Species           5               1                0.823                 125.3           94                      3
```

### 数据结构
- **每一行:** 一个 Taxon-Function 配对
- **列数:** 14列（2个标识符 + 12个特征）
- **行数:** 取决于匹配记录数（通常100-500行）

---

## 12个核心特征详解

### 1-2. 丰度特征 (Abundance Features)

#### `Relative_Abundance_Pct`
- **类型:** Float (0-100)
- **含义:** 该分类单元在样本中的相对丰度百分比
- **生物学意义:** 高丰度的分类单元更可能在生态系统中发挥重要功能
- **ML重要性:** ⭐⭐⭐⭐⭐

#### `Log_Abundance`
- **类型:** Float
- **公式:** log10(Relative_Abundance_Pct + 1)
- **含义:** 对数变换后的丰度
- **生物学意义:** 线性化丰度分布，使低丰度和高丰度taxa在模型中权重更平衡
- **ML重要性:** ⭐⭐⭐⭐

### 3-4. 分类置信度 (Taxonomic Confidence)

#### `Match_Level_Score`
- **类型:** Float (0.6 或 1.0)
- **含义:** 分类匹配的置信度
  - 1.0 = 种级匹配（Species-level）
  - 0.6 = 属级匹配（Genus-level）
- **生物学意义:** 种级鉴定比属级鉴定更可靠
- **ML重要性:** ⭐⭐⭐⭐

#### `Is_Known_Symbiont`
- **类型:** Binary (0/1)
- **含义:** 该属是否为已知共生菌属
- **已知共生菌列表:** Wolbachia, Buchnera, Wigglesworthia, Sodalis, Blattabacterium, Candidatus, Spiroplasma, Rickettsia, Serratia, Hamiltonella, Regiella, Arsenophonus, Cardinium
- **生物学意义:** 已知共生菌属更可能具有共生功能
- **ML重要性:** ⭐⭐⭐⭐

### 5-6. 宿主上下文 (Host Context)

#### `Host_Match_Weight`
- **类型:** Float (0.8-1.5)
- **含义:** 宿主匹配权重
- **取值范围:**
  - 1.5 = 物种级宿主匹配
  - 1.3 = 属级宿主匹配
  - 1.2 = 科级宿主匹配
  - 1.1 = 目级宿主匹配
  - 1.0 = 通用记录（无宿主特异性）
  - 0.8 = 宿主不匹配
- **生物学意义:** 宿主特异性共生菌更可能在该宿主中发挥功能
- **ML重要性:** ⭐⭐⭐⭐⭐

#### `Host_Match_Level`
- **类型:** Categorical (Species, Genus, Family, Order, General, Mismatch)
- **含义:** 宿主匹配的分类级别
- **生物学意义:** 提供宿主特异性的详细信息
- **ML使用:** 需要进行one-hot编码
- **ML重要性:** ⭐⭐⭐

### 7-8. 证据质量 (Evidence Quality)

#### `Evidence_Level`
- **类型:** Integer (1-5)
- **含义:** 科学证据的质量等级
- **等级定义:**
  - 5 = 共生菌 + 基因组数据 + 顶级期刊
  - 4 = 共生菌 + 基因组数据
  - 3 = 共生菌 + 顶级期刊
  - 2 = 仅共生菌证据
  - 1 = 低质量证据
- **生物学意义:** 高质量证据的预测更可靠
- **ML重要性:** ⭐⭐⭐⭐

#### `Has_Genome_Data`
- **类型:** Binary (0/1)
- **含义:** 是否有基因组测序数据
- **检测方法:** 检查证据字段中是否包含"GISB"或"genome"
- **生物学意义:** 有基因组数据的共生菌研究更深入
- **ML重要性:** ⭐⭐⭐

### 9-10. 预测置信度 (Prediction Confidence)

#### `Function_Probability`
- **类型:** Float (0-1)
- **含义:** 该功能存在的概率（来自functions表）
- **计算方法:** 基于丰度、宿主匹配、证据质量等多维度计算
- **生物学意义:** 模型对该功能预测的置信度
- **ML重要性:** ⭐⭐⭐⭐⭐

#### `Adjusted_Score`
- **类型:** Float
- **公式:** Base_Score × Host_Match_Weight² × Evidence_Weight^1.5
- **含义:** 综合质量分数
- **生物学意义:** 整合了丰度、宿主匹配、证据质量的综合指标
- **ML重要性:** ⭐⭐⭐⭐⭐

### 11. 功能上下文 (Function Context)

#### `Function_Support_Count`
- **类型:** Integer (≥1)
- **含义:** 样本中有多少个分类单元支持该功能
- **生物学意义:** 多个taxa支持的功能更可能是真实的
- **ML重要性:** ⭐⭐⭐

### 12. 相对排名 (Relative Ranking)

#### `Rank_By_Abundance`
- **类型:** Integer (≥1)
- **含义:** 按丰度排名（1=最高丰度）
- **生物学意义:** 提供相对丰度的上下文信息
- **ML重要性:** ⭐⭐⭐

---

## 机器学习工作流程

### 步骤1: 生成特征矩阵

```bash
python isympred/predictors/record_predictor.py \
    -i your_otu_table.tsv \
    -d isympred/database/symbiont_record/record_db.tsv \
    -o output/results.tsv \
    --host "Your Host Species" \
    --host-db isympred/database/host_taxonomy/insect_taxonomy.db
```

输出: `output/results_feature_matrix.tsv` (Taxon-Function配对，12特征)

### 步骤2: 手动标注关键功能

这是**最关键的步骤**！需要根据文献和生物学知识标注哪些Taxon-Function配对是真实的关键共生功能。

```python
import pandas as pd

# 加载特征矩阵
features = pd.read_csv('output/results_feature_matrix.tsv', sep='\t')

# 手动标注（示例）
# 1 = 这是真实的/重要的共生功能
# 0 = 这不是关键功能（或假阳性）

# 方法1: 基于已知共生菌
features['Is_Key_Function'] = 0  # 默认为0
features.loc[
    (features['Taxon'].str.contains('Wolbachia')) &
    (features['Function'].str.contains('cytoplasmic incompatibility')),
    'Is_Key_Function'
] = 1

features.loc[
    (features['Taxon'].str.contains('Buchnera')) &
    (features['Function'].str.contains('amino acid')),
    'Is_Key_Function'
] = 1

# 方法2: 导出到Excel手动标注
features.to_excel('annotation_template.xlsx', index=False)
# 在Excel中手动标注 Is_Key_Function 列
# 然后重新导入
features = pd.read_excel('annotated_features.xlsx')
```

### 步骤3: 准备训练数据

```python
# 分离特征和标签
X = features[['Relative_Abundance_Pct', 'Log_Abundance', 'Match_Level_Score',
              'Is_Known_Symbiont', 'Host_Match_Weight', 'Evidence_Level',
              'Has_Genome_Data', 'Function_Probability', 'Adjusted_Score',
              'Function_Support_Count', 'Rank_By_Abundance']]

# One-hot编码分类变量
X = pd.get_dummies(X, columns=['Host_Match_Level'], drop_first=True)

y = features['Is_Key_Function']

print(f"训练样本数: {len(X)}")
print(f"正样本数: {y.sum()}")
print(f"负样本数: {len(y) - y.sum()}")
print(f"特征数: {len(X.columns)}")
```

### 步骤4: 训练随机森林模型

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import classification_report, roc_auc_score

# 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 训练随机森林（小样本参数设置）
rf = RandomForestClassifier(
    n_estimators=50,        # 较少的树（避免过拟合）
    max_depth=5,            # 限制深度
    min_samples_split=5,    # 最小分裂样本数
    min_samples_leaf=2,     # 最小叶子节点样本数
    class_weight='balanced', # 处理类别不平衡
    random_state=42
)

# 交叉验证
cv_scores = cross_val_score(rf, X_train, y_train, cv=5, scoring='roc_auc')
print(f"交叉验证 ROC-AUC: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

# 训练最终模型
rf.fit(X_train, y_train)

# 测试集评估
y_pred = rf.predict(X_test)
y_prob = rf.predict_proba(X_test)[:, 1]

print("\n分类报告:")
print(classification_report(y_test, y_pred))
print(f"测试集 ROC-AUC: {roc_auc_score(y_test, y_prob):.3f}")
```

### 步骤5: 特征重要性分析

```python
# 特征重要性
importances = pd.DataFrame({
    'Feature': X.columns,
    'Importance': rf.feature_importances_
}).sort_values('Importance', ascending=False)

print("\n特征重要性排名:")
print(importances)

# 可视化
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
plt.barh(importances.head(10)['Feature'], importances.head(10)['Importance'])
plt.xlabel('Importance')
plt.title('Top 10 Feature Importances')
plt.tight_layout()
plt.savefig('feature_importance.png', dpi=300)
```

### 步骤6: 预测新样本

```python
# 对所有Taxon-Function配对进行预测
all_predictions = rf.predict_proba(X)[:, 1]

# 创建结果表
results = features[['Taxon', 'Function']].copy()
results['Prediction_Probability'] = all_predictions
results['Relative_Abundance'] = features['Relative_Abundance_Pct']
results['Adjusted_Score'] = features['Adjusted_Score']
results['Function_Probability'] = features['Function_Probability']

# 按预测概率排序
results = results.sort_values('Prediction_Probability', ascending=False)

print("\nTop 20 预测的关键共生功能:")
print(results.head(20))

# 保存结果
results.to_csv('predicted_key_functions.tsv', sep='\t', index=False)
```

---

## 预期特征重要性

基于生物学知识，预期的特征重要性排序：

1. **Function_Probability** (⭐⭐⭐⭐⭐) - 模型置信度
2. **Adjusted_Score** (⭐⭐⭐⭐⭐) - 综合质量分数
3. **Host_Match_Weight** (⭐⭐⭐⭐⭐) - 宿主特异性
4. **Relative_Abundance_Pct** (⭐⭐⭐⭐) - 丰度
5. **Is_Known_Symbiont** (⭐⭐⭐⭐) - 已知共生菌
6. **Evidence_Level** (⭐⭐⭐⭐) - 证据质量
7. **Match_Level_Score** (⭐⭐⭐) - 分类置信度
8. **Function_Support_Count** (⭐⭐⭐) - 功能支持度
9. **Log_Abundance** (⭐⭐⭐) - 对数丰度
10. **Has_Genome_Data** (⭐⭐) - 基因组数据
11. **Rank_By_Abundance** (⭐⭐) - 丰度排名
12. **Host_Match_Level** (⭐⭐) - 宿主匹配级别

*实际重要性会因数据集而异，需要通过训练验证*

---

## 小样本训练建议

### 样本量要求
- **最小样本:** 60-120个标注的Taxon-Function配对
- **推荐样本:** 150-300个标注配对
- **经验法则:** 每个特征需要5-10个样本

### 避免过拟合的策略
1. **限制模型复杂度:**
   - `max_depth=5` (限制树深度)
   - `min_samples_split=5` (最小分裂样本)
   - `n_estimators=50` (较少的树)

2. **交叉验证:**
   - 使用5折交叉验证
   - 监控训练集和验证集性能差异

3. **特征选择:**
   - 如果样本极少(<100)，考虑只使用top 8特征
   - 移除高度相关的特征

4. **类别平衡:**
   - 使用`class_weight='balanced'`
   - 或使用SMOTE过采样

### 标注质量控制
1. **一致性检查:** 同一Taxon的不同Function标注应该一致
2. **文献验证:** 标注应基于已发表的研究
3. **专家审核:** 关键标注应由领域专家确认
4. **迭代改进:** 根据模型预测结果调整标注

---

## 与v3.0的对比

| 特性 | v3.0 | v4.0 |
|------|------|------|
| 特征数 | 64 | 12 |
| 输出粒度 | Taxon级别 | Taxon-Function配对 |
| 训练样本数 | 55行 | 223行 |
| 适用场景 | 大样本(>500) | 小样本(50-300) |
| 过拟合风险 | 高 | 低 |
| 生物学解释性 | 中等 | 高 |
| 特征冗余 | 有 | 无 |

---

## 常见问题

### Q1: 为什么要用Taxon-Function配对而不是Taxon聚合？
**A:** Taxon-Function配对提供更细粒度的预测目标。同一个Taxon可能有多个功能，有些是真实的，有些是假阳性。配对级别的预测可以区分这些情况。

### Q2: 12个特征够用吗？
**A:** 对于小样本训练，12个特征是合适的。经验法则是每个特征需要5-10个样本，所以12个特征需要60-120个标注样本，这对于大多数研究是可行的。

### Q3: 如何选择标注哪些Taxon-Function配对？
**A:** 优先标注：
1. 已知共生菌的经典功能（如Wolbachia的CI）
2. 高丰度taxa的主要功能
3. 高Adjusted_Score的配对
4. 文献中有明确报道的配对

### Q4: Host_Match_Level需要one-hot编码吗？
**A:** 是的。这是一个分类变量，需要转换为多个二元特征。使用`pd.get_dummies()`即可。

### Q5: 如果样本量很小(<100)怎么办？
**A:** 考虑：
1. 只使用top 8特征（移除Rank_By_Abundance等次要特征）
2. 使用更简单的模型（如Logistic Regression）
3. 增加标注样本（这是最好的解决方案）

---

## 完整示例脚本

```python
#!/usr/bin/env python3
"""
完整的Taxon-Function配对预测工作流程
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

# ========== 步骤1: 加载数据 ==========
print("=== 加载特征矩阵 ===")
features = pd.read_csv('output_feature_matrix.tsv', sep='\t')
print(f"总配对数: {len(features)}")
print(f"唯一taxa数: {features['Taxon'].nunique()}")
print(f"唯一功能数: {features['Function'].nunique()}")

# ========== 步骤2: 手动标注（示例） ==========
print("\n=== 创建标注 ===")
# 这里使用简单规则作为示例，实际应该手动标注
features['Is_Key_Function'] = 0

# 规则1: 已知共生菌 + 高丰度 + 高分数
features.loc[
    (features['Is_Known_Symbiont'] == 1) &
    (features['Relative_Abundance_Pct'] > 1.0) &
    (features['Adjusted_Score'] > 50),
    'Is_Key_Function'
] = 1

# 规则2: 高宿主匹配 + 高证据等级
features.loc[
    (features['Host_Match_Weight'] >= 1.3) &
    (features['Evidence_Level'] >= 4),
    'Is_Key_Function'
] = 1

print(f"正样本数: {features['Is_Key_Function'].sum()}")
print(f"负样本数: {len(features) - features['Is_Key_Function'].sum()}")

# ========== 步骤3: 准备特征 ==========
print("\n=== 准备特征 ===")
feature_cols = ['Relative_Abundance_Pct', 'Log_Abundance', 'Match_Level_Score',
                'Is_Known_Symbiont', 'Host_Match_Weight', 'Evidence_Level',
                'Has_Genome_Data', 'Function_Probability', 'Adjusted_Score',
                'Function_Support_Count', 'Rank_By_Abundance']

X = features[feature_cols].copy()

# One-hot编码Host_Match_Level
X = pd.concat([X, pd.get_dummies(features['Host_Match_Level'], prefix='Host')], axis=1)

y = features['Is_Key_Function']

print(f"特征数: {len(X.columns)}")
print(f"特征列表: {list(X.columns)}")

# ========== 步骤4: 训练模型 ==========
print("\n=== 训练随机森林 ===")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

rf = RandomForestClassifier(
    n_estimators=50,
    max_depth=5,
    min_samples_split=5,
    class_weight='balanced',
    random_state=42
)

# 交叉验证
cv_scores = cross_val_score(rf, X_train, y_train, cv=5, scoring='roc_auc')
print(f"交叉验证 ROC-AUC: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

# 训练
rf.fit(X_train, y_train)

# 评估
y_pred = rf.predict(X_test)
y_prob = rf.predict_proba(X_test)[:, 1]

print("\n分类报告:")
print(classification_report(y_test, y_pred))
print(f"测试集 ROC-AUC: {roc_auc_score(y_test, y_prob):.3f}")

# ========== 步骤5: 特征重要性 ==========
print("\n=== 特征重要性 ===")
importances = pd.DataFrame({
    'Feature': X.columns,
    'Importance': rf.feature_importances_
}).sort_values('Importance', ascending=False)

print(importances.head(10))

# 可视化
plt.figure(figsize=(10, 6))
plt.barh(importances.head(10)['Feature'], importances.head(10)['Importance'])
plt.xlabel('Importance')
plt.title('Top 10 Feature Importances')
plt.tight_layout()
plt.savefig('feature_importance.png', dpi=300)
print("特征重要性图已保存: feature_importance.png")

# ========== 步骤6: 预测所有配对 ==========
print("\n=== 预测关键功能 ===")
all_predictions = rf.predict_proba(X)[:, 1]

results = features[['Taxon', 'Function']].copy()
results['ML_Probability'] = all_predictions
results['Relative_Abundance'] = features['Relative_Abundance_Pct']
results['Adjusted_Score'] = features['Adjusted_Score']
results['Function_Probability'] = features['Function_Probability']
results['True_Label'] = features['Is_Key_Function']

results = results.sort_values('ML_Probability', ascending=False)

print("\nTop 20 预测的关键功能:")
print(results.head(20)[['Taxon', 'Function', 'ML_Probability', 'Relative_Abundance']])

# 保存结果
results.to_csv('predicted_key_functions.tsv', sep='\t', index=False)
importances.to_csv('feature_importances.tsv', sep='\t', index=False)

print("\n✅ 分析完成！")
print("输出文件:")
print("  - predicted_key_functions.tsv")
print("  - feature_importances.tsv")
print("  - feature_importance.png")
```

---

## 总结

v4.0特征矩阵是专为小样本随机森林训练设计的精简版本：

✅ **12个核心特征** - 每个都有明确的生物学意义
✅ **Taxon-Function配对** - 更细粒度的预测目标
✅ **223行训练数据** - 相比v3.0的55行增加4倍
✅ **低过拟合风险** - 适合50-300个标注样本
✅ **高可解释性** - 特征重要性易于理解

**关键成功因素:** 高质量的手动标注！

---

**文档版本:** v4.0
**最后更新:** 2026-01-08
