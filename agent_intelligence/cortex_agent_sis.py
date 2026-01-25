"""
Cortex Agent & Intelligence Demo App for Snowflake China Region
Streamlit in Snowflake (SiS) 版本
使用 Qwen API 模拟 Cortex Agent 和 Cortex Intelligence 功能
支持语义模型 (Semantic Model) 来增强 SQL 生成效果
"""

import json
import uuid
import pandas as pd
import streamlit as st
from datetime import datetime
from typing import Any, Dict, List, Optional

# 设置页面配置
st.set_page_config(
    layout="wide",
    page_icon="❄️",
    page_title="Snowflake China Intelligence",
    initial_sidebar_state="expanded"
)

# SiS 环境检测和连接
def get_snowflake_connection():
    """获取 Snowflake 连接"""
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
    return session.connection

def get_snowpark_session():
    """获取 Snowpark Session"""
    from snowflake.snowpark.context import get_active_session
    return get_active_session()

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

.main-title {
    background: var(--primary-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2.5rem;
    font-weight: 700;
    text-align: center;
    margin-bottom: 0.5rem;
}

.subtitle {
    color: var(--text-secondary);
    text-align: center;
    font-size: 1rem;
    margin-bottom: 2rem;
}

.feature-card {
    background: var(--card-bg);
    backdrop-filter: blur(16px);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 1.5rem;
    margin: 1rem 0;
}

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

.tool-card {
    background: rgba(123, 44, 191, 0.15);
    border: 1px solid rgba(123, 44, 191, 0.3);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin: 0.5rem 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
}

.semantic-badge {
    background: linear-gradient(135deg, #00D4FF 0%, #7B2CBF 100%);
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 500;
}

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
}
</style>
"""

# ===============================
# 模型提供商和模型配置
# ===============================
MODEL_PROVIDERS = {
    "DashScope (通义千问)": {
        "models": {
            "qwen-max": "Qwen-Max (推荐，能力最强)",
            "qwen-plus": "Qwen-Plus (平衡性能与成本)",
            "qwen-turbo": "Qwen-Turbo (快速响应)",
            "qwen-max-longcontext": "Qwen-Max-LongContext (长文本)",
            "qwen2.5-72b-instruct": "Qwen2.5-72B-Instruct",
            "qwen2.5-32b-instruct": "Qwen2.5-32B-Instruct",
        },
        "default": "qwen-max"
    },
    "DeepSeek": {
        "models": {
            "deepseek-chat": "DeepSeek-V3 (推荐)",
            "deepseek-reasoner": "DeepSeek-R1 (深度推理)",
        },
        "default": "deepseek-chat"
    },
    "Kimi (月之暗面)": {
        "models": {
            "moonshot-v1-8k": "Moonshot-v1-8K",
            "moonshot-v1-32k": "Moonshot-v1-32K",
            "moonshot-v1-128k": "Moonshot-v1-128K (长文本)",
        },
        "default": "moonshot-v1-8k"
    },
    "MiniMax": {
        "models": {
            "abab6.5s-chat": "ABAB6.5s (快速)",
            "abab6.5-chat": "ABAB6.5 (标准)",
            "abab5.5-chat": "ABAB5.5",
        },
        "default": "abab6.5s-chat"
    },
}

DEFAULT_PROVIDER = "DashScope (通义千问)"
DEFAULT_MODEL = "qwen-max"


# ===============================
# 时间问候语生成 (中国时区 UTC+8)
# ===============================
def get_time_greeting(username: str = "Yuheng") -> tuple[str, str]:
    """根据中国时区时间生成问候语"""
    from datetime import timezone, timedelta
    
    # 中国时区 UTC+8
    china_tz = timezone(timedelta(hours=8))
    china_time = datetime.now(china_tz)
    current_hour = china_time.hour
    
    if 5 <= current_hour < 12:
        greeting = f"Good morning, {username}"
        greeting_cn = f"早上好，{username}"
    elif 12 <= current_hour < 14:
        greeting = f"Good afternoon, {username}"
        greeting_cn = f"中午好，{username}"
    elif 14 <= current_hour < 18:
        greeting = f"Good afternoon, {username}"
        greeting_cn = f"下午好，{username}"
    elif 18 <= current_hour < 22:
        greeting = f"Good evening, {username}"
        greeting_cn = f"晚上好，{username}"
    else:
        greeting = f"Good night, {username}"
        greeting_cn = f"夜深了，{username}"
    
    return greeting, greeting_cn


# ===============================
# Qwen API 调用 (通过 Snowflake UDF)
# ===============================

def call_qwen_udf(conn, model: str, prompt: str, system_prompt: str = None) -> str:
    """通过 Snowflake UDF 调用 Qwen API"""
    escaped_prompt = prompt.replace("'", "''").replace("\\", "\\\\")
    
    if system_prompt:
        escaped_system = system_prompt.replace("'", "''").replace("\\", "\\\\")
        full_prompt = f"[系统指令]: {escaped_system}\n\n[用户问题]: {escaped_prompt}"
    else:
        full_prompt = escaped_prompt
    
    query = f"SELECT SNOWFLAKE_PROD_USER1.CORTEX_ANALYST.QWEN_COMPLETE('{model}', $${full_prompt}$$)"
    
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        if result and result[0]:
            return result[0]
        return ""
    except Exception as e:
        return f"错误: {str(e)}"


# ===============================
# 语义模型管理
# ===============================
def load_semantic_model_from_stage(conn, stage_path: str) -> Optional[str]:
    """从 Stage 加载语义模型 YAML"""
    try:
        session = get_snowpark_session()
        # 获取 YAML 内容
        yaml_content = session.file.get_stream(stage_path).read().decode('utf-8')
        return yaml_content
    except Exception as e:
        st.warning(f"无法加载语义模型: {e}")
        return None

def list_yaml_files_in_stage(conn, stage_name: str) -> List[str]:
    """列出 Stage 中的 YAML 文件"""
    try:
        cursor = conn.cursor()
        cursor.execute(f"LIST @{stage_name}")
        files = []
        for row in cursor.fetchall():
            file_name = row[0]
            if file_name.endswith('.yaml') or file_name.endswith('.yml'):
                files.append(file_name)
        return files
    except Exception as e:
        return []

def parse_semantic_model(yaml_content: str) -> Dict[str, Any]:
    """解析语义模型 YAML 为结构化数据"""
    try:
        import yaml
        model = yaml.safe_load(yaml_content)
        return model
    except Exception:
        # 简单解析
        return {"raw": yaml_content}

def format_semantic_model_for_prompt(yaml_content: str) -> str:
    """格式化语义模型用于 LLM 提示"""
    return f"""
## 语义模型定义 (YAML)

以下是数据的语义模型，包含了表结构、业务含义、指标定义和关系：

```yaml
{yaml_content}
```

请根据这个语义模型来理解数据的业务含义：
- **name**: 语义层中的字段名称
- **description**: 字段的业务含义描述
- **expr**: 字段对应的 SQL 表达式
- **synonyms**: 同义词，用户可能用这些词来指代该字段
- **sample_values**: 示例值
- **data_type**: 数据类型
"""


# ===============================
# 数据库操作函数
# ===============================
@st.cache_data(ttl=300)
def fetch_databases(_conn) -> List[str]:
    """获取可用数据库列表"""
    cursor = _conn.cursor()
    cursor.execute("SHOW DATABASES")
    return [row[1] for row in cursor.fetchall()]

@st.cache_data(ttl=300)
def fetch_schemas(_conn, database: str) -> List[str]:
    """获取指定数据库的 Schema 列表"""
    cursor = _conn.cursor()
    cursor.execute(f"SHOW SCHEMAS IN DATABASE {database}")
    return [f"{database}.{row[1]}" for row in cursor.fetchall()]

@st.cache_data(ttl=300)
def fetch_tables(_conn, schema: str) -> List[str]:
    """获取指定 Schema 的表列表"""
    cursor = _conn.cursor()
    cursor.execute(f"SHOW TABLES IN {schema}")
    tables = [f"{schema}.{row[1]}" for row in cursor.fetchall()]
    cursor.execute(f"SHOW VIEWS IN {schema}")
    views = [f"{schema}.{row[1]}" for row in cursor.fetchall()]
    return tables + views

@st.cache_data(ttl=300)
def fetch_stages(_conn, schema: str) -> List[str]:
    """获取指定 Schema 的 Stage 列表"""
    cursor = _conn.cursor()
    cursor.execute(f"SHOW STAGES IN {schema}")
    return [f"{schema}.{row[1]}" for row in cursor.fetchall()]

def execute_sql(conn, sql: str) -> Dict[str, Any]:
    """执行 SQL 查询"""
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

def get_table_info(conn, table_name: str) -> Dict[str, Any]:
    """获取表结构信息"""
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


# ===============================
# Agent 核心逻辑 (支持语义模型)
# ===============================
AGENT_SYSTEM_PROMPT_WITH_SEMANTIC = """你是一个专业的数据分析助手，运行在 Snowflake 环境中。

## 重要：语义模型

你必须参考以下语义模型来理解数据的业务含义。语义模型定义了：
- 字段的业务名称和描述
- 计算指标的公式
- 字段的同义词（用户可能用不同的词描述同一个字段）
- 表之间的关系

{semantic_model}

## 可用工具:

1. **execute_sql** - 执行 SQL 查询
   参数: sql (string) - SQL 查询语句

2. **get_table_info** - 获取表信息
   参数: table_name (string) - 完全限定的表名

## 响应格式:

当需要调用工具时，请使用以下 JSON 格式：
```json
{{
  "thought": "你的思考过程，包括如何根据语义模型理解用户意图",
  "tool_call": {{
    "name": "工具名称",
    "parameters": {{
      "参数名": "参数值"
    }}
  }}
}}
```

当不需要调用工具，直接回答时：
```json
{{
  "thought": "你的思考过程",
  "response": "你的回答内容"
}}
```

## 重要规则:

1. **必须参考语义模型**：根据语义模型中的 description 和 synonyms 来理解用户问题
2. **使用正确的表达式**：使用语义模型中定义的 expr 作为 SQL 字段表达式
3. **理解业务术语**：用户可能使用业务术语而非字段名，需要映射到正确的字段
4. SQL 查询必须是有效的 Snowflake SQL 语法
5. 使用中文回答

当前上下文:
- 数据库: {database}
- Schema: {schema}
"""

AGENT_SYSTEM_PROMPT_WITHOUT_SEMANTIC = """你是一个专业的数据分析助手，运行在 Snowflake 环境中。

## 可用工具:

1. **execute_sql** - 执行 SQL 查询
   参数: sql (string) - SQL 查询语句

2. **get_table_info** - 获取表信息
   参数: table_name (string) - 完全限定的表名

## 响应格式:

当需要调用工具时：
```json
{{
  "thought": "你的思考过程",
  "tool_call": {{
    "name": "工具名称",
    "parameters": {{"参数名": "参数值"}}
  }}
}}
```

当直接回答时：
```json
{{
  "thought": "你的思考过程",
  "response": "你的回答内容"
}}
```

请用中文回答。

当前上下文:
- 数据库: {database}
- Schema: {schema}
- 可用表: {tables}
"""


def parse_agent_response(response: str) -> Dict[str, Any]:
    """解析 Agent 的响应"""
    import re
    try:
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        
        start = response.find('{')
        end = response.rfind('}') + 1
        if start != -1 and end > start:
            return json.loads(response[start:end])
    except json.JSONDecodeError:
        pass
    
    return {"response": response}


def run_agent(conn, user_input: str, context: Dict) -> Dict[str, Any]:
    """运行 Agent"""
    semantic_model = context.get("semantic_model")
    
    if semantic_model:
        # 使用语义模型增强的提示
        formatted_model = format_semantic_model_for_prompt(semantic_model)
        system_prompt = AGENT_SYSTEM_PROMPT_WITH_SEMANTIC.format(
            semantic_model=formatted_model,
            database=context.get("database", "未选择"),
            schema=context.get("schema", "未选择")
        )
    else:
        # 无语义模型的基础提示
        system_prompt = AGENT_SYSTEM_PROMPT_WITHOUT_SEMANTIC.format(
            database=context.get("database", "未选择"),
            schema=context.get("schema", "未选择"),
            tables=", ".join(context.get("tables", [])[:10])
        )
    
    messages = context.get("messages", [])
    history_text = ""
    for msg in messages[-6:]:
        role = "用户" if msg["role"] == "user" else "助手"
        history_text += f"\n{role}: {msg['content']}\n"
    
    full_prompt = f"{history_text}\n用户: {user_input}"
    
    # 使用 session state 中选择的模型
    model = st.session_state.get("selected_model", DEFAULT_MODEL)
    response = call_qwen_udf(conn, model, full_prompt, system_prompt)
    parsed = parse_agent_response(response)
    
    return parsed


def execute_tool_call(conn, tool_name: str, parameters: Dict, context: Dict) -> Dict[str, Any]:
    """执行工具调用"""
    if tool_name == "execute_sql":
        return execute_sql(conn, parameters.get("sql", ""))
    elif tool_name == "get_table_info":
        return get_table_info(conn, parameters.get("table_name", ""))
    else:
        return {"success": False, "error": f"未知工具: {tool_name}"}


# ===============================
# Intelligence 功能 (支持语义模型)
# ===============================
def generate_data_insights(conn, df: pd.DataFrame, context: str = "", semantic_model: str = None) -> str:
    """使用 AI 生成数据洞察"""
    summary = f"""
数据概览:
- 行数: {len(df)}
- 列数: {len(df.columns)}
- 列名: {', '.join(df.columns.tolist())}

数据统计:
{df.describe().to_string() if len(df) > 0 else '无数据'}

前5行数据示例:
{df.head().to_string() if len(df) > 0 else '无数据'}
"""
    
    semantic_context = ""
    if semantic_model:
        semantic_context = f"""
## 语义模型参考
以下语义模型定义了数据的业务含义，请据此解读数据：
```yaml
{semantic_model[:2000]}  # 截取前2000字符
```
"""
    
    prompt = f"""请分析以下数据并提供专业的商业洞察:

{summary}

{semantic_context}

{f"用户查询背景: {context}" if context else ""}

请提供:
1. 数据的关键发现 (3-5点)
2. 基于语义模型的业务解读
3. 建议的后续分析方向

请用专业但易懂的中文回答。
"""
    
    # 使用 session state 中选择的模型
    model = st.session_state.get("selected_model", DEFAULT_MODEL)
    return call_qwen_udf(conn, model, prompt)


def generate_sql_from_question(conn, question: str, schema_info: Dict, tables: List[str], semantic_model: str = None) -> str:
    """根据自然语言问题生成 SQL（支持语义模型）"""
    
    semantic_context = ""
    if semantic_model:
        semantic_context = f"""
## 重要：语义模型

请根据以下语义模型来理解数据的业务含义，并生成正确的 SQL：

```yaml
{semantic_model}
```

规则：
1. 根据语义模型中的 description 理解字段含义
2. 使用语义模型中的 expr 作为 SQL 表达式
3. 参考 synonyms 来匹配用户使用的业务术语
4. 如果用户问的指标在语义模型中有定义，使用定义的计算公式
"""
    
    prompt = f"""请根据以下问题生成 Snowflake SQL 查询:

问题: {question}

{semantic_context}

可用表: {', '.join(tables)}

表结构信息:
{json.dumps(schema_info, indent=2, ensure_ascii=False)}

要求:
1. 生成有效的 Snowflake SQL
2. 只返回 SQL 语句，不要任何解释
3. 使用完全限定的表名
4. 添加 LIMIT 100 限制结果数量
5. 如果有语义模型，必须参考其中的字段定义和表达式

SQL:
"""
    
    # 使用 session state 中选择的模型
    model = st.session_state.get("selected_model", DEFAULT_MODEL)
    response = call_qwen_udf(conn, model, prompt)
    
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


def suggest_questions(conn, tables: List[str], schema_info: Dict, semantic_model: str = None) -> List[str]:
    """根据表结构和语义模型建议问题"""
    
    semantic_context = ""
    if semantic_model:
        semantic_context = f"""
语义模型（包含业务定义）：
```yaml
{semantic_model[:1500]}
```

请根据语义模型中定义的指标和维度来建议问题。
"""
    
    prompt = f"""基于以下数据信息，建议5个有价值的数据分析问题:

可用表: {', '.join(tables[:5])}

表结构信息:
{json.dumps(schema_info, indent=2, ensure_ascii=False)}

{semantic_context}

请生成5个具体、可执行的数据分析问题，每行一个问题。
如果有语义模型，请使用其中定义的业务术语来提问。
只输出问题，不要编号。
"""
    
    # 使用快速模型来生成建议问题
    response = call_qwen_udf(conn, "qwen-turbo", prompt)
    questions = [q.strip() for q in response.strip().split('\n') if q.strip()]
    return questions[:5]


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


# ===============================
# 主应用
# ===============================
def main():
    # 注入自定义样式
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    # 获取时间问候语
    greeting_en, greeting_cn = get_time_greeting("Yuheng")
    
    # 标题和问候语
    st.markdown(f'<h1 class="main-title">❄️ Intelligence</h1>', unsafe_allow_html=True)
    st.markdown(f'<h2 style="text-align: center; color: #E8E8E8; font-weight: 400; margin-bottom: 0.5rem;">{greeting_en}</h2>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle" style="background: linear-gradient(135deg, #00D4FF 0%, #7B2CBF 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-size: 1.5rem; font-weight: 500;">What insights can I help with?</p>', unsafe_allow_html=True)
    
    # 初始化 session state
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
    
    if "semantic_model" not in st.session_state:
        st.session_state.semantic_model = None
    
    if "semantic_model_name" not in st.session_state:
        st.session_state.semantic_model_name = None
    
    if "selected_provider" not in st.session_state:
        st.session_state.selected_provider = DEFAULT_PROVIDER
    
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = DEFAULT_MODEL
    
    # 获取连接
    try:
        conn = get_snowflake_connection()
    except Exception as e:
        st.error(f"无法连接到 Snowflake: {e}")
        return
    
    # 侧边栏 - 数据源和语义模型选择
    with st.sidebar:
        st.markdown("### 🧠 模型选择")
        
        # 模型提供商选择
        provider_list = list(MODEL_PROVIDERS.keys())
        selected_provider = st.selectbox(
            "选择模型提供商",
            options=provider_list,
            index=provider_list.index(st.session_state.selected_provider) if st.session_state.selected_provider in provider_list else 0,
            key="provider_selector"
        )
        
        # 如果提供商变化，更新默认模型
        if selected_provider != st.session_state.selected_provider:
            st.session_state.selected_provider = selected_provider
            st.session_state.selected_model = MODEL_PROVIDERS[selected_provider]["default"]
        
        # 子模型选择
        provider_models = MODEL_PROVIDERS[selected_provider]["models"]
        model_list = list(provider_models.keys())
        
        # 确保当前选中的模型在列表中
        current_model_index = 0
        if st.session_state.selected_model in model_list:
            current_model_index = model_list.index(st.session_state.selected_model)
        
        selected_model = st.selectbox(
            "选择模型",
            options=model_list,
            index=current_model_index,
            format_func=lambda x: provider_models[x],
            key="model_selector"
        )
        
        if selected_model != st.session_state.selected_model:
            st.session_state.selected_model = selected_model
        
        st.caption(f"📍 **{selected_provider}** / `{selected_model}`")
        
        st.markdown("---")
        st.markdown("### 🗄️ 数据源配置")
        
        # 数据库选择
        try:
            databases = fetch_databases(conn)
        except Exception:
            databases = []
        
        selected_db = st.selectbox(
            "选择数据库",
            options=databases,
            index=0 if databases else None,
            key="db_selector"
        )
        
        if selected_db != st.session_state.selected_database:
            st.session_state.selected_database = selected_db
            st.session_state.selected_schema = None
            st.session_state.available_tables = []
            st.session_state.semantic_model = None
        
        # Schema 选择
        if selected_db:
            try:
                schemas = fetch_schemas(conn, selected_db)
                selected_schema = st.selectbox(
                    "选择 Schema",
                    options=schemas,
                    index=0 if schemas else None,
                    key="schema_selector",
                    format_func=lambda x: x.split(".")[-1] if "." in x else x
                )
                
                if selected_schema != st.session_state.selected_schema:
                    st.session_state.selected_schema = selected_schema
                    try:
                        st.session_state.available_tables = fetch_tables(conn, selected_schema)
                    except Exception:
                        st.session_state.available_tables = []
            except Exception:
                st.warning("无法获取 Schema 列表")
        
        # ===== 语义模型配置 =====
        st.markdown("---")
        st.markdown("### 📚 语义模型")
        
        if st.session_state.semantic_model:
            st.success(f"✅ 已加载: {st.session_state.semantic_model_name}")
            if st.button("🗑️ 卸载语义模型"):
                st.session_state.semantic_model = None
                st.session_state.semantic_model_name = None
                st.experimental_rerun()
        else:
            st.info("💡 加载语义模型可提升 SQL 生成准确性")
        
        # 从 Stage 加载语义模型
        if st.session_state.selected_schema:
            try:
                stages = fetch_stages(conn, st.session_state.selected_schema)
                if stages:
                    selected_stage = st.selectbox(
                        "选择 Stage",
                        options=stages,
                        format_func=lambda x: x.split(".")[-1],
                        key="stage_selector"
                    )
                    
                    if selected_stage:
                        yaml_files = list_yaml_files_in_stage(conn, selected_stage)
                        if yaml_files:
                            selected_yaml = st.selectbox(
                                "选择语义模型文件",
                                options=yaml_files,
                                format_func=lambda x: x.split("/")[-1],
                                key="yaml_selector"
                            )
                            
                            if st.button("📥 加载语义模型", type="primary"):
                                with st.spinner("加载中..."):
                                    yaml_content = load_semantic_model_from_stage(conn, f"@{selected_stage}/{selected_yaml.split('/')[-1]}")
                                    if yaml_content:
                                        st.session_state.semantic_model = yaml_content
                                        st.session_state.semantic_model_name = selected_yaml.split("/")[-1]
                                        st.success("✅ 语义模型加载成功！")
                                        st.experimental_rerun()
                        else:
                            st.caption("该 Stage 中没有 YAML 文件")
            except Exception as e:
                st.caption(f"无法列出 Stage: {e}")
        
        # 手动输入语义模型
        with st.expander("📝 手动输入语义模型"):
            manual_yaml = st.text_area(
                "粘贴语义模型 YAML",
                height=200,
                placeholder="粘贴您的语义模型 YAML 内容..."
            )
            if st.button("应用语义模型"):
                if manual_yaml.strip():
                    st.session_state.semantic_model = manual_yaml
                    st.session_state.semantic_model_name = "手动输入"
                    st.success("✅ 语义模型已应用！")
                    st.experimental_rerun()
        
        # 显示可用表
        st.markdown("---")
        if st.session_state.available_tables:
            st.markdown("### 📋 可用数据表")
            for table in st.session_state.available_tables[:10]:
                table_name = table.split(".")[-1]
                st.markdown(f"- `{table_name}`")
            if len(st.session_state.available_tables) > 10:
                st.caption(f"... 还有 {len(st.session_state.available_tables) - 10} 张表")
        
        st.markdown("---")
        
        # 清除对话按钮
        if st.button("🗑️ 清除对话", use_container_width=True):
            st.session_state.agent_messages = []
            st.session_state.last_query_result = None
            st.experimental_rerun()
    
    # 主要内容区 - 标签页
    tab1, tab2, tab3 = st.tabs(["🤖 智能对话 (Agent)", "📈 数据洞察 (Intelligence)", "🔧 工具箱"])
    
    # ===== Tab 1: Agent 对话 =====
    with tab1:
        # 语义模型状态提示
        if st.session_state.semantic_model:
            st.markdown(f"""
            <div class="feature-card">
                <span class="semantic-badge">🎯 语义模型已启用</span>
                <h3 style="margin-top: 1rem;">💬 与 AI 助手对话</h3>
                <p>语义模型 <strong>{st.session_state.semantic_model_name}</strong> 已加载，AI 将参考业务定义来理解您的问题。</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="feature-card">
                <h3>💬 与 AI 助手对话</h3>
                <p>⚠️ <strong>提示</strong>：未加载语义模型，SQL 生成仅基于表结构。建议在侧边栏加载语义模型以获得更好的效果。</p>
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
        
        # 输入框 (使用 text_input 替代 chat_input 以兼容 SiS)
        def submit_question():
            if st.session_state.user_question_input:
                st.session_state.submitted_question = st.session_state.user_question_input
                st.session_state.user_question_input = ""
        
        col_input, col_btn = st.columns([5, 1])
        with col_input:
            st.text_input(
                "输入你的问题",
                key="user_question_input",
                placeholder="Ask Snowflake Intelligence...",
                label_visibility="collapsed",
                on_change=submit_question
            )
        with col_btn:
            if st.button("发送", type="primary", use_container_width=True):
                submit_question()
        
        # 处理提交的问题
        user_input = st.session_state.pop("submitted_question", None)
        
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
                "last_query_result": st.session_state.last_query_result,
                "semantic_model": st.session_state.semantic_model  # 传入语义模型
            }
            
            # 运行 Agent
            with st.spinner("🤔 思考中（参考语义模型）..." if st.session_state.semantic_model else "🤔 思考中..."):
                response = run_agent(conn, user_input, context)
            
            # 处理响应
            thought = response.get("thought", "")
            tool_call = response.get("tool_call")
            direct_response = response.get("response")
            
            agent_message = {
                "role": "assistant",
                "content": "",
                "tool_info": None,
                "data": None
            }
            
            if tool_call:
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
            st.experimental_rerun()
    
    # ===== Tab 2: Intelligence =====
    with tab2:
        if st.session_state.semantic_model:
            st.markdown(f"""
            <div class="feature-card">
                <span class="semantic-badge">🎯 语义模型已启用</span>
                <h3 style="margin-top: 1rem;">📊 智能数据洞察</h3>
                <p>使用语义模型 <strong>{st.session_state.semantic_model_name}</strong> 来理解您的业务问题。</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="feature-card">
                <h3>📊 智能数据洞察</h3>
                <p>用自然语言描述你想查询的内容。⚠️ 建议先加载语义模型以获得更准确的结果。</p>
            </div>
            """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 🔍 自然语言查询")
            nl_query = st.text_area(
                "用自然语言描述你想查询的内容",
                placeholder="例如：查询过去一个月每天的订单数量和总金额\n\n如果有语义模型，可以使用业务术语如：VIP客户、销售额、退货率等",
                height=100
            )
            
            if st.button("🚀 生成并执行查询", type="primary"):
                if nl_query and st.session_state.available_tables:
                    # 获取表结构信息
                    schema_info = {}
                    for table in st.session_state.available_tables[:5]:
                        try:
                            result = get_table_info(conn, table)
                            if result["success"]:
                                schema_info[table] = result["columns"]
                        except Exception:
                            pass
                    
                    with st.spinner("🧠 生成 SQL（参考语义模型）..." if st.session_state.semantic_model else "🧠 生成 SQL..."):
                        sql = generate_sql_from_question(
                            conn, nl_query, schema_info, 
                            st.session_state.available_tables,
                            st.session_state.semantic_model  # 传入语义模型
                        )
                    
                    st.markdown("**生成的 SQL:**")
                    st.code(sql, language="sql")
                    
                    # 执行查询
                    with st.spinner("⚡ 执行查询..."):
                        result = execute_sql(conn, sql)
                    
                    if result["success"]:
                        st.session_state.last_query_result = result["data"]
                        render_data_preview(result["data"])
                        
                        # 生成洞察
                        with st.spinner("💡 生成数据洞察..."):
                            insights = generate_data_insights(
                                conn, result["data"], nl_query,
                                st.session_state.semantic_model  # 传入语义模型
                            )
                        
                        st.markdown("### 💡 AI 洞察")
                        st.markdown(insights)
                    else:
                        st.error(f"查询失败: {result['error']}")
                else:
                    st.warning("请先选择数据源并输入查询内容")
        
        with col2:
            st.markdown("### 💡 建议的问题")
            if st.session_state.available_tables and st.button("生成建议"):
                schema_info = {}
                for table in st.session_state.available_tables[:3]:
                    try:
                        result = get_table_info(conn, table)
                        if result["success"]:
                            schema_info[table] = result["columns"]
                    except Exception:
                        pass
                
                with st.spinner("生成建议问题..."):
                    questions = suggest_questions(
                        conn, st.session_state.available_tables, schema_info,
                        st.session_state.semantic_model  # 传入语义模型
                    )
                
                for q in questions:
                    st.info(f"📌 {q}")
    
    # ===== Tab 3: 工具箱 =====
    with tab3:
        st.markdown("""
        <div class="feature-card">
            <h3>🔧 数据工具箱</h3>
            <p>直接使用 SQL 查询和表信息查询工具。</p>
        </div>
        """, unsafe_allow_html=True)
        
        tool_tabs = st.tabs(["SQL 查询", "表信息", "数据统计", "语义模型预览"])
        
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
                        result = execute_sql(conn, sql_input)
                    
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
                        result = get_table_info(conn, selected_table)
                    
                    if result["success"]:
                        st.markdown(f"**表名:** `{result['table_name']}`")
                        st.markdown(f"**行数:** {result['row_count']:,}")
                        
                        cols_df = pd.DataFrame(result["columns"])
                        st.dataframe(cols_df, use_container_width=True, hide_index=True)
                    else:
                        st.error(result["error"])
            else:
                st.info("请先在侧边栏选择数据库和 Schema")
        
        # 数据统计工具
        with tool_tabs[2]:
            st.markdown("### 📊 数据统计")
            if st.session_state.last_query_result is not None:
                df = st.session_state.last_query_result
                
                st.markdown(f"**数据维度:** {len(df)} 行 × {len(df.columns)} 列")
                
                st.markdown("**描述性统计:**")
                st.dataframe(df.describe(), use_container_width=True)
                
                st.markdown("**数据类型:**")
                dtype_df = pd.DataFrame({
                    "列名": df.columns,
                    "数据类型": df.dtypes.astype(str).values,
                    "非空数量": df.count().values,
                    "空值数量": df.isnull().sum().values
                })
                st.dataframe(dtype_df, use_container_width=True, hide_index=True)
            else:
                st.info("请先执行查询以获取数据")
        
        # 语义模型预览
        with tool_tabs[3]:
            st.markdown("### 📚 语义模型预览")
            if st.session_state.semantic_model:
                st.markdown(f"**当前加载:** `{st.session_state.semantic_model_name}`")
                st.code(st.session_state.semantic_model, language="yaml")
            else:
                st.info("未加载语义模型。请在侧边栏加载语义模型。")


if __name__ == "__main__":
    main()
