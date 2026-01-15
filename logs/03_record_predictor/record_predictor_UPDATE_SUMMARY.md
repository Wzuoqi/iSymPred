# S16 Predictor v2.0 更新摘要

**更新日期**: 2026-01-07
**文件**: `isympred/predictors/record_predictor.py`

---

## 🎯 核心改动一览

### 1. 新增功能

#### ✨ 宿主匹配打分系统
- **功能**: 根据用户提供的宿主物种，对数据库记录进行宿主特异性加权
- **权重范围**: 0.8 (不匹配) ~ 1.5 (物种级匹配)
- **匹配层级**: Species > Genus > Family > Order > General > Mismatch
- **实现方法**:
  - `_query_host_taxonomy()`: 查询宿主分类信息
  - `_calculate_host_match_score()`: 计算宿主匹配权重

#### ✨ 证据等级整合
- **功能**: 基于文献质量对预测结果加权
- **权重范围**: 0.8 (低质量) ~ 1.5 (最高质量)
- **证据等级**: 1-5 (基于 Record Type + Genome ID + Journal)
- **数据来源**: 数据库中的 `evidence_level` 字段

### 2. 评分公式更新

**旧版 (v1.0)**:
```
Score = Taxon_Match_Weight × log10(RA% + 1) × 100
```

**新版 (v2.0)**:
```
Final_Score = Base_Score × Host_Match_Weight × Evidence_Weight
```

### 3. 输出格式变化

#### 表1: 功能汇总表
**新增列**:
- `Mean_Host_Match`: 平均宿主匹配权重
- `Mean_Evidence_Weight`: 平均证据等级权重

**列名变更**:
- `Potential_Score_Sum` → `Final_Score_Sum`

#### 表2: 潜在共生菌明细表
**新增列**:
- `Base_Score`: 基础得分
- `Host_Match_Weight`: 宿主匹配权重
- `Host_Match_Level`: 宿主匹配等级
- `Evidence_Level`: 证据等级 (1-5)
- `Evidence_Weight`: 证据等级权重

**列名变更**:
- `Potential_Score` → `Final_Score`

### 4. 命令行参数

**新增参数**:
- `--host`: 宿主物种拉丁名 (可选)
- `--host-db`: 宿主分类数据库路径 (可选，可自动推导)

---

## 📂 相关文件

### 主要文件
1. **`record_predictor.py`** (已更新)
   - 核心预测脚本
   - 新增宿主匹配和证据等级功能

2. **`record_predictor_CHANGELOG.md`** (新建)
   - 详细更新日志
   - 包含算法原理、评分公式、使用示例

3. **`record_predictor_USAGE.md`** (新建)
   - 快速使用指南
   - 包含参数说明、输出解读、常见问题

### 依赖文件
4. **`../database/symbiord/record_db.tsv`** (已更新)
   - 新增 `evidence_level` 列
   - 新增 `host_order`, `host_family` 列

5. **`../database/host_taxonomy/insect_taxonomy.db`** (已存在)
   - 宿主分类数据库
   - 用于查询宿主的目、科、属信息

6. **`../utils/host_query.py`** (已存在)
   - 宿主查询工具
   - 已整合到 s16_predict
---

## 🔧 代码改动位置

### 新增方法
- **第52-105行**: `_query_host_taxonomy()` - 查询宿主分类
- **第107-153行**: `_calculate_hosh_score()` - 计算宿主匹配得分

### 修改方法
- **第11-50行**: `__init__()` - 新增宿主相关参数和权重配置
- **第155-197行**: `_load_database()` - 新增字段检查 (evidence_level, host_order, host_family)
- **第259-353行**: `predict()` - 整合宿主匹配和证据等级到评分计算
- **第355-400行**: 输出表1 - 新增统计列
- **第402-423行**: 输出表2 - 新增详细列
- **第425-448行**: `__main__` - 新增命令行参数

### 新增依赖
- **第7行**: `import sqlite查询宿主数据库
- **第8行**: `from pathlib import Path` - 用于路径处理

---

## ✅ 测试结果

### 测试场景
1. ✅ 不带宿主参数（向后兼容）
2. ✅ 带宿主参数（新功能）
3. ✅ 宿主数据库自动推导
4. ✅ 输出格式验证
5. ✅ 评分公式验证

### 测试数据
- 输入: `tests/test_data.tsv` (538,623 reads)
- 数据库: `isympred/database/symbiont_record/record_db.tsv` (2,168 records)
- 宿主: `Drosophila melanogaster`

### 测试结果
- ✅ 宿主查询成功: Order=Diptera, Family=Drosophilidae, Genus=Drosophila
- ✅ Mean_Host_Match 从 1.0 变为 0.89-0.94
- ✅ Host_Match_Level 正确显示 (Order/General)
- ✅ Evidence_Level 和 Evidence_Weight 正确计算
- ✅ 评分公式验证通过: 69.8 × 1.1 × 1.15 = 88.3

---

## 📊 使用示例

### 基础用法（不指定宿主）
```bash
python isympred/predictors/record_predictor.py \
    -i otu_table.tsv \
    -d isympred/database/symbiont_record/record_db.tsv \
    -o results.tsv
```

### 推荐用法（指定宿主）
```bash
python isympred/predictors/record_predictor.py \
    -i otu_table.tsv \
    -d isympred/database/symbiont_record/record_db.tsv \
    -o results.tsv \
    --host "Apis mellifera"
```

---

## 🎓 关键概念

### 宿主匹配权重表
| 匹配等级 | 权重 | 说明 |
|---------|------|------|
| Species | 1.5 | 物种级精确匹配 |
| Genus | 1.3 | 属级匹配 |
| Family | 1.2 | 科级匹配 |
| Order | 1.1 | 目级匹配 |
| General | 1.0 | 通用记录 |
| Mismatch | 0.8 | 完全不匹配 |

### 证据等级权重表
| 证据等级 | 权重 | 组成 |
|---------|------|------|
| 5 | 1.5 | Symbiont + Genome + Top Journal |
| 4 | 1.3 | Symbiont + Genome |
| 3 | 1.15 | Symbiont + Top Journal |
| 2 | 1.0 | Symbiont only |
| 1 | 0.8 | 其他 |

---

## 🔄 向后兼容性

- ✅ **完全兼容旧版数据库**: 缺失字段会使用默认值
- ✅ **可选宿主参数**: 不提供时行为与旧版一致
- ✅ **输出格式扩展**: 新增列不影响旧版脚本读取核心列

---

## 📝 后续建议

1. **数据库更新**: 确保使用包含 `evidence_level` 的最新数据库
2. **宿主信息**: 尽可能提供宿主信息以提高预测准确性
3. **结果筛选**: 关注 `Evidence_Level ≥ 4` 和 `Host_Match_Level = Species/Genus` 的记录
4. **批量分析**: 可以编写脚本批量处理多个样本

---

## 📚 文档索引

- **详细更新日志**: `record_predictor_CHANGELOG.md` (完整技术文档)
- **使用指南**: `record_predictor_USAGE.md` (快速上手指南)
- **本文档**: `record_predictor_UPDATE_SUMMARY.md` (更新摘要)

---

**最后更新**: 2026-01-07
**版本**: v2.0
