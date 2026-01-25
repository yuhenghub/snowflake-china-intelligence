"""
Snowflake China Intelligence
智能数据分析对话平台
"""

import json
import pandas as pd
import streamlit as st
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

# 设置页面配置
st.set_page_config(
    layout="wide",
    page_icon="❄️",
    page_title="Snowflake China Intelligence",
    initial_sidebar_state="expanded"
)

# ===============================
# 样式定义 - 同时支持 Light 和 Dark 主题
# ===============================
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Sans+SC:wght@300;400;500;700&display=swap');

/* 全局字体 */
* {
    font-family: 'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* 隐藏默认 Streamlit 头部 */
header[data-testid="stHeader"] {
    background: transparent;
}

/* 主标题区域 */
.greeting-container {
    padding: 3rem 0;
    text-align: center;
}

.greeting-text {
    font-size: 2.5rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.greeting-question {
    font-size: 2rem;
    font-weight: 500;
    background: linear-gradient(90deg, #29B5E8, #0068C9);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* 输入框容器 */
.input-container {
    max-width: 800px;
    margin: 2rem auto;
    padding: 0 1rem;
}

/* 建议问题按钮 */
.suggestion-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    cursor: pointer;
    transition: all 0.2s ease;
    border: 1px solid rgba(128, 128, 128, 0.2);
}

.suggestion-btn:hover {
    border-color: #29B5E8;
    background: rgba(41, 181, 232, 0.1);
}

/* 侧边栏样式 */
[data-testid="stSidebar"] {
    padding-top: 1rem;
}

.sidebar-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0;
    margin-bottom: 1rem;
}

.sidebar-logo {
    width: 24px;
    height: 24px;
}

.sidebar-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #29B5E8;
}

/* 新建对话按钮 */
.new-chat-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    border: 1px solid rgba(128, 128, 128, 0.3);
    cursor: pointer;
    transition: all 0.2s ease;
}

.new-chat-btn:hover {
    background: rgba(41, 181, 232, 0.1);
    border-color: #29B5E8;
}

/* 对话历史项 */
.chat-history-item {
    padding: 0.75rem 1rem;
    border-radius: 8px;
    margin: 0.25rem 0;
    cursor: pointer;
    transition: all 0.2s ease;
    border: 1px solid transparent;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.chat-history-item:hover {
    background: rgba(128, 128, 128, 0.1);
}

.chat-history-item.active {
    background: rgba(41, 181, 232, 0.15);
    border-color: #29B5E8;
}

/* 消息样式 */
.message-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 1rem;
}

.user-message {
    display: flex;
    justify-content: flex-end;
    margin: 1rem 0;
}

.user-message-content {
    max-width: 70%;
    padding: 1rem 1.25rem;
    border-radius: 16px 16px 4px 16px;
    background: #29B5E8;
    color: white;
}

.assistant-message {
    display: flex;
    justify-content: flex-start;
    margin: 1rem 0;
}

.assistant-message-content {
    max-width: 85%;
    padding: 1rem 1.25rem;
    border-radius: 16px 16px 16px 4px;
    border: 1px solid rgba(128, 128, 128, 0.2);
}

/* SQL 代码块 */
.sql-block {
    border-radius: 8px;
    margin: 1rem 0;
    overflow: hidden;
}

.sql-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 1rem;
    background: rgba(128, 128, 128, 0.1);
    font-size: 0.85rem;
}

/* Agent 选择器 */
.agent-selector {
    padding: 0.5rem;
    border-radius: 8px;
    border: 1px solid rgba(128, 128, 128, 0.2);
    margin: 0.5rem 0;
}

/* 时间分组标签 */
.time-label {
    font-size: 0.75rem;
    opacity: 0.6;
    padding: 0.5rem 1rem;
    margin-top: 1rem;
}

/* 输入区域底部工具栏 */
.input-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.5rem 0;
    margin-top: 0.5rem;
}

.toolbar-left {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.toolbar-btn {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.35rem 0.75rem;
    border-radius: 6px;
    font-size: 0.85rem;
    border: 1px solid rgba(128, 128, 128, 0.2);
    cursor: pointer;
    transition: all 0.2s ease;
}

.toolbar-btn:hover {
    border-color: #29B5E8;
}
</style>
"""

# ===============================
# Snowflake 连接
# ===============================
def get_snowflake_connection():
    """获取 Snowflake 连接"""
    try:
        from snowflake.snowpark.context import get_active_session
        session = get_active_session()
        return session.connection
    except Exception:
        return None

def get_snowpark_session():
    """获取 Snowpark Session"""
    try:
        from snowflake.snowpark.context import get_active_session
        return get_active_session()
    except Exception:
        return None

def get_current_user(conn) -> str:
    """获取当前用户名"""
    if not conn:
        return "用户"
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_USER()")
        user = cursor.fetchone()[0]
        # 格式化用户名（首字母大写）
        return user.title() if user else "用户"
    except Exception:
        return "用户"

# ===============================
# Qwen API 调用
# ===============================
def call_qwen_api(conn, model: str, prompt: str, system_prompt: str = None) -> str:
    """通过 Snowflake UDF 调用 Qwen API"""
    if not conn:
        return "错误: 未连接到 Snowflake"
    
    escaped_prompt = prompt.replace("'", "''").replace("\\", "\\\\")
    
    if system_prompt:
        escaped_system = system_prompt.replace("'", "''").replace("\\", "\\\\")
        full_prompt = f"[系统指令]: {escaped_system}\n\n[用户问题]: {escaped_prompt}"
    else:
        full_prompt = escaped_prompt
    
    # 使用配置的 UDF 路径
    udf_path = st.session_state.get("qwen_udf_path", "SNOWFLAKE_PROD_USER1.CORTEX_ANALYST.QWEN_COMPLETE")
    query = f"SELECT {udf_path}('{model}', $${full_prompt}$$)"
    
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        if result and result[0]:
            return result[0]
        return ""
    except Exception as e:
        return f"错误: {str(e)}"

# ===============================
# 时间问候
# ===============================
def get_greeting() -> str:
    """根据当前时间返回问候语"""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "早上好"
    elif 12 <= hour < 18:
        return "下午好"
    else:
        return "晚上好"

# ===============================
# SQL 生成
# ===============================
def generate_sql_with_semantic_model(conn, question: str, semantic_model: str, tables: List[str], model: str) -> str:
    """使用语义模型生成 SQL"""
    
    system_prompt = f"""你是一个专业的 Snowflake SQL 专家。请根据以下语义模型来理解数据的业务含义，并生成正确的 SQL 查询。

## 语义模型定义：
```yaml
{semantic_model[:4000]}
```

## 规则：
1. 根据语义模型中的 description 理解字段含义
2. 使用语义模型中的 expr 作为 SQL 表达式
3. 参考 synonyms 来匹配用户使用的业务术语
4. 生成有效的 Snowflake SQL
5. 只返回 SQL 语句，不要任何解释
6. 添加 LIMIT 100 限制结果数量
"""
    
    response = call_qwen_api(conn, model, question, system_prompt)
    
    # 清理响应
    sql = response.strip()
    if sql.startswith("```"):
        lines = sql.split("\n")
        sql_lines = []
        in_code = False
        for line in lines:
            if line.startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                sql_lines.append(line)
        sql = "\n".join(sql_lines).strip()
    
    return sql

def execute_sql(conn, sql: str) -> Dict[str, Any]:
    """执行 SQL 查询"""
    if not conn:
        return {"success": False, "error": "未连接到 Snowflake"}
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=columns)
        return {
            "success": True,
            "data": df,
            "row_count": len(df),
            "columns": columns
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ===============================
# 对话管理
# ===============================
def create_new_chat():
    """创建新对话"""
    chat_id = str(uuid.uuid4())[:8]
    return {
        "id": chat_id,
        "title": "新对话",
        "messages": [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

def get_chat_title(messages: List[Dict]) -> str:
    """从消息中提取对话标题"""
    for msg in messages:
        if msg["role"] == "user":
            title = msg["content"][:30]
            if len(msg["content"]) > 30:
                title += "..."
            return title
    return "新对话"

# ===============================
# 主应用
# ===============================
def main():
    # 注入自定义样式
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    # 获取连接
    conn = get_snowflake_connection()
    user_name = get_current_user(conn)
    
    # 初始化 session state
    if "chats" not in st.session_state:
        st.session_state.chats = [create_new_chat()]
    
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = st.session_state.chats[0]["id"]
    
    if "selected_agent" not in st.session_state:
        st.session_state.selected_agent = None
    
    if "qwen_udf_path" not in st.session_state:
        st.session_state.qwen_udf_path = "SNOWFLAKE_PROD_USER1.CORTEX_ANALYST.QWEN_COMPLETE"
    
    # 获取当前对话
    current_chat = None
    for chat in st.session_state.chats:
        if chat["id"] == st.session_state.current_chat_id:
            current_chat = chat
            break
    
    if not current_chat:
        current_chat = st.session_state.chats[0]
        st.session_state.current_chat_id = current_chat["id"]
    
    # ===== 侧边栏 =====
    with st.sidebar:
        # Logo 和标题
        st.markdown("""
        <div class="sidebar-header">
            <span style="font-size: 1.5rem;">❄️</span>
            <span class="sidebar-title">intelligence</span>
        </div>
        """, unsafe_allow_html=True)
        
        # 新建对话按钮
        if st.button("📝 New chat", use_container_width=True, key="new_chat_btn"):
            new_chat = create_new_chat()
            st.session_state.chats.insert(0, new_chat)
            st.session_state.current_chat_id = new_chat["id"]
            st.rerun()
        
        # Agents 配置
        st.markdown("---")
        with st.expander("🤖 Agents", expanded=True):
            # 从 Agent 配置中加载
            agent_config = st.session_state.get("agent_config", {})
            
            if agent_config and agent_config.get("semantic_model_content"):
                st.success(f"✅ {agent_config.get('semantic_model_file', 'Agent 已配置')}")
                st.session_state.selected_agent = agent_config
            else:
                st.info("💡 请在 Cortex Agent 中配置数据源和语义模型")
                
                # 手动配置选项
                with st.expander("手动配置"):
                    udf_path = st.text_input(
                        "Qwen UDF 路径",
                        value=st.session_state.qwen_udf_path,
                        key="udf_path_input"
                    )
                    st.session_state.qwen_udf_path = udf_path
        
        # 搜索对话
        st.text_input("🔍 Search chats", key="search_chats", placeholder="搜索历史对话...")
        
        # 对话历史
        st.markdown('<div class="time-label">Last week</div>', unsafe_allow_html=True)
        
        search_term = st.session_state.get("search_chats", "").lower()
        
        for chat in st.session_state.chats:
            title = get_chat_title(chat["messages"])
            
            # 搜索过滤
            if search_term and search_term not in title.lower():
                continue
            
            # 对话项
            is_active = chat["id"] == st.session_state.current_chat_id
            
            if st.button(
                f"💬 {title}" if is_active else title,
                key=f"chat_{chat['id']}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state.current_chat_id = chat["id"]
                st.rerun()
        
        # 显示更多
        if len(st.session_state.chats) > 5:
            st.button("Show more", use_container_width=True, key="show_more")
        
        # 底部用户信息
        st.markdown("---")
        st.markdown(f"👤 **{user_name}**")
    
    # ===== 主内容区 =====
    
    # 如果没有消息，显示欢迎界面
    if not current_chat["messages"]:
        # 问候语
        greeting = get_greeting()
        st.markdown(f"""
        <div class="greeting-container">
            <div class="greeting-text">{greeting}, {user_name}</div>
            <div class="greeting-question">What insights can I help with?</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 输入框
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            user_input = st.text_input(
                "",
                placeholder="Ask Snowflake Intelligence...",
                key="main_input",
                label_visibility="collapsed"
            )
            
            # 工具栏
            tool_col1, tool_col2, tool_col3 = st.columns([2, 2, 3])
            with tool_col1:
                st.button("📎", key="attach_btn", help="附加文件")
            with tool_col2:
                # Agent 选择
                agent_config = st.session_state.get("agent_config", {})
                agent_name = agent_config.get("semantic_model_file", "Production Agent") if agent_config else "Production Agent"
                st.button(f"🤖 {agent_name}", key="agent_select_btn")
            with tool_col3:
                # 数据源
                sources = "Auto"
                st.button(f"📊 Sources: {sources}", key="sources_btn")
        
        # 建议问题
        st.markdown("---")
        
        suggestions = [
            "Show me production efficiency by assembly line",
            "What machines need maintenance?",
            "Show me quality issues by batch"
        ]
        
        for suggestion in suggestions:
            if st.button(f"💬 {suggestion}", key=f"sug_{suggestion[:20]}", use_container_width=True):
                # 添加用户消息
                current_chat["messages"].append({
                    "role": "user",
                    "content": suggestion
                })
                current_chat["updated_at"] = datetime.now().isoformat()
                st.rerun()
        
        # 处理输入
        if user_input:
            current_chat["messages"].append({
                "role": "user",
                "content": user_input
            })
            current_chat["updated_at"] = datetime.now().isoformat()
            st.rerun()
    
    else:
        # 显示对话历史
        st.markdown('<div class="message-container">', unsafe_allow_html=True)
        
        for msg in current_chat["messages"]:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="user-message">
                    <div class="user-message-content">{msg["content"]}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="assistant-message">
                    <div class="assistant-message-content">{msg["content"]}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # 如果有 SQL，显示
                if msg.get("sql"):
                    st.code(msg["sql"], language="sql")
                
                # 如果有数据，显示
                if msg.get("data") is not None:
                    st.dataframe(msg["data"], use_container_width=True, hide_index=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 底部输入框
        st.markdown("---")
        
        col1, col2 = st.columns([5, 1])
        with col1:
            new_input = st.text_input(
                "",
                placeholder="继续对话...",
                key="chat_input",
                label_visibility="collapsed"
            )
        with col2:
            send_btn = st.button("发送", type="primary", use_container_width=True)
        
        if new_input or send_btn:
            if new_input:
                # 添加用户消息
                current_chat["messages"].append({
                    "role": "user",
                    "content": new_input
                })
                
                # 生成回复
                with st.spinner("思考中..."):
                    agent_config = st.session_state.get("agent_config", {})
                    semantic_model = agent_config.get("semantic_model_content", "")
                    tables = agent_config.get("tables", [])
                    model = agent_config.get("llm_model", "qwen-max")
                    
                    if semantic_model:
                        # 使用语义模型生成 SQL
                        sql = generate_sql_with_semantic_model(
                            conn, new_input, semantic_model, tables, model
                        )
                        
                        # 执行 SQL
                        result = execute_sql(conn, sql)
                        
                        if result["success"]:
                            response_content = f"根据您的问题，我生成了以下查询，返回了 {result['row_count']} 条结果："
                            current_chat["messages"].append({
                                "role": "assistant",
                                "content": response_content,
                                "sql": sql,
                                "data": result["data"]
                            })
                        else:
                            current_chat["messages"].append({
                                "role": "assistant",
                                "content": f"抱歉，执行查询时出错：{result['error']}\n\n生成的 SQL：",
                                "sql": sql
                            })
                    else:
                        # 无语义模型，直接对话
                        response = call_qwen_api(conn, "qwen-max", new_input)
                        current_chat["messages"].append({
                            "role": "assistant",
                            "content": response
                        })
                
                current_chat["updated_at"] = datetime.now().isoformat()
                st.rerun()


if __name__ == "__main__":
    main()
