#!/bin/bash
# ============================================
# SPCS China Region 部署脚本
# 部署 LLM 服务到 Snowflake Container Services
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量 (请根据实际情况修改)
SNOWFLAKE_ACCOUNT="${SNOWFLAKE_ACCOUNT:-your_account}"
SNOWFLAKE_USER="${SNOWFLAKE_USER:-your_user}"
SNOWFLAKE_DATABASE="${SNOWFLAKE_DATABASE:-SPCS_CHINA}"
SNOWFLAKE_SCHEMA="${SNOWFLAKE_SCHEMA:-MODEL_SERVICE}"
IMAGE_REPO="${IMAGE_REPO:-model_service_repo}"
IMAGE_NAME="model-service"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}   SPCS China Region 部署工具${NC}"
echo -e "${BLUE}============================================${NC}"

# 检查必要工具
check_prerequisites() {
    echo -e "\n${YELLOW}[1/6] 检查必要工具...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}错误: Docker 未安装${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker 已安装${NC}"
    
    if ! command -v snowsql &> /dev/null; then
        echo -e "${YELLOW}警告: SnowSQL 未安装，将跳过 SQL 执行步骤${NC}"
        SNOWSQL_AVAILABLE=false
    else
        echo -e "${GREEN}✓ SnowSQL 已安装${NC}"
        SNOWSQL_AVAILABLE=true
    fi
}

# 获取镜像仓库 URL
get_registry_url() {
    echo -e "\n${YELLOW}[2/6] 获取镜像仓库 URL...${NC}"
    
    if [ "$SNOWSQL_AVAILABLE" = true ]; then
        REGISTRY_URL=$(snowsql -a "$SNOWFLAKE_ACCOUNT" -u "$SNOWFLAKE_USER" \
            -d "$SNOWFLAKE_DATABASE" -s "$SNOWFLAKE_SCHEMA" \
            -q "SELECT SYSTEM\$REGISTRY_URL('$IMAGE_REPO')" -o output_format=plain -o header=false 2>/dev/null | tr -d '[:space:]')
        
        if [ -z "$REGISTRY_URL" ]; then
            echo -e "${YELLOW}无法自动获取 Registry URL，请手动设置${NC}"
            read -p "请输入 Registry URL: " REGISTRY_URL
        fi
    else
        echo -e "${YELLOW}请手动输入镜像仓库 URL${NC}"
        echo -e "格式: <org>-<account>.registry.snowflakecomputing.cn/${SNOWFLAKE_DATABASE}/${SNOWFLAKE_SCHEMA}/${IMAGE_REPO}"
        read -p "Registry URL: " REGISTRY_URL
    fi
    
    echo -e "${GREEN}✓ Registry URL: ${REGISTRY_URL}${NC}"
}

# 构建 Docker 镜像
build_image() {
    echo -e "\n${YELLOW}[3/6] 构建 Docker 镜像...${NC}"
    
    cd "$SCRIPT_DIR/model_service"
    
    echo -e "构建镜像: ${IMAGE_NAME}:${IMAGE_TAG}"
    docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .
    
    echo -e "${GREEN}✓ 镜像构建完成${NC}"
}

# 登录到 Snowflake 镜像仓库
docker_login() {
    echo -e "\n${YELLOW}[4/6] 登录到 Snowflake 镜像仓库...${NC}"
    
    # 提取 registry host
    REGISTRY_HOST=$(echo "$REGISTRY_URL" | cut -d'/' -f1)
    
    echo -e "登录到: ${REGISTRY_HOST}"
    docker login "$REGISTRY_HOST" -u "$SNOWFLAKE_USER"
    
    echo -e "${GREEN}✓ 登录成功${NC}"
}

# 推送镜像
push_image() {
    echo -e "\n${YELLOW}[5/6] 推送镜像到 Snowflake...${NC}"
    
    FULL_IMAGE_NAME="${REGISTRY_URL}/${IMAGE_NAME}:${IMAGE_TAG}"
    
    echo -e "标记镜像: ${FULL_IMAGE_NAME}"
    docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${FULL_IMAGE_NAME}"
    
    echo -e "推送镜像..."
    docker push "${FULL_IMAGE_NAME}"
    
    echo -e "${GREEN}✓ 镜像推送完成${NC}"
}

# 创建/更新服务
deploy_service() {
    echo -e "\n${YELLOW}[6/6] 部署 SPCS 服务...${NC}"
    
    if [ "$SNOWSQL_AVAILABLE" = true ]; then
        echo -e "执行 SQL 脚本创建服务..."
        
        # 执行设置脚本
        for sql_file in "$SCRIPT_DIR"/setup_sql/*.sql; do
            echo -e "执行: $(basename "$sql_file")"
            snowsql -a "$SNOWFLAKE_ACCOUNT" -u "$SNOWFLAKE_USER" \
                -d "$SNOWFLAKE_DATABASE" -s "$SNOWFLAKE_SCHEMA" \
                -f "$sql_file" || echo -e "${YELLOW}警告: $sql_file 执行出错，请检查${NC}"
        done
        
        echo -e "${GREEN}✓ 服务部署完成${NC}"
    else
        echo -e "${YELLOW}SnowSQL 不可用，请手动执行以下 SQL 脚本:${NC}"
        echo -e "  1. setup_sql/01_create_compute_pool.sql"
        echo -e "  2. setup_sql/02_create_external_access.sql"
        echo -e "  3. setup_sql/03_create_image_repo.sql"
        echo -e "  4. setup_sql/04_create_service.sql"
        echo -e "  5. setup_sql/05_create_udf.sql"
    fi
}

# 显示帮助
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  build     仅构建 Docker 镜像"
    echo "  push      构建并推送镜像"
    echo "  deploy    完整部署 (构建 + 推送 + 创建服务)"
    echo "  sql       仅执行 SQL 脚本"
    echo "  help      显示帮助信息"
    echo ""
    echo "环境变量:"
    echo "  SNOWFLAKE_ACCOUNT   Snowflake 账户"
    echo "  SNOWFLAKE_USER      Snowflake 用户名"
    echo "  SNOWFLAKE_DATABASE  目标数据库 (默认: SPCS_CHINA)"
    echo "  SNOWFLAKE_SCHEMA    目标 Schema (默认: MODEL_SERVICE)"
    echo "  IMAGE_TAG           镜像标签 (默认: latest)"
}

# 主函数
main() {
    case "${1:-deploy}" in
        build)
            check_prerequisites
            build_image
            ;;
        push)
            check_prerequisites
            get_registry_url
            build_image
            docker_login
            push_image
            ;;
        deploy)
            check_prerequisites
            get_registry_url
            build_image
            docker_login
            push_image
            deploy_service
            ;;
        sql)
            check_prerequisites
            deploy_service
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
    echo -e "${GREEN}   部署完成!${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo -e "\n下一步操作:"
    echo -e "1. 设置 DashScope API Key:"
    echo -e "   ALTER SECRET dashscope_api_key_secret SET SECRET_STRING = 'your-api-key';"
    echo -e ""
    echo -e "2. 测试 UDF:"
    echo -e "   SELECT SPCS_CHINA.MODEL_SERVICE.QWEN_COMPLETE('qwen-turbo', '你好');"
    echo -e ""
    echo -e "3. 部署 Streamlit 应用:"
    echo -e "   - semantic_generator_app.py"
    echo -e "   - agent_intelligence_app.py"
}

main "$@"


