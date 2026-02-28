"""
Cortex Agent & Intelligence Demo App for Snowflake China Region
Streamlit in Snowflake (SiS) Version - V3.2
Multi-turn conversation for both Agent Chat and Data Insights
"""

import json
import uuid
import pandas as pd
import streamlit as st
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

APP_VERSION = "3.2.0"

st.set_page_config(
    layout="wide",
    page_icon="❄️",
    page_title="Snowflake China Intelligence V3",
    initial_sidebar_state="expanded"
)


# ===============================
# Snowflake Connection
# ===============================
def get_snowflake_connection():
    from snowflake.snowpark.context import get_active_session
    return get_active_session().connection

def get_snowpark_session():
    from snowflake.snowpark.context import get_active_session
    return get_active_session()

def ensure_warehouse():
    if "warehouse_set" not in st.session_state:
        try:
            session = get_snowpark_session()
            session.sql("USE WAREHOUSE COMPUTE_WH").collect()
            st.session_state["warehouse_set"] = True
        except:
            try:
                session = get_snowpark_session()
                wh_list = session.sql("SHOW WAREHOUSES").collect()
                if wh_list:
                    session.sql(f"USE WAREHOUSE {wh_list[0]['name']}").collect()
                    st.session_state["warehouse_set"] = True
            except:
                pass

ensure_warehouse()


# ===============================
# User Info & Greeting
# ===============================
def get_current_user_info() -> Dict[str, str]:
    """Get current user information from Snowflake session"""
    try:
        # Method 1: Try st.experimental_user (Streamlit in Snowflake)
        if hasattr(st, 'experimental_user') and st.experimental_user:
            user_info = st.experimental_user
            if hasattr(user_info, 'user_name'):
                return {"username": user_info.user_name, "email": getattr(user_info, 'email', '')}
        
        # Method 2: Query Snowflake for current user
        session = get_snowpark_session()
        result = session.sql("SELECT CURRENT_USER() as username").collect()
        if result:
            username = result[0]['USERNAME']
            try:
                user_desc = session.sql(f"DESCRIBE USER {username}").collect()
                first_name = None
                display_name = None
                for row in user_desc:
                    prop = row['property']
                    val = row['value']
                    if prop == 'FIRST_NAME' and val:
                        first_name = val
                    elif prop == 'DISPLAY_NAME' and val:
                        display_name = val
                if first_name:
                    return {"username": username, "first_name": first_name}
                if display_name:
                    return {"username": username, "display_name": display_name}
            except:
                pass
            return {"username": username}
    except:
        pass
    return {"username": "there"}


def get_display_name() -> str:
    """Get a friendly display name for the current user"""
    user_info = get_current_user_info()
    
    # Priority: first_name > display_name > parsed username > default
    if 'first_name' in user_info and user_info['first_name']:
        return user_info['first_name']
    
    if 'display_name' in user_info and user_info['display_name']:
        dn = user_info['display_name']
        return dn.split()[0] if ' ' in dn else dn
    
    username = user_info.get('username', 'there')
    
    if username and username != 'there':
        name_part = username.split('@')[0]
        for sep in ['_', '.', '-']:
            if sep in name_part:
                name_part = name_part.split(sep)[0]
                break
        return name_part.capitalize()
    
    return "there"


def get_user_id() -> str:
    try:
        user_info = get_current_user_info()
        return user_info.get('username', 'anonymous')
    except:
        return "anonymous"


def get_time_greeting(username: str = None) -> str:
    """Generate greeting based on China timezone"""
    if username is None:
        username = get_display_name()
    
    china_tz = timezone(timedelta(hours=8))
    hour = datetime.now(china_tz).hour
    
    if 5 <= hour < 12:
        return f"Good morning, {username}"
    elif 12 <= hour < 18:
        return f"Good afternoon, {username}"
    elif 18 <= hour < 22:
        return f"Good evening, {username}"
    return f"Good night, {username}"


# ===============================
# Chat History Storage (Agent Chat)
# ===============================
MAX_HISTORY_MESSAGES = 20
MAX_HISTORY_CHARS = 8000

AGENT_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS {schema}.AGENT_CHAT_SESSIONS (
    session_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(255),
    title VARCHAR(500),
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    semantic_model_name VARCHAR(255),
    message_count INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS {schema}.AGENT_CHAT_MESSAGES (
    message_id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36),
    role VARCHAR(20),
    content TEXT,
    tool_info TEXT,
    query_result TEXT,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
"""

INSIGHTS_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS {schema}.INSIGHTS_SESSIONS (
    session_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(255),
    title VARCHAR(500),
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    semantic_model_name VARCHAR(255),
    message_count INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS {schema}.INSIGHTS_MESSAGES (
    message_id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36),
    role VARCHAR(20),
    content TEXT,
    sql_query TEXT,
    query_result TEXT,
    insights TEXT,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
"""


def ensure_all_tables(session, schema: str) -> bool:
    try:
        for sql in [AGENT_TABLES_SQL, INSIGHTS_TABLES_SQL]:
            for stmt in sql.format(schema=schema).split(';'):
                stmt = stmt.strip()
                if stmt:
                    session.sql(stmt).collect()
        return True
    except:
        return False


# Agent Chat history functions
def save_agent_session(session, schema: str, session_id: str, user_id: str, 
                       title: str, semantic_model: str = None) -> bool:
    try:
        sql = f"""
        MERGE INTO {schema}.AGENT_CHAT_SESSIONS t
        USING (SELECT '{session_id}' as session_id) s
        ON t.session_id = s.session_id
        WHEN MATCHED THEN UPDATE SET
            updated_at = CURRENT_TIMESTAMP(),
            title = '{title.replace("'", "''")}',
            message_count = (SELECT COUNT(*) FROM {schema}.AGENT_CHAT_MESSAGES WHERE session_id = '{session_id}')
        WHEN NOT MATCHED THEN INSERT (session_id, user_id, title, semantic_model_name)
        VALUES ('{session_id}', '{user_id}', '{title.replace("'", "''")}', 
                {f"'{semantic_model}'" if semantic_model else 'NULL'})
        """
        session.sql(sql).collect()
        return True
    except:
        return False


def save_agent_message(session, schema: str, session_id: str, message_id: str,
                       role: str, content: str, tool_info: dict = None,
                       query_result: pd.DataFrame = None) -> bool:
    try:
        escaped = content.replace("'", "''").replace("\\", "\\\\") if content else ""
        tool_json = json.dumps(tool_info, ensure_ascii=False).replace("'", "''") if tool_info else None
        result_json = None
        if query_result is not None and len(query_result) > 0:
            result_json = query_result.head(50).to_json(orient='records', force_ascii=False).replace("'", "''")
        
        sql = f"""
        INSERT INTO {schema}.AGENT_CHAT_MESSAGES (message_id, session_id, role, content, tool_info, query_result)
        VALUES ('{message_id}', '{session_id}', '{role}', $${escaped}$$,
                {f"$${tool_json}$$" if tool_json else 'NULL'},
                {f"$${result_json}$$" if result_json else 'NULL'})
        """
        session.sql(sql).collect()
        return True
    except:
        return False


def load_agent_sessions(session, schema: str, user_id: str, limit: int = 15) -> List[Dict]:
    try:
        sql = f"""
        SELECT session_id, title, updated_at, message_count
        FROM {schema}.AGENT_CHAT_SESSIONS
        WHERE user_id = '{user_id}'
        ORDER BY updated_at DESC LIMIT {limit}
        """
        result = session.sql(sql).collect()
        return [{"session_id": r['SESSION_ID'], "title": r['TITLE'], 
                 "updated_at": r['UPDATED_AT'], "message_count": r['MESSAGE_COUNT']} for r in result]
    except:
        return []


def load_agent_messages(session, schema: str, session_id: str) -> List[Dict]:
    try:
        sql = f"""
        SELECT message_id, role, content, tool_info, query_result
        FROM {schema}.AGENT_CHAT_MESSAGES
        WHERE session_id = '{session_id}' ORDER BY created_at ASC
        """
        result = session.sql(sql).collect()
        msgs = []
        for r in result:
            msg = {"message_id": r['MESSAGE_ID'], "role": r['ROLE'], "content": r['CONTENT']}
            if r['TOOL_INFO']:
                try: msg["tool_info"] = json.loads(r['TOOL_INFO'])
                except: pass
            if r['QUERY_RESULT']:
                try: msg["data"] = pd.read_json(r['QUERY_RESULT'])
                except: pass
            msgs.append(msg)
        return msgs
    except:
        return []


def delete_agent_session(session, schema: str, session_id: str) -> bool:
    try:
        session.sql(f"DELETE FROM {schema}.AGENT_CHAT_MESSAGES WHERE session_id = '{session_id}'").collect()
        session.sql(f"DELETE FROM {schema}.AGENT_CHAT_SESSIONS WHERE session_id = '{session_id}'").collect()
        return True
    except:
        return False


# Insights history functions
def save_insights_session(session, schema: str, session_id: str, user_id: str, 
                          title: str, semantic_model: str = None) -> bool:
    try:
        sql = f"""
        MERGE INTO {schema}.INSIGHTS_SESSIONS t
        USING (SELECT '{session_id}' as session_id) s
        ON t.session_id = s.session_id
        WHEN MATCHED THEN UPDATE SET
            updated_at = CURRENT_TIMESTAMP(),
            title = '{title.replace("'", "''")}',
            message_count = (SELECT COUNT(*) FROM {schema}.INSIGHTS_MESSAGES WHERE session_id = '{session_id}')
        WHEN NOT MATCHED THEN INSERT (session_id, user_id, title, semantic_model_name)
        VALUES ('{session_id}', '{user_id}', '{title.replace("'", "''")}', 
                {f"'{semantic_model}'" if semantic_model else 'NULL'})
        """
        session.sql(sql).collect()
        return True
    except:
        return False


def save_insights_message(session, schema: str, session_id: str, message_id: str,
                          role: str, content: str, sql_query: str = None,
                          query_result: pd.DataFrame = None, insights: str = None) -> bool:
    try:
        escaped = content.replace("'", "''").replace("\\", "\\\\") if content else ""
        sql_escaped = sql_query.replace("'", "''") if sql_query else None
        insights_escaped = insights.replace("'", "''") if insights else None
        result_json = None
        if query_result is not None and len(query_result) > 0:
            result_json = query_result.head(50).to_json(orient='records', force_ascii=False).replace("'", "''")
        
        sql = f"""
        INSERT INTO {schema}.INSIGHTS_MESSAGES (message_id, session_id, role, content, sql_query, query_result, insights)
        VALUES ('{message_id}', '{session_id}', '{role}', $${escaped}$$,
                {f"$${sql_escaped}$$" if sql_escaped else 'NULL'},
                {f"$${result_json}$$" if result_json else 'NULL'},
                {f"$${insights_escaped}$$" if insights_escaped else 'NULL'})
        """
        session.sql(sql).collect()
        return True
    except:
        return False


def load_insights_sessions(session, schema: str, user_id: str, limit: int = 15) -> List[Dict]:
    try:
        sql = f"""
        SELECT session_id, title, updated_at, message_count
        FROM {schema}.INSIGHTS_SESSIONS
        WHERE user_id = '{user_id}'
        ORDER BY updated_at DESC LIMIT {limit}
        """
        result = session.sql(sql).collect()
        return [{"session_id": r['SESSION_ID'], "title": r['TITLE'], 
                 "updated_at": r['UPDATED_AT'], "message_count": r['MESSAGE_COUNT']} for r in result]
    except:
        return []


def load_insights_messages(session, schema: str, session_id: str) -> List[Dict]:
    try:
        sql = f"""
        SELECT message_id, role, content, sql_query, query_result, insights
        FROM {schema}.INSIGHTS_MESSAGES
        WHERE session_id = '{session_id}' ORDER BY created_at ASC
        """
        result = session.sql(sql).collect()
        msgs = []
        for r in result:
            msg = {"message_id": r['MESSAGE_ID'], "role": r['ROLE'], "content": r['CONTENT'],
                   "sql_query": r['SQL_QUERY'], "insights": r['INSIGHTS']}
            if r['QUERY_RESULT']:
                try: msg["data"] = pd.read_json(r['QUERY_RESULT'])
                except: pass
            msgs.append(msg)
        return msgs
    except:
        return []


def delete_insights_session(session, schema: str, session_id: str) -> bool:
    try:
        session.sql(f"DELETE FROM {schema}.INSIGHTS_MESSAGES WHERE session_id = '{session_id}'").collect()
        session.sql(f"DELETE FROM {schema}.INSIGHTS_SESSIONS WHERE session_id = '{session_id}'").collect()
        return True
    except:
        return False


def format_history_for_prompt(messages: List[Dict], max_msgs: int = MAX_HISTORY_MESSAGES,
                              max_chars: int = MAX_HISTORY_CHARS) -> str:
    if not messages:
        return ""
    recent = messages[-max_msgs:]
    parts = []
    total = 0
    for msg in reversed(recent):
        role = "User" if msg["role"] == "user" else "Assistant"
        content = msg.get("content", "")[:500]
        part = f"[{role}]: {content}"
        if total + len(part) > max_chars:
            break
        parts.insert(0, part)
        total += len(part)
    return "## Previous Conversation:\n" + "\n\n".join(parts) + "\n\n---\n" if parts else ""


def generate_title(text: str) -> str:
    return (text[:45] + "...") if len(text) > 45 else text


# ===============================
# Semantic Model Parsing
# ===============================
def parse_semantic_model(yaml_content: str) -> Dict[str, Any]:
    try:
        import yaml
        return yaml.safe_load(yaml_content)
    except:
        return {}


def extract_tables_from_semantic_model(yaml_content: str) -> List[str]:
    model = parse_semantic_model(yaml_content)
    tables = []
    if isinstance(model, dict) and 'tables' in model:
        for t in model['tables']:
            if isinstance(t, dict):
                bt = t.get('base_table', {})
                if isinstance(bt, dict) and bt.get('database') and bt.get('schema') and bt.get('table'):
                    tables.append(f"{bt['database']}.{bt['schema']}.{bt['table']}")
    return tables


# ===============================
# Styles
# ===============================
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;700&display=swap');
:root { --accent-cyan: #00D4FF; --accent-purple: #7B2CBF; --accent-pink: #FF6B6B; }
.stApp { font-family: 'Inter', sans-serif; }
.big-title { font-size: 2.2rem; font-weight: 700; text-align: center; margin-bottom: 0.3rem; }
.title-text { background: linear-gradient(135deg, #00D4FF 0%, #7B2CBF 50%, #FF6B6B 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.greeting-text { font-size: 1.6rem; text-align: center; margin-bottom: 0.3rem; }
.subtitle-text { font-size: 1.2rem; text-align: center; margin-bottom: 1.5rem;
    background: linear-gradient(135deg, #00D4FF 0%, #7B2CBF 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.feature-card { backdrop-filter: blur(16px); border-radius: 16px; padding: 1.5rem; margin: 1rem 0; }
.agent-message { border-left: 3px solid var(--accent-cyan); border-radius: 0 12px 12px 0;
    padding: 1rem; margin: 0.5rem 0; }
.user-message { border-right: 3px solid var(--accent-pink); border-radius: 12px 0 0 12px;
    padding: 1rem; margin: 0.5rem 0; text-align: right; }
.tool-card { border-radius: 8px; padding: 0.5rem; margin: 0.3rem 0; font-size: 0.85rem;
    background: rgba(123, 44, 191, 0.1); }
.semantic-badge { background: linear-gradient(135deg, #00D4FF 0%, #7B2CBF 100%);
    color: white; padding: 0.2rem 0.6rem; border-radius: 15px; font-size: 0.75rem; }
.insights-card { background: rgba(0, 212, 255, 0.05); border: 1px solid rgba(0, 212, 255, 0.2);
    border-radius: 12px; padding: 1rem; margin: 0.5rem 0; }
</style>
"""


# ===============================
# Model Configuration
# ===============================
MODEL_BACKENDS = {
    "External API": {"udf": "SNOWFLAKE_PROD_USER1.CORTEX_ANALYST.QWEN_COMPLETE"},
    "SPCS (Local)": {"udf": "SPCS_CHINA.MODEL_SERVICE.QWEN_COMPLETE"}
}
DEFAULT_BACKEND = "External API"

MODEL_PROVIDERS = {
    "DashScope": {"models": {"qwen-max": "Qwen-Max", "qwen-plus": "Qwen-Plus", "qwen-turbo": "Qwen-Turbo"}, "default": "qwen-max"},
    "DeepSeek": {"models": {"deepseek-chat": "DeepSeek-V3", "deepseek-reasoner": "DeepSeek-R1"}, "default": "deepseek-chat"},
}
DEFAULT_PROVIDER = "DashScope"
DEFAULT_MODEL = "qwen-max"


# ===============================
# LLM Calls
# ===============================
def call_llm(conn, model: str, prompt: str, system_prompt: str = None) -> str:
    backend = st.session_state.get("model_backend", DEFAULT_BACKEND)
    udf = MODEL_BACKENDS[backend]["udf"]
    
    if system_prompt:
        full = f"[System]: {system_prompt}\n\n[User]: {prompt}"
    else:
        full = prompt
    
    escaped = full.replace("'", "''").replace("\\", "\\\\")
    
    try:
        if backend == "SPCS (Local)":
            session = get_snowpark_session()
            result = session.sql(f"SELECT {udf}($${escaped}$$)").collect()
        else:
            cursor = conn.cursor()
            cursor.execute(f"SELECT {udf}('{model}', $${escaped}$$)")
            result = [cursor.fetchone()]
        return result[0][0] if result and result[0][0] else ""
    except Exception as e:
        return f"Error: {str(e)}"


# ===============================
# Database Operations
# ===============================
@st.cache_data(ttl=300)
def fetch_databases(_conn) -> List[str]:
    cursor = _conn.cursor()
    cursor.execute("SHOW DATABASES")
    return [r[1] for r in cursor.fetchall()]

@st.cache_data(ttl=300)
def fetch_schemas(_conn, db: str) -> List[str]:
    cursor = _conn.cursor()
    cursor.execute(f"SHOW SCHEMAS IN DATABASE {db}")
    return [f"{db}.{r[1]}" for r in cursor.fetchall()]

@st.cache_data(ttl=300)
def fetch_stages(_conn, schema: str) -> List[str]:
    cursor = _conn.cursor()
    cursor.execute(f"SHOW STAGES IN {schema}")
    return [f"{schema}.{r[1]}" for r in cursor.fetchall()]

def list_yaml_files(conn, stage: str) -> List[str]:
    try:
        cursor = conn.cursor()
        cursor.execute(f"LIST @{stage}")
        return [r[0] for r in cursor.fetchall() if r[0].endswith(('.yaml', '.yml'))]
    except:
        return []

def load_yaml_from_stage(stage_path: str) -> Optional[str]:
    try:
        session = get_snowpark_session()
        return session.file.get_stream(stage_path).read().decode('utf-8')
    except:
        return None

def execute_sql(conn, sql: str) -> Dict[str, Any]:
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        cols = [d[0] for d in cursor.description]
        df = pd.DataFrame(cursor.fetchall(), columns=cols)
        return {"success": True, "data": df, "row_count": len(df)}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_table_info(conn, table: str) -> Dict[str, Any]:
    try:
        cursor = conn.cursor()
        cursor.execute(f"DESC TABLE {table}")
        cols = [{"name": r[0], "type": r[1]} for r in cursor.fetchall()]
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        cnt = cursor.fetchone()[0]
        return {"success": True, "columns": cols, "row_count": cnt}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ===============================
# Agent Logic
# ===============================
def format_semantic_for_prompt(yaml: str) -> str:
    return f"## Semantic Model\n```yaml\n{yaml}\n```\nUse fully qualified table names and expr from the model."

AGENT_SYSTEM = """You are a data assistant for Snowflake.
{semantic}

## Language Rule:
- Respond in the SAME language as the user's question.
- If user asks in Chinese, respond in Chinese (including thought and response fields).
- If user asks in English, respond in English.

## Tools:
1. execute_sql - Parameters: sql (string)
2. get_table_info - Parameters: table_name (string)

## Response Format:
```json
{{"thought": "...", "tool_call": {{"name": "...", "parameters": {{...}}}}}}
```
or
```json
{{"thought": "...", "response": "..."}}
```
Always use LIMIT 100. Use fully qualified table names."""


def parse_response(text: str) -> Dict:
    import re
    try:
        m = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if m:
            return json.loads(m.group(1))
        s, e = text.find('{'), text.rfind('}') + 1
        if s != -1 and e > s:
            return json.loads(text[s:e])
    except:
        pass
    return {"response": text}


def run_agent(conn, question: str, context: Dict) -> Dict:
    sem = context.get("semantic_model")
    sys_prompt = AGENT_SYSTEM.format(semantic=format_semantic_for_prompt(sem) if sem else "No semantic model loaded.")
    history = format_history_for_prompt(context.get("messages", []))
    
    ctx = ""
    if context.get("last_result") is not None:
        df = context["last_result"]
        ctx = f"\n[Context: Last query returned {len(df)} rows, columns: {', '.join(df.columns[:8])}]\n"
    
    prompt = f"{history}{ctx}\n[Question]: {question}"
    response = call_llm(conn, st.session_state.get("selected_model", DEFAULT_MODEL), prompt, sys_prompt)
    return parse_response(response)


def execute_tool(conn, name: str, params: Dict) -> Dict:
    if name == "execute_sql":
        return execute_sql(conn, params.get("sql", ""))
    elif name == "get_table_info":
        return get_table_info(conn, params.get("table_name", ""))
    return {"success": False, "error": f"Unknown tool: {name}"}


# ===============================
# Insights Logic
# ===============================
INSIGHTS_SYSTEM = """You are a data analyst. Generate SQL based on the semantic model.
{semantic}

Rules:
1. Use fully qualified table names from base_table
2. Use expr from dimensions/measures
3. Always add LIMIT 100
4. Return ONLY valid Snowflake SQL, no explanation"""


def generate_sql(conn, question: str, context: Dict) -> str:
    sem = context.get("semantic_model", "")
    sys = INSIGHTS_SYSTEM.format(semantic=f"```yaml\n{sem}\n```" if sem else "No model")
    
    history = ""
    msgs = context.get("messages", [])
    if msgs:
        recent = msgs[-6:]
        for m in recent:
            if m["role"] == "user":
                history += f"User asked: {m['content'][:100]}\n"
            elif m.get("sql_query"):
                history += f"SQL used: {m['sql_query'][:200]}\n"
    
    prompt = f"{history}\nCurrent question: {question}\n\nGenerate SQL:"
    response = call_llm(conn, st.session_state.get("selected_model", DEFAULT_MODEL), prompt, sys)
    
    # Clean response
    sql = response.strip()
    if "```" in sql:
        lines = []
        in_code = False
        for line in sql.split("\n"):
            if line.startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                lines.append(line)
        sql = "\n".join(lines).strip()
    return sql


ANALYSIS_SYSTEM = """Analyze the data and provide business insights.
{context}

## Language Rule:
- If the user's question is in Chinese, respond entirely in Chinese.
- If the user's question is in English, respond entirely in English.

## Response Format:
1. **Key Findings** (3-5 bullet points summarizing the data)
2. **Business Interpretation** (what this means for the business)
3. **Recommended Actions** (2-3 concrete, actionable next steps the user can take based on this data, such as: investigate specific anomalies, set up alerts, adjust strategy, create reports, etc.)"""


def generate_insights(conn, df: pd.DataFrame, question: str, semantic: str = None) -> str:
    summary = f"Question: {question}\nRows: {len(df)}, Columns: {list(df.columns)}\n"
    summary += f"Sample:\n{df.head(5).to_string()}\n"
    if len(df) > 0:
        summary += f"Stats:\n{df.describe().to_string()}\n"
    
    ctx = summary
    if semantic:
        ctx += f"\nSemantic Model:\n{semantic[:1500]}"
    
    sys = ANALYSIS_SYSTEM.format(context=ctx)
    return call_llm(conn, st.session_state.get("selected_model", DEFAULT_MODEL), 
                    "Analyze this data and provide insights", sys)


# ===============================
# UI Components
# ===============================
def render_msg(role: str, content: str, tool_info: Dict = None):
    cls = "user-message" if role == "user" else "agent-message"
    st.markdown(f'<div class="{cls}">{content}</div>', unsafe_allow_html=True)
    if tool_info:
        st.markdown(f'<div class="tool-card">🔧 {tool_info.get("name")}: {json.dumps(tool_info.get("parameters", {}))}</div>', unsafe_allow_html=True)


def render_data(df: pd.DataFrame, title: str = "Results"):
    st.markdown(f"**{title}** ({len(df)} rows)")
    st.dataframe(df, use_container_width=True, height=min(350, 35 * len(df) + 40))


# ===============================
# Main Application
# ===============================
def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    # Get user info and greeting
    user_id = get_user_id()
    greeting = get_time_greeting()
    
    # Header
    st.markdown('<div class="big-title">❄️ <span class="title-text">Snowflake China Intelligence V3</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="greeting-text">{greeting}</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle-text">What insights can I help you discover?</div>', unsafe_allow_html=True)
    
    # Initialize state
    defaults = {
        "semantic_model": None, "semantic_model_name": None, "semantic_tables": [],
        "model_backend": DEFAULT_BACKEND, "selected_provider": DEFAULT_PROVIDER, "selected_model": DEFAULT_MODEL,
        "history_schema": None, "history_configured": False,
        "agent_session_id": str(uuid.uuid4()), "agent_messages": [], "agent_last_result": None,
        "insights_session_id": str(uuid.uuid4()), "insights_messages": [], "insights_last_result": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    
    try:
        conn = get_snowflake_connection()
        sp_session = get_snowpark_session()
    except Exception as e:
        st.error(f"Connection error: {e}")
        return
    
    # ========== SIDEBAR ==========
    with st.sidebar:
        # === Conversations & History Config ===
        st.markdown("### 💬 Conversations")
        
        # History storage config
        if not st.session_state.history_configured:
            st.info("Configure storage to enable history")
            dbs = fetch_databases(conn)
            hist_db = st.selectbox("Database", dbs, index=None, placeholder="Select...", key="hist_db")
            if hist_db:
                schemas = fetch_schemas(conn, hist_db)
                hist_schema = st.selectbox("Schema", schemas, index=None, placeholder="Select...", 
                                           format_func=lambda x: x.split(".")[-1], key="hist_schema")
                if hist_schema:
                    if st.button("✅ Configure & Setup Tables", type="primary", use_container_width=True):
                        if ensure_all_tables(sp_session, hist_schema):
                            st.session_state.history_schema = hist_schema
                            st.session_state.history_configured = True
                            st.success("Configured!")
                            st.rerun()
                        else:
                            st.error("Failed to create tables")
        else:
            st.success(f"📁 {st.session_state.history_schema.split('.')[-1]}")
            
            # New chat buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("➕ New Agent", use_container_width=True):
                    st.session_state.agent_session_id = str(uuid.uuid4())
                    st.session_state.agent_messages = []
                    st.session_state.agent_last_result = None
                    st.rerun()
            with col2:
                if st.button("➕ New Insights", use_container_width=True):
                    st.session_state.insights_session_id = str(uuid.uuid4())
                    st.session_state.insights_messages = []
                    st.session_state.insights_last_result = None
                    st.rerun()
            
            # History panels
            with st.expander("📜 Agent History"):
                sessions = load_agent_sessions(sp_session, st.session_state.history_schema, user_id)
                for s in sessions:
                    title = s["title"][:25] + "..." if len(s["title"]) > 25 else s["title"]
                    cols = st.columns([4, 1])
                    with cols[0]:
                        if st.button(f"💬 {title}", key=f"ag_{s['session_id']}", use_container_width=True):
                            st.session_state.agent_session_id = s["session_id"]
                            st.session_state.agent_messages = load_agent_messages(sp_session, st.session_state.history_schema, s["session_id"])
                            st.rerun()
                    with cols[1]:
                        if st.button("🗑️", key=f"agd_{s['session_id']}"):
                            delete_agent_session(sp_session, st.session_state.history_schema, s["session_id"])
                            st.rerun()
            
            with st.expander("📜 Insights History"):
                sessions = load_insights_sessions(sp_session, st.session_state.history_schema, user_id)
                for s in sessions:
                    title = s["title"][:25] + "..." if len(s["title"]) > 25 else s["title"]
                    cols = st.columns([4, 1])
                    with cols[0]:
                        if st.button(f"📊 {title}", key=f"in_{s['session_id']}", use_container_width=True):
                            st.session_state.insights_session_id = s["session_id"]
                            st.session_state.insights_messages = load_insights_messages(sp_session, st.session_state.history_schema, s["session_id"])
                            st.rerun()
                    with cols[1]:
                        if st.button("🗑️", key=f"ind_{s['session_id']}"):
                            delete_insights_session(sp_session, st.session_state.history_schema, s["session_id"])
                            st.rerun()
            
            if st.button("🔄 Reset Config", use_container_width=True):
                st.session_state.history_configured = False
                st.session_state.history_schema = None
                st.rerun()
        
        st.markdown("---")
        
        # === Semantic Model ===
        st.markdown("### 📚 Semantic Model")
        
        if st.session_state.semantic_model:
            st.success(f"✅ {st.session_state.semantic_model_name}")
            if st.session_state.semantic_tables:
                for t in st.session_state.semantic_tables[:3]:
                    st.caption(f"• {t.split('.')[-1]}")
            if st.button("🗑️ Unload", use_container_width=True, key="unload_sem"):
                st.session_state.semantic_model = None
                st.session_state.semantic_model_name = None
                st.session_state.semantic_tables = []
                st.rerun()
        else:
            dbs = fetch_databases(conn)
            sem_db = st.selectbox("Database", dbs, index=None, placeholder="Select...", key="sem_db")
            if sem_db:
                schemas = fetch_schemas(conn, sem_db)
                sem_schema = st.selectbox("Schema", schemas, index=None, placeholder="Select...",
                                          format_func=lambda x: x.split(".")[-1], key="sem_schema")
                if sem_schema:
                    stages = fetch_stages(conn, sem_schema)
                    if stages:
                        stage = st.selectbox("Stage", stages, format_func=lambda x: x.split(".")[-1], key="sem_stage")
                        yamls = list_yaml_files(conn, stage)
                        if yamls:
                            yaml_file = st.selectbox("YAML", yamls, format_func=lambda x: x.split("/")[-1], key="yaml_file")
                            if st.button("📥 Load", type="primary", use_container_width=True):
                                content = load_yaml_from_stage(f"@{stage}/{yaml_file.split('/')[-1]}")
                                if content:
                                    st.session_state.semantic_model = content
                                    st.session_state.semantic_model_name = yaml_file.split("/")[-1]
                                    st.session_state.semantic_tables = extract_tables_from_semantic_model(content)
                                    st.rerun()
        
        st.markdown("---")
        
        # === Model Selection ===
        st.markdown("### 🧠 LLM Model")
        backend = st.radio("Backend", list(MODEL_BACKENDS.keys()), 
                          index=list(MODEL_BACKENDS.keys()).index(st.session_state.model_backend),
                          horizontal=True, key="backend")
        st.session_state.model_backend = backend
        
        if backend == "External API":
            provider = st.selectbox("Provider", list(MODEL_PROVIDERS.keys()),
                                   index=list(MODEL_PROVIDERS.keys()).index(st.session_state.selected_provider),
                                   key="provider")
            st.session_state.selected_provider = provider
            models = MODEL_PROVIDERS[provider]["models"]
            model = st.selectbox("Model", list(models.keys()), format_func=lambda x: models[x], key="model")
            st.session_state.selected_model = model
        
        st.markdown("---")
        st.caption(f"v{APP_VERSION}")
    
    # ========== MAIN CONTENT ==========
    tab1, tab2, tab3 = st.tabs(["🤖 Agent Chat", "📈 Data Insights", "🔧 Toolbox"])
    
    # ===== TAB 1: Agent Chat =====
    with tab1:
        if st.session_state.semantic_model:
            st.markdown(f'<div class="feature-card"><span class="semantic-badge">🎯 Semantic Active</span> <strong>{st.session_state.semantic_model_name}</strong></div>', unsafe_allow_html=True)
        else:
            st.warning("Load a semantic model for best results")
        
        # Messages
        for msg in st.session_state.agent_messages:
            render_msg(msg["role"], msg["content"], msg.get("tool_info"))
            if msg.get("data") is not None:
                render_data(msg["data"])
        
        # Input
        def submit_agent():
            if st.session_state.agent_input:
                st.session_state.agent_question = st.session_state.agent_input
                st.session_state.agent_input = ""
        
        cols = st.columns([5, 1])
        with cols[0]:
            st.text_input("Question", key="agent_input", placeholder="Ask about your data...",
                         label_visibility="collapsed", on_change=submit_agent)
        with cols[1]:
            if st.button("Send", type="primary", use_container_width=True, key="agent_send"):
                submit_agent()
        
        question = st.session_state.pop("agent_question", None)
        if question:
            # Add user message
            user_msg = {"role": "user", "content": question, "message_id": str(uuid.uuid4())}
            st.session_state.agent_messages.append(user_msg)
            
            # Save
            if st.session_state.history_configured:
                schema = st.session_state.history_schema
                if len(st.session_state.agent_messages) == 1:
                    save_agent_session(sp_session, schema, st.session_state.agent_session_id, 
                                      user_id, generate_title(question), st.session_state.semantic_model_name)
                save_agent_message(sp_session, schema, st.session_state.agent_session_id,
                                  user_msg["message_id"], "user", question)
            
            # Run agent
            ctx = {"semantic_model": st.session_state.semantic_model,
                   "messages": st.session_state.agent_messages,
                   "last_result": st.session_state.agent_last_result}
            
            with st.spinner("🤔 Thinking..."):
                resp = run_agent(conn, question, ctx)
            
            thought = resp.get("thought", "")
            tool_call = resp.get("tool_call")
            direct = resp.get("response")
            
            asst_msg = {"role": "assistant", "content": "", "message_id": str(uuid.uuid4())}
            
            if tool_call:
                name, params = tool_call.get("name"), tool_call.get("parameters", {})
                asst_msg["tool_info"] = {"name": name, "parameters": params}
                
                with st.spinner(f"🔧 {name}..."):
                    result = execute_tool(conn, name, params)
                
                if result.get("success"):
                    if "data" in result:
                        asst_msg["data"] = result["data"]
                        st.session_state.agent_last_result = result["data"]
                        asst_msg["content"] = f"{thought}\n\n✅ {result['row_count']} rows returned"
                    else:
                        asst_msg["content"] = f"{thought}\n\n✅ Success"
                else:
                    asst_msg["content"] = f"{thought}\n\n❌ {result.get('error')}"
            elif direct:
                asst_msg["content"] = direct
            else:
                asst_msg["content"] = str(resp)
            
            st.session_state.agent_messages.append(asst_msg)
            
            # Save assistant
            if st.session_state.history_configured:
                save_agent_message(sp_session, st.session_state.history_schema,
                                  st.session_state.agent_session_id, asst_msg["message_id"],
                                  "assistant", asst_msg["content"], asst_msg.get("tool_info"), asst_msg.get("data"))
                save_agent_session(sp_session, st.session_state.history_schema,
                                  st.session_state.agent_session_id, user_id,
                                  generate_title(st.session_state.agent_messages[0]["content"]))
            
            st.rerun()
    
    # ===== TAB 2: Data Insights (Multi-turn) =====
    with tab2:
        if st.session_state.semantic_model:
            st.markdown(f'<div class="feature-card"><span class="semantic-badge">🎯 Semantic Active</span> <strong>{st.session_state.semantic_model_name}</strong></div>', unsafe_allow_html=True)
        else:
            st.warning("Load a semantic model for best results")
        
        # Show conversation history
        for msg in st.session_state.insights_messages:
            if msg["role"] == "user":
                st.markdown(f'<div class="user-message">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="agent-message">{msg["content"]}</div>', unsafe_allow_html=True)
                if msg.get("sql_query"):
                    with st.expander("📝 SQL Query"):
                        st.code(msg["sql_query"], language="sql")
                if msg.get("data") is not None:
                    render_data(msg["data"], "Query Results")
                if msg.get("insights"):
                    st.markdown('<div class="insights-card">', unsafe_allow_html=True)
                    st.markdown("### 💡 AI Insights")
                    st.markdown(msg["insights"])
                    st.markdown('</div>', unsafe_allow_html=True)
        
        # Input area
        st.markdown("---")
        
        def submit_insights():
            if st.session_state.insights_input:
                st.session_state.insights_question = st.session_state.insights_input
                st.session_state.insights_input = ""
        
        cols = st.columns([5, 1])
        with cols[0]:
            st.text_input("Question", key="insights_input", 
                         placeholder="输入问题分析数据 / Ask about your data...",
                         label_visibility="collapsed", on_change=submit_insights)
        with cols[1]:
            if st.button("Analyze", type="primary", use_container_width=True, key="insights_send"):
                submit_insights()
        
        question = st.session_state.pop("insights_question", None)
        if question:
            # Add user message
            user_msg = {"role": "user", "content": question, "message_id": str(uuid.uuid4())}
            st.session_state.insights_messages.append(user_msg)
            
            # Save user message
            if st.session_state.history_configured:
                schema = st.session_state.history_schema
                if len(st.session_state.insights_messages) == 1:
                    save_insights_session(sp_session, schema, st.session_state.insights_session_id,
                                         user_id, generate_title(question), st.session_state.semantic_model_name)
                save_insights_message(sp_session, schema, st.session_state.insights_session_id,
                                     user_msg["message_id"], "user", question)
            
            # Show user question immediately
            st.markdown(f'<div class="user-message">{question}</div>', unsafe_allow_html=True)
            
            # Generate SQL
            ctx = {"semantic_model": st.session_state.semantic_model,
                   "messages": st.session_state.insights_messages}
            
            with st.spinner("🧠 Generating SQL..."):
                sql = generate_sql(conn, question, ctx)
            
            asst_msg = {"role": "assistant", "content": "", "message_id": str(uuid.uuid4()),
                       "sql_query": sql, "insights": None}
            
            # Execute query
            with st.spinner("⚡ Executing query..."):
                result = execute_sql(conn, sql)
            
            if result["success"]:
                df = result["data"]
                asst_msg["data"] = df
                asst_msg["content"] = f"Query returned {result['row_count']} rows"
                st.session_state.insights_last_result = df
                
                # Show SQL and data immediately (before insights)
                with st.expander("📝 SQL Query", expanded=False):
                    st.code(sql, language="sql")
                st.markdown(f"**Query Results** ({result['row_count']} rows)")
                st.dataframe(df, use_container_width=True, height=min(350, 35 * len(df) + 40))
                
                # Now generate insights with spinner
                insights_placeholder = st.empty()
                with insights_placeholder.container():
                    with st.spinner("💡 Generating insights..."):
                        insights = generate_insights(conn, df, question, st.session_state.semantic_model)
                
                # Display insights
                insights_placeholder.empty()
                st.markdown('<div class="insights-card">', unsafe_allow_html=True)
                st.markdown("### 💡 AI Insights")
                st.markdown(insights)
                st.markdown('</div>', unsafe_allow_html=True)
                asst_msg["insights"] = insights
            else:
                asst_msg["content"] = f"❌ Query failed: {result['error']}"
                st.error(asst_msg["content"])
            
            st.session_state.insights_messages.append(asst_msg)
            
            # Save assistant message
            if st.session_state.history_configured:
                save_insights_message(sp_session, st.session_state.history_schema,
                                     st.session_state.insights_session_id, asst_msg["message_id"],
                                     "assistant", asst_msg["content"], asst_msg.get("sql_query"),
                                     asst_msg.get("data"), asst_msg.get("insights"))
                save_insights_session(sp_session, st.session_state.history_schema,
                                     st.session_state.insights_session_id, user_id,
                                     generate_title(st.session_state.insights_messages[0]["content"]))
            
            # Rerun to position input box after new content
            st.rerun()
    
    # ===== TAB 3: Toolbox =====
    with tab3:
        st.markdown("### 🔧 Toolbox")
        
        tabs = st.tabs(["SQL Query", "Table Info", "Semantic Preview"])
        
        with tabs[0]:
            sql_input = st.text_area("SQL", height=150, placeholder="SELECT * FROM db.schema.table LIMIT 10")
            if st.button("▶️ Execute", key="exec_sql"):
                if sql_input:
                    with st.spinner("Executing..."):
                        result = execute_sql(conn, sql_input)
                    if result["success"]:
                        st.success(f"{result['row_count']} rows")
                        render_data(result["data"])
                    else:
                        st.error(result["error"])
        
        with tabs[1]:
            tables = st.session_state.semantic_tables
            if tables:
                t = st.selectbox("Table", tables, format_func=lambda x: x.split(".")[-1])
                if st.button("🔍 View"):
                    info = get_table_info(conn, t)
                    if info["success"]:
                        st.markdown(f"**{t}** ({info['row_count']:,} rows)")
                        st.dataframe(pd.DataFrame(info["columns"]), use_container_width=True)
                    else:
                        st.error(info["error"])
            else:
                st.info("Load semantic model first")
        
        with tabs[2]:
            if st.session_state.semantic_model:
                st.code(st.session_state.semantic_model, language="yaml")
            else:
                st.info("No semantic model loaded")


if __name__ == "__main__":
    main()
