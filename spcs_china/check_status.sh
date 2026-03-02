#!/bin/bash
# ============================================
# SPCS 服务状态检查脚本
# ============================================

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 默认连接名称
CONNECTION="${SNOWFLAKE_CONNECTION:-china_dev}"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}   SPCS 服务状态检查${NC}"
echo -e "${BLUE}   使用连接: ${CONNECTION}${NC}"
echo -e "${BLUE}============================================${NC}"

echo -e "\n${YELLOW}=== 检查计算池状态 ===${NC}"
snow sql -c "$CONNECTION" -q "DESCRIBE COMPUTE POOL GPU_NV_S_POOL;" 2>/dev/null || \
snow sql -c "$CONNECTION" -q "SHOW COMPUTE POOLS LIKE 'GPU%';"

echo -e "\n${YELLOW}=== 检查服务状态 ===${NC}"
snow sql -c "$CONNECTION" -q "SELECT SYSTEM\$GET_SERVICE_STATUS('SPCS_CHINA.MODEL_SERVICE.QWEN_MODEL_SERVICE');"

echo -e "\n${YELLOW}=== 检查服务日志 (最近 30 行) ===${NC}"
snow sql -c "$CONNECTION" -q "SELECT SYSTEM\$GET_SERVICE_LOGS('SPCS_CHINA.MODEL_SERVICE.QWEN_MODEL_SERVICE', 0, 'qwen-service', 30);"

echo -e "\n${YELLOW}=== 测试 UDF (如果服务就绪) ===${NC}"
snow sql -c "$CONNECTION" -q "SELECT SPCS_CHINA.MODEL_SERVICE.QWEN_COMPLETE('{\"model\":\"Qwen/Qwen2.5-1.5B-Instruct\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello!\"}]}');"

echo -e "\n${GREEN}============================================${NC}"
echo -e "${GREEN}   检查完成${NC}"
echo -e "${GREEN}============================================${NC}"
