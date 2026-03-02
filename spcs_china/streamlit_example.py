"""
SPCS China - Streamlit 示例应用
支持多模型管理 (Qwen & DeepSeek) 和服务控制

部署方式:
1. 在 Snowflake UI 中创建 Streamlit 应用
2. 复制此文件内容到 Streamlit 编辑器
3. 确保 SPCS 服务已启动并运行

前置条件:
- SPCS 服务已部署 (QWEN_MODEL_SERVICE 和/或 DEEPSEEK_MODEL_SERVICE)
- 对应的 UDF 已创建
- 当前用户有执行该 UDF 的权限
"""

import streamlit as st
import json
from snowflake.snowpark.context import get_active_session

# ===============================
# 配置
# ===============================
# 模型配置
MODELS = {
    "Qwen": {
        "udf_path": "SPCS_CHINA.MODEL_SERVICE.QWEN_COMPLETE",
        "service_name": "SPCS_CHINA.MODEL_SERVICE.QWEN_MODEL_SERVICE",
        "container_name": "qwen-service",
        "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
        "description": "阿里通义千问 2.5 (1.5B) - 中英文通用",
        "icon": "🤖"
    },
    "DeepSeek": {
        "udf_path": "SPCS_CHINA.MODEL_SERVICE.DEEPSEEK_COMPLETE",
        "service_name": "SPCS_CHINA.MODEL_SERVICE.DEEPSEEK_MODEL_SERVICE",
        "container_name": "deepseek-service",
        "model_id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
        "description": "DeepSeek-R1 蒸馏版 (1.5B) - 支持推理链",
        "icon": "🧠"
    }
}


# ===============================
# 辅助函数
# ===============================
def safe_rerun():
    """兼容不同版本的 Streamlit rerun"""
    if hasattr(st, 'rerun'):
        safe_rerun()
    elif hasattr(st, 'experimental_rerun'):
        st.experimental_rerun()
    else:
        st.warning("请手动刷新页面以查看更新")

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
        return
    try:
        result = session.sql("SHOW WAREHOUSES").collect()
        if result and len(result) > 0:
            wh_name = result[0]["name"]
            session.sql(f"USE WAREHOUSE {wh_name}").collect()
    except Exception:
        pass


def call_llm(session, model_key: str, prompt: str, system_prompt: str = None,
             max_tokens: int = 2048, temperature: float = 0.7) -> str:
    """
    调用 LLM UDF
    
    Args:
        session: Snowpark session
        model_key: 模型标识 ("Qwen" 或 "DeepSeek")
        prompt: 用户输入
        system_prompt: 系统提示词 (可选)
        max_tokens: 最大输出 token 数
        temperature: 温度参数
    
    Returns:
        模型生成的响应文本
    """
    model_config = MODELS.get(model_key, MODELS["Qwen"])
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": model_config["model_id"],
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    payload_str = json.dumps(payload, ensure_ascii=False)
    payload_escaped = payload_str.replace("'", "''")
    
    ensure_warehouse(session)
    
    udf_path = model_config["udf_path"]
    query = f"SELECT {udf_path}('{payload_escaped}')"
    
    try:
        result = session.sql(query).collect()
        if result and len(result) > 0:
            response = result[0][0]
            if response and "</think>" in response:
                parts = response.split("</think>")
                if len(parts) > 1:
                    return parts[-1].strip()
            return response
        return "没有收到响应"
    except Exception as e:
        return f"错误: {str(e)}"


def get_service_status(session, service_name: str) -> dict:
    """获取 SPCS 服务状态"""
    try:
        query = f"SELECT SYSTEM$GET_SERVICE_STATUS('{service_name}')"
        result = session.sql(query).collect()
        if result and result[0][0]:
            return json.loads(result[0][0])
        return [{"status": "UNKNOWN"}]
    except Exception as e:
        return [{"status": "ERROR", "error": str(e)}]


def get_all_services_status(session) -> dict:
    """获取所有服务状态"""
    statuses = {}
    for model_key, config in MODELS.items():
        statuses[model_key] = get_service_status(session, config["service_name"])
    return statuses


def suspend_service(session, service_name: str) -> str:
    """暂停 SPCS 服务"""
    try:
        query = f"ALTER SERVICE {service_name} SUSPEND"
        session.sql(query).collect()
        return "✅ 服务已暂停"
    except Exception as e:
        return f"❌ 暂停失败: {str(e)}"


def resume_service(session, service_name: str) -> str:
    """恢复 SPCS 服务"""
    try:
        query = f"ALTER SERVICE {service_name} RESUME"
        session.sql(query).collect()
        return "✅ 服务已恢复，请等待 1-2 分钟启动完成"
    except Exception as e:
        return f"❌ 恢复失败: {str(e)}"


def get_service_logs(session, service_name: str, container_name: str, lines: int = 50) -> str:
    """获取服务日志"""
    try:
        query = f"SELECT SYSTEM$GET_SERVICE_LOGS('{service_name}', 0, '{container_name}', {lines})"
        result = session.sql(query).collect()
        if result and result[0][0]:
            return result[0][0]
        return "无日志"
    except Exception as e:
        return f"获取日志失败: {str(e)}"


def render_status_badge(status: str):
    """渲染状态徽章"""
    if status == "READY":
        st.success(f"🟢 {status}")
    elif status == "SUSPENDED":
        st.warning(f"🟡 {status}")
    elif status in ["PENDING", "STARTING"]:
        st.info(f"🔵 {status}")
    elif status == "ERROR":
        st.error(f"🔴 {status}")
    else:
        st.info(f"⚪ {status}")


# ===============================
# Streamlit 应用
# ===============================
def main():
    st.set_page_config(
        page_title="🤖 SPCS LLM Assistant",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 SPCS LLM Assistant")
    st.caption("基于 SPCS 部署的大语言模型服务 (中国区)")
    
    try:
        session = get_active_session()
    except Exception as e:
        st.error(f"❌ 无法获取 Snowflake session: {e}")
        st.info("请确保此应用运行在 Streamlit in Snowflake 环境中")
        return
    
    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 配置")
        
        # 模型选择
        selected_model = st.selectbox(
            "选择模型",
            list(MODELS.keys()),
            format_func=lambda x: f"{MODELS[x]['icon']} {x}"
        )
        
        model_config = MODELS[selected_model]
        st.caption(model_config["description"])
        
        st.divider()
        
        # 参数设置
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
        # 服务管理面板
        # ===============================
        st.header("🎛️ 服务管理")
        
        # 刷新状态按钮
        if st.button("🔄 刷新所有状态", use_container_width=True):
            st.session_state.services_status = get_all_services_status(session)
            safe_rerun()
        
        # 显示操作结果消息
        if "action_message" in st.session_state and st.session_state.action_message:
            st.success(st.session_state.action_message)
            st.session_state.action_message = None
        
        # 初始化状态
        if "services_status" not in st.session_state:
            st.session_state.services_status = get_all_services_status(session)
        
        # 显示每个服务的状态和控制
        for model_key, config in MODELS.items():
            with st.expander(f"{config['icon']} {model_key}", expanded=(model_key == selected_model)):
                status_list = st.session_state.services_status.get(model_key, [])
                
                if isinstance(status_list, list) and len(status_list) > 0:
                    status = status_list[0].get("status", "UNKNOWN")
                    message = status_list[0].get("message", "")
                    
                    render_status_badge(status)
                    
                    if message and status not in ["READY", "SUSPENDED"]:
                        st.caption(f"📝 {message[:50]}...")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("▶️ 启动", key=f"resume_{model_key}", 
                                    disabled=(status == "READY"),
                                    use_container_width=True):
                            with st.spinner("启动中..."):
                                result = resume_service(session, config["service_name"])
                                st.session_state.action_message = result
                                st.session_state.services_status = get_all_services_status(session)
                                safe_rerun()
                    
                    with col2:
                        if st.button("⏸️ 暂停", key=f"suspend_{model_key}",
                                    disabled=(status == "SUSPENDED"),
                                    use_container_width=True):
                            with st.spinner("暂停中..."):
                                result = suspend_service(session, config["service_name"])
                                st.session_state.action_message = result
                                st.session_state.services_status = get_all_services_status(session)
                                safe_rerun()
                else:
                    st.info("服务未部署或无法访问")
        
        st.caption("💡 暂停服务可节省 GPU 计算成本")
    
    # 主界面
    tab1, tab2, tab3, tab4 = st.tabs(["💬 对话", "📝 批量处理", "🔧 SQL 示例", "📊 服务监控"])
    
    # Tab 1: 对话界面
    with tab1:
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        st.markdown("### 对话历史")
        chat_container = st.container()
        
        with chat_container:
            for message in st.session_state.messages:
                icon = "🧑" if message["role"] == "user" else model_config["icon"]
                role = "用户" if message["role"] == "user" else selected_model
                st.markdown(f"**{icon} {role}:** {message['content']}")
                st.markdown("---")
        
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
                safe_rerun()
        
        if send_button and user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            with st.spinner(f"🤔 {selected_model} 思考中..."):
                response = call_llm(
                    session=session,
                    model_key=selected_model,
                    prompt=user_input,
                    system_prompt=system_prompt if system_prompt else None,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            safe_rerun()
    
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
                    response = call_llm(session, selected_model, full_prompt)
                    results.append({
                        "输入": line,
                        "输出": response
                    })
                    progress_bar.progress((i + 1) / len(lines))
                
                status_text.text("✅ 处理完成!")
                st.success(f"处理完成，共 {len(results)} 条")
                
                for r in results:
                    with st.expander(f"📄 {r['输入'][:50]}..."):
                        st.write("**输入:**", r['输入'])
                        st.write("**输出:**", r['输出'])
            else:
                st.warning("请输入要处理的文本")
    
    # Tab 3: SQL 示例
    with tab3:
        st.subheader("SQL 调用示例")
        
        st.markdown("### Qwen 模型调用")
        st.code("""
-- 简单问答
SELECT SPCS_CHINA.MODEL_SERVICE.QWEN_COMPLETE(
  '{"model":"Qwen/Qwen2.5-1.5B-Instruct","messages":[{"role":"user","content":"什么是 Snowflake?"}]}'
);

-- 带系统提示词
SELECT SPCS_CHINA.MODEL_SERVICE.QWEN_COMPLETE(
  '{"model":"Qwen/Qwen2.5-1.5B-Instruct","messages":[
    {"role":"system","content":"你是一个数据分析专家，请简洁回答"},
    {"role":"user","content":"如何优化 SQL 查询?"}
  ]}'
);
        """, language="sql")
        
        st.markdown("### DeepSeek 模型调用")
        st.code("""
-- DeepSeek-R1 问答 (带推理链)
SELECT SPCS_CHINA.MODEL_SERVICE.DEEPSEEK_COMPLETE(
  '{"model":"deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B","messages":[{"role":"user","content":"解释什么是机器学习"}]}'
);

-- 代码生成
SELECT SPCS_CHINA.MODEL_SERVICE.DEEPSEEK_COMPLETE(
  '{"model":"deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B","messages":[
    {"role":"system","content":"你是一个编程专家"},
    {"role":"user","content":"用 Python 实现快速排序"}
  ]}'
);
        """, language="sql")
        
        st.markdown("### 服务管理命令")
        st.code("""
-- 查看 Qwen 服务状态
SELECT SYSTEM$GET_SERVICE_STATUS('SPCS_CHINA.MODEL_SERVICE.QWEN_MODEL_SERVICE');

-- 查看 DeepSeek 服务状态
SELECT SYSTEM$GET_SERVICE_STATUS('SPCS_CHINA.MODEL_SERVICE.DEEPSEEK_MODEL_SERVICE');

-- 暂停服务 (节省成本)
ALTER SERVICE SPCS_CHINA.MODEL_SERVICE.QWEN_MODEL_SERVICE SUSPEND;
ALTER SERVICE SPCS_CHINA.MODEL_SERVICE.DEEPSEEK_MODEL_SERVICE SUSPEND;

-- 恢复服务
ALTER SERVICE SPCS_CHINA.MODEL_SERVICE.QWEN_MODEL_SERVICE RESUME;
ALTER SERVICE SPCS_CHINA.MODEL_SERVICE.DEEPSEEK_MODEL_SERVICE RESUME;

-- 查看服务日志
SELECT SYSTEM$GET_SERVICE_LOGS('SPCS_CHINA.MODEL_SERVICE.QWEN_MODEL_SERVICE', 0, 'qwen-service', 50);
SELECT SYSTEM$GET_SERVICE_LOGS('SPCS_CHINA.MODEL_SERVICE.DEEPSEEK_MODEL_SERVICE', 0, 'deepseek-service', 50);
        """, language="sql")
        
        st.markdown("### 自定义 SQL 执行")
        udf_path = model_config["udf_path"]
        custom_sql = st.text_area(
            "输入 SQL",
            value=f"SELECT {udf_path}('{{\"model\":\"{model_config['model_id']}\",\"messages\":[{{\"role\":\"user\",\"content\":\"你好\"}}]}}')",
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
    
    # Tab 4: 服务监控
    with tab4:
        st.subheader("📊 服务监控")
        
        col1, col2 = st.columns(2)
        
        for idx, (model_key, config) in enumerate(MODELS.items()):
            with (col1 if idx % 2 == 0 else col2):
                st.markdown(f"### {config['icon']} {model_key}")
                
                status_list = st.session_state.services_status.get(model_key, [])
                
                if isinstance(status_list, list) and len(status_list) > 0:
                    instance = status_list[0]
                    status = instance.get("status", "UNKNOWN")
                    
                    render_status_badge(status)
                    
                    st.markdown(f"**服务:** `{config['service_name']}`")
                    st.markdown(f"**模型:** `{config['model_id']}`")
                    
                    if instance.get("message"):
                        st.markdown(f"**消息:** {instance['message']}")
                    if instance.get("startTime"):
                        st.markdown(f"**启动时间:** {instance['startTime']}")
                    if instance.get("restartCount", 0) > 0:
                        st.markdown(f"**重启次数:** {instance['restartCount']}")
                    
                    if st.button(f"📜 查看日志", key=f"logs_{model_key}"):
                        with st.spinner("获取日志..."):
                            logs = get_service_logs(
                                session, 
                                config["service_name"], 
                                config["container_name"]
                            )
                            st.code(logs, language="text")
                else:
                    st.info("服务未部署或无法访问")
                
                st.divider()


# ===============================
# 入口
# ===============================
if __name__ == "__main__":
    main()
