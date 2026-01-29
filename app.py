import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import io
import base64

# 导入自定义模块
from data_processing import ComplaintDataProcessor
from database import ComplaintDatabase
from report_generator import ReportGenerator

# 页面配置
st.set_page_config(
    page_title="AI客诉数据分析系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化Session State
if 'processor' not in st.session_state:
    st.session_state.processor = ComplaintDataProcessor()
if 'db' not in st.session_state:
    st.session_state.db = ComplaintDatabase()
if 'report_gen' not in st.session_state:
    st.session_state.report_gen = ReportGenerator()
if 'current_data' not in st.session_state:
    st.session_state.current_data = {}

# 标题和说明
st.title("📊 AI驱动的客诉数据分析系统")
st.markdown("""
该系统用于自动化处理客诉数据，包括数据清洗、分类、统计分析和报告生成。
支持与SN数据库匹配、机型标准化、不良率计算等功能。
""")

# 侧边栏导航
st.sidebar.title("导航菜单")
page = st.sidebar.selectbox(
    "选择功能模块",
    ["首页", "数据上传", "数据处理", "统计分析", "报告生成", "系统设置"]
)

# 首页
if page == "首页":
    st.header("欢迎使用客诉数据分析系统")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("数据处理效率", "提升70%+", "目标")
    
    with col2:
        st.metric("错误率降低", "<1%", "目标")
    
    with col3:
        st.metric("报告生成时间", "<2小时", "目标")
    
    st.markdown("---")
    
    st.subheader("系统功能概览")
    
    features = {
        "📥 数据上传": "上传客诉数据、出货数据、SN数据库",
        "🧹 数据清洗": "自动清洗、纠错、补全客诉数据",
        "🏷️ 数据分类": "根据规则自动分类客诉问题",
        "📈 统计分析": "计算不良率、分析集中性问题",
        "📄 报告生成": "自动生成客诉月报 (PPT/PDF/Word)",
        "🤖 智能推荐": "解决方案智能推荐 (进阶功能)"
    }
    
    cols = st.columns(3)
    for i, (title, desc) in enumerate(features.items()):
        with cols[i % 3]:
            st.info(f"**{title}**\n\n{desc}")
    
    st.markdown("---")
    st.subheader("最近操作")
    
    # 显示最近操作记录
    if 'operation_log' in st.session_state:
        log_df = pd.DataFrame(st.session_state.operation_log[-5:])
        st.dataframe(log_df, use_container_width=True)
    else:
        st.info("暂无操作记录")

# 数据上传页面
elif page == "数据上传":
    st.header("数据上传")
    
    tab1, tab2, tab3 = st.tabs(["客诉数据", "出货数据", "SN数据库"])
    
    with tab1:
        st.subheader("上传客诉数据")
        st.markdown("支持Excel或CSV格式，每周更新")
        
        uploaded_file = st.file_uploader(
            "选择客诉数据文件",
            type=['xlsx', 'xls', 'csv'],
            key="complaint_upload"
        )
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                st.success(f"成功读取数据: {len(df)} 行 × {len(df.columns)} 列")
                
                # 显示数据预览
                with st.expander("数据预览"):
                    st.dataframe(df.head(10), use_container_width=True)
                
                # 显示数据信息
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("数据行数", len(df))
                with col2:
                    st.metric("数据列数", len(df.columns))
                
                # 保存到Session State
                st.session_state.current_data['raw_complaints'] = df
                
                # 上传到数据库按钮
                if st.button("上传到数据库", type="primary"):
                    with st.spinner("上传数据中..."):
                        success, message = st.session_state.db.upload_complaint_data(df)
                        if success:
                            st.success(message)
                            # 记录操作
                            if 'operation_log' not in st.session_state:
                                st.session_state.operation_log = []
                            st.session_state.operation_log.append({
                                '时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                '操作': '上传客诉数据',
                                '记录数': len(df)
                            })
                        else:
                            st.error(f"上传失败: {message}")
            
            except Exception as e:
                st.error(f"读取文件时出错: {str(e)}")
    
    with tab2:
        st.subheader("上传出货数据")
        st.markdown("支持Excel或CSV格式，每月更新")
        
        uploaded_file = st.file_uploader(
            "选择出货数据文件",
            type=['xlsx', 'xls', 'csv'],
            key="shipment_upload"
        )
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                st.success(f"成功读取数据: {len(df)} 行 × {len(df.columns)} 列")
                
                with st.expander("数据预览"):
                    st.dataframe(df.head(10), use_container_width=True)
                
                # 保存到Session State
                st.session_state.current_data['raw_shipments'] = df
                
                if st.button("上传出货数据到数据库", type="primary"):
                    with st.spinner("上传数据中..."):
                        success, message = st.session_state.db.upload_shipment_data(df)
                        if success:
                            st.success(message)
                            if 'operation_log' not in st.session_state:
                                st.session_state.operation_log = []
                            st.session_state.operation_log.append({
                                '时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                '操作': '上传出货数据',
                                '记录数': len(df)
                            })
                        else:
                            st.error(f"上传失败: {message}")
            
            except Exception as e:
                st.error(f"读取文件时出错: {str(e)}")
    
    with tab3:
        st.subheader("上传SN数据库")
        st.markdown("上传SN数据库A（储能、组串、工商储）和B（微逆）")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("SN数据库A")
            uploaded_file_a = st.file_uploader(
                "选择SN数据库A文件",
                type=['xlsx', 'xls', 'csv'],
                key="sn_a_upload"
            )
            
            if uploaded_file_a is not None:
                try:
                    if uploaded_file_a.name.endswith('.csv'):
                        df_a = pd.read_csv(uploaded_file_a)
                    else:
                        df_a = pd.read_excel(uploaded_file_a)
                    
                    st.info(f"数据库A: {len(df_a)} 条记录")
                    st.session_state.current_data['sn_database_a'] = df_a
                except Exception as e:
                    st.error(f"读取文件时出错: {str(e)}")
        
        with col2:
            st.subheader("SN数据库B (微逆)")
            uploaded_file_b = st.file_uploader(
                "选择SN数据库B文件",
                type=['xlsx', 'xls', 'csv'],
                key="sn_b_upload"
            )
            
            if uploaded_file_b is not None:
                try:
                    if uploaded_file_b.name.endswith('.csv'):
                        df_b = pd.read_csv(uploaded_file_b)
                    else:
                        df_b = pd.read_excel(uploaded_file_b)
                    
                    st.info(f"数据库B: {len(df_b)} 条记录")
                    st.session_state.current_data['sn_database_b'] = df_b
                except Exception as e:
                    st.error(f"读取文件时出错: {str(e)}")
        
        # 上传按钮
        if ('sn_database_a' in st.session_state.current_data or 
            'sn_database_b' in st.session_state.current_data):
            
            df_a = st.session_state.current_data.get('sn_database_a')
            df_b = st.session_state.current_data.get('sn_database_b')
            
            if st.button("上传SN数据库", type="primary"):
                with st.spinner("上传数据中..."):
                    success, message = st.session_state.db.upload_sn_database(df_a, df_b)
                    if success:
                        st.success(message)
                        # 加载到处理器
                        st.session_state.processor.load_sn_databases(df_a, df_b)
                        
                        if 'operation_log' not in st.session_state:
                            st.session_state.operation_log = []
                        total_records = (len(df_a) if df_a is not None else 0) + (len(df_b) if df_b is not None else 0)
                        st.session_state.operation_log.append({
                            '时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            '操作': '上传SN数据库',
                            '记录数': total_records
                        })
                    else:
                        st.error(f"上传失败: {message}")

# 数据处理页面
elif page == "数据处理":
    st.header("数据处理")
    
    # 检查是否有原始数据
    if 'raw_complaints' not in st.session_state.current_data:
        st.warning("请先上传客诉数据")
        st.stop()
    
    raw_df = st.session_state.current_data['raw_complaints']
    
    st.subheader("原始数据概览")
    st.dataframe(raw_df.head(), use_container_width=True)
    
    # 数据处理选项
    st.subheader("数据处理选项")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        clean_data = st.checkbox("数据清洗与增强", value=True, 
                                help="执行SN解析、机型纠错、信息补全等")
    
    with col2:
        classify_data = st.checkbox("自动分类", value=True,
                                   help="根据规则自动分类客诉问题")
    
    with col3:
        enrich_with_sn = st.checkbox("SN信息补充", value=True,
                                    help="使用SN数据库补充设备信息")
    
    # 开始处理按钮
    if st.button("开始数据处理", type="primary"):
        with st.spinner("处理数据中..."):
            # 第一步：数据清洗
            if clean_data:
                processed_df = st.session_state.processor.clean_complaint_data(raw_df)
                st.session_state.current_data['cleaned_complaints'] = processed_df
                
                with st.expander("数据清洗结果"):
                    st.dataframe(processed_df.head(), use_container_width=True)
                    st.metric("处理后列数", len(processed_df.columns))
            
            # 第二步：数据分类
            if classify_data:
                if 'cleaned_complaints' in st.session_state.current_data:
                    input_df = st.session_state.current_data['cleaned_complaints']
                else:
                    input_df = raw_df
                
                classified_df = st.session_state.processor.classify_complaints(input_df)
                st.session_state.current_data['classified_complaints'] = classified_df
                
                with st.expander("数据分类结果"):
                    if '问题分类' in classified_df.columns:
                        st.dataframe(classified_df[['SN', '问题描述', '问题分类', '告警代码']].head(), 
                                   use_container_width=True)
                        
                        # 显示分类分布
                        if not classified_df.empty:
                            class_dist = classified_df['问题分类'].value_counts()
                            fig = px.pie(values=class_dist.values, 
                                       names=class_dist.index,
                                       title="问题分类分布")
                            st.plotly_chart(fig, use_container_width=True)
            
            st.success("数据处理完成!")
            
            # 记录操作
            if 'operation_log' not in st.session_state:
                st.session_state.operation_log = []
            st.session_state.operation_log.append({
                '时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '操作': '数据处理',
                '记录数': len(raw_df)
            })
    
    # 显示当前处理后的数据
    if 'classified_complaints' in st.session_state.current_data:
        st.subheader("最终处理结果")
        
        final_df = st.session_state.current_data['classified_complaints']
        
        # 数据摘要
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总记录数", len(final_df))
        with col2:
            unique_machines = final_df['机型_标准化'].nunique() if '机型_标准化' in final_df.columns else 0
            st.metric("涉及机型", unique_machines)
        with col3:
            if '问题分类' in final_df.columns:
                unique_categories = final_df['问题分类'].nunique()
                st.metric("问题分类数", unique_categories)
        with col4:
            if '告警代码' in final_df.columns:
                alarm_codes = final_df['告警代码'].notna().sum()
                st.metric("告警代码数", alarm_codes)
        
        # 数据表格
        tab1, tab2, tab3 = st.tabs(["数据表格", "列信息", "数据统计"])
        
        with tab1:
            st.dataframe(final_df, use_container_width=True)
        
        with tab2:
            columns_info = []
            for col in final_df.columns:
                col_info = {
                    '列名': col,
                    '数据类型': str(final_df[col].dtype),
                    '非空值数': final_df[col].notna().sum(),
                    '空值数': final_df[col].isna().sum(),
                    '唯一值数': final_df[col].nunique()
                }
                columns_info.append(col_info)
            
            columns_df = pd.DataFrame(columns_info)
            st.dataframe(columns_df, use_container_width=True)
        
        with tab3:
            # 数值型列统计
            numeric_cols = final_df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                st.write("数值型列统计:")
                st.dataframe(final_df[numeric_cols].describe(), use_container_width=True)
        
        # 下载处理后的数据
        st.subheader("下载处理结果")
        
        csv = final_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="下载CSV格式",
            data=csv,
            file_name=f"processed_complaints_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

# 统计分析页面
elif page == "统计分析":
    st.header("统计分析")
    
    # 获取数据
    complaint_data = st.session_state.db.get_complaint_data()
    shipment_data = st.session_state.db.get_shipment_data()
    
    if complaint_data.empty:
        st.warning("暂无客诉数据，请先上传并处理数据")
        st.stop()
    
    if shipment_data.empty:
        st.warning("暂无出货数据，请先上传出货数据")
        st.stop()
    
    st.subheader("分析参数设置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 月份选择
        if '客诉时间' in complaint_data.columns:
            complaint_data['客诉时间'] = pd.to_datetime(complaint_data['客诉时间'], errors='coerce')
            available_months = complaint_data['客诉时间'].dt.to_period('M').unique()
            month_options = [str(m) for m in available_months] + ['全部月份']
        else:
            month_options = ['全部月份']
        
        selected_month = st.selectbox("选择月份", month_options, index=len(month_options)-1)
    
    with col2:
        # 机型选择
        if '机型_标准化' in complaint_data.columns:
            machine_types = complaint_data['机型_标准化'].unique().tolist()
            machine_options = ['全部机型'] + [str(m) for m in machine_types if pd.notna(m)]
        else:
            machine_options = ['全部机型']
        
        selected_machines = st.multiselect("选择机型", machine_options, default=['全部机型'])
    
    # 分析按钮
    if st.button("开始统计分析", type="primary"):
        with st.spinner("分析数据中..."):
            # 过滤数据
            analysis_complaints = complaint_data.copy()
            analysis_shipments = shipment_data.copy()
            
            if selected_month != '全部月份' and '客诉时间' in analysis_complaints.columns:
                target_month = pd.Period(selected_month)
                analysis_complaints = analysis_complaints[
                    analysis_complaints['客诉时间'].dt.to_period('M') == target_month
                ]
            
            if '全部机型' not in selected_machines and '机型_标准化' in analysis_complaints.columns:
                analysis_complaints = analysis_complaints[
                    analysis_complaints['机型_标准化'].isin(selected_machines)
                ]
                analysis_shipments = analysis_shipments[
                    analysis_shipments['机型_标准化'].isin(selected_machines)
                ]
            
            # 1. 计算不良率
            st.subheader("不良率统计")
            defect_stats = st.session_state.processor.calculate_defect_rate(
                analysis_complaints, analysis_shipments, selected_month, selected_machines
            )
            
            if not defect_stats.empty:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # 不良率图表
                    fig = px.bar(defect_stats, x='机型_标准化', y='不良率(%)',
                               title=f'{selected_month} 各机型不良率',
                               color='不良率(%)',
                               color_continuous_scale='RdYlGn_r')
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.dataframe(defect_stats, use_container_width=True)
                    
                    # 不良率摘要
                    avg_rate = defect_stats['不良率(%)'].mean()
                    max_rate = defect_stats['不良率(%)'].max()
                    min_rate = defect_stats['不良率(%)'].min()
                    
                    st.metric("平均不良率", f"{avg_rate:.2f}%")
                    st.metric("最高不良率", f"{max_rate:.2f}%")
                    st.metric("最低不良率", f"{min_rate:.2f}%")
            
            # 2. 集中性问题分析
            st.subheader("集中性问题分析")
            issue_stats, concentrated_issues, case_details = st.session_state.processor.analyze_concentrated_issues(
                analysis_complaints, selected_month, 
                selected_machines[0] if len(selected_machines) == 1 and selected_machines[0] != '全部机型' else None
            )
            
            if not issue_stats.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    # 问题分类分布图
                    fig = px.pie(issue_stats.reset_index(), 
                               values='问题数量', 
                               names='问题分类',
                               title='问题分类分布')
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.write("问题分类统计:")
                    st.dataframe(issue_stats, use_container_width=True)
                
                # 集中性问题详情
                if not concentrated_issues.empty:
                    st.subheader("集中性问题详情")
                    
                    for i, (issue, row) in enumerate(concentrated_issues.iterrows()):
                        with st.expander(f"{issue} - {int(row['问题数量'])} 例 ({row['占比(%)']}%)"):
                            st.write(f"**问题描述**: {issue}")
                            st.write(f"**问题数量**: {int(row['问题数量'])}")
                            st.write(f"**占比**: {row['占比(%)']}%")
                            st.write(f"**主要机型**: {row.get('机型_标准化', '未知')}")
                            
                            # 显示具体案例
                            if issue in case_details and not case_details[issue].empty:
                                st.write("**具体案例**:")
                                st.dataframe(case_details[issue], use_container_width=True)
            
            # 保存分析结果
            st.session_state.current_data['defect_stats'] = defect_stats
            st.session_state.current_data['issue_analysis'] = issue_stats
            st.session_state.current_data['concentrated_issues'] = concentrated_issues
            
            # 记录操作
            if 'operation_log' not in st.session_state:
                st.session_state.operation_log = []
            st.session_state.operation_log.append({
                '时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '操作': f'统计分析 ({selected_month})',
                '记录数': len(analysis_complaints)
            })
            
            st.success("统计分析完成!")

# 报告生成页面
elif page == "报告生成":
    st.header("报告生成")
    
    # 检查是否有分析结果
    if 'defect_stats' not in st.session_state.current_data:
        st.warning("请先进行统计分析")
        st.stop()
    
    st.subheader("报告配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        report_month = st.selectbox(
            "报告月份",
            options=["2024-01", "2024-02", "2024-03", "2024-04", "2024-05"],
            index=0
        )
    
    with col2:
        report_type = st.radio(
            "报告类型",
            options=["标准月报", "详细分析报告", "问题专项报告"],
            horizontal=True
        )
    
    # 报告内容选项
    st.subheader("报告内容")
    
    content_options = st.multiselect(
        "选择报告包含的内容",
        options=["总体概况", "不良率分析", "集中性问题", "趋势分析", "成本分析", "改进建议"],
        default=["总体概况", "不良率分析", "集中性问题"]
    )
    
    # 生成报告按钮
    if st.button("生成报告", type="primary"):
        with st.spinner("生成报告中..."):
            # 获取数据
            defect_stats = st.session_state.current_data.get('defect_stats', pd.DataFrame())
            issue_analysis = st.session_state.current_data.get('issue_analysis', pd.DataFrame())
            
            # 获取其他数据
            complaint_data = st.session_state.db.get_complaint_data()
            shipment_data = st.session_state.db.get_shipment_data()
            
            # 生成报告摘要
            report_summary = st.session_state.report_gen.create_monthly_report(
                report_month, defect_stats, issue_analysis, shipment_data, complaint_data
            )
            
            # 生成可视化图表
            figures = st.session_state.report_gen.create_visualizations(defect_stats, issue_analysis)
            
            # 显示报告预览
            st.subheader("报告预览")
            
            # 报告摘要
            st.write("### 报告摘要")
            summary_df = pd.DataFrame([report_summary]).T.reset_index()
            summary_df.columns = ['指标', '数值']
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            
            # 可视化图表
            st.write("### 关键图表")
            
            if figures:
                cols = st.columns(2)
                figure_keys = list(figures.keys())
                
                for i, fig_key in enumerate(figure_keys):
                    with cols[i % 2]:
                        st.plotly_chart(figures[fig_key], use_container_width=True)
            
            # 导出选项
            st.subheader("导出报告")
            
            export_col1, export_col2, export_col3 = st.columns(3)
            
            with export_col1:
                if st.button("导出Word格式"):
                    filename = f"客诉分析报告_{report_month}.docx"
                    output_file = st.session_state.report_gen.export_to_word(
                        report_summary, defect_stats, issue_analysis, filename
                    )
                    
                    with open(output_file, "rb") as file:
                        btn = st.download_button(
                            label="下载Word报告",
                            data=file,
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
            
            with export_col2:
                if st.button("导出PDF格式"):
                    filename = f"客诉分析报告_{report_month}.pdf"
                    output_file = st.session_state.report_gen.export_to_pdf(report_summary, filename)
                    
                    with open(output_file, "rb") as file:
                        btn = st.download_button(
                            label="下载PDF报告",
                            data=file,
                            file_name=filename,
                            mime="application/pdf"
                        )
            
            with export_col3:
                # 生成PPT报告按钮
                if st.button("导出PPT格式"):
                    st.info("PPT导出功能开发中...")
            
            # 记录操作
            if 'operation_log' not in st.session_state:
                st.session_state.operation_log = []
            st.session_state.operation_log.append({
                '时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '操作': f'生成报告 ({report_month})',
                '报告类型': report_type
            })

# 系统设置页面
elif page == "系统设置":
    st.header("系统设置")
    
    tab1, tab2, tab3 = st.tabs(["数据库配置", "规则设置", "用户管理"])
    
    with tab1:
        st.subheader("数据库连接配置")
        
        st.info("""
        配置Supabase数据库连接信息。
        可以在本地开发时使用模拟数据，或配置真实的Supabase连接。
        """)
        
        with st.form("db_config_form"):
            db_url = st.text_input("Supabase URL", value=st.secrets.get("supabase", {}).get("url", ""))
            db_key = st.text_input("Supabase Key", value=st.secrets.get("supabase", {}).get("key", ""), type="password")
            
            submitted = st.form_submit_button("保存配置")
            if submitted:
                st.success("配置已保存 (实际部署时需配置环境变量)")
    
    with tab2:
        st.subheader("分类规则设置")
        
        st.info("设置客诉问题的分类规则。")
        
        # 默认分类规则
        default_rules = {
            '硬件故障': ['损坏', '故障', '不工作', '无响应', '短路', '断路', '烧坏'],
            '软件问题': ['程序', '软件', '固件', '升级', '版本', 'bug', '死机', '卡顿'],
            '安装问题': ['安装', '接线', '连接', '配置', '设置', '调试'],
            '性能问题': ['效率低', '功率不足', '过热', '噪音', '振动', '不稳定'],
            '外观问题': ['划伤', '变形', '颜色', '外观', '掉漆', '破损'],
            '其他': []
        }
        
        # 编辑分类规则
        st.write("### 当前分类规则")
        
        categories = list(default_rules.keys())
        selected_category = st.selectbox("选择分类", categories)
        
        if selected_category:
            current_keywords = default_rules[selected_category]
            new_keywords = st.text_area(
                f"{selected_category} 关键词",
                value="\n".join(current_keywords),
                height=150
            )
            
            if st.button("更新规则"):
                updated_keywords = [k.strip() for k in new_keywords.split('\n') if k.strip()]
                default_rules[selected_category] = updated_keywords
                st.success(f"已更新 {selected_category} 的分类规则")
        
        # 添加新分类
        st.write("### 添加新分类")
        
        col1, col2 = st.columns(2)
        with col1:
            new_category = st.text_input("新分类名称")
        with col2:
            new_category_keywords = st.text_input("关键词 (用逗号分隔)")
        
        if st.button("添加分类") and new_category:
            keywords = [k.strip() for k in new_category_keywords.split(',') if k.strip()]
            default_rules[new_category] = keywords
            st.success(f"已添加分类: {new_category}")
    
    with tab3:
        st.subheader("用户管理")
        st.info("当前版本为原型系统，用户管理功能将在正式版本中实现。")

# 页脚
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
    AI客诉数据分析系统 - 原型版本 v1.0<br>
    技术支持: 云平台AI开发部/AI组<br>
    更新时间: 2024年1月
    </div>
    """,
    unsafe_allow_html=True
)
