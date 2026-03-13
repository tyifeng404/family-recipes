"""web/account_dialog.py —— 侧边栏触发的账号管理弹窗（含管理员审核）"""

import streamlit as st

import storage


def _render_admin_pending(accounts: list, actor: str):
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
                    key=f"dlg_approve_{account['username']}",
                    type="primary",
                    use_container_width=True,
                ):
                    ok, msg = storage.set_account_status(
                        username=account["username"], approved=True, actor_username=actor
                    )
                    if ok:
                        st.session_state["save_msg"] = msg
                        st.rerun()
                    else:
                        st.error(msg)
            with col_reject:
                if st.button(
                    "拒绝",
                    key=f"dlg_reject_{account['username']}",
                    use_container_width=True,
                ):
                    ok, msg = storage.set_account_status(
                        username=account["username"], approved=False, actor_username=actor
                    )
                    if ok:
                        st.session_state["save_msg"] = msg
                        st.rerun()
                    else:
                        st.error(msg)


def _render_admin_editor(accounts: list, actor: str, current_user: str):
    usernames = [a["username"] for a in accounts]
    if not usernames:
        st.caption("暂无可管理账号。")
        return

    target = st.selectbox("选择账号", usernames, key="dlg_admin_target_user")
    account = storage.find_account(accounts, target)
    if not account:
        st.warning("账号不存在。")
        return

    key_suffix = target.replace(" ", "_")
    username_input = st.text_input(
        "账户名称",
        value=account.get("username", ""),
        key=f"dlg_admin_username_{key_suffix}",
    )
    real_name = st.text_input(
        "真实姓名",
        value=account.get("real_name", ""),
        key=f"dlg_admin_real_name_{key_suffix}",
    )
    phone = st.text_input(
        "手机号",
        value=account.get("phone", ""),
        key=f"dlg_admin_phone_{key_suffix}",
    )
    password = st.text_input(
        "重置密码（留空不改）",
        type="password",
        key=f"dlg_admin_password_{key_suffix}",
    )

    shares = account.get("share_settings") or {}
    col1, col2, col3 = st.columns(3)
    with col1:
        share_recipes = st.checkbox(
            "共享菜谱",
            value=bool(shares.get("recipes", False)),
            key=f"dlg_admin_share_recipes_{key_suffix}",
        )
    with col2:
        share_records = st.checkbox(
            "共享记录",
            value=bool(shares.get("records", False)),
            key=f"dlg_admin_share_records_{key_suffix}",
        )
    with col3:
        share_ingredients = st.checkbox(
            "共享食材",
            value=bool(shares.get("ingredients", False)),
            key=f"dlg_admin_share_ingredients_{key_suffix}",
        )

    if st.button("保存账号信息", type="primary", key=f"dlg_admin_save_{key_suffix}"):
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
            if target == current_user:
                st.session_state["auth_user"] = username_input.strip().lower()
            st.session_state["save_msg"] = msg
            st.rerun()
        else:
            st.error(msg)


@st.dialog("👤 账号管理")
def render_account_dialog(current_user: str):
    accounts = storage.ensure_admin_account()
    account = storage.find_account(accounts, current_user)
    if not account:
        st.error("当前账号信息缺失，请联系管理员。")
        if st.button("关闭", key="dlg_close_missing", use_container_width=True):
            st.session_state["open_account_dialog"] = False
            st.rerun()
        return

    is_admin = bool(account.get("is_admin"))
    if is_admin:
        with st.expander("🛂 待审核账号（管理员）", expanded=True):
            _render_admin_pending(accounts, current_user)
        with st.expander("🧾 账号信息管理（管理员）", expanded=False):
            _render_admin_editor(accounts, current_user, current_user)
        st.divider()

    st.caption("我的资料")

    username_input = st.text_input(
        "账户名称",
        value=account.get("username", ""),
        key="dlg_username",
    )
    real_name = st.text_input(
        "真实姓名",
        value=account.get("real_name", ""),
        key="dlg_real_name",
    )
    phone = st.text_input(
        "手机号",
        value=account.get("phone", ""),
        key="dlg_phone",
    )
    password = st.text_input(
        "修改密码（留空不改）",
        type="password",
        key="dlg_password",
    )

    shares = account.get("share_settings") or {}
    col1, col2, col3 = st.columns(3)
    with col1:
        share_recipes = st.checkbox(
            "共享菜谱",
            value=bool(shares.get("recipes", False)),
            key="dlg_share_recipes",
        )
    with col2:
        share_records = st.checkbox(
            "共享记录",
            value=bool(shares.get("records", False)),
            key="dlg_share_records",
        )
    with col3:
        share_ingredients = st.checkbox(
            "共享食材",
            value=bool(shares.get("ingredients", False)),
            key="dlg_share_ingredients",
        )

    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button(
            "保存资料",
            type="primary",
            use_container_width=True,
            key="dlg_save_profile",
        ):
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
                st.session_state["open_account_dialog"] = False
                st.session_state["save_msg"] = msg
                st.rerun()
            else:
                st.error(msg)

    with col_cancel:
        if st.button("关闭", use_container_width=True, key="dlg_close_profile"):
            st.session_state["open_account_dialog"] = False
            st.rerun()
