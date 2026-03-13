"""
web/auth.py —— 登录与注册页面
"""

import streamlit as st

import storage


def ensure_auth_state():
    defaults = {
        "auth_user": "",
        "auth_real_name": "",
        "auth_is_admin": False,
        "auth_msg": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def is_logged_in() -> bool:
    return bool(st.session_state.get("auth_user"))


def current_user() -> str:
    return st.session_state.get("auth_user", "")


def current_user_is_admin() -> bool:
    return bool(st.session_state.get("auth_is_admin", False))


def logout():
    st.session_state["auth_user"] = ""
    st.session_state["auth_real_name"] = ""
    st.session_state["auth_is_admin"] = False
    st.session_state["auth_msg"] = "已退出登录。"


def render_auth_page():
    st.subheader("🔐 账号登录")
    if st.session_state.get("auth_msg"):
        st.info(st.session_state["auth_msg"])
        st.session_state["auth_msg"] = ""

    tab_login, tab_register = st.tabs(["登录", "注册"])
    with tab_login:
        _render_login_form()
    with tab_register:
        _render_register_form()


def _render_login_form():
    username = st.text_input("账户名称", key="login_username")
    password = st.text_input("密码", type="password", key="login_password")
    if st.button("登录", type="primary", key="btn_login", use_container_width=True):
        ok, msg, account = storage.authenticate(username.strip(), password)
        if not ok or not account:
            st.error(msg)
            return
        st.session_state["auth_user"] = account["username"]
        st.session_state["auth_real_name"] = account.get("real_name", "")
        st.session_state["auth_is_admin"] = bool(account.get("is_admin"))
        st.session_state["auth_msg"] = f"欢迎回来，{account['username']}！"
        st.rerun()


def _render_register_form():
    username = st.text_input("账户名称（唯一）", key="reg_username")
    password = st.text_input("密码", type="password", key="reg_password")
    real_name = st.text_input("真实姓名", key="reg_real_name")
    phone = st.text_input("手机号", key="reg_phone")
    if st.button("提交注册", key="btn_register", use_container_width=True):
        ok, msg = storage.register_account(
            username=username,
            password=password,
            real_name=real_name,
            phone=phone,
        )
        if ok:
            st.success(msg)
        else:
            st.error(msg)
