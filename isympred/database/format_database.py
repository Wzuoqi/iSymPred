import pandas as pd
import argparse
import sys
import os
import re
import csv
from io import StringIO

def construct_qiime_taxonomy(row):
    """
    构建 QIIME 2 / SILVA 标准格式的 Taxonomy 字符串。
    格式: d__Dom; p__Phy; c__Cls; o__Ord; f__Fam; g__Gen; s__Sp
    """
    def get_clean_val(val):
        if pd.isna(val) or str(val).lower() in ['none', 'nan', '', 'unknown', 'null']:
            return '*'
        return str(val).strip()

    domain = get_clean_val(row.get('symbiont_domain'))
    if domain == '*' and row.get('symbiont_phylum') != 'None':
         domain = 'Bacteria'

    phylum = get_clean_val(row.get('symbiont_phylum'))
    order = get_clean_val(row.get('symbiont_order'))
    genus = get_clean_val(row.get('symbiont_genus'))
    cls = '*'
    family = '*'

    species = '*'
    raw_name = str(row.get('symbiont_name', ''))

    if genus != '*' and pd.notna(raw_name) and raw_name.lower() != 'none':
        parts = raw_name.split()
        if len(parts) >= 2:
            pot_genus = parts[0]
            pot_species = parts[1]
            pot_genus_clean = re.sub(r'[^a-zA-Z\-_]', '', pot_genus)
            pot_species_clean = re.sub(r'[^a-zA-Z\-_]', '', pot_species)

            if (pot_genus_clean.lower() == genus.lower()) and \
               ('sp' not in pot_species_clean.lower()):
                species = f"{genus} {pot_species_clean}"

    taxonomy_str = (
        f"d__{domain}; p__{phylum}; c__{cls}; o__{order}; "
        f"f__{family}; g__{genus}; s__{species}"
    )
    return taxonomy_str

def pre_clean_data(filepath):
    """
    [核心修复] 预清洗数据：
    1. 统一列数：以第一行(表头)的列数为准，截断多余的列 (修复 Line 1625 错误)
    2. 禁用引号：将所有内容视为纯文本 (修复 Line 2386 错误)
    """
    print("Pre-cleaning data to handle format errors...")
    clean_lines = []
    expected_cols = 0

    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            # 读取所有行
            lines = f.readlines()

        if not lines:
            return None

        # 处理表头
        header = lines[0].strip().split('\t')
        expected_cols = len(header)
        clean_lines.append("\t".join(header))

        # 处理数据行
        for i, line in enumerate(lines[1:], start=2):
            # 去除换行符，按制表符分割
            parts = line.rstrip('\n').split('\t')

            # 情况 A: 列数正好
            if len(parts) == expected_cols:
                clean_lines.append("\t".join(parts))

            # 情况 B: 列数过多 (比如 Line 1625 的那个问号) -> 截断
            elif len(parts) > expected_cols:
                # print(f"Warning: Line {i} has {len(parts)} columns. Truncating to {expected_cols}.")
                clean_lines.append("\t".join(parts[:expected_cols]))

            # 情况 C: 列数不足 -> 补全 (可选，防止报错)
            elif len(parts) < expected_cols:
                # print(f"Warning: Line {i} has {len(parts)} columns. Padding.")
                parts.extend([''] * (expected_cols - len(parts)))
                clean_lines.append("\t".join(parts))

        # 将清洗后的字符串列表转为 Pandas 可读的 StringIO 对象
        return StringIO('\n'.join(clean_lines))

    except Exception as e:
        print(f"Pre-cleaning failed: {e}")
        return None

def format_symbiont_data(input_path, output_path):
    print(f"Loading data from {input_path}...")

    # ==========================================
    # 1. 读取数据 (使用预清洗逻辑)
    # ==========================================
    try:
        if str(input_path).endswith('.xlsx'):
            df = pd.read_excel(input_path)
        else:
            # 先进行清洗
            cleaned_data = pre_clean_data(input_path)
            if cleaned_data is None:
                raise ValueError("Data cleaning returned empty result")

            # 读取清洗后的数据
            # quoting=3 (csv.QUOTE_NONE) 是关键！它彻底禁用了引号解析，修复 Line 2386
            df = pd.read_csv(
                cleaned_data,
                sep='\t',
                quoting=csv.QUOTE_NONE,
                engine='python'
            )

    except Exception as e:
        print(f"[CRITICAL FAIL] Could not read file: {e}")
        sys.exit(1)

    print(f"Successfully loaded {len(df)} lines.")

    # ==========================================
    # 2. 列名映射
    # ==========================================
    df.columns = df.columns.str.strip()

    col_mapping = {
        'record_type': ['Record Type', 'Record_Type'],
        'symbiont_domain': ['Classification', 'Domain', 'Kingdom'],
        'symbiont_phylum': ['Symbiont Phylum', 'Symbiont_Phylum'],
        'symbiont_order': ['Symbiont Order', 'Symbiont_Order'],
        'symbiont_genus': ['Symbiont Genus', 'Symbiont_Genus', 'Genus'],
        'symbiont_name': ['Symbiont Name', 'Symbiont_Name', 'Species'],
        'host_order': ['Order', 'Host Order'],
        'host_family': ['Family', 'Host Family'],
        'host_species': ['Insect Species', 'Insect_Species', 'Host'],
        'function_tags': ['Function Tag', 'Function_Tag'],
        'function_desc': ['Function', 'Function Description', 'Description'],
        'doi': ['doi', 'DOI', 'Doi']
    }

    rename_dict = {}
    actual_cols = df.columns
    for standard, variants in col_mapping.items():
        for var in variants:
            if var in actual_cols:
                rename_dict[var] = standard
                break

    df = df.rename(columns=rename_dict)

    if 'symbiont_genus' not in df.columns:
        print("[ERROR] Missing 'Symbiont Genus' column.")
        sys.exit(1)

    # ==========================================
    # 3. 数据清洗
    # ==========================================
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].str.strip()

    if 'record_type' in df.columns:
        # 大小写不敏感匹配
        df = df[df['record_type'].astype(str).str.lower() == 'symbiont']

    df = df[df['symbiont_genus'].notna()]
    df = df[~df['symbiont_genus'].isin(['None', 'none', '', 'nan'])]

    expected_cols = ['symbiont_domain', 'symbiont_phylum', 'symbiont_order', 'symbiont_name']
    for c in expected_cols:
        if c not in df.columns: df[c] = 'Unknown'

    # ==========================================
    # 4. 生成 Taxonomy
    # ==========================================
    print("Constructing QIIME 2 standard taxonomy strings...")
    df['taxonomy'] = df.apply(construct_qiime_taxonomy, axis=1)
    df = df[df['taxonomy'].notna()]

    # ==========================================
    # 5. Explode
    # ==========================================
    if 'function_tags' in df.columns:
        df['function_tags'] = df['function_tags'].astype(str).apply(lambda x: x.split(','))
        df = df.explode('function_tags')
        df['function_tags'] = df['function_tags'].str.strip()
        df = df[~df['function_tags'].str.lower().isin(['none', 'nan', '', 'null'])]

    # ==========================================
    # 6. 输出
    # ==========================================
    if 'host_species' not in df.columns: df['host_species'] = 'General'
    if 'function_desc' not in df.columns: df['function_desc'] = ''
    if 'doi' not in df.columns: df['doi'] = ''

    for col in ['symbiont_phylum', 'symbiont_order', 'symbiont_genus', 'host_order', 'host_family']:
        if col not in df.columns: df[col] = '*'

    final_cols = [
        'taxonomy',
        'host_species',
        'function_tags',
        'symbiont_phylum',
        'symbiont_order',
        'symbiont_genus',
        'host_order',
        'host_family',
        'function_desc',
        'doi'
    ]

    output_rename = {
        'host_species': 'host',
        'function_tags': 'function',
        'function_desc': 'description',
        'doi': 'evidence'
    }

    final_df = df[[c for c in final_cols if c in df.columns]].copy()
    final_df = final_df.rename(columns=output_rename)
    final_df = final_df.drop_duplicates()

    try:
        final_df.to_csv(output_path, sep='\t', index=False)
        print(f"SUCCESS! Saved {len(final_df)} formatted records.")
        print(f"File path: {output_path}")
        print("\n[Preview First Row Taxonomy]:")
        try:
            print(final_df.iloc[0]['taxonomy'])
        except:
            pass

    except Exception as e:
        print(f"[ERROR] Failed to write file: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True)
    parser.add_argument('-o', '--output', required=True)
    args = parser.parse_args()

    format_symbiont_data(args.input, args.output)