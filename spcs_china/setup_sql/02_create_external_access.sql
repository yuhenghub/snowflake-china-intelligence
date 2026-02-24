-- 创建网络规则和外部访问集成
-- 支持 ModelScope 和 HF-Mirror 下载模型

USE DATABASE SPCS_CHINA;
USE SCHEMA MODEL_SERVICE;

-- 网络规则：允许访问模型下载源
CREATE OR REPLACE NETWORK RULE modelscope_network_rule
    MODE = EGRESS
    TYPE = HOST_PORT
    VALUE_LIST = (
        -- ModelScope (备用)
        'www.modelscope.cn:443',
        'modelscope.cn:443',
        'cdn-lfs-cn-1.modelscope.cn:443',
        'cdn-lfs-cn-2.modelscope.cn:443',
        'cdn.modelscope.cn:443',
        -- HF-Mirror (推荐，速度更快)
        'hf-mirror.com:443',
        'cdn-lfs.hf-mirror.com:443',
        -- HuggingFace CDN (如果 HF-Mirror 重定向)
        'cdn-lfs.huggingface.co:443',
        'huggingface.co:443'
    )
    COMMENT = 'Network rule for model download from ModelScope and HF-Mirror';

-- 外部访问集成
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION modelscope_access_integration
    ALLOWED_NETWORK_RULES = (modelscope_network_rule)
    ENABLED = TRUE
    COMMENT = 'External access integration for model download';
