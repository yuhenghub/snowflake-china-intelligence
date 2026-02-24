-- ============================================================================
-- Cortex Agent & Intelligence - Streamlit in Snowflake (SiS) 部署脚本
-- 适用于 Snowflake 中国区域，使用通义千问 (Qwen) API
-- ============================================================================

-- 设置当前 Warehouse
SET (streamlit_warehouse)=(SELECT CURRENT_WAREHOUSE());

-- ============================================================================
-- Step 1: 创建数据库和 Schema (如果不存在)
-- ============================================================================
CREATE DATABASE IF NOT EXISTS CORTEX_ANALYST_SEMANTICS
COMMENT = '{"origin": "sf_sit",
            "name": "cortex_agent",
            "version": {"major": 1, "minor": 0},
            "attributes": {"deployment": "sis_china"}}';

CREATE SCHEMA IF NOT EXISTS CORTEX_ANALYST_SEMANTICS.CORTEX_AGENT
COMMENT = '{"origin": "sf_sit",
            "name": "cortex_agent",
            "version": {"major": 1, "minor": 0},
            "attributes": {"deployment": "sis_china"}}';

USE DATABASE CORTEX_ANALYST_SEMANTICS;
USE SCHEMA CORTEX_AGENT;

-- ============================================================================
-- Step 2: 创建 Qwen API 外部访问集成
-- ⚠️ 请将 <YOUR_QWEN_API_KEY> 替换为您的通义千问 API Key
-- ============================================================================

-- 创建网络规则允许访问通义千问 API
CREATE OR REPLACE NETWORK RULE qwen_agent_network_rule
    MODE = EGRESS
    TYPE = HOST_PORT
    VALUE_LIST = ('dashscope.aliyuncs.com:443');

-- 创建 Secret 存储 API Key
-- ⚠️ 请替换为您的实际 API Key
CREATE OR REPLACE SECRET qwen_agent_api_secret
    TYPE = GENERIC_STRING
    SECRET_STRING = '<YOUR_QWEN_API_KEY>';

-- 创建外部访问集成
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION qwen_agent_integration
    ALLOWED_NETWORK_RULES = (qwen_agent_network_rule)
    ALLOWED_AUTHENTICATION_SECRETS = (qwen_agent_api_secret)
    ENABLED = TRUE;

-- ============================================================================
-- Step 3: 创建 Qwen Complete UDF
-- ============================================================================
CREATE OR REPLACE FUNCTION CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.QWEN_COMPLETE(model VARCHAR, prompt VARCHAR)
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.10'
PACKAGES = ('requests')
HANDLER = 'qwen_complete'
EXTERNAL_ACCESS_INTEGRATIONS = (qwen_agent_integration)
SECRETS = ('api_key' = qwen_agent_api_secret)
AS $$
import requests
import json
import _snowflake

def qwen_complete(model: str, prompt: str) -> str:
    """
    调用通义千问 API 生成文本
    支持的模型: qwen-turbo, qwen-plus, qwen-max
    """
    api_key = _snowflake.get_generic_secret_string('api_key')
    
    # 模型映射
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
            timeout=120,
        )
        response.raise_for_status()
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        return ""
    except Exception as e:
        return f"Error calling Qwen API: {str(e)}"
$$;

-- 测试 Qwen UDF
-- SELECT CORTEX_ANALYST_SEMANTICS.SEMANTIC_MODEL_GENERATOR.QWEN_COMPLETE('qwen-turbo', '你好，请用一句话介绍你自己。');

-- ============================================================================
-- Step 4: 创建 Stage 用于存储应用文件
-- ============================================================================
CREATE OR REPLACE STAGE CORTEX_ANALYST_SEMANTICS.CORTEX_AGENT.AGENT_STAGE
DIRECTORY = (ENABLE = true)
COMMENT = '{"origin": "sf_sit",
            "name": "cortex_agent",
            "version": {"major": 1, "minor": 0},
            "attributes": {"deployment": "sis_china"}}';

-- ============================================================================
-- Step 5: 上传应用文件
-- ⚠️ 从项目根目录 (semantic-model-generator/) 运行以下命令
-- ============================================================================

-- 上传主应用文件
PUT file://cortex_agent_sis.py @CORTEX_ANALYST_SEMANTICS.CORTEX_AGENT.AGENT_STAGE/cortex_agent/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;

-- 上传 environment.yml (使用现有的)
PUT file://environment.yml @CORTEX_ANALYST_SEMANTICS.CORTEX_AGENT.AGENT_STAGE/cortex_agent/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;

-- ============================================================================
-- Step 6: 创建 Streamlit 应用
-- ============================================================================
CREATE OR REPLACE STREAMLIT CORTEX_ANALYST_SEMANTICS.CORTEX_AGENT.CORTEX_AGENT_APP
ROOT_LOCATION = '@CORTEX_ANALYST_SEMANTICS.CORTEX_AGENT.AGENT_STAGE/cortex_agent'
MAIN_FILE = 'cortex_agent_sis.py'
TITLE = "🤖 Cortex Agent & Intelligence (中国区)"
QUERY_WAREHOUSE = $streamlit_warehouse
EXTERNAL_ACCESS_INTEGRATIONS = (qwen_agent_integration)
COMMENT = '{"origin": "sf_sit",
            "name": "cortex_agent",
            "version": {"major": 1, "minor": 0},
            "attributes": {"deployment": "sis_china"}}';

-- ============================================================================
-- Step 7: 创建示例数据表（可选，用于演示）
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS CORTEX_ANALYST_SEMANTICS.DEMO_DATA;

-- 创建订单表
CREATE OR REPLACE TABLE CORTEX_ANALYST_SEMANTICS.DEMO_DATA.ORDERS (
    ORDER_ID NUMBER AUTOINCREMENT,
    CUSTOMER_ID NUMBER,
    ORDER_DATE DATE,
    PRODUCT_NAME VARCHAR(200),
    CATEGORY VARCHAR(100),
    QUANTITY NUMBER,
    UNIT_PRICE NUMBER(10,2),
    TOTAL_AMOUNT NUMBER(10,2),
    STATUS VARCHAR(50),
    REGION VARCHAR(50)
);

-- 插入示例数据
INSERT INTO CORTEX_ANALYST_SEMANTICS.DEMO_DATA.ORDERS 
(CUSTOMER_ID, ORDER_DATE, PRODUCT_NAME, CATEGORY, QUANTITY, UNIT_PRICE, TOTAL_AMOUNT, STATUS, REGION)
VALUES
(101, '2024-01-15', '笔记本电脑', '电子产品', 2, 5999.00, 11998.00, '已完成', '华东'),
(102, '2024-01-16', '无线鼠标', '电子配件', 5, 99.00, 495.00, '已完成', '华北'),
(103, '2024-01-17', '机械键盘', '电子配件', 3, 299.00, 897.00, '配送中', '华南'),
(101, '2024-01-18', '显示器', '电子产品', 1, 2499.00, 2499.00, '已完成', '华东'),
(104, '2024-01-19', '耳机', '电子配件', 2, 199.00, 398.00, '待发货', '西南'),
(105, '2024-01-20', '平板电脑', '电子产品', 1, 3299.00, 3299.00, '已完成', '华中'),
(106, '2024-01-21', 'USB Hub', '电子配件', 4, 79.00, 316.00, '已完成', '华北'),
(107, '2024-01-22', '智能手表', '穿戴设备', 2, 1599.00, 3198.00, '配送中', '华东'),
(108, '2024-01-23', '蓝牙音箱', '音频设备', 3, 299.00, 897.00, '已完成', '华南'),
(109, '2024-01-24', '移动电源', '电子配件', 5, 129.00, 645.00, '待发货', '西北'),
(110, '2024-02-01', '游戏主机', '游戏设备', 1, 3999.00, 3999.00, '已完成', '华东'),
(111, '2024-02-02', '手柄', '游戏配件', 2, 399.00, 798.00, '已完成', '华北'),
(112, '2024-02-03', 'VR眼镜', '穿戴设备', 1, 2999.00, 2999.00, '配送中', '华南'),
(113, '2024-02-04', '路由器', '网络设备', 2, 599.00, 1198.00, '已完成', '华中'),
(114, '2024-02-05', '摄像头', '安防设备', 3, 399.00, 1197.00, '已完成', '西南');

-- 创建客户表
CREATE OR REPLACE TABLE CORTEX_ANALYST_SEMANTICS.DEMO_DATA.CUSTOMERS (
    CUSTOMER_ID NUMBER,
    CUSTOMER_NAME VARCHAR(100),
    EMAIL VARCHAR(200),
    PHONE VARCHAR(20),
    CITY VARCHAR(50),
    REGION VARCHAR(50),
    REGISTRATION_DATE DATE,
    CUSTOMER_LEVEL VARCHAR(20)
);

INSERT INTO CORTEX_ANALYST_SEMANTICS.DEMO_DATA.CUSTOMERS VALUES
(101, '张三', 'zhangsan@email.com', '13800138001', '上海', '华东', '2023-06-15', '黄金'),
(102, '李四', 'lisi@email.com', '13800138002', '北京', '华北', '2023-07-20', '白银'),
(103, '王五', 'wangwu@email.com', '13800138003', '广州', '华南', '2023-08-10', '黄金'),
(104, '赵六', 'zhaoliu@email.com', '13800138004', '成都', '西南', '2023-09-05', '普通'),
(105, '钱七', 'qianqi@email.com', '13800138005', '武汉', '华中', '2023-10-12', '白银'),
(106, '孙八', 'sunba@email.com', '13800138006', '天津', '华北', '2023-11-08', '普通'),
(107, '周九', 'zhoujiu@email.com', '13800138007', '杭州', '华东', '2023-12-01', '黄金'),
(108, '吴十', 'wushi@email.com', '13800138008', '深圳', '华南', '2024-01-05', '白银'),
(109, '郑一', 'zhengyi@email.com', '13800138009', '西安', '西北', '2024-01-10', '普通'),
(110, '王二', 'wanger@email.com', '13800138010', '南京', '华东', '2024-01-15', '黄金');

-- 创建产品表
CREATE OR REPLACE TABLE CORTEX_ANALYST_SEMANTICS.DEMO_DATA.PRODUCTS (
    PRODUCT_ID NUMBER AUTOINCREMENT,
    PRODUCT_NAME VARCHAR(200),
    CATEGORY VARCHAR(100),
    BRAND VARCHAR(100),
    UNIT_PRICE NUMBER(10,2),
    STOCK_QUANTITY NUMBER,
    SUPPLIER VARCHAR(100)
);

INSERT INTO CORTEX_ANALYST_SEMANTICS.DEMO_DATA.PRODUCTS
(PRODUCT_NAME, CATEGORY, BRAND, UNIT_PRICE, STOCK_QUANTITY, SUPPLIER)
VALUES
('笔记本电脑', '电子产品', '联想', 5999.00, 100, '联想科技'),
('无线鼠标', '电子配件', '罗技', 99.00, 500, '罗技中国'),
('机械键盘', '电子配件', '雷蛇', 299.00, 200, '雷蛇科技'),
('显示器', '电子产品', '戴尔', 2499.00, 80, '戴尔中国'),
('耳机', '电子配件', '索尼', 199.00, 300, '索尼中国'),
('平板电脑', '电子产品', '苹果', 3299.00, 50, '苹果中国'),
('智能手表', '穿戴设备', '华为', 1599.00, 150, '华为科技'),
('蓝牙音箱', '音频设备', 'JBL', 299.00, 200, 'JBL中国'),
('移动电源', '电子配件', '小米', 129.00, 400, '小米科技'),
('游戏主机', '游戏设备', '索尼', 3999.00, 30, '索尼中国');

-- ============================================================================
-- 部署完成！
-- ============================================================================

SELECT '✅ Cortex Agent & Intelligence 部署完成!' AS STATUS,
       '请在 Snowsight 中打开应用: CORTEX_ANALYST_SEMANTICS.CORTEX_AGENT.CORTEX_AGENT_APP' AS MESSAGE;

-- ============================================================================
-- 使用说明:
-- 1. 确保已将 <YOUR_QWEN_API_KEY> 替换为您的实际 API Key
-- 2. 从项目根目录运行 PUT 命令上传文件
-- 3. 在 Snowsight 中打开应用
-- 4. 选择 CORTEX_ANALYST_SEMANTICS.DEMO_DATA 作为数据源进行测试
-- ============================================================================
