"""web/account_dialog.py —— 侧边栏触发的账号管理弹窗（个人资料）"""

import streamlit as st

import storage


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

    st.caption("可在此快速修改当前登录账号信息。")

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
                st.session_state.save_msg = msg
                st.rerun()
            else:
                st.error(msg)

    with col_cancel:
        if st.button("关闭", use_container_width=True, key="dlg_close_profile"):
            st.session_state["open_account_dialog"] = False
            st.rerun()
