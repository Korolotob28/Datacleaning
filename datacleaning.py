# app_streamlit.py - 保存这个文件
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO, BytesIO
import base64

# 页面配置
st.set_page_config(
    page_title="🧬 数据矩阵交互分析平台",
    page_icon="🧬",
    layout="wide"
)

# 标题
st.title("🧬 数据矩阵交互分析平台")
st.markdown("支持CSV、Excel、TXT格式 | 智能数据处理 | 拖拽式分析")

# 初始化session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'original_df' not in st.session_state:
    st.session_state.original_df = None

# ==================== 侧边栏：数据导入 ====================
with st.sidebar:
    st.header("📥 数据导入")
    
    uploaded_file = st.file_uploader(
        "上传CSV、Excel或TXT文件",
        type=['csv', 'xlsx', 'txt'],
        help="支持CSV、Excel (.xlsx) 和TXT格式"
    )
    
    if uploaded_file is not None:
        col1, col2 = st.columns(2)
        with col1:
            encoding = st.selectbox("编码", ['utf-8', 'gbk', 'gb2312'], index=0)
        with col2:
            separator = st.selectbox("分隔符", [',', '\t', ';', ' '], index=0)
        
        try:
            # 读取文件
            if uploaded_file.name.endswith('.csv') or uploaded_file.name.endswith('.txt'):
                df = pd.read_csv(uploaded_file, encoding=encoding, sep=separator)
            elif uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            
            # 处理空值
            df = df.replace(['', 'NA', 'NULL'], np.nan)
            
            st.session_state.df = df.copy()
            st.session_state.original_df = df.copy()
            
            st.success(f"✅ 成功加载: {len(df)}行 × {len(df.columns)}列")
            st.info(f"文件: {uploaded_file.name}")
            
        except Exception as e:
            st.error(f"加载失败: {str(e)}")

# ==================== 主界面 ====================
if st.session_state.df is not None:
    df = st.session_state.df
    
    # Tab布局
    tab1, tab2, tab3, tab4 = st.tabs(["📊 数据浏览", "🛠️ 数据操作", "📈 数据分析", "💾 数据导出"])
    
    # ===== Tab 1: 数据浏览 =====
    with tab1:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("数据摘要")
            st.metric("总行数", len(df))
            st.metric("总列数", len(df.columns))
            st.metric("缺失值总数", df.isnull().sum().sum())
            
            st.subheader("列数据类型")
            for col in df.columns:
                dtype = df[col].dtype
                nulls = df[col].isnull().sum()
                st.text(f"• {col}: {dtype} (空值: {nulls})")
        
        with col2:
            st.subheader("数据预览")
            st.dataframe(df.head(20), use_container_width=True)
            
            # 缺失值可视化
            missing_df = pd.DataFrame({
                '列名': df.columns,
                '缺失值数量': df.isnull().sum()
            })
            fig = px.bar(missing_df, x='列名', y='缺失值数量', 
                        title='各列缺失值分布', color='缺失值数量')
            st.plotly_chart(fig, use_container_width=True)
    
    # ===== Tab 2: 数据操作 =====
    with tab2:
        st.subheader("行列管理")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**设置行名**")
            row_col = st.selectbox("选择列作为行名", ['无'] + list(df.columns), key='row_name')
            if st.button("✅ 应用行名", key='apply_row'):
                if row_col != '无' and row_col in df.columns:
                    df.set_index(row_col, inplace=True)
                    st.session_state.df = df
                    st.success(f"已将 '{row_col}' 设为行名")
                    st.rerun()
        
        with col2:
            st.markdown("**设置列名**")
            row_idx = st.number_input("选择行号作为列名", min_value=0, max_value=len(df)-1, step=1, key='col_name')
            if st.button("✅ 应用列名", key='apply_col'):
                new_columns = df.iloc[row_idx].values
                df.columns = new_columns
                df = df.drop(index=row_idx)
                st.session_state.df = df
                st.success(f"已将第{row_idx}行设为列名")
                st.rerun()
        
        with col3:
            st.markdown("**新增行列**")
            new_name = st.text_input("名称", key='new_name')
            new_type = st.selectbox("类型", ['numeric', 'character', 'logical'], key='new_type')
            
            if st.button("➕ 新增行", key='add_row'):
                new_row = {col: 0 if new_type == 'numeric' else '' for col in df.columns}
                df.loc[new_name or f'row_{len(df)}'] = new_row
                st.session_state.df = df
                st.success(f"已添加行: {new_name}")
                st.rerun()
            
            if st.button("➕ 新增列", key='add_col'):
                df[new_name or f'col_{len(df.columns)}'] = 0 if new_type == 'numeric' else ''
                st.session_state.df = df
                st.success(f"已添加列: {new_name}")
                st.rerun()
        
        # 显示当前数据
        st.subheader("当前数据矩阵")
        st.dataframe(df, use_container_width=True, height=400)
    
    # ===== Tab 3: 数据分析 =====
    with tab3:
        st.subheader("统计分析")
        
        # 选择数值型变量
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if numeric_cols:
            selected_vars = st.multiselect("选择分析变量", numeric_cols, default=numeric_cols[:min(3, len(numeric_cols))])
            analysis_type = st.selectbox(
                "分析类型",
                ['描述性统计', '相关性矩阵', '分布直方图', '箱线图', '热力图']
            )
            
            if st.button("🔍 执行分析"):
                if selected_vars:
                    if analysis_type == '描述性统计':
                        st.dataframe(df[selected_vars].describe().round(2))
                    
                    elif analysis_type == '相关性矩阵':
                        corr = df[selected_vars].corr()
                        st.dataframe(corr.round(3))
                        fig = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r')
                        st.plotly_chart(fig, use_container_width=True)
                    
                    elif analysis_type == '分布直方图':
                        for var in selected_vars[:2]:  # 最多显示2个
                            fig = px.histogram(df, x=var, title=f'{var} 分布')
                            st.plotly_chart(fig, use_container_width=True)
                    
                    elif analysis_type == '箱线图':
                        if len(selected_vars) >= 2:
                            melted = df[selected_vars].melt(var_name='变量', value_name='值')
                            fig = px.box(melted, x='变量', y='值')
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            fig = px.box(df, y=selected_vars[0])
                            st.plotly_chart(fig, use_container_width=True)
                    
                    elif analysis_type == '热力图':
                        fig = px.imshow(df[selected_vars].T, aspect='auto', color_continuous_scale='Viridis')
                        st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("数据中没有数值型列，无法进行统计分析")
    
    # ===== Tab 4: 数据导出 =====
    with tab4:
        st.subheader("导出处理后的数据")
        
        col1, col2 = st.columns(2)
        with col1:
            export_format = st.selectbox("导出格式", ['CSV', 'Excel', 'TSV'])
        with col2:
            include_index = st.checkbox("包含行名", value=True)
        
        if st.button("📥 下载数据"):
            if export_format == 'CSV':
                csv = df.to_csv(index=include_index)
                st.download_button(
                    label="点击下载 CSV",
                    data=csv,
                    file_name="processed_data.csv",
                    mime="text/csv"
                )
            elif export_format == 'Excel':
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=include_index)
                st.download_button(
                    label="点击下载 Excel",
                    data=output.getvalue(),
                    file_name="processed_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            elif export_format == 'TSV':
                tsv = df.to_csv(index=include_index, sep='\t')
                st.download_button(
                    label="点击下载 TSV",
                    data=tsv,
                    file_name="processed_data.tsv",
                    mime="text/tab-separated-values"
                )

else:
    st.info("👈 请从左侧边栏上传数据文件开始分析")

# 页脚
st.markdown("---")
st.markdown("🔬 数据矩阵交互分析平台 v2.0 | 基于Streamlit构建")