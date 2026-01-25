#!/bin/bash
# Cortex Agent & Intelligence 启动脚本
# 用于 Snowflake China 区域

echo "🚀 启动 Cortex Agent & Intelligence Demo..."
echo ""

# 检查环境变量
check_env() {
    if [ -z "${!1}" ]; then
        echo "⚠️  警告: $1 未设置"
        return 1
    else
        echo "✅ $1 已配置"
        return 0
    fi
}

echo "📋 检查环境配置..."
check_env "SNOWFLAKE_ACCOUNT_LOCATOR"
check_env "SNOWFLAKE_USER"
check_env "SNOWFLAKE_HOST"

# 设置中国区域标志
export USE_QWEN_FOR_CHINA=true
export QWEN_MODEL=${QWEN_MODEL:-"qwen-max"}
export QWEN_SQL_MODEL=${QWEN_SQL_MODEL:-"qwen-max"}

echo ""
echo "🔧 当前配置:"
echo "   - USE_QWEN_FOR_CHINA: $USE_QWEN_FOR_CHINA"
echo "   - QWEN_MODEL: $QWEN_MODEL"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "📂 工作目录: $SCRIPT_DIR"
echo ""

# 启动 Streamlit 应用
echo "🌐 启动 Streamlit 应用..."
echo "   访问地址: http://localhost:8502"
echo ""

streamlit run cortex_agent_app.py --server.port 8502 --server.headless true
