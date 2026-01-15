# iSymPred 日志管理准则

**版本:** 1.0
**日期:** 2026-01-08
**目的:** 规范项目日志文件的组织、命名和归档，确保文档易于查找和维护

---

## 📁 目录结构

```
logs/
├── 01_current/              # 当前版本文档（最新、最重要）
├── 02_feature_matrix/       # 特征矩阵相关文档
├── 03_record_predictor/     # 记录预测器相关文档
├── 04_host_taxonomy/        # 宿主分类查询相关文档
├── 05_archived/             # 已归档的旧版本文档
├── LOG_MANAGEMENT_GUIDE.md  # 本文件：日志管理准则
└── INDEX.md                 # 文档索引（快速导航）
```

---

## 📋 分类规则

### 1. **01_current/** - 当前版本文档
**用途:** 存放当前生产版本的核心文档

**应包含的文件类型:**
- 版本实现完成总结 (`vX.X_IMPLEMENTATION_COMPLETE.md`)
- 版本更新摘要 (`vX.X_UPDATE_SUMMARY.md`)
- 快速参考卡片 (`vX.X_QUICK_REFERENCE.txt`)

**命名规范:**
```
v{major}.{minor}_IMPLEMENTATION_COMPLETE.md
v{major}.{minor}_UPDATE_SUMMARY.md
v{major}.{minor}_QUICK_REFERENCE.txt
```

**示例:**
```
v2.2_IMPLEMENTATION_COMPLETE.md
v2.2_UPDATE_SUMMARY.md
v2.2_QUICK_REFERENCE.txt
```

**更新规则:**
- 发布新版本时，将旧版本文件移至 `05_archived/`
- 保持此目录只包含最新版本的文档
- 每个版本最多保留 3 个核心文件

---

### 2. **02_feature_matrix/** - 特征矩阵文档
**用途:** 存放特征矩阵设计、更新和使用文档

**应包含的文件类型:**
- 特征矩阵最终版本文档 (`feature_matrix_vX.X_FINAL.md`)
- 特定功能更新文档 (`feature_matrix_vX.X_{FEATURE}_UPDATE.md`)
- 使用指南 (`feature_matrix_vX.X_USAGE.md`)
- 快速参考 (`FEATURE_MATRIX_VX.X_QUICKREF.txt`)

**命名规范:**
```
feature_matrix_v{major}.{minor}_FINAL.md           # 最终版本文档
feature_matrix_v{major}.{minor}_{FEATURE}_UPDATE.md # 特定功能更新
feature_matrix_v{major}.{minor}_USAGE.md           # 使用指南
FEATURE_MATRIX_V{major}.{minor}_QUICKREF.txt       # 快速参考
```

**示例:**
```
feature_matrix_v4.1_FINAL.md
feature_matrix_v4.1_Bottleneck_Score_UPDATE.md
feature_matrix_v4.0_USAGE.md
FEATURE_MATRIX_V4.0_QUICKREF.txt
```

**更新规则:**
- 保留最近 2 个主版本的文档（如 v4.x 和 v3.x）
- 更老的版本移至 `05_archived/`
- 每个版本保留：FINAL + 重要更新文档 + USAGE

---

### 3. **03_record_predictor/** - 记录预测器文档
**用途:** 存放记录预测器（record_predictor.py）的更新日志和使用文档

**应包含的文件类型:**
- 变更日志 (`record_predictor_CHANGELOG.md`)
- 更新摘要 (`record_predictor_UPDATE_SUMMARY.md`)
- 使用指南 (`record_predictor_USAGE.md`)
- 版本特定功能文档 (`record_predictor_vX.X_{FEATURE}.md`)

**命名规范:**
```
record_predictor_CHANGELOG.md                      # 累积变更日志
record_predictor_UPDATE_SUMMARY.md                 # 最新更新摘要
record_predictor_USAGE.md                          # 使用指南
record_predictor_v{major}.{minor}_{FEATURE}.md     # 版本特定功能
```

**示例:**
```
record_predictor_CHANGELOG.md
record_predictor_UPDATE_SUMMARY.md
record_predictor_USAGE.md
record_predictor_v2.1_PROBABILITY.md
record_predictor_v2.4_MATCH_RECORDS.md
```

**更新规则:**
- `CHANGELOG.md` 持续更新，不归档
- `UPDATE_SUMMARY.md` 每次大版本更新时覆盖
- `USAGE.md` 保持最新，旧版本归档
- 版本特定文档保留最近 3 个版本

---

### 4. **04_host_taxonomy/** - 宿主分类查询文档
**用途:** 存放宿主分类查询相关的技术文档

**应包含的文件类型:**
- 迁移文档 (`host_taxonomy_{FEATURE}_migration.md`)
- 使用示例 (`{TOOL}_usage_examples.md`)
- 技术说明 (`host_taxonomy_{TOPIC}.md`)

**命名规范:**
```
host_taxonomy_{FEATURE}_migration.md               # 迁移文档
{TOOL}_usage_examples.md                           # 工具使用示例
host_taxonomy_{TOPIC}.md                           # 技术说明
```

**示例:**
```
host_taxonomy_ete3_migration.md
ete3_usage_examples.md
host_taxonomy_distance_calculation.md
```

**更新规则:**
- 保留所有迁移文档（历史记录重要）
- 使用示例保持最新版本
- 技术说明按主题组织，不按版本

---

### 5. **05_archived/** - 已归档文档
**用途:** 存放已被新版本替代的旧文档

**应包含的文件类型:**
- 旧版本的设计文档
- 已废弃的功能文档
- 被替代的实现方案

**命名规范:**
- 保持原有命名，添加归档日期前缀（可选）

**示例:**
```
feature_matrix_v3.0_FINAL.md
feature_matrix_v4.0_REDESIGN.md
record_predictor_v1.0_USAGE.md
```

**归档规则:**
- 当新版本发布时，旧版本文档移至此目录
- 保留至少 2 个历史主版本的文档
- 超过 2 年的文档可以考虑删除（如果不再需要）

---

## 📝 文件命名规范

### 通用规则
1. **使用小写字母和下划线:** `feature_matrix_v4.1_FINAL.md`
2. **版本号格式:** `v{major}.{minor}` (如 `v2.2`, `v4.1`)
3. **文件类型后缀:**
   - `_FINAL.md` - 最终版本文档
   - `_UPDATE.md` - 更新说明
   - `_USAGE.md` - 使用指南
   - `_CHANGELOG.md` - 变更日志
   - `_QUICKREF.txt` - 快速参考（纯文本）
   - `_SUMMARY.md` - 摘要
   - `_COMPLETE.md` - 完成总结

### 特殊命名约定
- **全大写文件名:** 用于重要的顶层文档（如 `FEATURE_MATRIX_V4.0_QUICKREF.txt`）
- **模块前缀:** 使用模块名作为前缀（如 `record_predictor_`, `feature_matrix_`）
- **功能后缀:** 描述特定功能（如 `_Bottleneck_Score_UPDATE.md`）

---

## 🔄 更新工作流

### 场景 1: 发布新的主版本（如 v2.2 → v2.3）

**步骤:**
1. 将 `01_current/` 中的旧版本文件移至 `05_archived/`
   ```bash
   mv logs/01_current/v2.2_* logs/05_archived/
   ```

2. 创建新版本的核心文档
   ```bash
   # 在 01_current/ 中创建
   v2.3_IMPLEMENTATION_COMPLETE.md
   v2.3_UPDATE_SUMMARY.md
   v2.3_QUICK_REFERENCE.txt
   ```

3. 更新 `INDEX.md` 中的版本链接

4. 更新相关模块目录中的文档（如果有变化）

---

### 场景 2: 更新特征矩阵（如 v4.1 → v4.2）

**步骤:**
1. 在 `02_feature_matrix/` 中创建新文档
   ```bash
   feature_matrix_v4.2_FINAL.md
   feature_matrix_v4.2_{NEW_FEATURE}_UPDATE.md
   ```

2. 如果 v4.1 不再需要，移至 `05_archived/`
   ```bash
   mv logs/02_feature_matrix/feature_matrix_v4.1_* logs/05_archived/
   ```

3. 保留 v4.2 的 FINAL 和重要更新文档

4. 更新 `INDEX.md`

---

### 场景 3: 添加新功能文档（如新增分类学距离）

**步骤:**
1. 确定文档所属类别（如 `04_host_taxonomy/`）

2. 创建文档，遵循命名规范
   ```bash
   host_taxonomy_distance_calculation.md
   ```

3. 如果是版本特定功能，添加版本号
   ```bash
   record_predictor_v2.2_TAXONOMIC_DISTANCE.md
   ```

4. 更新 `INDEX.md` 添加新文档链接

---

### 场景 4: 归档旧版本

**步骤:**
1. 识别需要归档的文档（通常是被新版本替代的）

2. 移动到 `05_archived/`
   ```bash
   mv logs/02_feature_matrix/feature_matrix_v3.0_* logs/05_archived/
   ```

3. 在 `05_archived/README.md` 中记录归档原因和日期

4. 从 `INDEX.md` 中移除或标记为已归档

---

## 📊 文档优先级

### 高优先级（必须保持最新）
- `01_current/` 中的所有文件
- `INDEX.md`
- 各模块的 `USAGE.md` 和 `CHANGELOG.md`

### 中优先级（定期更新）
- 特征矩阵的 `FINAL.md`
- 记录预测器的版本特定文档
- 宿主分类的技术文档

### 低优先级（按需更新）
- 快速参考文档（`QUICKREF.txt`）
- 归档文档（`05_archived/`）

---

## 🔍 查找文档指南

### 我想找...

**1. 最新版本的核心信息**
→ 查看 `01_current/vX.X_IMPLEMENTATION_COMPLETE.md`

**2. 如何使用某个功能**
→ 查看对应模块的 `USAGE.md`
- 特征矩阵: `02_feature_matrix/feature_matrix_vX.X_USAGE.md`
- 记录预测器: `03_record_predictor/record_predictor_USAGE.md`

**3. 某个功能的变更历史**
→ 查看 `CHANGELOG.md`
- 记录预测器: `03_record_predictor/record_predictor_CHANGELOG.md`

**4. 快速参考某个版本**
→ 查看 `QUICKREF.txt`
- 当前版本: `01_current/vX.X_QUICK_REFERENCE.txt`
- 特征矩阵: `02_feature_matrix/FEATURE_MATRIX_VX.X_QUICKREF.txt`

**5. 某个技术的实现细节**
→ 查看对应模块目录
- 宿主分类: `04_host_taxonomy/`
- 特征矩阵: `02_feature_matrix/`

**6. 旧版本的文档**
→ 查看 `05_archived/`

**7. 所有文档的概览**
→ 查看 `INDEX.md`

---

## ✅ 文档质量检查清单

创建新文档时，确保包含以下内容：

### 必需元素
- [ ] 文件头部包含标题、版本、日期
- [ ] 清晰的目录结构（如果文档较长）
- [ ] 简洁的摘要或引言
- [ ] 代码示例（如果适用）
- [ ] 相关文档的链接

### 推荐元素
- [ ] 使用场景或示例
- [ ] 常见问题解答
- [ ] 故障排除指南
- [ ] 性能考虑
- [ ] 未来改进建议

### 格式要求
- [ ] 使用 Markdown 格式
- [ ] 代码块使用语法高亮
- [ ] 表格格式正确
- [ ] 链接有效
- [ ] 图片（如果有）可访问

---

## 🚀 自动化建议

### 脚本 1: 创建新版本文档
```bash
#!/bin/bash
# create_version_docs.sh
VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: ./create_version_docs.sh v2.3"
    exit 1
fi

# Archive old version
mv logs/01_current/v* logs/05_archived/ 2>/dev/null

# Create new version templates
cat > logs/01_current/${VERSION}_IMPLEMENTATION_COMPLETE.md << EOF
# iSymPred ${VERSION} - Implementation Complete

**Date:** $(date +%Y-%m-%d)
**Version:** ${VERSION}
**Status:** 🚧 In Progress

---

## Summary
[Add summary here]

---
EOF

cat > logs/01_current/${VERSION}_UPDATE_SUMMARY.md << EOF
# iSymPred ${VERSION} Update Summary

**Date:** $(date +%Y-%m-%d)
**Version:** ${VERSION}

---

## Changes
[Add changes here]

---
EOF

echo "Created version ${VERSION} documentation templates"
```

### 脚本 2: 归档旧版本
```bash
#!/bin/bash
# archive_old_versions.sh
KEEP_VERSIONS=2

cd logs/02_feature_matrix
# Find all version numbers
versions=$(ls feature_matrix_v*.md | grep -oP 'v\d+\.\d+' | sort -V -u)
version_count=$(echo "$versions" | wc -l)

if [ $version_count -gt $KEEP_VERSIONS ]; then
    # Archive old versions
    old_versions=$(echo "$versions" | head -n -$KEEP_VERSIONS)
    for ver in $old_versions; do
        mv feature_matrix_${ver}_* ../05_archived/ 2>/dev/null
        echo "Archived version $ver"
    done
fi
```

### 脚本 3: 生成文档索引
```bash
#!/bin/bash
# generate_index.sh
cat > logs/INDEX.md << EOF
# iSymPred Documentation Index

**Generated:** $(date +%Y-%m-%d)

---

## Current Version
$(ls logs/01_current/)

## Feature Matrix
$(ls logs/02_feature_matrix/)

## Record Predictor
$(ls logs/03_record_predictor/)

## Host Taxonomy
$(ls logs/04_host_taxonomy/)

## Archived
$(ls logs/05_archived/ | head -10)
(Showing first 10 files)

---
EOF
```

---

## 📌 最佳实践

### DO ✅
1. **及时更新文档** - 代码更新后立即更新相关文档
2. **使用清晰的命名** - 文件名应该自解释
3. **保持目录整洁** - 定期归档旧版本
4. **添加交叉引用** - 在文档间添加链接
5. **记录决策原因** - 不仅记录"做了什么"，还要记录"为什么"
6. **使用版本号** - 所有文档都应该有明确的版本标识
7. **创建快速参考** - 为复杂功能创建 QUICKREF 文档

### DON'T ❌
1. **不要在根目录堆积文件** - 所有文档都应该分类
2. **不要使用模糊的文件名** - 避免 `update.md`, `new_feature.md`
3. **不要删除重要的历史文档** - 归档而不是删除
4. **不要创建重复文档** - 更新现有文档而不是创建新文档
5. **不要忽略 INDEX.md** - 每次添加文档都要更新索引
6. **不要混合不同类别** - 特征矩阵文档不应该放在记录预测器目录
7. **不要使用空格命名** - 使用下划线代替空格

---

## 🔧 维护计划

### 每周
- [ ] 检查 `01_current/` 是否只包含最新版本
- [ ] 更新 `INDEX.md` 如果有新文档

### 每月
- [ ] 归档超过 2 个版本的旧文档
- [ ] 检查文档链接是否有效
- [ ] 清理 `05_archived/` 中超过 1 年的文档

### 每季度
- [ ] 审查文档结构是否需要调整
- [ ] 更新 `LOG_MANAGEMENT_GUIDE.md`（本文件）
- [ ] 生成文档统计报告

---

## 📞 联系与反馈

如果对日志管理有建议或发现问题：
1. 在项目中创建 Issue
2. 更新本文件并提交 PR
3. 在团队会议中讨论

---

## 📚 相关资源

- **项目文档:** `README.md`
- **开发指南:** `CLAUDE.md`
- **文档索引:** `logs/INDEX.md`

---

**版本历史:**
- v1.0 (2026-01-08) - 初始版本，建立日志管理准则

---

**END OF GUIDE**
