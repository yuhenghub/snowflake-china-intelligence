import streamlit as st


# 兼容性处理：旧版本 streamlit 不支持 experimental_dialog
def _compat_dialog(title="Dialog", width="small"):
    if hasattr(st, 'experimental_dialog'):
        return st.experimental_dialog(title, width=width)
    elif hasattr(st, 'dialog'):
        return st.dialog(title, width=width)
    else:
        def decorator(func):
            def wrapper(*args, **kwargs):
                with st.container():
                    st.subheader(f"📋 {title}")
                    return func(*args, **kwargs)
            return wrapper
        return decorator


@_compat_dialog("Partner Semantic Support", width="large")
def partner_semantic_setup() -> None:
    """
    Renders the partner semantic setup dialog with instructions.
    """
    from partner.partner_utils import configure_partner_semantic

    st.write(
        """
        Have an existing semantic layer in a partner tool that's integrated with Snowflake?
        See the below instructions for integrating your partner semantic specs into Cortex Analyst's semantic file.
        """
    )
    configure_partner_semantic()


def show() -> None:
    """
    Runs partner setup dialog.
    """
    partner_semantic_setup()
