"""
web/tab_recipe.py —— Tab 1：菜谱管理（搜索 / 浏览 / 添加 / 修改）
"""

import streamlit as st

import storage
from web.ui_helpers import (
    enter_edit,
    ingredient_tags_html,
    parse_ingredients,
    strip_number_prefix,
)


def render_recipe_tab(recipes: dict):
    """渲染菜谱管理 Tab 的全部内容。"""
    query = st.text_input(
        "🔍 搜索菜谱", placeholder="输入菜名关键字，如：番茄、排骨…"
    )

    if query:
        _show_search_results(recipes, query)
    else:
        _show_all_recipes(recipes)

    # ── 添加 / 修改表单 ──
    if st.session_state.show_form:
        _show_recipe_form(recipes)


def _show_search_results(recipes: dict, query: str):
    matches = [(n, d) for n, d in recipes.items() if query in n]
    if matches:
        st.success(f"找到 {len(matches)} 道相关菜谱")
        for name, data in matches:
            with st.container(border=True):
                st.subheader(f"📖 {name}")
                ings = data.get("ingredients", [])
                if ings:
                    st.markdown(
                        f"**主要食材：** {ingredient_tags_html(ings)}",
                        unsafe_allow_html=True,
                    )
                for step in data["steps"]:
                    st.markdown(f"&emsp;{step}")
                if st.button(f"✏️ 修改「{name}」", key=f"edit_{name}"):
                    enter_edit(name, data)
    else:
        st.warning(f"没有找到包含「{query}」的菜谱，可以在下方直接添加 👇")
        if not st.session_state.show_form:
            st.session_state.show_form = True
            st.session_state.form_name = query
            st.session_state.form_steps = ""
            st.session_state.form_ingredients = ""
            st.rerun()


def _show_all_recipes(recipes: dict):
    if recipes:
        st.subheader("📚 全部菜谱")
        for name, data in recipes.items():
            with st.expander(f"📖 {name}"):
                ings = data.get("ingredients", [])
                if ings:
                    st.markdown(
                        f"**主要食材：** {ingredient_tags_html(ings)}",
                        unsafe_allow_html=True,
                    )
                for step in data["steps"]:
                    st.markdown(f"&emsp;{step}")
                if st.button("✏️ 修改", key=f"edit_all_{name}"):
                    enter_edit(name, data)
    else:
        st.info("还没有任何菜谱，快来添加第一道吧！")
        st.session_state.show_form = True


def _show_recipe_form(recipes: dict):
    st.divider()
    is_editing = st.session_state.form_name in recipes
    st.subheader("✏️ 修改菜谱" if is_editing else "📝 添加新菜谱")

    name_input = st.text_input(
        "菜名", value=st.session_state.form_name, key="inp_name"
    )
    ingredients_input = st.text_input(
        "主要食材（用逗号或顿号分隔）",
        value=st.session_state.form_ingredients,
        key="inp_ingredients",
        placeholder="例如：番茄、鸡蛋、盐",
    )
    steps_input = st.text_area(
        "做法步骤（每行写一步，无需手动编号）",
        value=st.session_state.form_steps,
        height=250,
        key="inp_steps",
        placeholder="例如：\n鸡蛋打散，加少许盐搅匀\n番茄切块备用\n热锅凉油，炒蛋…",
    )

    col_save, col_cancel, _ = st.columns([1, 1, 4])
    with col_save:
        save_clicked = st.button(
            "保存", type="primary", use_container_width=True, key="save_recipe"
        )
    with col_cancel:
        cancel_clicked = st.button(
            "取消", use_container_width=True, key="cancel_recipe"
        )

    if save_clicked:
        final_name = name_input.strip()
        final_text = steps_input.strip()
        if not final_name or not final_text:
            st.error("请填写菜名和至少一个步骤！")
        else:
            lines = [l.strip() for l in final_text.split("\n") if l.strip()]
            numbered = [
                f"{i}. {strip_number_prefix(line)}"
                for i, line in enumerate(lines, 1)
            ]
            parsed_ings = parse_ingredients(ingredients_input)
            if is_editing and final_name != st.session_state.form_name:
                recipes.pop(st.session_state.form_name, None)
            recipes[final_name] = {
                "steps": numbered,
                "ingredients": parsed_ings,
            }
            storage.save_recipes(recipes)
            storage.recipes = recipes
            _reset_form()
            st.session_state.save_msg = f"「{final_name}」已保存成功！"
            st.rerun()

    if cancel_clicked:
        _reset_form()
        st.rerun()


def _reset_form():
    st.session_state.show_form = False
    st.session_state.form_name = ""
    st.session_state.form_steps = ""
    st.session_state.form_ingredients = ""
