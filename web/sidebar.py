"""
web/sidebar.py —— 侧边栏：菜谱搜索 + 可用食材目录
"""

import streamlit as st

import storage


def render_sidebar(recipes: dict, ingredients_data: list, records: list):
    """渲染侧边栏内容。"""
    with st.sidebar:
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
                if q in name.lower() or any(q in ig.lower() for ig in ings):
                    sb_results.append((name, ings))
            if sb_results:
                for name, ings in sb_results:
                    st.markdown(f"📖 **{name}**")
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
