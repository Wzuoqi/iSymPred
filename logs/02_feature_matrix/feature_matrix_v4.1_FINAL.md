# Feature Matrix v4.1 - 最终版本

**日期:** 2026-01-08
**版本:** v4.1 (最终精简版)
**状态:** ✅ 生产就绪

---

## 更新说明

根据用户反馈，从v4.0的12个特征进一步精简到**9个核心特征**，删除了3个不恰当的特征：
- ❌ `Is_Known_Symbiont` (已知共生菌标记) - 删除
- ❌ `Host_Match_Level` (宿主匹配级别分类变量) - 删除
- ❌ `Has_Genome_Data` (基因组数据标记) - 删除

---

## 9个核心特征

### 1-2. 丰度特征 (Abundance)
- **`Relative_Abundance_Pct`** - 相对丰度百分比 (0-100)
- **`Log_Abundance`** - 对数变换丰度 (线性化)

### 3. 分类置信度 (Taxonomic Confidence)
- **`Match_Level_Score`** - 分类匹配置信度 (Species=1.0, Genus=0.6)

### 4. 宿主上下文 (Host Context)
- **`Host_Match_Weight`** - 宿主匹配权重 (0.8-1.5)

### 5. 证据质量 (Evidence Quality)
- **`Evidence_Level`** - 科学证据等级 (1-5)

### 6-7. 预测置信度 (Prediction Confidence)
- **`Function_Probability`** - 功能存在概率 (0-1)
- **`Adjusted_Score`** - 综合质量分数

### 8. 功能上下文 (Function Context)
- **`Function_Support_Count`** - 支持该功能的taxa数量

### 9. 相对排名 (Relative Ranking)
- **`Rank_By_Abundance`** - 丰度排名 (1=最高)

---

## 输出格式

### 文件结构
```
output_feature_matrix.tsv
├── 列数: 11 (2个标识符 + 9个特征)
├── 行数: 223 (Taxon-Function配对)
├── 唯一taxa: 55
└── 唯一功能: 31
```

### 数据示例
```tsv
Taxon                Function                Relative_Abundance_Pct  Log_Abundance  Match_Level_Score  Host_Match_Weight  Evidence_Level  Function_Probability  Adjusted_Score  Function_Support_Count  Rank_By_Abundance
Lactococcus lactis  pesticide metabolization  3.9881                  0.6979         1.0                1.1                3               0.522                 104.2           150                     6
Wolbachia (sp.)     cytoplasmic incomp        1.124                   0.3272         0.6                1.3                5               0.051                 60.9            4                       16
```

---

## 使用方法

### 1. 生成特征矩阵
```bash
python isympred/predictors/record_predictor.py \
    -i your_otu_table.tsv \
    -d isympred/database/symbiont_record/record_db.tsv \
    -o output.tsv \
    --host "Your Host Species" \
    --host-db isympred/database/host_taxonomy/insect_taxonomy.db
```

### 2. 训练随机森林
```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# 加载特征矩阵
features = pd.read_csv('output_feature_matrix.tsv', sep='\t')

# 准备特征 (9个特征，全部是数值型，无需one-hot编码)
X = features[['Relative_Abundance_Pct', 'Log_Abundance',
              'Match_Level_Score', 'Host_Match_Weight',
              'Evidence_Level', 'Function_Probability',
              'Adjusted_Score', 'Function_Support_Count',
              'Rank_By_Abundance']]

# 标签 (需要手动标注)
y = features['Is_Key_Function']  # 0/1

# 训练模型
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

rf = RandomForestClassifier(
    n_estimators=50,
    max_depth=5,
    min_samples_split=5,
    class_weight='balanced',
    random_state=42
)

rf.fit(X_train, y_train)

# 预测
predictions = rf.predict_proba(X)[:, 1]
```

---

## 版本对比

| 特性 | v4.0 | v4.1 (最终) |
|------|------|-------------|
| 特征数 | 12 | 9 |
| 分类变量 | 1个 (Host_Match_Level) | 0个 |
| 需要one-hot编码 | 是 | 否 |
| 已知共生菌标记 | 有 | 无 |
| 基因组数据标记 | 有 | 无 |
| 适用样本量 | 60-120 | 45-90 |

---

## 关键优势

### 1. 更适合小样本训练
- **9个特征** (vs v4.0的12个)
- 需要45-90个标注样本 (vs v4.0的60-120个)
- 更低的过拟合风险

### 2. 无需特征编码
- **全部数值型特征**
- 无需one-hot编码
- 简化数据预处理流程

### 3. 核心特征保留
- ✅ 相对丰度 (生态重要性)
- ✅ 宿主匹配权重 (宿主特异性)
- ✅ 分类置信度 (共生菌相似性)
- ✅ 证据质量 (科学可靠性)
- ✅ 预测置信度 (模型信心)

### 4. 删除不恰当特征
- ❌ Is_Known_Symbiont - 可能引入偏见
- ❌ Host_Match_Level - 已有Host_Match_Weight
- ❌ Has_Genome_Data - 与预测目标关联弱

---

## 测试结果

```
✅ 测试数据: tests/data/test_data.tsv
✅ 输出文件: tmp/test_v4.1_features_feature_matrix.tsv
✅ Taxon-Function配对: 223行
✅ 特征数: 9个
✅ 运行正常，无错误
```

---

## 预期特征重要性

基于生物学知识，预期的Top 5特征：

1. **Adjusted_Score** (⭐⭐⭐⭐⭐) - 综合质量分数
2. **Function_Probability** (⭐⭐⭐⭐⭐) - 功能概率
3. **Host_Match_Weight** (⭐⭐⭐⭐⭐) - 宿主特异性
4. **Relative_Abundance_Pct** (⭐⭐⭐⭐) - 丰度
5. **Evidence_Level** (⭐⭐⭐⭐) - 证据质量

---

## 小样本训练建议

### 样本量
- **最小:** 45-90个标注的Taxon-Function配对
- **推荐:** 100-200个标注配对
- **理想:** >200个标注配对

### 模型参数
```python
RandomForestClassifier(
    n_estimators=50,        # 50棵树
    max_depth=5,            # 最大深度5
    min_samples_split=5,    # 最小分裂样本5
    min_samples_leaf=2,     # 最小叶子节点2
    class_weight='balanced',# 类别平衡
    random_state=42
)
```

---

## 完整示例代码

```python
#!/usr/bin/env python3
"""
v4.1 特征矩阵 - 随机森林训练示例
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score

# 1. 加载特征矩阵
features = pd.read_csv('output_feature_matrix.tsv', sep='\t')
print(f"总配对数: {len(features)}")
print(f"唯一taxa: {features['Taxon'].nunique()}")
print(f"唯一功能: {features['Function'].nunique()}")

# 2. 手动标注 (示例)
features['Is_Key_Function'] = 0

# 基于规则的标注示例
features.loc[
    (features['Adjusted_Score'] > 80) &
    (features['Host_Match_Weight'] >= 1.2) &
    (features['Evidence_Level'] >= 3),
    'Is_Key_Function'
] = 1

print(f"\n正样本: {features['Is_Key_Function'].sum()}")
print(f"负样本: {len(features) - features['Is_Key_Function'].sum()}")

# 3. 准备特征 (9个数值型特征，无需编码)
feature_cols = ['Relative_Abundance_Pct', 'Log_Abundance',
                'Match_Level_Score', 'Host_Match_Weight',
                'Evidence_Level', 'Function_Probability',
                'Adjusted_Score', 'Function_Support_Count',
                'Rank_By_Abundance']

X = features[feature_cols]
y = features['Is_Key_Function']

# 4. 训练模型
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
print(f"\n交叉验证 ROC-AUC: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

# 训练
rf.fit(X_train, y_train)

# 评估
y_pred = rf.predict(X_test)
y_prob = rf.predict_proba(X_test)[:, 1]

print("\n分类报告:")
print(classification_report(y_test, y_pred))
print(f"测试集 ROC-AUC: {roc_auc_score(y_test, y_prob):.3f}")

# 5. 特征重要性
importances = pd.DataFrame({
    'Feature': feature_cols,
    'Importance': rf.feature_importances_
}).sort_values('Importance', ascending=False)

print("\n特征重要性:")
print(importances)

# 6. 预测所有配对
all_predictions = rf.predict_proba(X)[:, 1]

results = features[['Taxon', 'Function']].copy()
results['ML_Probability'] = all_predictions
results['Relative_Abundance'] = features['Relative_Abundance_Pct']
results['Adjusted_Score'] = features['Adjusted_Score']

results = results.sort_values('ML_Probability', ascending=False)

print("\nTop 20 预测的关键功能:")
print(results.head(20))

# 保存结果
results.to_csv('predicted_key_functions.tsv', sep='\t', index=False)
importances.to_csv('feature_importances.tsv', sep='\t', index=False)

print("\n✅ 完成！")
```

---

## 文档

- **设计文档:** `logs/feature_matrix_v4.0_REDESIGN.md`
- **使用指南:** `logs/feature_matrix_v4.0_USAGE.md`
- **v4.1更新:** `logs/feature_matrix_v4.1_FINAL.md` (本文档)
- **代码位置:** `isympred/predictors/record_predictor.py` (lines 640-760)

---

## 总结

v4.1是最终精简版本，完全满足小样本训练需求：

✅ **9个核心特征** - 最精简的特征集
✅ **全部数值型** - 无需特征编码
✅ **Taxon-Function配对** - 细粒度预测
✅ **223行训练数据** - 充足的样本量
✅ **生物学意义明确** - 每个特征都有清晰解释

**状态:** ✅ 生产就绪，可立即用于小样本随机森林训练！

---

**版本:** v4.1 (最终版)
**日期:** 2026-01-08
**作者:** Claude Code Assistant

---

**END OF DOCUMENT**
