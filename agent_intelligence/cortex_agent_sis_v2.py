"""
Cortex Agent & Intelligence Demo App for Snowflake China Region
Streamlit in Snowflake (SiS) Version
Using LLM APIs to simulate Cortex Agent and Cortex Intelligence features
Supports Semantic Model for enhanced SQL generation
"""

import json
import uuid
import pandas as pd
import streamlit as st
from datetime import datetime
from typing import Any, Dict, List, Optional

# Page configuration
st.set_page_config(
    layout="wide",
    page_icon="❄️",
    page_title="Snowflake China Intelligence V2",
    initial_sidebar_state="expanded"
)

# SiS environment detection and connection
def get_snowflake_connection():
    """Get Snowflake connection"""
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
    return session.connection

def get_snowpark_session():
    """Get Snowpark Session"""
    from snowflake.snowpark.context import get_active_session
    return get_active_session()

def ensure_warehouse():
    """Ensure warehouse is set for session - call this early in the app"""
    if "warehouse_set" not in st.session_state:
        try:
            session = get_snowpark_session()
            # Try to use COMPUTE_WH
            session.sql("USE WAREHOUSE COMPUTE_WH").collect()
            st.session_state["warehouse_set"] = True
        except Exception as e:
            # If COMPUTE_WH fails, try to find any available warehouse
            try:
                session = get_snowpark_session()
                wh_list = session.sql("SHOW WAREHOUSES").collect()
                if wh_list:
                    wh_name = wh_list[0]['name']
                    session.sql(f"USE WAREHOUSE {wh_name}").collect()
                    st.session_state["warehouse_set"] = True
            except Exception:
                pass

# Initialize warehouse at app startup
ensure_warehouse()

# ===============================
# Style definitions (Light and Dark mode support)
# ===============================
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Inter:wght@300;400;500;700&display=swap');

/* ===== Common variables ===== */
:root {
    --primary-gradient: linear-gradient(135deg, #00D4FF 0%, #7B2CBF 50%, #FF6B6B 100%);
    --accent-cyan: #00D4FF;
    --accent-purple: #7B2CBF;
    --accent-pink: #FF6B6B;
}

/* ===== Dark Mode (default) ===== */
[data-testid="stAppViewContainer"],
.stApp {
    font-family: 'Inter', 'JetBrains Mono', sans-serif;
}

/* Big title style */
.big-title {
    font-size: 2.2rem;
    font-weight: 700;
    text-align: center;
    margin-bottom: 0.3rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
}

.big-title .snowflake-icon {
    font-size: 2rem;
}

.big-title .title-text {
    background: var(--primary-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* Greeting style */
.greeting-text {
    font-size: 1.8rem;
    font-weight: 400;
    text-align: center;
    margin-bottom: 0.3rem;
}

/* Subtitle style */
.subtitle-text {
    font-size: 1.3rem;
    font-weight: 500;
    text-align: center;
    margin-bottom: 1.5rem;
    background: linear-gradient(135deg, #00D4FF 0%, #7B2CBF 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* Feature Card */
.feature-card {
    backdrop-filter: blur(16px);
    border-radius: 16px;
    padding: 1.5rem;
    margin: 1rem 0;
}

/* Agent Message */
.agent-message {
    border-left: 3px solid var(--accent-cyan);
    border-radius: 0 12px 12px 0;
    padding: 1rem 1.25rem;
    margin: 0.75rem 0;
}

/* User Message */
.user-message {
    border-right: 3px solid var(--accent-pink);
    border-radius: 12px 0 0 12px;
    padding: 1rem 1.25rem;
    margin: 0.75rem 0;
    text-align: right;
}

/* Tool Card */
.tool-card {
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin: 0.5rem 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
}

/* Semantic Badge */
.semantic-badge {
    background: linear-gradient(135deg, #00D4FF 0%, #7B2CBF 100%);
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 500;
}

/* Metric Card */
.metric-card {
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

/* ===== Dark Mode specific styles ===== */
@media (prefers-color-scheme: dark) {
    .greeting-text {
        color: #E8E8E8;
    }
    .feature-card {
        background: rgba(17, 25, 40, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.125);
    }
    .agent-message {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(123, 44, 191, 0.1) 100%);
    }
    .user-message {
        background: rgba(255, 107, 107, 0.1);
    }
    .tool-card {
        background: rgba(123, 44, 191, 0.15);
        border: 1px solid rgba(123, 44, 191, 0.3);
    }
    .metric-card {
        background: rgba(17, 25, 40, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.125);
    }
    .metric-label {
        color: #A0A0A0;
    }
}

/* ===== Light Mode specific styles ===== */
@media (prefers-color-scheme: light) {
    .greeting-text {
        color: #1a1a2e;
    }
    .feature-card {
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(0, 0, 0, 0.1);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    .agent-message {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.08) 0%, rgba(123, 44, 191, 0.08) 100%);
    }
    .user-message {
        background: rgba(255, 107, 107, 0.08);
    }
    .tool-card {
        background: rgba(123, 44, 191, 0.08);
        border: 1px solid rgba(123, 44, 191, 0.2);
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(0, 0, 0, 0.1);
    }
    .metric-label {
        color: #666666;
    }
}

/* Streamlit theme adaptation */
[data-theme="light"] .greeting-text,
[data-baseweb="light"] .greeting-text {
    color: #1a1a2e;
}

[data-theme="dark"] .greeting-text,
[data-baseweb="dark"] .greeting-text {
    color: #E8E8E8;
}
</style>
"""

# ===============================
# Model Backend Configuration (SPCS or External API)
# ===============================
MODEL_BACKENDS = {
    "SPCS (Local)": {
        "description": "Snowflake Container Services locally deployed model, data stays in cloud",
        "icon": "🏠",
        "udf_path": "SPCS_CHINA.MODEL_SERVICE.QWEN_COMPLETE"
    },
    "External API": {
        "description": "Call external LLM APIs (DashScope/DeepSeek/Kimi etc.)",
        "icon": "🌐",
        "udf_path": "SNOWFLAKE_PROD_USER1.CORTEX_ANALYST.QWEN_COMPLETE"
    }
}

DEFAULT_BACKEND = "External API"

# ===============================
# SPCS Model Configuration
# ===============================
SPCS_MODELS = {
    "Qwen/Qwen2.5-1.5B-Instruct": "Qwen2.5-1.5B (SPCS Deployed)",
}

# ===============================
# External API Model Provider Configuration
# ===============================
MODEL_PROVIDERS = {
    "DashScope (Qwen)": {
        "models": {
            "qwen-max": "Qwen-Max (Recommended, Most Capable)",
            "qwen-plus": "Qwen-Plus (Balanced)",
            "qwen-turbo": "Qwen-Turbo (Fast Response)",
            "qwen-max-longcontext": "Qwen-Max-LongContext (Long Text)",
            "qwen2.5-72b-instruct": "Qwen2.5-72B-Instruct",
            "qwen2.5-32b-instruct": "Qwen2.5-32B-Instruct",
        },
        "default": "qwen-max"
    },
    "DeepSeek": {
        "models": {
            "deepseek-chat": "DeepSeek-V3 (Recommended)",
            "deepseek-reasoner": "DeepSeek-R1 (Deep Reasoning)",
        },
        "default": "deepseek-chat"
    },
    "Kimi (Moonshot)": {
        "models": {
            "moonshot-v1-8k": "Moonshot-v1-8K",
            "moonshot-v1-32k": "Moonshot-v1-32K",
            "moonshot-v1-128k": "Moonshot-v1-128K (Long Text)",
        },
        "default": "moonshot-v1-8k"
    },
    "MiniMax": {
        "models": {
            "abab6.5s-chat": "ABAB6.5s (Fast)",
            "abab6.5-chat": "ABAB6.5 (Standard)",
            "abab5.5-chat": "ABAB5.5",
        },
        "default": "abab6.5s-chat"
    },
}

DEFAULT_PROVIDER = "DashScope (Qwen)"
DEFAULT_MODEL = "qwen-max"


# ===============================
# Get Current User Info
# ===============================
def get_current_user_info() -> Dict[str, str]:
    """Get current user information from Snowflake session"""
    try:
        # Method 1: Try st.experimental_user (Streamlit in Snowflake)
        if hasattr(st, 'experimental_user') and st.experimental_user:
            user_info = st.experimental_user
            # user_info may contain: user_name, email, etc.
            if hasattr(user_info, 'user_name'):
                return {"username": user_info.user_name, "email": getattr(user_info, 'email', '')}
        
        # Method 2: Query Snowflake for current user
        session = get_snowpark_session()
        result = session.sql("SELECT CURRENT_USER() as username").collect()
        if result:
            username = result[0]['USERNAME']
            # Try to get first name from DESCRIBE USER (may require privileges)
            try:
                user_desc = session.sql(f"DESCRIBE USER {username}").collect()
                first_name = None
                for row in user_desc:
                    if row['property'] == 'FIRST_NAME' and row['value']:
                        first_name = row['value']
                        break
                if first_name:
                    return {"username": username, "first_name": first_name}
            except Exception:
                pass
            return {"username": username}
    except Exception:
        pass
    
    return {"username": "there"}


def get_display_name() -> str:
    """Get a friendly display name for the current user"""
    user_info = get_current_user_info()
    
    # Priority: first_name > parsed username > default
    if 'first_name' in user_info and user_info['first_name']:
        return user_info['first_name']
    
    username = user_info.get('username', 'there')
    
    # Try to extract a readable name from username
    # e.g., "JOHN_DOE" -> "John", "john.doe@company.com" -> "John"
    if username and username != 'there':
        # Remove email domain if present
        name_part = username.split('@')[0]
        # Split by common separators
        for sep in ['_', '.', '-']:
            if sep in name_part:
                name_part = name_part.split(sep)[0]
                break
        # Capitalize properly
        return name_part.capitalize()
    
    return "there"


# ===============================
# Time-based Greeting (China Timezone UTC+8)
# ===============================
def get_time_greeting(username: str = None) -> str:
    """Generate greeting based on China timezone"""
    from datetime import timezone, timedelta
    
    # Get username if not provided
    if username is None:
        username = get_display_name()
    
    china_tz = timezone(timedelta(hours=8))
    china_time = datetime.now(china_tz)
    current_hour = china_time.hour
    
    if 5 <= current_hour < 12:
        greeting = f"Good morning, {username}"
    elif 12 <= current_hour < 18:
        greeting = f"Good afternoon, {username}"
    elif 18 <= current_hour < 22:
        greeting = f"Good evening, {username}"
    else:
        greeting = f"Good night, {username}"
    
    return greeting


# ===============================
# LLM Calls (SPCS and External API support)
# ===============================

def call_spcs_model(conn, model: str, prompt: str, system_prompt: str = None) -> str:
    """Call locally deployed model via SPCS service"""
    
    # Combine system prompt and user prompt
    full_prompt = prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\n{prompt}"
    
    escaped_prompt = full_prompt.replace("'", "''")
    
    udf_path = MODEL_BACKENDS["SPCS (Local)"]["udf_path"]
    query = f"SELECT {udf_path}('{escaped_prompt}')"
    
    try:
        # Use Snowpark session for better SiS compatibility
        session = get_snowpark_session()
        
        # Ensure warehouse is active (required for Service Function calls)
        try:
            wh_result = session.sql("SELECT CURRENT_WAREHOUSE()").collect()
            if not wh_result or not wh_result[0][0]:
                session.sql("USE WAREHOUSE COMPUTE_WH").collect()
        except Exception:
            try:
                session.sql("USE WAREHOUSE COMPUTE_WH").collect()
            except Exception:
                pass
        
        result = session.sql(query).collect()
        if result and result[0][0]:
            return result[0][0]
        return ""
    except Exception as e:
        return f"SPCS call error: {str(e)}"


def call_external_api(conn, model: str, prompt: str, system_prompt: str = None) -> str:
    """Call LLM via external API UDF"""
    escaped_prompt = prompt.replace("'", "''").replace("\\", "\\\\")
    
    if system_prompt:
        escaped_system = system_prompt.replace("'", "''").replace("\\", "\\\\")
        full_prompt = f"[System]: {escaped_system}\n\n[User]: {escaped_prompt}"
    else:
        full_prompt = escaped_prompt
    
    udf_path = MODEL_BACKENDS["External API"]["udf_path"]
    query = f"SELECT {udf_path}('{model}', $${full_prompt}$$)"
    
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        if result and result[0]:
            return result[0]
        return ""
    except Exception as e:
        return f"External API call error: {str(e)}"


def call_llm(conn, model: str, prompt: str, system_prompt: str = None) -> str:
    """Unified LLM call interface, routes to different backends based on selection"""
    backend = st.session_state.get("model_backend", DEFAULT_BACKEND)
    
    if backend == "SPCS (Local)":
        return call_spcs_model(conn, model, prompt, system_prompt)
    else:
        return call_external_api(conn, model, prompt, system_prompt)


def call_qwen_udf(conn, model: str, prompt: str, system_prompt: str = None) -> str:
    """Call LLM via Snowflake UDF (backward compatible)"""
    return call_llm(conn, model, prompt, system_prompt)


# ===============================
# Semantic Model Management
# ===============================
def load_semantic_model_from_stage(conn, stage_path: str) -> Optional[str]:
    """Load semantic model YAML from Stage"""
    try:
        session = get_snowpark_session()
        yaml_content = session.file.get_stream(stage_path).read().decode('utf-8')
        return yaml_content
    except Exception as e:
        st.warning(f"Cannot load semantic model: {e}")
        return None

def list_yaml_files_in_stage(conn, stage_name: str) -> List[str]:
    """List YAML files in Stage"""
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
    """Parse semantic model YAML to structured data"""
    try:
        import yaml
        model = yaml.safe_load(yaml_content)
        return model
    except Exception:
        return {"raw": yaml_content}

def format_semantic_model_for_prompt(yaml_content: str) -> str:
    """Format semantic model for LLM prompt"""
    return f"""
## Semantic Model Definition (YAML)

Below is the semantic model for the data, containing table structures, business meanings, metric definitions and relationships:

```yaml
{yaml_content}
```

Please use this semantic model to understand the business meaning of the data:
- **name**: Field name in the semantic layer
- **description**: Business meaning description
- **expr**: SQL expression for the field
- **synonyms**: Alternative terms users may use to refer to this field
- **sample_values**: Example values
- **data_type**: Data type
"""


# ===============================
# Database Operations
# ===============================
@st.cache_data(ttl=300)
def fetch_databases(_conn) -> List[str]:
    """Get available database list"""
    cursor = _conn.cursor()
    cursor.execute("SHOW DATABASES")
    return [row[1] for row in cursor.fetchall()]

@st.cache_data(ttl=300)
def fetch_schemas(_conn, database: str) -> List[str]:
    """Get schema list for specified database"""
    cursor = _conn.cursor()
    cursor.execute(f"SHOW SCHEMAS IN DATABASE {database}")
    return [f"{database}.{row[1]}" for row in cursor.fetchall()]

@st.cache_data(ttl=300)
def fetch_tables(_conn, schema: str) -> List[str]:
    """Get table list for specified schema"""
    cursor = _conn.cursor()
    cursor.execute(f"SHOW TABLES IN {schema}")
    tables = [f"{schema}.{row[1]}" for row in cursor.fetchall()]
    cursor.execute(f"SHOW VIEWS IN {schema}")
    views = [f"{schema}.{row[1]}" for row in cursor.fetchall()]
    return tables + views

@st.cache_data(ttl=300)
def fetch_stages(_conn, schema: str) -> List[str]:
    """Get stage list for specified schema"""
    cursor = _conn.cursor()
    cursor.execute(f"SHOW STAGES IN {schema}")
    return [f"{schema}.{row[1]}" for row in cursor.fetchall()]

def execute_sql(conn, sql: str) -> Dict[str, Any]:
    """Execute SQL query"""
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
    """Get table structure information"""
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
# Agent Core Logic (Semantic Model Support)
# ===============================
AGENT_SYSTEM_PROMPT_WITH_SEMANTIC = """You are a professional data analysis assistant running in Snowflake environment.

## Important: Semantic Model

You must refer to the following semantic model to understand business meanings. The semantic model defines:
- Business names and descriptions of fields
- Formulas for calculated metrics
- Synonyms for fields (users may use different terms)
- Relationships between tables

{semantic_model}

## Available Tools:

1. **execute_sql** - Execute SQL query
   Parameters: sql (string) - SQL query statement

2. **get_table_info** - Get table information
   Parameters: table_name (string) - Fully qualified table name

## Response Format:

When calling a tool, use this JSON format:
```json
{{
  "thought": "Your thinking process, including how to understand user intent based on semantic model",
  "tool_call": {{
    "name": "tool_name",
    "parameters": {{
      "param_name": "param_value"
    }}
  }}
}}
```

When answering directly without tools:
```json
{{
  "thought": "Your thinking process",
  "response": "Your answer content"
}}
```

## Important Rules:

1. **Must refer to semantic model**: Use description and synonyms to understand user questions
2. **Use correct expressions**: Use expr defined in semantic model as SQL field expressions
3. **Understand business terms**: Users may use business terms instead of field names, map them correctly
4. SQL queries must be valid Snowflake SQL syntax
5. Answer in English

Current Context:
- Database: {database}
- Schema: {schema}
"""

AGENT_SYSTEM_PROMPT_WITHOUT_SEMANTIC = """You are a professional data analysis assistant running in Snowflake environment.

## Available Tools:

1. **execute_sql** - Execute SQL query
   Parameters: sql (string) - SQL query statement

2. **get_table_info** - Get table information
   Parameters: table_name (string) - Fully qualified table name

## Response Format:

When calling a tool:
```json
{{
  "thought": "Your thinking process",
  "tool_call": {{
    "name": "tool_name",
    "parameters": {{"param_name": "param_value"}}
  }}
}}
```

When answering directly:
```json
{{
  "thought": "Your thinking process",
  "response": "Your answer content"
}}
```

Please answer in English.

Current Context:
- Database: {database}
- Schema: {schema}
- Available Tables: {tables}
"""


def parse_agent_response(response: str) -> Dict[str, Any]:
    """Parse Agent response"""
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
    """Run Agent"""
    semantic_model = context.get("semantic_model")
    
    if semantic_model:
        formatted_model = format_semantic_model_for_prompt(semantic_model)
        system_prompt = AGENT_SYSTEM_PROMPT_WITH_SEMANTIC.format(
            semantic_model=formatted_model,
            database=context.get("database", "Not selected"),
            schema=context.get("schema", "Not selected")
        )
    else:
        system_prompt = AGENT_SYSTEM_PROMPT_WITHOUT_SEMANTIC.format(
            database=context.get("database", "Not selected"),
            schema=context.get("schema", "Not selected"),
            tables=", ".join(context.get("tables", [])[:10])
        )
    
    messages = context.get("messages", [])
    history_text = ""
    for msg in messages[-6:]:
        role = "User" if msg["role"] == "user" else "Assistant"
        history_text += f"\n{role}: {msg['content']}\n"
    
    full_prompt = f"{history_text}\nUser: {user_input}"
    
    model = st.session_state.get("selected_model", DEFAULT_MODEL)
    response = call_qwen_udf(conn, model, full_prompt, system_prompt)
    parsed = parse_agent_response(response)
    
    return parsed


def execute_tool_call(conn, tool_name: str, parameters: Dict, context: Dict) -> Dict[str, Any]:
    """Execute tool call"""
    if tool_name == "execute_sql":
        return execute_sql(conn, parameters.get("sql", ""))
    elif tool_name == "get_table_info":
        return get_table_info(conn, parameters.get("table_name", ""))
    else:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}


# ===============================
# Intelligence Features (Semantic Model Support)
# ===============================
def generate_data_insights(conn, df: pd.DataFrame, context: str = "", semantic_model: str = None) -> str:
    """Generate data insights using AI"""
    summary = f"""
Data Overview:
- Rows: {len(df)}
- Columns: {len(df.columns)}
- Column Names: {', '.join(df.columns.tolist())}

Statistics:
{df.describe().to_string() if len(df) > 0 else 'No data'}

Sample Data (first 5 rows):
{df.head().to_string() if len(df) > 0 else 'No data'}
"""
    
    semantic_context = ""
    if semantic_model:
        semantic_context = f"""
## Semantic Model Reference
The semantic model below defines business meanings of the data, use it to interpret:
```yaml
{semantic_model[:2000]}
```
"""
    
    prompt = f"""Please analyze the following data and provide professional business insights:

{summary}

{semantic_context}

{f"Query Context: {context}" if context else ""}

Please provide:
1. Key findings (3-5 points)
2. Business interpretation based on semantic model
3. Suggested follow-up analysis directions

Please answer in professional but easy-to-understand English.
"""
    
    model = st.session_state.get("selected_model", DEFAULT_MODEL)
    return call_qwen_udf(conn, model, prompt)


def generate_sql_from_question(conn, question: str, schema_info: Dict, tables: List[str], semantic_model: str = None) -> str:
    """Generate SQL from natural language question (with semantic model support)"""
    
    semantic_context = ""
    if semantic_model:
        semantic_context = f"""
## Important: Semantic Model

Please use the following semantic model to understand business meanings and generate correct SQL:

```yaml
{semantic_model}
```

Rules:
1. Use description in semantic model to understand field meanings
2. Use expr in semantic model as SQL expressions
3. Refer to synonyms to match business terms used by user
4. If user asks about metrics defined in semantic model, use the defined calculation formulas
"""
    
    # Build table list with explicit full paths
    table_list_str = "\n".join([f"- {t}" for t in tables])
    
    # Get example full table name for the prompt
    example_table = tables[0] if tables else "DATABASE.SCHEMA.TABLE"
    
    prompt = f"""Please generate a Snowflake SQL query based on the following question:

Question: {question}

{semantic_context}

Available Tables (MUST use these EXACT full names in your SQL):
{table_list_str}

Table Schema Information:
{json.dumps(schema_info, indent=2, ensure_ascii=False)}

CRITICAL REQUIREMENTS:
1. MUST use fully qualified table names with database.schema.table format
   - CORRECT: SELECT * FROM {example_table}
   - WRONG: SELECT * FROM {example_table.split('.')[-1] if '.' in example_table else 'TABLE_NAME'}
2. Generate valid Snowflake SQL only
3. Return ONLY the SQL statement, no explanation or markdown
4. Add LIMIT 100 to limit results
5. If semantic model exists, must refer to field definitions and expressions

SQL:
"""
    
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
    """Suggest questions based on table structure and semantic model"""
    
    semantic_context = ""
    if semantic_model:
        semantic_context = f"""
Semantic Model (contains business definitions):
```yaml
{semantic_model[:1500]}
```

Please suggest questions based on metrics and dimensions defined in the semantic model.
"""
    
    prompt = f"""Based on the following data information, suggest 5 valuable data analysis questions:

Available Tables: {', '.join(tables[:5])}

Table Schema Information:
{json.dumps(schema_info, indent=2, ensure_ascii=False)}

{semantic_context}

Please generate 5 specific, actionable data analysis questions, one per line.
If there's a semantic model, use business terms defined in it.
Output only questions, no numbering.
"""
    
    response = call_qwen_udf(conn, "qwen-turbo", prompt)
    questions = [q.strip() for q in response.strip().split('\n') if q.strip()]
    return questions[:5]


# ===============================
# UI Components
# ===============================
def render_message(role: str, content: str, tool_info: Dict = None):
    """Render chat message"""
    if role == "user":
        st.markdown(f'<div class="user-message">{content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="agent-message">{content}</div>', unsafe_allow_html=True)
        if tool_info:
            st.markdown(f"""
            <div class="tool-card">
                🔧 Tool Call: <strong>{tool_info.get('name', 'unknown')}</strong><br>
                Parameters: {json.dumps(tool_info.get('parameters', {}), ensure_ascii=False)}
            </div>
            """, unsafe_allow_html=True)


def render_data_preview(df: pd.DataFrame, title: str = "Data Preview"):
    """Render data preview"""
    st.markdown(f"### 📊 {title}")
    st.dataframe(
        df,
        use_container_width=True,
        height=min(400, 35 * len(df) + 38)
    )


# ===============================
# Main Application
# ===============================
def main():
    # Inject custom styles
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    # Get time-based greeting (automatically gets current user's name)
    greeting = get_time_greeting()
    
    # Big title + greeting + subtitle
    st.markdown('''
    <div class="big-title">
        <span class="snowflake-icon">❄️</span>
        <span class="title-text">Snowflake China Intelligence V2</span>
    </div>
    ''', unsafe_allow_html=True)
    st.markdown(f'<div class="greeting-text">{greeting}</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle-text">What insights can I help you discover?</div>', unsafe_allow_html=True)
    
    # Initialize session state
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
    
    if "model_backend" not in st.session_state:
        st.session_state.model_backend = DEFAULT_BACKEND
    
    if "selected_provider" not in st.session_state:
        st.session_state.selected_provider = DEFAULT_PROVIDER
    
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = DEFAULT_MODEL
    
    # Get connection
    try:
        conn = get_snowflake_connection()
    except Exception as e:
        st.error(f"Cannot connect to Snowflake: {e}")
        return
    
    # Sidebar - Data source and semantic model selection
    with st.sidebar:
        st.markdown("### 🧠 Model Selection")
        
        # ===== Model Backend Selection (SPCS or External API) =====
        backend_list = list(MODEL_BACKENDS.keys())
        selected_backend = st.radio(
            "Select Model Backend",
            options=backend_list,
            index=backend_list.index(st.session_state.model_backend) if st.session_state.model_backend in backend_list else 1,
            key="backend_selector",
            horizontal=True,
            help="SPCS: Local deployment, data stays in cloud | External API: Call cloud LLM"
        )
        
        # If backend changed
        if selected_backend != st.session_state.model_backend:
            st.session_state.model_backend = selected_backend
            if selected_backend == "SPCS (Local)":
                st.session_state.selected_model = list(SPCS_MODELS.keys())[0]
            else:
                st.session_state.selected_model = MODEL_PROVIDERS[st.session_state.selected_provider]["default"]
        
        # Display backend info
        backend_info = MODEL_BACKENDS[selected_backend]
        st.caption(f"{backend_info['icon']} {backend_info['description']}")
        
        # ===== Show different model selection based on backend =====
        if selected_backend == "SPCS (Local)":
            # SPCS model selection
            spcs_model_list = list(SPCS_MODELS.keys())
            current_spcs_index = 0
            if st.session_state.selected_model in spcs_model_list:
                current_spcs_index = spcs_model_list.index(st.session_state.selected_model)
            
            selected_model = st.selectbox(
                "Select SPCS Model",
                options=spcs_model_list,
                index=current_spcs_index,
                format_func=lambda x: SPCS_MODELS[x],
                key="spcs_model_selector"
            )
            
            if selected_model != st.session_state.selected_model:
                st.session_state.selected_model = selected_model
            
            st.success(f"🏠 **SPCS** / `{selected_model.split('/')[-1]}`")
            
            st.info("💡 SPCS model runs in Snowflake Container Services, data never leaves Snowflake.")
        
        else:
            # External API - model provider selection
            provider_list = list(MODEL_PROVIDERS.keys())
            selected_provider = st.selectbox(
                "Select Model Provider",
                options=provider_list,
                index=provider_list.index(st.session_state.selected_provider) if st.session_state.selected_provider in provider_list else 0,
                key="provider_selector"
            )
            
            if selected_provider != st.session_state.selected_provider:
                st.session_state.selected_provider = selected_provider
                st.session_state.selected_model = MODEL_PROVIDERS[selected_provider]["default"]
            
            provider_models = MODEL_PROVIDERS[selected_provider]["models"]
            model_list = list(provider_models.keys())
            
            current_model_index = 0
            if st.session_state.selected_model in model_list:
                current_model_index = model_list.index(st.session_state.selected_model)
            
            selected_model = st.selectbox(
                "Select Model",
                options=model_list,
                index=current_model_index,
                format_func=lambda x: provider_models[x],
                key="model_selector"
            )
            
            if selected_model != st.session_state.selected_model:
                st.session_state.selected_model = selected_model
            
            st.caption(f"🌐 **{selected_provider}** / `{selected_model}`")
        
        st.markdown("---")
        st.markdown("### 🗄️ Data Source")
        
        # Database selection
        try:
            databases = fetch_databases(conn)
        except Exception:
            databases = []
        
        selected_db = st.selectbox(
            "Select Database",
            options=databases,
            index=0 if databases else None,
            key="db_selector"
        )
        
        if selected_db != st.session_state.selected_database:
            st.session_state.selected_database = selected_db
            st.session_state.selected_schema = None
            st.session_state.available_tables = []
            st.session_state.semantic_model = None
        
        # Schema selection
        if selected_db:
            try:
                schemas = fetch_schemas(conn, selected_db)
                selected_schema = st.selectbox(
                    "Select Schema",
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
                st.warning("Cannot get schema list")
        
        # ===== Semantic Model Configuration =====
        st.markdown("---")
        st.markdown("### 📚 Semantic Model")
        
        if st.session_state.semantic_model:
            st.success(f"✅ Loaded: {st.session_state.semantic_model_name}")
            if st.button("🗑️ Unload Semantic Model"):
                st.session_state.semantic_model = None
                st.session_state.semantic_model_name = None
                st.experimental_rerun()
        else:
            st.info("💡 Loading a semantic model improves SQL generation accuracy")
        
        # Load semantic model from Stage
        if st.session_state.selected_schema:
            try:
                stages = fetch_stages(conn, st.session_state.selected_schema)
                if stages:
                    selected_stage = st.selectbox(
                        "Select Stage",
                        options=stages,
                        format_func=lambda x: x.split(".")[-1],
                        key="stage_selector"
                    )
                    
                    if selected_stage:
                        yaml_files = list_yaml_files_in_stage(conn, selected_stage)
                        if yaml_files:
                            selected_yaml = st.selectbox(
                                "Select Semantic Model File",
                                options=yaml_files,
                                format_func=lambda x: x.split("/")[-1],
                                key="yaml_selector"
                            )
                            
                            if st.button("📥 Load Semantic Model", type="primary"):
                                with st.spinner("Loading..."):
                                    yaml_content = load_semantic_model_from_stage(conn, f"@{selected_stage}/{selected_yaml.split('/')[-1]}")
                                    if yaml_content:
                                        st.session_state.semantic_model = yaml_content
                                        st.session_state.semantic_model_name = selected_yaml.split("/")[-1]
                                        st.success("✅ Semantic model loaded!")
                                        st.experimental_rerun()
                        else:
                            st.caption("No YAML files in this Stage")
            except Exception as e:
                st.caption(f"Cannot list Stage: {e}")
        
        # Manual semantic model input
        with st.expander("📝 Manual Input"):
            manual_yaml = st.text_area(
                "Paste Semantic Model YAML",
                height=200,
                placeholder="Paste your semantic model YAML content..."
            )
            if st.button("Apply Semantic Model"):
                if manual_yaml.strip():
                    st.session_state.semantic_model = manual_yaml
                    st.session_state.semantic_model_name = "Manual Input"
                    st.success("✅ Semantic model applied!")
                    st.experimental_rerun()
        
        # Display available tables
        st.markdown("---")
        if st.session_state.available_tables:
            st.markdown("### 📋 Available Tables")
            for table in st.session_state.available_tables[:10]:
                table_name = table.split(".")[-1]
                st.markdown(f"- `{table_name}`")
            if len(st.session_state.available_tables) > 10:
                st.caption(f"... and {len(st.session_state.available_tables) - 10} more tables")
        
        st.markdown("---")
        
        # Clear conversation button
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.agent_messages = []
            st.session_state.last_query_result = None
            st.experimental_rerun()
    
    # Main content area - Tabs
    tab1, tab2, tab3 = st.tabs(["🤖 Agent Chat", "📈 Data Insights", "🔧 Toolbox"])
    
    # ===== Tab 1: Agent Chat =====
    with tab1:
        # Semantic model status
        if st.session_state.semantic_model:
            st.markdown(f"""
            <div class="feature-card">
                <span class="semantic-badge">🎯 Semantic Model Enabled</span>
                <h3 style="margin-top: 1rem;">💬 Chat with AI Assistant</h3>
                <p>Semantic model <strong>{st.session_state.semantic_model_name}</strong> loaded. AI will use business definitions to understand your questions.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="feature-card">
                <h3>💬 Chat with AI Assistant</h3>
                <p>⚠️ <strong>Note</strong>: No semantic model loaded. SQL generation is based on table structure only. Load a semantic model in the sidebar for better results.</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Conversation history
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.agent_messages:
                render_message(
                    msg["role"], 
                    msg["content"],
                    msg.get("tool_info")
                )
                if msg.get("data") is not None:
                    render_data_preview(msg["data"], "Query Results")
        
        # Input box
        def submit_question():
            if st.session_state.user_question_input:
                st.session_state.submitted_question = st.session_state.user_question_input
                st.session_state.user_question_input = ""
        
        col_input, col_btn = st.columns([5, 1])
        with col_input:
            st.text_input(
                "Enter your question",
                key="user_question_input",
                placeholder="Ask Snowflake Intelligence...",
                label_visibility="collapsed",
                on_change=submit_question
            )
        with col_btn:
            if st.button("Send", type="primary", use_container_width=True):
                submit_question()
        
        # Process submitted question
        user_input = st.session_state.pop("submitted_question", None)
        
        if user_input:
            st.session_state.agent_messages.append({
                "role": "user",
                "content": user_input
            })
            
            context = {
                "database": st.session_state.selected_database,
                "schema": st.session_state.selected_schema,
                "tables": st.session_state.available_tables,
                "messages": st.session_state.agent_messages,
                "last_query_result": st.session_state.last_query_result,
                "semantic_model": st.session_state.semantic_model
            }
            
            with st.spinner("🤔 Thinking (with semantic model)..." if st.session_state.semantic_model else "🤔 Thinking..."):
                response = run_agent(conn, user_input, context)
            
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
                
                with st.spinner(f"🔧 Executing {tool_name}..."):
                    result = execute_tool_call(conn, tool_name, parameters, context)
                
                if result.get("success"):
                    if "data" in result:
                        agent_message["data"] = result["data"]
                        st.session_state.last_query_result = result["data"]
                        agent_message["content"] = f"{thought}\n\n✅ Query successful, returned {result['row_count']} rows."
                    elif "columns" in result:
                        cols_info = "\n".join([f"- {c['name']}: {c['type']}" for c in result['columns']])
                        agent_message["content"] = f"{thought}\n\n📋 Table `{result['table_name']}` structure ({result['row_count']} rows):\n{cols_info}"
                    else:
                        agent_message["content"] = f"{thought}\n\n✅ Execution successful."
                else:
                    agent_message["content"] = f"{thought}\n\n❌ Execution failed: {result.get('error', 'Unknown error')}"
            
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
                <span class="semantic-badge">🎯 Semantic Model Enabled</span>
                <h3 style="margin-top: 1rem;">📊 Intelligent Data Insights</h3>
                <p>Using semantic model <strong>{st.session_state.semantic_model_name}</strong> to understand your business questions.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="feature-card">
                <h3>📊 Intelligent Data Insights</h3>
                <p>Describe what you want to query in natural language. ⚠️ Load a semantic model first for more accurate results.</p>
            </div>
            """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 🔍 Natural Language Query")
            nl_query = st.text_area(
                "Describe what you want to query",
                placeholder="e.g., Show me daily order count and total amount for the past month\n\nWith semantic model, you can use business terms like: VIP customers, revenue, return rate, etc.",
                height=100
            )
            
            if st.button("🚀 Generate and Execute Query", type="primary"):
                if nl_query and st.session_state.available_tables:
                    schema_info = {}
                    for table in st.session_state.available_tables[:5]:
                        try:
                            result = get_table_info(conn, table)
                            if result["success"]:
                                schema_info[table] = result["columns"]
                        except Exception:
                            pass
                    
                    with st.spinner("🧠 Generating SQL (with semantic model)..." if st.session_state.semantic_model else "🧠 Generating SQL..."):
                        sql = generate_sql_from_question(
                            conn, nl_query, schema_info, 
                            st.session_state.available_tables,
                            st.session_state.semantic_model
                        )
                    
                    st.markdown("**Generated SQL:**")
                    st.code(sql, language="sql")
                    
                    with st.spinner("⚡ Executing query..."):
                        result = execute_sql(conn, sql)
                    
                    if result["success"]:
                        st.session_state.last_query_result = result["data"]
                        render_data_preview(result["data"])
                        
                        with st.spinner("💡 Generating insights..."):
                            insights = generate_data_insights(
                                conn, result["data"], nl_query,
                                st.session_state.semantic_model
                            )
                        
                        st.markdown("### 💡 AI Insights")
                        st.markdown(insights)
                    else:
                        st.error(f"Query failed: {result['error']}")
                else:
                    st.warning("Please select a data source and enter query content")
        
        with col2:
            st.markdown("### 💡 Suggested Questions")
            if st.session_state.available_tables and st.button("Generate Suggestions"):
                schema_info = {}
                for table in st.session_state.available_tables[:3]:
                    try:
                        result = get_table_info(conn, table)
                        if result["success"]:
                            schema_info[table] = result["columns"]
                    except Exception:
                        pass
                
                with st.spinner("Generating suggested questions..."):
                    questions = suggest_questions(
                        conn, st.session_state.available_tables, schema_info,
                        st.session_state.semantic_model
                    )
                
                for q in questions:
                    st.info(f"📌 {q}")
    
    # ===== Tab 3: Toolbox =====
    with tab3:
        st.markdown("""
        <div class="feature-card">
            <h3>🔧 Data Toolbox</h3>
            <p>Direct access to SQL query and table information tools.</p>
        </div>
        """, unsafe_allow_html=True)
        
        tool_tabs = st.tabs(["SQL Query", "Table Info", "Statistics", "Semantic Model"])
        
        # SQL Query tool
        with tool_tabs[0]:
            st.markdown("### 📝 SQL Query")
            sql_input = st.text_area(
                "Enter SQL Query",
                height=150,
                placeholder="SELECT * FROM your_table LIMIT 10"
            )
            
            if st.button("▶️ Execute Query", key="run_sql"):
                if sql_input:
                    with st.spinner("Executing..."):
                        result = execute_sql(conn, sql_input)
                    
                    if result["success"]:
                        st.success(f"Query successful, returned {result['row_count']} rows")
                        st.session_state.last_query_result = result["data"]
                        render_data_preview(result["data"])
                    else:
                        st.error(f"Query failed: {result['error']}")
        
        # Table Info tool
        with tool_tabs[1]:
            st.markdown("### 📋 Table Structure")
            if st.session_state.available_tables:
                selected_table = st.selectbox(
                    "Select Table",
                    st.session_state.available_tables,
                    format_func=lambda x: x.split(".")[-1]
                )
                
                if st.button("🔍 View Structure", key="view_schema"):
                    with st.spinner("Getting table info..."):
                        result = get_table_info(conn, selected_table)
                    
                    if result["success"]:
                        st.markdown(f"**Table:** `{result['table_name']}`")
                        st.markdown(f"**Rows:** {result['row_count']:,}")
                        
                        cols_df = pd.DataFrame(result["columns"])
                        st.dataframe(cols_df, use_container_width=True)
                    else:
                        st.error(result["error"])
            else:
                st.info("Please select a database and schema in the sidebar first")
        
        # Statistics tool
        with tool_tabs[2]:
            st.markdown("### 📊 Data Statistics")
            if st.session_state.last_query_result is not None:
                df = st.session_state.last_query_result
                
                st.markdown(f"**Dimensions:** {len(df)} rows × {len(df.columns)} columns")
                
                st.markdown("**Descriptive Statistics:**")
                st.dataframe(df.describe(), use_container_width=True)
                
                st.markdown("**Data Types:**")
                dtype_df = pd.DataFrame({
                    "Column": df.columns,
                    "Data Type": df.dtypes.astype(str).values,
                    "Non-Null Count": df.count().values,
                    "Null Count": df.isnull().sum().values
                })
                st.dataframe(dtype_df, use_container_width=True)
            else:
                st.info("Execute a query first to see data statistics")
        
        # Semantic Model Preview
        with tool_tabs[3]:
            st.markdown("### 📚 Semantic Model Preview")
            if st.session_state.semantic_model:
                st.markdown(f"**Currently Loaded:** `{st.session_state.semantic_model_name}`")
                st.code(st.session_state.semantic_model, language="yaml")
            else:
                st.info("No semantic model loaded. Load one in the sidebar.")


if __name__ == "__main__":
    main()

