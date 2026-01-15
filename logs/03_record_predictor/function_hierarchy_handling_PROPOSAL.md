# Function Tag 层级关系处理方案

**日期**: 2026-01-14
**版本**: v2.0 (结合 FAPROTAX 经验)
**作者**: Claude Code
**状态**: 待讨论

---

## 1. 问题描述

### 1.1 当前情况

在 `function_tag.tsv` 中，部分 Function Tag 存在父子层级关系：

| Function Tag | Parent | Parent Category |
|--------------|--------|-----------------|
| stress resistance | None | Defense |
| temperature adaptation | stress resistance | Defense |
| natural enemy resistance | stress resistance | Defense |
| pathogen resistance | stress resistance | Defense |
| detoxification enzymes | stress resistance | Defense |
| pesticide metabolization | detoxification enzymes | Defense |
| toxin production | chemical biosynthesis | Other |
| semiochemical biosynthesis | chemical biosynthesis | Other |
| cellulose hydrolysis | plant biomass digestion | Nutrition |
| ... | ... | ... |

### 1.2 问题场景

当预测结果同时包含子功能和父功能时，会出现以下问题：

**示例 1**: 某共生菌被预测具有 `toxin production` 功能
- `toxin production` 的 Parent 是 `chemical biosynthesis`
- 如果同时输出两者，用户可能会误认为这是两个独立的功能
- 实际上 `toxin production` 是 `chemical biosynthesis` 的一种具体形式

**示例 2**: 某共生菌被预测具有 `pesticide metabolization` 功能
- 层级链：`pesticide metabolization` → `detoxification enzymes` → `stress resistance`
- 如果三者都出现在结果中，会造成功能冗余和混淆

---

## 2. FAPROTAX 的层级处理机制分析

### 2.1 FAPROTAX 数据库结构

FAPROTAX 使用 **集合操作（Set Operations）** 来定义功能组之间的层级关系：

```
# 子功能定义
acetoclastic_methanogenesis
*Methanosarcina*barkeri*
*Methanosarcina*acetivorans*
...

methanogenesis_by_CO2_reduction_with_H2
*Methanosarcina*barkeri*
*Methanomicrobiales*
...

# 父功能通过 add_group: 聚合子功能
hydrogenotrophic_methanogenesis
add_group:methanogenesis_by_CO2_reduction_with_H2
add_group:methanogenesis_by_reduction_of_methyl_compounds_with_H2
*Methanobacteriales*
...

# 顶层功能聚合所有子功能
methanogenesis
add_group:hydrogenotrophic_methanogenesis
add_group:methanogenesis_by_disproportionation_of_methyl_groups
add_group:acetoclastic_methanogenesis
add_group:methanogenesis_using_formate
...

# 另一个例子：nitrification = aerobic_ammonia_oxidation + aerobic_nitrite_oxidation
nitrification
add_group:aerobic_ammonia_oxidation
add_group:aerobic_nitrite_oxidation
```

### 2.2 FAPROTAX 的核心设计理念

1. **允许重叠（Overlapping Groups）**
   - FAPROTAX 明确允许功能组之间存在重叠
   - 同一个 OTU 可以被分配到多个功能组
   - **关键点**：输出表的列总和通常不等于输入表的列总和（因为存在重复计数）

2. **多对多映射（Many-to-Many Mapping）**
   - `group_to_records[g]` 是一个 Set，包含属于该功能组的所有记录索引
   - 一个记录可以出现在多个功能组中
   - 这是 **设计意图**，而非 bug

3. **集合操作实现层级**
   ```python
   # FAPROTAX 的集合操作逻辑
   if operation == 0:  # add_group (并集)
       group_to_records[current_group].update(group_to_records[target_group])
   elif operation == 1:  # subtract_group (差集)
       group_to_records[current_group].difference_update(group_to_records[target_group])
   elif operation == 2:  # intersect_group (交集)
       group_to_records[current_group].intersection_update(group_to_records[target_group])
   ```

4. **父功能 = 子功能的并集 + 额外成员**
   - 父功能通过 `add_group:` 包含所有子功能的成员
   - 父功能还可以有自己独有的成员（不属于任何子功能）
   - 这意味着：**父功能的记录数 ≥ 所有子功能记录数的并集**

### 2.3 FAPROTAX 的输出策略

FAPROTAX **同时输出所有功能组**，包括父功能和子功能：

```
# FAPROTAX 输出示例（功能表）
Function                              Sample_A    Sample_B
methanogenesis                        1250        890
hydrogenotrophic_methanogenesis       800         500
acetoclastic_methanogenesis           450         390
methanogenesis_by_CO2_reduction_with_H2  600      400
...
```

**FAPROTAX 的设计哲学**：
- 用户可能对不同粒度的功能感兴趣
- 父功能提供宏观视角，子功能提供精确信息
- 由用户根据研究需求选择使用哪个层级

### 2.4 FAPROTAX 的 Report 文件

FAPROTAX 生成详细的 Report 文件，列出每个功能组包含的 OTU：

```
# methanogenesis (45 records):
    OTU_001 (Methanosarcina barkeri)
    OTU_023 (Methanobacterium)
    ...

# hydrogenotrophic_methanogenesis (30 records):
    OTU_001 (Methanosarcina barkeri)
    OTU_023 (Methanobacterium)
    ...
```

这让用户可以清楚地看到哪些 OTU 被分配到了哪些功能组。

---

## 3. iSymPred 与 FAPROTAX 的差异

| 特性 | FAPROTAX | iSymPred |
|------|----------|----------|
| 数据库结构 | 功能组定义文件（含 add_group:） | TSV 表格（含 Parent 列） |
| 层级定义方式 | 集合操作（add_group:, subtract_group:） | Parent 字段引用 |
| 匹配逻辑 | 分类学字符串匹配 | 分类学 + 宿主上下文 + 证据等级 |
| 输出粒度 | 所有功能组（含重叠） | 当前：所有功能（无层级标注） |
| 丰度计算 | 简单求和/平均 | 加权评分（宿主、证据、置信度） |

### 3.1 iSymPred 的特殊考虑

1. **宿主上下文权重**：iSymPred 的预测考虑了宿主匹配度，这在 FAPROTAX 中不存在
2. **证据等级**：iSymPred 有文献证据等级评分
3. **概率计算**：iSymPred 计算功能存在概率，需要考虑层级关系对概率的影响

---

## 4. 推荐方案：借鉴 FAPROTAX + iSymPred 特色

### 4.1 核心原则

1. **保留完整信息**：像 FAPROTAX 一样，同时输出所有层级的功能
2. **添加层级标注**：明确标注父子关系，便于用户理解
3. **提供过滤选项**：允许用户选择只看叶子功能或只看顶层功能
4. **避免重复计数**：在汇总统计时，提供去重选项

### 4.2 数据库增强：引入 `add_group:` 机制（可选）

借鉴 FAPROTAX，可以在 `record_db.tsv` 或预测逻辑中实现类似的集合操作：

**方案 A：在数据库层面定义（推荐）**

在 `function_tag.tsv` 中添加 `Members` 列，定义父功能包含哪些子功能：

```tsv
Function Tag    Parent              Parent Category    Members
stress resistance    None           Defense            add_group:temperature adaptation,add_group:natural enemy resistance,add_group:pathogen resistance,...
detoxification enzymes    stress resistance    Defense    add_group:pesticide metabolization,add_group:plant secondary metabolites
chemical biosynthesis    None       Other              add_group:toxin production,add_group:semiochemical biosynthesis
```

**方案 B：在预测逻辑中实现（更灵活）**

在 `record_predictor.py` 中，根据 `function_tag.tsv` 的 Parent 关系，自动将子功能的贡献者聚合到父功能：

```python
def aggregate_to_parent_functions(func_results, parent_map, children_map):
    """
    将子功能的贡献者聚合到父功能（类似 FAPROTAX 的 add_group:）

    注意：这会导致父功能的 Taxa_Count 和 RA% 包含所有子功能的贡献
    """
    for func in list(func_results.keys()):
        parent = parent_map.get(func)
        while parent:
            if parent not in func_results:
                # 初始化父功能
                func_results[parent] = {
                    'fps_score': 0.0,
                    'ra_sum': 0.0,
                    'contributors': [],
                    # ... 其他字段
                }
            # 将子功能的贡献者添加到父功能（去重）
            child_contributors = set(c['name'] for c in func_results[func]['contributors'])
            parent_contributors = set(c['name'] for c in func_results[parent]['contributors'])
            new_contributors = child_contributors - parent_contributors
            # ... 聚合逻辑
            parent = parent_map.get(parent)
```

### 4.3 输出格式增强

#### 4.3.1 `*_functions.tsv` 新增列

| 列名 | 类型 | 说明 |
|------|------|------|
| Parent | string | 直接父功能名称，None 表示顶层 |
| Parent_Category | string | 所属大类（Defense/Nutrition/Physiology/Other） |
| Hierarchy_Level | int | 层级深度（1=顶层，2=二级，3=三级） |
| Is_Leaf | bool | 是否为当前预测中的叶子功能 |
| Child_Functions | string | 当前预测中包含的子功能列表（逗号分隔） |
| Unique_Contributors | int | 该功能独有的贡献者数量（不与子功能共享） |

**输出示例**：
```tsv
Function                    Final_Score_Sum  Total_RA_Pct  ...  Parent                  Parent_Category  Hierarchy_Level  Is_Leaf  Child_Functions                          Unique_Contributors
pesticide metabolization    2701.7           220.08        ...  detoxification enzymes  Defense          3                True     None                                     150
detoxification enzymes      1885.0           205.31        ...  stress resistance       Defense          2                False    pesticide metabolization,plant secondary metabolites  45
stress resistance           3500.0           300.00        ...  None                    Defense          1                False    detoxification enzymes,pathogen resistance,...  20
toxin production            500.0            30.00         ...  chemical biosynthesis   Other            2                True     None                                     13
chemical biosynthesis       1476.9           93.26         ...  None                    Other            1                False    toxin production,semiochemical biosynthesis  30
```

#### 4.3.2 新增 `*_functions_hierarchy.tsv`（可选）

专门展示层级关系的视图：

```tsv
Function                    Hierarchy_Path                                              Level  Total_RA_Pct  Unique_RA_Pct
pesticide metabolization    Defense > stress resistance > detoxification enzymes > pesticide metabolization  3  220.08  220.08
detoxification enzymes      Defense > stress resistance > detoxification enzymes        2      205.31        -14.77
stress resistance           Defense > stress resistance                                 1      300.00        94.69
```

其中 `Unique_RA_Pct` = 该功能的 RA% - 所有子功能 RA% 的并集

### 4.4 命令行参数

```bash
# 默认：输出所有功能（含层级标注）
python record_predictor.py -i input.tsv -d db.tsv -o output.tsv

# 仅输出叶子功能（最具体的子功能）
python record_predictor.py -i input.tsv -d db.tsv -o output.tsv --leaf-only

# 仅输出顶层功能（Parent=None）
python record_predictor.py -i input.tsv -d db.tsv -o output.tsv --top-level-only

# 输出层级汇总表
python record_predictor.py -i input.tsv -d db.tsv -o output.tsv --hierarchy-summary

# 禁用父功能聚合（不将子功能贡献者计入父功能）
python record_predictor.py -i input.tsv -d db.tsv -o output.tsv --no-hierarchy-aggregation
```

---

## 5. 实现细节

### 5.1 加载层级关系

```python
def load_function_hierarchy(hierarchy_file):
    """
    加载 function_tag.tsv 中的层级关系

    Returns:
        parent_map: {function: parent}
        category_map: {function: parent_category}
        children_map: {function: [children]}
        level_map: {function: hierarchy_level}
    """
    import pandas as pd

    df = pd.read_csv(hierarchy_file, sep='\t')

    parent_map = {}
    category_map = {}
    children_map = {}

    for _, row in df.iterrows():
        func = row['Function Tag']
        parent = row['Parent'] if row['Parent'] != 'None' else None
        category = row['Parent Category']

        parent_map[func] = parent
        category_map[func] = category

        if parent:
            if parent not in children_map:
                children_map[parent] = []
            children_map[parent].append(func)

    # 计算层级深度
    level_map = {}
    for func in parent_map:
        level = 1
        current = parent_map.get(func)
        while current:
            level += 1
            current = parent_map.get(current)
        level_map[func] = level

    return parent_map, category_map, children_map, level_map
```

### 5.2 判断叶子功能

```python
def identify_leaf_functions(predicted_functions, children_map):
    """
    识别当前预测结果中的叶子功能

    Args:
        predicted_functions: 预测到的功能集合
        children_map: {function: [children]} 映射

    Returns:
        set: 叶子功能集合
    """
    leaf_functions = set()

    for func in predicted_functions:
        children = children_map.get(func, [])
        # 检查是否有任何子功能出现在预测结果中
        has_predicted_child = any(child in predicted_functions for child in children)
        if not has_predicted_child:
            leaf_functions.add(func)

    return leaf_functions
```

### 5.3 FAPROTAX 风格的层级聚合

```python
def aggregate_hierarchy_faprotax_style(func_results, parent_map, children_map):
    """
    类似 FAPROTAX 的 add_group: 机制
    将子功能的贡献者聚合到父功能

    注意：这会修改 func_results，使父功能包含所有子功能的贡献者
    """
    # 按层级深度排序，从最深的子功能开始向上聚合
    sorted_funcs = sorted(
        func_results.keys(),
        key=lambda f: get_hierarchy_level(f, parent_map),
        reverse=True
    )

    for func in sorted_funcs:
        parent = parent_map.get(func)
        if not parent:
            continue

        if parent not in func_results:
            # 初始化父功能（如果数据库中有但预测中没有直接匹配）
            func_results[parent] = {
                'fps_score': 0.0,
                'ra_sum': 0.0,
                'raw_reads': 0,
                'weighted_conf_sum': 0.0,
                'weighted_host_sum': 0.0,
                'weighted_evidence_sum': 0.0,
                'contributors': [],
                'from_aggregation': True  # 标记为聚合产生
            }

        # 聚合贡献者（去重）
        existing_names = {c['name'] for c in func_results[parent]['contributors']}
        for contrib in func_results[func]['contributors']:
            if contrib['name'] not in existing_names:
                func_results[parent]['contributors'].append(contrib.copy())
                existing_names.add(contrib['name'])

                # 聚合数值（注意：这里需要避免重复计数）
                # 只有当贡献者是新增的时候才累加
                func_results[parent]['fps_score'] += contrib.get('score', 0)
                func_results[parent]['ra_sum'] += contrib['ra']
                # ... 其他字段

    return func_results
```

### 5.4 计算独有贡献者

```python
def calculate_unique_contributors(func_results, children_map):
    """
    计算每个功能独有的贡献者数量（不与子功能共享）

    这对于理解父功能的"额外价值"很重要
    """
    unique_counts = {}

    for func, data in func_results.items():
        func_contributors = {c['name'] for c in data['contributors']}

        # 收集所有子功能的贡献者
        child_contributors = set()
        for child in children_map.get(func, []):
            if child in func_results:
                child_contributors.update(
                    c['name'] for c in func_results[child]['contributors']
                )

        # 独有贡献者 = 该功能贡献者 - 所有子功能贡献者
        unique = func_contributors - child_contributors
        unique_counts[func] = len(unique)

    return unique_counts
```

### 5.5 过滤输出

```python
def filter_functions_by_hierarchy(func_results, parent_map, children_map, mode='all'):
    """
    根据层级关系过滤功能

    Args:
        mode: 'all' | 'leaf-only' | 'top-level-only'

    Returns:
        过滤后的 func_results
    """
    if mode == 'all':
        return func_results

    predicted = set(func_results.keys())

    if mode == 'leaf-only':
        # 只保留叶子功能
        leaves = identify_leaf_functions(predicted, children_map)
        return {f: d for f, d in func_results.items() if f in leaves}

    elif mode == 'top-level-only':
        # 只保留顶层功能（Parent=None）
        return {f: d for f, d in func_results.items() if parent_map.get(f) is None}

    return func_results
```

---

## 6. 概率计算的层级考虑

### 6.1 当前问题

当前的概率计算没有考虑层级关系。如果 `pesticide metabolization` 的概率是 0.7，那么其父功能 `detoxification enzymes` 的概率应该至少是 0.7（因为子功能存在意味着父功能存在）。

### 6.2 层级概率传播

```python
def propagate_probability_to_parents(func_results, parent_map):
    """
    将子功能的概率传播到父功能

    规则：父功能概率 = max(自身概率, 所有子功能概率的最大值)

    原因：如果子功能存在，父功能必然存在
    """
    # 按层级深度排序，从最深的子功能开始向上传播
    sorted_funcs = sorted(
        func_results.keys(),
        key=lambda f: get_hierarchy_level(f, parent_map),
        reverse=True
    )

    for func in sorted_funcs:
        parent = parent_map.get(func)
        if parent and parent in func_results:
            child_prob = func_results[func].get('Probability', 0)
            parent_prob = func_results[parent].get('Probability', 0)
            # 父功能概率至少等于子功能概率
            func_results[parent]['Probability'] = max(parent_prob, child_prob)

    return func_results
```

---

## 7. 与 FAPROTAX 的关键差异总结

| 方面 | FAPROTAX 做法 | iSymPred 推荐做法 |
|------|--------------|------------------|
| 层级定义 | 在数据库中用 `add_group:` 显式定义 | 在 `function_tag.tsv` 中用 Parent 列定义 |
| 重复计数 | 允许，用户自行处理 | 提供 `Unique_Contributors` 列帮助用户理解 |
| 输出粒度 | 全部输出 | 默认全部输出，提供 `--leaf-only` 等过滤选项 |
| 层级标注 | 无（用户需查阅数据库） | 在输出中明确标注 Parent、Level、Is_Leaf |
| 概率计算 | 无 | 考虑层级传播（子功能存在 → 父功能存在） |

---

## 8. 测试用例

### 8.1 基本层级识别

**输入**:
```python
predicted = {'pesticide metabolization', 'detoxification enzymes', 'stress resistance'}
```

**期望输出**:
```python
# Is_Leaf 标注
{
    'pesticide metabolization': {'Is_Leaf': True, 'Level': 3},
    'detoxification enzymes': {'Is_Leaf': False, 'Level': 2},
    'stress resistance': {'Is_Leaf': False, 'Level': 1}
}

# --leaf-only 模式
filtered = {'pesticide metabolization'}
```

### 8.2 多分支情况

**输入**:
```python
predicted = {'pesticide metabolization', 'pathogen resistance', 'stress resistance'}
# pesticide metabolization → detoxification enzymes → stress resistance
# pathogen resistance → stress resistance
```

**期望输出**:
```python
# Is_Leaf 标注
{
    'pesticide metabolization': {'Is_Leaf': True},
    'pathogen resistance': {'Is_Leaf': True},
    'stress resistance': {'Is_Leaf': False}
}

# --leaf-only 模式
filtered = {'pesticide metabolization', 'pathogen resistance'}
```

### 8.3 概率传播

**输入**:
```python
func_results = {
    'pesticide metabolization': {'Probability': 0.8},
    'detoxification enzymes': {'Probability': 0.5},
    'stress resistance': {'Probability': 0.3}
}
```

**期望输出（概率传播后）**:
```python
{
    'pesticide metabolization': {'Probability': 0.8},
    'detoxification enzymes': {'Probability': 0.8},  # max(0.5, 0.8)
    'stress resistance': {'Probability': 0.8}        # max(0.3, 0.8)
}
```

---

## 9. 实现优先级

### Phase 1（必须）
1. 加载 `function_tag.tsv` 的层级关系
2. 在 `*_functions.tsv` 中添加 `Parent`, `Parent_Category`, `Hierarchy_Level`, `Is_Leaf` 列
3. 实现 `--leaf-only` 参数

### Phase 2（推荐）
4. 实现概率的层级传播
5. 添加 `Child_Functions` 和 `Unique_Contributors` 列
6. 实现 `--top-level-only` 参数

### Phase 3（可选）
7. 生成 `*_functions_hierarchy.tsv` 层级汇总表
8. 实现 FAPROTAX 风格的层级聚合（`--aggregate-hierarchy`）
9. 在 `*_feature_matrix.tsv` 中添加 `Is_Leaf_Function` 和 `Hierarchy_Level` 特征

---

## 10. 决策点

请确认以下选项：

1. **默认行为**:
   - [ ] A: 默认输出所有功能（含层级标注）— **推荐，与 FAPROTAX 一致**
   - [ ] B: 默认仅输出叶子功能

2. **是否实现 FAPROTAX 风格的层级聚合**:
   - [ ] A: 是，将子功能贡献者自动聚合到父功能
   - [ ] B: 否，保持当前独立计算方式 — **推荐，更简单**

3. **概率传播**:
   - [ ] A: 实现概率向上传播（子功能概率 → 父功能概率）— **推荐**
   - [ ] B: 不实现，保持独立计算

4. **参数命名**:
   - [ ] `--leaf-only` — **推荐**
   - [ ] `--specific-only`
   - [ ] `--no-parent-functions`

---

## 11. 总结

| 方案 | 复杂度 | 信息保留 | FAPROTAX 兼容性 | 推荐度 |
|------|--------|----------|-----------------|--------|
| 仅添加层级标注列 | 低 | 高 | 高 | ★★★★★ |
| + `--leaf-only` 过滤 | 低 | 高 | 高 | ★★★★★ |
| + 概率层级传播 | 中 | 高 | 中 | ★★★★☆ |
| + FAPROTAX 风格聚合 | 高 | 高 | 最高 | ★★★☆☆ |

**最终推荐**：
1. **Phase 1**：添加层级标注列 + `--leaf-only` 参数（最小改动，最大收益）
2. **Phase 2**：实现概率层级传播（提高生物学合理性）
3. **Phase 3**：根据用户反馈决定是否实现 FAPROTAX 风格聚合
