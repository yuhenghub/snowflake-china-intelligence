"""
Cortex Agent & Intelligence Demo App for Snowflake China Region
使用 Qwen API 模拟 Cortex Agent 和 Cortex Intelligence 功能
"""

import os
import json
import uuid
import pandas as pd
import streamlit as st
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
import plotly.express as px
import plotly.graph_objects as go

# 设置页面配置
st.set_page_config(
    layout="wide",
    page_icon="🤖",
    page_title="Cortex Agent & Intelligence",
    initial_sidebar_state="expanded"
)

# 自动检测中国区域
def _detect_china_region() -> bool:
    if os.environ.get("USE_QWEN_FOR_CHINA", "").lower() == "true":
        return True
    host = os.environ.get("SNOWFLAKE_HOST", "")
    if any(x in host.lower() for x in [".cn", "cn-", "china"]):
        return True
    return False

if _detect_china_region():
    os.environ["USE_QWEN_FOR_CHINA"] = "true"
    if not os.environ.get("QWEN_MODEL"):
        os.environ["QWEN_MODEL"] = "qwen-max"

from app_utils.shared_utils import (
    get_snowflake_connection,
    set_account_name,
    set_host_name,
    set_sit_query_tag,
    set_snowpark_session,
    set_streamlit_location,
    set_user_name,
    get_available_databases,
    get_available_schemas,
    get_available_tables,
)
from semantic_model_generator.snowflake_utils.env_vars import (
    SNOWFLAKE_ACCOUNT_LOCATOR,
    SNOWFLAKE_HOST,
    SNOWFLAKE_USER,
)

# ===============================
# 样式定义
# ===============================
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Noto+Sans+SC:wght@300;400;500;700&display=swap');

:root {
    --primary-gradient: linear-gradient(135deg, #00D4FF 0%, #7B2CBF 50%, #FF6B6B 100%);
    --card-bg: rgba(17, 25, 40, 0.75);
    --border-color: rgba(255, 255, 255, 0.125);
    --text-primary: #E8E8E8;
    --text-secondary: #A0A0A0;
    --accent-cyan: #00D4FF;
    --accent-purple: #7B2CBF;
    --accent-pink: #FF6B6B;
}

.main {
    background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 50%, #16213e 100%);
    font-family: 'Noto Sans SC', 'JetBrains Mono', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 50%, #16213e 100%);
}

/* 标题样式 */
.main-title {
    background: var(--primary-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 3rem;
    font-weight: 700;
    text-align: center;
    margin-bottom: 0.5rem;
    letter-spacing: -0.02em;
}

.subtitle {
    color: var(--text-secondary);
    text-align: center;
    font-size: 1.1rem;
    margin-bottom: 2rem;
}

/* 卡片样式 */
.feature-card {
    background: var(--card-bg);
    backdrop-filter: blur(16px);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 1.5rem;
    margin: 1rem 0;
    transition: all 0.3s ease;
}

.feature-card:hover {
    border-color: var(--accent-cyan);
    box-shadow: 0 8px 32px rgba(0, 212, 255, 0.15);
    transform: translateY(-2px);
}

/* Agent 消息样式 */
.agent-message {
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(123, 44, 191, 0.1) 100%);
    border-left: 3px solid var(--accent-cyan);
    border-radius: 0 12px 12px 0;
    padding: 1rem 1.25rem;
    margin: 0.75rem 0;
}

.user-message {
    background: rgba(255, 107, 107, 0.1);
    border-right: 3px solid var(--accent-pink);
    border-radius: 12px 0 0 12px;
    padding: 1rem 1.25rem;
    margin: 0.75rem 0;
    text-align: right;
}

/* 工具调用卡片 */
.tool-card {
    background: rgba(123, 44, 191, 0.15);
    border: 1px solid rgba(123, 44, 191, 0.3);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin: 0.5rem 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
}

/* 按钮样式 */
.stButton > button {
    background: var(--primary-gradient);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1.5rem;
    font-weight: 500;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: scale(1.02);
    box-shadow: 0 4px 20px rgba(0, 212, 255, 0.3);
}

/* 输入框样式 */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: rgba(17, 25, 40, 0.9);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    color: var(--text-primary);
}

/* 侧边栏样式 */
.css-1d391kg {
    background: rgba(17, 25, 40, 0.95);
}

/* 指标卡片 */
.metric-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 1.25rem;
    text-align: center;
}

.metric-value {
    font-size: 2rem;
    font-weight: 700;
    background: var(--primary-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.metric-label {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin-top: 0.25rem;
}

/* 数据表格样式 */
.dataframe {
    background: var(--card-bg) !important;
    border-radius: 8px;
}

/* 标签页样式 */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: transparent;
}

.stTabs [data-baseweb="tab"] {
    background: var(--card-bg);
    border-radius: 8px;
    border: 1px solid var(--border-color);
    color: var(--text-secondary);
}

.stTabs [aria-selected="true"] {
    background: var(--primary-gradient);
    color: white;
}

/* 动画效果 */
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.thinking {
    animation: pulse 1.5s infinite;
}
</style>
"""

# ===============================
# Qwen API 调用
# ===============================
QWEN_MODEL = os.environ.get("QWEN_MODEL", "qwen-max")

def call_qwen_udf(conn, model: str, prompt: str, system_prompt: str = None) -> str:
    """通过 Snowflake UDF 调用 Qwen API"""
    escaped_prompt = prompt.replace("'", "''").replace("\\", "\\\\")
    
    if system_prompt:
        full_prompt = f"[系统指令]: {system_prompt}\n\n[用户问题]: {escaped_prompt}"
    else:
        full_prompt = escaped_prompt
    
    query = f"SELECT CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.QWEN_COMPLETE('{model}', $${full_prompt}$$)"
    
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        if result and result[0]:
            return result[0]
        return ""
    except Exception as e:
        st.error(f"Qwen API 调用失败: {str(e)}")
        return f"错误: {str(e)}"


# ===============================
# 工具定义
# ===============================
class Tool:
    """工具基类"""
    def __init__(self, name: str, description: str, parameters: Dict):
        self.name = name
        self.description = description
        self.parameters = parameters
    
    def execute(self, conn, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError


class SQLQueryTool(Tool):
    """SQL 查询工具"""
    def __init__(self):
        super().__init__(
            name="execute_sql",
            description="执行 SQL 查询并返回结果。用于从 Snowflake 数据库查询数据。",
            parameters={
                "sql": {"type": "string", "description": "要执行的 SQL 查询语句"}
            }
        )
    
    def execute(self, conn, sql: str) -> Dict[str, Any]:
        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            df = pd.DataFrame(rows, columns=columns)
            return {
                "success": True,
                "data": df,
                "row_count": len(df),
                "columns": columns
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class DataAnalysisTool(Tool):
    """数据分析工具"""
    def __init__(self):
        super().__init__(
            name="analyze_data",
            description="对数据进行统计分析，包括描述性统计、分布分析等。",
            parameters={
                "data": {"type": "dataframe", "description": "要分析的数据"},
                "analysis_type": {"type": "string", "description": "分析类型: summary, distribution, correlation"}
            }
        )
    
    def execute(self, conn, data: pd.DataFrame, analysis_type: str = "summary") -> Dict[str, Any]:
        try:
            if analysis_type == "summary":
                return {
                    "success": True,
                    "analysis": data.describe().to_dict(),
                    "row_count": len(data),
                    "column_count": len(data.columns),
                    "dtypes": data.dtypes.astype(str).to_dict()
                }
            elif analysis_type == "distribution":
                numeric_cols = data.select_dtypes(include=['number']).columns
                distributions = {}
                for col in numeric_cols:
                    distributions[col] = {
                        "mean": data[col].mean(),
                        "median": data[col].median(),
                        "std": data[col].std(),
                        "min": data[col].min(),
                        "max": data[col].max()
                    }
                return {"success": True, "distributions": distributions}
            else:
                return {"success": True, "analysis": data.describe().to_dict()}
        except Exception as e:
            return {"success": False, "error": str(e)}


class VisualizationTool(Tool):
    """可视化工具"""
    def __init__(self):
        super().__init__(
            name="create_visualization",
            description="创建数据可视化图表。支持柱状图、折线图、饼图、散点图等。",
            parameters={
                "data": {"type": "dataframe", "description": "要可视化的数据"},
                "chart_type": {"type": "string", "description": "图表类型: bar, line, pie, scatter"},
                "x_column": {"type": "string", "description": "X轴列名"},
                "y_column": {"type": "string", "description": "Y轴列名"}
            }
        )
    
    def execute(self, conn, data: pd.DataFrame, chart_type: str, x_column: str, y_column: str = None) -> Dict[str, Any]:
        try:
            if chart_type == "bar":
                fig = px.bar(data, x=x_column, y=y_column, 
                            color_discrete_sequence=['#00D4FF'])
            elif chart_type == "line":
                fig = px.line(data, x=x_column, y=y_column,
                             color_discrete_sequence=['#7B2CBF'])
            elif chart_type == "pie":
                fig = px.pie(data, names=x_column, values=y_column,
                            color_discrete_sequence=px.colors.sequential.Plasma)
            elif chart_type == "scatter":
                fig = px.scatter(data, x=x_column, y=y_column,
                                color_discrete_sequence=['#FF6B6B'])
            else:
                fig = px.bar(data, x=x_column, y=y_column)
            
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#E8E8E8'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
            )
            
            return {"success": True, "figure": fig}
        except Exception as e:
            return {"success": False, "error": str(e)}


class TableInfoTool(Tool):
    """表信息查询工具"""
    def __init__(self):
        super().__init__(
            name="get_table_info",
            description="获取 Snowflake 表的元数据信息，包括列名、数据类型等。",
            parameters={
                "table_name": {"type": "string", "description": "完全限定的表名 (DATABASE.SCHEMA.TABLE)"}
            }
        )
    
    def execute(self, conn, table_name: str) -> Dict[str, Any]:
        try:
            cursor = conn.cursor()
            cursor.execute(f"DESC TABLE {table_name}")
            columns = cursor.fetchall()
            schema_info = [{"name": col[0], "type": col[1], "nullable": col[3]} for col in columns]
            
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            return {
                "success": True,
                "table_name": table_name,
                "columns": schema_info,
                "row_count": row_count
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# 注册所有工具
AVAILABLE_TOOLS = {
    "execute_sql": SQLQueryTool(),
    "analyze_data": DataAnalysisTool(),
    "create_visualization": VisualizationTool(),
    "get_table_info": TableInfoTool()
}


# ===============================
# Agent 核心逻辑
# ===============================
AGENT_SYSTEM_PROMPT = """你是一个专业的数据分析助手，运行在 Snowflake 环境中。你可以使用以下工具来帮助用户：

## 可用工具:

1. **execute_sql** - 执行 SQL 查询
   参数: sql (string) - SQL 查询语句

2. **get_table_info** - 获取表信息
   参数: table_name (string) - 完全限定的表名

3. **analyze_data** - 分析数据
   参数: analysis_type (string) - 分析类型 (summary/distribution/correlation)

4. **create_visualization** - 创建可视化
   参数: chart_type (string), x_column (string), y_column (string)

## 响应格式:

当需要调用工具时，请使用以下 JSON 格式：
```json
{
  "thought": "你的思考过程",
  "tool_call": {
    "name": "工具名称",
    "parameters": {
      "参数名": "参数值"
    }
  }
}
```

当不需要调用工具，直接回答时：
```json
{
  "thought": "你的思考过程",
  "response": "你的回答内容"
}
```

请确保：
1. SQL 查询必须是有效的 Snowflake SQL 语法
2. 在执行查询前先了解表结构
3. 给出清晰的分析和解释
4. 使用中文回答

当前上下文:
- 用户选择的数据库: {database}
- 用户选择的 Schema: {schema}
- 可用的表: {tables}
"""


def parse_agent_response(response: str) -> Dict[str, Any]:
    """解析 Agent 的响应"""
    # 尝试提取 JSON
    try:
        # 查找 JSON 块
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        
        # 尝试直接解析
        # 查找第一个 { 和最后一个 }
        start = response.find('{')
        end = response.rfind('}') + 1
        if start != -1 and end > start:
            return json.loads(response[start:end])
    except json.JSONDecodeError:
        pass
    
    # 如果无法解析，返回纯文本响应
    return {"response": response}


def run_agent(conn, user_input: str, context: Dict) -> Dict[str, Any]:
    """运行 Agent"""
    system_prompt = AGENT_SYSTEM_PROMPT.format(
        database=context.get("database", "未选择"),
        schema=context.get("schema", "未选择"),
        tables=", ".join(context.get("tables", [])[:10])  # 限制显示的表数量
    )
    
    # 构建消息历史
    messages = context.get("messages", [])
    history_text = ""
    for msg in messages[-6:]:  # 只保留最近6条消息
        role = "用户" if msg["role"] == "user" else "助手"
        history_text += f"\n{role}: {msg['content']}\n"
    
    full_prompt = f"{history_text}\n用户: {user_input}"
    
    response = call_qwen_udf(conn, QWEN_MODEL, full_prompt, system_prompt)
    parsed = parse_agent_response(response)
    
    return parsed


def execute_tool_call(conn, tool_name: str, parameters: Dict, context: Dict) -> Dict[str, Any]:
    """执行工具调用"""
    if tool_name not in AVAILABLE_TOOLS:
        return {"success": False, "error": f"未知工具: {tool_name}"}
    
    tool = AVAILABLE_TOOLS[tool_name]
    
    # 特殊处理某些工具
    if tool_name == "analyze_data" or tool_name == "create_visualization":
        # 这些工具需要先有数据
        if "last_query_result" in context and context["last_query_result"] is not None:
            parameters["data"] = context["last_query_result"]
        else:
            return {"success": False, "error": "没有可用的数据，请先执行查询"}
    
    return tool.execute(conn, **parameters)


# ===============================
# Intelligence 功能
# ===============================
def generate_data_insights(conn, df: pd.DataFrame, context: str = "") -> str:
    """使用 AI 生成数据洞察"""
    # 准备数据摘要
    summary = f"""
数据概览:
- 行数: {len(df)}
- 列数: {len(df.columns)}
- 列名: {', '.join(df.columns.tolist())}

数据统计:
{df.describe().to_string()}

前5行数据示例:
{df.head().to_string()}
"""
    
    prompt = f"""请分析以下数据并提供专业的商业洞察:

{summary}

{f"额外背景: {context}" if context else ""}

请提供:
1. 数据的关键发现 (3-5点)
2. 潜在的业务价值
3. 建议的后续分析方向
4. 需要注意的数据质量问题（如有）

请用专业但易懂的中文回答。
"""
    
    return call_qwen_udf(conn, QWEN_MODEL, prompt)


def suggest_questions(conn, tables: List[str], schema_info: Dict) -> List[str]:
    """根据表结构建议问题"""
    prompt = f"""基于以下数据表信息，建议5个有价值的数据分析问题:

可用表: {', '.join(tables[:5])}

表结构信息:
{json.dumps(schema_info, indent=2, ensure_ascii=False)}

请生成5个具体、可执行的数据分析问题，每行一个问题。
问题应该：
1. 涉及数据汇总和统计
2. 包含时间趋势分析（如适用）
3. 涉及不同维度的对比
4. 有实际的业务价值

只输出问题，不要编号，每行一个。
"""
    
    response = call_qwen_udf(conn, "qwen-turbo", prompt)
    questions = [q.strip() for q in response.strip().split('\n') if q.strip()]
    return questions[:5]


def generate_sql_from_question(conn, question: str, schema_info: Dict, tables: List[str]) -> str:
    """根据自然语言问题生成 SQL"""
    prompt = f"""请根据以下问题生成 Snowflake SQL 查询:

问题: {question}

可用表: {', '.join(tables)}

表结构信息:
{json.dumps(schema_info, indent=2, ensure_ascii=False)}

要求:
1. 生成有效的 Snowflake SQL
2. 只返回 SQL 语句，不要任何解释
3. 如果需要聚合，请使用适当的 GROUP BY
4. 限制返回结果数量（使用 LIMIT）
5. 使用完全限定的表名

SQL:
"""
    
    response = call_qwen_udf(conn, QWEN_MODEL, prompt)
    
    # 清理响应，提取 SQL
    sql = response.strip()
    if sql.startswith("```"):
        lines = sql.split("\n")
        sql_lines = []
        in_code = False
        for line in lines:
            if line.startswith("```"):
                in_code = not in_code
                continue
            if in_code or not line.startswith("```"):
                sql_lines.append(line)
        sql = "\n".join(sql_lines).strip()
    
    return sql


# ===============================
# UI 组件
# ===============================
def render_message(role: str, content: str, tool_info: Dict = None):
    """渲染聊天消息"""
    if role == "user":
        st.markdown(f'<div class="user-message">{content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="agent-message">{content}</div>', unsafe_allow_html=True)
        if tool_info:
            st.markdown(f"""
            <div class="tool-card">
                🔧 工具调用: <strong>{tool_info.get('name', 'unknown')}</strong><br>
                参数: {json.dumps(tool_info.get('parameters', {}), ensure_ascii=False)}
            </div>
            """, unsafe_allow_html=True)


def render_data_preview(df: pd.DataFrame, title: str = "数据预览"):
    """渲染数据预览"""
    st.markdown(f"### 📊 {title}")
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=min(400, 35 * len(df) + 38)
    )


def render_metrics_row(metrics: List[Dict]):
    """渲染指标行"""
    cols = st.columns(len(metrics))
    for col, metric in zip(cols, metrics):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{metric['value']}</div>
                <div class="metric-label">{metric['label']}</div>
            </div>
            """, unsafe_allow_html=True)


# ===============================
# 主应用
# ===============================
def main():
    # 注入自定义样式
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    # 标题
    st.markdown('<h1 class="main-title">🤖 Cortex Agent & Intelligence</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">基于 Qwen 的智能数据分析平台 | Snowflake China</p>', unsafe_allow_html=True)
    
    # 初始化 session state
    if "sis" not in st.session_state:
        st.session_state["sis"] = set_streamlit_location()
    
    if "agent_messages" not in st.session_state:
        st.session_state.agent_messages = []
    
    if "last_query_result" not in st.session_state:
        st.session_state.last_query_result = None
    
    if "selected_database" not in st.session_state:
        st.session_state.selected_database = None
    
    if "selected_schema" not in st.session_state:
        st.session_state.selected_schema = None
    
    if "available_tables" not in st.session_state:
        st.session_state.available_tables = []
    
    # 获取连接
    try:
        conn = get_snowflake_connection()
        set_snowpark_session(conn)
        set_account_name(conn, SNOWFLAKE_ACCOUNT_LOCATOR)
        set_host_name(conn, SNOWFLAKE_HOST)
        set_user_name(conn, SNOWFLAKE_USER)
    except Exception as e:
        st.error(f"无法连接到 Snowflake: {e}")
        st.info("请确保已正确配置 Snowflake 连接信息。")
        return
    
    # 侧边栏 - 数据源选择
    with st.sidebar:
        st.markdown("### 🗄️ 数据源配置")
        
        # 数据库选择
        databases = get_available_databases()
        selected_db = st.selectbox(
            "选择数据库",
            options=databases,
            index=databases.index(st.session_state.selected_database) if st.session_state.selected_database in databases else 0,
            key="db_selector"
        )
        
        if selected_db != st.session_state.selected_database:
            st.session_state.selected_database = selected_db
            st.session_state.selected_schema = None
            st.session_state.available_tables = []
        
        # Schema 选择
        if selected_db:
            try:
                schemas = get_available_schemas(selected_db)
                selected_schema = st.selectbox(
                    "选择 Schema",
                    options=schemas,
                    index=0,
                    key="schema_selector",
                    format_func=lambda x: x.split(".")[-1] if "." in x else x
                )
                
                if selected_schema != st.session_state.selected_schema:
                    st.session_state.selected_schema = selected_schema
                    # 获取表列表
                    try:
                        st.session_state.available_tables = get_available_tables(selected_schema)
                    except Exception:
                        st.session_state.available_tables = []
            except Exception:
                st.warning("无法获取 Schema 列表")
        
        # 显示可用表
        if st.session_state.available_tables:
            st.markdown("### 📋 可用数据表")
            for table in st.session_state.available_tables[:10]:
                table_name = table.split(".")[-1]
                st.markdown(f"- `{table_name}`")
            if len(st.session_state.available_tables) > 10:
                st.caption(f"... 还有 {len(st.session_state.available_tables) - 10} 张表")
        
        st.markdown("---")
        
        # 模型信息
        st.markdown("### 🧠 模型信息")
        st.info(f"当前使用模型: **{QWEN_MODEL}**")
        
        # 清除对话按钮
        if st.button("🗑️ 清除对话", use_container_width=True):
            st.session_state.agent_messages = []
            st.session_state.last_query_result = None
            st.rerun()
    
    # 主要内容区 - 标签页
    tab1, tab2, tab3 = st.tabs(["🤖 智能对话 (Agent)", "📈 数据洞察 (Intelligence)", "🔧 工具箱"])
    
    # ===== Tab 1: Agent 对话 =====
    with tab1:
        st.markdown("""
        <div class="feature-card">
            <h3>💬 与 AI 助手对话</h3>
            <p>我可以帮你查询数据、分析结果、生成可视化。试着问我：</p>
            <ul>
                <li>"查看订单表的结构"</li>
                <li>"统计每个月的销售总额"</li>
                <li>"分析客户的消费分布"</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # 对话历史
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.agent_messages:
                render_message(
                    msg["role"], 
                    msg["content"],
                    msg.get("tool_info")
                )
                if msg.get("data") is not None:
                    render_data_preview(msg["data"], "查询结果")
                if msg.get("figure") is not None:
                    st.plotly_chart(msg["figure"], use_container_width=True)
        
        # 输入框
        user_input = st.chat_input("输入你的问题...")
        
        if user_input:
            # 添加用户消息
            st.session_state.agent_messages.append({
                "role": "user",
                "content": user_input
            })
            
            # 准备上下文
            context = {
                "database": st.session_state.selected_database,
                "schema": st.session_state.selected_schema,
                "tables": st.session_state.available_tables,
                "messages": st.session_state.agent_messages,
                "last_query_result": st.session_state.last_query_result
            }
            
            # 运行 Agent
            with st.spinner("🤔 思考中..."):
                response = run_agent(conn, user_input, context)
            
            # 处理响应
            thought = response.get("thought", "")
            tool_call = response.get("tool_call")
            direct_response = response.get("response")
            
            agent_message = {
                "role": "assistant",
                "content": "",
                "tool_info": None,
                "data": None,
                "figure": None
            }
            
            if tool_call:
                # 执行工具调用
                tool_name = tool_call.get("name")
                parameters = tool_call.get("parameters", {})
                
                agent_message["tool_info"] = {"name": tool_name, "parameters": parameters}
                
                with st.spinner(f"🔧 执行 {tool_name}..."):
                    result = execute_tool_call(conn, tool_name, parameters, context)
                
                if result.get("success"):
                    if "data" in result:
                        agent_message["data"] = result["data"]
                        st.session_state.last_query_result = result["data"]
                        agent_message["content"] = f"{thought}\n\n✅ 查询成功，返回 {result['row_count']} 行数据。"
                    elif "figure" in result:
                        agent_message["figure"] = result["figure"]
                        agent_message["content"] = f"{thought}\n\n✅ 图表生成成功。"
                    elif "analysis" in result:
                        agent_message["content"] = f"{thought}\n\n📊 分析结果:\n```json\n{json.dumps(result['analysis'], indent=2, ensure_ascii=False)}\n```"
                    elif "columns" in result:
                        cols_info = "\n".join([f"- {c['name']}: {c['type']}" for c in result['columns']])
                        agent_message["content"] = f"{thought}\n\n📋 表 `{result['table_name']}` 结构 (共 {result['row_count']} 行):\n{cols_info}"
                    else:
                        agent_message["content"] = f"{thought}\n\n✅ 执行成功。"
                else:
                    agent_message["content"] = f"{thought}\n\n❌ 执行失败: {result.get('error', '未知错误')}"
            
            elif direct_response:
                agent_message["content"] = direct_response
            
            else:
                agent_message["content"] = str(response)
            
            st.session_state.agent_messages.append(agent_message)
            st.rerun()
    
    # ===== Tab 2: Intelligence =====
    with tab2:
        st.markdown("""
        <div class="feature-card">
            <h3>📊 智能数据洞察</h3>
            <p>上传数据或执行查询后，AI 将自动分析并提供深度洞察。</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 自然语言查询
            st.markdown("### 🔍 自然语言查询")
            nl_query = st.text_area(
                "用自然语言描述你想查询的内容",
                placeholder="例如：查询过去一个月每天的订单数量和总金额",
                height=100
            )
            
            if st.button("🚀 生成并执行查询", type="primary"):
                if nl_query and st.session_state.available_tables:
                    # 获取表结构信息
                    schema_info = {}
                    for table in st.session_state.available_tables[:5]:
                        try:
                            result = AVAILABLE_TOOLS["get_table_info"].execute(conn, table)
                            if result["success"]:
                                schema_info[table] = result["columns"]
                        except Exception:
                            pass
                    
                    with st.spinner("🧠 生成 SQL..."):
                        sql = generate_sql_from_question(
                            conn, nl_query, schema_info, 
                            st.session_state.available_tables
                        )
                    
                    st.markdown("**生成的 SQL:**")
                    st.code(sql, language="sql")
                    
                    # 执行查询
                    with st.spinner("⚡ 执行查询..."):
                        result = AVAILABLE_TOOLS["execute_sql"].execute(conn, sql)
                    
                    if result["success"]:
                        st.session_state.last_query_result = result["data"]
                        render_data_preview(result["data"])
                        
                        # 生成洞察
                        with st.spinner("💡 生成数据洞察..."):
                            insights = generate_data_insights(conn, result["data"], nl_query)
                        
                        st.markdown("### 💡 AI 洞察")
                        st.markdown(insights)
                    else:
                        st.error(f"查询失败: {result['error']}")
                else:
                    st.warning("请先选择数据源并输入查询内容")
        
        with col2:
            # 建议的问题
            st.markdown("### 💡 建议的问题")
            if st.session_state.available_tables and st.button("生成建议"):
                schema_info = {}
                for table in st.session_state.available_tables[:3]:
                    try:
                        result = AVAILABLE_TOOLS["get_table_info"].execute(conn, table)
                        if result["success"]:
                            schema_info[table] = result["columns"]
                    except Exception:
                        pass
                
                with st.spinner("生成建议问题..."):
                    questions = suggest_questions(conn, st.session_state.available_tables, schema_info)
                
                for q in questions:
                    if st.button(f"📌 {q}", key=f"q_{hash(q)}"):
                        st.session_state.suggested_question = q
        
        # 如果有数据，显示可视化选项
        if st.session_state.last_query_result is not None:
            st.markdown("---")
            st.markdown("### 📈 快速可视化")
            
            df = st.session_state.last_query_result
            
            vis_col1, vis_col2, vis_col3 = st.columns(3)
            
            with vis_col1:
                chart_type = st.selectbox(
                    "图表类型",
                    ["bar", "line", "pie", "scatter"],
                    format_func=lambda x: {"bar": "柱状图", "line": "折线图", "pie": "饼图", "scatter": "散点图"}[x]
                )
            
            with vis_col2:
                x_col = st.selectbox("X轴 / 分类", df.columns.tolist())
            
            with vis_col3:
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                y_col = st.selectbox("Y轴 / 数值", numeric_cols if numeric_cols else df.columns.tolist())
            
            if st.button("📊 生成图表"):
                result = AVAILABLE_TOOLS["create_visualization"].execute(
                    conn, df, chart_type, x_col, y_col
                )
                if result["success"]:
                    st.plotly_chart(result["figure"], use_container_width=True)
                else:
                    st.error(result["error"])
    
    # ===== Tab 3: 工具箱 =====
    with tab3:
        st.markdown("""
        <div class="feature-card">
            <h3>🔧 数据工具箱</h3>
            <p>直接使用各种数据工具进行分析。</p>
        </div>
        """, unsafe_allow_html=True)
        
        tool_tabs = st.tabs(["SQL 查询", "表信息", "数据分析"])
        
        # SQL 查询工具
        with tool_tabs[0]:
            st.markdown("### 📝 SQL 查询")
            sql_input = st.text_area(
                "输入 SQL 查询",
                height=150,
                placeholder="SELECT * FROM your_table LIMIT 10"
            )
            
            if st.button("▶️ 执行查询", key="run_sql"):
                if sql_input:
                    with st.spinner("执行中..."):
                        result = AVAILABLE_TOOLS["execute_sql"].execute(conn, sql_input)
                    
                    if result["success"]:
                        st.success(f"查询成功，返回 {result['row_count']} 行")
                        st.session_state.last_query_result = result["data"]
                        render_data_preview(result["data"])
                    else:
                        st.error(f"查询失败: {result['error']}")
        
        # 表信息工具
        with tool_tabs[1]:
            st.markdown("### 📋 表结构查询")
            if st.session_state.available_tables:
                selected_table = st.selectbox(
                    "选择表",
                    st.session_state.available_tables,
                    format_func=lambda x: x.split(".")[-1]
                )
                
                if st.button("🔍 查看结构", key="view_schema"):
                    with st.spinner("获取表信息..."):
                        result = AVAILABLE_TOOLS["get_table_info"].execute(conn, selected_table)
                    
                    if result["success"]:
                        st.markdown(f"**表名:** `{result['table_name']}`")
                        st.markdown(f"**行数:** {result['row_count']:,}")
                        
                        cols_df = pd.DataFrame(result["columns"])
                        st.dataframe(cols_df, use_container_width=True, hide_index=True)
                    else:
                        st.error(result["error"])
            else:
                st.info("请先在侧边栏选择数据库和 Schema")
        
        # 数据分析工具
        with tool_tabs[2]:
            st.markdown("### 📊 数据分析")
            if st.session_state.last_query_result is not None:
                df = st.session_state.last_query_result
                
                analysis_type = st.selectbox(
                    "分析类型",
                    ["summary", "distribution"],
                    format_func=lambda x: {"summary": "描述性统计", "distribution": "数据分布"}[x]
                )
                
                if st.button("📈 执行分析", key="run_analysis"):
                    result = AVAILABLE_TOOLS["analyze_data"].execute(conn, df, analysis_type)
                    
                    if result["success"]:
                        if analysis_type == "summary":
                            st.markdown(f"**行数:** {result['row_count']} | **列数:** {result['column_count']}")
                            st.json(result["analysis"])
                        else:
                            st.json(result["distributions"])
                    else:
                        st.error(result["error"])
            else:
                st.info("请先执行查询以获取数据")


if __name__ == "__main__":
    main()
