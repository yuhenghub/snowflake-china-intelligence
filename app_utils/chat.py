import json
import os
import re
import uuid
from typing import Any, Dict

import requests
import streamlit as st
from snowflake.connector import SnowflakeConnection

def _get_snowpark_session():
    """Get Snowpark Session for SiS compatibility"""
    try:
        from snowflake.snowpark.context import get_active_session
        return get_active_session()
    except Exception:
        return None

API_ENDPOINT = "https://{HOST}/api/v2/cortex/analyst/message"

# Default Qwen model for SQL generation
QWEN_SQL_MODEL = os.environ.get("QWEN_SQL_MODEL", "qwen-max")


def _get_selected_model() -> str:
    """获取当前选择的模型"""
    return st.session_state.get("selected_model", QWEN_SQL_MODEL)


def _is_china_region_chat(conn: SnowflakeConnection) -> bool:
    """
    Check if running in China region. Uses cached result for performance.
    """
    # Check cache first
    if "is_china_region" in st.session_state:
        return st.session_state["is_china_region"]
    
    # Check environment variable
    if os.environ.get("USE_QWEN_FOR_CHINA", "").lower() == "true":
        st.session_state["is_china_region"] = True
        return True
    
    # Check connection host for China region indicators
    try:
        host = conn.host or ""
        if any(x in host.lower() for x in [".cn", "cn-", "china", "amazonaws.com.cn"]):
            st.session_state["is_china_region"] = True
            return True
    except Exception:
        pass
    
    # Check region from Snowflake
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_REGION()")
        region = cursor.fetchone()[0] or ""
        if "cn-" in region.lower() or "china" in region.lower():
            st.session_state["is_china_region"] = True
            return True
    except Exception:
        pass
    
    # Default: not China region
    st.session_state["is_china_region"] = False
    return False

# Prompt template for Qwen to generate SQL
QWEN_SQL_PROMPT_TEMPLATE = """你是一个专业的 SQL 专家。根据以下语义模型和用户问题，生成正确的 Snowflake SQL 查询。

## 语义模型 (YAML 格式):
```yaml
{semantic_model}
```

## 用户问题:
{question}

## 要求:
1. 只返回 SQL 查询，不要包含任何解释
2. 使用语义模型中定义的表和列
3. 确保 SQL 语法正确，适用于 Snowflake
4. 如果问题无法用给定的语义模型回答，返回 "CANNOT_ANSWER: [原因]"

## SQL 查询:
"""

QWEN_EXPLANATION_PROMPT_TEMPLATE = """根据以下 SQL 查询，用中文简要解释这个查询做了什么：

SQL: {sql}

请用一句话解释："""


# ============================================
# 模型后端配置
# ============================================
MODEL_BACKENDS_CHAT = {
    "SPCS (本地)": {
        "udf_path": "SPCS_CHINA.MODEL_SERVICE.QWEN_COMPLETE"
    },
    "外部 API": {
        "udf_path": "SNOWFLAKE_PROD_USER1.CORTEX_ANALYST.QWEN_COMPLETE"
    }
}

DEFAULT_BACKEND_CHAT = "外部 API"


def _get_model_backend() -> str:
    """获取当前选择的模型后端"""
    return st.session_state.get("model_backend", DEFAULT_BACKEND_CHAT)


def _get_qwen_udf_path() -> str:
    """获取 Qwen UDF 的完整路径，根据后端选择返回对应路径"""
    # 首先检查是否有自定义 UDF 路径
    custom_path = st.session_state.get("qwen_udf_path", "")
    if custom_path and custom_path != "SNOWFLAKE_PROD_USER1.CORTEX_ANALYST.QWEN_COMPLETE":
        return custom_path
    
    # 根据后端返回对应的 UDF 路径
    backend = _get_model_backend()
    if backend in MODEL_BACKENDS_CHAT:
        return MODEL_BACKENDS_CHAT[backend]["udf_path"]
    
    return "SNOWFLAKE_PROD_USER1.CORTEX_ANALYST.QWEN_COMPLETE"


def _call_spcs_model(conn: SnowflakeConnection, model: str, prompt: str) -> str:
    """Call locally deployed model via SPCS service."""
    
    # 直接使用简单的 prompt 调用 /complete 端点
    escaped_prompt = prompt.replace("'", "''")
    
    udf_path = MODEL_BACKENDS_CHAT["SPCS (本地)"]["udf_path"]
    query = f"SELECT {udf_path}('{escaped_prompt}')"
    
    try:
        # 使用 Snowpark session 以获得更好的 SiS 兼容性
        session = _get_snowpark_session()
        
        if session:
            # 确保有活动的 warehouse（Service Function 调用需要）
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
        else:
            # Fallback to cursor
            cursor = conn.cursor()
            cursor.execute("USE WAREHOUSE COMPUTE_WH")
            cursor.execute(query)
            result = cursor.fetchone()
            if result and result[0]:
                return result[0]
            return ""
    except Exception as e:
        raise ValueError(f"SPCS call error: {str(e)}")


def _call_external_api(conn: SnowflakeConnection, model: str, prompt: str) -> str:
    """Call LLM via external API UDF."""
    escaped_prompt = prompt.replace("'", "''").replace("\\", "\\\\")
    udf_path = MODEL_BACKENDS_CHAT["外部 API"]["udf_path"]
    query = f"SELECT {udf_path}('{model}', $${escaped_prompt}$$)"
    
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        if result and result[0]:
            return result[0]
        return ""
    except Exception as e:
        raise ValueError(f"外部 API 调用失败: {str(e)}")


def _call_qwen_udf(conn: SnowflakeConnection, model: str, prompt: str) -> str:
    """
    Call Qwen UDF in Snowflake to generate response.
    Routes to different backends based on user selection.
    """
    backend = _get_model_backend()
    
    if backend == "SPCS (本地)":
        return _call_spcs_model(conn, model, prompt)
    else:
        return _call_external_api(conn, model, prompt)


def _generate_sql_with_qwen(
    conn: SnowflakeConnection, 
    semantic_model: str, 
    question: str
) -> Dict[str, Any]:
    """
    Use Qwen to generate SQL based on semantic model and user question.
    Returns a response in the same format as Cortex Analyst API.
    """
    # Generate SQL using Qwen
    sql_prompt = QWEN_SQL_PROMPT_TEMPLATE.format(
        semantic_model=semantic_model,
        question=question
    )
    
    # 使用用户选择的模型
    selected_model = _get_selected_model()
    sql_response = _call_qwen_udf(conn, selected_model, sql_prompt)
    sql_response = sql_response.strip()
    
    # Check if Qwen couldn't answer
    if sql_response.startswith("CANNOT_ANSWER:"):
        reason = sql_response.replace("CANNOT_ANSWER:", "").strip()
        return {
            "request_id": str(uuid.uuid4()),
            "message": {
                "role": "analyst",
                "content": [
                    {
                        "type": "text",
                        "text": f"抱歉，我无法根据当前语义模型回答这个问题。原因：{reason}"
                    }
                ]
            }
        }
    
    # Clean up SQL (remove markdown code blocks if present)
    if sql_response.startswith("```"):
        lines = sql_response.split("\n")
        sql_lines = []
        in_code_block = False
        for line in lines:
            if line.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block or not line.startswith("```"):
                sql_lines.append(line)
        sql_response = "\n".join(sql_lines).strip()
    
    # Generate explanation
    explanation_prompt = QWEN_EXPLANATION_PROMPT_TEMPLATE.format(sql=sql_response)
    explanation = _call_qwen_udf(conn, "qwen-turbo", explanation_prompt)
    
    # Format response like Cortex Analyst API
    return {
        "request_id": str(uuid.uuid4()),
        "message": {
            "role": "analyst",
            "content": [
                {
                    "type": "text",
                    "text": f"__{question}__\n\n{explanation}"
                },
                {
                    "type": "sql",
                    "statement": sql_response
                }
            ]
        }
    }


@st.cache_data(ttl=60, show_spinner=False)
def send_message(
    _conn: SnowflakeConnection, semantic_model: str, messages: list[dict[str, str]]
) -> Dict[str, Any]:
    """
    Calls the REST API with a list of messages and returns the response.
    For China region, uses Qwen-based SQL generation instead of Cortex Analyst.
    
    Args:
        _conn: SnowflakeConnection, used to grab the token for auth.
        messages: list of chat messages to pass to the Analyst API.
        semantic_model: stringified YAML of the semantic model.

    Returns: The raw ChatMessage response from Analyst (or Qwen equivalent).
    """
    
    # For China region, use Qwen-based SQL generation
    if _is_china_region_chat(_conn):
        # Extract the latest user message
        latest_message = messages[-1] if messages else None
        if latest_message and latest_message.get("role") == "user":
            content = latest_message.get("content", [])
            if isinstance(content, list) and len(content) > 0:
                question = content[0].get("text", "")
            elif isinstance(content, str):
                question = content
            else:
                question = str(content)
            
            return _generate_sql_with_qwen(_conn, semantic_model, question)
        else:
            raise ValueError("没有找到用户消息")
    
    # Original Cortex Analyst API call for non-China regions
    request_body = {
        "messages": messages,
        "semantic_model": semantic_model,
    }

    if st.session_state.get("sis", False):
        import _snowflake

        resp = _snowflake.send_snow_api_request(  # type: ignore
            "POST",
            "/api/v2/cortex/analyst/message",
            {},
            {},
            request_body,
            {},
            30000,
        )
        if resp["status"] < 400:
            json_resp: Dict[str, Any] = json.loads(resp["content"])
            return json_resp
        else:
            err_body = json.loads(resp["content"])
            if "message" in err_body:
                error_msg = re.sub(
                    r"\s*Please use https://github\.com/Snowflake-Labs/semantic-model-generator.*",
                    "",
                    err_body["message"],
                )
                raise ValueError(error_msg)
            raise ValueError(err_body)

    else:
        host = st.session_state.host_name
        resp = requests.post(
            API_ENDPOINT.format(
                HOST=host,
            ),
            json=request_body,
            headers={
                "Authorization": f'Snowflake Token="{_conn.rest.token}"',  # type: ignore[union-attr]
                "Content-Type": "application/json",
            },
        )
        if resp.status_code < 400:
            json_resp: Dict[str, Any] = resp.json()
            return json_resp
        else:
            err_body = json.loads(resp.text)
            if "message" in err_body:
                error_msg = re.sub(
                    r"\s*Please use https://github\.com/Snowflake-Labs/semantic-model-generator.*",
                    "",
                    err_body["message"],
                )
                raise ValueError(error_msg)
            raise ValueError(err_body)
