#!/bin/bash
# ============================================
# LLM 模型一键部署脚本
# 支持多种开源模型部署到 Snowflake SPCS
# 使用 china_dev 连接
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 配置变量
CONNECTION="${SNOWFLAKE_CONNECTION:-china_dev}"
DATABASE="SPCS_CHINA"
SCHEMA="MODEL_SERVICE"
COMPUTE_POOL="GPU_NV_S_POOL"
SERVICE_NAME="LLM_MODEL_SERVICE"
IMAGE_NAME="model-service"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# 从环境变量获取值（如果已设置）
MODEL_NAME="${MODEL_NAME:-}"
HF_ENDPOINT="${HF_ENDPOINT:-}"
SERVICE_SUFFIX=""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Note: Using simple case statements instead of associative arrays for bash 3.x compatibility on macOS

# ============================================
# 显示模型选择菜单
# ============================================
show_model_menu() {
    echo -e "\n${BLUE}============================================${NC}"
    echo -e "${BLUE}          选择要部署的模型${NC}"
    echo -e "${BLUE}============================================${NC}"
    
    echo -e "\n${CYAN}【DeepSeek 系列】${NC}"
    echo -e "  1) DeepSeek R1 蒸馏版 (1.5B)  ${GREEN}[推荐入门]${NC} ~3GB"
    echo -e "  2) DeepSeek R1 蒸馏版 (7B)     ${YELLOW}[需要大GPU]${NC} ~14GB"
    echo -e "  3) DeepSeek Coder (1.3B)       ${GREEN}[代码生成]${NC} ~2.5GB"
    echo -e "  4) DeepSeek LLM Chat (7B)      ~14GB"
    
    echo -e "\n${CYAN}【Qwen 系列 - 阿里通义千问】${NC}"
    echo -e "  5) Qwen 2.5 (1.5B)             ${GREEN}[推荐]${NC} ~3GB"
    echo -e "  6) Qwen 2.5 (3B)               ${GREEN}[平衡选择]${NC} ~6GB"
    echo -e "  7) Qwen 2.5 (7B)               ~14GB"
    echo -e "  8) Qwen 2.5 Coder (1.5B)       ${GREEN}[代码生成]${NC} ~3GB"
    echo -e "  9) Qwen 2.5 Coder (7B)         ~14GB"
    
    echo -e "\n${CYAN}【ChatGLM 系列 - 清华智谱】${NC}"
    echo -e "  10) ChatGLM3 (6B)              ~12GB"
    echo -e "  11) GLM-4 (9B)                 ${YELLOW}[需要大GPU]${NC} ~18GB"
    
    echo -e "\n${CYAN}【Llama 系列 - Meta】${NC}"
    echo -e "  12) Llama 3.2 (1B)             ${GREEN}[最小]${NC} ~2GB"
    echo -e "  13) Llama 3.2 (3B)             ~6GB"
    
    echo -e "\n${CYAN}【Yi 系列 - 零一万物】${NC}"
    echo -e "  14) Yi 1.5 (6B)                ~12GB"
    echo -e "  15) Yi 1.5 (9B)                ${YELLOW}[需要大GPU]${NC} ~18GB"
    
    echo -e "\n${CYAN}【InternLM 系列 - 上海AI实验室】${NC}"
    echo -e "  16) InternLM 2.5 (1.8B)        ~3.5GB"
    echo -e "  17) InternLM 2.5 (7B)          ~14GB"
    
    echo -e "\n${CYAN}【Baichuan 系列 - 百川智能】${NC}"
    echo -e "  18) Baichuan2 (7B)             ~14GB"
    
    echo -e "\n${CYAN}【自定义】${NC}"
    echo -e "  99) 输入自定义模型名称"
    
    echo -e "\n${YELLOW}提示: GPU_NV_S (T4 16GB) 建议选择 7B 以下模型${NC}"
    echo -e "${YELLOW}      GPU_NV_M (A10 24GB) 可运行 7-13B 模型${NC}"
}

# ============================================
# 显示镜像源选择菜单
# ============================================
show_mirror_menu() {
    echo -e "\n${BLUE}============================================${NC}"
    echo -e "${BLUE}          选择模型下载镜像源${NC}"
    echo -e "${BLUE}============================================${NC}"
    
    echo -e "\n${CYAN}【可用镜像源】${NC}"
    echo -e "  1) ${GREEN}hf-mirror.com${NC}          ${GREEN}[推荐]${NC} 国内访问最快"
    echo -e "     └─ https://hf-mirror.com"
    echo -e "  2) HuggingFace 官方           需要科学上网"
    echo -e "     └─ https://huggingface.co"
    echo -e "  3) 上海交大镜像               教育网访问快"
    echo -e "     └─ https://mirror.sjtu.edu.cn/hugging-face-models"
    echo -e "  4) HF-Mirror CDN              备用镜像"
    echo -e "     └─ https://hf-cdn.hf-mirror.com"
    echo -e "  99) 输入自定义镜像地址"
    
    echo -e "\n${YELLOW}提示: 中国大陆用户推荐使用 hf-mirror.com${NC}"
}

# ============================================
# 根据模型名称获取服务后缀
# ============================================
get_service_suffix() {
    local model="$1"
    case "$model" in
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B") echo "DEEPSEEK_1_5B" ;;
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B") echo "DEEPSEEK_7B" ;;
        "deepseek-ai/deepseek-coder-1.3b-instruct") echo "DEEPSEEK_CODER" ;;
        "deepseek-ai/deepseek-llm-7b-chat") echo "DEEPSEEK_CHAT" ;;
        "Qwen/Qwen2.5-1.5B-Instruct") echo "QWEN_1_5B" ;;
        "Qwen/Qwen2.5-3B-Instruct") echo "QWEN_3B" ;;
        "Qwen/Qwen2.5-7B-Instruct") echo "QWEN_7B" ;;
        "Qwen/Qwen2.5-Coder-1.5B-Instruct") echo "QWEN_CODER_1_5B" ;;
        "Qwen/Qwen2.5-Coder-7B-Instruct") echo "QWEN_CODER_7B" ;;
        "THUDM/chatglm3-6b") echo "CHATGLM3" ;;
        "THUDM/glm-4-9b-chat") echo "GLM4" ;;
        "meta-llama/Llama-3.2-1B-Instruct") echo "LLAMA_1B" ;;
        "meta-llama/Llama-3.2-3B-Instruct") echo "LLAMA_3B" ;;
        "01-ai/Yi-1.5-6B-Chat") echo "YI_6B" ;;
        "01-ai/Yi-1.5-9B-Chat") echo "YI_9B" ;;
        "internlm/internlm2_5-1_8b-chat") echo "INTERNLM_1_8B" ;;
        "internlm/internlm2_5-7b-chat") echo "INTERNLM_7B" ;;
        "baichuan-inc/Baichuan2-7B-Chat") echo "BAICHUAN_7B" ;;
        *)
            # 为自定义模型生成后缀：取模型名并转换为大写下划线格式
            echo "$model" | sed 's/.*\///' | tr '[:lower:]' '[:upper:]' | tr '-.' '_'
            ;;
    esac
}

# ============================================
# 交互式选择模型
# ============================================
select_model() {
    if [ -n "$MODEL_NAME" ]; then
        echo -e "${GREEN}使用预设模型: ${MODEL_NAME}${NC}"
        # 自动根据模型名称生成服务后缀
        SERVICE_SUFFIX=$(get_service_suffix "$MODEL_NAME")
        SERVICE_NAME="LLM_SERVICE_${SERVICE_SUFFIX}"
        echo -e "${GREEN}服务名称: ${SERVICE_NAME}${NC}"
        return
    fi
    
    show_model_menu
    
    echo -e "\n请输入模型编号 (1-18, 或 99 自定义): "
    read -r model_choice
    
    case "$model_choice" in
        1) MODEL_NAME="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"; SERVICE_SUFFIX="DEEPSEEK_1_5B" ;;
        2) MODEL_NAME="deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"; SERVICE_SUFFIX="DEEPSEEK_7B" ;;
        3) MODEL_NAME="deepseek-ai/deepseek-coder-1.3b-instruct"; SERVICE_SUFFIX="DEEPSEEK_CODER" ;;
        4) MODEL_NAME="deepseek-ai/deepseek-llm-7b-chat"; SERVICE_SUFFIX="DEEPSEEK_CHAT" ;;
        5) MODEL_NAME="Qwen/Qwen2.5-1.5B-Instruct"; SERVICE_SUFFIX="QWEN_1_5B" ;;
        6) MODEL_NAME="Qwen/Qwen2.5-3B-Instruct"; SERVICE_SUFFIX="QWEN_3B" ;;
        7) MODEL_NAME="Qwen/Qwen2.5-7B-Instruct"; SERVICE_SUFFIX="QWEN_7B" ;;
        8) MODEL_NAME="Qwen/Qwen2.5-Coder-1.5B-Instruct"; SERVICE_SUFFIX="QWEN_CODER_1_5B" ;;
        9) MODEL_NAME="Qwen/Qwen2.5-Coder-7B-Instruct"; SERVICE_SUFFIX="QWEN_CODER_7B" ;;
        10) MODEL_NAME="THUDM/chatglm3-6b"; SERVICE_SUFFIX="CHATGLM3" ;;
        11) MODEL_NAME="THUDM/glm-4-9b-chat"; SERVICE_SUFFIX="GLM4" ;;
        12) MODEL_NAME="meta-llama/Llama-3.2-1B-Instruct"; SERVICE_SUFFIX="LLAMA_1B" ;;
        13) MODEL_NAME="meta-llama/Llama-3.2-3B-Instruct"; SERVICE_SUFFIX="LLAMA_3B" ;;
        14) MODEL_NAME="01-ai/Yi-1.5-6B-Chat"; SERVICE_SUFFIX="YI_6B" ;;
        15) MODEL_NAME="01-ai/Yi-1.5-9B-Chat"; SERVICE_SUFFIX="YI_9B" ;;
        16) MODEL_NAME="internlm/internlm2_5-1_8b-chat"; SERVICE_SUFFIX="INTERNLM_1_8B" ;;
        17) MODEL_NAME="internlm/internlm2_5-7b-chat"; SERVICE_SUFFIX="INTERNLM_7B" ;;
        18) MODEL_NAME="baichuan-inc/Baichuan2-7B-Chat"; SERVICE_SUFFIX="BAICHUAN_7B" ;;
        99)
            echo -e "请输入模型名称 (格式: org/model-name):"
            read -r MODEL_NAME
            echo -e "请输入服务后缀名 (用于区分不同服务, 如 MY_MODEL):"
            read -r SERVICE_SUFFIX
            ;;
        *)
            echo -e "${RED}无效选择，使用默认模型${NC}"
            MODEL_NAME="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
            SERVICE_SUFFIX="DEEPSEEK_1_5B"
            ;;
    esac
    
    # 更新服务名称
    SERVICE_NAME="LLM_SERVICE_${SERVICE_SUFFIX}"
    
    echo -e "\n${GREEN}已选择模型: ${MODEL_NAME}${NC}"
    echo -e "${GREEN}服务名称: ${SERVICE_NAME}${NC}"
}

# ============================================
# 交互式选择镜像源
# ============================================
select_mirror() {
    if [ -n "$HF_ENDPOINT" ]; then
        echo -e "${GREEN}使用预设镜像源: ${HF_ENDPOINT}${NC}"
        return
    fi
    
    show_mirror_menu
    
    echo -e "\n请输入镜像源编号 (1-4, 或 99 自定义): "
    read -r mirror_choice
    
    case "$mirror_choice" in
        1) HF_ENDPOINT="https://hf-mirror.com" ;;
        2) HF_ENDPOINT="https://huggingface.co" ;;
        3) HF_ENDPOINT="https://mirror.sjtu.edu.cn/hugging-face-models" ;;
        4) HF_ENDPOINT="https://hf-cdn.hf-mirror.com" ;;
        99)
            echo -e "请输入自定义镜像地址 (如 https://my-mirror.com):"
            read -r HF_ENDPOINT
            ;;
        *)
            echo -e "${YELLOW}使用默认镜像源: hf-mirror.com${NC}"
            HF_ENDPOINT="https://hf-mirror.com"
            ;;
    esac
    
    echo -e "\n${GREEN}已选择镜像源: ${HF_ENDPOINT}${NC}"
}

# ============================================
# 显示部署摘要
# ============================================
show_deploy_summary() {
    echo -e "\n${BLUE}============================================${NC}"
    echo -e "${BLUE}            部署配置摘要${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo -e "  连接名称:    ${CONNECTION}"
    echo -e "  数据库:      ${DATABASE}"
    echo -e "  Schema:      ${SCHEMA}"
    echo -e "  计算池:      ${COMPUTE_POOL}"
    echo -e "  服务名称:    ${SERVICE_NAME}"
    echo -e "  模型名称:    ${MODEL_NAME}"
    echo -e "  镜像源:      ${HF_ENDPOINT}"
    echo -e "${BLUE}============================================${NC}"
    
    echo -e "\n${YELLOW}确认部署? (y/N): ${NC}"
    read -r confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo -e "${RED}部署已取消${NC}"
        exit 0
    fi
}

# ============================================
# 检查必要工具
# ============================================
check_prerequisites() {
    echo -e "\n${YELLOW}[1/8] 检查必要工具...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}错误: Docker 未安装${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker 已安装${NC}"
    
    if ! command -v snow &> /dev/null; then
        echo -e "${RED}错误: Snowflake CLI (snow) 未安装${NC}"
        echo -e "请安装: pip install snowflake-cli-labs"
        exit 1
    fi
    echo -e "${GREEN}✓ Snowflake CLI 已安装${NC}"
    
    # 验证连接
    echo -e "验证 Snowflake 连接..."
    if ! snow sql -c "$CONNECTION" -q "SELECT CURRENT_USER();" &>/dev/null; then
        echo -e "${RED}错误: 无法连接到 Snowflake (连接: $CONNECTION)${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Snowflake 连接正常${NC}"
}

# ============================================
# 创建数据库和 Schema
# ============================================
setup_database() {
    echo -e "\n${YELLOW}[2/8] 创建数据库和 Schema...${NC}"
    
    snow sql -c "$CONNECTION" -q "
    CREATE DATABASE IF NOT EXISTS ${DATABASE};
    CREATE SCHEMA IF NOT EXISTS ${DATABASE}.${SCHEMA};
    "
    echo -e "${GREEN}✓ 数据库和 Schema 创建完成${NC}"
}

# ============================================
# 创建计算池
# ============================================
create_compute_pool() {
    echo -e "\n${YELLOW}[3/8] 创建 GPU 计算池...${NC}"
    
    snow sql -c "$CONNECTION" -q "
    CREATE COMPUTE POOL IF NOT EXISTS ${COMPUTE_POOL}
        MIN_NODES = 1
        MAX_NODES = 1
        INSTANCE_FAMILY = GPU_NV_S
        AUTO_RESUME = TRUE
        AUTO_SUSPEND_SECS = 600
        COMMENT = 'GPU compute pool for LLM inference';
    " || echo -e "${YELLOW}计算池可能已存在${NC}"
    
    echo -e "${GREEN}✓ 计算池创建完成${NC}"
}

# ============================================
# 创建外部访问
# ============================================
create_external_access() {
    echo -e "\n${YELLOW}[4/8] 配置外部网络访问...${NC}"
    
    snow sql -c "$CONNECTION" -q "
    USE DATABASE ${DATABASE};
    USE SCHEMA ${SCHEMA};
    
    CREATE OR REPLACE NETWORK RULE model_download_rule
        MODE = EGRESS
        TYPE = HOST_PORT
        VALUE_LIST = (
            'hf-mirror.com:443',
            'cdn-lfs.hf-mirror.com:443',
            'hf-cdn.hf-mirror.com:443',
            'www.modelscope.cn:443',
            'modelscope.cn:443',
            'cdn-lfs-cn-1.modelscope.cn:443',
            'cdn-lfs-cn-2.modelscope.cn:443',
            'cdn.modelscope.cn:443',
            'cdn-lfs.huggingface.co:443',
            'huggingface.co:443',
            'mirror.sjtu.edu.cn:443',
            'cas-bridge.xethub.hf.co:443',
            'xethub.hf.co:443',
            'cdn.xethub.hf.co:443'
        )
        COMMENT = 'Network rule for model download from various mirrors';
    
    CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION model_access_integration
        ALLOWED_NETWORK_RULES = (model_download_rule)
        ENABLED = TRUE
        COMMENT = 'External access for model download';
    "
    echo -e "${GREEN}✓ 外部访问配置完成${NC}"
}

# ============================================
# 创建镜像仓库
# ============================================
create_image_repo() {
    echo -e "\n${YELLOW}[5/8] 创建镜像仓库...${NC}"
    
    snow sql -c "$CONNECTION" -q "
    USE DATABASE ${DATABASE};
    USE SCHEMA ${SCHEMA};
    
    CREATE IMAGE REPOSITORY IF NOT EXISTS MODEL_SERVICE_REPO
        COMMENT = 'Image repository for SPCS model service';
    "
    
    # 获取仓库 URL
    REPO_URL=$(snow sql -c "$CONNECTION" -q "SHOW IMAGE REPOSITORIES LIKE 'MODEL_SERVICE_REPO' IN SCHEMA ${DATABASE}.${SCHEMA};" --format json 2>/dev/null | python3 -c "import sys,json; data=json.load(sys.stdin); print(data[0]['repository_url'] if data else '')" 2>/dev/null || echo "")
    
    if [ -z "$REPO_URL" ]; then
        echo -e "${YELLOW}无法自动获取仓库 URL，请手动获取:${NC}"
        snow sql -c "$CONNECTION" -q "SHOW IMAGE REPOSITORIES LIKE 'MODEL_SERVICE_REPO' IN SCHEMA ${DATABASE}.${SCHEMA};"
        echo -e "\n请输入 repository_url 列的值:"
        read -r REPO_URL
    fi
    
    export REGISTRY_URL="$REPO_URL"
    REGISTRY_HOST=$(echo "$REPO_URL" | cut -d'/' -f1)
    export REGISTRY_HOST
    
    echo -e "${GREEN}✓ 镜像仓库: ${REGISTRY_URL}${NC}"
}

# ============================================
# 构建 Docker 镜像
# ============================================
build_image() {
    echo -e "\n${YELLOW}[6/8] 构建 Docker 镜像...${NC}"
    
    cd "$SCRIPT_DIR/model_service"
    
    echo -e "构建镜像: ${IMAGE_NAME}:${IMAGE_TAG}"
    docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .
    
    echo -e "${GREEN}✓ 镜像构建完成${NC}"
}

# ============================================
# 推送镜像
# ============================================
push_image() {
    echo -e "\n${YELLOW}[7/8] 推送镜像到 Snowflake...${NC}"
    
    echo -e "登录到 Snowflake 镜像仓库: ${REGISTRY_HOST}"
    
    # 尝试使用 PAT token 文件
    PAT_FILE="$HOME/.snowflake/china_dev-token.txt"
    if [ -f "$PAT_FILE" ]; then
        echo -e "使用 PAT token 文件: $PAT_FILE"
        cat "$PAT_FILE" | docker login "$REGISTRY_HOST" -u SNOW_PROD_USER --password-stdin
    else
        echo -e "${YELLOW}请输入 Docker 登录密码 (PAT Token):${NC}"
        docker login "$REGISTRY_HOST"
    fi
    
    FULL_IMAGE="${REGISTRY_URL}/${IMAGE_NAME}:${IMAGE_TAG}"
    
    echo -e "标记镜像: ${FULL_IMAGE}"
    docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${FULL_IMAGE}"
    
    echo -e "推送镜像..."
    docker push "${FULL_IMAGE}"
    
    echo -e "${GREEN}✓ 镜像推送完成${NC}"
}

# ============================================
# 创建服务
# ============================================
create_service() {
    echo -e "\n${YELLOW}[8/8] 创建 SPCS 服务...${NC}"
    
    # 先删除已有服务（如果存在）
    snow sql -c "$CONNECTION" -q "DROP SERVICE IF EXISTS ${DATABASE}.${SCHEMA}.${SERVICE_NAME};" 2>/dev/null || true
    
    snow sql -c "$CONNECTION" -q "
    USE DATABASE ${DATABASE};
    USE SCHEMA ${SCHEMA};
    
    CREATE SERVICE ${SERVICE_NAME}
        IN COMPUTE POOL ${COMPUTE_POOL}
        MIN_INSTANCES = 1
        MAX_INSTANCES = 1
        EXTERNAL_ACCESS_INTEGRATIONS = (model_access_integration)
        FROM SPECIFICATION \$\$
spec:
  containers:
    - name: model-service
      image: /${DATABASE}/${SCHEMA}/model_service_repo/${IMAGE_NAME}:${IMAGE_TAG}
      env:
        MODEL_NAME: \"${MODEL_NAME}\"
        HF_ENDPOINT: \"${HF_ENDPOINT}\"
        MODELSCOPE_CACHE: \"/app/models\"
        MAX_NEW_TOKENS: \"2048\"
      resources:
        requests:
          memory: 10Gi
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
    - name: llm-api
      port: 8001
      public: false
\$\$;
    "
    
    echo -e "${GREEN}✓ 服务创建完成${NC}"
    
    # 创建 UDF
    create_udf
}

# ============================================
# 创建 UDF
# ============================================
create_udf() {
    echo -e "\n创建 UDF..."
    
    UDF_NAME="LLM_COMPLETE_${SERVICE_SUFFIX}"
    
    snow sql -c "$CONNECTION" -q "
    USE DATABASE ${DATABASE};
    USE SCHEMA ${SCHEMA};
    
    CREATE OR REPLACE FUNCTION ${UDF_NAME}(prompt VARCHAR)
    RETURNS VARCHAR
    SERVICE = ${SERVICE_NAME}
    ENDPOINT = 'llm-api'
    MAX_BATCH_ROWS = 1
    AS '/v1/chat/completions';
    
    GRANT USAGE ON FUNCTION ${UDF_NAME}(VARCHAR) TO ROLE PUBLIC;
    "
    
    echo -e "${GREEN}✓ UDF 创建完成: ${UDF_NAME}${NC}"
}

# ============================================
# 检查服务状态
# ============================================
check_status() {
    echo -e "\n${YELLOW}检查服务状态...${NC}"
    
    snow sql -c "$CONNECTION" -q "SELECT SYSTEM\$GET_SERVICE_STATUS('${DATABASE}.${SCHEMA}.${SERVICE_NAME}');"
}

# ============================================
# 等待服务就绪
# ============================================
wait_for_service() {
    echo -e "\n${YELLOW}等待服务就绪 (模型下载中，预计需要 3-10 分钟)...${NC}"
    
    for i in {1..30}; do
        STATUS=$(snow sql -c "$CONNECTION" -q "SELECT SYSTEM\$GET_SERVICE_STATUS('${DATABASE}.${SCHEMA}.${SERVICE_NAME}');" --format json 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['SYSTEM\$GET_SERVICE_STATUS(\'${DATABASE}.${SCHEMA}.${SERVICE_NAME}\')'])" 2>/dev/null || echo "")
        
        if echo "$STATUS" | grep -q '"status":"READY"'; then
            echo -e "\n${GREEN}✓ 服务已就绪!${NC}"
            return 0
        fi
        
        echo -e "等待中... ($i/30) - 当前状态: $(echo "$STATUS" | grep -o '"status":"[^"]*"' | head -1)"
        sleep 20
    done
    
    echo -e "\n${YELLOW}服务尚未就绪，请手动检查状态:${NC}"
    echo -e "snow sql -c $CONNECTION -q \"SELECT SYSTEM\\\$GET_SERVICE_LOGS('${DATABASE}.${SCHEMA}.${SERVICE_NAME}', 0, 'model-service', 50);\""
}

# ============================================
# 测试服务
# ============================================
test_service() {
    echo -e "\n${YELLOW}测试 LLM 服务...${NC}"
    
    UDF_NAME="LLM_COMPLETE_${SERVICE_SUFFIX}"
    
    snow sql -c "$CONNECTION" -q "
    SELECT ${DATABASE}.${SCHEMA}.${UDF_NAME}(
        '{\"model\":\"${MODEL_NAME}\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello! Please introduce yourself briefly.\"}]}'
    ) AS response;
    "
}

# ============================================
# 查看日志
# ============================================
view_logs() {
    echo -e "\n${YELLOW}服务日志:${NC}"
    snow sql -c "$CONNECTION" -q "SELECT SYSTEM\$GET_SERVICE_LOGS('${DATABASE}.${SCHEMA}.${SERVICE_NAME}', 0, 'model-service', 100);"
}

# ============================================
# 清理资源
# ============================================
cleanup() {
    echo -e "\n${YELLOW}清理资源...${NC}"
    
    UDF_NAME="LLM_COMPLETE_${SERVICE_SUFFIX}"
    
    read -p "确定要删除服务和相关资源吗? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "取消操作"
        return
    fi
    
    snow sql -c "$CONNECTION" -q "
    DROP SERVICE IF EXISTS ${DATABASE}.${SCHEMA}.${SERVICE_NAME};
    DROP FUNCTION IF EXISTS ${DATABASE}.${SCHEMA}.${UDF_NAME}(VARCHAR);
    " || true
    
    echo -e "${GREEN}✓ 清理完成${NC}"
}

# ============================================
# 列出所有已部署的服务
# ============================================
list_services() {
    echo -e "\n${YELLOW}已部署的 LLM 服务:${NC}"
    
    snow sql -c "$CONNECTION" -q "
    SHOW SERVICES LIKE 'LLM_SERVICE_%' IN SCHEMA ${DATABASE}.${SCHEMA};
    "
}

# ============================================
# 显示帮助
# ============================================
show_help() {
    echo "LLM 模型一键部署脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  deploy      交互式完整部署 (默认)"
    echo "  quick       快速部署（跳过镜像构建）"
    echo "  build       仅构建镜像"
    echo "  push        构建并推送镜像"
    echo "  service     仅创建服务 (镜像已存在)"
    echo "  status      检查服务状态"
    echo "  logs        查看服务日志"
    echo "  test        测试服务"
    echo "  list        列出所有已部署的服务"
    echo "  cleanup     清理资源"
    echo "  models      显示可用模型列表"
    echo "  mirrors     显示可用镜像源列表"
    echo "  help        显示帮助"
    echo ""
    echo "环境变量:"
    echo "  SNOWFLAKE_CONNECTION  Snowflake 连接名 (默认: china_dev)"
    echo "  MODEL_NAME            预设模型名称 (跳过选择)"
    echo "  HF_ENDPOINT           预设镜像源 (跳过选择)"
    echo "  IMAGE_TAG             镜像标签 (默认: latest)"
    echo ""
    echo "示例:"
    echo "  # 交互式部署"
    echo "  ./deploy_model.sh deploy"
    echo ""
    echo "  # 使用预设模型快速部署"
    echo "  MODEL_NAME=\"Qwen/Qwen2.5-1.5B-Instruct\" HF_ENDPOINT=\"https://hf-mirror.com\" ./deploy_model.sh deploy"
}

# ============================================
# 主函数
# ============================================
main() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}   LLM 模型 SPCS 一键部署工具${NC}"
    echo -e "${BLUE}   连接: ${CONNECTION}${NC}"
    echo -e "${BLUE}============================================${NC}"
    
    case "${1:-deploy}" in
        deploy)
            select_model
            select_mirror
            show_deploy_summary
            check_prerequisites
            setup_database
            create_compute_pool
            create_external_access
            create_image_repo
            build_image
            push_image
            create_service
            wait_for_service
            test_service
            ;;
        quick)
            select_model
            select_mirror
            show_deploy_summary
            check_prerequisites
            setup_database
            create_compute_pool
            create_external_access
            create_image_repo
            create_service
            wait_for_service
            ;;
        build)
            check_prerequisites
            build_image
            ;;
        push)
            check_prerequisites
            create_image_repo
            build_image
            push_image
            ;;
        service)
            select_model
            select_mirror
            check_prerequisites
            create_image_repo
            create_service
            wait_for_service
            ;;
        status)
            select_model
            check_status
            ;;
        logs)
            select_model
            view_logs
            ;;
        test)
            select_model
            test_service
            ;;
        list)
            list_services
            ;;
        cleanup)
            select_model
            cleanup
            ;;
        models)
            show_model_menu
            ;;
        mirrors)
            show_mirror_menu
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}未知命令: $1${NC}"
            show_help
            exit 1
            ;;
    esac
    
    echo -e "\n${GREEN}============================================${NC}"
    echo -e "${GREEN}   操作完成!${NC}"
    echo -e "${GREEN}============================================${NC}"
    
    if [ -n "$SERVICE_SUFFIX" ]; then
        UDF_NAME="LLM_COMPLETE_${SERVICE_SUFFIX}"
        echo -e "\n${BLUE}使用示例:${NC}"
        echo -e "SELECT ${DATABASE}.${SCHEMA}.${UDF_NAME}("
        echo -e "  '{\"model\":\"${MODEL_NAME}\",\"messages\":[{\"role\":\"user\",\"content\":\"你好\"}]}'"
        echo -e ");"
    fi
}

main "$@"
