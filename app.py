import os
import streamlit as st
from snowflake.connector import DatabaseError
from snowflake.connector.connection import SnowflakeConnection

# set_page_config must be run as the first Streamlit command on the page, before any other streamlit imports.
st.set_page_config(layout="wide", page_icon="💬", page_title="Semantic Model Generator V2")


# ============================================
# 默认配置
# ============================================
DEFAULT_QWEN_UDF_PATH = "SNOWFLAKE_PROD_USER1.CORTEX_ANALYST.QWEN_COMPLETE"
DEFAULT_SEMANTIC_STAGE_PATH = "@SNOWFLAKE_PROD_USER1.CORTEX_ANALYST.SEMANTIC_MODELS"

# ============================================
# 模型后端配置 (SPCS 或 外部 API)
# ============================================
MODEL_BACKENDS = {
    "SPCS (本地)": {
        "description": "Snowflake Container Services 本地部署模型，数据不出云",
        "icon": "🏠",
        "udf_path": "SPCS_CHINA.MODEL_SERVICE.QWEN_COMPLETE"
    },
    "外部 API": {
        "description": "调用外部 LLM API (DashScope/DeepSeek/Kimi 等)",
        "icon": "🌐",
        "udf_path": "SNOWFLAKE_PROD_USER1.CORTEX_ANALYST.QWEN_COMPLETE"
    }
}

DEFAULT_BACKEND = "外部 API"

# SPCS 模型列表
SPCS_MODELS = {
    "Qwen/Qwen2.5-1.5B-Instruct": "Qwen2.5-1.5B (SPCS 部署)",
}

# 外部 API 模型列表
EXTERNAL_MODELS = {
    "qwen-turbo": "Qwen Turbo (快速)",
    "qwen-plus": "Qwen Plus (平衡)",
    "qwen-max": "Qwen Max (高精度)",
}


def get_qwen_udf_path() -> str:
    """获取 Qwen UDF 的完整路径，根据选择的后端返回对应路径"""
    backend = st.session_state.get("model_backend", DEFAULT_BACKEND)
    if backend in MODEL_BACKENDS:
        return MODEL_BACKENDS[backend]["udf_path"]
    return st.session_state.get("qwen_udf_path", DEFAULT_QWEN_UDF_PATH)


def get_selected_model() -> str:
    """获取当前选择的模型"""
    return st.session_state.get("selected_model", "qwen-max")


def get_semantic_stage_path() -> str:
    """获取语义模型存储的 Stage 路径"""
    return st.session_state.get("semantic_stage_path", DEFAULT_SEMANTIC_STAGE_PATH)


def render_config_sidebar():
    """渲染配置侧边栏"""
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🧠 模型配置")
        
        # Initialize session state
        if "model_backend" not in st.session_state:
            st.session_state.model_backend = DEFAULT_BACKEND
        if "selected_model" not in st.session_state:
            st.session_state.selected_model = "qwen-max"
        if "qwen_udf_path" not in st.session_state:
            st.session_state.qwen_udf_path = DEFAULT_QWEN_UDF_PATH
        if "semantic_stage_path" not in st.session_state:
            st.session_state.semantic_stage_path = DEFAULT_SEMANTIC_STAGE_PATH
        
        # ===== 模型后端选择 (SPCS 或 外部 API) =====
        backend_list = list(MODEL_BACKENDS.keys())
        selected_backend = st.radio(
            "选择模型后端",
            options=backend_list,
            index=backend_list.index(st.session_state.model_backend) if st.session_state.model_backend in backend_list else 1,
            key="backend_selector",
            horizontal=True,
            help="SPCS: 本地部署，数据不出云 | 外部 API: 调用云端 LLM"
        )
        
        # 如果后端改变，更新 session state
        if selected_backend != st.session_state.model_backend:
            st.session_state.model_backend = selected_backend
            if selected_backend == "SPCS (本地)":
                st.session_state.selected_model = list(SPCS_MODELS.keys())[0]
            else:
                st.session_state.selected_model = "qwen-max"
        
        # 显示当前后端信息
        backend_info = MODEL_BACKENDS[selected_backend]
        st.caption(f"{backend_info['icon']} {backend_info['description']}")
        
        # ===== 根据后端显示不同的模型选择 =====
        if selected_backend == "SPCS (本地)":
            # SPCS 模型选择
            spcs_model_list = list(SPCS_MODELS.keys())
            current_model = st.session_state.selected_model
            if current_model not in spcs_model_list:
                current_model = spcs_model_list[0]
            
            selected_model = st.selectbox(
                "选择 SPCS 模型",
                options=spcs_model_list,
                index=spcs_model_list.index(current_model) if current_model in spcs_model_list else 0,
                format_func=lambda x: SPCS_MODELS[x],
                key="spcs_model_selector"
            )
            
            if selected_model != st.session_state.selected_model:
                st.session_state.selected_model = selected_model
            
            st.success(f"🏠 **SPCS** / `{selected_model.split('/')[-1]}`")
            st.info("💡 SPCS 模型运行在 Snowflake Container Services，数据永远不会离开 Snowflake。")
        
        else:
            # 外部 API 模型选择
            external_model_list = list(EXTERNAL_MODELS.keys())
            current_model = st.session_state.selected_model
            if current_model not in external_model_list:
                current_model = "qwen-max"
            
            selected_model = st.selectbox(
                "选择外部模型",
                options=external_model_list,
                index=external_model_list.index(current_model) if current_model in external_model_list else 2,
                format_func=lambda x: EXTERNAL_MODELS[x],
                key="external_model_selector"
            )
            
            if selected_model != st.session_state.selected_model:
                st.session_state.selected_model = selected_model
            
            st.success(f"🌐 **外部 API** / `{selected_model}`")
        
        # ===== 高级配置 =====
        with st.expander("⚙️ 高级配置", expanded=False):
            st.markdown("##### UDF 路径配置")
            
            # 显示当前使用的 UDF 路径
            current_udf_path = get_qwen_udf_path()
            st.code(f"当前 UDF: {current_udf_path}", language=None)
            
            # 自定义 UDF 路径 (可选)
            custom_udf = st.text_input(
                "自定义 UDF 路径 (可选)",
                value="",
                help="留空则使用默认路径。格式: DATABASE.SCHEMA.FUNCTION_NAME",
                key="custom_udf_input"
            )
            if custom_udf:
                st.session_state.qwen_udf_path = custom_udf
            
            st.markdown("##### 语义模型存储")
            
            # Stage Path input
            stage_path = st.text_input(
                "Stage 路径",
                value=st.session_state.semantic_stage_path,
                help="格式: @DATABASE.SCHEMA.STAGE_NAME",
                key="stage_path_input"
            )
            if stage_path != st.session_state.semantic_stage_path:
                st.session_state.semantic_stage_path = stage_path


def _detect_china_region() -> bool:
    """
    Detect if running in Snowflake China region.
    Returns True if China region is detected.
    """
    # Check if explicitly set
    if os.environ.get("USE_QWEN_FOR_CHINA", "").lower() == "true":
        return True
    
    # Check host name for China region indicators
    host = os.environ.get("SNOWFLAKE_HOST", "")
    if any(x in host.lower() for x in [".cn", "cn-", "china"]):
        return True
    
    # Check account locator for China region
    account = os.environ.get("SNOWFLAKE_ACCOUNT_LOCATOR", "")
    if any(x in account.lower() for x in ["cn-", ".cn"]):
        return True
    
    return False


# Auto-detect China region and set environment variable
if _detect_china_region():
    os.environ["USE_QWEN_FOR_CHINA"] = "true"
    # Also set default Qwen models
    if not os.environ.get("QWEN_MODEL"):
        os.environ["QWEN_MODEL"] = "qwen-turbo"
    if not os.environ.get("QWEN_SQL_MODEL"):
        os.environ["QWEN_SQL_MODEL"] = "qwen-max"
    if not os.environ.get("QWEN_JUDGE_MODEL"):
        os.environ["QWEN_JUDGE_MODEL"] = "qwen-max"

from app_utils.shared_utils import (  # noqa: E402
    GeneratorAppScreen,
    get_snowflake_connection,
    set_account_name,
    set_host_name,
    set_sit_query_tag,
    set_snowpark_session,
    set_streamlit_location,
    set_user_name,
)
from semantic_model_generator.snowflake_utils.env_vars import (  # noqa: E402
    SNOWFLAKE_ACCOUNT_LOCATOR,
    SNOWFLAKE_HOST,
    SNOWFLAKE_USER,
)


# 兼容性处理：旧版本 streamlit 不支持 experimental_dialog
def _compat_dialog(title="Dialog"):
    """兼容旧版本 streamlit 的 dialog 装饰器"""
    if hasattr(st, 'experimental_dialog'):
        return st.experimental_dialog(title=title)
    elif hasattr(st, 'dialog'):
        return st.dialog(title=title)
    else:
        def decorator(func):
            def wrapper(*args, **kwargs):
                with st.container():
                    st.error(f"⚠️ {title}")
                    return func(*args, **kwargs)
            return wrapper
        return decorator


@_compat_dialog(title="Connection Error")
def failed_connection_popup() -> None:
    """
    Renders a dialog box detailing that the credentials provided could not be used to connect to Snowflake.
    """
    st.markdown(
        """It looks like the credentials provided could not be used to connect to the account."""
    )
    st.stop()


def verify_environment_setup() -> SnowflakeConnection:
    """
    Ensures that the correct environment variables are set before proceeding.
    """

    # Instantiate the Snowflake connection that gets reused throughout the app.
    try:
        with st.spinner(
            "Validating your connection to Snowflake. If you are using MFA, please check your authenticator app for a push notification."
        ):
            return get_snowflake_connection()
    except DatabaseError:
        failed_connection_popup()


if __name__ == "__main__":
    from journeys import builder, iteration, partner

    st.session_state["sis"] = set_streamlit_location()

    def onboarding_dialog() -> None:
        """
        Renders the initial screen where users can choose to create a new semantic model or edit an existing one.
        """

        # Direct to specific page based instead of default onboarding if user comes from successful partner setup
        st.markdown(
            """
                <div style="text-align: center;">
                    <h1>Welcome to Semantic Model Generator V2! ❄️</h1>
                    <p>🚀 Create, edit and test your semantic models with this tool</p>
                    <p>💡 Semantic models help AI understand your data structure for natural language queries</p>
                    <p>🧠 <b>NEW:</b> Support SPCS (Local) and External API model backends</p>
                </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='margin: 60px;'></div>", unsafe_allow_html=True)

        _, center, _ = st.columns([1, 2, 1])
        with center:
            if st.button(
                "**🛠 创建新的语义模型**",
                use_container_width=True,
                type="primary",
            ):
                builder.show()
            st.markdown("")
            if st.button(
                "**✏️ 编辑现有语义模型**",
                use_container_width=True,
                type="primary",
            ):
                iteration.show()

    conn = verify_environment_setup()
    set_snowpark_session(conn)

    # Populating common state between builder and iteration apps.
    set_account_name(conn, SNOWFLAKE_ACCOUNT_LOCATOR)
    set_host_name(conn, SNOWFLAKE_HOST)
    set_user_name(conn, SNOWFLAKE_USER)

    # Render configuration sidebar
    render_config_sidebar()

    # When the app first loads, show the onboarding screen.
    if "page" not in st.session_state:
        st.session_state["page"] = GeneratorAppScreen.ONBOARDING

    # Depending on the page state, we either show the onboarding menu or the chat app flow.
    # The builder flow is simply an intermediate dialog before the iteration flow.
    if st.session_state["page"] == GeneratorAppScreen.ITERATION:
        iteration.show()
    else:
        onboarding_dialog()
