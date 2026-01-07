import sqlite3
import os
import argparse
import sys

# --- 自动路径配置 ---
# 获取当前脚本的绝对路径: ~/01_project/05_iSymPred/iSymPred/isympred/utils/host_query.py
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 根据你的目录结构推导数据库默认路径:
# 脚本在 utils/，数据库在 ../database/host_taxonomy/insect_taxonomy.db
DEFAULT_DB_PATH = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'database', 'host_taxonomy', 'insect_taxonomy.db'))

class InsectTaxonQuery:
    def __init__(self, db_path=None):
        # 如果调用时没传路径，则使用自动推导的默认路径
        self.db_path = db_path if db_path else DEFAULT_DB_PATH

        if not os.path.exists(self.db_path):
            print(f"错误: 数据库文件不存在！")
            print(f"尝试读取路径: {self.db_path}")
            print(f"请检查数据库文件是否已生成，或者通过 -d 参数手动指定。")
            sys.exit(1)

    def get_lineage(self, latin_name):
        """核心查询逻辑：向上溯源获取目、科、属"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 1. 查找起始物种或属的 TaxID
        cursor.execute("SELECT tax_id, parent_id, rank, name FROM taxonomy WHERE name = ?", (latin_name,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return None

        # 定义我们需要提取的阶元
        targets = {"order": "N/A", "family": "N/A", "genus": "N/A"}
        curr_tid, curr_pid, curr_rank, curr_name = row

        # 2. 循环向上追溯直到根节点
        visited = set()
        while curr_tid != 0 and curr_tid not in visited:
            visited.add(curr_tid)

            # 记录匹配到的阶元
            if curr_rank in targets:
                targets[curr_rank] = curr_name

            # 查询父节点信息
            cursor.execute("SELECT tax_id, parent_id, rank, name FROM taxonomy WHERE tax_id = ?", (curr_pid,))
            parent_row = cursor.fetchone()

            if not parent_row:
                break

            curr_tid, curr_pid, curr_rank, curr_name = parent_row

        conn.close()
        return targets

def main():
    parser = argparse.ArgumentParser(description="根据昆虫拉丁名查询目、科、属信息")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-n", "--name", help="单个昆虫拉丁名 (例如: 'Apis mellifera')")
    group.add_argument("-f", "--file", help="包含拉丁名列表的文本文件路径 (每行一个名称)")

    # 将默认值设为上面计算出来的 DEFAULT_DB_PATH
    parser.add_argument("-d", "--db", default=DEFAULT_DB_PATH, help=f"数据库路径 (默认: {DEFAULT_DB_PATH})")

    args = parser.parse_args()

    # 初始化查询器
    querier = InsectTaxonQuery(args.db)

    # 打印表头
    print(f"{'Input_Name':<30} | {'Order':<15} | {'Family':<15} | {'Genus':<15}")
    print("-" * 80)

    # 处理单个查询
    if args.name:
        res = querier.get_lineage(args.name)
        if res:
            print(f"{args.name:<30} | {res['order']:<15} | {res['family']:<15} | {res['genus']:<15}")
        else:
            print(f"{args.name:<30} | 未在数据库(昆虫纲)中找到该名称")

    # 处理批量查询
    elif args.file:
        if not os.path.exists(args.file):
            print(f"错误: 输入列表文件 '{args.file}' 不存在")
            return

        with open(args.file, 'r') as f:
            for line in f:
                name = line.strip()
                if not name: continue
                res = querier.get_lineage(name)
                if res:
                    print(f"{name:<30} | {res['order']:<15} | {res['family']:<15} | {res['genus']:<15}")
                else:
                    print(f"{name:<30} | 未找到")

if __name__ == "__main__":
    main()