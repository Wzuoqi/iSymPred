import sqlite3
import collections
import os
import sys

# --- 1. 构建数据库的函数 ---
def build_insect_db(nodes_file, names_file, db_file):
    if not os.path.exists(nodes_file) or not os.path.exists(names_file):
        print(f"Error: {nodes_file} or {names_file} not found!")
        sys.exit(1)

    print("Step 1: Loading nodes structure (this may take about 30s)...")
    child_to_parent = {}
    with open(nodes_file, 'r') as f:
        for line in f:
            parts = line.split('|')
            tid = int(parts[0].strip())
            pid = int(parts[1].strip())
            rank = parts[2].strip()
            child_to_parent[tid] = (pid, rank)

    print("Step 2: Filtering Insecta subtree (TaxID: 50557)...")
    insecta_id = 50557
    if insecta_id not in child_to_parent:
        print("Error: Insecta TaxID 50557 not found in nodes.dmp!")
        return

    # 建立父子关系索引
    parent_to_children = collections.defaultdict(list)
    for tid, (pid, rank) in child_to_parent.items():
        parent_to_children[pid].append(tid)

    # 找所有子节点
    insect_ids = {insecta_id}
    queue = [insecta_id]
    while queue:
        curr = queue.pop(0)
        if curr in parent_to_children:
            children = parent_to_children[curr]
            insect_ids.update(children)
            queue.extend(children)

    print(f"Found {len(insect_ids)} insect-related TaxIDs.")

    print("Step 3: Reading names and building SQLite database...")
    # 如果存在 0 字节文件，先删除
    if os.path.exists(db_file):
        os.remove(db_file)

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS taxonomy')
    cursor.execute('''CREATE TABLE taxonomy (
                        tax_id INTEGER PRIMARY KEY,
                        parent_id INTEGER,
                        rank TEXT,
                        name TEXT)''')

    insert_data = []
    with open(names_file, 'r') as f:
        for line in f:
            if 'scientific name' in line:
                parts = line.split('|')
                tid = int(parts[0].strip())
                if tid in insect_ids:
                    name = parts[1].strip()
                    pid, rank = child_to_parent.get(tid, (0, ''))
                    insert_data.append((tid, pid, rank, name))
                    if len(insert_data) > 50000:
                        cursor.executemany('INSERT INTO taxonomy VALUES (?,?,?,?)', insert_data)
                        insert_data = []

    cursor.executemany('INSERT INTO taxonomy VALUES (?,?,?,?)', insert_data)
    cursor.execute('CREATE INDEX idx_name ON taxonomy(name)')
    conn.commit()
    conn.close()
    print(f"Database {db_file} built successfully! File size: {os.path.getsize(db_file)/1024/1024:.2f} MB")

# --- 2. 查询类 ---
class InsectTaxonomy:
    def __init__(self, db_path):
        self.db_path = db_path

    def get_info(self, latin_name):
        if not os.path.exists(self.db_path):
            return None
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT tax_id, parent_id, rank, name FROM taxonomy WHERE name = ?", (latin_name,))
            row = cursor.fetchone()
            if not row:
                return None

            res = {"order": None, "family": None, "genus": None}
            curr_tid, curr_pid, curr_rank, curr_name = row
            # 向上溯源
            while curr_tid != 0:
                if curr_rank in res:
                    res[curr_rank] = curr_name
                cursor.execute("SELECT tax_id, parent_id, rank, name FROM taxonomy WHERE tax_id = ?", (curr_pid,))
                parent_row = cursor.fetchone()
                if not parent_row: break
                curr_tid, curr_pid, curr_rank, curr_name = parent_row
            return res
        except sqlite3.OperationalError:
            return None
        finally:
            conn.close()

# --- 3. 执行逻辑 ---
if __name__ == "__main__":
    db_name = 'insect_taxonomy.db'

    # 修改逻辑：如果文件不存在 OR 文件大小为 0，则构建
    if not os.path.exists(db_name) or os.path.getsize(db_name) == 0:
        build_insect_db('nodes.dmp', 'names.dmp', db_name)

    # 验证数据库是否建立成功
    if os.path.exists(db_name) and os.path.getsize(db_name) > 0:
        itax = InsectTaxonomy(db_name)
        test_list = ["Apis mellifera", "Drosophila melanogaster", "Harmonia axyridis"]

        print(f"\n{'Name':<25} | {'Order':<15} | {'Family':<15} | {'Genus':<15}")
        print("-" * 75)
        for name in test_list:
            info = itax.get_info(name)
            if info:
                print(f"{name:<25} | {str(info['order']):<15} | {str(info['family']):<15} | {str(info['genus']):<15}")
            else:
                print(f"{name:<25} | Not Found")
    else:
        print("Error: Database construction failed.")