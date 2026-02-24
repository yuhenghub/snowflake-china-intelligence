-- ============================================
-- Cortex Agent & Intelligence Setup for Snowflake China
-- 用于在 Snowflake China 区域部署 Cortex Agent 和 Intelligence 模拟功能
-- ============================================

-- 1. 创建数据库和 Schema (如果不存在)
CREATE DATABASE IF NOT EXISTS CORTEX_AGENT_DEMO;
USE DATABASE CORTEX_AGENT_DEMO;

CREATE SCHEMA IF NOT EXISTS AGENT_SCHEMA;
USE SCHEMA AGENT_SCHEMA;

-- 2. 创建网络规则以访问 Qwen API
CREATE OR REPLACE NETWORK RULE qwen_api_network_rule
    MODE = EGRESS
    TYPE = HOST_PORT
    VALUE_LIST = ('dashscope.aliyuncs.com:443');

-- 3. 创建存储 Qwen API Key 的密钥
-- 请将 'your-qwen-api-key' 替换为您的实际 API Key
CREATE OR REPLACE SECRET qwen_api_key_secret
    TYPE = GENERIC_STRING
    SECRET_STRING = 'your-qwen-api-key';  -- ⚠️ 请替换为您的 Qwen API Key

-- 4. 创建外部访问集成
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION qwen_api_integration
    ALLOWED_NETWORK_RULES = (qwen_api_network_rule)
    ALLOWED_AUTHENTICATION_SECRETS = (qwen_api_key_secret)
    ENABLED = TRUE;

-- 5. 创建 Qwen API 调用 UDF
CREATE OR REPLACE FUNCTION QWEN_COMPLETE(model VARCHAR, prompt VARCHAR)
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.10'
PACKAGES = ('requests')
HANDLER = 'qwen_complete'
EXTERNAL_ACCESS_INTEGRATIONS = (qwen_api_integration)
SECRETS = ('api_key' = qwen_api_key_secret)
AS $$
import requests
import json
import _snowflake

def qwen_complete(model: str, prompt: str) -> str:
    """调用 Qwen API 生成文本"""
    api_key = _snowflake.get_generic_secret_string('api_key')
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2048,
        "temperature": 0.7,
    }
    
    try:
        response = requests.post(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
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
        return f"Error: {str(e)}"
$$;

-- 6. 创建 Agent 系统提示 UDF
CREATE OR REPLACE FUNCTION AGENT_COMPLETE(user_input VARCHAR, context_json VARCHAR)
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.10'
PACKAGES = ('requests')
HANDLER = 'agent_complete'
EXTERNAL_ACCESS_INTEGRATIONS = (qwen_api_integration)
SECRETS = ('api_key' = qwen_api_key_secret)
AS $$
import requests
import json
import _snowflake

AGENT_SYSTEM_PROMPT = """你是一个专业的数据分析助手，运行在 Snowflake 环境中。你可以使用以下工具来帮助用户：

## 可用工具:
1. execute_sql - 执行 SQL 查询
2. get_table_info - 获取表信息
3. analyze_data - 分析数据
4. create_visualization - 创建可视化

## 响应格式:
当需要调用工具时：
{
  "thought": "思考过程",
  "tool_call": {"name": "工具名", "parameters": {"参数名": "值"}}
}

当直接回答时：
{
  "thought": "思考过程",
  "response": "回答内容"
}

请用中文回答。"""

def agent_complete(user_input: str, context_json: str) -> str:
    api_key = _snowflake.get_generic_secret_string('api_key')
    
    context = json.loads(context_json) if context_json else {}
    
    full_prompt = f"{AGENT_SYSTEM_PROMPT}\n\n上下文:\n{json.dumps(context, ensure_ascii=False)}\n\n用户: {user_input}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": "qwen-max",
        "messages": [{"role": "user", "content": full_prompt}],
        "max_tokens": 2048,
        "temperature": 0.7,
    }
    
    try:
        response = requests.post(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
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
        return json.dumps({"error": str(e)})
$$;

-- 7. 创建 SQL 生成 UDF
CREATE OR REPLACE FUNCTION GENERATE_SQL_FROM_NL(question VARCHAR, schema_info VARCHAR, tables_json VARCHAR)
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.10'
PACKAGES = ('requests')
HANDLER = 'generate_sql'
EXTERNAL_ACCESS_INTEGRATIONS = (qwen_api_integration)
SECRETS = ('api_key' = qwen_api_key_secret)
AS $$
import requests
import json
import _snowflake

def generate_sql(question: str, schema_info: str, tables_json: str) -> str:
    api_key = _snowflake.get_generic_secret_string('api_key')
    
    tables = json.loads(tables_json) if tables_json else []
    
    prompt = f"""请根据以下问题生成 Snowflake SQL 查询:

问题: {question}

可用表: {', '.join(tables)}

表结构信息:
{schema_info}

要求:
1. 生成有效的 Snowflake SQL
2. 只返回 SQL 语句，不要任何解释
3. 使用完全限定的表名
4. 添加 LIMIT 限制结果数量

SQL:
"""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": "qwen-max",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1024,
        "temperature": 0.3,
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
            sql = result["choices"][0]["message"]["content"]
            # 清理 SQL
            if sql.startswith("```"):
                lines = sql.split("\n")
                sql_lines = []
                in_code = False
                for line in lines:
                    if line.startswith("```"):
                        in_code = not in_code
                        continue
                    sql_lines.append(line)
                sql = "\n".join(sql_lines)
            return sql.strip()
        return ""
    except Exception as e:
        return f"-- Error: {str(e)}"
$$;

-- 8. 创建数据洞察生成 UDF
CREATE OR REPLACE FUNCTION GENERATE_DATA_INSIGHTS(data_summary VARCHAR, context VARCHAR)
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.10'
PACKAGES = ('requests')
HANDLER = 'generate_insights'
EXTERNAL_ACCESS_INTEGRATIONS = (qwen_api_integration)
SECRETS = ('api_key' = qwen_api_key_secret)
AS $$
import requests
import json
import _snowflake

def generate_insights(data_summary: str, context: str) -> str:
    api_key = _snowflake.get_generic_secret_string('api_key')
    
    prompt = f"""请分析以下数据并提供专业的商业洞察:

{data_summary}

{f"额外背景: {context}" if context else ""}

请提供:
1. 数据的关键发现 (3-5点)
2. 潜在的业务价值
3. 建议的后续分析方向
4. 需要注意的数据质量问题（如有）

请用专业但易懂的中文回答。
"""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": "qwen-max",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2048,
        "temperature": 0.7,
    }
    
    try:
        response = requests.post(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
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
        return f"Error generating insights: {str(e)}"
$$;

-- 9. 测试 UDF
-- SELECT QWEN_COMPLETE('qwen-turbo', '你好，请用一句话介绍自己');

-- 10. 创建示例数据表（可选）
/*
CREATE OR REPLACE TABLE SAMPLE_ORDERS (
    ORDER_ID NUMBER,
    CUSTOMER_ID NUMBER,
    ORDER_DATE DATE,
    PRODUCT_NAME VARCHAR,
    QUANTITY NUMBER,
    UNIT_PRICE NUMBER(10,2),
    TOTAL_AMOUNT NUMBER(10,2),
    STATUS VARCHAR
);

INSERT INTO SAMPLE_ORDERS VALUES
(1, 101, '2024-01-15', '笔记本电脑', 2, 5999.00, 11998.00, '已完成'),
(2, 102, '2024-01-16', '无线鼠标', 5, 99.00, 495.00, '已完成'),
(3, 103, '2024-01-17', '机械键盘', 3, 299.00, 897.00, '配送中'),
(4, 101, '2024-01-18', '显示器', 1, 2499.00, 2499.00, '已完成'),
(5, 104, '2024-01-19', '耳机', 2, 199.00, 398.00, '待发货');
*/

-- 完成提示
SELECT '✅ Cortex Agent & Intelligence 设置完成!' AS STATUS;
