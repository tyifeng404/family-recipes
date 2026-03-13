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
        "saved_login_username": "",
        "saved_login_password": "",
        "remember_login_enabled": False,
        "auto_login_enabled": False,
        "auto_login_attempted": False,
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
    # 手动退出后，本次会话不再自动登录，避免“刚退出就回登”。
    st.session_state["auto_login_attempted"] = True


def render_auth_page():
    _try_auto_login()
    if is_logged_in():
        return

    st.subheader("🔐 账号登录")
    if st.session_state.get("auth_msg"):
        st.info(st.session_state["auth_msg"])
        st.session_state["auth_msg"] = ""

    tab_login, tab_register = st.tabs(["登录", "注册"])
    with tab_login:
        _render_login_form()
    with tab_register:
        _render_register_form()


def _try_auto_login():
    if not st.session_state.get("auto_login_enabled", False):
        return
    if st.session_state.get("auto_login_attempted", False):
        return

    username = st.session_state.get("saved_login_username", "").strip()
    password = st.session_state.get("saved_login_password", "")
    if not username or not password:
        return

    st.session_state["auto_login_attempted"] = True
    ok, msg, account = storage.authenticate(username, password)
    if not ok or not account:
        st.session_state["auth_msg"] = f"自动登录失败：{msg}"
        return

    st.session_state["auth_user"] = account["username"]
    st.session_state["auth_real_name"] = account.get("real_name", "")
    st.session_state["auth_is_admin"] = bool(account.get("is_admin"))
    st.session_state["auth_msg"] = f"已自动登录：{account['username']}"
    st.rerun()


def _render_login_form():
    username = st.text_input(
        "账户名称",
        value=st.session_state.get("saved_login_username", ""),
        key="login_username",
    )
    password = st.text_input(
        "密码",
        type="password",
        value=st.session_state.get("saved_login_password", ""),
        key="login_password",
    )
    remember_enabled = st.checkbox(
        "保存登录名和密码",
        value=bool(st.session_state.get("remember_login_enabled", False)),
        key="login_remember_enabled",
    )
    auto_default = (
        bool(st.session_state.get("auto_login_enabled", False))
        if remember_enabled
        else False
    )
    auto_login_enabled = st.checkbox(
        "自动登录",
        value=auto_default,
        key="login_auto_enabled",
        disabled=not remember_enabled,
    )

    if st.button("登录", type="primary", key="btn_login", use_container_width=True):
        ok, msg, account = storage.authenticate(username.strip(), password)
        if not ok or not account:
            st.error(msg)
            return
        st.session_state["auth_user"] = account["username"]
        st.session_state["auth_real_name"] = account.get("real_name", "")
        st.session_state["auth_is_admin"] = bool(account.get("is_admin"))
        st.session_state["auth_msg"] = f"欢迎回来，{account['username']}！"
        st.session_state["auto_login_attempted"] = False

        if remember_enabled:
            st.session_state["saved_login_username"] = username.strip().lower()
            st.session_state["saved_login_password"] = password
            st.session_state["remember_login_enabled"] = True
            st.session_state["auto_login_enabled"] = bool(auto_login_enabled)
        else:
            st.session_state["saved_login_username"] = ""
            st.session_state["saved_login_password"] = ""
            st.session_state["remember_login_enabled"] = False
            st.session_state["auto_login_enabled"] = False

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
