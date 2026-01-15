# S16 Predictor v2.3 - Contributor_List 功能

**更新日期**: 2026-01-07
**版本**: v2.2 → v2.3
**更新内容**: 在功能汇总表中新增 Contributor_List 列

---

## 📋 更新概述

在功能汇总表（`_functions.tsv`）中新增 **Contributor_List** 列，列出所有贡献该功能的微生物属（Genus 级别），方便用户快速了解功能的微生物来源。

---

## 🎯 核心改动

### 新增列：Contributor_List

**位置**: 功能汇总表最后一列

**内容**: 所有贡献该功能的属名（Genus 级别），按丰度排序，逗号分隔

**示例**:
```
Function: pathogen resistance
Contributor_List: Lactococcus, Acinetobacter, Wolbachia, Enterobacter, Serratia, Pseudomonas
```

---

## 📊 列结构变化

### 旧版 (v2.2)
```
Function | Final_Score_Sum | ... | Probability | Dominant_Contributor
```

### 新版 (v2.3)
```
Function | Final_Score_Sum | ... | Probability | Dominant_Contributor | Contributor_List
                                                                              ↑
                                                                            新增列
```

---

## 🔧 实现细节

### 数据提取逻辑

1. **来源**: 从 `contributors` 列表中提取（已按丰度排序）
2. **级别**: 提取到属（Genus）级别
3. **去重**: 同一属只出现一次
4. **排序**: 按相对丰度从高到低排序
5. **分隔**: 使用逗号+空格（`, `）分隔

### 属名提取规则

```python
# 输入格式示例:
# - "Lactococcus lactis"
# - "Acinetobacter (sp.)"

# 提取逻辑:
genus = taxon_name.split()[0]  # 取第一个单词

# 输出:
# - "Lactococcus"
# - "Acinetobacter"
```

### 去重机制

使用 `set()` 确保每个属只出现一次：
```python
seen_genera = set()
for contrib in sorted_contributors:
    genus = contrib['name'].split()[0]
    if genus not in seen_genera:
        seen_genera.add(genus)
        contributor_genera.append(genus)
```

---

## 💡 使用场景

### 1. 快速识别功能来源

**问题**: "pathogen resistance 功能主要由哪些微生物贡献？"

**答案**: 查看 Contributor_List 列
```
Lactococcus, Acinetobacter, Wolbachia, Enterobacter, Serratia
```

### 2. 功能多样性分析

**问题**: "哪些功能的微生物来源最多样？"

**方法**: 统计 Contributor_List 中的属数量
```python
df['Contributor_Count'] = df['Contributor_List'].str.split(', ').str.len()
diverse_functions = df.nlargest(10, 'Contributor_Count')
```

### 3. 核心功能菌识别

**问题**: "哪些属参与了最多的功能？"

**方法**: 统计每个属出现的频率
```python
from collections import Counter

all_genera = []
for contributors in df['Contributor_List']:
    all_genera.extend(contributors.split(', '))

genus_freq = Counter(all_genera)
top_genera = genus_freq.most_common(10)
```

### 4. 功能网络构建

**用途**: 构建"功能-微生物"二部图网络

**方法**:
```python
import networkx as nx

G = nx.Graph()
for _, row in df.iterrows():
    function = row['Function']
    genera = row['Contributor_List'].split(', ')
    for genus in genera:
        G.add_edge(function, genus, weight=row['Probability'])
```

---

## 📈 输出示例

### 完整输出格式

```tsv
Function	Final_Score_Sum	Total_RA_Pct	Mean_Confidence	Mean_Host_Match	Mean_Evidence_Weight	Taxa_Count	Probability	Dominant_Contributor	Contributor_List
pathogen resistance	208.1	10.491	0.61	1.06	1.0	183	0.212	Acinetobacter (sp.) (31.6% contribution)	Lactococcus, Acinetobacter, Wolbachia, Enterobacter, Serratia, Pseudomonas, Pantoea, Klebsiella
antimicrobial activity	203.8	9.868	0.61	1.07	1.03	198	0.194	Acinetobacter (sp.) (33.6% contribution)	Acinetobacter, Lactococcus, Wolbachia, Enterobacter, Pseudomonas, Serratia, Bacillus, Staphylococcus
```

### 与 Dominant_Contributor 的区别

**Dominant_Contributor**:
- 显示单个主要贡献者
- 包含贡献比例
- 示例: `Acinetobacter (sp.) (31.6% contribution)`

**Contributor_List**:
- 显示所有贡献者（属级别）
- 按丰度排序
- 示例: `Lactococcus, Acinetobacter, Wolbachia, Enterobacter`

---

## 🔍 数据解读

### 示例 1: 单一来源功能

```
Function: nitrogen fixation
Taxa_Count: 3
Contributor_List: Rhizobium, Bradyrhizobium, Sinorhizobium
```

**解读**: 该功能由少数特定属贡献，功能特异性强

### 示例 2: 多样来源功能

```
Function: other
Taxa_Count: 173
Contributor_List: Lactococcus, Acinetobacter, Wolbachia, Comamonas, ... (21 genera)
```

**解读**: 该功能由多个属贡献，可能是通用功能或功能定义过于宽泛

### 示例 3: 核心功能菌

如果某个属（如 Lactococcus）出现在多个功能的 Contributor_List 中：
- 可能是样本中的优势菌
- 可能具有多功能性
- 需要结合丰度数据进一步分析

---

## 📊 下游分析示例

### 1. 统计每个属的功能数量

```python
import pandas as pd
from collections import defaultdict

df = pd.read_csv('results_functions.tsv', sep='\t')

genus_functions = defaultdict(set)
for _, row in df.iterrows():
    if row['Probability'] >= 0.40:  # 只统计中等以上概率的功能
        genera = row['Contributor_List'].split(', ')
        for genus in genera:
            genus_functions[genus].add(row['Function'])

# 输出多功能菌
for genus, functions in sorted(genus_functions.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
    print(f"{genus}: {len(functions)} functions")
```

### 2. 功能特异性分析

```python
# 计算每个功能的贡献者多样性
df['Contributor_Diversity'] = df['Contributor_List'].str.split(', ').str.len()

# 识别高特异性功能（贡献者少）
specific_functions = df[df['Contributor_Diversity'] <= 5]

# 识别通用功能（贡献者多）
general_functions = df[df['Contributor_Diversity'] >= 20]
```

### 3. 核心-边缘分析

```python
# 识别核心功能菌（出现频率高）
from collections import Counter

all_genera = []
for contributors in df['Contributor_List']:
    all_genera.extend(contributors.split(', '))

genus_freq = Counter(all_genera)

# 核心菌（出现在 >50% 的功能中）
core_genera = [g for g, f in genus_freq.items() if f > len(df) * 0.5]

# 边缘菌（仅出现在 1-2 个功能中）
peripheral_genera = [g for g, f in genus_freq.items() if f <= 2]
```

---

## 🔧 代码实现位置

**文件**: `isympred/predictors/record_predictor.py`

**修改位置**: 第496-528行

**关键代码**:
```python
# 收集所有贡献者的属名
contributor_genera = []
seen_genera = set()

for contrib in sorted_contributors:
    taxon_name = contrib['name']
    genus = taxon_name.split()[0] if taxon_name else ''

    if genus and genus not in seen_genera:
        seen_genera.add(genus)
        contributor_genera.append(genus)

contributor_list = ', '.join(contributor_genera)
```

---

## 📝 注意事项

### 1. 分隔符选择

**为什么使用逗号而非制表符？**
- TSV 文件中制表符是列分隔符
- 使用制表符会导致列错位
- 逗号+空格（`, `）是标准的列表分隔符

### 2. 属名提取

**假设**:
- 分类单元名称格式为 "Genus species" 或 "Genus (sp.)"
- 属名是第一个单词

**限制**:
- 如果名称格式不标准，可能提取失败
- 不处理亚属或其他复杂分类层级

### 3. 排序依据

**当前**: 按相对丰度（RA%）从高到低排序

**替代方案**:
- 按字母顺序排序
- 按贡献分数排序
- 按出现频率排序

---

## 🔄 向后兼容性

### 输出格式
- ✅ 完全兼容，仅新增一列
- ✅ 旧版脚本可以忽略新列继续工作

### 数据处理
- ✅ 新列位于最后，不影响现有列的位置
- ✅ 可以使用 `cut -f1-9` 获取旧版格式

---

## 💡 未来扩展

### 可能的改进

1. **添加丰度信息**:
   ```
   Contributor_List: Lactococcus(15.2%), Acinetobacter(10.5%), Wolbachia(8.3%)
   ```

2. **添加置信度标记**:
   ```
   Contributor_List: Lactococcus*, Acinetobacter*, Wolbachia
   (* = species-level match)
   ```

3. **分层显示**:
   ```
   Core_Contributors: Lactococcus, Acinetobacter
   Minor_Contributors: Wolbachia, Enterobacter, Serratia
   ```

4. **功能特异性标记**:
   ```
   Contributor_List: Rhizobium†, Bradyrhizobium†
   († = function-specific genus)
   ```

---

## 📚 相关文档

- **v2.2 更新**: `record_predictor_v2.2_PROBABILITY_REFACTOR.md`
- **v2.0 更新**: `record_predictor_CHANGELOG.md`
- **使用指南**: `record_predictor_USAGE.md`

---

**版本**: v2.3
**状态**: ✅ 已完成并测试
**最后更新**: 2026-01-07
