#!/bin/bash
# ============================================================================
# Semantic Model Generator - China Region Deployment Script
# 中国区部署脚本
# ============================================================================

set -e

echo "=========================================="
echo "Semantic Model Generator - 中国区部署"
echo "=========================================="

# 配置变量
SNOW_CONNECTION="china"
QWEN_API_KEY="${QWEN_API_KEY:-sk-974d67fdc0744f1fb0723686c810f327}"

# 检查 Snow CLI
if ! command -v snow &> /dev/null; then
    echo "❌ 错误: Snowflake CLI 未安装"
    echo "请参考: https://docs.snowflake.com/en/developer-guide/snowflake-cli-v2/installation/installation"
    exit 1
fi

# 检查连接配置
echo ""
echo "📡 验证 Snowflake 中国区连接..."
snow connection test --connection $SNOW_CONNECTION || {
    echo "❌ 连接测试失败，请检查 ~/.snowflake/connections.toml 中的 [$SNOW_CONNECTION] 配置"
    exit 1
}

echo "✅ 连接验证成功"

# 切换到项目目录
cd "$(dirname "$0")"

echo ""
echo "📦 Step 1: 创建数据库、Schema 和 Qwen UDF..."
echo "-------------------------------------------"

# 首先创建基础对象和 Qwen UDF
cat > /tmp/china_qwen_setup.sql << 'EOSQL'
-- 创建数据库和 Schema
CREATE DATABASE IF NOT EXISTS CORTEX_ANALYST_SEMANTICS;
CREATE SCHEMA IF NOT EXISTS CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR;
USE DATABASE CORTEX_ANALYST_SEMANTICS;
USE SCHEMA SEMANTIC_MODEL_GENERATOR;

-- 创建网络规则允许访问通义千问 API
CREATE OR REPLACE NETWORK RULE qwen_api_network_rule
    MODE = EGRESS
    TYPE = HOST_PORT
    VALUE_LIST = ('dashscope.aliyuncs.com:443');
EOSQL

snow sql -f /tmp/china_qwen_setup.sql --connection $SNOW_CONNECTION

# 创建 Secret (带 API Key)
echo ""
echo "🔐 Step 2: 创建 Qwen API Secret..."
snow sql -q "CREATE OR REPLACE SECRET CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.qwen_api_secret TYPE = GENERIC_STRING SECRET_STRING = '$QWEN_API_KEY';" --connection $SNOW_CONNECTION

# 创建外部访问集成
echo ""
echo "🌐 Step 3: 创建 External Access Integration..."
cat > /tmp/china_integration.sql << 'EOSQL'
USE DATABASE CORTEX_ANALYST_SEMANTICS;
USE SCHEMA SEMANTIC_MODEL_GENERATOR;

CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION qwen_api_integration
    ALLOWED_NETWORK_RULES = (qwen_api_network_rule)
    ALLOWED_AUTHENTICATION_SECRETS = (qwen_api_secret)
    ENABLED = TRUE;
EOSQL

snow sql -f /tmp/china_integration.sql --connection $SNOW_CONNECTION

# 创建 Qwen UDF
echo ""
echo "🤖 Step 4: 创建 Qwen Complete UDF..."
cat > /tmp/china_qwen_udf.sql << 'EOSQL'
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
EOSQL

snow sql -f /tmp/china_qwen_udf.sql --connection $SNOW_CONNECTION

# 测试 Qwen UDF
echo ""
echo "🧪 Step 5: 测试 Qwen UDF..."
snow sql -q "SELECT CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.QWEN_COMPLETE('qwen-turbo', '你好，请用一句话介绍你自己。');" --connection $SNOW_CONNECTION

# 部署 Streamlit 应用
echo ""
echo "📤 Step 6: 部署 Streamlit 应用文件..."
snow sql -f sis_setup/app_setup.sql --connection $SNOW_CONNECTION

echo ""
echo "=========================================="
echo "✅ 部署完成!"
echo "=========================================="
echo ""
echo "🚀 打开应用:"
echo "   snow streamlit get-url SEMANTIC_MODEL_GENERATOR --open \\"
echo "       --database cortex_analyst_semantics \\"
echo "       --schema semantic_model_generator \\"
echo "       --connection $SNOW_CONNECTION"
echo ""
echo "📝 或者在 Snowsight 中打开:"
echo "   1. 登录 Snowsight"
echo "   2. 导航到 Data > Databases > CORTEX_ANALYST_SEMANTICS"
echo "   3. 找到 SEMANTIC_MODEL_GENERATOR schema"
echo "   4. 点击 Streamlit Apps > SEMANTIC_MODEL_GENERATOR"
echo ""
echo "⚠️  注意: 如果需要本地运行应用，请设置以下环境变量:"
echo "   export USE_QWEN_FOR_CHINA=true"
echo "   export QWEN_API_KEY=$QWEN_API_KEY"
echo ""

