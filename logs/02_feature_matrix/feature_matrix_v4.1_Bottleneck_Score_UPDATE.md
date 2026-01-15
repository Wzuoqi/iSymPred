# Feature Matrix v4.1 Final - Bottleneck_Score 更新

**日期:** 2026-01-08
**版本:** v4.1 Final
**更新:** 重命名 Function_Probability → Bottleneck_Score

---

## 更新说明

根据用户反馈，将特征`Function_Probability`重命名为`Bottleneck_Score`，以更准确地反映其含义和用途。

### 重命名原因

1. **避免混淆:** `Function_Probability`容易与其他概率特征混淆
2. **体现木桶效应:** 该特征基于木桶效应（bottleneck effect）计算，使用`min()`函数捕获短板
3. **明确用途:** 主要用于**排除**不太可能的功能，而非排序

---

## 最终9个特征

### 1-2. 丰度特征
- `Relative_Abundance_Pct` - 相对丰度(%)
- `Log_Abundance` - 对数丰度

### 3. 分类置信度
- `Match_Level_Score` - 分类匹配置信度 (0.6/1.0)

### 4. 宿主上下文
- `Host_Match_Weight` - 宿主匹配权重 (0.8-1.5)

### 5. 证据质量
- `Evidence_Level` - 证据等级 (1-5)

### 6-7. 预测置信度（关键区别）

#### `Bottleneck_Score` ⭐ (新名称)
- **类型:** Float (0-1)
- **来源:** 从functions表的Probability字段获取
- **计算方法:** 基于木桶效应（bottleneck effect）
  ```python
  # 在functions表中计算
  bottleneck_factor = min(confidence_factor, host_factor, evidence_factor)
  probability = base_prob * bottleneck_factor * taxa_factor
  ```
- **核心思想:** 使用`min()`捕获短板，任一维度不足都会限制最终分数
- **主要用途:** **排除（Filtering）** - 识别和过滤不太可能的功能预测
- **解释:**
  - 低分(< 0.5): 存在明显短板，应排除
  - 中分(0.5-0.7): 某些维度不足，需谨慎
  - 高分(> 0.7): 各维度均衡，可信度高

#### `Adjusted_Score`
- **类型:** Float
- **计算方法:** Base_Score × Host_Match_Weight² × Evidence_Weight^1.5
- **核心思想:** 综合质量分数，整合丰度、宿主匹配、证据质量
- **主要用途:** **排序（Ranking）** - 对可能的功能进行优先级排序
- **解释:**
  - 分数越高，预测质量越好
  - 用于确定哪些功能最重要

### 8. 功能上下文
- `Function_Support_Count` - 支持该功能的taxa数量

### 9. 相对排名
- `Rank_By_Abundance` - 丰度排名

---

## Bottleneck_Score vs Adjusted_Score

| 维度 | Bottleneck_Score | Adjusted_Score |
|------|------------------|----------------|
| **计算方法** | min()木桶效应 | 乘法综合 |
| **主要用途** | 排除（Filtering） | 排序（Ranking） |
| **关注点** | 短板/缺陷 | 综合质量 |
| **取值范围** | 0-1 (概率) | 0-∞ (分数) |
| **解释** | 任一短板限制 | 整体质量高低 |
| **使用场景** | 过滤假阳性 | 优先级排序 |

### 使用示例

```python
import pandas as pd

features = pd.read_csv('output_feature_matrix.tsv', sep='\t')

# 1. 使用 Bottleneck_Score 排除不太可能的功能
filtered = features[features['Bottleneck_Score'] > 0.5]
print(f"排除后剩余: {len(filtered)}/{len(features)} 配对")

# 2. 使用 Adjusted_Score 对剩余功能排序
filtered = filtered.sort_values('Adjusted_Score', ascending=False)

# 3. 查看Top预测
print("\nTop 20 预测:")
print(filtered.head(20)[['Taxon', 'Function', 'Bottleneck_Score', 'Adjusted_Score']])
```

---

## 木桶效应（Bottleneck Effect）详解

### 计算公式（在functions表中）

```python
# 步骤1: 基础概率（基于丰度）
base_prob = 1 / (1 + exp(-0.2 * (RA% - 15)))

# 步骤2: 各维度因子
confidence_factor = 1.0 if species_match else 0.7
host_factor = 0.5 to 1.0 (based on host match level)
evidence_factor = 0.6 to 1.0 (based on evidence level)

# 步骤3: 木桶效应 - 使用min()捕获短板
bottleneck_factor = min(confidence_factor, host_factor, evidence_factor)

# 步骤4: 最终概率
probability = base_prob * bottleneck_factor * taxa_factor
```

### 为什么叫"木桶效应"？

**木桶理论（Bucket Theory）:** 一个木桶能装多少水，取决于最短的那块木板。

在共生菌功能预测中：
- **置信度短板:** 只有属级匹配 → 降低可信度
- **宿主短板:** 宿主不匹配 → 降低可信度
- **证据短板:** 证据质量低 → 降低可信度

**任何一个短板都会限制最终的预测可信度！**

### 示例

```
案例1: 高丰度但宿主不匹配
- RA% = 20% → base_prob = 0.8
- confidence_factor = 1.0 (species match)
- host_factor = 0.5 (mismatch) ← 短板！
- evidence_factor = 1.0 (level 5)
- bottleneck = min(1.0, 0.5, 1.0) = 0.5
- Bottleneck_Score = 0.8 × 0.5 × 1.0 = 0.4 (低分，应排除)

案例2: 各维度均衡
- RA% = 20% → base_prob = 0.8
- confidence_factor = 1.0 (species match)
- host_factor = 1.0 (species match)
- evidence_factor = 1.0 (level 5)
- bottleneck = min(1.0, 1.0, 1.0) = 1.0
- Bottleneck_Score = 0.8 × 1.0 × 1.0 = 0.8 (高分，可信)
```

---

## 机器学习使用建议

### 特征重要性预期

基于木桶效应的设计，预期特征重要性：

1. **Bottleneck_Score** (⭐⭐⭐⭐⭐) - 排除假阳性的关键特征
2. **Adjusted_Score** (⭐⭐⭐⭐⭐) - 排序的关键特征
3. **Host_Match_Weight** (⭐⭐⭐⭐) - 宿主特异性
4. **Relative_Abundance_Pct** (⭐⭐⭐⭐) - 生态重要性
5. **Evidence_Level** (⭐⭐⭐⭐) - 证据质量

### 特征使用策略

```python
from sklearn.ensemble import RandomForestClassifier

# 准备特征
X = features[['Relative_Abundance_Pct', 'Log_Abundance',
              'Match_Level_Score', 'Host_Match_Weight',
              'Evidence_Level', 'Bottleneck_Score',  # 用于排除
              'Adjusted_Score',                       # 用于排序
              'Function_Support_Count', 'Rank_By_Abundance']]

# 训练模型
rf = RandomForestClassifier(n_estimators=50, max_depth=5, class_weight='balanced')
rf.fit(X_train, y_train)

# 分析特征重要性
importances = pd.DataFrame({
    'Feature': X.columns,
    'Importance': rf.feature_importances_
}).sort_values('Importance', ascending=False)

print(importances)
```

### 预测后处理

```python
# 预测
predictions = rf.predict_proba(X)[:, 1]

results = features[['Taxon', 'Function']].copy()
results['ML_Probability'] = predictions
results['Bottleneck_Score'] = features['Bottleneck_Score']
results['Adjusted_Score'] = features['Adjusted_Score']

# 策略1: 结合Bottleneck_Score过滤
# 只保留Bottleneck_Score > 0.5 且 ML_Probability > 0.5的预测
high_confidence = results[
    (results['Bottleneck_Score'] > 0.5) &
    (results['ML_Probability'] > 0.5)
]

# 策略2: 按Adjusted_Score排序
high_confidence = high_confidence.sort_values('Adjusted_Score', ascending=False)

print("\n高置信度预测 (Top 20):")
print(high_confidence.head(20))
```

---

## 测试结果

```
✅ 测试数据: tests/data/test_data.tsv
✅ 输出文件: tmp/test_final_feature_matrix.tsv
✅ 特征名称: Bottleneck_Score ✓
✅ 配对数: 223行
✅ 特征数: 9个
✅ 运行正常
```

### 输出示例

```tsv
Taxon                Function                Bottleneck_Score  Adjusted_Score
Lactococcus lactis  pesticide metabolization  0.522             104.2
Wolbachia (sp.)     cytoplasmic incomp        0.051             60.9
```

---

## 文档更新

- **代码位置:** `isympred/predictors/record_predictor.py` (lines 692-701, 726, 762)
- **更新内容:**
  1. 变量名: `func_probability` → `bottleneck_score`
  2. 列名: `Function_Probability` → `Bottleneck_Score`
  3. 注释: 添加木桶效应说明
  4. 输出: 更新特征描述

---

## 总结

### 更新前 (v4.1)
- 特征名: `Function_Probability`
- 含义不明确，容易混淆

### 更新后 (v4.1 Final)
- 特征名: `Bottleneck_Score` ✅
- 含义明确: 木桶效应分数，用于排除
- 与`Adjusted_Score`形成互补:
  - `Bottleneck_Score`: 排除（Filtering）
  - `Adjusted_Score`: 排序（Ranking）

---

**版本:** v4.1 Final
**日期:** 2026-01-08
**状态:** ✅ 生产就绪

---

**END OF DOCUMENT**
