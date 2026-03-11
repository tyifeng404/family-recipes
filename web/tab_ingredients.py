"""
web/tab_ingredients.py —— Tab 3：可用食材管理 + 菜谱推荐
"""

from datetime import date

import streamlit as st

import storage


def render_ingredients_tab(recipes: dict, ingredients_data: list):
    """渲染可用食材 Tab 的全部内容。"""
    st.subheader("🥬 可用食材管理")

    _render_add_form(ingredients_data)

    st.divider()
    _render_ingredient_list(ingredients_data)

    st.divider()
    _render_recommendations(recipes, ingredients_data)


# ────────────────────────────────────────────
#  添加食材
# ────────────────────────────────────────────


def _render_add_form(ingredients_data: list):
    with st.container(border=True):
        st.markdown("**➕ 添加新食材**")
        col_name, col_date, col_btn = st.columns([2, 2, 1])
        with col_name:
            new_ing_name = st.text_input(
                "食材名称", key="new_ing_name", placeholder="例如：番茄"
            )
        with col_date:
            new_ing_date = st.date_input(
                "购买日期", value=date.today(), key="new_ing_date"
            )
        with col_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            add_clicked = st.button(
                "添加",
                type="primary",
                use_container_width=True,
                key="add_ing_btn",
            )

        if add_clicked:
            ing_name = new_ing_name.strip()
            if not ing_name:
                st.error("请输入食材名称！")
            else:
                existing_names = {ing["name"] for ing in ingredients_data}
                if ing_name in existing_names:
                    st.warning(f"「{ing_name}」已在可用食材清单中。")
                else:
                    ingredients_data.append(
                        {"name": ing_name, "date": new_ing_date.isoformat()}
                    )
                    storage.save_ingredients(ingredients_data)
                    storage.ingredients = ingredients_data
                    st.session_state.save_msg = f"已添加食材「{ing_name}」！"
                    if "new_ing_name" in st.session_state:
                        del st.session_state["new_ing_name"]
                    st.rerun()


# ────────────────────────────────────────────
#  当前食材清单
# ────────────────────────────────────────────


def _render_ingredient_list(ingredients_data: list):
    st.markdown("**📦 当前可用食材清单**")

    if not ingredients_data:
        st.info("暂无可用食材，请在上方添加。")
        return

    for idx, ing in enumerate(ingredients_data):
        col_info, col_del = st.columns([5, 1])
        with col_info:
            st.markdown(
                f"🏷️ **{ing['name']}** &nbsp;&nbsp; "
                f"<span style='color:gray;font-size:0.85em;'>"
                f"购买于 {ing['date']}</span>",
                unsafe_allow_html=True,
            )
        with col_del:
            if st.button("🗑️", key=f"del_ing_{idx}"):
                ingredients_data.pop(idx)
                storage.save_ingredients(ingredients_data)
                storage.ingredients = ingredients_data
                st.rerun()


# ────────────────────────────────────────────
#  菜谱推荐
# ────────────────────────────────────────────

_TAG_OK = (
    '<span style="display:inline-block;background:#c8e6c9;'
    'color:#2e7d32;padding:3px 10px;border-radius:12px;'
    'font-size:0.85em;margin:2px;">✓ {}</span>'
)
_TAG_MISS = (
    '<span style="display:inline-block;background:#ffcdd2;'
    'color:#c62828;padding:3px 10px;border-radius:12px;'
    'font-size:0.85em;margin:2px;">✗ {}</span>'
)


def _render_recommendations(recipes: dict, ingredients_data: list):
    st.markdown("**🍳 菜谱推荐**")
    st.caption("根据当前可用食材，为您推荐可以制作的菜谱")

    if not ingredients_data:
        st.info("请先添加可用食材，才能获得菜谱推荐。")
        return

    avail_names = {ing["name"] for ing in ingredients_data}
    full_matches = []
    partial_matches = []

    for r_name, r_data in recipes.items():
        r_ings = r_data.get("ingredients", [])
        if not r_ings:
            continue
        matched = [ig for ig in r_ings if ig in avail_names]
        missing = [ig for ig in r_ings if ig not in avail_names]
        if not missing:
            full_matches.append((r_name, r_data, matched, missing))
        elif matched:
            partial_matches.append((r_name, r_data, matched, missing))

    # 完全匹配
    if full_matches:
        st.success(f"🎉 有 {len(full_matches)} 道菜谱的食材已全部齐备！")
        for r_name, r_data, matched, _ in full_matches:
            _render_full_match(r_name, r_data, matched)
    else:
        st.info("暂无食材完全齐备的菜谱。")

    # 部分匹配
    if partial_matches:
        st.markdown("---")
        st.markdown(f"**差一点就能做的菜（{len(partial_matches)} 道）：**")
        for r_name, r_data, matched, missing in partial_matches:
            _render_partial_match(r_name, r_data, matched, missing)


def _start_cooking(r_name: str, key: str):
    """「开始做菜」popover 的通用渲染。"""
    if st.button("确认开始", key=key, type="primary"):
        st.session_state.start_cooking_recipe = r_name
        st.session_state.save_msg = (
            f"已为您预选「{r_name}」，"
            f"请点击「📝 做菜记录」标签页开始记录！"
        )
        st.rerun()


def _render_full_match(r_name, r_data, matched):
    with st.container(border=True):
        st.markdown(f"### ✅ {r_name}")
        tags = " ".join(_TAG_OK.format(n) for n in matched)
        st.markdown(
            f"食材齐全（{len(matched)}/{len(matched)}）：&nbsp;{tags}",
            unsafe_allow_html=True,
        )
        with st.expander("查看做法"):
            for step in r_data["steps"]:
                st.markdown(f"&emsp;{step}")
        with st.popover("🍳 开始做菜"):
            st.markdown(f"确认开始「{r_name}」的做菜记录？")
            _start_cooking(r_name, f"confirm_cook_{r_name}")


def _render_partial_match(r_name, r_data, matched, missing):
    with st.container(border=True):
        total = len(matched) + len(missing)
        st.markdown(f"### 📖 {r_name}")
        tags = " ".join(_TAG_OK.format(n) for n in matched)
        tags += " " + " ".join(_TAG_MISS.format(n) for n in missing)
        st.markdown(
            f"食材匹配（{len(matched)}/{total}）：&nbsp;{tags}",
            unsafe_allow_html=True,
        )
        with st.popover("🍳 开始做菜"):
            st.markdown(
                f"「{r_name}」还缺少食材：**{'、'.join(missing)}**\n\n"
                f"仍然要开始做菜记录吗？"
            )
            _start_cooking(r_name, f"confirm_cook_partial_{r_name}")
