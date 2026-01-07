# S16 Predictor 更新日志 (Changelog)

**更新日期**: 2026-01-07
**版本**: v2.0 (Host-Context & Evidence-Level Integration)

---

## 📋 更新概述 (Summary)

本次更新为 `s16_predictor.py` 添加了两个核心功能：
1. **宿主匹配打分系统 (Host-Context Scoring)**: 基于宿主分类信息（目、科、属、种）对预测结果进行加权
2. **证据等级整合 (Evidence-Level Integration)**: 基于文献质量（Record Type、Genome ID、Journal）对预测结果进行加权

这两个功能显著提高了预测的准确性和可信度，使得预测结果更符合生物学实际。

---

## 🎯 核心改动 (Core Changes)

### 1. 新增宿主匹配打分系统

#### 1.1 功能说明
- **目的**: 根据用户提供的宿主物种信息，对数据库中的共生菌记录进行宿主特异性加权
- **原理**: 宿主-共生菌关系具有特异性，同一微生物在不同宿主中的功能可能不同
- **实现**: 整合 `host_query.py` 的宿主分类查询功能，自动获取宿主的目、科、属信息

#### 1.2 宿主匹配权重表

| 匹配等级 | 权重 | 说明 | 示例 |
|---------|------|------|------|
| **Species** | 1.5 | 物种级精确匹配 | 用户宿主: *Apis mellifera*, 数据库: *Apis mellifera* |
| **Genus** | 1.3 | 属级匹配 | 用户宿主: *Apis mellifera*, 数据库: *Apis* sp. |
| **Family** | 1.2 | 科级匹配 | 用户宿主: *Apis mellifera* (Apidae), 数据库: Apidae |
| **Order** | 1.1 | 目级匹配 | 用户宿主: *Apis mellifera* (Hymenoptera), 数据库: Hymenoptera |
| **General** | 1.0 | 通用记录（无宿主特异性） | 数据库中 host = "General" |
| **Mismatch** | 0.8 | 完全不匹配（降低权重） | 用户宿主: *Apis mellifera*, 数据库: *Drosophila* |

#### 1.3 代码实现位置
- **新增方法**: `_query_host_taxonomy()` (第52-105行)
  - 功能: 查询宿主的分类信息（目、科、属）
  - 依赖: SQLite 数据库 `insect_taxonomy.db`

- **新增方法**: `_calculate_host_match_score()` (第107-153行)
  - 功能: 计算宿主匹配得分
  - 输入: 数据库中的宿主物种名、目、科
  - 输出: 宿主匹配权重 (0.8-1.5)

- **修改**: `__init_)` 方法 (第11-50行)
  - 新增参数: `host_db_path`, `user_host`
  - 新增属性: `self.host_taxonomy`, `self.HOST_MATCH_WEIGHTS`

#### 1.4 使用示例
```bash
# 不指定宿主（所有记录权重相同）
python s16_predictor.py -i otu_table.tsv -d record_db.tsv -o output.tsv

# 指定宿主（启用宿主匹配打分）
python s16_predictor.py -i otu_table.tsv -d record_db.tsv -o output.tsv \
    --host "Apis mellifera" \
    --host-db ../database/host_taxonomy/insect_taxonomy.db

# 自动推导宿主数据库路径
python s16_predictor.py -i otu_table.tsv -d record_db.tsv -o output.tsv \
    --host "Apis mellifera"
```

---

### 2. 新增证据等级整合

#### 2.1 功能说明
- **目的**: 根据文献证据质量对预测结果进行加权
- **原理**: 高质量证据（有基因组、顶级期刊）的记录更可靠
- **数据来源**: 数据库中的 `evidence_level` 字段（1-5）

#### 2.2 证据等级权重表

| 证据等级 | 权重 | 说明 | 组成 |
|---------|------|------|------|
| **5** | 1.5 | 最高证据等级 | Symbiont + Genome ID + Top Journal |
| **4** | 1.3 | 高证据等级 | Symbiont + Genome ID |
| **3** | 1.15 | 中等证据等级 | Symbiont + Top Journal |
| **2** | 1.0 | 基础证据等级 | Symbiont only |
| **1** | 0.8 | 低证据等级 | 其他类型记录 |

**顶级期刊列表**:
- Nature 系列: Nature, Nature Communications, Nature Microbiology, Nature Biotechnology
- Science 系列: Science, Science Advances, PNAS
- Cell 系列: Cell, Cell Host & Microbe
- 微生物组期刊: ISME Journal, Microbiome, mBio, PLOS Biology

#### 2.3 代码实现位置
- **修改**: `__init__()` 方法 (第43-50行)
  - 新增属性: `self.EVIDENCE_LEVEL_WEIGHTS`

- **修改**: `_load_database()` 方法 (第155-197行)
  - 新增字段检查: `evidence_level`, `host_order`, `host_family`
  - 默认值: 如果缺失 `evidence_level`，使用默认值 2

- **修改**: `predict()` 方法 (第274-353行)
  - 读取 `evidence_level` 字段
  - 计算证据等级权重
  - 整合到最终得分计算

---

### 3. 评分公式更新

#### 3.1 旧版评分公式 (v1.0)
```
Score = Taxon_Match_Weight × log10(RA% + 1) × 100
```
- `Taxon_Match_Weight`: 1.0 (种级) 或 0.6 (属级)
- `RA%`: 相对丰度百分比

#### 3.2 新版评分公式 (v2.0)
```
Final_Score = Base_Score × Host_Match_Weight × Evidence_Weight

其中:
Base_Score = Taxon_Match_Weight × log10(RA% + 1) × 100
Host_Match_Weight = 0.8 ~ 1.5 (根据宿主匹配等级)
Evidence_Weight = 0.8 ~ 1.5 (根据证据等级)
```

#### 3.3 评分示例

**场景 1: 高质量匹配**
- OTU: *Buchnera aphidicola*, RA = 10%
- 用户宿主: *Acyrthosiphon pisum* (蚜虫)
- 数据库记录: *Buchnera aphidicola* in *Acyrthosiphon pisum*, Evidence Level = 5

计算:
```
Base_Score = 1.0 × log10(10 + 1) × 100 = 104.1
Host_Match_Weight = 1.5 (物种级匹配)
Evidence_Weight = 1.5 (最高证据等级)
Final_Score = 104.1 × 1.5 × 1.5 = 234.2
```

**场景 2: 中等质量匹配**
- OTU: *Wolbachia* sp., RA = 5%
- 用户宿主: *Drosophila melanogaster*
- 数据库记录: *Wolbachia* in General, Evidence Level = 3

计算:
```
Base_Score = 0.6 × log10(5 + 1) × 100 = 46.9 (属级匹配)
Host_Match_Weight = 1.0 (通用记录)
Evidence_Weight = 1.15 (中等证据等级)
Final_Score = 46.9 × 1.0 × 1.15 = 53.9
```

**场景 3: 低质量匹配**
- OTU: *Serratia* sp., RA = 2%
- 用户宿主: *Apis mellifera*
- 数据库记录: *Serratia* in *Drosophila*, Evidence Level = 2

计算:
```
Base_Score = 0.6 × log10(2 + 1) × 100 = 28.7
Host_Match_Weight = 0.8 (宿主不匹配)
Evidence_Weight = 1.0 (基础证据等级)
Final_Score = 28.7 × 0.8 × 1.0 = 23.0
```

---

## 📊 输出格式变化

### 4.1 表格 1: 功能预测汇总表 (Function Summary)

**新增列**:
- `Final_Score_Sum`: 最终总分（整合所有权重后的总分）
- `Mean_Host_Match`: 平均宿主匹配权重
- `Mean_Evidence_Weight`: 平均证据等级权重

**列名变更**:
- `Potential_Score_Sum` → `Final_Score_Sum`

**完整列结构**:
```
Function | Final_Score_Sum | Total_RA_Pct | Mean_Confidence | Mean_Host_Match | Mean_Evidence_Weight | Taxa_Count | Dominant_Contributor
```

### 4.2 表格 2: 潜在共生菌明细表 (Potential Symbionts)

**新增列**:
- `Final_Score`: 最终得分（整合所有权重）
- `Base_Score`: 基础得分（仅考虑分类匹配和丰度）
- `Host_Match_Weight`: 宿主匹配权重 (0.8-1.5)
- `Host_Match_Level`: 宿主匹配等级 (Species/Genus/Family/Order/General/Mismatch)
- `Evidence_Level`: 证据等级 (1-5)
- `Evidence_Weight`: 证据等级权重 (0.8-1.5)

**列名变更**:
- `Potential_Score` → `Final_Score`

**完整列结构**:
```
Symbiont_Taxon | Predicted_Function | Final_Score | Base_Score | Host_Match_Weight | Host_Match_Level | Evidence_Level | Evidence_Weight | Match_Level | Relative_Abundance_Pct | DB_Host_Context | DB_Description | DB_Evidence
```

---

## 🔧 技术细节

### 5.1 依赖变更

**新增依赖**:
```python
import sqlite3  # 用于查询宿主分类数据库
from pathlib import Path  # 用于路径处理
```

### 5.2 数据库字段要求

**必需字段** (record_db.tsv):
- `taxonomy`: QIIME 2 格式分类字符串
- `host`: 宿主物种名
- `function`: 功能标签
- `host_order`: 宿主目 (新增)
- `host_family`: 宿主科 (新增)
- `evidence_level`: 证据等级 1-5 (新增)

**可选字段**:
- `description`: 功能描述
- `evidence`: DOI 或文献信息
- `genome_id`: 基因组 ID
- `journal`: 期刊名称

### 5.3 向后兼容性

- ✅ **完全兼容旧版数据库**: 如果数据库缺少 `evidence_level`、`host_order`、`host_family` 字段，会自动使用默认值
- ✅ **可选宿主参数**: 不提供 `--host` 参数时，行为与旧版一致（所有记录权重相同）
- ✅ **输出格式扩展**: 新增列不影响旧版脚本读取核心列（Function, Final_Score_Sum, Total_RA_Pct）

---

## 📝 使用建议

### 6.1 何时使用宿主匹配打分？

**推荐使用**:
- ✅ 研究特定宿主的共生菌功能
- ✅ 宿主物种已知且在数据库中有记录
- ✅ 需要区分宿主特异性功能和通用功能

**不推荐使用**:
- ❌ 宿主未知或混合样本
- ❌ 探索性分析（想看所有可能的功能）
- ❌ 宿主不在昆虫纲范围内

### 6.2 如何解读新增的权重列？

**Mean_Host_Match**:
- `> 1.2`: 该功能主要由宿主特异性共生菌贡献（高可信度）
- `1.0 - 1.2`: 混合了通用记录和宿主特异性记录
- `< 1.0`: 该功能主要由非宿主特异性微生物贡献（需谨慎解读）

**Mean_Evidence_Weight**:
- `> 1.3`: 该功能有高质量文献支持（有基因组数据）
- `1.0 - 1.3`: 中等质量文献支持
- `< 1.0`: 证据质量较低，需进一步验证

**Evidence_Level** (明细表):
- `5`: 最可靠（Symbiont + Genome + Top Journal）
- `4`: 高可靠（Symbiont + Genome）
- `3`: 中等可靠（Symbiont + Top Journal）
- `2`: 基础可靠（Symbiont only）
- `1`: 需验证

---

## 🐛 已知限制

1. **宿主数据库覆盖范围**: 目前仅支持昆虫纲（Insecta），其他节肢动物需扩展数据库
2. **宿主名称标准化**: 需要使用标准拉丁学名，俗名或缩写可能无法匹配
3. **证据等级主观性**: 期刊质量评估基于预定义列表，可能需要根据研究领域调整
4. **计算复杂度**: 宿主查询增加了初始化时间（约 0.1-0.5 秒），对大规模分析影响较小

---

## 🔄 迁移指南 (Migration Guide)

### 从 v1.0 迁移到 v2.0

**步骤 1: 更新数据库**
```bash
# 重新生成数据库（包含 evidence_level 字段）
python isympred/database/format_database_record.py \
    -i raw_symbiont_record.tsv \
    -o record_db.tsv
```

**步骤 2: 更新命令行调用**
```bash
# 旧版命令（仍然有效）
python s16_predictor.py -i otu.tsv -d record_db.tsv -o output.tsv

# 新版命令（推荐）
python s16_predictor.py -i otu.tsv -d record_db.tsv -o output.tsv \
    --host "Apis mellifera"
```

**步骤 3: 更新下游分析脚本**
- 如果脚本读取 `Potential_Score_Sum` 列，需改为 `Final_Score_Sum`
- 新增列可选择性使用，不影响核心功能

---

## 📚 参考文献

1. **宿主-共生菌特异性**:
   - Douglas, A. E. (2015). Multiorganismal insects: diversity and function of resident microorganisms. *Annual Review of Entomology*, 60, 17-34.

2. **证据等级评估**:
   - 基于 RISB (Reference Insect Symbiont Database) 的数据质量标准

3. **FAPROTAX 方法论**:
   - Louca, S., et al. (2016). Decoupling function and taxonomy in the global ocean microbiome. *Science*, 353(6305), 1272-1277.

---

## 📧 联系方式

如有问题或建议，请联系:
- 项目维护者: [Your Name]
- GitHub Issues: [Project URL]
- Email: [Your Email]

---

**最后更新**: 2026-01-07
**文档版本**: 1.0
