-- ============================================
-- 创建镜像仓库和上传 Docker 镜像
-- ============================================

USE ROLE ACCOUNTADMIN;
USE DATABASE SPCS_CHINA;
USE SCHEMA MODEL_SERVICE;

-- ============================================
-- 1. 创建镜像仓库
-- ============================================
CREATE IMAGE REPOSITORY IF NOT EXISTS MODEL_SERVICE_REPO
    COMMENT = 'Image repository for SPCS model service';

-- 查看仓库信息
SHOW IMAGE REPOSITORIES;

-- 获取仓库 URL (用于 docker push)
-- 格式: <org>-<account>.registry.snowflakecomputing.cn/spcs_china/model_service/model_service_repo
SELECT SYSTEM$REGISTRY_URL('MODEL_SERVICE_REPO');

-- ============================================
-- 2. 创建 Stage 用于存储服务规范
-- ============================================
CREATE STAGE IF NOT EXISTS MODEL_SERVICE_STAGE
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Stage for SPCS service specifications';

-- ============================================
-- 3. 上传服务规范文件
-- ============================================
-- 使用 SnowSQL 或 Snowflake UI 上传 spec.yaml 文件:
-- PUT file:///path/to/spec.yaml @MODEL_SERVICE_STAGE/;

-- 查看上传的文件
LIST @MODEL_SERVICE_STAGE;

-- ============================================
-- 上传 Docker 镜像的步骤 (在本地执行):
-- ============================================
-- 
-- 1. 登录到 Snowflake 镜像仓库:
--    docker login <org>-<account>.registry.snowflakecomputing.cn -u <username>
--
-- 2. 构建 Docker 镜像:
--    cd spcs_china/model_service
--    docker build -t model-service:latest .
--
-- 3. 标记镜像:
--    docker tag model-service:latest \
--      <org>-<account>.registry.snowflakecomputing.cn/spcs_china/model_service/model_service_repo/model-service:latest
--
-- 4. 推送镜像:
--    docker push \
--      <org>-<account>.registry.snowflakecomputing.cn/spcs_china/model_service/model_service_repo/model-service:latest
--
-- 5. 查看已上传的镜像:
SHOW IMAGES IN IMAGE REPOSITORY MODEL_SERVICE_REPO;


