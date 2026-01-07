import pandas as pd
import numpy as np
import re
import argparse
import sys
import os
import sqlite3
from pathlib import Path

class S16Predictor:
    def __init__(self, db_path, host_db_path=None, user_host=None):
        """
        初始化 16S 预测器

        Args:
            db_path: 共生菌数据库路径 (record_db.tsv)
            host_db_path: 宿主分类数据库路径 (insect_taxonomy.db)，可选
            user_host: 用户提供的宿主拉丁名，可选
        """
        self.db = self._load_database(db_path)
        self.user_host = user_host
        self.host_taxonomy = None

        # 如果提供了宿主信息，尝试查询宿主分类
        if user_host and host_db_path:
            self.host_taxonomy = self._query_host_taxonomy(host_db_path, user_host)

        # === 核心算法参数 ===
        self.WEIGHT_SPECIES = 1.0  # 种级匹配权重
        self.WEIGHT_GENUS = 0.6    # 属级匹配权重
        # 缩放因子：让 log 后的分数变成 0-200 左右的整数，便于阅读
        self.SCORE_SCALING_FACTOR = 100.0

        # === 新增：宿主匹配权重 ===
        self.HOST_MATCH_WEIGHTS = {
            'species': 1.5,   # 物种级精确匹配
            'genus': 1.3,     # 属级匹配
            'family': 1.2,    # 科级匹配
            'order': 1.1,     # 目级匹配
            'general': 1.0    # 通用记录（无宿主特异性）
        }

        # === 新增：证据等级权重 ===
        self.EVIDENCE_LEVEL_WEIGHTS = {
            5: 1.5,  # 最高证据等级（Symbiont + Genome + Top Journal）
            4: 1.3,  # 高证据等级（Symbiont + Genome）
            3: 1.15, # 中等证据等级（Symbiont + Top Journal）
            2: 1.0,  # 基础证据等级（Symbiont only）
            1: 0.8   # 低证据等级
        }

    def _query_host_taxonomy(self, host_db_path, latin_name):
        """
        查询宿主的分类信息（目、科、属）

        Args:
            host_db_path: 宿主分类数据库路径
            latin_name: 宿主拉丁名

        Returns:
            dict: {'order': '...', 'family': '...', 'genus': '...', 'species': '...'}
        """
        if not os.path.exists(host_db_path):
            print(f"[Warning] Host taxonomy database not found: {host_db_path}")
            return None

        try:
            conn = sqlite3.connect(host_db_path)
            cursor = conn.cursor()

            # 查找起始物种
            cursor.execute("SELECT tax_id, parent_id, rank, name FROM taxonomy WHERE name = ?", (latin_name,))
            row = cursor.fetchone()

            if not row:
                conn.close()
                print(f"[Warning] Host '{latin_name}' not found in taxonomy database")
                return None

            # 向上溯源获取目、科、属
            targets = {"order": "N/A", "family": "N/A", "genus": "N/A", "species": latin_name}
            curr_tid, curr_pid, curr_rank, curr_name = row

            visited = set()
            while curr_tid != 0 and curr_tid not in visited:
                visited.add(curr_tid)

                if curr_rank in targets:
                    targets[curr_rank] = curr_name

                cursor.execute("SELECT tax_id, parent_id, rank, name FROM taxonomy WHERE tax_id = ?", (curr_pid,))
                parent_row = cursor.fetchone()

                if not parent_row:
                    break

                curr_tid, curr_pid, curr_rank, curr_name = parent_row

            conn.close()
            print(f"[Host Taxonomy] {latin_name} -> Order: {targets['order']}, Family: {targets['family']}, Genus: {targets['genus']}")
            return targets

        except Exception as e:
            print(f"[Error] Failed to query host taxonomy: {e}")
            return None

    def _calculate_host_match_score(self, db_host, db_host_order, db_host_family):
        """
        计算宿主匹配得分

        Args:
            db_host: 数据库中的宿主物种名
            db_host_order: 数据库中的宿主目
            db_host_family: 数据库中的宿主科

        Returns:
            float: 宿主匹配权重 (0.8-1.5)
        """
        # 如果没有提供用户宿主信息，所有记录权重相同
        if not self.user_host or not self.host_taxonomy:
            return self.HOST_MATCH_WEIGHTS['general']

        db_host = str(db_host).strip().lower()
        db_host_order = str(db_host_order).strip().lower()
        db_host_family = str(db_host_family).strip().lower()

        user_species = self.user_host.lower()
        user_order = self.host_taxonomy.get('order', '').lower()
        user_family = self.host_taxonomy.get('family', '').lower()
        user_genus = self.host_taxonomy.get('genus', '').lower()

        # 1. 物种级精确匹配
        if db_host == user_species or db_host in user_species:
            return self.HOST_MATCH_WEIGHTS['species']

        # 2. 属级匹配（从物种名提取属名）
        if user_genus != 'n/a' and user_genus in db_host:
            return self.HOST_MATCH_WEIGHTS['genus']

        # 3. 科级匹配
        if db_host_family != '*' and db_host_family != 'n/a' and db_host_family == user_family:
            return self.HOST_MATCH_WEIGHTS['family']

        # 4. 目级匹配
        if db_host_order != '*' and db_host_order != 'n/a' and db_host_order == user_order:
            return self.HOST_MATCH_WEIGHTS['order']

        # 5. 通用记录（General）或无匹配
        if db_host == 'general':
            return self.HOST_MATCH_WEIGHTS['general']

        # 6. 完全不匹配（降低权重）
        return 0.8

    def _load_database(self, db_path):
        """加载数据库（包含 evidence_level 字段）"""
        print(f"Loading database from {db_path}...")
        try:
            df = pd.read_csv(db_path, sep='\t')
        except Exception as e:
            print(f"[Error] Failed to load DB: {e}")
            sys.exit(1)

        species_map = {}
        genus_map = {}

        # 确保必要字段存在
        if 'host' not in df.columns: df['host'] = 'General'
        if 'description' not in df.columns: df['description'] = ''
        if 'evidence' not in df.columns: df['evidence'] = ''
        if 'host_order' not in df.columns: df['host_order'] = '*'
        if 'host_family' not in df.columns: df['host_family'] = '*'
        if 'evidence_level' not in df.columns:
            print("[Warning] 'evidence_level' column not found, using default value 2")
            df['evidence_level'] = 2

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

            # 2. 计算基础 Score (基于 RA%)
            # Formula: Weight * log10(RA% + 1) * 100
            log_ra = np.log10(ra_pct + 1)
            base_score = confidence_weight * log_ra * self.SCORE_SCALING_FACTOR

            # 辅助数据
            simple_name = species if match_type == "Species" else f"{genus} (sp.)"

            # === 遍历匹配记录 ===
            unique_funcs_for_summary = set()

            for rec in matched_records:
                func_name = rec['function']
                db_host = str(rec.get('host', 'General'))
                db_host_order = str(rec.get('host_order', '*'))
                db_host_family = str(rec.get('host_family', '*'))
                db_desc = str(rec.get('description', ''))
                db_evidence = str(rec.get('evidence', ''))
                evidence_level = int(rec.get('evidence_level', 2))

                # === 新增：计算宿主匹配权重 ===
                host_match_weight = self._calculate_host_match_score(db_host, db_host_order, db_host_family)

                # === 新增：获取证据等级权重 ===
                evidence_weight = self.EVIDENCE_LEVEL_WEIGHTS.get(evidence_level, 1.0)

                # === 最终得分 = 基础分 × 宿主匹配权重 × 证据等级权重 ===
                final_score = base_score * host_match_weight * evidence_weight

                # 确定宿主匹配等级（用于展示）
                if host_match_weight >= 1.5:
                    host_match_level = "Species"
                elif host_match_weight >= 1.3:
                    host_match_level = "Genus"
                elif host_match_weight >= 1.2:
                    host_match_level = "Family"
                elif host_match_weight >= 1.1:
                    host_match_level = "Order"
                elif host_match_weight >= 1.0:
                    host_match_level = "General"
                else:
                    host_match_level = "Mismatch"

                # --- 填充表 2 (明细表) ---
                potential_symbionts.append({
                    'Symbiont_Taxon': simple_name,
                    'Predicted_Function': func_name,
                    'Final_Score': round(final_score, 1),
                    'Base_Score': round(base_score, 1),
                    'Host_Match_Weight': round(host_match_weight, 2),
                    'Evidence_Level': evidence_level,
                    'Evidence_Weight': round(evidence_weight, 2),
                    'Match_Level': match_type,
                    'Host_Match_Level': host_match_level,
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
                            'weighted_host_sum': 0.0,  # 新增：宿主匹配权重总和
                            'weighted_evidence_sum': 0.0,  # 新增：证据等级权重总和
                            'contributors': []
                        }

                    res = func_results[func_name]
                    res['fps_score'] += final_score
                    res['ra_sum'] += ra_pct
                    res['raw_reads'] += abundance
                    # 使用 RA% 加权计算平均置信度
                    res['weighted_conf_sum'] += (confidence_weight * ra_pct)
                    res['weighted_host_sum'] += (host_match_weight * ra_pct)
                    res['weighted_evidence_sum'] += (evidence_weight * ra_pct)

                    res['contributors'].append({
                        'name': simple_name,
                        'ra': ra_pct,
                        'match_level': match_type,
                        'host_match_level': host_match_level,
                        'evidence_level': evidence_level
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

            # === 新增：平均宿主匹配权重 ===
            avg_host_match = data['weighted_host_sum'] / data['ra_sum'] if data['ra_sum'] > 0 else 1.0

            # === 新增：平均证据等级权重 ===
            avg_evidence_weight = data['weighted_evidence_sum'] / data['ra_sum'] if data['ra_sum'] > 0 else 1.0

            # === 新增：计算功能存在概率 (Probability) ===
            #
            # 设计原则：
            # 1. 保守估计：默认假设功能不存在，需要多重证据支持才能提高概率
            # 2. 瓶颈制：任一关键因素不足都会显著降低概率
            # 3. 区分度：高潜力功能（>0.75）应该稀少，需要满足严格条件
            # 4. 生物学合理性：即使高丰度，缺乏其他证据也不应超过 0.6
            #
            # 概率计算公式：
            # Probability = Base_Prob × min(Confidence_Factor, Host_Factor, Evidence_Factor) × Taxa_Factor
            #
            # 核心思想：使用 min() 实现"木桶效应"，任一短板都会限制最终概率

            import math
            ra_pct = data['ra_sum']

            # ========================================
            # 步骤 1: 基础概率 (Base_Prob) - 更保守的 Sigmoid
            # ========================================
            # 新参数：k=0.2 (更平缓), x0=15 (中点右移)
            # 效果：
            #   RA=5%  -> 0.18 (低)
            #   RA=10% -> 0.27 (中低)
            #   RA=15% -> 0.50 (中等)
            #   RA=25% -> 0.82 (高)
            #   RA=35% -> 0.95 (极高)
            base_prob = 1 / (1 + math.exp(-0.2 * (ra_pct - 15)))

            # ========================================
            # 步骤 2: 置信度因子 (Confidence_Factor) - 惩罚属级匹配
            # ========================================
            # 种级匹配 (1.0) -> 1.0 (无惩罚)
            # 属级匹配 (0.6) -> 0.7 (显著惩罚)
            if avg_confidence >= 0.9:  # 种级或接近种级
                confidence_factor = 1.0
            elif avg_confidence >= 0.7:  # 中等置信度
                confidence_factor = 0.85
            else:  # 属级匹配
                confidence_factor = 0.70

            # ========================================
            # 步骤 3: 宿主匹配因子 (Host_Factor) - 严格惩罚不匹配
            # ========================================
            # 物种级匹配 (1.5) -> 1.0 (最佳)
            # 属级匹配 (1.3) -> 0.95
            # 科级匹配 (1.2) -> 0.90
            # 目级匹配 (1.1) -> 0.85
            # 通用记录 (1.0) -> 0.75 (显著惩罚)
            # 不匹配 (0.8) -> 0.50 (严重惩罚)
            if avg_host_match >= 1.4:  # 物种级
                host_factor = 1.0
            elif avg_host_match >= 1.25:  # 属级
                host_factor = 0.95
            elif avg_host_match >= 1.15:  # 科级
                host_factor = 0.90
            elif avg_host_match >= 1.05:  # 目级
                host_factor = 0.85
            elif avg_host_match >= 0.95:  # 通用记录
                host_factor = 0.75
            else:  # 不匹配
                host_factor = 0.50

            # ========================================
            # 步骤 4: 证据质量因子 (Evidence_Factor) - 奖励高质量证据
            # ========================================
            # Evidence Level 5 (1.5) -> 1.0 (最佳)
            # Evidence Level 4 (1.3) -> 0.95
            # Evidence Level 3 (1.15) -> 0.85
            # Evidence Level 2 (1.0) -> 0.75 (基础惩罚)
            # Evidence Level 1 (0.8) -> 0.60 (显著惩罚)
            if avg_evidence_weight >= 1.4:  # Level 5
                evidence_factor = 1.0
            elif avg_evidence_weight >= 1.25:  # Level 4
                evidence_factor = 0.95
            elif avg_evidence_weight >= 1.1:  # Level 3
                evidence_factor = 0.85
            elif avg_evidence_weight >= 0.95:  # Level 2
                evidence_factor = 0.75
            else:  # Level 1
                evidence_factor = 0.60

            # ========================================
            # 步骤 5: 分类单元数量因子 (Taxa_Factor) - 温和奖励
            # ========================================
            # 多个分类单元支持提升可信度，但影响有限
            # Taxa=1   -> 0.90 (单一证据惩罚)
            # Taxa=5   -> 0.95
            # Taxa=10  -> 1.00
            # Taxa=50  -> 1.05
            # Taxa=100 -> 1.08
            if taxa_count == 1:
                taxa_factor = 0.90  # 单一分类单元惩罚
            elif taxa_count <= 5:
                taxa_factor = 0.90 + (taxa_count - 1) * 0.0125  # 0.90 -> 0.95
            elif taxa_count <= 20:
                taxa_factor = 0.95 + ((taxa_count - 5) / 15) * 0.05  # 0.95 -> 1.00
            else:
                taxa_factor = 1.0 + (math.log10(taxa_count / 20) * 0.05)  # 1.00 -> 1.08
                taxa_factor = min(taxa_factor, 1.08)  # 上限 1.08

            # ========================================
            # 最终概率计算：木桶效应 + 分类单元调整
            # ========================================
            # 使用 min() 确保任一短板都会限制最终概率
            bottleneck_factor = min(confidence_factor, host_factor, evidence_factor)
            probability = base_prob * bottleneck_factor * taxa_factor

            # 限制在 0-1 范围内，并设置实际上限为 0.95
            # (即使所有条件完美，也保留 5% 的不确定性)
            probability = max(0.0, min(0.95, probability))

            func_rows.append({
                'Function': func,
                'Final_Score_Sum': round(data['fps_score'], 1),  # 最终总分（整合所有权重）
                'Total_RA_Pct': round(data['ra_sum'], 3),        # 该功能的总丰度
                'Mean_Confidence': round(avg_confidence, 2),
                'Mean_Host_Match': round(avg_host_match, 2),     # 新增
                'Mean_Evidence_Weight': round(avg_evidence_weight, 2),  # 新增
                'Taxa_Count': taxa_count,
                'Probability': round(probability, 3),             # 新增：功能存在概率
                'Dominant_Contributor': top_contributor_str
            })

        func_df = pd.DataFrame(func_rows)
        if not func_df.empty:
            func_df = func_df.sort_values('Final_Score_Sum', ascending=False)

        # 修改输出文件名：使用 _functions.tsv 后缀
        base, ext = os.path.splitext(output_path)
        if not base.endswith('_functions'):
            functions_output_path = f"{base}_functions{ext}"
        else:
            functions_output_path = output_path

        func_df.to_csv(functions_output_path, sep='\t', index=False)
        print(f"Function summary saved to: {functions_output_path}")

        # ==========================================
        # 输出表格 2: 潜在功能共生菌明细 (Detailed Potential)
        # ==========================================
        base, ext = os.path.splitext(output_path)
        taxa_output_path = f"{base}_potential_symbionts{ext}"

        taxa_df = pd.DataFrame(potential_symbionts)

        if not taxa_df.empty:
            # 排序：先看最终分数，再看丰度
            taxa_df = taxa_df.sort_values(['Final_Score', 'Relative_Abundance_Pct'], ascending=[False, False])

            cols = ['Symbiont_Taxon', 'Predicted_Function', 'Final_Score', 'Base_Score',
                    'Host_Match_Weight', 'Host_Match_Level', 'Evidence_Level', 'Evidence_Weight',
                    'Match_Level', 'Relative_Abundance_Pct', 'DB_Host_Context',
                    'DB_Description', 'DB_Evidence']
            taxa_df = taxa_df[cols]

            taxa_df.to_csv(taxa_output_path, sep='\t', index=False)
            print(f"Potential symbiont list saved to: {taxa_output_path}")
        else:
            print("No potential symbionts matched.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="16S rRNA-based symbiont function prediction with host-context scoring"
    )
    parser.add_argument('-i', '--input', required=True, help="Input OTU table (TSV format)")
    parser.add_argument('-d', '--db', required=True, help="Symbiont database TSV (record_db.tsv)")
    parser.add_argument('-o', '--output', required=True, help="Output file path")
    parser.add_argument('--host', help="Host species Latin name (e.g., 'Apis mellifera')")
    parser.add_argument('--host-db', help="Host taxonomy database path (insect_taxonomy.db)")
    args = parser.parse_args()

    # 自动推导宿主数据库路径（如果未指定）
    if args.host and not args.host_db:
        script_dir = Path(__file__).parent
        default_host_db = script_dir.parent / 'database' / 'host_taxonomy' / 'insect_taxonomy.db'
        if default_host_db.exists():
            args.host_db = str(default_host_db)
            print(f"[Info] Using default host database: {args.host_db}")
        else:
            print(f"[Warning] Host specified but host database not found at {default_host_db}")
            print("[Warning] Proceeding without host-context scoring")

    predictor = S16Predictor(args.db, host_db_path=args.host_db, user_host=args.host)
    predictor.predict(args.input, args.output)