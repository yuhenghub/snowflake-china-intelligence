-- ============================================
-- 创建 SPCS 服务 - 本地 Qwen 模型
-- ============================================

USE DATABASE SPCS_CHINA;
USE SCHEMA MODEL_SERVICE;

-- ============================================
-- 1. 创建服务 (使用内联规范)
-- ============================================
CREATE SERVICE IF NOT EXISTS QWEN_MODEL_SERVICE
    IN COMPUTE POOL GPU_NV_S_POOL
    MIN_INSTANCES = 1
    MAX_INSTANCES = 1
    EXTERNAL_ACCESS_INTEGRATIONS = (modelscope_access_integration)
    FROM SPECIFICATION $$
spec:
  containers:
    - name: qwen-service
      image: /spcs_china/model_service/model_service_repo/qwen-service:latest
      env:
        MODEL_NAME: "Qwen/Qwen2.5-1.5B-Instruct"
        HF_ENDPOINT: "https://hf-mirror.com"
        MODELSCOPE_CACHE: "/app/models"
        MAX_NEW_TOKENS: "2048"
        WORKERS: "1"
      resources:
        requests:
          memory: 8Gi
          cpu: 2
          nvidia.com/gpu: 1
        limits:
          memory: 14Gi
          cpu: 4
          nvidia.com/gpu: 1
      readinessProbe:
        port: 8001
        path: /health
  endpoints:
    - name: qwen-api
      port: 8001
      public: false
$$;

-- ============================================
-- 2. 查看服务状态
-- ============================================
SHOW SERVICES;
DESCRIBE SERVICE QWEN_MODEL_SERVICE;

-- 查看服务实例状态
SELECT SYSTEM$GET_SERVICE_STATUS('QWEN_MODEL_SERVICE');

-- 查看服务日志 (模型下载和加载进度)
-- SELECT SYSTEM$GET_SERVICE_LOGS('QWEN_MODEL_SERVICE', 0, 'qwen-service', 100);

-- ============================================
-- 3. 获取服务端点 URL
-- ============================================
SHOW ENDPOINTS IN SERVICE QWEN_MODEL_SERVICE;

-- ============================================
-- 4. 服务管理命令
-- ============================================
-- 暂停服务 (节省成本)
-- ALTER SERVICE QWEN_MODEL_SERVICE SUSPEND;

-- 恢复服务
-- ALTER SERVICE QWEN_MODEL_SERVICE RESUME;

-- 重启服务 (重新下载模型)
-- ALTER SERVICE QWEN_MODEL_SERVICE RESTART;

-- 删除服务
-- DROP SERVICE QWEN_MODEL_SERVICE;
