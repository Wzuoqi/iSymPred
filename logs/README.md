# iSymPred 日志文件索引

**目录**: `./logs/`
**用途**: 存放所有更新日志、变更记录、技术文档

---

## 📚 日志文件列表

### S16 Predictor 相关

#### 1. s16_predictor_CHANGELOG.md
- **版本**: v2.0
- **日期**: 2026-01-07
- **内容**: 详细技术文档（~600行）
- **包含**:
  - 宿主匹配打分系统完整说明
  - 证据等级整合详细文档
  - 评分公式推导和示例
  - 输出格式变化说明
  - 使用示例和最佳实践

#### 2. s16_predictor_USAGE.md
- **版本**: v2.0
- **日期**: 2026-01-07
- **内容**: 快速使用指南（~300行）
- **包含**:
  - 参数说明
  - 输入输出格式
  - 使用场景和示例
  - 结果解读指南
  - 常见问题解答

#### 3. s16_predictor_UPDATE_SUMMARY.md
- **版本**: v2.0
- **日期**: 2026-01-07
- **内容**: 更新摘要（~200行）
- **包含**:
  - 核心改动一览
  - 代码修改位置
  - 测试结果
  - 迁移指南

#### 4. s16_predictor_v2.1_PROBABILITY.md
- **版本**: v2.1
- **日期**: 2026-01-07
- **内容**: Probability 功能详细文档
- **包含**:
  - Probability 计算逻辑完整推导
  - Sigmoid 函数参数说明
  - 多因素综合评估方法
  - 概率等级划分和解读
  - 参数调优建议
  - 科学依据说明

---

## 📋 版本历史

### v2.2 (2026-01-07)
- ✅ **重构 Probability 算法**（重大更新）
  - 更保守的 Sigmoid 函数（k=0.2, x0=15）
  - 引入"木桶效应"（min() 函数）
  - 严格的惩罚机制（宿主不匹配 -50%，低质量证据 -40%）
  - 概率上限设为 0.95
  - 区分度大幅提升，高潜力功能更突出
- 📄 文档: `s16_predictor_v2.2_PROBABILITY_REFACTOR.md`

### v2.1 (2026-01-07)
- ✅ 新增 Probability 列（功能存在概率）
- ✅ 修改输出文件名为 `_functions.tsv`
- 📄 文档: `s16_predictor_v2.1_PROBABILITY.md`

### v2.0 (2026-01-07)
- ✅ 整合宿主匹配打分系统
- ✅ 整合证据等级权重
- ✅ 更新评分公式
- ✅ 扩展输出格式
- 📄 文档: `s16_predictor_CHANGELOG.md`, `s16_predictor_USAGE.md`, `s16_predictor_UPDATE_SUMMARY.md`

---

## 🔍 快速查找

### 想了解如何使用？
→ 查看 `s16_predictor_USAGE.md`

### 想了解技术细节？
→ 查看 `s16_predictor_CHANGELOG.md`

### 想快速了解改动？
→ 查看 `s16_predictor_UPDATE_SUMMARY.md`

### 想了解 Probability 计算？
→ 查看 `s16_predictor_v2.1_PROBABILITY.md` (旧算法)
→ 查看 `s16_predictor_v2.2_PROBABILITY_REFACTOR.md` (新算法，推荐) ⭐

---

## 📝 日志文件命名规范

**格式**: `<模块名>_<类型>_<版本>.md`

**类型说明**:
- `CHANGELOG`: 详细更新日志
- `USAGE`: 使用指南
- `UPDATE_SUMMARY`: 更新摘要
- `v<版本号>_<功能名>`: 特定版本的特定功能文档

**示例**:
- `s16_predictor_CHANGELOG.md`
- `s16_predictor_v2.1_PROBABILITY.md`
- `database_format_UPDATE.md`

---

## 🔄 日志维护规范

1. **新增功能**: 创建独立的功能文档（如 `v2.1_PROBABILITY.md`）
2. **重大更新**: 更新 `CHANGELOG.md` 和 `UPDATE_SUMMARY.md`
3. **使用变更**: 更新 `USAGE.md`
4. **版本发布**: 在本文件中记录版本历史

---

**最后更新**: 2026-01-07
