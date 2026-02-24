USE DATABASE CORTEX_ANALYST_SEMANTICS;
USE SCHEMA SEMANTIC_MODEL_GENERATOR;

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
    
    model_mapping = {
        'llama3-8b': 'qwen-turbo',
        'mistral-large2': 'qwen-max',
        'mixtral-8x7b': 'qwen-plus',
    }
    qwen_model = model_mapping.get(model.lower(), model)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": qwen_model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2048,
        "temperature": 0.7,
    }
    
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
        return f"Error: {str(e)}"
$$;

