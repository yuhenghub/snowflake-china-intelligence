-- ============================================================================
-- Cortex Agent V2 - UDF 部署脚本
-- 适用于 Snowflake 中国区域，使用通义千问 (Qwen) API
-- ============================================================================

-- ============================================================================
-- ⚠️ 配置变量 - 请根据实际情况修改
-- ============================================================================
-- 替换为你的数据库和 Schema
SET DATABASE_NAME = 'SNOWFLAKE_PROD_USER1';
SET SCHEMA_NAME = 'CORTEX_ANALYST';
-- ⚠️ 替换为你的通义千问 API Key
SET QWEN_API_KEY = '<YOUR_QWEN_API_KEY>';

-- ============================================================================
-- Step 1: 创建数据库和 Schema (如果不存在)
-- ============================================================================
CREATE DATABASE IF NOT EXISTS IDENTIFIER($DATABASE_NAME);
CREATE SCHEMA IF NOT EXISTS IDENTIFIER($DATABASE_NAME || '.' || $SCHEMA_NAME);

USE DATABASE IDENTIFIER($DATABASE_NAME);
USE SCHEMA IDENTIFIER($SCHEMA_NAME);

-- ============================================================================
-- Step 2: 创建网络规则 (允许访问通义千问 API)
-- ============================================================================
CREATE OR REPLACE NETWORK RULE qwen_api_network_rule
    MODE = EGRESS
    TYPE = HOST_PORT
    VALUE_LIST = (
        'dashscope.aliyuncs.com:443',      -- 通义千问 DashScope API
        'api.deepseek.com:443',             -- DeepSeek API (可选)
        'api.moonshot.cn:443'               -- Kimi/Moonshot API (可选)
    );

-- ============================================================================
-- Step 3: 创建 Secret (存储 API Key)
-- ============================================================================
CREATE OR REPLACE SECRET qwen_api_secret
    TYPE = GENERIC_STRING
    SECRET_STRING = $QWEN_API_KEY;

-- ============================================================================
-- Step 4: 创建外部访问集成
-- ============================================================================
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION qwen_api_integration
    ALLOWED_NETWORK_RULES = (qwen_api_network_rule)
    ALLOWED_AUTHENTICATION_SECRETS = (qwen_api_secret)
    ENABLED = TRUE;

-- ============================================================================
-- Step 5: 创建 QWEN_COMPLETE UDF (双参数版本)
-- ============================================================================
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
    """
    调用通义千问 API 生成文本
    
    支持的模型:
    - DashScope: qwen-turbo, qwen-plus, qwen-max, qwen-max-longcontext
    - DeepSeek: deepseek-chat, deepseek-reasoner
    - Moonshot: moonshot-v1-8k, moonshot-v1-32k, moonshot-v1-128k
    """
    api_key = _snowflake.get_generic_secret_string('api_key')
    
    # 模型映射 (兼容 Cortex LLM 模型名称)
    model_mapping = {
        'llama3-8b': 'qwen-turbo',
        'mistral-large2': 'qwen-max',
        'mixtral-8x7b': 'qwen-plus',
        'claude-3-sonnet': 'qwen-max',
        'gemini-1.5-pro': 'qwen-max',
    }
    qwen_model = model_mapping.get(model.lower(), model)
    
    # 根据模型选择 API 端点
    if qwen_model.startswith('deepseek'):
        api_url = "https://api.deepseek.com/v1/chat/completions"
    elif qwen_model.startswith('moonshot'):
        api_url = "https://api.moonshot.cn/v1/chat/completions"
    else:
        # 默认使用 DashScope (通义千问)
        api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": qwen_model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4096,
        "temperature": 0.7,
    }
    
    try:
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        return ""
    except Exception as e:
        return f"Error calling LLM API: {str(e)}"
$$;

-- ============================================================================
-- Step 6: 测试 UDF
-- ============================================================================
-- 取消注释以下语句进行测试:
-- SELECT QWEN_COMPLETE('qwen-turbo', '你好，请用一句话介绍你自己。');
-- SELECT QWEN_COMPLETE('qwen-max', 'What is 2+2? Answer with just the number.');

-- ============================================================================
-- 部署完成！
-- ============================================================================
SELECT '✅ QWEN_COMPLETE UDF 部署完成!' AS STATUS,
       CONCAT($DATABASE_NAME, '.', $SCHEMA_NAME, '.QWEN_COMPLETE') AS UDF_PATH;



