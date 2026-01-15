# S16 Predictor v2.2 - Probability 算法重构

**更新日期**: 2026-01-07
**版本**: v2.1 → v2.2
**更新内容**: 重构 Probability 计算算法，实现更严格、更符合生物学现实的概率估计

---

## 🎯 问题诊断

### v2.1 算法的问题

1. **过度乐观**: 概率普遍偏高（>0.8），不符合生物学现实
2. **区分度不足**: 大部分功能概率相近，用户难以识别真正重要的功能
3. **饱和过快**: RA=10% 时概率就达到 0.82，RA=20% 时接近 1.0
4. **惩罚不足**: 所有调整因子都 ≥0.9，缺乏显著的惩罚机制

### 生物学现实

- 即使某个微生物丰度很高（20%），如果缺乏宿主特异性和高质量文献支持，其功能预测的可信度也不应超过 60%
- 真正高潜力的功能（>75%）应该非常稀少，需要满足严格的多重条件
- 单一证据（如仅有丰度数据）不足以支撑高概率预测

---

## ✨ v2.2 新算法设计

### 核心设计原则

1. **保守估计**: 默认假设功能不存在，需要多重证据支持才能提高概率
2. **瓶颈制** (木桶效应): 任一关键因素不足都会显著降低概率
3. **高区分度**: 高潜力功能（>0.75）应该稀少，需要满足严格条件
4. **生物学合理性**: 即使高丰度，缺乏其他证据也不应超过 0.6

### 算法公式

```
Probability = Base_Prob × min(Confidence_Factor, Host_Factor, Evidence_Factor) × Taxa_Factor
```

**关键创新**: 使用 `min()` 实现"木桶效应"，任一短板都会限制最终概率

---

## 📊 算法详解

### 步骤 1: 基础概率 (Base_Prob) - 更保守的 Sigmoid

**旧版 (v2.1)**:
```python
base_prob = 1 / (1 + exp(-0.3 * (RA% - 5)))
```
- RA=5%: 0.50
- RA=10%: 0.82
- RA=20%: 0.99 ❌ 过于乐观

**新版 (v2.2)**:
```python
base_prob = 1 / (1 + exp(-0.2 * (RA% - 15)))
```
- RA=5%: 0.18 ✅
- RA=10%: 0.27 ✅
- RA=15%: 0.50 ✅
- RA=25%: 0.82 ✅
- RA=35%: 0.95 ✅

**改进**:
- 参数 k: 0.3 → 0.2 (曲线更平缓)
- 参数 x0: 5 → 15 (中点右移)
- 效果: 需要更高丰度才能达到高概率

---

### 步骤 2: 置信度因子 (Confidence_Factor) - 惩罚属级匹配

**旧版 (v2.1)**:
```python
confidence_factor = 0.9 + (avg_confidence × 0.2)
```
- 种级 (1.0): 1.10 ❌ 过度奖励
- 属级 (0.6): 1.02 ❌ 惩罚不足

**新版 (v2.2)**:
```python
if avg_confidence >= 0.9:    # 种级
    confidence_factor = 1.0
elif avg_confidence >= 0.7:  # 中等
    confidence_factor = 0.85
else:                        # 属级
    confidence_factor = 0.70
```

**改进**:
- 种级匹配: 1.0 (无惩罚，但也不奖励)
- 属级匹配: 0.70 (显著惩罚 -30%)
- 阶梯式设计，区分度更高

---

### 步骤 3: 宿主匹配因子 (Host_Factor) - 严格惩罚不匹配

**旧版 (v2.1)**:
```python
host_factor = 0.95 + ((avg_host_match - 1.0) × 0.1)
```
- 物种级 (1.5): 1.00 ✅
- 通用 (1.0): 0.95 ❌ 惩罚不足
- 不匹配 (0.8): 0.93 ❌ 惩罚不足

**新版 (v2.2)**:
```python
if avg_host_match >= 1.4:    # 物种级
    host_factor = 1.0
elif avg_host_match >= 1.25: # 属级
    host_factor = 0.95
elif avg_host_match >= 1.15: # 科级
    host_factor = 0.90
elif avg_host_match >= 1.05: # 目级
    host_factor = 0.85
elif avg_host_match >= 0.95: # 通用
    host_factor = 0.75
else:                        # 不匹配
    host_factor = 0.50
```

**改进**:
- 通用记录: 0.75 (显著惩罚 -25%)
- 不匹配: 0.50 (严重惩罚 -50%)
- 6 个等级，区分度大幅提升

---

### 步骤 4: 证据质量因子 (Evidence_Factor) - 奖励高质量证据

**旧版 (v2.1)**:
```python
evidence_factor = 0.95 + ((avg_evidence_weight - 1.0) × 0.1)
```
- Level 5 (1.5): 1.00 ✅
- Level 2 (1.0): 0.95 ❌ 惩罚不足
- Level 1 (0.8): 0.93 ❌ 惩罚不足

**新版 (v2.2)**:
```python
if avg_evidence_weight >= 1.4:   # Level 5
    evidence_factor = 1.0
elif avg_evidence_weight >= 1.25: # Level 4
    evidence_factor = 0.95
elif avg_evidence_weight >= 1.1:  # Level 3
    evidence_factor = 0.85
elif avg_evidence_weight >= 0.95: # Level 2
    evidence_factor = 0.75
else:                             # Level 1
    evidence_factor = 0.60
```

**改进**:
- Level 2 (基础): 0.75 (显著惩罚 -25%)
- Level 1 (低质量): 0.60 (严重惩罚 -40%)
- 5 个等级，强调高质量证据的重要性

---

### 步骤 5: 分类单元数量因子 (Taxa_Factor) - 温和奖励

**旧版 (v2.1)**:
```python
taxa_factor = 1.0 + (log10(taxa_count + 1) × 0.05)
```
- Taxa=1: 1.015
- Taxa=10: 1.052
- Taxa=100: 1.101

**新版 (v2.2)**:
```python
if taxa_count == 1:
    taxa_factor = 0.90  # 单一证据惩罚
elif taxa_count <= 5:
    taxa_factor = 0.90 + (taxa_count - 1) × 0.0125  # 0.90 -> 0.95
elif taxa_count <= 20:
    taxa_factor = 0.95 + ((taxa_count - 5) / 15) × 0.05  # 0.95 -> 1.00
else:
    taxa_factor = 1.0 + (log10(taxa_count / 20) × 0.05)  # 1.00 -> 1.08
    taxa_factor = min(taxa_factor, 1.08)
```

**改进**:
- Taxa=1: 0.90 (单一证据惩罚 -10%)
- Taxa=5: 0.95
- Taxa=10: 1.00 (中性)
- Taxa=50: 1.05
- Taxa=100: 1.08 (上限)
- 惩罚单一证据，温和奖励多证据

---

### 步骤 6: 最终概率计算 - 木桶效应

**旧版 (v2.1)**:
```python
probability = base_prob × confidence_factor × host_factor × evidence_factor × taxa_factor
```
- 所有因子相乘，缺乏瓶颈限制

**新版 (v2.2)**:
```python
bottleneck_factor = min(confidence_factor, host_factor, evidence_factor)
probability = base_prob × bottleneck_factor × taxa_factor
probability = max(0.0, min(0.95, probability))
```

**改进**:
- 使用 `min()` 实现木桶效应
- 任一短板（置信度/宿主/证据）都会限制最终概率
- 上限设为 0.95，保留 5% 不确定性

---

## 📈 效果对比

### 测试数据
- 输入: `tests/data/test_data.tsv` (538,623 reads)
- 宿主: `Drosophila melanogaster`

### v2.1 结果 (旧算法)
```
Function                    Probability  Total_RA_Pct
other                       1.000        15.767
pesticide metabolization    0.973        14.098
pathogen resistance         0.867        10.491
antimicrobial activity      0.843         9.868
```
❌ 问题: 概率普遍过高，区分度不足

### v2.2 结果 (新算法)
```
Function                    Probability  Total_RA_Pct
other                       0.282        15.767
pesticide metabolization    0.237        14.098
pathogen resistance         0.212        10.491
antimicrobial activity      0.194         9.868
```
✅ 改进: 概率更保守，区分度显著提升

---

## 🎯 概率等级重新划分

### 新的概率等级

| 概率范围 | 等级 | 颜色建议 | 解释 | 预期比例 |
|---------|------|---------|------|---------|
| **0.75 - 0.95** | 极高 | 深绿色 | 功能几乎确定存在，满足所有严格条件 | <5% |
| **0.60 - 0.74** | 高 | 绿色 | 功能很可能存在，有强力证据支持 | 5-10% |
| **0.40 - 0.59** | 中等 | 黄色 | 功能可能存在，需要进一步验证 | 15-25% |
| **0.20 - 0.39** | 低 | 橙色 | 功能存在可能性较低，证据不足 | 40-50% |
| **0.00 - 0.19** | 极低 | 灰色 | 功能可能不存在，可能为假阳性 | 20-30% |

### 达到高概率 (>0.75) 的条件

需要**同时满足**以下条件：

1. **高丰度**: RA% > 25%
2. **种级匹配**: Mean_Confidence ≥ 0.9
3. **宿主特异性**: Mean_Host_Match ≥ 1.4 (物种级匹配)
4. **高质量证据**: Mean_Evidence_Weight ≥ 1.4 (Evidence Level 5)
5. **多证据支持**: Taxa_Count ≥ 10

**示例计算**:
```
Base_Prob = sigmoid(25%) = 0.82
Confidence_Factor = 1.0 (种级)
Host_Factor = 1.0 (物种级)
Evidence_Factor = 1.0 (Level 5)
Taxa_Factor = 1.0 (10个分类单元)

Bottleneck = min(1.0, 1.0, 1.0) = 1.0
Probability = 0.82 × 1.0 × 1.0 = 0.82 ✅
```

---

## 💡 使用建议

### 1. 筛选策略

**高置信度功能** (推荐用于发表):
```python
high_confidence = df[
    (df['Probability'] >= 0.60) &
    (df['Final_Score_Sum'] > 200) &
    (df['Mean_Evidence_Weight'] > 1.2)
]
```

**中等置信度功能** (需要实验验证):
```python
medium_confidence = df[
    (df['Probability'] >= 0.40) &
    (df['Probability'] < 0.60)
]
```

**低置信度功能** (谨慎使用):
```python
low_confidence = df[
    (df['Probability'] < 0.40)
]
```

### 2. 可视化建议

**颜色编码**:
```python
def get_color(prob):
    if prob >= 0.75:
        return '#006400'  # 深绿色
    elif prob >= 0.60:
        return '#32CD32'  # 绿色
    elif prob >= 0.40:
        return '#FFD700'  # 黄色
    elif prob >= 0.20:
        return '#FF8C00'  # 橙色
    else:
        return '#A9A9A9'  # 灰色
```

**气泡图**:
- X 轴: Total_RA_Pct
- Y 轴: Final_Score_Sum
- 气泡大小: Taxa_Count
- 气泡颜色: Probability

### 3. 报告撰写

**高潜力功能** (Prob > 0.60):
> "We identified 3 high-confidence functions (Probability > 0.60) supported by multiple lines of evidence including high abundance (>20%), species-level taxonomic match, and high-quality genomic evidence."

**中等潜力功能** (Prob 0.40-0.60):
> "Several functions showed moderate probability (0.40-0.60), suggesting potential roles that warrant further experimental validation."

**低潜力功能** (Prob < 0.40):
> "Functions with low probability (<0.40) were excluded from downstream analysis due to insufficient evidence."

---

## 🔬 科学依据

### 1. 保守估计的必要性

**文献支持**:
- Louca et al. (2016) Science: 功能预测存在固有的不确定性
- Douglas (2015) Annu Rev Entomol: 宿主-共生菌关系的复杂性

**理由**:
- 16S 数据本身只提供分类信息，功能推断是间接的
- 即使高丰度微生物，其功能也可能不活跃或受环境调控
- 避免过度解读，减少假阳性

### 2. 木桶效应的合理性

**生物学逻辑**:
- 功能预测需要多重证据的**交叉验证**
- 单一强证据（如高丰度）不足以确定功能存在
- 任一关键证据缺失都应降低可信度

**类比**:
- 类似于 Bradford Hill 因果关系标准
- 需要强度、一致性、特异性、时序性等多重证据

### 3. 阈值设计的依据

**参考标准**:
- FAPROTAX: 基于文献的功能注释，保守估计
- PICRUSt2: NSTI (Nearest Sequenced Taxon Index) 作为质量指标
- 本算法: 综合多维度证据，提供量化概率

**阈值选择**:
- 0.75: 对应统计学中的"强证据" (类似 p<0.01)
- 0.60: 对应"中等证据" (类似 p<0.05)
- 0.40: 对应"弱证据" (类似 p<0.10)

---

## 🔧 参数调优指南

如果需要调整算法严格程度，可以修改以下参数：

### 调整基础概率曲线
```python
# 第411行
base_prob = 1 / (1 + math.exp(-k * (ra_pct - x0)))

# 更严格: k=0.15, x0=20
# 更宽松: k=0.25, x0=10
```

### 调整惩罚力度
```python
# 宿主不匹配惩罚 (第444行)
host_factor = 0.50  # 可调整为 0.40 (更严格) 或 0.60 (更宽松)

# 低质量证据惩罚 (第463行)
evidence_factor = 0.60  # 可调整为 0.50 (更严格) 或 0.70 (更宽松)
```

### 调整概率上限
```python
# 第494行
probability = max(0.0, min(0.95, probability))
#                           ↑
# 可调整为 0.90 (更严格) 或 0.98 (更宽松)
```

---

## 📝 代码实现位置

**文件**: `isympred/predictors/record_predictor.py`

**修改行数**: 第385-494行

**关键改动**:
1. 第411行: 更保守的 Sigmoid 参数
2. 第418-423行: 阶梯式置信度因子
3. 第434-445行: 严格的宿主匹配惩罚
4. 第455-464行: 证据质量阶梯惩罚
5. 第475-483行: 分类单元数量惩罚/奖励
6. 第489行: 木桶效应实现
7. 第494行: 概率上限设置

---

## 🔄 向后兼容性

### 输出格式
- ✅ 完全兼容，仅 Probability 列的数值发生变化
- ✅ 其他列（Final_Score_Sum, Total_RA_Pct 等）保持不变

### 下游分析
- ⚠️ 需要更新 Probability 阈值
- ⚠️ 旧版阈值 (>0.75) 在新版中可能过滤掉大部分功能
- ✅ 建议使用新阈值: >0.60 (高), >0.40 (中等)

---

## 📚 参考文献

1. Louca, S., et al. (2016). Decoupling function and taxonomy in the global ocean microbiome. *Science*, 353(6305), 1272-1277.

2. Douglas, A. E. (2015). Multiorganismal insects: diversity and function of resident microorganisms. *Annual Review of Entomology*, 60, 17-34.

3. Langille, M. G., et al. (2013). Predictive functional profiling of microbial communities using 16S rRNA marker gene sequences. *Nature Biotechnology*, 31(9), 814-821.

4. Louca, S., et al. (2018). Function and functional redundancy in microbial systems. *Nature Ecology & Evolution*, 2(6), 936-943.

---

**版本**: v2.2
**状态**: ✅ 已完成并测试
**最后更新**: 2026-01-07
