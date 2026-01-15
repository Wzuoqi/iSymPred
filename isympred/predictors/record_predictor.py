import pandas as pd
import numpy as np
import re
import argparse
import sys
import os
from pathlib import Path

# 使用 ete3 进行分类查询（替代本地 SQLite 数据库）
try:
    from ete3 import NCBITaxa
    NCBI_TAXA_AVAILABLE = True
except ImportError:
    NCBI_TAXA_AVAILABLE = False
    print("[Warning] ete3 not installed. Host taxonomy query will be disabled.")
    print("[Info] Install with: pip install ete3")

class RecordPredictor:
    """
    共生菌功能预测器

    支持模糊匹配：自动清理分类名中的细致分类后缀
    例如：s__Akkermansia muciniphila_D_776786 -> Akkermansia muciniphila
    """

    # 用于清理分类名后缀的正则表达式模式
    # 匹配模式：_[大写字母]_[数字] 或 _[数字] 结尾的后缀
    # 例如：_D_776786, _A_123456, _12345
    TAXONOMY_SUFFIX_PATTERN = re.compile(r'_[A-Z]_\d+$|_\d+$')

    def __init__(self, db_path, host_db_path=None, user_host=None, leaf_only=False):
        """
        初始化共生菌记录预测器

        Args:
            db_path: 共生菌数据库路径 (record_db.tsv)
            host_db_path: [已废弃] 保留参数以保持向后兼容，现使用 ete3 查询 NCBI Taxonomy
            user_host: 用户提供的宿主拉丁名，可选
            leaf_only: 是否仅输出叶子功能（最具体的子功能），默认 False
        """
        self.db = self._load_database(db_path)
        self.user_host = user_host
        self.host_taxonomy = None
        self.leaf_only = leaf_only

        # === CLR 转换相关参数 ===
        # 用于存储样本级别的 CLR 转换结果
        self.clr_values = None
        self.geometric_mean = None

        # === 加载功能层级关系 ===
        # 从 function_tag.tsv 加载 Parent 和 Parent Category 信息
        db_dir = Path(db_path).parent
        function_tag_path = db_dir / 'function_tag.tsv'
        self.func_hierarchy = self._load_function_hierarchy(function_tag_path)

        # 初始化 NCBI Taxonomy 查询工具
        self.ncbi = None
        if NCBI_TAXA_AVAILABLE:
            try:
                self.ncbi = NCBITaxa()
                print("[Info] Using ete3 NCBITaxa for host taxonomy queries")
            except Exception as e:
                print(f"[Warning] Failed to initialize NCBITaxa: {e}")
                self.ncbi = None

        # 如果提供了宿主信息，尝试查询宿主分类
        if user_host:
            self.host_taxonomy = self._query_host_taxonomy_ete3(user_host)

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

    def _clean_taxonomy_name(self, name):
        """
        清理分类名，移除细致分类后缀（模糊匹配）

        处理模式：
        1. _[大写字母]_[数字] 后缀，如 _D_776786, _A_123456
        2. _[数字] 后缀，如 _12345
        3. 多个连续的此类后缀

        示例：
        - Akkermansia muciniphila_D_776786 -> Akkermansia muciniphila
        - Bacteroides_A_123 -> Bacteroides
        - Lactobacillus_12345 -> Lactobacillus
        - Genus species_A_1_B_2 -> Genus species

        Args:
            name: 原始分类名

        Returns:
            str: 清理后的分类名
        """
        if not name or not isinstance(name, str):
            return name

        # 循环移除所有匹配的后缀（处理多个连续后缀的情况）
        cleaned = name.strip()
        while True:
            new_cleaned = self.TAXONOMY_SUFFIX_PATTERN.sub('', cleaned)
            if new_cleaned == cleaned:
                break
            cleaned = new_cleaned

        return cleaned.strip()

    def _load_function_hierarchy(self, hierarchy_file):
        """
        加载 function_tag.tsv 中的功能层级关系

        Args:
            hierarchy_file: function_tag.tsv 文件路径

        Returns:
            dict: {
                'parent_map': {function: parent},
                'category_map': {function: parent_category},
                'children_map': {function: [children]},
                'level_map': {function: hierarchy_level}
            }
        """
        parent_map = {}
        category_map = {}
        children_map = {}
        level_map = {}

        if not Path(hierarchy_file).exists():
            print(f"[Warning] Function hierarchy file not found: {hierarchy_file}")
            print("[Warning] Hierarchy features will be disabled")
            return {
                'parent_map': parent_map,
                'category_map': category_map,
                'children_map': children_map,
                'level_map': level_map
            }

        try:
            df = pd.read_csv(hierarchy_file, sep='\t')
            print(f"[Info] Loading function hierarchy from {hierarchy_file}")

            # 检查必要的列
            if 'Function Tag' not in df.columns:
                print(f"[Warning] 'Function Tag' column not found in {hierarchy_file}")
                return {
                    'parent_map': parent_map,
                    'category_map': category_map,
                    'children_map': children_map,
                    'level_map': level_map
                }

            for _, row in df.iterrows():
                func = str(row['Function Tag']).strip()
                parent = str(row.get('Parent', 'None')).strip()
                category = str(row.get('Parent Category', 'Other')).strip()

                # 处理 'None' 字符串
                if parent.lower() == 'none' or parent == '':
                    parent = None

                parent_map[func] = parent
                category_map[func] = category

                # 构建子功能映射
                if parent:
                    if parent not in children_map:
                        children_map[parent] = []
                    children_map[parent].append(func)

            # 计算层级深度
            for func in parent_map:
                level = 1
                current = parent_map.get(func)
                visited = set()  # 防止循环引用
                while current and current not in visited:
                    visited.add(current)
                    level += 1
                    current = parent_map.get(current)
                level_map[func] = level

            # 统计信息
            top_level_count = sum(1 for p in parent_map.values() if p is None)
            max_depth = max(level_map.values()) if level_map else 0
            print(f"[Info] Function hierarchy loaded: {len(parent_map)} functions, "
                  f"{top_level_count} top-level, max depth {max_depth}")

        except Exception as e:
            print(f"[Error] Failed to load function hierarchy: {e}")

        return {
            'parent_map': parent_map,
            'category_map': category_map,
            'children_map': children_map,
            'level_map': level_map
        }

    def _get_hierarchy_level(self, func):
        """获取功能的层级深度"""
        return self.func_hierarchy['level_map'].get(func, 1)

    def _get_parent(self, func):
        """获取功能的父功能"""
        return self.func_hierarchy['parent_map'].get(func)

    def _get_category(self, func):
        """获取功能的大类"""
        return self.func_hierarchy['category_map'].get(func, 'Unknown')

    def _get_children(self, func):
        """获取功能的子功能列表"""
        return self.func_hierarchy['children_map'].get(func, [])

    def _identify_leaf_functions(self, predicted_functions):
        """
        识别当前预测结果中的叶子功能

        Args:
            predicted_functions: 预测到的功能集合

        Returns:
            set: 叶子功能集合（在当前预测中没有子功能被预测到的功能）
        """
        leaf_functions = set()
        children_map = self.func_hierarchy['children_map']

        for func in predicted_functions:
            children = children_map.get(func, [])
            # 检查是否有任何子功能出现在预测结果中
            has_predicted_child = any(child in predicted_functions for child in children)
            if not has_predicted_child:
                leaf_functions.add(func)

        return leaf_functions

    def _get_predicted_children(self, func, predicted_functions):
        """
        获取某功能在当前预测结果中的子功能列表

        Args:
            func: 功能名称
            predicted_functions: 预测到的功能集合

        Returns:
            list: 在预测结果中出现的子功能列表
        """
        children = self._get_children(func)
        return [child for child in children if child in predicted_functions]

    def _propagate_probability_to_parents(self, func_results):
        """
        将子功能的概率传播到父功能

        规则：父功能概率 = max(自身概率, 所有子功能概率的最大值)
        原因：如果子功能存在，父功能必然存在

        Args:
            func_results: 功能预测结果字典

        Returns:
            dict: 更新后的 func_results
        """
        parent_map = self.func_hierarchy['parent_map']

        # 按层级深度排序，从最深的子功能开始向上传播
        sorted_funcs = sorted(
            func_results.keys(),
            key=lambda f: self._get_hierarchy_level(f),
            reverse=True
        )

        for func in sorted_funcs:
            parent = parent_map.get(func)
            if parent and parent in func_results:
                child_prob = func_results[func].get('probability', 0)
                parent_prob = func_results[parent].get('probability', 0)
                # 父功能概率至少等于子功能概率
                func_results[parent]['probability'] = max(parent_prob, child_prob)

        return func_results

    def _calculate_unique_contributors(self, func_results):
        """
        计算每个功能独有的贡献者数量（不与子功能共享）

        Args:
            func_results: 功能预测结果字典

        Returns:
            dict: {function: unique_contributor_count}
        """
        unique_counts = {}
        children_map = self.func_hierarchy['children_map']

        for func, data in func_results.items():
            func_contributors = {c['name'] for c in data.get('contributors', [])}

            # 收集所有子功能的贡献者
            child_contributors = set()
            for child in children_map.get(func, []):
                if child in func_results:
                    child_contributors.update(
                        c['name'] for c in func_results[child].get('contributors', [])
                    )

            # 独有贡献者 = 该功能贡献者 - 所有子功能贡献者
            unique = func_contributors - child_contributors
            unique_counts[func] = len(unique)

        return unique_counts

    def _query_host_taxonomy_ete3(self, latin_name):
        """
        使用 ete3 查询宿主的分类信息（目、科、属）

        Args:
            latin_name: 宿主拉丁名

        Returns:
            dict: {'order': '...', 'family': '...', 'genus': '...', 'species': '...', 'taxid': int, 'lineage': list}
        """
        if not self.ncbi:
            print(f"[Warning] NCBITaxa not available, cannot query host taxonomy")
            return None

        try:
            # 查询物种名对应的 taxid
            name2taxid = self.ncbi.get_name_translator([latin_name])

            if not name2taxid or latin_name not in name2taxid:
                print(f"[Warning] Host '{latin_name}' not found in NCBI Taxonomy")
                return None

            taxid = name2taxid[latin_name][0]

            # 获取完整的分类谱系
            lineage = self.ncbi.get_lineage(taxid)

            # 获取所有分类等级的名称
            ranks = self.ncbi.get_rank(lineage)
            names = self.ncbi.get_taxid_translator(lineage)

            # 提取目、科、属信息
            targets = {
                "order": "N/A",
                "family": "N/A",
                "genus": "N/A",
                "species": latin_name,
                "taxid": taxid,
                "lineage": lineage  # 保存完整谱系用于距离计算
            }

            for tid in lineage:
                rank = ranks.get(tid, "")
                name = names.get(tid, "")

                if rank == "order":
                    targets["order"] = name
                elif rank == "family":
                    targets["family"] = name
                elif rank == "genus":
                    targets["genus"] = name

            print(f"[Host Taxonomy] {latin_name} -> Order: {targets['order']}, Family: {targets['family']}, Genus: {targets['genus']}")
            return targets

        except Exception as e:
            print(f"[Error] Failed to query host taxonomy via ete3: {e}")
            return None

    def _calculate_taxonomic_distance(self, db_host):
        """
        计算用户宿主与数据库宿主之间的分类学距离（线性量化）

        分类学距离定义：
        - 0: 同一物种
        - 1: 同属不同种
        - 2: 同科不同属
        - 3: 同目不同科
        - 4: 同纲不同目
        - 5: 同门不同纲
        - 6: 不同门
        - 999: 无法计算（缺少分类信息）

        Args:
            db_host: 数据库中的宿主物种名

        Returns:
            int: 分类学距离 (0-6, 999表示无法计算)
        """
        # 如果没有用户宿主信息或 NCBI 不可用，返回默认值
        if not self.user_host or not self.host_taxonomy or not self.ncbi:
            return 999

        db_host = str(db_host).strip()

        # 处理特殊情况
        if db_host.lower() in ['general', 'n/a', '*', '']:
            return 999  # 通用记录，无法计算距离

        try:
            # 查询数据库宿主的 taxid
            name2taxid = self.ncbi.get_name_translator([db_host])

            if not name2taxid or db_host not in name2taxid:
                # 如果找不到，返回最大距离
                return 999

            db_taxid = name2taxid[db_host][0]
            user_taxid = self.host_taxonomy.get('taxid')

            if not user_taxid:
                return 999

            # 如果是同一物种
            if db_taxid == user_taxid:
                return 0

            # 获取两个物种的分类谱系
            user_lineage = self.host_taxonomy.get('lineage', [])
            db_lineage = self.ncbi.get_lineage(db_taxid)

            # 找到最近公共祖先 (LCA - Lowest Common Ancestor)
            common_ancestors = set(user_lineage) & set(db_lineage)

            if not common_ancestors:
                return 6  # 完全不同的谱系

            # 获取所有公共祖先的等级
            ranks = self.ncbi.get_rank(list(common_ancestors))

            # 定义标准分类等级的优先级（从低到高）
            standard_ranks = ["species", "genus", "family", "order", "class", "phylum", "superkingdom"]
            rank_distance = {
                "species": 0,
                "genus": 1,
                "family": 2,
                "order": 3,
                "class": 4,
                "phylum": 5,
                "superkingdom": 6
            }

            # 找到最近的标准分类等级
            lca_rank = None
            for rank in standard_ranks:
                # 检查是否有公共祖先属于这个等级
                for taxid, tid_rank in ranks.items():
                    if tid_rank == rank:
                        lca_rank = rank
                        break
                if lca_rank:
                    break

            if lca_rank:
                distance = rank_distance.get(lca_rank, 6)
            else:
                # 如果没有找到标准等级，返回最大距离
                distance = 6

            return distance

        except Exception as e:
            # 查询失败，返回最大距离
            return 999

    def _compute_clr_transformation(self, abundance_series):
        """
        计算中心对数比转换 (Centered Log-Ratio, CLR)

        CLR 转换公式：
        CLR(x_i) = ln(x_i) - (1/D) * Σ ln(x_j) = ln(x_i / g(x))
        其中 g(x) 是所有成分的几何均值

        优势：
        1. 消除组成性数据的闭合效应（compositional data closure）
        2. 转换后数据更接近正态分布
        3. 保留成分间的相对关系
        4. 适合后续的统计分析和机器学习

        零值处理策略：
        使用乘法替换法（Multiplicative Replacement）
        - 将零值替换为 δ = 0.65 * min(非零值)
        - 按比例调整非零值以保持总和不变

        Args:
            abundance_series: pandas Series，包含各 OTU 的丰度值

        Returns:
            dict: {
                'clr_values': {taxon: clr_value},  # 每个分类单元的 CLR 值
                'geometric_mean': float,            # 几何均值
                'pseudocount': float                # 使用的伪计数
            }
        """
        # 过滤掉零值和负值，获取有效丰度
        valid_abundances = abundance_series[abundance_series > 0]

        if len(valid_abundances) == 0:
            print("[Warning] No valid abundances for CLR transformation")
            return {
                'clr_values': {},
                'geometric_mean': 1.0,
                'pseudocount': 0.0
            }

        # === 零值处理：乘法替换法 ===
        # 计算伪计数 δ = 0.65 * min(非零值)
        # 0.65 是常用的保守系数，避免过度影响数据结构
        min_nonzero = valid_abundances.min()
        pseudocount = 0.65 * min_nonzero

        # 创建替换后的丰度数组
        replaced_abundances = abundance_series.copy()
        zero_count = (abundance_series == 0).sum()

        if zero_count > 0:
            # 计算需要分配给零值的总量
            total_delta = pseudocount * zero_count
            # 计算非零值的缩放因子（保持总和不变）
            original_sum = abundance_series.sum()
            if original_sum > total_delta:
                scale_factor = (original_sum - total_delta) / valid_abundances.sum()
                # 替换零值
                replaced_abundances = abundance_series.apply(
                    lambda x: pseudocount if x == 0 else x * scale_factor
                )
            else:
                # 如果零值太多，使用简单的伪计数加法
                replaced_abundances = abundance_series + pseudocount

        # === 计算 CLR 转换 ===
        # 1. 计算对数值
        log_abundances = np.log(replaced_abundances[replaced_abundances > 0])

        # 2. 计算几何均值的对数（= 对数的算术均值）
        log_geometric_mean = log_abundances.mean()

        # 3. 几何均值
        geometric_mean = np.exp(log_geometric_mean)

        # 4. CLR 值 = ln(x_i) - ln(g(x))
        clr_values = {}
        for idx, value in replaced_abundances.items():
            if value > 0:
                clr_values[idx] = np.log(value) - log_geometric_mean
            else:
                clr_values[idx] = 0.0  # 理论上不应该发生

        return {
            'clr_values': clr_values,
            'geometric_mean': geometric_mean,
            'pseudocount': pseudocount
        }

    def _get_clr_value(self, taxon_key):
        """
        获取指定分类单元的 CLR 值

        Args:
            taxon_key: 分类单元的键（通常是 DataFrame 的索引）

        Returns:
            float: CLR 值，如果未找到则返回 0.0
        """
        if self.clr_values is None:
            return 0.0
        return self.clr_values.get(taxon_key, 0.0)

    def _clr_to_score(self, clr_value):
        """
        将 CLR 值转换为评分

        CLR 值的特点：
        - 范围：理论上 (-∞, +∞)，实际通常在 [-10, +10]
        - 均值：0（几何均值对应的 CLR 值）
        - 正值：高于几何均值（相对丰度较高）
        - 负值：低于几何均值（相对丰度较低）

        转换策略：
        使用 Sigmoid 函数将 CLR 值映射到 [0, 1] 范围，然后缩放

        Args:
            clr_value: CLR 转换后的值

        Returns:
            float: 转换后的评分（用于 base_score 计算）
        """
        # Sigmoid 转换：将 CLR 值映射到 (0, 1)
        # 使用 k=0.5 作为缩放因子，使得 CLR=2 对应约 0.73，CLR=4 对应约 0.88
        sigmoid_value = 1 / (1 + np.exp(-0.5 * clr_value))

        # 缩放到合理的分数范围
        # 原来的 log10(ra_pct + 1) 范围大约是 [0, 2]（对于 0-100% 的 RA）
        # 我们将 sigmoid 值缩放到类似范围
        return sigmoid_value * 2.0

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
        """
        加载数据库（包含 evidence_level 字段）

        支持模糊匹配：自动清理数据库中分类名的细致分类后缀
        """
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

            genus_raw = g_match.group(1).strip() if g_match else None
            species_raw = s_match.group(1).strip() if s_match else None

            # === 模糊匹配：清理分类名后缀 ===
            genus = self._clean_taxonomy_name(genus_raw) if genus_raw else None
            species = self._clean_taxonomy_name(species_raw) if species_raw else None

            if not genus or genus == '*': continue

            # 存入字典
            if genus not in genus_map: genus_map[genus] = []
            genus_map[genus].append(row)

            if species and species != '*' and 'unclassified' not in species.lower():
                full_name = species if genus in species else f"{genus} {species}"
                if full_name not in species_map: species_map[full_name] = []
                species_map[full_name].append(row)

        print(f"Database loaded: {len(species_map)} species keys, {len(genus_map)} genus keys.")
        print(f"[Info] Fuzzy matching enabled: taxonomy suffixes like '_D_776786' will be automatically cleaned")
        return {'species': species_map, 'genus': genus_map}

    def _parse_input_taxon(self, taxon_str):
        """
        解析输入 OTU 的分类字符串（支持模糊匹配）

        自动清理分类名中的细致分类后缀，如：
        - g__Akkermansia_A -> Akkermansia
        - s__Akkermansia muciniphila_D_776786 -> Akkermansia muciniphila

        Args:
            taxon_str: 分类字符串，如 "g__Genus;s__Species"

        Returns:
            tuple: (genus, species) 清理后的属名和种名
        """
        g_match = re.search(r'g__([^;]+)', taxon_str)
        s_match = re.search(r's__([^;]+)', taxon_str)

        genus_raw = g_match.group(1).strip() if g_match else None
        species_raw = s_match.group(1).strip() if s_match else None

        # === 模糊匹配：清理分类名后缀 ===
        genus = self._clean_taxonomy_name(genus_raw) if genus_raw else None
        species_cleaned = self._clean_taxonomy_name(species_raw) if species_raw else None

        species = None
        invalid_species = ['unclassified', 'unknown', 'none', '*', 'sp.', 'sp']
        if genus and species_cleaned:
            is_valid = not any(x in species_cleaned.lower() for x in invalid_species)
            if is_valid:
                species = species_cleaned if genus in species_cleaned else f"{genus} {species_cleaned}"

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

        # === 计算 Shannon Index (α 多样性) ===
        # Shannon Index = -Σ(pi * ln(pi))
        # 其中 pi 是每个 OTU 的相对丰度
        shannon_index = 0.0
        for _, row in input_df.iterrows():
            abundance = float(row['Abundance'])
            if abundance > 0:
                pi = abundance / total_reads
                shannon_index += -pi * np.log(pi)

        print(f"Shannon Index (α-diversity): {shannon_index:.4f}")

        # === 计算 CLR 转换 (Centered Log-Ratio) ===
        # CLR 转换更适合组成性数据（compositional data），消除闭合效应
        print("[Info] Computing CLR (Centered Log-Ratio) transformation...")
        clr_result = self._compute_clr_transformation(input_df['Abundance'])
        self.clr_values = clr_result['clr_values']
        self.geometric_mean = clr_result['geometric_mean']
        print(f"[Info] CLR transformation complete: geometric mean = {self.geometric_mean:.4f}, "
              f"pseudocount = {clr_result['pseudocount']:.6f}")

        # 创建索引到 CLR 值的映射（用于后续查询）
        # 同时创建 Taxon 到 CLR 值的映射
        taxon_clr_map = {}
        for idx, row in input_df.iterrows():
            taxon = row['Taxon']
            clr_val = self.clr_values.get(idx, 0.0)
            taxon_clr_map[taxon] = clr_val

        # === 预处理：计算每个属的总丰度和 CLR 值 ===
        # 用于在 match records 中显示正确的属级别 RA%
        genus_abundance = {}
        genus_clr = {}  # 属级别的 CLR 值（取该属下所有 OTU 的最大 CLR 值）
        for idx, row in input_df.iterrows():
            taxon = row['Taxon']
            abundance = float(row['Abundance'])
            if abundance <= 0: continue

            genus, species = self._parse_input_taxon(taxon)
            if genus:
                if genus not in genus_abundance:
                    genus_abundance[genus] = 0
                    genus_clr[genus] = float('-inf')
                genus_abundance[genus] += abundance
                # 取该属下所有 OTU 的最大 CLR 值
                clr_val = self.clr_values.get(idx, 0.0)
                genus_clr[genus] = max(genus_clr[genus], clr_val)

        # === 容器 ===
        func_results = {}
        potential_symbionts = []

        for idx, row in input_df.iterrows():
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

            # === [Updated v5.0] 计算相对丰度和 CLR 值 ===
            # 1. 计算 RA% (0-100) - 保留用于展示和概率计算
            # 对于属级别匹配，使用整个属的总丰度
            # 对于种级别匹配，使用当前 OTU 的丰度
            if match_type == "Genus":
                # 属级别匹配：使用整个属的总丰度和 CLR 值
                effective_abundance = genus_abundance.get(genus, abundance)
                clr_value = genus_clr.get(genus, 0.0)
            else:
                # 种级别匹配：使用当前 OTU 的丰度和 CLR 值
                effective_abundance = abundance
                clr_value = self.clr_values.get(idx, 0.0)

            ra_pct = (effective_abundance / total_reads) * 100

            # 2. 计算基础 Score (基于 CLR 值)
            # CLR 转换更适合组成性数据，消除闭合效应
            # Formula: Weight * clr_to_score(CLR) * SCALING_FACTOR
            clr_score = self._clr_to_score(clr_value)
            base_score = confidence_weight * clr_score * self.SCORE_SCALING_FACTOR

            # 辅助数据
            simple_name = species if match_type == "Species" else f"{genus} (sp.)"

            # === 遍历匹配记录 ===
            unique_funcs_for_summary = set()

            for rec in matched_records:
                func_name = rec['function']

                # === 排除 'other' 标签 ===
                # 'other' 是一个特殊的兜底标签，不具有明确的功能含义，在预测中排除
                if func_name.lower() == 'other':
                    continue

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
                    'CLR_Value': round(clr_value, 4),  # 新增：CLR 转换值
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

        # === Phase 1 & 2: 层级关系处理 ===
        # 1. 识别叶子功能
        predicted_functions = set(func_results.keys())
        leaf_functions = self._identify_leaf_functions(predicted_functions)

        # 2. 计算独有贡献者数量
        unique_contributor_counts = self._calculate_unique_contributors(func_results)

        # 3. 为每个功能添加概率（用于后续传播）
        # 先计算原始概率，存入 func_results
        for func, data in func_results.items():
            taxa_count = len(data['contributors'])
            ra_pct = data['ra_sum']
            avg_confidence = data['weighted_conf_sum'] / data['ra_sum'] if data['ra_sum'] > 0 else 0
            avg_host_match = data['weighted_host_sum'] / data['ra_sum'] if data['ra_sum'] > 0 else 1.0
            avg_evidence_weight = data['weighted_evidence_sum'] / data['ra_sum'] if data['ra_sum'] > 0 else 1.0

            # 计算原始概率（与下面的逻辑相同）
            import math
            base_prob = 1 / (1 + math.exp(-0.2 * (ra_pct - 15)))

            if avg_confidence >= 0.9:
                confidence_factor = 1.0
            elif avg_confidence >= 0.7:
                confidence_factor = 0.85
            else:
                confidence_factor = 0.70

            if avg_host_match >= 1.4:
                host_factor = 1.0
            elif avg_host_match >= 1.25:
                host_factor = 0.95
            elif avg_host_match >= 1.15:
                host_factor = 0.90
            elif avg_host_match >= 1.05:
                host_factor = 0.85
            elif avg_host_match >= 0.95:
                host_factor = 0.75
            else:
                host_factor = 0.50

            if avg_evidence_weight >= 1.4:
                evidence_factor = 1.0
            elif avg_evidence_weight >= 1.25:
                evidence_factor = 0.95
            elif avg_evidence_weight >= 1.1:
                evidence_factor = 0.85
            elif avg_evidence_weight >= 0.95:
                evidence_factor = 0.75
            else:
                evidence_factor = 0.60

            if taxa_count == 1:
                taxa_factor = 0.90
            elif taxa_count <= 5:
                taxa_factor = 0.90 + (taxa_count - 1) * 0.0125
            elif taxa_count <= 20:
                taxa_factor = 0.95 + ((taxa_count - 5) / 15) * 0.05
            else:
                taxa_factor = 1.0 + (math.log10(taxa_count / 20) * 0.05)
                taxa_factor = min(taxa_factor, 1.08)

            bottleneck_factor = min(confidence_factor, host_factor, evidence_factor)
            probability = base_prob * bottleneck_factor * taxa_factor
            probability = max(0.0, min(0.95, probability))

            data['probability'] = probability

        # 4. Phase 2: 概率层级传播（子功能概率 → 父功能概率）
        self._propagate_probability_to_parents(func_results)

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

            # === 新增：收集所有贡献者的属名（Genus 级别）===
            # 从 contributors 列表中提取属名，去重并按丰度排序
            contributor_genera = []
            seen_genera = set()

            for contrib in sorted_contributors:
                # 从 contributor name 中提取属名
                # 格式可能是 "Genus species" 或 "Genus (sp.)"
                taxon_name = contrib['name']

                # 提取属名（第一个单词）
                genus = taxon_name.split()[0] if taxon_name else ''

                # 去重
                if genus and genus not in seen_genera:
                    seen_genera.add(genus)
                    contributor_genera.append(genus)

            # 用逗号分隔（而非制表符，因为在 TSV 中制表符会被解析为列分隔符）
            contributor_list = ', '.join(contributor_genera)

            # === Phase 1 & 2: 获取层级信息 ===
            # 获取父功能
            parent_func = self._get_parent(func)
            # 获取大类
            parent_category = self._get_category(func)
            # 获取层级深度
            hierarchy_level = self._get_hierarchy_level(func)
            # 判断是否为叶子功能
            is_leaf = func in leaf_functions
            # 获取当前预测中的子功能
            predicted_children = self._get_predicted_children(func, predicted_functions)
            child_functions_str = ', '.join(predicted_children) if predicted_children else 'None'
            # 获取独有贡献者数量
            unique_contributors = unique_contributor_counts.get(func, taxa_count)

            # 使用传播后的概率（Phase 2）
            final_probability = data.get('probability', probability)

            func_rows.append({
                'Function': func,
                'Final_Score_Sum': round(data['fps_score'], 1),  # 最终总分（整合所有权重）
                'Total_RA_Pct': round(data['ra_sum'], 3),        # 该功能的总丰度
                'Mean_Confidence': round(avg_confidence, 2),
                'Mean_Host_Match': round(avg_host_match, 2),
                'Mean_Evidence_Weight': round(avg_evidence_weight, 2),
                'Taxa_Count': taxa_count,
                'Probability': round(final_probability, 3),       # 使用传播后的概率
                # === Phase 1: 层级标注列 ===
                'Parent': parent_func if parent_func else 'None',
                'Parent_Category': parent_category,
                'Hierarchy_Level': hierarchy_level,
                'Is_Leaf': is_leaf,
                # === Phase 2: 子功能和独有贡献者 ===
                'Child_Functions': child_functions_str,
                'Unique_Contributors': unique_contributors,
                'Dominant_Contributor': top_contributor_str,
                'Contributor_List': contributor_list
            })

        func_df = pd.DataFrame(func_rows)
        if not func_df.empty:
            func_df = func_df.sort_values('Final_Score_Sum', ascending=False)

        # === Phase 1: --leaf-only 过滤 ===
        # 如果启用了 leaf_only 模式，只保留叶子功能
        if self.leaf_only and not func_df.empty:
            original_count = len(func_df)
            func_df = func_df[func_df['Is_Leaf'] == True]
            filtered_count = len(func_df)
            print(f"[Info] --leaf-only mode: filtered {original_count} -> {filtered_count} functions")

        # 修改输出文件名：使用 _functions.tsv 后缀
        # 用户提供前缀，自动添加后缀
        base, ext = os.path.splitext(output_path)
        # 如果没有后缀或后缀不是 .tsv，强制使用 .tsv
        if ext.lower() not in ['.tsv', '.txt', '.csv']:
            ext = '.tsv'
            base = output_path  # 整个路径作为前缀

        if not base.endswith('_functions'):
            functions_output_path = f"{base}_functions{ext}"
        else:
            functions_output_path = f"{base}{ext}"

        func_df.to_csv(functions_output_path, sep='\t', index=False)
        print(f"Function summary saved to: {functions_output_path}")

        # ==========================================
        # 输出表格 2: 匹配记录明细 (Match Records)
        # ==========================================
        match_records_path = f"{base}_match_records{ext}"

        taxa_df = pd.DataFrame(potential_symbionts)

        if not taxa_df.empty:
            # === 改进 1: 每个 Symbiont_Taxon 只保留 Top 5 记录 ===
            # 按 Symbiont_Taxon 分组，每组保留 Final_Score 最高的 5 条记录
            taxa_df = taxa_df.sort_values('Final_Score', ascending=False)
            taxa_df = taxa_df.groupby('Symbiont_Taxon', as_index=False).head(5)

            # === 改进 2: 重新计算 Final_Score，提高宿主匹配和证据等级的权重 ===
            # 新公式: Final_Score = Base_Score × (Host_Match_Weight^2) × (Evidence_Weight^1.5)
            # 原因:
            # - 宿主匹配的科学说服力应该更高（平方放大差异）
            # - 证据等级也应该有更强的影响（1.5 次方）
            # - 这样可以显著提升高质量匹配的分数，降低 Mismatch 的分数
            taxa_df['Adjusted_Score'] = (
                taxa_df['Base_Score'] *
                (taxa_df['Host_Match_Weight'] ** 2) *
                (taxa_df['Evidence_Weight'] ** 1.5)
            ).round(1)

            # === 改进 3: 添加综合质量指标 (Quality_Score) ===
            # 用于进一步区分记录质量
            # Quality_Score = (Host_Match_Weight × 40) + (Evidence_Weight × 30) +
            #                 (Match_Level_Score × 20) + (RA% × 10)
            #
            # 各因素权重:
            # - 宿主匹配: 40% (最重要)
            # - 证据质量: 30% (次重要)
            # - 分类匹配: 20% (重要)
            # - 相对丰度: 10% (参考)

            # Match_Level 转换为分数
            match_level_score = taxa_df['Match_Level'].map({
                'Species': 1.0,
                'Genus': 0.6
            }).fillna(0.6)

            # 标准化 RA% 到 0-1 范围（假设最大 RA% 为 50%）
            normalized_ra = (taxa_df['Relative_Abundance_Pct'] / 50).clip(upper=1.0)

            taxa_df['Quality_Score'] = (
                (taxa_df['Host_Match_Weight'] * 40) +
                (taxa_df['Evidence_Weight'] * 30) +
                (match_level_score * 20) +
                (normalized_ra * 10)
            ).round(1)

            # 最终排序：优先 Adjusted_Score，其次 Quality_Score
            taxa_df = taxa_df.sort_values(
                ['Adjusted_Score', 'Quality_Score', 'Relative_Abundance_Pct'],
                ascending=[False, False, False]
            )

            # 输出列顺序
            cols = ['Symbiont_Taxon', 'Predicted_Function',
                    'Adjusted_Score', 'Quality_Score', 'Base_Score',
                    'CLR_Value',  # 新增：CLR 转换值
                    'Host_Match_Weight', 'Host_Match_Level',
                    'Evidence_Level', 'Evidence_Weight',
                    'Match_Level', 'Relative_Abundance_Pct',
                    'DB_Host_Context', 'DB_Description', 'DB_Evidence']
            taxa_df = taxa_df[cols]

            taxa_df.to_csv(match_records_path, sep='\t', index=False)
            print(f"Match records saved to: {match_records_path}")
            print(f"  - Total records: {len(taxa_df)}")
            print(f"  - Unique symbionts: {taxa_df['Symbiont_Taxon'].nunique()}")

            # ==========================================
            # 输出表格 3: 特征矩阵 (Feature Matrix for ML)
            # ==========================================
            # v4.6: 新增 Shannon_Index - 反映微生物组α多样性
            # 适用于小样本随机森林训练
            print("\nGenerating feature matrix for machine learning...")
            print("  - Design: Taxon-Function pair level (v4.6 - with α-diversity)")
            print("  - Features: 8 core non-redundant features")
            print("  - Key improvement: Added Shannon_Index for community diversity")
            print("  - Strategy: Ceiling principle + Literature support + α-diversity")

            # === 预处理：收集函数级别的概率和支持度数据 ===
            func_prob_map = {}
            func_support_count = {}

            if not func_df.empty:
                for _, row in func_df.iterrows():
                    func_prob_map[row['Function']] = row['Probability']
                    func_support_count[row['Function']] = row['Taxa_Count']

            # === 构建 Taxon-Function 配对级别的特征矩阵 ===
            # v4.6: 新增 Shannon_Index - 反映微生物组α多样性
            # 移除: Relative_Abundance_Pct, Host_Match_Weight_Mean, Evidence_Level_Mean,
            #       Bottleneck_Score, Function_Support_Count, Taxonomic_Distance_Min
            # 保留: 8 个核心特征（新增 Shannon_Index）
            feature_rows = []

            # 按 Taxon-Function 分组聚合
            grouped = taxa_df.groupby(['Symbiont_Taxon', 'Predicted_Function'])

            for (taxon, function), group in grouped:
                # === 聚合策略 ===
                # 1. 丰度、分类匹配：取第一条（同一 taxon 的所有记录相同）
                # 2. 宿主匹配、证据等级：取最大值（最佳匹配）
                # 3. 分数：取最大值（最高质量）
                # 4. 文献数：基于 DOI 去重统计（同一篇文献只算一次）
                # 5. Shannon Index：样本级别的α多样性（所有行相同）
                # 6. CLR 值：取最大值（最高相对丰度）

                # 取第一条记录的基础信息（丰度、分类匹配）
                first_record = group.iloc[0]
                relative_abundance = first_record['Relative_Abundance_Pct']
                match_level = first_record['Match_Level']
                # 获取 CLR 值（取最大值，因为同一 taxon 可能有多条记录）
                clr_value = group['CLR_Value'].max()

                # 取最大值的质量指标（宿主匹配、证据等级、分数）
                max_host_match_weight = group['Host_Match_Weight'].max()
                max_evidence_level = group['Evidence_Level'].max()
                max_adjusted_score = group['Adjusted_Score'].max()

                # === 优化：基于 DOI 去重统计文献数量 ===
                # 从 group 中提取所有 DB_Evidence 字段（DOI）
                # 注意：DB_Evidence 列在 taxa_df 中对应原始数据库的 evidence 字段
                dois = []
                for _, rec in group.iterrows():
                    doi = str(rec.get('DB_Evidence', '')).strip()
                    # 过滤空值和无效 DOI
                    if doi and doi.lower() not in ['', 'nan', 'none', 'n/a', '-']:
                        dois.append(doi)

                # 去重统计唯一 DOI 数量
                unique_dois = set(dois)
                literature_count = len(unique_dois) if unique_dois else len(group)
                # 如果没有有效 DOI，则回退到记录数（保守估计）

                # === Feature 1: Abundance (CLR 转换) ===
                # F1. CLR_Abundance (中心对数比转换)
                # CLR 转换更适合组成性数据（compositional data）
                # 优势：消除闭合效应，保留成分间相对关系
                # 范围：理论上 (-∞, +∞)，实际通常在 [-10, +10]
                # 正值表示高于几何均值，负值表示低于几何均值
                clr_abundance = clr_value

                # === Feature 2: Taxonomic Confidence ===
                # F2. Match_Level_Score (分类匹配置信度)
                match_level_score = 1.0 if match_level == 'Species' else 0.6

                # === Feature 3: Host Context ===
                # F3. Host_Match_Weight_Max (最佳宿主匹配权重)
                # 移除 Host_Match_Weight_Mean（关注潜力天花板，而非平均值）
                # 移除 Taxonomic_Distance_Min（与 Host_Match_Weight_Max 逻辑重复）
                host_weight_max = max_host_match_weight

                # === Feature 4: Evidence Quality ===
                # F4. Evidence_Level_Max (最高证据等级)
                # 移除 Evidence_Level_Mean（遵循"最高证据原则"）
                evidence_lvl_max = max_evidence_level

                # === Feature 5: Integrated Quality Score ===
                # F5. Adjusted_Score_Max (最高综合质量分数)
                # 移除 Bottleneck_Score（特征重叠，已被其他特征覆盖）
                adj_score_max = max_adjusted_score

                # === Feature 6: Literature Support (优化) ===
                # F6. DB_Literature_Count (该 Taxon-Function 组合有多少篇文献支持)
                # 基于 DOI 去重：同一篇文献在不同宿主中的记录只算 1 次
                # 反映该预测的文献支持度（比记录数更科学）
                db_literature_count = literature_count

                # === Feature 7: Community Diversity (新增) ===
                # F7. Shannon_Index (样本的α多样性)
                # 反映微生物组的多样性，可能影响共生菌功能表达
                # 所有 Taxon-Function 对的 Shannon Index 相同（样本级别特征）
                shannon_idx = shannon_index

                # === Feature 8: Rank by Abundance (相对排名) ===
                # F8. Rank_By_Abundance (丰度排名)
                # 这个特征需要在所有记录收集后计算，先设置占位符
                # 移除 Function_Support_Count（描述群落而非特定分类单元）
                rank_by_abundance = 0  # Placeholder

                # 构建特征向量（每个 Taxon-Function 组合一行）
                feature_rows.append({
                    # === Identifiers ===
                    'Taxon': taxon,
                    'Function': function,
                    # === 8 Core Features ===
                    'CLR_Abundance': round(clr_abundance, 4),  # 改用 CLR 转换
                    'Match_Level_Score': match_level_score,
                    'Host_Match_Weight_Max': round(host_weight_max, 3),
                    'Evidence_Level_Max': int(evidence_lvl_max),
                    'Adjusted_Score_Max': round(adj_score_max, 2),
                    'DB_Literature_Count': db_literature_count,
                    'Shannon_Index': round(shannon_idx, 4),
                    'Rank_By_Abundance': rank_by_abundance
                })

            feature_df = pd.DataFrame(feature_rows)

            # === Post-processing: Compute Ranking Features ===
            if not feature_df.empty:
                # 按 CLR 值排名（1 = 最高 CLR 值 = 最高相对丰度）
                # CLR 值越高表示相对丰度越高于几何均值
                feature_df['Rank_By_Abundance'] = feature_df['CLR_Abundance'].rank(
                    ascending=False, method='min'
                ).astype(int)

            # 按 Adjusted_Score_Max 排序（最高质量的预测在前）
            feature_df = feature_df.sort_values('Adjusted_Score_Max', ascending=False)

            # 保存特征矩阵
            feature_matrix_path = f"{base}_feature_matrix{ext}"
            feature_df.to_csv(feature_matrix_path, sep='\t', index=False)

            print(f"Feature matrix saved to: {feature_matrix_path}")
            print(f"  - Total unique Taxon-Function pairs: {len(feature_df)}")
            print(f"  - Unique taxa: {feature_df['Taxon'].nunique()}")
            print(f"  - Unique functions: {feature_df['Function'].nunique()}")
            print(f"  - Features per pair: {len(feature_df.columns) - 2}")  # 减去 Taxon 和 Function
            print(f"\nFeature list (8 core features, v5.0 - with CLR transformation):")
            print(f"  1. CLR_Abundance              - Centered Log-Ratio transformed abundance ⭐ UPDATED")
            print(f"  2. Match_Level_Score          - Taxonomic confidence (0.6=Genus, 1.0=Species)")
            print(f"  3. Host_Match_Weight_Max      - Best host match (0.8-1.5, ceiling principle)")
            print(f"  4. Evidence_Level_Max         - Highest evidence quality (1-5, best evidence)")
            print(f"  5. Adjusted_Score_Max         - Integrated quality score (for ranking)")
            print(f"  6. DB_Literature_Count        - Unique publications (DOI-based, 1-N)")
            print(f"  7. Shannon_Index              - α-diversity (community evenness)")
            print(f"  8. Rank_By_Abundance          - Abundance rank (1=highest)")
            print(f"\nCLR transformation advantages:")
            print(f"  ✓ Eliminates compositional data closure effect")
            print(f"  ✓ Preserves relative relationships between components")
            print(f"  ✓ More suitable for microbiome abundance data")
            print(f"  ✓ Zero handling via multiplicative replacement")
        else:
            print("No match records found.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Record-based symbiont function prediction with host-context scoring (using ete3 NCBI Taxonomy)"
    )
    parser.add_argument('-i', '--input', required=True, help="Input OTU table (TSV format)")
    parser.add_argument('-d', '--db', required=True, help="Symbiont database TSV (record_db.tsv)")
    parser.add_argument('-o', '--output', required=True, help="Output file path")
    parser.add_argument('--host', help="Host species Latin name (e.g., 'Apis mellifera'). Queries NCBI Taxonomy via ete3.")
    parser.add_argument('--host-db', help="[Deprecated] This parameter is kept for backward compatibility but is no longer used. Host taxonomy is now queried via ete3.")
    parser.add_argument('--leaf-only', action='store_true',
                        help="Only output leaf functions (most specific child functions). "
                             "Parent functions that have predicted child functions will be filtered out.")
    args = parser.parse_args()

    # 提示用户 --host-db 参数已废弃
    if args.host_db:
        print(f"[Info] --host-db parameter is deprecated and will be ignored.")
        print(f"[Info] Host taxonomy is now queried from NCBI Taxonomy via ete3.")

    # 检查 ete3 是否可用
    if args.host and not NCBI_TAXA_AVAILABLE:
        print(f"[Warning] Host specified but ete3 is not installed.")
        print(f"[Warning] Install ete3 with: pip install ete3")
        print(f"[Warning] Proceeding without host-context scoring")

    # 显示 --leaf-only 模式信息
    if args.leaf_only:
        print(f"[Info] --leaf-only mode enabled: only leaf functions will be output")

    predictor = RecordPredictor(args.db, host_db_path=None, user_host=args.host, leaf_only=args.leaf_only)
    predictor.predict(args.input, args.output)