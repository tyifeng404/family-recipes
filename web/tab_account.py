"""
web/tab_account.py —— 账号管理（个人资料 / 管理员审核）
"""

import streamlit as st

import storage


def render_account_tab(current_user: str, is_admin: bool):
    st.subheader("👤 账号管理")
    accounts = storage.ensure_admin_account()

    if is_admin:
        _render_admin_pending(accounts, current_user)
        st.divider()
        _render_admin_editor(accounts, current_user)
        st.divider()

    _render_self_editor(accounts, current_user)


def _render_admin_pending(accounts: list, actor: str):
    st.markdown("**🛂 待审核账号**")
    pending = [a for a in accounts if a.get("status") == "pending"]
    if not pending:
        st.caption("当前没有待审核账号。")
        return

    for account in pending:
        with st.container(border=True):
            st.markdown(
                f"**{account['username']}** · {account.get('real_name', '')} · {account.get('phone', '')}"
            )
            col_ok, col_reject = st.columns(2)
            with col_ok:
                if st.button(
                    "通过",
                    key=f"approve_{account['username']}",
                    type="primary",
                    use_container_width=True,
                ):
                    ok, msg = storage.set_account_status(
                        username=account["username"], approved=True, actor_username=actor
                    )
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            with col_reject:
                if st.button(
                    "拒绝",
                    key=f"reject_{account['username']}",
                    use_container_width=True,
                ):
                    ok, msg = storage.set_account_status(
                        username=account["username"], approved=False, actor_username=actor
                    )
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)


def _render_admin_editor(accounts: list, actor: str):
    st.markdown("**🧾 账号信息管理（管理员）**")
    usernames = [a["username"] for a in accounts]
    target = st.selectbox("选择账号", usernames, key="admin_edit_user")
    account = storage.find_account(accounts, target)
    if not account:
        st.warning("账号不存在。")
        return

    username_input = st.text_input(
        "账户名称",
        value=account.get("username", ""),
        key="admin_edit_username",
    )
    real_name = st.text_input(
        "真实姓名",
        value=account.get("real_name", ""),
        key="admin_edit_real_name",
    )
    phone = st.text_input("手机号", value=account.get("phone", ""), key="admin_edit_phone")
    password = st.text_input(
        "重置密码（留空不改）", type="password", key="admin_edit_password"
    )

    shares = account.get("share_settings") or {}
    col1, col2, col3 = st.columns(3)
    with col1:
        share_recipes = st.checkbox(
            "共享菜谱", value=bool(shares.get("recipes", False)), key="admin_share_recipes"
        )
    with col2:
        share_records = st.checkbox(
            "共享记录", value=bool(shares.get("records", False)), key="admin_share_records"
        )
    with col3:
        share_ingredients = st.checkbox(
            "共享食材",
            value=bool(shares.get("ingredients", False)),
            key="admin_share_ingredients",
        )

    if st.button("保存账号信息", type="primary", key="admin_save_user"):
        ok, msg = storage.update_account_profile(
            actor_username=actor,
            target_username=target,
            new_username=username_input,
            real_name=real_name,
            phone=phone,
            password=password,
            share_settings={
                "recipes": share_recipes,
                "records": share_records,
                "ingredients": share_ingredients,
            },
        )
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)


def _render_self_editor(accounts: list, current_user: str):
    st.markdown("**🙋 我的资料**")
    account = storage.find_account(accounts, current_user)
    if not account:
        st.warning("当前账号信息缺失，请联系管理员。")
        return

    username_input = st.text_input(
        "账户名称",
        value=account["username"],
        key="self_username",
    )
    real_name = st.text_input("真实姓名", value=account.get("real_name", ""), key="self_real_name")
    phone = st.text_input("手机号", value=account.get("phone", ""), key="self_phone")
    password = st.text_input("修改密码（留空不改）", type="password", key="self_password")

    shares = account.get("share_settings") or {}
    col1, col2, col3 = st.columns(3)
    with col1:
        share_recipes = st.checkbox(
            "共享菜谱",
            value=bool(shares.get("recipes", False)),
            key="self_share_recipes",
        )
    with col2:
        share_records = st.checkbox(
            "共享记录",
            value=bool(shares.get("records", False)),
            key="self_share_records",
        )
    with col3:
        share_ingredients = st.checkbox(
            "共享食材",
            value=bool(shares.get("ingredients", False)),
            key="self_share_ingredients",
        )

    if st.button("保存我的资料", type="primary", key="self_save_profile"):
        ok, msg = storage.update_account_profile(
            actor_username=current_user,
            target_username=current_user,
            new_username=username_input,
            real_name=real_name,
            phone=phone,
            password=password,
            share_settings={
                "recipes": share_recipes,
                "records": share_records,
                "ingredients": share_ingredients,
            },
        )
        if ok:
            st.session_state["auth_user"] = username_input.strip().lower()
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)
