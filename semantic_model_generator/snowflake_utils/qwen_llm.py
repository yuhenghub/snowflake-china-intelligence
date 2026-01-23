"""
Qwen (通义千问) LLM API Integration for Snowflake China Region
This module provides LLM capabilities using Alibaba Cloud's Qwen API
as a replacement for Snowflake Cortex LLM functions in China region.
"""

import os
import json
import requests
from typing import Optional
from loguru import logger

# Qwen API Configuration
QWEN_API_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_DEFAULT_MODEL = "qwen-turbo"  # 可选: qwen-turbo, qwen-plus, qwen-max

# Get API key from environment variable
QWEN_API_KEY = os.environ.get("QWEN_API_KEY", "")


def set_qwen_api_key(api_key: str) -> None:
    """Set the Qwen API key programmatically."""
    global QWEN_API_KEY
    QWEN_API_KEY = api_key
    os.environ["QWEN_API_KEY"] = api_key


def qwen_complete(
    prompt: str,
    model: str = QWEN_DEFAULT_MODEL,
    max_tokens: int = 1024,
    temperature: float = 0.7,
) -> Optional[str]:
    """
    Call Qwen API to generate text completion.
    
    Args:
        prompt: The input prompt for the model
        model: The Qwen model to use (qwen-turbo, qwen-plus, qwen-max)
        max_tokens: Maximum tokens in the response
        temperature: Sampling temperature (0-1)
    
    Returns:
        The generated text response, or None if the call fails
    """
    if not QWEN_API_KEY:
        logger.warning("QWEN_API_KEY not set. Please set the environment variable or call set_qwen_api_key()")
        return None
    
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    
    try:
        response = requests.post(
            f"{QWEN_API_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            logger.warning(f"Unexpected Qwen API response format: {result}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Qwen API request failed: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Qwen API response: {e}")
        return None


def qwen_complete_for_snowflake(
    prompt: str,
    model: str = QWEN_DEFAULT_MODEL,
) -> str:
    """
    Wrapper function that mimics the behavior of Snowflake Cortex COMPLETE function.
    Returns empty string on failure instead of None.
    
    Args:
        prompt: The input prompt
        model: The Qwen model to use
    
    Returns:
        The generated text, or empty string on failure
    """
    result = qwen_complete(prompt, model)
    return result if result else ""


# SQL UDF for Snowflake that calls external Qwen API
QWEN_UDF_SQL = """
-- Create network rule for Qwen API access
CREATE OR REPLACE NETWORK RULE qwen_api_rule
    MODE = EGRESS
    TYPE = HOST_PORT
    VALUE_LIST = ('dashscope.aliyuncs.com:443');

-- Create secret for Qwen API key
CREATE OR REPLACE SECRET qwen_api_secret
    TYPE = GENERIC_STRING
    SECRET_STRING = '{api_key}';

-- Create external access integration
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION qwen_api_integration
    ALLOWED_NETWORK_RULES = (qwen_api_rule)
    ALLOWED_AUTHENTICATION_SECRETS = (qwen_api_secret)
    ENABLED = TRUE;

-- Create Python UDF that calls Qwen API
CREATE OR REPLACE FUNCTION QWEN_COMPLETE(model VARCHAR, prompt VARCHAR)
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.10'
PACKAGES = ('requests')
HANDLER = 'qwen_complete'
EXTERNAL_ACCESS_INTEGRATIONS = (qwen_api_integration)
SECRETS = ('api_key' = qwen_api_secret)
AS $$
import requests
import json
import _snowflake

def qwen_complete(model: str, prompt: str) -> str:
    api_key = _snowflake.get_generic_secret_string('api_key')
    
    headers = {{
        "Authorization": f"Bearer {{api_key}}",
        "Content-Type": "application/json",
    }}
    
    payload = {{
        "model": model,
        "messages": [{{"role": "user", "content": prompt}}],
        "max_tokens": 1024,
        "temperature": 0.7,
    }}
    
    try:
        response = requests.post(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        return ""
    except Exception as e:
        return f"Error: {{str(e)}}"
$$;
"""


def get_qwen_udf_sql(api_key: str, database: str = "CORTEX_ANALYST_SEMANTICS", schema: str = "SEMANTIC_MODEL_GENERATOR") -> str:
    """
    Generate SQL statements to create Qwen UDF in Snowflake.
    
    Args:
        api_key: The Qwen API key
        database: Target database name
        schema: Target schema name
    
    Returns:
        SQL statements as a string
    """
    sql = f"""
USE DATABASE {database};
USE SCHEMA {schema};

-- Create network rule for Qwen API access
CREATE OR REPLACE NETWORK RULE qwen_api_rule
    MODE = EGRESS
    TYPE = HOST_PORT
    VALUE_LIST = ('dashscope.aliyuncs.com:443');

-- Create secret for Qwen API key
CREATE OR REPLACE SECRET qwen_api_secret
    TYPE = GENERIC_STRING
    SECRET_STRING = '{api_key}';

-- Create external access integration
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION qwen_api_integration
    ALLOWED_NETWORK_RULES = (qwen_api_rule)
    ALLOWED_AUTHENTICATION_SECRETS = (qwen_api_secret)
    ENABLED = TRUE;

-- Create Python UDF that calls Qwen API
CREATE OR REPLACE FUNCTION QWEN_COMPLETE(model VARCHAR, prompt VARCHAR)
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.10'
PACKAGES = ('requests')
HANDLER = 'qwen_complete'
EXTERNAL_ACCESS_INTEGRATIONS = (qwen_api_integration)
SECRETS = ('api_key' = qwen_api_secret)
AS $$
import requests
import json
import _snowflake

def qwen_complete(model: str, prompt: str) -> str:
    api_key = _snowflake.get_generic_secret_string('api_key')
    
    headers = {{
        "Authorization": f"Bearer {{api_key}}",
        "Content-Type": "application/json",
    }}
    
    payload = {{
        "model": model,
        "messages": [{{"role": "user", "content": prompt}}],
        "max_tokens": 1024,
        "temperature": 0.7,
    }}
    
    try:
        response = requests.post(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        return ""
    except Exception as e:
        return f"Error: {{str(e)}}"
$$;
"""
    return sql

