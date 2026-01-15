# iSymPred 日志文件索引

**目录**: `./logs/`
**用途**: 存放所有更新日志、变更记录、技术文档
**最后更新**: 2025-01-15

---

## 📁 目录结构

```
logs/
├── 01_current/              # 当前版本快速参考
├── 02_feature_matrix/       # 特征矩阵模块文档
├── 03_record_predictor/     # 记录预测器模块文档
├── 04_host_taxonomy/        # 宿主分类模块文档
├── 05_archived/             # 已归档的旧版本文档
├── 06_design_docs/          # 设计文档和架构说明
├── 07_ml_training/          # 机器学习训练模块文档 [NEW]
└── README.md                # 本文件
```

---

## 📚 各目录内容

### 01_current/ - 当前版本快速参考
| 文件 | 说明 |
|------|------|
| `v2.2_UPDATE_SUMMARY.md` | v2.2 更新摘要 |
| `v2.2_IMPLEMENTATION_COMPLETE.md` | v2.2 实现完成报告 |
| `v2.2_QUICK_REFERENCE.txt` | v2.2 快速参考 |

### 02_feature_matrix/ - 特征矩阵模块
| 文件 | 版本 | 说明 |
|------|------|------|
| `feature_matrix_v4.0_USAGE.md` | v4.0 | 使用指南 |
| `FEATURE_MATRIX_V4.0_FINAL_SUMMARY.md` | v4.0 | 最终总结 |
| `feature_matrix_v4.1_FINAL.md` | v4.1 | v4.1 更新 |
| `feature_matrix_v4.1_Bottleneck_Score_UPDATE.md` | v4.1 | Bottleneck Score 更新 |
| `feature_matrix_v4.3_DEDUPLICATION.md` | v4.3 | 去重优化 |
| `feature_matrix_v4.4_STREAMLINED.md` | v4.4 | 精简特征 |
| `feature_matrix_v4.5_DOI_DEDUPLICATION.md` | v4.5 | DOI 去重 |
| `feature_matrix_v4.6_SHANNON_INDEX.md` | v4.6 | Shannon Index 新增 |

### 03_record_predictor/ - 记录预测器模块
| 文件 | 版本 | 说明 |
|------|------|------|
| `record_predictor_CHANGELOG.md` | - | 完整更新日志 |
| `record_predictor_USAGE.md` | - | 使用指南 |
| `record_predictor_UPDATE_SUMMARY.md` | - | 更新摘要 |
| `record_predictor_DESIGN_ANALYSIS.md` | - | 设计分析 |
| `record_predictor_v2.1_PROBABILITY.md` | v2.1 | Probability 功能 |
| `record_predictor_v2.2_PROBABILITY_REFACTOR.md` | v2.2 | Probability 重构 |
| `record_predictor_v2.3_CONTRIBUTOR_LIST.md` | v2.3 | Contributor List |
| `record_predictor_v2.4_MATCH_RECORDS.md` | v2.4 | Match Records 优化 |
| `record_predictor_v5.0_HIERARCHY_UPDATE.md` | v5.0 | 功能层级处理 |
| `record_predictor_v5.1_FUZZY_MATCHING.md` | v5.1 | 模糊匹配支持 |
| `function_hierarchy_handling_PROPOSAL.md` | - | 功能层级处理提案 |

### 04_host_taxonomy/ - 宿主分类模块
| 文件 | 说明 |
|------|------|
| `host_taxonomy_ete3_migration.md` | ete3 迁移文档 |
| `ete3_usage_examples.md` | ete3 使用示例 |

### 05_archived/ - 已归档文档
| 文件 | 说明 |
|------|------|
| `feature_matrix_v3.0_*.md` | v3.0 系列文档 |
| `feature_matrix_v4.0_REDESIGN.md` | v4.0 重设计文档 |
| `README.md` | 归档说明 |

### 06_design_docs/ - 设计文档
| 文件 | 说明 |
|------|------|
| `iSymPred_DESIGN_OVERVIEW.md` | iSymPred 整体设计概述 |

### 07_ml_training/ - 机器学习训练模块 [NEW]
| 文件 | 说明 |
|------|------|
| `ML_TRAINING_PROPOSAL.md` | ML 训练方案设计文档 |

---

## 📋 版本历史

### Record Predictor

| 版本 | 日期 | 主要更新 |
|------|------|----------|
| v5.1 | 2025-01-15 | 模糊匹配支持（清理分类名后缀如 `_D_776786`） |
| v5.0 | 2025-01-14 | 功能层级处理（Parent/Child 关系、概率传播） |
| v2.4 | 2025-01-08 | Match Records 优化（Top 5、Adjusted Score） |
| v2.3 | 2025-01-08 | Contributor List 新增 |
| v2.2 | 2025-01-08 | Probability 算法重构（木桶效应） |
| v2.1 | 2025-01-08 | Probability 功能新增 |

### Feature Matrix

| 版本 | 日期 | 主要更新 |
|------|------|----------|
| v4.6 | 2025-01-13 | Shannon Index 新增 |
| v4.5 | 2025-01-13 | DOI 去重统计 |
| v4.4 | 2025-01-13 | 特征精简（8 核心特征） |
| v4.3 | 2025-01-12 | Taxon-Function 去重 |
| v4.1 | 2025-01-08 | Bottleneck Score 更新 |
| v4.0 | 2025-01-08 | 特征矩阵重设计 |

---

## 🔍 快速查找

### 想了解如何使用 Record Predictor？
→ 查看 `03_record_predictor/record_predictor_USAGE.md`

### 想了解 Feature Matrix 设计？
→ 查看 `02_feature_matrix/FEATURE_MATRIX_V4.0_FINAL_SUMMARY.md`

### 想了解整体架构？
→ 查看 `06_design_docs/iSymPred_DESIGN_OVERVIEW.md`

### 想了解最新更新？
→ 查看 `03_record_predictor/record_predictor_v5.1_FUZZY_MATCHING.md`

### 想了解机器学习训练方案？ [NEW]
→ 查看 `07_ml_training/ML_TRAINING_PROPOSAL.md`

---

## 📝 日志文件命名规范

**格式**: `<模块名>_<类型>_<版本>.md`

**类型说明**:
- `CHANGELOG`: 详细更新日志
- `USAGE`: 使用指南
- `UPDATE_SUMMARY`: 更新摘要
- `DESIGN_*`: 设计文档
- `v<版本号>_<功能名>`: 特定版本的特定功能文档

---

## 🔄 日志维护规范

1. **新增功能**: 在对应模块目录创建独立的功能文档
2. **重大更新**: 更新 `CHANGELOG.md` 和 `UPDATE_SUMMARY.md`
3. **使用变更**: 更新 `USAGE.md`
4. **版本发布**: 在本文件中记录版本历史
5. **归档旧文档**: 移动到 `05_archived/` 目录
