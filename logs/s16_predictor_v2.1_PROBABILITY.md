# S16 Predictor v2.1 更新日志 - Probability 功能

**更新日期**: 2026-01-07
**版本**: v2.1
**更新内容**: 添加功能存在概率 (Probability) 列，修改输出文件名

---

## 📋 更新概述

本次更新为功能汇总表添加了 **Probability** 列，用于量化每个功能标签在种群中存在的可能性。同时将输出文件名从 `output.tsv` 改为 `output_functions.tsv`，使文件用途更加明确。

---

## 🎯 核心改动

### 1. 新增 Probability 列

**位置**: 功能汇总表 (`_functions.tsv`)，位于 `Dominant_Contributor` 列之前

**列结构变化**:
```
旧版 (v2.0):
Function | Final_Score_Sum | ... | Taxa_Count | Dominant_Contributor

新版 (v2.1):
Function | Final_Score_Sum | ... | Taxa_Count | Probability | Dominant_Contributor
```

### 2. 输出文件名变更

**变更内容**:
- 功能汇总表: `output.tsv` → `output_functions.tsv`
- 明细表: `output_potential_symbionts.tsv` (保持不变)

**示例**:
```bash
# 用户指定输出: -o results.tsv
# 实际输出文件:
#   - results_functions.tsv (功能汇总表)
#   - results_potential_symbionts.tsv (明细表)
```

---

## 🧮 Probability 计算逻辑

### 设计原理

Probability 表示该功能在种群中真实存在的可能性（0-1 范围），综合考虑以下因素：

1. **相对丰度 (RA%)**: 丰度越高，功能存在可能性越大
2. **分类匹配置信度**: 种级匹配比属级匹配更可靠
3. **宿主特异性**: 宿主匹配度越高，功能存在可能性越大
4. **文献证据质量**: 高质量证据提升可信度
5. **分类单元数量**: 多个分类单元支持提升可信度

### 计算公式

```
Probability = Base_Prob × Confidence_Factor × Host_Factor × Evidence_Factor × Taxa_Factor
```

#### 步骤 1: 基础概率 (Base_Prob)

基于相对丰度 (RA%)，使用 **Sigmoid 函数**映射到 0-1 范围：

```
Base_Prob = 1 / (1 + e^(-k*(RA% - x0)))
```

**参数**:
- `k = 0.3`: 控制曲线陡峭度
- `x0 = 5`: 中点位置（RA% = 5% 时，Base_Prob ≈ 0.5）

**特性**:
- RA% = 0%: Base_Prob ≈ 0.18
- RA% = 5%: Base_Prob ≈ 0.50
- RA% = 10%: Base_Prob ≈ 0.82
- RA% = 20%: Base_Prob ≈ 0.99

#### 步骤 2: 置信度调整 (Confidence_Factor)

基于分类匹配等级 (Mean_Confidence: 0.6-1.0)：

```
Confidence_Factor = 0.9 + (Mean_Confidence × 0.2)
```

**映射**:
- Mean_Confidence = 0.6 (属级): Factor = 1.02
- Mean_Confidence = 1.0 (种级): Factor = 1.10

#### 步骤 3: 宿主匹配调整 (Host_Factor)

基于宿主特异性 (Mean_Host_Match: 0.8-1.5)：

```
Host_Factor = 0.95 + ((Mean_Host_Match - 1.0) × 0.1)
```

**映射**:
- Mean_Host_Match = 0.8 (不匹配): Factor = 0.93
- Mean_Host_Match = 1.0 (通用): Factor = 0.95
- Mean_Host_Match = 1.5 (物种级): Factor = 1.00

#### 步骤 4: 证据质量调整 (Evidence_Factor)

基于文献证据 (Mean_Evidence_Weight: 0.8-1.5)：

```
Evidence_Factor = 0.95 + ((Mean_Evidence_Weight - 1.0) × 0.1)
```

**映射**:
- Mean_Evidence_Weight = 0.8 (低质量): Factor = 0.93
- Mean_Evidence_Weight = 1.0 (基础): Factor = 0.95
- Mean_Evidence_Weight = 1.5 (最高): Factor = 1.00

#### 步骤 5: 分类单元数量调整 (Taxa_Factor)

基于贡献该功能的分类单元数量 (Taxa_Count)：

```
Taxa_Factor = 1.0 + (log10(Taxa_Count + 1) × 0.05)
```

**映射**:
- Taxa_Count = 1: Factor = 1.015
- Taxa_Count = 10: Factor = 1.052
- Taxa_Count = 100: Factor = 1.101
- Taxa_Count = 200: Factor = 1.119

**设计理由**: 使用对数函数避免分类单元数量过度影响概率

#### 最终限制

```
Probability = max(0.0, min(1.0, Final_Probability))
```

确保概率值在 0-1 范围内。

---

## 📊 Probability 解读指南

### 概率等级划分

| 概率范围 | 等级 | 解释 | 建议 |
|---------|------|------|------|
| **0.90 - 1.00** | 极高 | 功能几乎确定存在 | 高置信度，可直接使用 |
| **0.75 - 0.89** | 高 | 功能很可能存在 | 较高置信度，推荐使用 |
| **0.50 - 0.74** | 中等 | 功能可能存在 | 中等置信度，建议验证 |
| **0.30 - 0.49** | 低 | 功能存在可能性较低 | 低置信度，需进一步验证 |
| **0.00 - 0.29** | 极低 | 功能可能不存在 | 谨慎使用，可能为假阳性 |

### 影响因素分析

**高概率 (>0.9) 的典型特征**:
- ✅ 高相对丰度 (RA% > 10%)
- ✅ 种级匹配 (Mean_Confidence = 1.0)
- ✅ 宿主特异性强 (Mean_Host_Match > 1.2)
- ✅ 高质量证据 (Mean_Evidence_Weight > 1.3)
- ✅ 多个分类单元支持 (Taxa_Count > 50)

**低概率 (<0.5) 的典型特征**:
- ❌ 低相对丰度 (RA% < 3%)
- ❌ 属级匹配 (Mean_Confidence = 0.6)
- ❌ 宿主不匹配 (Mean_Host_Match < 1.0)
- ❌ 低质量证据 (Mean_Evidence_Weight < 1.0)
- ❌ 单一分类单元 (Taxa_Count = 1-2)

---

## 💡 使用建议

### 1. 筛选策略

**保守策略** (高精度):
```
Probability >= 0.75 AND Final_Score_Sum > 200
```

**平衡策略** (推荐):
```
Probability >= 0.50 AND Final_Score_Sum > 100
```

**宽松策略** (高召回):
```
Probability >= 0.30 AND Final_Score_Sum > 50
```

### 2. 结合其他指标

不要单独依赖 Probability，应结合其他列综合判断：

```python
# 高可信度功能
high_confidence = df[
    (df['Probability'] >= 0.75) &
    (df['Mean_Host_Match']
    (df['Mean_Evidence_Weight'] > 1.2) &
    (df['Taxa_Count'] > 10)
]

# 需要验证的功能
need_validation = df[
    (df['Probability'] >= 0.50) &
    (df['Probability'] < 0.75)
]

# 可能的假阳性
potential_false_positive = df[
    (df['Probability'] < 0.30)
]
```

### 3. 下游分析

**功能富集分析**:
- 使用 `Probability >= 0.75` 的功能作为"存在"
- 使用 `Probability` 作为权重进行加权富集分析

**功能网络构建**:
- 使用 `Probability` 作为边的权重
- 过滤低概率功能 (< 0.5) 减少噪音

**比较分析**:
- 比较不同样本间功能的 `Probability` 差异
- 识别样本特异性功能 (某样本 Prob > 0.8，其他 < 0.3)

---

## 🧪 测试结果

### 测试数据
- 输入: `tests/data/test_data.tsv` (538,623 reads)
- 宿主: `Drosophila melanogaster`

### 输出示例

```
Function                    Probability  Total_RA_Pct  Taxa_Count  Mean_Host_Match
other                       1.000        15.767        173         0.94
pesticide metabolization    0.973        14.098        150         0.89
pathogen resistance         0.867        10.491        183         1.06
antimicrobial activity      0.843        9.868         198         1.07
```

**观察**:
1. 高丰度功能 (RA% > 10%) 的概率接近 1.0
2. 中等丰度功能 (RA% ≈ 10%) 的概率在 0.85-0.97
3. 宿主匹配度对概率有微调作用
4. 分类单元数量多的功能概率略高

---

## 🔧 代码实现位置

**文件**: `isympred/predictors/s16_predictor.py`

**修改位置**:
- **第385-423行**: Probability 计算逻辑
- **第433行**: 添加 Probability 列到输出
- **第441-446行**: 修改输出文件名逻辑

**新增依赖**:
- `import math` (用于 sigmoid 和 log10 函数)

---

## 📝 向后兼容性

### 完全兼容
- ✅ 旧版脚本仍可读取核心列 (Function, Final_Score_Sum, Total_RA_Pct)
- ✅ 新增 Probability 列不影响现有分析流程
- ✅ 文件名变更不影响程序逻辑（自动添加后缀）

### 迁移建议
1. **更新下游脚本**: 如果脚本依赖固定文件名，需要更新为 `*_functions.tsv`
2. **利用 Probability 列**: 在筛选和排序时考虑使用 Probability
3. **调整阈值**: 根据实际数据分布调整 Probability 阈值

---

## 🔬 参数调优建议

如果需要调整 Probability 计算参数，可以修改以下值：

### Sigmoid 函数参数
```python
# 第404行
base_prob = 1 / (1 + math.exp(-0.3 * (ra_pct - 5)))
#                                 ↑           ↑
#                                 k          x0
```

**调整建议**:
- **增大 k (如 0.5)**: 曲线更陡峭，概率变化更剧烈
- **减小 k (如 0.2)**: 曲线更平缓，概率变化更温和
- **增大 x0 (如 10)**: 需要更高丰度才能达到 0.5 概率
- **减小 x0 (如 3)**: 较低丰度即可达到 0.5 概率

### 调整因子权重
```python
# 第407行: 置信度影响
confidence_factor = 0.9 + (avg_confidence * 0.2)
#                                            ↑
#                                      增大此值提升置信度影响

# 第410行: 宿主匹配影响
host_factor = 0.95 + ((avg_host_match - 1.0) * 0.1)
#                                                ↑
#                                      增大此值提升宿主匹配影响

# 第417行: 分类单元数量影响
taxa_factor = 1.0 + (math.log10(taxa_count + 1) * 0.05)
#                                                   ↑
#                                      增大此值提升分类单元数量影响
```

---

## 📚 相关文档

- **详细更新日志**: `s16_predictor_CHANGELOG.md`
- **使用指南**: `s16_predictor_USAGE.md`
- **v2.0 更新摘要**: `s16_predictor_UPDATE_SUMMARY.md`

---

## 🎓 科学依据

### Sigmoid 函数的选择

**为什么使用 Sigmoid 而非线性映射？**

1. **生物学合理性**: 微生物功能的存在不是线性关系
   - 低丰度 (< 1%): 可能是污染或瞬时存在
   - 中等丰度 (5-10%): 功能可能存在
   - 高丰度 (> 15%): 功能几乎确定存在

2. **数学特性**: Sigmoid 函数提供平滑过渡
   - 避免硬阈值导致的突变
   - 在中间区域提供更细致的区分

3. **参数可调**: 通过 k 和 x0 调整曲线形状
   - 适应不同研究场景和数据分布

### 多因素综合评估

**为什么使用乘法而非加法？**

1. **相互依赖**: 各因素不是独立的
   - 高丰度 + 低质量证据 ≠ 高可信度
   - 低丰度 + 高质量证据 ≠ 高可信度

2. **权重平衡**: 乘法确保任一因素过低都会降低概率
   - 避免单一高分因素掩盖其他低分因素

3. **数值稳定**: 调整因子接近 1.0，避免过度放大或缩小

---

**最后更新**: 2026-01-07
**版本**: v2.1
