#!/bin/bash
# ============================================================================
# Cortex Agent & Intelligence - SiS 部署脚本
# 用于将应用部署到 Snowflake China 区域
# ============================================================================

set -e

echo "🚀 开始部署 Cortex Agent & Intelligence 到 Snowflake..."
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查环境变量
check_env() {
    if [ -z "${!1}" ]; then
        echo -e "${RED}❌ 错误: $1 未设置${NC}"
        return 1
    else
        echo -e "${GREEN}✅ $1${NC}"
        return 0
    fi
}

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}📋 检查环境配置...${NC}"
echo ""
ALL_SET=true

check_env "SNOWFLAKE_ACCOUNT" || ALL_SET=false
check_env "SNOWFLAKE_USER" || ALL_SET=false
check_env "SNOWFLAKE_PASSWORD" || check_env "SNOWFLAKE_PRIVATE_KEY_PATH" || ALL_SET=false

if [ "$ALL_SET" = false ]; then
    echo ""
    echo -e "${YELLOW}⚠️  请设置以上环境变量后重试${NC}"
    echo ""
    echo "示例:"
    echo "  export SNOWFLAKE_ACCOUNT=your_account"
    echo "  export SNOWFLAKE_USER=your_user"
    echo "  export SNOWFLAKE_PASSWORD=your_password"
    exit 1
fi

echo ""
echo -e "${BLUE}📂 工作目录: $SCRIPT_DIR${NC}"
echo ""

# 检查 Qwen API Key
if [ -z "$QWEN_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  QWEN_API_KEY 未设置${NC}"
    echo "请输入您的通义千问 API Key:"
    read -s QWEN_API_KEY
    echo ""
fi

# 创建临时 SQL 文件，替换 API Key
echo -e "${BLUE}📝 准备部署脚本...${NC}"
TEMP_SQL=$(mktemp)
sed "s/<YOUR_QWEN_API_KEY>/$QWEN_API_KEY/g" sis_setup/cortex_agent_sis_setup.sql > "$TEMP_SQL"

# 使用 SnowSQL 执行部署
echo -e "${BLUE}🔧 执行 Snowflake 部署...${NC}"
echo ""

if command -v snowsql &> /dev/null; then
    # 使用 SnowSQL
    echo "使用 SnowSQL 执行部署..."
    
    # 第一步：执行 SQL 创建数据库、Schema 和 UDF
    snowsql -a "$SNOWFLAKE_ACCOUNT" -u "$SNOWFLAKE_USER" \
        -f "$TEMP_SQL" \
        -o exit_on_error=true \
        -o friendly=false
    
    # 第二步：上传应用文件
    echo ""
    echo -e "${BLUE}📤 上传应用文件...${NC}"
    
    snowsql -a "$SNOWFLAKE_ACCOUNT" -u "$SNOWFLAKE_USER" -q "
        PUT file://$SCRIPT_DIR/cortex_agent_sis.py @CORTEX_ANALYST_SEMANTICS.CORTEX_AGENT.AGENT_STAGE/cortex_agent/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;
        PUT file://$SCRIPT_DIR/environment.yml @CORTEX_ANALYST_SEMANTICS.CORTEX_AGENT.AGENT_STAGE/cortex_agent/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;
    "
    
    echo ""
    echo -e "${GREEN}✅ 部署完成！${NC}"
    
elif command -v snow &> /dev/null; then
    # 使用 Snowflake CLI (snow)
    echo "使用 Snowflake CLI 执行部署..."
    
    snow sql -f "$TEMP_SQL"
    
    echo ""
    echo -e "${BLUE}📤 上传应用文件...${NC}"
    
    snow sql -q "PUT file://$SCRIPT_DIR/cortex_agent_sis.py @CORTEX_ANALYST_SEMANTICS.CORTEX_AGENT.AGENT_STAGE/cortex_agent/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;"
    snow sql -q "PUT file://$SCRIPT_DIR/environment.yml @CORTEX_ANALYST_SEMANTICS.CORTEX_AGENT.AGENT_STAGE/cortex_agent/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;"
    
    echo ""
    echo -e "${GREEN}✅ 部署完成！${NC}"
    
else
    echo -e "${YELLOW}⚠️  未找到 SnowSQL 或 Snowflake CLI${NC}"
    echo ""
    echo "请手动执行以下步骤:"
    echo ""
    echo "1. 在 Snowsight 中执行 SQL 文件:"
    echo "   $SCRIPT_DIR/sis_setup/cortex_agent_sis_setup.sql"
    echo "   (记得替换 <YOUR_QWEN_API_KEY> 为您的 API Key)"
    echo ""
    echo "2. 在 Snowsight SQL Worksheet 中执行以下命令上传文件:"
    echo "   PUT file://$SCRIPT_DIR/cortex_agent_sis.py @CORTEX_ANALYST_SEMANTICS.CORTEX_AGENT.AGENT_STAGE/cortex_agent/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;"
    echo "   PUT file://$SCRIPT_DIR/environment.yml @CORTEX_ANALYST_SEMANTICS.CORTEX_AGENT.AGENT_STAGE/cortex_agent/ OVERWRITE = TRUE AUTO_COMPRESS = FALSE;"
fi

# 清理临时文件
rm -f "$TEMP_SQL"

echo ""
echo "============================================"
echo -e "${GREEN}🎉 Cortex Agent & Intelligence 部署完成！${NC}"
echo "============================================"
echo ""
echo "📱 访问方式:"
echo "   1. 打开 Snowsight"
echo "   2. 导航到 Projects -> Streamlit"
echo "   3. 找到 'CORTEX_AGENT_APP' 并点击打开"
echo ""
echo "   或者使用以下命令获取 URL:"
echo "   snowsql -q \"SELECT GET_PRESIGNED_URL('@CORTEX_ANALYST_SEMANTICS.CORTEX_AGENT.AGENT_STAGE', 'cortex_agent/cortex_agent_sis.py');\""
echo ""
echo "📊 示例数据:"
echo "   数据库: CORTEX_ANALYST_SEMANTICS"
echo "   Schema: DEMO_DATA"
echo "   表: ORDERS, CUSTOMERS, PRODUCTS"
echo ""
