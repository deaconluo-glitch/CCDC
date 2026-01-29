import pandas as pd
import numpy as np
import re
from datetime import datetime
import streamlit as st

class ComplaintDataProcessor:
    def __init__(self):
        self.sn_database_a = None
        self.sn_database_b = None
        
    def load_sn_databases(self, df_a, df_b=None):
        """加载SN数据库"""
        self.sn_database_a = df_a
        self.sn_database_b = df_b
        
    def clean_complaint_data(self, df):
        """客诉数据清洗与增强 - A.1"""
        cleaned_df = df.copy()
        
        # 记录原始列
        if '原始数据' not in cleaned_df.columns:
            cleaned_df['原始数据'] = cleaned_df.to_dict('records')
        
        # 1. 处理SN列 - 多个SN的情况
        if 'SN' in cleaned_df.columns:
            cleaned_df['SN_原始'] = cleaned_df['SN']
            
            def process_sn_cell(cell):
                if pd.isna(cell):
                    return None, None
                
                # 检查是否包含多个SN（用逗号、分号或空格分隔）
                cell_str = str(cell)
                separators = [',', ';', ' ', '，', '、']
                
                for sep in separators:
                    if sep in cell_str:
                        sn_list = [s.strip() for s in cell_str.split(sep) if s.strip()]
                        if len(sn_list) > 1:
                            # 保留第一个SN在SN列
                            first_sn = sn_list[0]
                            # 所有SN放入问题描述
                            all_sns = '; '.join(sn_list)
                            return first_sn, all_sns
                
                return cell_str, None
            
            cleaned_df[['SN', '多个SN列表']] = cleaned_df['SN_原始'].apply(
                lambda x: pd.Series(process_sn_cell(x))
            )
            
            # 如果有多个SN，添加到问题描述
            mask = cleaned_df['多个SN列表'].notna()
            if '问题描述' in cleaned_df.columns and mask.any():
                cleaned_df.loc[mask, '问题描述'] = cleaned_df.loc[mask].apply(
                    lambda row: f"{row['问题描述']} [多个SN: {row['多个SN列表']}]" 
                    if pd.notna(row['问题描述']) else f"[多个SN: {row['多个SN列表']}]",
                    axis=1
                )
        
        # 2. 机型纠错与标准化
        if '机器型号' in cleaned_df.columns:
            cleaned_df['机型_原始'] = cleaned_df['机器型号']
            cleaned_df['机型_标准化'] = cleaned_df['机器型号'].apply(self.standardize_machine_type)
        
        # 3. 根据SN补充信息
        if 'SN' in cleaned_df.columns and self.sn_database_a is not None:
            cleaned_df = self.enrich_with_sn_info(cleaned_df)
        
        # 4. 功率标准化
        if '功率' in cleaned_df.columns:
            cleaned_df['功率_原始'] = cleaned_df['功率']
            cleaned_df[['功率_标准化', '功率单位']] = cleaned_df['功率'].apply(
                lambda x: pd.Series(self.standardize_power(x))
            )
        
        # 5. 添加处理时间戳
        cleaned_df['数据处理时间'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return cleaned_df
    
    def standardize_machine_type(self, machine_desc):
        """标准化机型描述"""
        if pd.isna(machine_desc):
            return "未知"
        
        desc = str(machine_desc).lower()
        
        # 根据需求文档中的规则
        mapping_rules = {
            '微逆': '微逆',
            '组串单相': '单相组串',
            '组串三相': '三相组串',
            '储能单相': '单相储能',
            '储能三相低压': '低压三相储能',
            '储能三相高压': '高压三相储能',
            '裂相': '裂相储能',
            '离网机': '单相储能',
            'pcs': '工商业储能',
            'mppt': '工商业储能',
            'sts': '工商业储能',
            '微储': '阳台储能',
            '阳台': '阳台储能',
        }
        
        for keyword, std_type in mapping_rules.items():
            if keyword in desc:
                return std_type
        
        # 检查产品代码
        product_code_patterns = {
            'LP1': '单相储能',
            'LP2': '裂相储能',
            'LP3': '低压三相储能',
            'HP3': '高压三相储能',
            'MG': '微逆',
            'OG': '单相储能',
            'P1': '单相组串',
            'P3': '三相组串',
        }
        
        for code, std_type in product_code_patterns.items():
            if code in desc.upper():
                return std_type
        
        return "其他"
    
    def standardize_power(self, power_value):
        """标准化功率"""
        if pd.isna(power_value):
            return None, None
        
        power_str = str(power_value)
        
        # 提取数字
        numbers = re.findall(r'\d+\.?\d*', power_str)
        if not numbers:
            return None, None
        
        power_num = float(numbers[0])
        
        # 判断单位
        if 'w' in power_str.lower() and 'kw' not in power_str.lower():
            # 微逆使用W，其他使用KW
            if '微逆' in power_str.lower():
                unit = 'W'
            else:
                power_num = power_num / 1000
                unit = 'KW'
        else:
            unit = 'KW'
        
        return power_num, unit
    
    def enrich_with_sn_info(self, df):
        """根据SN补充信息"""
        enriched_df = df.copy()
        
        # 首先匹配数据库A
        matched_info = []
        for sn in enriched_df['SN']:
            if pd.isna(sn):
                matched_info.append({})
                continue
            
            # 在数据库A中查找
            match_a = None
            if self.sn_database_a is not None:
                match_a = self.sn_database_a[self.sn_database_a['SN'] == sn]
            
            # 在数据库B中查找 (微逆)
            match_b = None
            if self.sn_database_b is not None:
                match_b = self.sn_database_b[self.sn_database_b['SN'] == sn]
            
            info = {}
            if not match_a.empty:
                info = match_a.iloc[0].to_dict()
            
            # 如果是微逆且数据库B有匹配，使用数据库B的信息
            if not match_b.empty and ('微逆' in str(info.get('产品描述', '')) or '微逆' in str(enriched_df.get('机器型号', ''))):
                info = match_b.iloc[0].to_dict()
            
            matched_info.append(info)
        
        # 将匹配的信息合并到主表
        info_df = pd.DataFrame(matched_info)
        for col in info_df.columns:
            if col not in enriched_df.columns:
                enriched_df[f'SN信息_{col}'] = info_df[col]
        
        return enriched_df
    
    def classify_complaints(self, df, classification_rules=None):
        """客诉数据自动分类 - A.3"""
        classified_df = df.copy()
        
        # 默认分类规则
        if classification_rules is None:
            classification_rules = {
                '硬件故障': ['损坏', '故障', '不工作', '无响应', '短路', '断路'],
                '软件问题': ['程序', '软件', '固件', '升级', '版本', 'bug'],
                '安装问题': ['安装', '接线', '连接', '配置', '设置'],
                '性能问题': ['效率低', '功率不足', '过热', '噪音'],
                '外观问题': ['划伤', '变形', '颜色', '外观'],
                '其他': []  # 默认分类
            }
        
        def assign_category(problem_desc, solution_desc):
            if pd.isna(problem_desc):
                problem_desc = ''
            if pd.isna(solution_desc):
                solution_desc = ''
            
            combined_text = f"{problem_desc} {solution_desc}".lower()
            
            for category, keywords in classification_rules.items():
                for keyword in keywords:
                    if keyword.lower() in combined_text:
                        return category
            
            return '其他'
        
        # 应用分类
        if '问题描述' in classified_df.columns and '解决办法' in classified_df.columns:
            classified_df['问题分类'] = classified_df.apply(
                lambda row: assign_category(row.get('问题描述', ''), row.get('解决办法', '')),
                axis=1
            )
        
        # 提取告警代码
        if '问题描述' in classified_df.columns:
            def extract_alarm_code(text):
                if pd.isna(text):
                    return None
                
                # 查找常见的告警代码模式
                patterns = [
                    r'ERR\d{2,4}',  # ERR001, ERR1234
                    r'ALM\d{2,4}',   # ALM001
                    r'F\d{2,4}',     # F001, F123
                    r'E\d{2,4}',     # E001
                    r'代码[：:]\s*(\w+)',  # 代码: ERR001
                    r'报警[：:]\s*(\w+)',  # 报警: ERR001
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, str(text), re.IGNORECASE)
                    if matches:
                        return matches[0]
                
                return None
            
            classified_df['告警代码'] = classified_df['问题描述'].apply(extract_alarm_code)
        
        # 提取生产日期 (SN前4位)
        if 'SN' in classified_df.columns:
            def extract_production_date(sn):
                if pd.isna(sn) or len(str(sn)) < 4:
                    return None
                
                sn_str = str(sn)
                date_code = sn_str[:4]
                
                # 假设前4位是年月，如2308表示2023年8月
                if date_code.isdigit():
                    year = int(date_code[:2])
                    month = int(date_code[2:4])
                    
                    # 处理2000年以后的年份
                    if 0 <= year <= 99:
                        full_year = 2000 + year if year < 50 else 1900 + year
                        return f"{full_year}-{month:02d}"
                
                return None
            
            classified_df['生产日期'] = classified_df['SN'].apply(extract_production_date)
        
        return classified_df
    
    def calculate_defect_rate(self, complaint_df, shipment_df, period, machine_types):
        """计算不良率 - B.1"""
        
        if complaint_df.empty or shipment_df.empty:
            return pd.DataFrame()
        
        # 过滤指定期间的数据
        if '客诉时间' in complaint_df.columns:
            # 假设客诉时间是日期字符串
            complaint_df['客诉日期'] = pd.to_datetime(complaint_df['客诉时间'], errors='coerce')
        
        # 按机型统计不良数
        if '机型_标准化' in complaint_df.columns:
            defect_counts = complaint_df.groupby('机型_标准化').size().reset_index(name='不良数')
        else:
            defect_counts = pd.DataFrame({'机型_标准化': [], '不良数': []})
        
        # 按机型统计出货数
        if '机型_标准化' in shipment_df.columns:
            shipment_counts = shipment_df.groupby('机型_标准化').size().reset_index(name='出货数')
        else:
            shipment_counts = pd.DataFrame({'机型_标准化': [], '出货数': []})
        
        # 合并数据并计算不良率
        result = pd.merge(defect_counts, shipment_counts, on='机型_标准化', how='outer')
        result = result.fillna(0)
        
        # 计算不良率
        result['不良率(%)'] = result.apply(
            lambda row: (row['不良数'] / row['出货数'] * 100) if row['出货数'] > 0 else 0,
            axis=1
        )
        
        # 过滤指定机型
        if machine_types and '全部' not in machine_types:
            result = result[result['机型_标准化'].isin(machine_types)]
        
        return result
    
    def analyze_concentrated_issues(self, complaint_df, month=None, machine_type=None):
        """集中性问题分析 - B.2"""
        
        if complaint_df.empty:
            return pd.DataFrame(), pd.DataFrame()
        
        # 按问题分类统计
        if '问题分类' in complaint_df.columns:
            issue_stats = complaint_df.groupby('问题分类').agg({
                'SN': 'count',  # 问题数量
                '机型_标准化': lambda x: x.mode()[0] if not x.mode().empty else '未知'
            }).rename(columns={'SN': '问题数量'})
            
            issue_stats['占比(%)'] = (issue_stats['问题数量'] / len(complaint_df) * 100).round(2)
            issue_stats = issue_stats.sort_values('问题数量', ascending=False)
        else:
            issue_stats = pd.DataFrame()
        
        # 识别集中性问题 (数量超过阈值的问题)
        threshold = max(3, len(complaint_df) * 0.05)  # 至少3个或5%
        concentrated_issues = issue_stats[issue_stats['问题数量'] >= threshold].copy()
        
        # 为每个集中性问题获取具体案例
        case_details = {}
        for issue in concentrated_issues.index:
            cases = complaint_df[complaint_df['问题分类'] == issue][['SN', '问题描述', '客诉时间', '机型_标准化']].head(10)
            case_details[issue] = cases
        
        return issue_stats, concentrated_issues, case_details
