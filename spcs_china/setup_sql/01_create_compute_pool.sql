-- ============================================
-- SPCS 计算池创建脚本
-- Snowflake China Region
-- 使用 gpu_nv_s 实例类型
-- ============================================

-- 使用 ACCOUNTADMIN 角色创建计算池
USE ROLE ACCOUNTADMIN;

-- 创建 GPU 计算池 (gpu_nv_s - NVIDIA T4 GPU)
-- gpu_nv_s: 适合中小型模型推理，性价比高
CREATE COMPUTE POOL IF NOT EXISTS GPU_NV_S_POOL
    MIN_NODES = 1
    MAX_NODES = 2
    INSTANCE_FAMILY = GPU_NV_S
    AUTO_RESUME = TRUE
    AUTO_SUSPEND_SECS = 600
    COMMENT = 'GPU compute pool for LLM inference service (China Region)';

-- 查看计算池状态
SHOW COMPUTE POOLS;
DESC COMPUTE POOL GPU_NV_S_POOL;

-- 如果需要更大的 GPU，可以使用 gpu_nv_m 或 gpu_nv_l
-- CREATE COMPUTE POOL GPU_NV_M_POOL
--     MIN_NODES = 1
--     MAX_NODES = 2
--     INSTANCE_FAMILY = GPU_NV_M
--     AUTO_RESUME = TRUE
--     AUTO_SUSPEND_SECS = 600;


