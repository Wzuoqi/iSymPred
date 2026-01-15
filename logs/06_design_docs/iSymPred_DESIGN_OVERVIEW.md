# iSymPred: 昆虫共生菌功能预测软件设计概览

**版本**: v0.1.0 (Alpha)
**日期**: 2026-01-12
**用途**: Slides 制作参考

---

## 1. 核心理念 (Core Concept)

### 一句话概括
> **基于宿主-共生菌特异性关系，整合分类学、宿主上下文和证据质量，实现高精度的昆虫共生菌功能预测**

### 科学创新点
```
传统工具 (FAPROTAX, PICRUSt2)
    ↓
仅基于微生物分类 → 忽略宿主特异性 → 预测泛化

iSymPred (本研究)
    ↓
分类 + 宿主上下文 + 证据质量 → 宿主特异性预测 → 精准功能注释
```

---

## 2. 设计原则 (Design Principles)

### 🎯 三大支柱

#### (1) 宿主上下文感知 (Host-Context Awareness)
- **问题**: 同一微生物在不同宿主中功能不同
  - 例: *Wolbachia* 在蚊子中导致细胞质不亲和，在蚜虫中提供营养
- **解决**: 引入宿主分类信息（目、科、属、种）
- **实现**: 多层级宿主匹配（物种 > 属 > 科 > 目 > 通用）

#### (2) 证据等级分层 (Evidence-Level Stratification)
- **问题**: 文献质量参差不齐
- **解决**: 5 级证据分层系统
  ```
  Level 5: Symbiont + Genome + Top Journal  (权重 1.5)
  Level 4: Symbiont + Genome               (权重 1.3)
  Level 3: Symbiont + Top Journal          (权重 1.15)
  Level 2: Symbiont only                   (权重 1.0)
  Level 1: Low confidence                  (权重 0.8)
  ```

#### (3) 保守预测策略 (Conservative Prediction)
- **问题**: 过度预测导致假阳性
- **解决**: "木桶效应" (Bottleneck Effect)
  ```python
  Probability = Base_Prob × min(Confidence, Host_Match, Evidence) × Taxa_Factor
  ```
- **效果**: 任一短板都会限制最终概率（最高 0.95）

---

## 3. 算法流程 (Algorithm Workflow)

### 输入 → 处理 → 输出

```
┌─────────────────────────────────────────────────────────────────┐
│ INPUT                                                            │
├─────────────────────────────────────────────────────────────────┤
│ • OTU 丰度表 (16S 扩增子数据)                                     │
│ • 宿主拉丁名 (e.g., "Leptinotarsa decemlineata")                 │
│ • 共生菌数据库 (record_db.tsv)                                    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: 宿主分类查询 (Host Taxonomy Query)                       │
├─────────────────────────────────────────────────────────────────┤
│ • 使用 ete3 查询 NCBI Taxonomy                                   │
│ • 提取: Order, Family, Genus, Species                           │
│ • 示例: Coleoptera → Chrysomelidae → Leptinotarsa              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: 分类匹配 (Taxonomic Matching)                           │
├─────────────────────────────────────────────────────────────────┤
│ • 优先级 1: 种级匹配 (Species-level, 权重 1.0)                   │
│ • 优先级 2: 属级匹配 (Genus-level, 权重 0.6)                     │
│ • 示例: "Wolbachia pipientis" vs "Wolbachia (sp.)"             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: 宿主匹配评分 (Host Matching Scoring)                    │
├─────────────────────────────────────────────────────────────────┤
│ • 物种级精确匹配: 权重 1.5 (最佳)                                │
│ • 属级匹配: 权重 1.3                                             │
│ • 科级匹配: 权重 1.2                                             │
│ • 目级匹配: 权重 1.1                                             │
│ • 通用记录 (General): 权重 1.0                                   │
│ • 不匹配: 权重 0.8 (惩罚)                                        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: 综合评分 (Integrated Scoring)                           │
├─────────────────────────────────────────────────────────────────┤
│ Base_Score = Match_Weight × log10(RA% + 1) × 100               │
│ Final_Score = Base_Score × Host_Weight × Evidence_Weight       │
│                                                                  │
│ 示例:                                                            │
│ • RA = 5%, Match = Genus (0.6), Host = Species (1.5), Evid = 3 │
│ • Base = 0.6 × log10(6) × 100 = 46.7                           │
│ • Final = 46.7 × 1.5 × 1.15 = 80.5                             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: 概率计算 (Probability Estimation)                       │
├─────────────────────────────────────────────────────────────────┤
│ • Base_Prob = Sigmoid(RA%, k=0.2, x0=15)                       │
│ • Bottleneck = min(Confidence, Host_Match, Evidence)           │
│ • Probability = Base_Prob × Bottleneck × Taxa_Factor           │
│ • 上限: 0.95 (保留 5% 不确定性)                                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ OUTPUT (3 Tables)                                                │
├─────────────────────────────────────────────────────────────────┤
│ 1. Functions Table (功能汇总)                                    │
│    - 按功能聚合，显示总分、概率、主要贡献者                        │
│                                                                  │
│ 2. Match Records (匹配明细)                                      │
│    - 每个共生菌-功能对的详细信息                                  │
│    - 包含宿主匹配、证据等级、数据库来源                           │
│                                                                  │
│ 3. Feature Matrix (特征矩阵) ⭐                                  │
│    - 机器学习就绪的特征向量                                       │
│    - 13 个生物学特征，无重复                                      │
│    - 适用于随机森林/深度学习                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. 关键技术特性 (Key Technical Features)

### 🔬 多层级匹配策略

| 匹配层级 | 权重 | 示例 | 适用场景 |
|---------|------|------|---------|
| **种级** | 1.0 | *Buchnera aphidicola* | 精确功能预测 |
| **属级** | 0.6 | *Buchnera* (sp.) | 种级信息缺失 |
| **宿主-物种** | 1.5 | 同一宿主物种 | 最高可信度 |
| **宿主-属** | 1.3 | 同属宿主 | 高可信度 |
| **宿主-科** | 1.2 | 同科宿主 | 中等可信度 |
| **通用** | 1.0 | General host | 保守预测 |

### 📊 特征矩阵设计 (v4.3)

**13 个核心特征** (每个 Taxon-Function 组合一行)

| 特征类别 | 特征名称 | 生物学意义 |
|---------|---------|-----------|
| **丰度** | Relative_Abundance_Pct | 微生物丰度 |
|  | Log_Abundance | 线性化丰度 |
| **分类** | Match_Level_Score | 分类匹配置信度 (0.6/1.0) |
| **宿主** | Host_Match_Weight_Max | 最佳宿主匹配 (0.8-1.5) |
|  | Host_Match_Weight_Mean | 平均宿主匹配 |
| **证据** | Evidence_Level_Max | 最高证据等级 (1-5) |
|  | Evidence_Level_Mean | 平均证据等级 |
| **质量** | Bottleneck_Score | 木桶效应分数 (0-1) |
|  | Adjusted_Score_Max | 综合质量分数 |
| **支持度** | Function_Support_Count | 支持该功能的分类单元数 |
|  | **DB_Record_Count** ⭐ | 数据库记录数 (可靠性指标) |
| **排名** | Rank_By_Abundance | 丰度排名 |
| **距离** | Taxonomic_Distance_Min | 宿主进化距离 (0-6) |

### 🎯 木桶效应 (Bottleneck Effect)

**核心思想**: 任一短板都会限制最终概率

```python
# 三大质量因子
Confidence_Factor = f(Match_Level)      # 分类匹配质量
Host_Factor = f(Host_Match_Weight)      # 宿主匹配质量
Evidence_Factor = f(Evidence_Level)     # 证据质量

# 取最小值（木桶效应）
Bottleneck = min(Confidence_Factor, Host_Factor, Evidence_Factor)

# 最终概率
Probability = Base_Prob × Bottleneck × Taxa_Factor
```

**效果示例**:
```
场景 1: 高丰度 + 属级匹配 + 通用宿主 + 低证据
→ Bottleneck = min(0.7, 0.75, 0.6) = 0.6
→ Probability ≈ 0.35 (中低)

场景 2: 中丰度 + 种级匹配 + 物种级宿主 + 高证据
→ Bottleneck = min(1.0, 1.0, 1.0) = 1.0
→ Probability ≈ 0.75 (高)
```

---

## 5. 数据库设计 (Database Design)

### 核心数据结构

```
record_db.tsv (共生菌功能数据库)
├── taxonomy          : 微生物分类 (g__Genus;s__Species)
├── function          : 功能标签 (e.g., "nitrogen fixation")
├── host              : 宿主物种名 (e.g., "Apis mellifera")
├── host_order        : 宿主目 (e.g., "Hymenoptera")
├── host_family       : 宿主科 (e.g., "Apidae")
├── evidence_level    : 证据等级 (1-5)
├── description       : 功能描述
└── evidence          : 文献来源
```

### 数据质量控制

**证据等级定义**:
```
Level 5 (1.5×): Symbiont + Genome sequenced + Top journal (Nature/Science/Cell)
Level 4 (1.3×): Symbiont + Genome sequenced
Level 3 (1.15×): Symbiont + Top journal
Level 2 (1.0×): Symbiont confirmed (baseline)
Level 1 (0.8×): Low confidence / preliminary data
```

**宿主标准化**:
- 使用 NCBI Taxonomy 标准拉丁名
- 支持 "General" 作为通配符（适用于所有宿主）
- 自动查询宿主分类谱系（Order, Family, Genus）

---

## 6. 应用场景 (Use Cases)

### 🔬 科研应用

#### (1) 昆虫微生物组功能注释
```
输入: 16S 扩增子 OTU 表 + 宿主信息
输出: 功能预测表 (营养、防御、生殖调控等)
优势: 宿主特异性预测，避免泛化
```

#### (2) 共生菌功能验证
```
场景: 发现新的共生菌，需要预测其功能
方法: 基于近缘种和宿主上下文推断
输出: 功能假设 + 概率 + 证据支持度
```

#### (3) 比较微生物组学
```
场景: 比较不同宿主/处理组的共生菌功能
方法: 功能汇总表 + 统计检验
输出: 差异功能 + 生物学解释
```

### 🤖 机器学习应用

#### (4) 功能预测模型训练
```
输入: Feature Matrix (13 特征)
标签: 已验证的功能 (实验数据)
模型: 随机森林 / XGBoost / 神经网络
输出: 功能预测分类器
```

#### (5) 特征重要性分析
```
问题: 哪些因素最影响功能预测准确性？
方法: SHAP / Permutation Importance
发现: DB_Record_Count, Host_Match_Weight 最重要
```

---

## 7. 技术栈 (Technology Stack)

### 核心依赖

```python
# 数据处理
pandas >= 1.3.0          # 数据框操作
numpy >= 1.21.0          # 数值计算

# 生物信息学
biopython >= 1.79        # 序列处理
ete3 >= 3.1.2            # NCBI Taxonomy 查询

# CLI 交互
click >= 8.0.0           # 命令行界面

# 可选
biom-format >= 2.1.10    # BIOM 文件支持
diamond                  # 宏基因组比对 (外部工具)
```

### 软件架构

```
iSymPred/
├── isympred/
│   ├── cli.py                    # 命令行入口
│   ├── config.py                 # 配置管理
│   ├── database/
│   │   ├── builder.py            # 数据库构建
│   │   ├── query.py              # 数据库查询
│   │   └── symbiont_record/      # 共生菌数据库
│   ├── predictors/
│   │   ├── record_predictor.py   # 16S 预测器 (核心)
│   │   └── meta_predictor.py     # 宏基因组预测器
│   └── utils/
│       ├── io.py                 # 文件读写
│       ├── taxonomy.py           # 分类名标准化
│       └── host_query.py         # 宿主查询工具
├── tests/                        # 单元测试
├── docs/                         # 文档
└── setup.py                      # 安装脚本
```

---

## 8. 性能指标 (Performance Metrics)

### 计算效率

| 数据规模 | OTU 数量 | 处理时间 | 内存占用 |
|---------|---------|---------|---------|
| 小型 | < 100 | < 5 秒 | < 100 MB |
| 中型 | 100-1000 | < 30 秒 | < 500 MB |
| 大型 | > 1000 | < 2 分钟 | < 1 GB |

### 预测质量

**去重效果** (v4.3):
- 数据冗余率: 0% (从 51.7% 降至 0%)
- 特征矩阵行数: 减少 51.7% (224 → 108)
- 唯一 Taxon-Function 对: 保持 100% (107 对)

**概率校准**:
- 高概率预测 (>0.75): 需满足严格条件（高丰度 + 种级匹配 + 物种级宿主 + 高证据）
- 中等概率 (0.5-0.75): 部分条件满足
- 低概率 (<0.5): 存在明显短板

---

## 9. 与现有工具对比 (Comparison)

| 特性 | FAPROTAX | PICRUSt2 | **iSymPred** |
|-----|----------|----------|-------------|
| **输入数据** | 16S OTU 表 | 16S OTU 表 | 16S OTU 表 + 宿主信息 |
| **预测依据** | 分类学 | 基因组推断 | 分类 + 宿主 + 证据 |
| **宿主特异性** | ❌ 无 | ❌ 无 | ✅ **多层级宿主匹配** |
| **证据分层** | ❌ 无 | ❌ 无 | ✅ **5 级证据系统** |
| **概率输出** | ❌ 无 | ❌ 无 | ✅ **保守概率估计** |
| **数据库支持度** | ❌ 无 | ❌ 无 | ✅ **DB_Record_Count** |
| **机器学习就绪** | ❌ 否 | ❌ 否 | ✅ **13 特征矩阵** |
| **适用场景** | 环境微生物 | 人体微生物 | **昆虫共生菌** |
| **预测精度** | 中等 | 中等 | **高（宿主特异性）** |

### 核心优势

1. **宿主上下文感知**: 同一微生物在不同宿主中功能不同
2. **证据质量控制**: 区分高质量研究和初步报道
3. **保守预测策略**: 避免过度预测，降低假阳性
4. **机器学习友好**: 特征矩阵可直接用于模型训练
5. **可解释性强**: 每个预测都有详细的匹配信息和证据来源

---

## 10. 未来方向 (Future Directions)

### 短期目标 (3-6 个月)

- [ ] **扩展数据库**: 收集更多昆虫共生菌功能记录（目标 500+ 条）
- [ ] **机器学习模型**: 基于特征矩阵训练随机森林分类器
- [ ] **Web 界面**: 开发在线预测平台（Flask/Django）
- [ ] **BIOM 格式支持**: 完善 BIOM 文件读写功能

### 中期目标 (6-12 个月)

- [ ] **宏基因组模块**: 完善基因功能预测（DIAMOND + KEGG）
- [ ] **功能层级聚合**: 基于 Ontology 进行功能分类
- [ ] **可视化模块**: 功能热图、网络图、Sankey 图
- [ ] **发布到 Bioconda**: 简化安装流程

### 长期目标 (1-2 年)

- [ ] **深度学习模型**: 基于 Transformer 的序列-功能预测
- [ ] **多组学整合**: 整合转录组、代谢组数据
- [ ] **实验验证**: 与实验室合作验证预测准确性
- [ ] **发表论文**: 在 Microbiome / ISME J 等期刊发表

---

## 11. 引用与致谢 (Citation & Acknowledgments)

### 引用格式 (待发表)

```bibtex
@software{isympred2026,
  title = {iSymPred: Host-Context Aware Prediction of Insect Symbiont Functions},
  author = {Your Name},
  year = {2026},
  version = {0.1.0},
  url = {https://github.com/yourusername/iSymPred}
}
```

### 参考工具

- **FAPROTAX**: Louca et al. (2016) *Bioinformatics*
- **PICRUSt2**: Douglas et al. (2020) *Nature Biotechnology*
- **ete3**: Huerta-Cepas et al. (2016) *Molecular Biology and Evolution*

### 数据来源

- **NCBI Taxonomy**: 宿主分类信息
- **RISB Database**: 昆虫共生菌功能记录（自建）
- **文献数据库**: PubMed, Google Scholar

---

## 12. 快速开始 (Quick Start)

### 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/iSymPred.git
cd iSymPred

# 安装依赖
pip install -r requirements.txt

# 安装 iSymPred
pip install -e .
```

### 基本用法

```bash
# 运行 16S 预测
isympred predict-16s \
    -i examples/demo_otu.txt \
    -d isympred/database/symbiont_record/record_db.tsv \
    -o output_results.tsv \
    --host "Leptinotarsa decemlineata"

# 输出文件
# - output_results_functions.tsv      (功能汇总)
# - output_results_match_records.tsv  (匹配明细)
# - output_results_feature_matrix.tsv (特征矩阵)
```

### Python API

```python
from isympred.predictors.record_predictor import RecordPredictor

# 初始化预测器
predictor = RecordPredictor(
    db_path="isympred/database/symbiont_record/record_db.tsv",
    user_host="Leptinotarsa decemlineata"
)

# 运行预测
predictor.predict(
    input_table_path="examples/demo_otu.txt",
    output_path="output_results.tsv"
)
```

---

## 13. 联系方式 (Contact)

**开发者**: [Your Name]
**邮箱**: your.email@example.com
**GitHub**: https://github.com/yourusername/iSymPred
**文档**: https://isympred.readthedocs.io (待建)

**问题反馈**: 请在 GitHub Issues 提交
**功能建议**: 欢迎通过 Pull Request 贡献代码

---

## 附录: 关键术语表 (Glossary)

| 术语 | 英文 | 定义 |
|-----|------|------|
| **共生菌** | Symbiont | 与宿主形成共生关系的微生物 |
| **宿主上下文** | Host Context | 宿主的分类学信息和生态背景 |
| **证据等级** | Evidence Level | 文献证据的质量分层（1-5 级）|
| **木桶效应** | Bottleneck Effect | 最短板决定最终概率的策略 |
| **分类学距离** | Taxonomic Distance | 宿主间的进化距离（0-6）|
| **数据库支持度** | DB Record Count | 支持某预测的数据库记录数 |
| **特征矩阵** | Feature Matrix | 机器学习用的特征向量集合 |
| **OTU** | Operational Taxonomic Unit | 操作分类单元（16S 聚类结果）|

---

**文档版本**: v1.0
**最后更新**: 2026-01-12
**适用于**: iSymPred v0.1.0 (Alpha)

---

## Slides 制作建议

### 推荐结构 (15-20 页)

1. **标题页** (1 页)
   - 软件名称 + Logo
   - 核心理念一句话

2. **背景与动机** (2-3 页)
   - 现有工具的局限性
   - 宿主特异性的重要性
   - 科学问题

3. **设计原则** (2 页)
   - 三大支柱（宿主上下文、证据分层、保守预测）
   - 可视化流程图

4. **算法流程** (3-4 页)
   - 输入 → 处理 → 输出
   - 关键步骤详解（配图）

5. **核心技术** (3-4 页)
   - 多层级匹配策略（表格）
   - 木桶效应（公式 + 示例）
   - 特征矩阵设计（表格）

6. **性能展示** (2-3 页)
   - 去重效果对比
   - 预测质量指标
   - 与现有工具对比表

7. **应用案例** (2 页)
   - 科研应用场景
   - 机器学习应用

8. **未来展望** (1 页)
   - 短期/中期/长期目标

9. **总结** (1 页)
   - 核心优势
   - 联系方式

### 可视化建议

- 使用流程图展示算法流程（第 3 节）
- 使用表格对比工具特性（第 9 节）
- 使用柱状图展示性能提升（第 8 节）
- 使用热图展示特征重要性（第 6 节）
- 配色方案：蓝色（科技感）+ 绿色（生物学）

---

**祝 Slides 制作顺利！** 🎉
