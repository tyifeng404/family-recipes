"""
web/sidebar.py —— 侧边栏：菜谱搜索 + 可用食材目录
"""

import streamlit as st

import storage
from cuisine import infer_cuisine_group
from web.auth import logout


def render_sidebar(
    recipes: dict,
    ingredients_data: list,
    records: list,
    current_user: str,
    is_admin: bool,
):
    """渲染侧边栏内容。"""
    with st.sidebar:
        st.markdown(f"**当前账号：** `{current_user}`")
        st.caption("角色：管理员" if is_admin else "角色：普通用户")
        col_account, col_logout = st.columns(2)
        with col_account:
            if st.button("账号管理", key="btn_open_account_dialog", use_container_width=True):
                st.session_state["open_account_dialog"] = True
                st.rerun()
        with col_logout:
            if st.button("退出登录", key="btn_logout", use_container_width=True):
                logout()
                st.rerun()
        st.divider()

        # ── 菜谱搜索 ──
        st.header("🔍 菜谱搜索")
        sidebar_query = st.text_input(
            "搜索菜谱",
            placeholder="输入菜名或食材关键词…",
            key="sidebar_search",
            label_visibility="collapsed",
        )
        if sidebar_query:
            q = sidebar_query.strip().lower()
            sb_results = []
            for name, data in recipes.items():
                ings = data.get("ingredients", [])
                all_ings = data.get("all_ingredients", [])
                cuisine = str(data.get("cuisine", "家常特色")).strip()
                cuisine_group = str(
                    data.get("cuisine_group") or infer_cuisine_group(cuisine)
                ).strip()
                difficulty = str(data.get("difficulty", "简单")).strip()
                tags = [str(t).strip() for t in data.get("tags", []) if str(t).strip()]
                if (
                    q in name.lower()
                    or any(q in ig.lower() for ig in ings)
                    or any(q in ig.lower() for ig in all_ings)
                    or q in cuisine.lower()
                    or q in cuisine_group.lower()
                    or q in difficulty.lower()
                    or any(q in t.lower() for t in tags)
                ):
                    sb_results.append((name, cuisine_group, cuisine, difficulty, tags, ings))
            if sb_results:
                for name, cuisine_group, cuisine, difficulty, tags, ings in sb_results:
                    st.markdown(f"📖 **{name}**")
                    st.caption(f"分类：{cuisine_group} / {cuisine} · 难度：{difficulty}")
                    if tags:
                        st.caption(f"标签：{'、'.join(tags)}")
                    if ings:
                        st.caption(f"食材：{'、'.join(ings)}")
                st.caption(f"找到 {len(sb_results)} 道菜谱")
            else:
                st.caption("未找到匹配的菜谱")
        else:
            st.caption(f"共收录 {len(recipes)} 道菜谱")

        st.divider()

        # ── 可用食材目录 ──
        st.header("🥬 可用食材")
        if ingredients_data:
            for ing in ingredients_data:
                st.markdown(
                    f"🏷️ **{ing['name']}** &nbsp; "
                    f"<span style='color:gray;font-size:0.8em;'>{ing['date']}</span>",
                    unsafe_allow_html=True,
                )
        else:
            st.caption("暂无可用食材")

        st.divider()
        st.caption(
            f"{len(recipes)} 道菜谱 · {len(records)} 条记录 · "
            f"{len(ingredients_data)} 种食材"
        )
        st.caption(f"存储后端：`{storage.backend_name()}`")
        diag = storage.backend_diagnostic()
        if storage.backend_name() == "local" and "当前使用本地存储" not in diag and diag:
            st.caption(f"后端诊断：{diag}")
