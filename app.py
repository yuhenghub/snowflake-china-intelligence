import os
import streamlit as st
from snowflake.connector import DatabaseError
from snowflake.connector.connection import SnowflakeConnection

# set_page_config must be run as the first Streamlit command on the page, before any other streamlit imports.
st.set_page_config(layout="wide", page_icon="💬", page_title="语义模型生成器")


# ============================================
# 默认配置
# ============================================
DEFAULT_QWEN_UDF_PATH = "SNOWFLAKE_PROD_USER1.CORTEX_ANALYST.QWEN_COMPLETE"
DEFAULT_SEMANTIC_STAGE_PATH = "@SNOWFLAKE_PROD_USER1.CORTEX_ANALYST.SEMANTIC_MODELS"


def get_qwen_udf_path() -> str:
    """获取 Qwen UDF 的完整路径"""
    return st.session_state.get("qwen_udf_path", DEFAULT_QWEN_UDF_PATH)


def get_semantic_stage_path() -> str:
    """获取语义模型存储的 Stage 路径"""
    return st.session_state.get("semantic_stage_path", DEFAULT_SEMANTIC_STAGE_PATH)


def render_config_sidebar():
    """渲染配置侧边栏"""
    with st.sidebar:
        st.markdown("---")
        with st.expander("⚙️ 高级配置", expanded=False):
            st.markdown("##### Qwen UDF 配置")
            
            # Initialize session state
            if "qwen_udf_path" not in st.session_state:
                st.session_state.qwen_udf_path = DEFAULT_QWEN_UDF_PATH
            if "semantic_stage_path" not in st.session_state:
                st.session_state.semantic_stage_path = DEFAULT_SEMANTIC_STAGE_PATH
            
            # UDF Path input
            udf_path = st.text_input(
                "Qwen UDF 路径",
                value=st.session_state.qwen_udf_path,
                help="格式: DATABASE.SCHEMA.FUNCTION_NAME",
                key="udf_path_input"
            )
            if udf_path != st.session_state.qwen_udf_path:
                st.session_state.qwen_udf_path = udf_path
            
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
            
            # Show current config
            st.markdown("---")
            st.caption("当前配置:")
            st.code(f"UDF: {st.session_state.qwen_udf_path}", language=None)
            st.code(f"Stage: {st.session_state.semantic_stage_path}", language=None)


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


@st.experimental_dialog(title="Connection Error")
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
                    <h1>欢迎使用 Snowflake 语义模型生成器! ❄️</h1>
                    <p>🚀 使用此工具创建、编辑和测试您的语义模型</p>
                    <p>💡 语义模型帮助 AI 理解您的数据结构，实现自然语言查询</p>
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
