-- ============================================================================
-- Cortex Agent & Snowflake China Intelligence 部署脚本
-- ============================================================================

SET (streamlit_warehouse)=(SELECT CURRENT_WAREHOUSE());

USE DATABASE SNOWFLAKE_PROD_USER1;
USE SCHEMA CORTEX_ANALYST;

-- ============================================================================
-- Step 1: 创建 Stage (如果不存在)
-- ============================================================================
CREATE STAGE IF NOT EXISTS APPS_STAGE
DIRECTORY = (ENABLE = true)
COMMENT = 'Stage for Cortex Agent and Intelligence Apps';

-- ============================================================================
-- Step 2: 上传 Cortex Agent 文件
-- 从项目根目录运行
-- ============================================================================
-- PUT file://agent/cortex_agent.py @SNOWFLAKE_PROD_USER1.CORTEX_ANALYST.APPS_STAGE/agent/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;
-- PUT file://agent/environment.yml @SNOWFLAKE_PROD_USER1.CORTEX_ANALYST.APPS_STAGE/agent/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;

-- ============================================================================
-- Step 3: 创建 Cortex Agent Streamlit 应用
-- ============================================================================
CREATE OR REPLACE STREAMLIT SNOWFLAKE_PROD_USER1.CORTEX_ANALYST.CORTEX_AGENT
ROOT_LOCATION = '@SNOWFLAKE_PROD_USER1.CORTEX_ANALYST.APPS_STAGE/agent'
MAIN_FILE = 'cortex_agent.py'
TITLE = '🤖 Cortex Agent'
QUERY_WAREHOUSE = $streamlit_warehouse
EXTERNAL_ACCESS_INTEGRATIONS = (SNOWFLAKE_PROD_USER1_CORTEX_ANALYST_QWEN_INTEGRATION)
COMMENT = 'Cortex Agent - 数据源与语义模型配置中心';

-- ============================================================================
-- Step 4: 上传 Snowflake China Intelligence 文件
-- 从项目根目录运行
-- ============================================================================
-- PUT file://intelligence/snowflake_intelligence.py @SNOWFLAKE_PROD_USER1.CORTEX_ANALYST.APPS_STAGE/intelligence/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;
-- PUT file://intelligence/environment.yml @SNOWFLAKE_PROD_USER1.CORTEX_ANALYST.APPS_STAGE/intelligence/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;

-- ============================================================================
-- Step 5: 创建 Snowflake China Intelligence Streamlit 应用
-- ============================================================================
CREATE OR REPLACE STREAMLIT SNOWFLAKE_PROD_USER1.CORTEX_ANALYST.SNOWFLAKE_INTELLIGENCE
ROOT_LOCATION = '@SNOWFLAKE_PROD_USER1.CORTEX_ANALYST.APPS_STAGE/intelligence'
MAIN_FILE = 'snowflake_intelligence.py'
TITLE = '❄️ Snowflake China Intelligence'
QUERY_WAREHOUSE = $streamlit_warehouse
EXTERNAL_ACCESS_INTEGRATIONS = (SNOWFLAKE_PROD_USER1_CORTEX_ANALYST_QWEN_INTEGRATION)
COMMENT = 'Snowflake China Intelligence - 智能数据分析对话平台';

-- ============================================================================
-- 验证部署
-- ============================================================================
SHOW STREAMLITS IN SCHEMA SNOWFLAKE_PROD_USER1.CORTEX_ANALYST;

SELECT '✅ 部署完成!' AS STATUS;
