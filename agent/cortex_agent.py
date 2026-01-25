"""
Cortex Agent - 数据源和语义模型配置中心
Snowflake China Region
"""

import json
import pandas as pd
import streamlit as st
from datetime import datetime
from typing import Any, Dict, List, Optional

# 设置页面配置
st.set_page_config(
    layout="wide",
    page_icon="🤖",
    page_title="Cortex Agent",
    initial_sidebar_state="expanded"
)

# ===============================
# Dashscope 模型列表
# ===============================
DASHSCOPE_MODELS = {
    "通义千问系列": {
        "qwen-max": "Qwen-Max (最强大，适合复杂任务)",
        "qwen-max-longcontext": "Qwen-Max 长文本 (支持30K上下文)",
        "qwen-plus": "Qwen-Plus (性价比高)",
        "qwen-turbo": "Qwen-Turbo (快速响应)",
        "qwen-long": "Qwen-Long (超长文本)",
    },
    "通义千问2.5系列": {
        "qwen2.5-72b-instruct": "Qwen2.5-72B (开源最强)",
        "qwen2.5-32b-instruct": "Qwen2.5-32B",
        "qwen2.5-14b-instruct": "Qwen2.5-14B",
        "qwen2.5-7b-instruct": "Qwen2.5-7B",
    },
    "通义千问代码系列": {
        "qwen2.5-coder-32b-instruct": "Qwen2.5-Coder-32B (代码专家)",
        "qwen2.5-coder-14b-instruct": "Qwen2.5-Coder-14B",
        "qwen2.5-coder-7b-instruct": "Qwen2.5-Coder-7B",
    },
    "DeepSeek系列": {
        "deepseek-v3": "DeepSeek-V3 (最新)",
        "deepseek-r1": "DeepSeek-R1 (推理增强)",
        "deepseek-r1-distill-qwen-32b": "DeepSeek-R1-Distill-32B",
    }
}

# 扁平化模型列表
ALL_MODELS = {}
for category, models in DASHSCOPE_MODELS.items():
    ALL_MODELS.update(models)

# ===============================
# 样式定义 - 支持 Light/Dark 主题
# ===============================
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Sans+SC:wght@300;400;500;700&display=swap');

/* 主容器 - 适配两种主题 */
.main-header {
    text-align: center;
    padding: 2rem 0;
    margin-bottom: 2rem;
}

.main-title {
    font-size: 2.5rem;
    font-weight: 700;
    background: linear-gradient(135deg, #29B5E8 0%, #0068C9 50%, #7B2CBF 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.5rem;
}

.subtitle {
    font-size: 1.1rem;
    opacity: 0.7;
}

/* 配置卡片 */
.config-card {
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1rem 0;
    border: 1px solid rgba(128, 128, 128, 0.2);
    background: rgba(128, 128, 128, 0.05);
}

.config-card h3 {
    margin-top: 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* 状态徽章 */
.status-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 500;
}

.status-success {
    background: rgba(0, 200, 83, 0.2);
    color: #00C853;
    border: 1px solid rgba(0, 200, 83, 0.3);
}

.status-warning {
    background: rgba(255, 152, 0, 0.2);
    color: #FF9800;
    border: 1px solid rgba(255, 152, 0, 0.3);
}

.status-info {
    background: rgba(41, 181, 232, 0.2);
    color: #29B5E8;
    border: 1px solid rgba(41, 181, 232, 0.3);
}

/* 模型选择卡片 */
.model-card {
    border-radius: 8px;
    padding: 1rem;
    margin: 0.5rem 0;
    border: 1px solid rgba(128, 128, 128, 0.2);
    cursor: pointer;
    transition: all 0.2s ease;
}

.model-card:hover {
    border-color: #29B5E8;
    background: rgba(41, 181, 232, 0.1);
}

.model-card.selected {
    border-color: #29B5E8;
    background: rgba(41, 181, 232, 0.15);
}

/* 语义模型预览 */
.yaml-preview {
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 0.85rem;
    line-height: 1.5;
    max-height: 400px;
    overflow-y: auto;
    border-radius: 8px;
    padding: 1rem;
    background: rgba(0, 0, 0, 0.05);
}

/* 配置摘要 */
.config-summary {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin: 1rem 0;
}

.summary-item {
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid rgba(128, 128, 128, 0.2);
    background: rgba(128, 128, 128, 0.05);
}

.summary-label {
    font-size: 0.85rem;
    opacity: 0.7;
    margin-bottom: 0.25rem;
}

.summary-value {
    font-size: 1.1rem;
    font-weight: 600;
}
</style>
"""

# ===============================
# Snowflake 连接
# ===============================
def get_snowflake_connection():
    """获取 Snowflake 连接"""
    try:
        from snowflake.snowpark.context import get_active_session
        session = get_active_session()
        return session.connection
    except Exception:
        return None

def get_snowpark_session():
    """获取 Snowpark Session"""
    try:
        from snowflake.snowpark.context import get_active_session
        return get_active_session()
    except Exception:
        return None

# ===============================
# 数据库操作
# ===============================
@st.cache_data(ttl=300)
def fetch_databases(_conn) -> List[str]:
    """获取可用数据库列表"""
    if not _conn:
        return []
    cursor = _conn.cursor()
    cursor.execute("SHOW DATABASES")
    return [row[1] for row in cursor.fetchall()]

@st.cache_data(ttl=300)
def fetch_schemas(_conn, database: str) -> List[str]:
    """获取指定数据库的 Schema 列表"""
    if not _conn:
        return []
    cursor = _conn.cursor()
    cursor.execute(f"SHOW SCHEMAS IN DATABASE {database}")
    return [f"{database}.{row[1]}" for row in cursor.fetchall()]

@st.cache_data(ttl=300)
def fetch_tables(_conn, schema: str) -> List[str]:
    """获取指定 Schema 的表列表"""
    if not _conn:
        return []
    cursor = _conn.cursor()
    cursor.execute(f"SHOW TABLES IN {schema}")
    tables = [f"{schema}.{row[1]}" for row in cursor.fetchall()]
    cursor.execute(f"SHOW VIEWS IN {schema}")
    views = [f"{schema}.{row[1]}" for row in cursor.fetchall()]
    return tables + views

@st.cache_data(ttl=300)
def fetch_stages(_conn, schema: str) -> List[str]:
    """获取指定 Schema 的 Stage 列表"""
    if not _conn:
        return []
    cursor = _conn.cursor()
    cursor.execute(f"SHOW STAGES IN {schema}")
    return [f"{schema}.{row[1]}" for row in cursor.fetchall()]

def list_yaml_files_in_stage(conn, stage_name: str) -> List[str]:
    """列出 Stage 中的 YAML 文件"""
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(f"LIST @{stage_name}")
        files = []
        for row in cursor.fetchall():
            file_name = row[0]
            if file_name.endswith('.yaml') or file_name.endswith('.yml'):
                files.append(file_name)
        return files
    except Exception:
        return []

def load_semantic_model_from_stage(stage_path: str) -> Optional[str]:
    """从 Stage 加载语义模型 YAML"""
    try:
        session = get_snowpark_session()
        if session:
            yaml_content = session.file.get_stream(stage_path).read().decode('utf-8')
            return yaml_content
    except Exception as e:
        st.warning(f"无法加载语义模型: {e}")
    return None

def get_current_user(conn) -> str:
    """获取当前用户名"""
    if not conn:
        return "用户"
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_USER()")
        return cursor.fetchone()[0]
    except Exception:
        return "用户"

# ===============================
# 配置管理
# ===============================
def save_agent_config():
    """保存 Agent 配置到 session state"""
    config = {
        "database": st.session_state.get("agent_database"),
        "schema": st.session_state.get("agent_schema"),
        "stage": st.session_state.get("agent_stage"),
        "semantic_model_file": st.session_state.get("agent_semantic_model_file"),
        "semantic_model_content": st.session_state.get("agent_semantic_model_content"),
        "llm_model": st.session_state.get("agent_llm_model", "qwen-max"),
        "tables": st.session_state.get("agent_tables", []),
    }
    st.session_state["agent_config"] = config
    return config

def load_agent_config() -> Dict:
    """加载 Agent 配置"""
    return st.session_state.get("agent_config", {})

# ===============================
# 主应用
# ===============================
def main():
    # 注入自定义样式
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    # 标题
    st.markdown("""
    <div class="main-header">
        <div class="main-title">🤖 Cortex Agent</div>
        <div class="subtitle">数据源与语义模型配置中心</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 获取连接
    conn = get_snowflake_connection()
    
    if not conn:
        st.warning("⚠️ 未检测到 Snowflake 连接，部分功能可能不可用")
    
    # 初始化 session state
    if "agent_database" not in st.session_state:
        st.session_state.agent_database = None
    if "agent_schema" not in st.session_state:
        st.session_state.agent_schema = None
    if "agent_stage" not in st.session_state:
        st.session_state.agent_stage = None
    if "agent_semantic_model_file" not in st.session_state:
        st.session_state.agent_semantic_model_file = None
    if "agent_semantic_model_content" not in st.session_state:
        st.session_state.agent_semantic_model_content = None
    if "agent_llm_model" not in st.session_state:
        st.session_state.agent_llm_model = "qwen-max"
    if "agent_tables" not in st.session_state:
        st.session_state.agent_tables = []
    
    # 布局：左侧配置摘要，右侧详细配置
    col_summary, col_config = st.columns([1, 2])
    
    # ===== 左侧：配置摘要和模型选择 =====
    with col_summary:
        st.markdown("### 📊 当前配置")
        
        # 配置状态
        config = load_agent_config()
        
        # 数据源状态
        if st.session_state.agent_database and st.session_state.agent_schema:
            st.markdown(f"""
            <div class="config-card">
                <h4>🗄️ 数据源</h4>
                <p><span class="status-badge status-success">✓ 已配置</span></p>
                <p><strong>数据库:</strong> {st.session_state.agent_database}</p>
                <p><strong>Schema:</strong> {st.session_state.agent_schema.split('.')[-1] if st.session_state.agent_schema else '-'}</p>
                <p><strong>表数量:</strong> {len(st.session_state.agent_tables)}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="config-card">
                <h4>🗄️ 数据源</h4>
                <p><span class="status-badge status-warning">⚠ 未配置</span></p>
                <p>请在右侧配置数据源</p>
            </div>
            """, unsafe_allow_html=True)
        
        # 语义模型状态
        if st.session_state.agent_semantic_model_content:
            st.markdown(f"""
            <div class="config-card">
                <h4>📚 语义模型</h4>
                <p><span class="status-badge status-success">✓ 已加载</span></p>
                <p><strong>文件:</strong> {st.session_state.agent_semantic_model_file or '已加载'}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="config-card">
                <h4>📚 语义模型</h4>
                <p><span class="status-badge status-warning">⚠ 未加载</span></p>
                <p>请在右侧选择语义模型</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ===== 大模型选择 =====
        st.markdown("### 🧠 大模型选择")
        
        # 模型分类选择
        model_category = st.selectbox(
            "模型系列",
            options=list(DASHSCOPE_MODELS.keys()),
            key="model_category"
        )
        
        # 具体模型选择
        category_models = DASHSCOPE_MODELS[model_category]
        selected_model = st.selectbox(
            "选择模型",
            options=list(category_models.keys()),
            format_func=lambda x: category_models[x],
            key="model_selector"
        )
        
        if selected_model != st.session_state.agent_llm_model:
            st.session_state.agent_llm_model = selected_model
        
        # 显示当前选中的模型
        st.markdown(f"""
        <div class="config-card">
            <h4>当前模型</h4>
            <p><strong>{selected_model}</strong></p>
            <p style="font-size: 0.9rem; opacity: 0.8;">{category_models[selected_model]}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 模型说明
        with st.expander("💡 模型选择建议"):
            st.markdown("""
            **推荐场景：**
            - **复杂分析**: qwen-max, deepseek-v3
            - **日常查询**: qwen-plus, qwen-turbo
            - **代码生成**: qwen2.5-coder 系列
            - **推理任务**: deepseek-r1
            - **长文本**: qwen-max-longcontext, qwen-long
            """)
    
    # ===== 右侧：详细配置 =====
    with col_config:
        tab1, tab2, tab3 = st.tabs(["🗄️ 数据源配置", "📚 语义模型", "⚙️ 高级设置"])
        
        # ===== Tab 1: 数据源配置 =====
        with tab1:
            st.markdown("### 数据源配置")
            st.markdown("选择要分析的数据库、Schema 和数据表。")
            
            # 数据库选择
            databases = fetch_databases(conn) if conn else []
            selected_db = st.selectbox(
                "选择数据库",
                options=databases,
                index=databases.index(st.session_state.agent_database) if st.session_state.agent_database in databases else 0,
                key="db_select"
            )
            
            if selected_db != st.session_state.agent_database:
                st.session_state.agent_database = selected_db
                st.session_state.agent_schema = None
                st.session_state.agent_tables = []
            
            # Schema 选择
            schemas = fetch_schemas(conn, selected_db) if conn and selected_db else []
            if schemas:
                selected_schema = st.selectbox(
                    "选择 Schema",
                    options=schemas,
                    format_func=lambda x: x.split(".")[-1],
                    index=schemas.index(st.session_state.agent_schema) if st.session_state.agent_schema in schemas else 0,
                    key="schema_select"
                )
                
                if selected_schema != st.session_state.agent_schema:
                    st.session_state.agent_schema = selected_schema
                    st.session_state.agent_tables = []
            
            # 表列表
            if st.session_state.agent_schema:
                tables = fetch_tables(conn, st.session_state.agent_schema)
                if tables:
                    st.markdown("#### 可用数据表")
                    
                    # 显示表列表
                    selected_tables = st.multiselect(
                        "选择要包含的表（可多选）",
                        options=tables,
                        default=st.session_state.agent_tables if st.session_state.agent_tables else tables[:5],
                        format_func=lambda x: x.split(".")[-1],
                        key="table_select"
                    )
                    st.session_state.agent_tables = selected_tables
                    
                    st.info(f"已选择 {len(selected_tables)} 张表")
        
        # ===== Tab 2: 语义模型 =====
        with tab2:
            st.markdown("### 语义模型配置")
            st.markdown("从 Stage 中选择使用 Semantic Model Generator 生成的语义模型。")
            
            if st.session_state.agent_schema:
                # Stage 选择
                stages = fetch_stages(conn, st.session_state.agent_schema) if conn else []
                
                if stages:
                    selected_stage = st.selectbox(
                        "选择 Stage",
                        options=stages,
                        format_func=lambda x: x.split(".")[-1],
                        key="stage_select"
                    )
                    st.session_state.agent_stage = selected_stage
                    
                    # YAML 文件列表
                    yaml_files = list_yaml_files_in_stage(conn, selected_stage)
                    
                    if yaml_files:
                        selected_yaml = st.selectbox(
                            "选择语义模型文件",
                            options=yaml_files,
                            format_func=lambda x: x.split("/")[-1],
                            key="yaml_select"
                        )
                        
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.button("📥 加载语义模型", type="primary", use_container_width=True):
                                with st.spinner("加载中..."):
                                    file_name = selected_yaml.split("/")[-1]
                                    yaml_content = load_semantic_model_from_stage(f"@{selected_stage}/{file_name}")
                                    if yaml_content:
                                        st.session_state.agent_semantic_model_content = yaml_content
                                        st.session_state.agent_semantic_model_file = file_name
                                        st.success(f"✅ 已加载语义模型: {file_name}")
                                        st.rerun()
                        
                        with col2:
                            if st.session_state.agent_semantic_model_content:
                                if st.button("🗑️ 卸载语义模型", use_container_width=True):
                                    st.session_state.agent_semantic_model_content = None
                                    st.session_state.agent_semantic_model_file = None
                                    st.rerun()
                    else:
                        st.warning("该 Stage 中没有 YAML 文件。请先使用 Semantic Model Generator 生成语义模型。")
                else:
                    st.warning("当前 Schema 中没有 Stage。请先创建 Stage 并上传语义模型。")
            else:
                st.info("请先在「数据源配置」中选择数据库和 Schema。")
            
            # 语义模型预览
            if st.session_state.agent_semantic_model_content:
                st.markdown("---")
                st.markdown("#### 📄 语义模型预览")
                with st.expander("查看完整 YAML", expanded=False):
                    st.code(st.session_state.agent_semantic_model_content, language="yaml")
        
        # ===== Tab 3: 高级设置 =====
        with tab3:
            st.markdown("### 高级设置")
            
            # API 配置
            st.markdown("#### 🔑 API 配置")
            st.info("API Key 已通过 External Access Integration 配置，无需手动设置。")
            
            # 模型参数
            st.markdown("#### 🎛️ 模型参数")
            
            col1, col2 = st.columns(2)
            with col1:
                temperature = st.slider(
                    "Temperature (创造性)",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.7,
                    step=0.1,
                    key="temperature"
                )
            
            with col2:
                max_tokens = st.slider(
                    "Max Tokens (最大长度)",
                    min_value=256,
                    max_value=4096,
                    value=2048,
                    step=256,
                    key="max_tokens"
                )
            
            # 保存到 session state
            st.session_state["agent_temperature"] = temperature
            st.session_state["agent_max_tokens"] = max_tokens
    
    # ===== 底部：保存配置 =====
    st.markdown("---")
    
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("💾 保存配置", type="primary", use_container_width=True):
            config = save_agent_config()
            st.success("✅ 配置已保存！")
            st.json(config)
    
    # 配置状态检查
    st.markdown("---")
    st.markdown("### ✅ 配置状态检查")
    
    checks = [
        ("数据源", bool(st.session_state.agent_database and st.session_state.agent_schema)),
        ("数据表", len(st.session_state.agent_tables) > 0),
        ("语义模型", bool(st.session_state.agent_semantic_model_content)),
        ("大模型", bool(st.session_state.agent_llm_model)),
    ]
    
    cols = st.columns(len(checks))
    all_ready = True
    for col, (name, status) in zip(cols, checks):
        with col:
            if status:
                st.success(f"✅ {name}")
            else:
                st.warning(f"⚠️ {name}")
                all_ready = False
    
    if all_ready:
        st.success("🎉 所有配置已就绪！可以在 Snowflake China Intelligence 中使用。")
    else:
        st.info("💡 完成以上配置后，即可在 Snowflake China Intelligence 中进行智能数据分析。")


if __name__ == "__main__":
    main()
