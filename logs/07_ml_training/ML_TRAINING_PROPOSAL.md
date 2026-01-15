# iSymPred 机器学习训练方案

**版本**: v1.0
**日期**: 2025-01-15
**模块**: Key Symbiont Identification via ML

---

## 1. 项目目标

基于 `record_predictor.py` 构建的特征矩阵，训练机器学习模型来自动识别微生物组数据中的**关键共生菌 (Key Symbionts)** 及其对应的**功能标签 (Function Tags)**。

### 1.1 核心任务

| 阶段 | 输入 | 输出 |
|------|------|------|
| 训练 | SRA 样本 + 先验标注数据 | 训练好的模型 |
| 预测 | 新的物种组成文件 | 关键 Taxon-Function 对 |

### 1.2 预期成果

- 自动识别样本中潜在的关键共生菌
- 预测每个关键菌的功能标签
- 输出置信度评分，便于结果筛选

---

## 2. 数据结构设计

### 2.1 目录结构

```
iSymPred/
├── isympred/
│   ├── ml/                          # 新增：机器学习模块
│   │   ├── __init__.py
│   │   ├── trainer.py               # 模型训练脚本
│   │   ├── predictor.py             # 模型预测脚本
│   │   ├── feature_builder.py       # 批量特征构建
│   │   ├── data_loader.py           # 数据加载工具
│   │   └── models/                  # 模型定义
│   │       ├── __init__.py
│   │       ├── random_forest.py     # 随机森林模型
│   │       └── xgboost_model.py     # XGBoost 模型（可选）
│   └── ...
├── data/
│   └── ml_training/                 # 新增：ML 训练数据目录
│       ├── raw_samples/             # 原始 SRA 样本文件
│       │   ├── SRR123456.tsv        # QIIME 格式物种组成
│       │   ├── SRR123457.tsv
│       │   └── ...
│       ├── prior_labels/            # 先验标注数据
│       │   └── key_symbionts.tsv    # 关键菌标注表
│       ├── processed/               # 处理后的特征矩阵
│       │   ├── features/            # 各样本的特征矩阵
│       │   └── merged_features.tsv  # 合并后的训练数据
│       └── models/                  # 训练好的模型
│           ├── key_symbiont_rf.pkl  # 随机森林模型
│           └── model_metadata.json  # 模型元数据
└── ...
```

### 2.2 输入文件格式

#### 2.2.1 原始样本文件 (QIIME 格式)

**文件名**: `SRR{ID}.tsv` 或 `{SRA_ID}.tsv`
**位置**: `data/ml_training/raw_samples/`

```tsv
Taxon	Abundance
d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;o__Enterobacterales;f__Enterobacteriaceae;g__Buchnera;s__Buchnera aphidicola	15000
d__Bacteria;p__Proteobacteria;c__Alphaproteobacteria;o__Rickettsiales;f__Anaplasmataceae;g__Wolbachia;s__Wolbachia pipientis	8500
...
```

#### 2.2.2 先验标注数据

**文件名**: `key_symbionts.tsv`
**位置**: `data/ml_training/prior_labels/`

```tsv
SRA_ID	Taxon	Function_Tag	Evidence_Source	Host_Species
SRR123456	Buchnera aphidicola	amino_acid_provision	PMID:12345678	Acyrthosiphon pisum
SRR123456	Wolbachia	cytoplasmic_incompatibility	PMID:23456789	Acyrthosiphon pisum
SRR123457	Wigglesworthia glossinidia	vitamin_supplementation	PMID:34567890	Glossina morsitans
...
```

**字段说明**:
| 字段 | 类型 | 说明 |
|------|------|------|
| SRA_ID | string | SRA 样本编号 |
| Taxon | string | 关键菌名称（属或种级别） |
| Function_Tag | string | 功能标签（与 function_tag.tsv 一致） |
| Evidence_Source | string | 文献来源（可选） |
| Host_Species | string | 宿主物种（可选，用于宿主匹配） |

---

## 3. 特征工程

### 3.1 基于 record_predictor.py 的特征

利用现有的 `record_predictor.py` 生成特征矩阵，包含 8 个核心特征：

| # | 特征名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | CLR_Abundance | float | 中心对数比转换丰度 |
| 2 | Match_Level_Score | float | 分类匹配置信度 (0.6/1.0) |
| 3 | Host_Match_Weight_Max | float | 最佳宿主匹配权重 |
| 4 | Evidence_Level_Max | int | 最高证据等级 |
| 5 | Adjusted_Score_Max | float | 综合质量分数 |
| 6 | DB_Literature_Count | int | 文献支持数量 |
| 7 | Shannon_Index | float | 样本 α 多样性 |
| 8 | Rank_By_Abundance | int | 丰度排名 |

### 3.2 新增特征（建议）

| # | 特征名 | 类型 | 说明 |
|---|--------|------|------|
| 9 | Relative_Abundance_Pct | float | 相对丰度百分比 |
| 10 | Is_Dominant | bool | 是否为优势菌（Top 5） |
| 11 | Function_Count | int | 该 Taxon 关联的功能数量 |
| 12 | Sample_Richness | int | 样本物种丰富度 |
| 13 | Taxon_Prevalence | float | 该 Taxon 在训练集中的出现频率 |

### 3.3 标签定义

**二分类任务**: 预测 Taxon-Function 对是否为"关键共生菌-功能"关系

```python
# 标签生成逻辑
label = 1 if (taxon, function) in prior_labels else 0
```

---

## 4. 模型选择

### 4.1 推荐模型：随机森林 (Random Forest)

**理由**:
1. **小样本友好**: 适合训练数据量有限的场景
2. **可解释性强**: 可输出特征重要性，便于生物学解读
3. **抗过拟合**: 集成学习天然具有正则化效果
4. **处理不平衡数据**: 支持 class_weight 参数
5. **无需特征标准化**: 对特征尺度不敏感

**参数建议**:
```python
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(
    n_estimators=200,           # 树的数量
    max_depth=10,               # 最大深度（防止过拟合）
    min_samples_split=5,        # 最小分裂样本数
    min_samples_leaf=2,         # 叶节点最小样本数
    class_weight='balanced',    # 处理类别不平衡
    random_state=42,
    n_jobs=-1                   # 并行计算
)
```

### 4.2 备选模型：XGBoost

**适用场景**: 数据量较大（>1000 样本）时考虑

```python
from xgboost import XGBClassifier

model = XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    scale_pos_weight=neg_count/pos_count,  # 处理不平衡
    random_state=42
)
```

### 4.3 模型评估指标

| 指标 | 说明 | 重要性 |
|------|------|--------|
| Precision | 预测为正的准确率 | ⭐⭐⭐ |
| Recall | 真正例的召回率 | ⭐⭐⭐ |
| F1-Score | Precision 和 Recall 的调和平均 | ⭐⭐⭐ |
| AUC-ROC | ROC 曲线下面积 | ⭐⭐ |
| PR-AUC | Precision-Recall 曲线下面积 | ⭐⭐⭐ |

**注意**: 由于正负样本不平衡，PR-AUC 比 AUC-ROC 更有参考价值。

---

## 5. 训练流程

### 5.1 数据准备流程

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Raw Samples    │     │  Prior Labels   │     │  Symbiont DB    │
│  (SRA files)    │     │  (key_symbionts)│     │  (record_db)    │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         ▼                       │                       │
┌─────────────────┐              │                       │
│ record_predictor│◄─────────────┼───────────────────────┘
│ (per sample)    │              │
└────────┬────────┘              │
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│ Feature Matrix  │     │  Label Matrix   │
│ (per sample)    │     │  (from prior)   │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
            ┌─────────────────┐
            │ Merged Training │
            │     Dataset     │
            └────────┬────────┘
                     │
                     ▼
            ┌─────────────────┐
            │   ML Training   │
            └────────┬────────┘
                     │
                     ▼
            ┌─────────────────┐
            │  Trained Model  │
            └─────────────────┘
```

### 5.2 详细步骤

#### Step 1: 批量生成特征矩阵

```bash
# 对每个 SRA 样本运行 record_predictor
python isympred/ml/feature_builder.py \
    --input-dir data/ml_training/raw_samples/ \
    --output-dir data/ml_training/processed/features/ \
    --db isympred/database/symbiont_record/record_db.tsv \
    --prior-labels data/ml_training/prior_labels/key_symbionts.tsv
```

#### Step 2: 合并特征矩阵并生成标签

```bash
# 合并所有样本的特征矩阵，添加标签列
python isympred/ml/data_loader.py \
    --features-dir data/ml_training/processed/features/ \
    --prior-labels data/ml_training/prior_labels/key_symbionts.tsv \
    --output data/ml_training/processed/merged_features.tsv
```

#### Step 3: 训练模型

```bash
# 训练随机森林模型
python isympred/ml/trainer.py \
    --input data/ml_training/processed/merged_features.tsv \
    --output-dir data/ml_training/models/ \
    --model-type random_forest \
    --cv-folds 5 \
    --test-size 0.2
```

#### Step 4: 模型评估

```bash
# 评估模型性能
python isympred/ml/trainer.py \
    --input data/ml_training/processed/merged_features.tsv \
    --model data/ml_training/models/key_symbiont_rf.pkl \
    --evaluate
```

---

## 6. 预测流程

### 6.1 预测新样本

```bash
# 对新样本进行预测
python isympred/ml/predictor.py \
    --input new_sample.tsv \
    --model data/ml_training/models/key_symbiont_rf.pkl \
    --db isympred/database/symbiont_record/record_db.tsv \
    --output predictions.tsv \
    --threshold 0.5
```

### 6.2 预测输出格式

**文件名**: `{sample_id}_predictions.tsv`

```tsv
Taxon	Function_Tag	Probability	Is_Key_Symbiont	Confidence_Level	Supporting_Features
Buchnera aphidicola	amino_acid_provision	0.92	True	High	CLR=3.2, Evidence=5, Host_Match=1.5
Wolbachia	cytoplasmic_incompatibility	0.78	True	Medium	CLR=2.1, Evidence=4, Host_Match=1.3
Lactobacillus	nutrient_provision	0.35	False	Low	CLR=1.5, Evidence=2, Host_Match=1.0
```

**字段说明**:
| 字段 | 说明 |
|------|------|
| Taxon | 分类单元名称 |
| Function_Tag | 预测的功能标签 |
| Probability | 模型预测概率 |
| Is_Key_Symbiont | 是否为关键共生菌（基于阈值） |
| Confidence_Level | 置信度等级 (High/Medium/Low) |
| Supporting_Features | 支持该预测的关键特征 |

---

## 7. 新增脚本清单

### 7.1 核心脚本

| 脚本 | 位置 | 功能 |
|------|------|------|
| `feature_builder.py` | `isympred/ml/` | 批量调用 record_predictor 生成特征 |
| `data_loader.py` | `isympred/ml/` | 加载、合并数据，生成标签 |
| `trainer.py` | `isympred/ml/` | 模型训练和评估 |
| `predictor.py` | `isympred/ml/` | 模型预测 |

### 7.2 模型定义

| 脚本 | 位置 | 功能 |
|------|------|------|
| `random_forest.py` | `isympred/ml/models/` | 随机森林模型封装 |
| `xgboost_model.py` | `isympred/ml/models/` | XGBoost 模型封装（可选） |

### 7.3 CLI 集成

在 `cli.py` 中新增命令：

```python
@click.command()
@click.option('--input-dir', required=True, help='Directory containing SRA sample files')
@click.option('--prior-labels', required=True, help='Prior labels TSV file')
@click.option('--output-dir', required=True, help='Output directory for model')
def train_model(input_dir, prior_labels, output_dir):
    """Train ML model for key symbiont identification."""
    pass

@click.command()
@click.option('--input', required=True, help='Input sample file (QIIME format)')
@click.option('--model', required=True, help='Trained model file')
@click.option('--output', required=True, help='Output predictions file')
def predict_key_symbionts(input, model, output):
    """Predict key symbionts in a new sample."""
    pass
```

---

## 8. 依赖项

### 8.1 新增 Python 依赖

```txt
# requirements-ml.txt
scikit-learn>=1.0.0
xgboost>=1.5.0        # 可选
joblib>=1.1.0         # 模型序列化
imbalanced-learn>=0.9.0  # 处理不平衡数据（可选）
```

### 8.2 安装命令

```bash
pip install -r requirements-ml.txt
```

---

## 9. 注意事项

### 9.1 数据质量

1. **先验标注质量**: 确保 `key_symbionts.tsv` 中的标注准确可靠
2. **样本多样性**: 训练样本应覆盖多种宿主和环境
3. **类别平衡**: 正负样本比例建议不超过 1:10

### 9.2 模型泛化

1. **交叉验证**: 使用 5-fold CV 评估模型稳定性
2. **留出测试集**: 保留 20% 数据作为独立测试集
3. **特征重要性**: 分析特征重要性，确保模型学到生物学相关特征

### 9.3 阈值选择

1. **默认阈值**: 0.5（平衡 Precision 和 Recall）
2. **高 Precision 场景**: 提高阈值至 0.7-0.8
3. **高 Recall 场景**: 降低阈值至 0.3-0.4

---

## 10. 后续扩展

### 10.1 多标签分类

当前设计为二分类（是否为关键共生菌）。未来可扩展为多标签分类，直接预测功能标签。

### 10.2 深度学习

数据量充足时（>10000 样本），可考虑使用神经网络模型。

### 10.3 迁移学习

利用预训练的微生物组嵌入（如 MicroBERT）提升小样本性能。

---

## 11. 参考资料

1. scikit-learn 文档: https://scikit-learn.org/
2. XGBoost 文档: https://xgboost.readthedocs.io/
3. 不平衡学习: https://imbalanced-learn.org/

---

**文档维护**: 本文档将随项目进展持续更新。
