#!/usr/bin/env python3
"""
测试分类学距离（Taxonomic Distance）计算功能

展示如何使用 ete3 计算不同宿主之间的进化距离
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from ete3 import NCBITaxa
    print("✅ ete3 已安装\n")
except ImportError:
    print("❌ ete3 未安装")
    print("请运行: pip install ete3")
    sys.exit(1)

# 初始化 NCBITaxa
print("初始化 NCBITaxa...")
ncbi = NCBITaxa()
print("✅ 初始化成功\n")

# 定义测试用的宿主
query_host = "Drosophila melanogaster"  # 查询宿主（黑腹果蝇）

# 测试不同距离的宿主
test_hosts = [
    ("Drosophila melanogaster", "黑腹果蝇", "同种"),
    ("Drosophila simulans", "拟果蝇", "同属不同种"),
    ("Musca domestica", "家蝇", "同目不同科"),
    ("Apis mellifera", "西方蜜蜂", "不同目"),
    ("Bombyx mori", "家蚕", "不同目"),
]

print("="*80)
print(f"查询宿主: {query_host} (黑腹果蝇)")
print("="*80)

# 获取查询宿主的信息
query_name2taxid = ncbi.get_name_translator([query_host])
if query_host not in query_name2taxid:
    print(f"错误: 无法找到 {query_host}")
    sys.exit(1)

query_taxid = query_name2taxid[query_host][0]
query_lineage = set(ncbi.get_lineage(query_taxid))

print(f"TaxID: {query_taxid}")
print(f"谱系长度: {len(query_lineage)} 个分类单元\n")

# 定义距离映射
rank_distance = {
    "species": 0,
    "genus": 1,
    "family": 2,
    "order": 3,
    "class": 4,
    "phylum": 5,
    "superkingdom": 6
}

distance_names = {
    0: "同种",
    1: "同属不同种",
    2: "同科不同属",
    3: "同目不同科",
    4: "同纲不同目",
    5: "同门不同纲",
    6: "不同门"
}

print("="*80)
print("分类学距离计算结果")
print("="*80)

for db_host, chinese_name, expected in test_hosts:
    print(f"\n目标宿主: {db_host} ({chinese_name})")
    print(f"预期距离: {expected}")
    print("-" * 80)

    try:
        # 查询目标宿主的 taxid
        db_name2taxid = ncbi.get_name_translator([db_host])

        if db_host not in db_name2taxid:
            print(f"  ❌ 无法找到物种: {db_host}")
            continue

        db_taxid = db_name2taxid[db_host][0]

        # 如果是同一物种
        if db_taxid == query_taxid:
            distance = 0
            lca_rank = "species"
            print(f"  ✅ 同一物种")
        else:
            # 获取目标宿主的谱系
            db_lineage = set(ncbi.get_lineage(db_taxid))

            # 找到最近公共祖先 (LCA)
            common_ancestors = query_lineage & db_lineage

            if not common_ancestors:
                distance = 6
                lca_rank = "none"
                print(f"  ⚠️  没有共同祖先")
            else:
                # 获取最近的公共祖先
                lca_taxid = max(common_ancestors)
                lca_rank = ncbi.get_rank([lca_taxid]).get(lca_taxid, "")
                lca_name = ncbi.get_taxid_translator([lca_taxid]).get(lca_taxid, "")

                distance = rank_distance.get(lca_rank, 6)

                print(f"  最近公共祖先 (LCA):")
                print(f"    - TaxID: {lca_taxid}")
                print(f"    - 名称: {lca_name}")
                print(f"    - 等级: {lca_rank}")

        print(f"  分类学距离: {distance} ({distance_names.get(distance, '未知')})")

        # 验证预期
        if distance_names.get(distance, '') == expected or (distance == 0 and expected == "同种"):
            print(f"  ✅ 与预期一致")
        else:
            print(f"  ⚠️  与预期不同 (预期: {expected})")

    except Exception as e:
        print(f"  ❌ 计算失败: {e}")

print("\n" + "="*80)
print("距离定义说明")
print("="*80)
print("""
分类学距离是一个线性量化指标，用于衡量两个物种之间的进化距离：

  0 - 同种 (Same species)
  1 - 同属不同种 (Same genus, different species)
  2 - 同科不同属 (Same family, different genus)
  3 - 同目不同科 (Same order, different family)
  4 - 同纲不同目 (Same class, different order)
  5 - 同门不同纲 (Same phylum, different class)
  6 - 不同门 (Different phylum)
999 - 无法计算 (Cannot calculate)

距离越小，表示两个物种的进化关系越近，共生菌功能的可迁移性越高。
""")

print("="*80)
print("✅ 测试完成")
print("="*80)
