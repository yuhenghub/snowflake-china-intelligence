#!/bin/bash
# 检查 SPCS 服务状态的脚本

--  "=== 检查计算池状态 ==="
DESCRIBE COMPUTE POOL QWEN_GPU_POOL;

 ""
--  "=== 检查服务状态 ==="
SELECT SYSTEM\$GET_SERVICE_STATUS('SPCS_CHINA.MODEL_SERVICE.QWEN_MODEL_SERVICE');

 ""
--  "=== 检查服务日志 (最近 30 行) ==="
SELECT SYSTEM\$GET_SERVICE_LOGS('SPCS_CHINA.MODEL_SERVICE.QWEN_MODEL_SERVICE', 0, 'qwen-vllm', 30);

 ""
--  "=== 测试 UDF (如果服务就绪) ==="
SELECT SPCS_CHINA.MODEL_SERVICE.QWEN_COMPLETE('{\\\"model\\\":\\\"Qwen/Qwen2.5-1.5B-Instruct\\\",\\\"messages\\\":[{\\\"role\\\":\\\"user\\\",\\\"content\\\":\\\"Hello!\\\"}]}');

