# Record Predictor v5.0 - Function Hierarchy Update

**日期**: 2026-01-14
**版本**: v5.0
**作者**: Claude Code
**状态**: 已完成

---

## 更新概述

本次更新为 `record_predictor.py` 添加了 **Function Tag 层级关系处理** 功能，借鉴了 FAPROTAX 的设计理念，同时保留了 iSymPred 的特色（宿主上下文、证据等级、概率计算）。

---

## 新增功能

### Phase 1: 层级标注

1. **加载层级关系**
   - 从 `function_tag.tsv` 自动加载 Parent 和 Parent Category 信息
   - 构建 parent_map、children_map、level_map 等数据结构

2. **新增输出列** (`*_functions.tsv`)
   | 列名 | 类型 | 说明 |
   |------|------|------|
   | Parent | string | 直接父功能名称，None 表示顶层 |
   | Parent_Category | string | 所属大类（Defense/Nutrition/Physiology/Other） |
   | Hierarchy_Level | int | 层级深度（1=顶层，2=二级，3=三级，4=四级） |
   | Is_Leaf | bool | 是否为当前预测中的叶子功能 |

3. **新增命令行参数**
   ```bash
   --leaf-only    # 仅输出叶子功能（最具体的子功能）
   ```

### Phase 2: 高级功能

1. **概率层级传播**
   - 规则：父功能概率 = max(自身概率, 所有子功能概率的最大值)
   - 原因：如果子功能存在，父功能必然存在
   - 示例：如果 `pesticide metabolization` 概率为 0.8，则 `detoxification enzymes` 概率至少为 0.8

2. **新增输出列**
   | 列名 | 类型 | 说明 |
   |------|------|------|
   | Child_Functions | string | 当前预测中包含的子功能列表（逗号分隔） |
   | Unique_Contributors | int | 该功能独有的贡献者数量（不与子功能共享） |

---

## 使用示例

### 默认模式（输出所有功能）
```bash
python isympred/predictors/record_predictor.py \
    -i tests/data/test_data.tsv \
    -d isympred/database/symbiont_record/record_db.tsv \
    -o tmp/output.tsv \
    --host "Drosophila melanogaster"
```

### Leaf-only 模式（仅输出叶子功能）
```bash
python isympred/predictors/record_predictor.py \
    -i tests/data/test_data.tsv \
    -d isympred/database/symbiont_record/record_db.tsv \
    -o tmp/output.tsv \
    --host "Drosophila melanogaster" \
    --leaf-only
```

---

## 输出示例

### 默认模式输出
```
Function                    Probability  Parent                  Hierarchy_Level  Is_Leaf  Child_Functions
pesticide metabolization    0.522        detoxification enzymes  4                True     None
detoxification enzymes      0.522        stress resistance       3                False    pesticide metabolization, plant secondary metabolites
stress resistance           0.735        None                    2                False    temparature adaptation, natural enemy resistance, ...
antimicrobial activity      0.735        stress resistance       3                True     None
```

### Leaf-only 模式输出
```
Function                    Probability  Parent                  Hierarchy_Level  Is_Leaf  Child_Functions
pesticide metabolization    0.522        detoxification enzymes  4                True     None
antimicrobial activity      0.735        stress resistance       3                True     None
pathogen resistance         0.734        stress resistance       3                True     None
```

---

## 层级关系示例

```
Defense (Parent Category)
├── stress resistance (Level 2)
│   ├── temparature adaptation (Level 3, Leaf)
│   ├── natural enemy resistance (Level 3, Leaf)
│   ├── pathogen resistance (Level 3, Leaf)
│   ├── antiviral activity (Level 3, Leaf)
│   ├── antimicrobial activity (Level 3, Leaf)
│   └── detoxification enzymes (Level 3)
│       ├── pesticide metabolization (Level 4, Leaf)
│       └── plant secondary metabolites (Level 4, Leaf)
├── plant defense modulation (Level 2, Leaf)

Nutrition (Parent Category)
├── nutrient provision (Level 2)
│   ├── amino acid provision (Level 3, Leaf)
│   ├── vitamin supplementation (Level 3, Leaf)
│   └── nitrogen fixation (Level 3, Leaf)
├── plant biomass digestion (Level 2)
│   ├── cellulose hydrolysis (Level 3, Leaf)
│   ├── xylan hydrolysis (Level 3, Leaf)
│   ├── lipase (Level 3, Leaf)
│   └── pectin hydrolysis (Level 3, Leaf)

Other (Parent Category)
├── chemical biosynthesis (Level 2)
│   ├── toxin production (Level 3, Leaf)
│   └── semiochemical biosynthesis (Level 3, Leaf)
```

---

## 技术实现

### 新增方法

1. `_load_function_hierarchy(hierarchy_file)` - 加载层级关系
2. `_get_hierarchy_level(func)` - 获取层级深度
3. `_get_parent(func)` - 获取父功能
4. `_get_category(func)` - 获取大类
5. `_get_children(func)` - 获取子功能列表
6. `_identify_leaf_functions(predicted_functions)` - 识别叶子功能
7. `_get_predicted_children(func, predicted_functions)` - 获取预测中的子功能
8. `_propagate_probability_to_parents(func_results)` - 概率传播
9. `_calculate_unique_contributors(func_results)` - 计算独有贡献者

### 修改的参数

`RecordPredictor.__init__()` 新增参数：
- `leaf_only` (bool): 是否仅输出叶子功能，默认 False

---

## 与 FAPROTAX 的对比

| 方面 | FAPROTAX | iSymPred v5.0 |
|------|----------|---------------|
| 层级定义 | `add_group:` 显式定义 | Parent 列引用 |
| 输出粒度 | 全部输出 | 默认全部，支持 `--leaf-only` |
| 层级标注 | 无 | Parent, Level, Is_Leaf 列 |
| 概率计算 | 无 | 支持层级传播 |
| 独有贡献者 | 无 | Unique_Contributors 列 |

---

## 测试结果

```
# 默认模式
Function summary: 46 functions
- 叶子功能: 40
- 非叶子功能: 6

# Leaf-only 模式
Function summary: 40 functions (filtered from 46)
- 被过滤的非叶子功能:
  - stress resistance
  - detoxification enzymes
  - chemical biosynthesis
  - nutrient provision
  - plant biomass digestion
  - carbohydrate metabolism
```

---

## 后续计划

- [ ] Phase 3: 生成 `*_functions_hierarchy.tsv` 层级汇总表（可选）
- [ ] Phase 3: 在 `*_feature_matrix.tsv` 中添加 `Is_Leaf_Function` 和 `Hierarchy_Level` 特征
- [ ] 根据用户反馈决定是否实现 FAPROTAX 风格的层级聚合（`--aggregate-hierarchy`）
