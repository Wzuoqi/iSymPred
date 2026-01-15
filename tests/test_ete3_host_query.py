#!/usr/bin/env python3
"""
快速测试 ete3 宿主分类查询功能

测试多个常见昆虫宿主的分类查询
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from ete3 import NCBITaxa
    print("✅ ete3 已安装")
except ImportError:
    print("❌ ete3 未安装")
    print("请运行: pip install ete3")
    sys.exit(1)

# 初始化 NCBITaxa
print("\n初始化 NCBITaxa...")
try:
    ncbi = NCBITaxa()
    print("✅ NCBITaxa 初始化成功")
except Exception as e:
    print(f"❌ NCBITaxa 初始化失败: {e}")
    sys.exit(1)

# 测试物种列表
test_hosts = [
    ("Drosophila melanogaster", "黑腹果蝇"),
    ("Apis mellifera", "西方蜜蜂"),
    ("Bombyx mori", "家蚕"),
    ("Acyrthosiphon pisum", "豌豆蚜虫"),
    ("Tribolium castaneum", "赤拟谷盗"),
]

print("\n" + "="*80)
print("测试宿主分类查询")
print("="*80)

success_count = 0
fail_count = 0

for latin_name, chinese_name in test_hosts:
    print(f"\n测试: {latin_name} ({chinese_name})")
    print("-" * 80)

    try:
        # 查询 taxid
        name2taxid = ncbi.get_name_translator([latin_name])

        if latin_name not in name2taxid:
            print(f"  ❌ 未找到物种: {latin_name}")
            fail_count += 1
            continue

        taxid = name2taxid[latin_name][0]
        print(f"  TaxID: {taxid}")

        # 获取分类谱系
        lineage = ncbi.get_lineage(taxid)
        ranks = ncbi.get_rank(lineage)
        names = ncbi.get_taxid_translator(lineage)

        # 提取目、科、属
        order = family = genus = "N/A"
        for tid in lineage:
            rank = ranks.get(tid, "")
            name = names.get(tid, "")

            if rank == "order":
                order = name
            elif rank == "family":
                family = name
            elif rank == "genus":
                genus = name

        print(f"  Order (目): {order}")
        print(f"  Family (科): {family}")
        print(f"  Genus (属): {genus}")
        print(f"  ✅ 查询成功")
        success_count += 1

    except Exception as e:
        print(f"  ❌ 查询失败: {e}")
        fail_count += 1

# 总结
print("\n" + "="*80)
print("测试总结")
print("="*80)
print(f"成功: {success_count}/{len(test_hosts)}")
print(f"失败: {fail_count}/{len(test_hosts)}")

if fail_count == 0:
    print("\n✅ 所有测试通过！")
    sys.exit(0)
else:
    print(f"\n⚠️  {fail_count} 个测试失败")
    sys.exit(1)
