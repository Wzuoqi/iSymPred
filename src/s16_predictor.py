import pandas as pd
import numpy as np
import re
import argparse
import sys
import os

class S16Predictor:
    def __init__(self, db_path):
        self.db = self._load_database(db_path)
        # === 核心算法参数 ===
        self.WEIGHT_SPECIES = 1.0  # 种级匹配权重
        self.WEIGHT_GENUS = 0.6    # 属级匹配权重
        # 缩放因子：让 log 后的分数变成 0-200 左右的整数，便于阅读
        self.SCORE_SCALING_FACTOR = 100.0

    def _load_database(self, db_path):
        """加载数据库"""
        print(f"Loading database from {db_path}...")
        try:
            df = pd.read_csv(db_path, sep='\t')
        except Exception as e:
            print(f"[Error] Failed to load DB: {e}")
            sys.exit(1)

        species_map = {}
        genus_map = {}

        if 'host' not in df.columns: df['host'] = 'General'
        if 'description' not in df.columns: df['description'] = ''
        if 'evidence' not in df.columns: df['evidence'] = ''

        for _, row in df.iterrows():
            raw_tax = str(row.get('taxonomy', ''))
            g_match = re.search(r'g__([^;]+)', raw_tax)
            s_match = re.search(r's__([^;]+)', raw_tax)

            genus = g_match.group(1).strip() if g_match else None
            species = s_match.group(1).strip() if s_match else None

            if not genus or genus == '*': continue

            # 存入字典
            if genus not in genus_map: genus_map[genus] = []
            genus_map[genus].append(row)

            if species and species != '*' and 'unclassified' not in species.lower():
                full_name = species if genus in species else f"{genus} {species}"
                if full_name not in species_map: species_map[full_name] = []
                species_map[full_name].append(row)

        print(f"Database loaded: {len(species_map)} species keys, {len(genus_map)} genus keys.")
        return {'species': species_map, 'genus': genus_map}

    def _parse_input_taxon(self, taxon_str):
        """解析输入 OTU 的分类字符串"""
        g_match = re.search(r'g__([^;]+)', taxon_str)
        s_match = re.search(r's__([^;]+)', taxon_str)

        genus = g_match.group(1).strip() if g_match else None
        species_raw = s_match.group(1).strip() if s_match else None

        species = None
        invalid_species = ['unclassified', 'unknown', 'none', '*', 'sp.', 'sp']
        if genus and species_raw:
            is_valid = not any(x in species_raw.lower() for x in invalid_species)
            if is_valid:
                species = species_raw if genus in species_raw else f"{genus} {species_raw}"

        return genus, species

    def predict(self, input_table_path, output_path):
        print(f"Reading input OTU table from {input_table_path}...")
        input_df = pd.read_csv(input_table_path, sep='\t')

        if 'Abundance' not in input_df.columns:
            input_df.rename(columns={input_df.columns[1]: 'Abundance'}, inplace=True)

        total_reads = input_df['Abundance'].sum()
        print(f"Total Reads in Sample: {total_reads}")

        if total_reads == 0:
            print("[Error] Total reads is 0. Exiting.")
            sys.exit(1)

        # === 容器 ===
        func_results = {}
        potential_symbionts = []

        for _, row in input_df.iterrows():
            taxon = row['Taxon']
            abundance = float(row['Abundance'])

            if abundance <= 0: continue

            genus, species = self._parse_input_taxon(taxon)
            if not genus: continue

            matched_records = []
            confidence_weight = 0.0
            match_type = ""

            # === 匹配逻辑 ===
            if species and species in self.db['species']:
                matched_records = self.db['species'][species]
                confidence_weight = self.WEIGHT_SPECIES
                match_type = "Species"
            elif genus in self.db['genus']:
                matched_records = self.db['genus'][genus]
                confidence_weight = self.WEIGHT_GENUS
                match_type = "Genus"

            if not matched_records: continue

            # === [Updated] 计算相对丰度和得分 ===
            # 1. 计算 RA% (0-100)
            ra_pct = (abundance / total_reads) * 100

            # 2. 计算 Score (基于 RA%)
            # Formula: Weight * log10(RA% + 1) * 100
            log_ra = np.log10(ra_pct + 1)
            contribution_score = confidence_weight * log_ra * self.SCORE_SCALING_FACTOR

            # 辅助数据
            simple_name = species if match_type == "Species" else f"{genus} (sp.)"

            # === 遍历匹配记录 ===
            unique_funcs_for_summary = set()

            for rec in matched_records:
                func_name = rec['function']
                db_host = str(rec.get('host', 'General'))
                db_desc = str(rec.get('description', ''))
                db_evidence = str(rec.get('evidence', ''))

                # --- 填充表 2 (明细表) ---
                potential_symbionts.append({
                    'Symbiont_Taxon': simple_name,
                    'Predicted_Function': func_name,
                    'Potential_Score': round(contribution_score, 1), # 保留1位小数
                    'Match_Level': match_type,
                    'Relative_Abundance_Pct': round(ra_pct, 4),
                    'DB_Host_Context': db_host,
                    'DB_Description': db_desc[:100] + '...' if len(db_desc) > 100 else db_desc,
                    'DB_Evidence': db_evidence
                })

                # --- 填充表 1 (汇总表) ---
                if func_name not in unique_funcs_for_summary:
                    unique_funcs_for_summary.add(func_name)

                    if func_name not in func_results:
                        func_results[func_name] = {
                            'fps_score': 0.0,
                            'ra_sum': 0.0,      # RA% 总和
                            'raw_reads': 0,
                            'weighted_conf_sum': 0.0,
                            'contributors': []
                        }

                    res = func_results[func_name]
                    res['fps_score'] += contribution_score
                    res['ra_sum'] += ra_pct
                    res['raw_reads'] += abundance
                    # 使用 RA% 加权计算平均置信度
                    res['weighted_conf_sum'] += (confidence_weight * ra_pct)

                    res['contributors'].append({
                        'name': simple_name,
                        'ra': ra_pct,
                        'match_level': match_type
                    })

        # ==========================================
        # 输出表格 1: 功能预测表 (Function Summary)
        # ==========================================
        func_rows = []
        for func, data in func_results.items():
            taxa_count = len(data['contributors'])
            # 按 RA% 排序寻找最主要贡献者
            sorted_contributors = sorted(data['contributors'], key=lambda x: x['ra'], reverse=True)

            if sorted_contributors:
                top = sorted_contributors[0]
                # 计算其在贡献此功能的 RA 总量中的占比
                func_ra_total = data['ra_sum']
                contrib_share = (top['ra'] / func_ra_total) * 100 if func_ra_total > 0 else 0

                # 显示: Taxon (Share of function)
                # 例如: Acinetobacter (90.5% of func)
                top_contributor_str = f"{top['name']} ({contrib_share:.1f}% contribution)"
            else:
                top_contributor_str = "None"

            # 平均置信度
            avg_confidence = data['weighted_conf_sum'] / data['ra_sum'] if data['ra_sum'] > 0 else 0

            func_rows.append({
                'Function': func,
                'Potential_Score_Sum': round(data['fps_score'], 1), # 总分
                'Total_RA_Pct': round(data['ra_sum'], 3),           # 该功能的总丰度
                'Mean_Confidence': round(avg_confidence, 2),
                'Taxa_Count': taxa_count,
                'Dominant_Contributor': top_contributor_str
            })

        func_df = pd.DataFrame(func_rows)
        if not func_df.empty:
            func_df = func_df.sort_values('Potential_Score_Sum', ascending=False)
        func_df.to_csv(output_path, sep='\t', index=False)
        print(f"Function summary saved to: {output_path}")

        # ==========================================
        # 输出表格 2: 潜在功能共生菌明细 (Detailed Potential)
        # ==========================================
        base, ext = os.path.splitext(output_path)
        taxa_output_path = f"{base}_potential_symbionts{ext}"

        taxa_df = pd.DataFrame(potential_symbionts)

        if not taxa_df.empty:
            # 排序：先看分，再看丰度
            taxa_df = taxa_df.sort_values(['Potential_Score', 'Relative_Abundance_Pct'], ascending=[False, False])

            cols = ['Symbiont_Taxon', 'Predicted_Function', 'Potential_Score',
                    'Match_Level', 'Relative_Abundance_Pct', 'DB_Host_Context',
                    'DB_Description', 'DB_Evidence']
            taxa_df = taxa_df[cols]

            taxa_df.to_csv(taxa_output_path, sep='\t', index=False)
            print(f"Potential symbiont list saved to: {taxa_output_path}")
        else:
            print("No potential symbionts matched.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, help="Input OTU table")
    parser.add_argument('-d', '--db', required=True, help="Database TSV")
    parser.add_argument('-o', '--output', required=True, help="Output file")
    args = parser.parse_args()

    predictor = S16Predictor(args.db)
    predictor.predict(args.input, args.output)