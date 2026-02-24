-- ============================================
-- 创建调用 SPCS 模型服务的 UDF
-- ============================================

USE DATABASE SPCS_CHINA;
USE SCHEMA MODEL_SERVICE;

-- ============================================
-- 1. 基础 LLM 调用 UDF
-- ============================================
CREATE OR REPLACE FUNCTION QWEN_COMPLETE(prompt VARCHAR)
RETURNS VARCHAR
SERVICE = QWEN_MODEL_SERVICE
ENDPOINT = 'qwen-api'
MAX_BATCH_ROWS = 1
AS '/v1/chat/completions';

-- ============================================
-- 2. 授权
-- ============================================
GRANT USAGE ON FUNCTION QWEN_COMPLETE(VARCHAR) TO ROLE SNOW_DEV_RL;

-- ============================================
-- 3. 测试 UDF (服务就绪后执行)
-- ============================================
-- SELECT SPCS_CHINA.MODEL_SERVICE.QWEN_COMPLETE('{"model":"Qwen/Qwen2.5-1.5B-Instruct","messages":[{"role":"user","content":"Hello, who are you?"}]}');
