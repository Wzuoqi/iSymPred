# RecordPredictor 设计原理与架构分析

**文档版本**: v1.0
**创建日期**: 2026-01-14
**脚本版本**: v4.6 (当前分析版本)
**分析对象**: `isympred/predictors/record_predictor.py`

---

## 一、核心设计目标

### 1.1 科学目标
`RecordPredictor` 是 iSymPred 项目的核心预测引擎，旨在基于 **16S 扩增子测序数据** 预测昆虫共生菌的功能。其设计目标包括：

1. **宿主上下文感知 (Host-Context Awareness)**
   - 不同宿主中的同一共生菌可能执行不同功能
   - 需要整合宿主分类信息（目、科、属、种）进行精准匹配

2. **证据质量分级 (Evidence-Level Weighting)**
   - 文献证据质量差异显著（顶刊 vs 普通期刊，基因组证据 vs 仅分类记录）
   - 需要量化证据强度，避免低质量数据污染预测结果

3. **多层次分类匹配 (Hierarchical Taxonomic Matching)**
   - 种级匹配（最精确）> 属级匹配（次精确）
   - 需要在缺乏种级信息时回退到属级预测

4. **概率化预测 (Probabilistic Prediction)**
   - 避免二元判断（有/无功能），提供连续概率值
   - 整合多重证据（丰度、宿主匹配、证据质量、分类单元数量）

5. **机器学习友好 (ML-Ready Feature Engineering)**
   - 生成标准化特征矩阵，支持随机森林等监督学习模型
   - 特征设计遵循生物学可解释性原则

---

## 二、核心算法架构

### 2.1 整体流程图

```
[输入 OTU 表]
    ↓
[解析分类信息] → 提取 Genus, Species
    ↓
[数据库匹配] → 种级匹配 / 属级匹配
    ↓
[宿主上下文查询] → NCBI Taxonomy (ete3)
    ↓
[多维度评分]
    ├─ 基础分数 (Base Score): 丰度 × 分类置信度
    ├─ 宿主匹配权重 (Host Match Weight): 1.5 (物种) ~ 0.8 (不匹配)
    └─ 证据等级权重 (Evidence Weight): 1.5 (Level 5) ~ 0.8 (Level 1)
    ↓
[概率计算] → 木桶效应 (Bottleneck Principle)
    ↓
[输出三张表]
    ├─ 功能汇总表 (Function Summary)
    ├─ 匹配记录明细 (Match Records)
    └─ 特征矩阵 (Feature Matrix for ML)
```

---

## 三、关键设计原理

### 3.1 宿主上下文匹配系统

#### 3.1.1 设计动机
传统工具（如 FAPROTAX）忽略宿主特异性，导致预测结果泛化。例如：
- *Buchnera aphidicola* 在蚜虫中合成必需氨基酸
- 同属细菌在其他宿主中可能功能不同

#### 3.1.2 实现机制
**宿主分类查询 (ete3 + NCBI Taxonomy)**
- 用户提供宿主拉丁名（如 *Apis mellifera*）
- 通过 `ete3.NCBITaxa` 查询完整分类谱系（目、科、属、种）
- 计算用户宿主与数据库宿主的分类学距离

**匹配权重分级**
```python
HOST_MATCH_WEIGHTS = {
    'species': 1.5,   # 物种级精确匹配（最高可信度）
    'genus': 1.3,     # 属级匹配
    'family': 1.2,    # 科级匹配
    'order': 1.1,     # 目级匹配
    'general': 1.0,   # 通用记录（无宿主特异性）
    'mismatch': 0.8   # 完全不匹配（显著惩罚）
}
```

**分类学距离计算**
- 基于最近公共祖先 (LCA - Lowest Common Ancestor)
- 距离定义：
  - 0: 同一物种
  - 1: 同属不同种
  - 2: 同科不同属
  - 3: 同目不同科
  - 4-6: 更远的分类关系
  - 999: 无法计算（缺少分类信息）

---

### 3.2 证据等级分级系统

#### 3.2.1 设计动机
文献证据质量差异巨大：
- **高质量证据**: 顶刊 + 基因组测序 + 功能实验验证
- **低质量证据**: 仅基于 16S 分类，无功能验证

#### 3.2.2 证据等级定义
```python
EVIDENCE_LEVEL_WEIGHTS = {
    5: 1.5,  # 最高证据（Symbiont + Genome + Top Journal）
    4: 1.3,  # 高证据（Symbiont + Genome）
    3: 1.15, # 中等证据（Symbiont + Top Journal）
    2: 1.0,  # 基础证据（Symbiont only）
    1: 0.8   # 低证据（仅分类记录）
}
```

#### 3.2.3 应用场景
- 数据库构建时，人工标注每条记录的证据等级
- 预测时，高证据等级的记录获得更高权重
- 避免低质量数据主导预测结果

---

### 3.3 多维度评分系统

#### 3.3.1 基础分数 (Base Score)
**公式**:
```
Base_Score = Confidence_Weight × log10(RA% + 1) × 100
```

**参数说明**:
- `Confidence_Weight`: 分类匹配置信度
  - 种级匹配: 1.0
  - 属级匹配: 0.6
- `RA%`: 相对丰度百分比 (0-100)
- `log10` 变换: 线性化丰度分布，避免高丰度 OTU 主导
- `× 100`: 缩放因子，使分数在 0-200 范围内

**设计原理**:
- 对数变换压缩高丰度差异，放大低丰度信号
- 例如：RA=1% → log=0.30, RA=10% → log=1.04, RA=50% → log=1.71

#### 3.3.2 最终分数 (Final Score)
**公式**:
```
Final_Score = Base_Score × Host_Match_Weight × Evidence_Weight
```

**设计原理**:
- 乘法模型：任一维度不足都会显著降低分数
- 体现"多重证据支持"的科学原则
- 避免单一高丰度 OTU 在宿主不匹配时获得高分

---

### 3.4 概率计算系统 (Probability Estimation)

#### 3.4.1 设计哲学
**保守估计原则 (Conservative Estimation)**
- 默认假设功能不存在，需要多重证据支持才能提高概率
- 高概率预测（>0.75）应该稀少，需要满足严格条件
- 即使高丰度，缺乏其他证据也不应超过 0.6

**木桶效应 (Bottleneck Principle)**
- 任一关键因素不足都会显著降低概率
- 使用 `min()` 函数实现短板限制
- 避免单一维度优势掩盖其他维度缺陷

#### 3.4.2 概率计算公式
```
Probability = Base_Prob × Bottleneck_Factor × Taxa_Factor

其中:
Bottleneck_Factor = min(Confidence_Factor, Host_Factor, Evidence_Factor)
```

**步骤 1: 基础概率 (Base_Prob) - Sigmoid 变换**
```python
base_prob = 1 / (1 + exp(-0.2 × (RA% - 15)))
```
- 参数: k=0.2 (平缓曲线), x0=15 (中点)
- 效果:
  - RA=5%  → 0.18 (低)
  - RA=15% → 0.50 (中等)
  - RA=25% → 0.82 (高)
  - RA=35% → 0.95 (极高)

**步骤 2: 置信度因子 (Confidence_Factor)**
```python
if avg_confidence >= 0.9:  # 种级匹配
    confidence_factor = 1.0
elif avg_confidence >= 0.7:  # 中等置信度
    confidence_factor = 0.85
else:  # 属级匹配
    confidence_factor = 0.70
```

**步骤 3: 宿主匹配因子 (Host_Factor)**
```python
if avg_host_match >= 1.4:  # 物种级
    host_factor = 1.0
elif avg_host_match >= 1.25:  # 属级
    host_factor = 0.95
elif avg_host_match >= 1.15:  # 科级
    host_factor = 0.90
elif avg_host_match >= 1.05:  # 目级
    host_factor = 0.85
elif avg_host_match >= 0.95:  # 通用记录
    host_factor = 0.75
else:  # 不匹配
    host_factor = 0.50
```

**步骤 4: 证据质量因子 (Evidence_Factor)**
```python
if avg_evidence_weight >= 1.4:  # Level 5
    evidence_factor = 1.0
elif avg_evidence_weight >= 1.25:  # Level 4
    evidence_factor = 0.95
elif avg_evidence_weight >= 1.1:  # Level 3
    evidence_factor = 0.85
elif avg_evidence_weight >= 0.95:  # Level 2
    evidence_factor = 0.75
else:  # Level 1
    evidence_factor = 0.60
```

**步骤 5: 分类单元数量因子 (Taxa_Factor)**
```python
if taxa_count == 1:
    taxa_factor = 0.90  # 单一证据惩罚
elif taxa_count <= 5:
    taxa_factor = 0.90 + (taxa_count - 1) × 0.0125
elif taxa_count <= 20:
    taxa_factor = 0.95 + ((taxa_count - 5) / 15) × 0.05
else:
    taxa_factor = 1.0 + (log10(taxa_count / 20) × 0.05)
    taxa_factor = min(taxa_factor, 1.08)  # 上限 1.08
```

**最终概率**:
```python
probability = base_prob × min(confidence_factor, host_factor, evidence_factor) × taxa_factor
probability = max(0.0, min(0.95, probability))  # 限制在 [0, 0.95]
```

#### 3.4.3 设计亮点
1. **木桶效应**: 使用 `min()` 确保任一短板都会限制最终概率
2. **保守上限**: 即使所有条件完美，概率上限为 0.95（保留 5% 不确定性）
3. **生物学合理性**: 高丰度 + 低证据质量 → 中等概率（~0.5-0.6）
4. **区分度**: 高潜力功能（>0.75）稀少，需要满足严格条件

---

### 3.5 特征工程系统 (Feature Matrix for ML)

#### 3.5.1 设计目标
生成标准化特征矩阵，支持随机森林等监督学习模型训练，用于：
- 功能预测的二分类任务（功能存在 vs 不存在）
- 功能重要性排序
- 模型可解释性分析

#### 3.5.2 特征设计原则
**v4.6 核心特征 (8 个非冗余特征)**

1. **Log_Abundance** (对数丰度)
   - 公式: `log10(RA% + 1)`
   - 作用: 线性化丰度分布，移除偏态
   - 移除冗余: 删除 `Relative_Abundance_Pct`（与 Log_Abundance 高度共线）

2. **Match_Level_Score** (分类匹配置信度)
   - 取值: 1.0 (种级) / 0.6 (属级)
   - 作用: 量化分类匹配精度

3. **Host_Match_Weight_Max** (最佳宿主匹配权重)
   - 取值: 0.8-1.5
   - 作用: 反映宿主特异性（天花板原则）
   - 移除冗余: 删除 `Host_Match_Weight_Mean`（关注潜力天花板）
   - 移除冗余: 删除 `Taxonomic_Distance_Min`（与 Host_Match_Weight_Max 逻辑重复）

4. **Evidence_Level_Max** (最高证据等级)
   - 取值: 1-5
   - 作用: 反映文献证据质量（最高证据原则）
   - 移除冗余: 删除 `Evidence_Level_Mean`（遵循"最高证据原则"）

5. **Adjusted_Score_Max** (最高综合质量分数)
   - 公式: `Base_Score × (Host_Match_Weight^2) × (Evidence_Weight^1.5)`
   - 作用: 整合多维度质量指标，用于排序
   - 移除冗余: 删除 `Bottleneck_Score`（特征重叠）

6. **DB_Literature_Count** (文献支持数量)
   - 计算: 基于 DOI 去重统计
   - 作用: 反映该预测的文献支持度
   - 优化: 同一篇文献在不同宿主中的记录只算 1 次

7. **Shannon_Index** (α多样性) ⭐ **v4.6 新增**
   - 公式: `Shannon Index = -Σ(pi × ln(pi))`
   - 作用: 反映微生物组的多样性，可能影响共生菌功能表达
   - 特点: 样本级别特征（所有 Taxon-Function 对相同）

8. **Rank_By_Abundance** (丰度排名)
   - 取值: 1 (最高丰度), 2, 3, ...
   - 作用: 相对排名，补充绝对丰度信息
   - 移除冗余: 删除 `Function_Support_Count`（描述群落而非特定分类单元）

#### 3.5.3 特征创新点
- **Shannon_Index**: 捕获群落级别上下文，高多样性可能影响共生菌功能表达
- **天花板原则**: 使用 `_Max` 而非 `_Mean`，关注最佳潜力而非平均水平
- **DOI 去重**: 文献计数基于唯一 DOI，避免重复记录夸大支持度
- **非冗余设计**: 移除 6 个冗余特征，保留 8 个核心特征

---

## 四、数据流与输出

### 4.1 输入数据
**OTU 表 (TSV 格式)**
```
Taxon                                           Abundance
k__Bacteria;p__Proteobacteria;...;g__Buchnera  1250.5
k__Bacteria;p__Proteobacteria;...;g__Wolbachia 320.2
```

**共生菌数据库 (record_db.tsv)**
```
taxonomy    function    host    host_order    host_family    evidence_level    description    evidence
g__Buchnera;s__aphidicola    Nutrition_Essential_AA    Aphid    Hemiptera    Aphididae    5    ...    DOI:xxx
```

**宿主信息 (可选)**
```
--host "Apis mellifera"
```

### 4.2 输出数据

#### 4.2.1 功能汇总表 (Function Summary)
**文件名**: `*_functions.tsv`

**列说明**:
- `Function`: 预测的功能类别
- `Final_Score_Sum`: 最终总分（整合所有权重）
- `Total_RA_Pct`: 该功能的总相对丰度
- `Mean_Confidence`: 平均分类置信度
- `Mean_Host_Match`: 平均宿主匹配权重
- `Mean_Evidence_Weight`: 平均证据等级权重
- `Taxa_Count`: 支持该功能的分类单元数量
- `Probability`: 功能存在概率 (0-0.95)
- `Dominant_Contributor`: 主要贡献者（占比最高的分类单元）
- `Contributor_List`: 所有贡献者的属名列表（逗号分隔）

**排序**: 按 `Final_Score_Sum` 降序

#### 4.2.2 匹配记录明细 (Match Records)
**文件名**: `*_match_records.tsv`

**列说明**:
- `Symbiont_Taxon`: 共生菌分类名
- `Predicted_Function`: 预测功能
- `Adjusted_Score`: 调整后分数（强化宿主匹配和证据等级）
- `Quality_Score`: 综合质量指标
- `Base_Score`: 基础分数
- `Host_Match_Weight`: 宿主匹配权重
- `Host_Match_Level`: 宿主匹配等级（Species/Genus/Family/Order/General/Mismatch）
- `Evidence_Level`: 证据等级 (1-5)
- `Evidence_Weight`: 证据权重
- `Match_Level`: 分类匹配等级（Species/Genus）
- `Relative_Abundance_Pct`: 相对丰度百分比
- `DB_Host_Context`: 数据库中的宿主上下文
- `DB_Description`: 功能描述
- `DB_Evidence`: 文献证据（DOI）

**优化策略**:
- 每个 `Symbiont_Taxon` 只保留 Top 5 记录（避免冗余）
- 按 `Adjusted_Score` 和 `Quality_Score` 排序

#### 4.2.3 特征矩阵 (Feature Matrix)
**文件名**: `*_feature_matrix.tsv`

**列说明**:
- `Taxon`: 分类单元
- `Function`: 功能类别
- `Log_Abundance`: 对数丰度
- `Match_Level_Score`: 分类匹配分数
- `Host_Match_Weight_Max`: 最佳宿主匹配权重
- `Evidence_Level_Max`: 最高证据等级
- `Adjusted_Score_Max`: 最高综合质量分数
- `DB_Literature_Count`: 文献支持数量
- `Shannon_Index`: α多样性
- `Rank_By_Abundance`: 丰度排名

**用途**:
- 随机森林训练
- 功能预测模型
- 特征重要性分析

---

## 五、技术实现细节

### 5.1 依赖库
- **pandas**: 数据处理
- **numpy**: 数值计算
- **ete3**: NCBI Taxonomy 查询（替代本地 SQLite 数据库）
- **re**: 正则表达式解析分类字符串

### 5.2 关键方法

#### 5.2.1 `_query_host_taxonomy_ete3()`
- 功能: 查询宿主的完整分类谱系
- 输入: 宿主拉丁名（如 *Apis mellifera*）
- 输出: `{'order': '...', 'family': '...', 'genus': '...', 'species': '...', 'taxid': int, 'lineage': list}`
- 实现: 调用 `ete3.NCBITaxa` API

#### 5.2.2 `_calculate_taxonomic_distance()`
- 功能: 计算用户宿主与数据库宿主的分类学距离
- 算法: 基于最近公共祖先 (LCA)
- 输出: 0-6 (距离等级), 999 (无法计算)

#### 5.2.3 `_calculate_host_match_score()`
- 功能: 计算宿主匹配权重
- 输入: 数据库宿主信息（物种、目、科）
- 输出: 0.8-1.5 (权重值)
- 逻辑: 物种级 > 属级 > 科级 > 目级 > 通用 > 不匹配

#### 5.2.4 `_load_database()`
- 功能: 加载共生菌数据库
- 输出: 两个字典
  - `species_map`: 种级索引
  - `genus_map`: 属级索引
- 优化: 预处理分类字符串，提取 Genus 和 Species

#### 5.2.5 `predict()`
- 功能: 主预测流程
- 步骤:
  1. 读取 OTU 表
  2. 计算 Shannon Index
  3. 遍历每个 OTU，匹配数据库
  4. 计算多维度评分
  5. 聚合功能结果
  6. 计算概率
  7. 生成三张输出表

---

## 六、设计优势与创新点

### 6.1 科学创新
1. **宿主上下文整合**: 首次在功能预测中系统性整合宿主分类信息
2. **证据质量分级**: 量化文献证据强度，避免低质量数据污染
3. **概率化预测**: 提供连续概率值，而非二元判断
4. **木桶效应**: 多维度短板限制，符合生物学保守估计原则
5. **α多样性整合**: 将群落级别特征纳入预测模型

### 6.2 工程优势
1. **模块化设计**: 清晰的方法分离，易于维护和扩展
2. **外部依赖最小化**: 使用 ete3 替代本地数据库，减少部署复杂度
3. **特征工程优化**: 移除冗余特征，提高模型训练效率
4. **输出多样化**: 三张表满足不同分析需求（汇总、明细、机器学习）
5. **可解释性**: 所有评分和概率计算都有明确的生物学意义

### 6.3 与现有工具对比
| 特性 | FAPROTAX | PICRUSt2 | RecordPredictor |
|------|----------|----------|-----------------|
| 宿主上下文 | ❌ | ❌ | ✅ |
| 证据质量分级 | ❌ | ❌ | ✅ |
| 概率化预测 | ❌ | ✅ | ✅ |
| 分类学距离 | ❌ | ❌ | ✅ |
| 机器学习支持 | ❌ | ❌ | ✅ |
| α多样性整合 | ❌ | ❌ | ✅ |

---

## 七、已知限制与未来改进

### 7.1 当前限制
1. **数据库依赖**: 预测质量高度依赖数据库完整性和准确性
2. **宿主信息可选**: 未提供宿主信息时，宿主匹配权重失效
3. **单样本分析**: 当前版本仅支持单样本输入
4. **计算效率**: 大规模数据集（>10000 OTUs）可能较慢

### 7.2 未来改进方向
1. **批量样本支持**: 支持多样本并行分析
2. **宿主自动推断**: 基于微生物组特征自动推断宿主类型
3. **功能层级聚合**: 基于 Ontology 进行功能层级汇总
4. **可视化模块**: 生成功能热图、网络图等
5. **性能优化**: 使用多进程或 GPU 加速

---

## 八、使用建议

### 8.1 最佳实践
1. **提供宿主信息**: 强烈建议提供宿主拉丁名，显著提高预测准确性
2. **数据质量控制**: 输入 OTU 表应经过质控（去除嵌合体、低丰度过滤）
3. **结果解读**: 关注 `Probability > 0.6` 的功能，低概率功能需谨慎解读
4. **多重验证**: 结合文献证据和实验验证，避免过度依赖预测结果

### 8.2 参数调优
- **丰度阈值**: 可在预处理时过滤低丰度 OTU（如 RA < 0.1%）
- **概率阈值**: 根据研究目的调整概率阈值（保守: >0.7, 宽松: >0.5）
- **Top N 记录**: 可调整 Match Records 中每个 Taxon 保留的记录数（默认 5）

---

## 九、版本历史

### v4.6 (当前版本)
- **新增**: Shannon_Index 特征（α多样性）
- **优化**: 特征矩阵精简至 8 个核心特征
- **优化**: DOI 去重统计文献数量
- **优化**: 调整后分数公式（强化宿主匹配和证据等级）

### v4.x (历史版本)
- v4.5: 引入 Quality_Score 综合质量指标
- v4.0: 实现概率计算系统（木桶效应）
- v3.0: 整合证据等级权重
- v2.0: 实现宿主上下文匹配
- v1.0: 基础功能预测框架

---

## 十、总结

`RecordPredictor` 是一个科学严谨、工程优雅的共生菌功能预测系统。其核心创新在于：

1. **多维度整合**: 丰度 + 分类 + 宿主 + 证据质量
2. **保守估计**: 木桶效应 + 概率上限
3. **机器学习友好**: 标准化特征矩阵 + 非冗余设计
4. **生物学可解释性**: 所有评分都有明确的生物学意义

该系统适用于昆虫微生物组研究、共生菌功能注释、宏基因组功能分析等场景，为研究者提供了一个强大的功能预测工具。

---

**文档结束**
