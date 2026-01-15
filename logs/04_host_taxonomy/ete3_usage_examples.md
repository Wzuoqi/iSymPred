# ete3 宿主分类查询 - 使用示例

**日期:** 2026-01-08
**版本:** v2.2

---

## 快速开始

### 1. 安装依赖

```bash
pip install ete3
```

### 2. 基本使用

```bash
# 使用宿主信息进行预测
python isympred/predictors/record_predictor.py \
    -i tests/data/test_data.tsv \
    -d isympred/database/symbiont_record/record_db.tsv \
    -o output.tsv \
    --host "Drosophila melanogaster"
```

### 3. 首次运行

首次使用时会自动下载 NCBI Taxonomy 数据库（约 200MB）：

```
[Info] Using ete3 NCBITaxa for host taxonomy queries
Downloading taxdump.tar.gz from NCBI FTP...
Extracting taxonomy database...
[Host Taxonomy] Drosophila melanogaster -> Order: Diptera, Family: Drosophilidae, Genus: Drosophila
```

---

## Python API 使用

### 直接使用 ete3 查询

```python
from ete3 import NCBITaxa

# 初始化
ncbi = NCBITaxa()

# 查询物种分类
host = "Apis mellifera"
name2taxid = ncbi.get_name_translator([host])

if host in name2taxid:
    taxid = name2taxid[host][0]

    # 获取分类谱系
    lineage = ncbi.get_lineage(taxid)

    # 获取分类等级和名称
    ranks = ncbi.get_rank(lineage)
    names = ncbi.get_taxid_translator(lineage)

    # 提取目、科、属
    for tid in lineage:
        rank = ranks.get(tid, "")
        name = names.get(tid, "")
        if rank in ["order", "family", "genus"]:
            print(f"{rank}: {name}")
```

输出：
```
order: Hymenoptera
family: Apidae
genus: Apis
```

### 在 RecordPredictor 中使用

```python
from isympred.predictors.record_predictor import RecordPredictor

# 初始化预测器（自动使用 ete3）
predictor = RecordPredictor(
    db_path="isympred/database/symbiont_record/record_db.tsv",
    user_host="Bombyx mori"
)

# 运行预测
predictor.predict(
    input_table_path="tests/data/test_data.tsv",
    output_path="output.tsv"
)
```

---

## 常见宿主示例

### 模式昆虫

```python
from ete3 import NCBITaxa
ncbi = NCBITaxa()

model_insects = [
    "Drosophila melanogaster",  # 黑腹果蝇
    "Bombyx mori",              # 家蚕
    "Apis mellifera",           # 西方蜜蜂
    "Tribolium castaneum",      # 赤拟谷盗
]

for host in model_insects:
    name2taxid = ncbi.get_name_translator([host])
    if host in name2taxid:
        taxid = name2taxid[host][0]
        lineage = ncbi.get_lineage(taxid)
        ranks = ncbi.get_rank(lineage)
        names = ncbi.get_taxid_translator(lineage)

        order = family = genus = "N/A"
        for tid in lineage:
            if ranks.get(tid) == "order":
                order = names.
            elif ranks.get(tid) == "family":
                family = names.get(tid)
            elif ranks.get(tid) == "genus":
                genus = names.get(tid)

        print(f"{host}:")
        print(f"  Order: {order}, Family: {family}, Genus: {genus}\n")
```

输出：
```
Drosophila melanogaster:
  Order: Diptera, Family: Drosophilidae, Genus: Drosophila

Bombyx mori:
  Order: Lepidoptera, Family: Bombycidae, Genus: Bombyx

Apis mellifera:
  Order: Hymenoptera, Family: Apidae, Genus: Apis

Triboliuum:
  Order: Coleoptera, Family: Tenebrionidae, Genus: Tribolium
```

### 农业害虫

```python
agricultural_pests = [
    "Helicoverpa armigera",     # 棉铃虫
    "Spodoptera frugiperda",    # 草地贪夜蛾
    "Plutella xylostella",      # 小菜蛾
    "Nilaparvata lugens",       # 褐飞虱
]

# 使用相同的查询代码...
```

### 传粉昆虫

```python
pollinators = [
    "Apis mellifera",           # 西方蜜蜂
    "Bombus terrestris",        # 熊蜂
    "Megachile rotundata",      # 苜蓿切叶蜂
]

# 使用相同的查询代码...
```

---

## 高级功能

### 1. 更新 NCBI Taxonomy 数据库

```python
from ete3 import NCBITaxa

ncbi = NCBITaxa()

# 更新到最新版本
ncbi.update_taxonomy_database()
```

### 2. 批量查询

```python
from ete3 import NCBITaxa

ncbi = NCBITaxa()

# 批量查询多个物种
hosts = [
    "Drosophila melanogaster",
    "Apis mellifera",
    "Bombyx mor
]

# 一次性查询所有物种的 taxid
name2taxid = ncbi.get_name_translator(hosts)

for host in hosts:
    if host in name2taxid:
        taxid = name2taxid[host][0]
        print(f"{host}: taxid={taxid}")
```

### 3. 查询同义名

```python
from ete3 import NCBITaxa

ncbi = NCBITaxa()

# 查询物种的所有同义名
taxid = 7227  # Drosophila melanogaster
synonyms = ncbi.get_taxid_translator([taxid])
print(f"Synonyms: {synonyms}")
```

### 4. 获取完整分类树

```python
from ete3 import NCBITaxa

ncbi = NCBITaxa()

# 获取完整的分类树
host = "Apis mellifera"
name2taxid = ncbi.get_name_translator([host])
taxid = name2taxid[host][0]

# 获取分类谱系
lineage = ncbi.get_lineage(taxid)
ranks = ncbi.get_rank(lineage)
names = ncbi.get_taxid_translator(lineage)

print(f"Complete lineage for {host}:")
for tid in lineage:
    rank = ranks.get(tid, "no rank")
    name = names.get(tid, "unknown")
    print(f"  {rank}: {name}")
```

---

## 故障排除

### 问题 1: 网络连接失败

```python
# 设置代理（如果需要）
import os
os.environ['http_proxy'] = 'http://proxy.example.com:8080'
os.environ['https_proxy'] = 'http://proxy.example.com:8080'

from ete3 import NCBITaxa
ncbi = NCBITaxa()
```

### 问题 2: 数据库损坏

```python
from ete3 import NCBITaxa
import os

# 删除旧数据库
db_path = os.path.expanduser("~/.etetoolkit/taxa.sqlite")
if os.path.exists(db_path):
    os.remove(db_path)

# 重新下载
ncbi = NCBITaxa()
ncbi.update_taxonomy_database()
```

### 问题 3: 物种名未找到

```python
from ete3 import NCBITaxa

ncbi = NCBITaxa()

# 尝试模糊搜索
host = "Drosophila"
results = ncbi.get_name_translator([host])

if not results:
    # 尝试搜索所有包含该名称的物种
    print(f"Searching for species containing '{host}'...")
    # 注意：ete3 不直接支持模糊搜索，需要使用 NCBI Entrez API
```

---

## 性能优化

### 1. 缓存查询结果

```python
from ete3 import NCBITaxa
from functools import lru_cache

ncbi = NCBITaxa()

@lru_cache(maxsize=1000)
def get_host_taxonomy(host):
    """缓存宿主分类查询结果"""
    name2taxid = ncbi.get_name_translator([host])
    if host not in name2taxid:
        return None

    taxid = name2taxid[host][0]
    lineage = ncbi.get_lineage(taxid)
    ranks = ncbi.get_rank(lineage)
    names = ncbi.get_taxid_translator(lineage)

    result = {"order": "N/A", "family": "N/A", "genus": "N/A", "species": host}
    for tid in lineage:
        rank = ranks.get(tid, "")
        name = names.get(tid, "")
        if rank in result:
            result[rank] = name

    return result

# 使用缓存
taxonomy1 = get_host_taxonomy("Apis mellifera")  # 查询数据库
taxonomy2 = get_host_taxonomy("Apis mellifera")  # 使用缓存
```

### 2. 预加载常用物种

```python
from ete3 import NCBITaxa

ncbi = NCBITaxa()

# 预加载常用昆虫宿主
common_hosts = [
    "Drosophila melanogaster",
    "Apis mellifera",
    "Bombyx mori",
    "Acyrthosiphon pisum",
    # ... 更多常用物种
]

# 批量查询并缓存
host_cache = {}
name2taxid = ncbi.get_name_translator(common_hosts)

for host in common_hosts:
    if host in name2taxid:
        taxid = name2taxid[host][0]
        lineage = ncbi.get_lineage(taxid)
        ranks = ncbi.get_rank(lineage)
        names = ncbi.get_taxid_translator(lineage)

        result = {"order": "N/A", "family": "N/A", "genus": "N/A", "species": host}
        for tid in lineage:
            rank = ranks.get(tid, "")
            name = names.get(tid, "")
            if rank in result:
                result[rank] = name

        host_cache[host] = result

# 使用缓存
def get_cached_taxonomy(host):
    return host_cache.get(host)
```

---

## 参考资源

- **ete3 官方文档:** http://etetoolkit.org/
- **NCBI Taxonomy:** https://www.ncbi.nlm.nih.gov/taxonomy
- **ete3 GitHub:** https://github.com/etetoolkit/ete

---

**版本:** v2.2
**日期:** 2026-01-08
**作者:** Claude Code Assistant

---

**END OF DOCUMENT**
