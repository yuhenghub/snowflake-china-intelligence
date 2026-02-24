"""
SPCS China - Streamlit 示例应用
演示如何在 Streamlit in Snowflake 中使用 QWEN_COMPLETE UDF

部署方式:
1. 在 Snowflake UI 中创建 Streamlit 应用
2. 复制此文件内容到 Streamlit 编辑器
3. 确保 SPCS 服务已启动并运行

前置条件:
- SPCS 服务 QWEN_MODEL_SERVICE 已部署并运行
- UDF SPCS_CHINA.MODEL_SERVICE.QWEN_COMPLETE 已创建
- 当前用户有执行该 UDF 的权限
"""

import streamlit as st
import json
from snowflake.snowpark.context import get_active_session

# ===============================
# 配置
# ===============================
# UDF 完整路径
QWEN_UDF_PATH = "SPCS_CHINA.MODEL_SERVICE.QWEN_COMPLETE"

# 服务名称
SERVICE_NAME = "SPCS_CHINA.MODEL_SERVICE.QWEN_MODEL_SERVICE"

# 默认模型
DEFAULT_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"


# ===============================
# 辅助函数
# ===============================
def get_current_warehouse(session) -> str:
    """获取当前 session 的 warehouse"""
    try:
        result = session.sql("SELECT CURRENT_WAREHOUSE()").collect()
        if result and result[0][0]:
            return result[0][0]
    except Exception:
        pass
    return None


def ensure_warehouse(session):
    """确保有可用的 warehouse"""
    current_wh = get_current_warehouse(session)
    if current_wh:
        return  # 已经有 warehouse，无需操作
    
    # 如果没有 warehouse，尝试获取可用的 warehouse 列表并使用第一个
    try:
        result = session.sql("SHOW WAREHOUSES").collect()
        if result and len(result) > 0:
            # 获取第一个 warehouse 的名称
            wh_name = result[0]["name"]
            session.sql(f"USE WAREHOUSE {wh_name}").collect()
    except Exception:
        pass  # 忽略错误，让后续操作自然报错


def call_qwen_complete(session, prompt: str, system_prompt: str = None, 
                       model: str = DEFAULT_MODEL, max_tokens: int = 2048,
                       temperature: float = 0.7) -> str:
    """
    调用 QWEN_COMPLETE UDF
    
    Args:
        session: Snowpark session
        prompt: 用户输入
        system_prompt: 系统提示词 (可选)
        model: 模型名称
        max_tokens: 最大输出 token 数
        temperature: 温度参数
    
    Returns:
        模型生成的响应文本
    """
    # 构建消息列表
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    # 构建请求 payload
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    # 转换为 JSON 字符串并转义
    payload_str = json.dumps(payload, ensure_ascii=False)
    # 转义单引号
    payload_escaped = payload_str.replace("'", "''")
    
    # 确保使用 warehouse
    ensure_warehouse(session)
    
    # 执行 UDF
    query = f"SELECT {QWEN_UDF_PATH}('{payload_escaped}')"
    
    try:
        result = session.sql(query).collect()
        if result and len(result) > 0:
            return result[0][0]
        return "没有收到响应"
    except Exception as e:
        return f"错误: {str(e)}"


def call_qwen_simple(session, prompt: str) -> str:
    """
    简化版调用 - 直接传入 prompt
    """
    # 确保使用 warehouse
    ensure_warehouse(session)
    
    payload = {
        "model": DEFAULT_MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }
    payload_str = json.dumps(payload, ensure_ascii=False).replace("'", "''")
    
    query = f"SELECT {QWEN_UDF_PATH}('{payload_str}')"
    result = session.sql(query).collect()
    return result[0][0] if result else ""


def get_service_status(session) -> dict:
    """获取 SPCS 服务状态"""
    try:
        query = f"SELECT SYSTEM$GET_SERVICE_STATUS('{SERVICE_NAME}')"
        result = session.sql(query).collect()
        if result and result[0][0]:
            return json.loads(result[0][0])
        return {"status": "UNKNOWN"}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


def suspend_service(session) -> str:
    """暂停 SPCS 服务"""
    try:
        query = f"ALTER SERVICE {SERVICE_NAME} SUSPEND"
        session.sql(query).collect()
        return "✅ 服务已暂停"
    except Exception as e:
        return f"❌ 暂停失败: {str(e)}"


def resume_service(session) -> str:
    """恢复 SPCS 服务"""
    try:
        query = f"ALTER SERVICE {SERVICE_NAME} RESUME"
        session.sql(query).collect()
        return "✅ 服务已恢复，请等待 1-2 分钟启动完成"
    except Exception as e:
        return f"❌ 恢复失败: {str(e)}"


# ===============================
# Streamlit 应用
# ===============================
def main():
    st.set_page_config(
        page_title="🤖 Qwen AI Assistant",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 Qwen AI Assistant")
    st.caption("基于 SPCS 部署的 Qwen2.5 大语言模型 (中国区)")
    
    # 获取 Snowflake session
    try:
        session = get_active_session()
        st.success("✅ 已连接到 Snowflake")
    except Exception as e:
        st.error(f"❌ 无法获取 Snowflake session: {e}")
        st.info("请确保此应用运行在 Streamlit in Snowflake 环境中")
        return
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 配置")
        
        model = st.selectbox(
            "选择模型",
            ["Qwen/Qwen2.5-1.5B-Instruct"],
            help="当前部署的模型"
        )
        
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="较高的值使输出更随机，较低的值使输出更确定"
        )
        
        max_tokens = st.slider(
            "Max Tokens",
            min_value=256,
            max_value=4096,
            value=2048,
            step=256,
            help="最大输出 token 数"
        )
        
        system_prompt = st.text_area(
            "系统提示词 (可选)",
            placeholder="例如: 你是一个专业的数据分析师...",
            help="设置 AI 的角色和行为"
        )
        
        st.divider()
        
        # ===============================
        # 服务控制面板
        # ===============================
        st.header("🎛️ 服务控制")
        
        # 获取服务状态
        if st.button("🔄 刷新状态"):
            st.session_state.service_status = get_service_status(session)
        
        # 显示服务状态
        if "service_status" not in st.session_state:
            st.session_state.service_status = get_service_status(session)
        
        status_info = st.session_state.service_status
        
        if isinstance(status_info, list) and len(status_info) > 0:
            instance = status_info[0]
            status = instance.get("status", "UNKNOWN")
            
            # 状态颜色
            if status == "READY":
                st.success(f"🟢 服务状态: {status}")
            elif status == "SUSPENDED":
                st.warning(f"🟡 服务状态: {status}")
            elif status in ["PENDING", "STARTING"]:
                st.info(f"🔵 服务状态: {status}")
            else:
                st.error(f"🔴 服务状态: {status}")
        elif isinstance(status_info, dict):
            status = status_info.get("status", "UNKNOWN")
            if "error" in status_info:
                st.error(f"状态: {status}\n错误: {status_info['error']}")
            else:
                st.info(f"状态: {status}")
        
        st.markdown("---")
        
        # 控制按钮
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("▶️ 启动", help="恢复暂停的服务"):
                with st.spinner("正在启动服务..."):
                    result = resume_service(session)
                    st.info(result)
                    st.session_state.service_status = get_service_status(session)
        
        with col2:
            if st.button("⏸️ 暂停", help="暂停服务以节省成本"):
                with st.spinner("正在暂停服务..."):
                    result = suspend_service(session)
                    st.info(result)
                    st.session_state.service_status = get_service_status(session)
        
        st.caption("💡 暂停服务可节省 GPU 计算成本")
    
    # 主界面
    tab1, tab2, tab3 = st.tabs(["💬 对话", "📝 批量处理", "🔧 SQL 调用示例"])
    
    # Tab 1: 对话界面 (兼容旧版 Streamlit)
    with tab1:
        # 初始化聊天历史
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # 显示聊天历史
        st.markdown("### 对话历史")
        chat_container = st.container()
        
        with chat_container:
            for i, message in enumerate(st.session_state.messages):
                if message["role"] == "user":
                    st.markdown(f"**🧑 用户:** {message['content']}")
                else:
                    st.markdown(f"**🤖 AI:** {message['content']}")
                st.markdown("---")
        
        # 用户输入 (使用 text_input 替代 chat_input)
        st.markdown("### 发送消息")
        user_input = st.text_area(
            "请输入您的问题:",
            key="user_input_area",
            height=100,
            placeholder="在这里输入您的问题..."
        )
        
        col1, col2 = st.columns([1, 5])
        with col1:
            send_button = st.button("🚀 发送", type="primary")
        with col2:
            if st.button("🗑️ 清除历史"):
                st.session_state.messages = []
                st.experimental_rerun()
        
        if send_button and user_input:
            # 添加用户消息
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # 生成 AI 响应
            with st.spinner("🤔 AI 思考中..."):
                response = call_qwen_complete(
                    session=session,
                    prompt=user_input,
                    system_prompt=system_prompt if system_prompt else None,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            
            # 添加 AI 响应到历史
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # 刷新页面显示新消息
            st.experimental_rerun()
    
    # Tab 2: 批量处理
    with tab2:
        st.subheader("批量文本处理")
        st.markdown("输入多行文本，每行单独处理")
        
        batch_input = st.text_area(
            "输入文本 (每行一个)",
            height=200,
            placeholder="第一个问题\n第二个问题\n第三个问题",
            key="batch_input"
        )
        
        batch_prompt = st.text_input(
            "处理指令",
            value="请用一句话回答以下问题: ",
            help="将添加到每个输入前面"
        )
        
        if st.button("🚀 开始批量处理"):
            if batch_input:
                lines = [line.strip() for line in batch_input.split("\n") if line.strip()]
                
                results = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, line in enumerate(lines):
                    status_text.text(f"处理 {i+1}/{len(lines)}: {line[:30]}...")
                    full_prompt = f"{batch_prompt}{line}"
                    response = call_qwen_simple(session, full_prompt)
                    results.append({
                        "输入": line,
                        "输出": response
                    })
                    progress_bar.progress((i + 1) / len(lines))
                
                status_text.text("✅ 处理完成!")
                st.success(f"处理完成，共 {len(results)} 条")
                
                # 显示结果
                for r in results:
                    with st.expander(f"📄 {r['输入'][:50]}..."):
                        st.write("**输入:**", r['输入'])
                        st.write("**输出:**", r['输出'])
            else:
                st.warning("请输入要处理的文本")
    
    # Tab 3: SQL 示例
    with tab3:
        st.subheader("SQL 调用示例")
        
        st.markdown("### 基础调用")
        st.code("""
-- 简单问答
SELECT SPCS_CHINA.MODEL_SERVICE.QWEN_COMPLETE(
  '{"model":"Qwen/Qwen2.5-1.5B-Instruct","messages":[{"role":"user","content":"什么是 Snowflake?"}]}'
);
        """, language="sql")
        
        st.markdown("### 带系统提示词")
        st.code("""
-- 设置 AI 角色
SELECT SPCS_CHINA.MODEL_SERVICE.QWEN_COMPLETE(
  '{"model":"Qwen/Qwen2.5-1.5B-Instruct","messages":[
    {"role":"system","content":"你是一个数据分析专家，请简洁回答"},
    {"role":"user","content":"如何优化 SQL 查询?"}
  ]}'
);
        """, language="sql")
        
        st.markdown("### 批量处理表数据")
        st.code("""
-- 为每条记录生成摘要
SELECT 
    id,
    description,
    SPCS_CHINA.MODEL_SERVICE.QWEN_COMPLETE(
      '{"model":"Qwen/Qwen2.5-1.5B-Instruct","messages":[
        {"role":"system","content":"生成一句话摘要"},
        {"role":"user","content":"' || REPLACE(description, '"', '\\\\"') || '"}
      ]}'
    ) AS summary
FROM my_table
LIMIT 10;
        """, language="sql")
        
        st.markdown("### 服务管理命令")
        st.code("""
-- 查看服务状态
SELECT SYSTEM$GET_SERVICE_STATUS('SPCS_CHINA.MODEL_SERVICE.QWEN_MODEL_SERVICE');

-- 暂停服务 (节省成本)
ALTER SERVICE SPCS_CHINA.MODEL_SERVICE.QWEN_MODEL_SERVICE SUSPEND;

-- 恢复服务
ALTER SERVICE SPCS_CHINA.MODEL_SERVICE.QWEN_MODEL_SERVICE RESUME;

-- 查看服务日志
SELECT SYSTEM$GET_SERVICE_LOGS('SPCS_CHINA.MODEL_SERVICE.QWEN_MODEL_SERVICE', 0, 'qwen-service', 50);
        """, language="sql")
        
        st.markdown("### 自定义 SQL 执行")
        custom_sql = st.text_area(
            "输入 SQL",
            value=f"SELECT {QWEN_UDF_PATH}('{{\"model\":\"Qwen/Qwen2.5-1.5B-Instruct\",\"messages\":[{{\"role\":\"user\",\"content\":\"你好\"}}]}}')",
            height=100,
            key="custom_sql"
        )
        
        if st.button("▶️ 执行 SQL"):
            with st.spinner("执行中..."):
                try:
                    result = session.sql(custom_sql).collect()
                    st.success("执行成功!")
                    st.write(result)
                except Exception as e:
                    st.error(f"执行失败: {e}")


# ===============================
# 入口
# ===============================
if __name__ == "__main__":
    main()
