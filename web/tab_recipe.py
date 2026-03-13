"""
web/tab_recipe.py —— Tab 1：菜谱管理（按菜系分组 / 搜索 / 添加 / 修改）
"""

from __future__ import annotations

import streamlit as st

import storage
from cuisine import (
    BASE_TAG_OPTIONS,
    CHINESE_CUISINE_OPTIONS,
    CUISINE_GROUP_OPTIONS,
    DEFAULT_CUISINE,
    DEFAULT_CUISINE_GROUP,
    DEFAULT_DIFFICULTY,
    DIFFICULTY_OPTIONS,
    FOREIGN_CUISINE_OPTIONS,
    infer_cuisine_group,
    normalize_cuisine,
    normalize_cuisine_group,
    normalize_difficulty,
    normalize_tags,
)
from web.ui_helpers import (
    enter_edit,
    ingredient_tags_html,
    parse_ingredients,
    strip_number_prefix,
)


def render_recipe_tab(
    recipes: dict,
    visible_recipes: dict,
    current_user: str,
    is_admin_user: bool,
):
    """渲染菜谱管理 Tab 的全部内容。"""
    col_q, col_group, col_cuisine = st.columns([3, 1.5, 1.5])
    with col_q:
        query = st.text_input(
            "🔍 搜索菜谱",
            placeholder="支持菜名 / 食材 / 菜系 / 标签 / 难度",
            key="recipe_search_query",
        ).strip()
    with col_group:
        group_filter = st.selectbox(
            "大类",
            _build_group_filter_options(visible_recipes),
            key="recipe_group_filter",
        )
    with col_cuisine:
        cuisine_filter = st.selectbox(
            "细分类",
            _build_cuisine_filter_options(visible_recipes, group_filter),
            key="recipe_cuisine_filter",
        )

    filtered = _filter_recipes(visible_recipes, query, group_filter, cuisine_filter)

    if query or group_filter != "全部大类" or cuisine_filter != "全部细分类":
        _show_search_results(filtered, query, current_user, is_admin_user)
    else:
        _show_all_recipes_grouped(filtered, current_user, is_admin_user)

    if st.session_state.show_form:
        _show_recipe_form(recipes, current_user, is_admin_user)


def _build_group_filter_options(recipes: dict) -> list[str]:
    groups = {
        normalize_cuisine_group(data.get("cuisine_group") or infer_cuisine_group(data.get("cuisine")))
        for data in recipes.values()
        if isinstance(data, dict)
    }
    return ["全部大类"] + sorted(groups)


def _build_cuisine_filter_options(recipes: dict, group_filter: str) -> list[str]:
    cuisines: set[str] = set()
    for data in recipes.values():
        if not isinstance(data, dict):
            continue
        group = normalize_cuisine_group(data.get("cuisine_group") or infer_cuisine_group(data.get("cuisine")))
        if group_filter != "全部大类" and group != group_filter:
            continue
        cuisines.add(normalize_cuisine(data.get("cuisine")))
    return ["全部细分类"] + sorted(cuisines)


def _filter_recipes(recipes: dict, query: str, group_filter: str, cuisine_filter: str) -> dict:
    result: dict = {}
    q = query.lower()

    for name, data in recipes.items():
        if not isinstance(data, dict):
            continue

        cuisine = normalize_cuisine(data.get("cuisine"))
        cuisine_group = normalize_cuisine_group(data.get("cuisine_group") or infer_cuisine_group(cuisine))
        difficulty = normalize_difficulty(data.get("difficulty"))
        tags = normalize_tags(data.get("tags", []))

        if group_filter != "全部大类" and cuisine_group != group_filter:
            continue
        if cuisine_filter != "全部细分类" and cuisine != cuisine_filter:
            continue

        if q:
            ingredients = [str(x).lower() for x in data.get("ingredients", [])]
            text_parts = [
                name.lower(),
                cuisine_group.lower(),
                cuisine.lower(),
                difficulty.lower(),
            ] + ingredients + [t.lower() for t in tags]
            if not any(q in part for part in text_parts):
                continue

        result[name] = data

    return result


def _can_edit_recipe(data: dict, current_user: str, is_admin_user: bool) -> bool:
    owner = data.get("owner", "admin")
    return is_admin_user or owner == current_user


def _tags_text(tags: list[str]) -> str:
    if not tags:
        return "（无）"
    return " ".join([f"`{t}`" for t in tags])


def _show_meta(data: dict, current_user: str):
    group = normalize_cuisine_group(data.get("cuisine_group") or infer_cuisine_group(data.get("cuisine")))
    cuisine = normalize_cuisine(data.get("cuisine"))
    difficulty = normalize_difficulty(data.get("difficulty"))
    tags = normalize_tags(data.get("tags", []))
    owner = data.get("owner", "admin")

    st.caption(f"分类：{group} / {cuisine} · 难度：{difficulty}")
    st.markdown(f"**标签：** {_tags_text(tags)}")
    if owner != current_user:
        st.caption(f"来源账号：{owner}")


def _show_search_results(recipes: dict, query: str, current_user: str, is_admin_user: bool):
    if recipes:
        st.success(f"找到 {len(recipes)} 道匹配菜谱")
        for name, data in recipes.items():
            with st.container(border=True):
                st.subheader(f"📖 {name}")
                _show_meta(data, current_user)
                _render_recipe_detail(name, data, current_user, is_admin_user)
        return

    st.warning("当前筛选条件没有匹配的菜谱，可以在下方直接新增 👇")
    if not st.session_state.show_form:
        st.session_state.show_form = True
        st.session_state.form_name = query if query else ""
        st.session_state.form_steps = ""
        st.session_state.form_ingredients = ""
        st.rerun()


def _show_all_recipes_grouped(recipes: dict, current_user: str, is_admin_user: bool):
    if not recipes:
        st.info("还没有任何菜谱，快来添加第一道吧！")
        st.session_state.show_form = True
        return

    st.subheader("📚 全部菜谱（按分类）")
    groups: dict[str, dict[str, list[tuple[str, dict]]]] = {}

    for name, data in recipes.items():
        cuisine = normalize_cuisine(data.get("cuisine"))
        group = normalize_cuisine_group(data.get("cuisine_group") or infer_cuisine_group(cuisine))
        groups.setdefault(group, {}).setdefault(cuisine, []).append((name, data))

    for group in sorted(groups.keys()):
        st.markdown(f"### {group}")
        for cuisine in sorted(groups[group].keys()):
            st.markdown(f"**{cuisine}**")
            for name, data in groups[group][cuisine]:
                with st.expander(f"📖 {name}"):
                    _show_meta(data, current_user)
                    _render_recipe_detail(name, data, current_user, is_admin_user)


def _render_recipe_detail(name: str, data: dict, current_user: str, is_admin_user: bool):
    ingredients = data.get("ingredients", [])
    if ingredients:
        st.markdown(
            f"**主要食材：** {ingredient_tags_html(ingredients)}",
            unsafe_allow_html=True,
        )
    for step in data.get("steps", []):
        st.markdown(f"&emsp;{step}")

    if _can_edit_recipe(data, current_user, is_admin_user):
        if st.button(f"✏️ 修改「{name}」", key=f"edit_{name}"):
            enter_edit(name, data)
    else:
        st.caption("仅创建者或管理员可编辑")


def _resolve_cuisine(group_selected: str, cuisine_selected: str, custom_cuisine: str) -> tuple[str, str]:
    group = normalize_cuisine_group(group_selected)
    if group == DEFAULT_CUISINE_GROUP:
        return DEFAULT_CUISINE_GROUP, DEFAULT_CUISINE

    custom = custom_cuisine.strip()
    if custom:
        return group, custom

    if group == "外国菜":
        cuisine = cuisine_selected if cuisine_selected in FOREIGN_CUISINE_OPTIONS else FOREIGN_CUISINE_OPTIONS[0]
        return group, cuisine

    if group == "中餐":
        cuisine = cuisine_selected if cuisine_selected in CHINESE_CUISINE_OPTIONS else CHINESE_CUISINE_OPTIONS[0]
        return group, cuisine

    return group, DEFAULT_CUISINE


def _build_final_tags(
    spice_choice: str,
    child_friendly: bool,
    selected_extra_tags: list[str],
    custom_tags_text: str,
) -> list[str]:
    tags: list[str] = []

    if spice_choice in ["辣", "不辣"]:
        tags.append(spice_choice)

    if child_friendly:
        tags.append("适合儿童")

    for tag in selected_extra_tags:
        t = str(tag).strip()
        if t and t not in BASE_TAG_OPTIONS:
            tags.append(t)

    if custom_tags_text.strip():
        separators = [",", "，", "、", ";", "；"]
        normalized = custom_tags_text
        for sep in separators[1:]:
            normalized = normalized.replace(sep, separators[0])
        for tag in normalized.split(separators[0]):
            t = tag.strip()
            if t:
                tags.append(t)

    return normalize_tags(tags)


def _show_recipe_form(recipes: dict, current_user: str, is_admin_user: bool):
    st.divider()
    is_editing = st.session_state.form_name in recipes
    old_data = recipes.get(st.session_state.form_name, {})
    old_owner = old_data.get("owner", "admin")

    if is_editing and not (is_admin_user or old_owner == current_user):
        st.error("你没有权限编辑这道菜谱。")
        _reset_form()
        return

    old_group = normalize_cuisine_group(old_data.get("cuisine_group") or infer_cuisine_group(old_data.get("cuisine")))
    old_cuisine = normalize_cuisine(old_data.get("cuisine"))
    old_difficulty = normalize_difficulty(old_data.get("difficulty"))
    old_tags = normalize_tags(old_data.get("tags", []))

    st.subheader("✏️ 修改菜谱" if is_editing else "📝 添加新菜谱")

    name_input = st.text_input("菜名", value=st.session_state.form_name, key="inp_name")

    group_idx = CUISINE_GROUP_OPTIONS.index(old_group) if old_group in CUISINE_GROUP_OPTIONS else 0
    group_selected = st.selectbox(
        "菜系大类",
        CUISINE_GROUP_OPTIONS,
        index=group_idx if is_editing else 0,
        key="inp_cuisine_group",
    )

    cuisine_options = []
    if group_selected == "外国菜":
        cuisine_options = FOREIGN_CUISINE_OPTIONS
    elif group_selected == "中餐":
        cuisine_options = CHINESE_CUISINE_OPTIONS

    if cuisine_options:
        cuisine_idx = cuisine_options.index(old_cuisine) if old_cuisine in cuisine_options else 0
        cuisine_selected = st.selectbox(
            "细分菜系",
            cuisine_options,
            index=cuisine_idx,
            key="inp_cuisine",
        )
    else:
        cuisine_selected = DEFAULT_CUISINE

    custom_cuisine = st.text_input(
        "自定义细分菜系（可选）",
        value="" if not is_editing else ("" if old_cuisine in cuisine_options or old_group == DEFAULT_CUISINE_GROUP else old_cuisine),
        key="inp_custom_cuisine",
        placeholder="例如：意大利菜 / 家庭快手菜",
    )

    difficulty_idx = DIFFICULTY_OPTIONS.index(old_difficulty) if old_difficulty in DIFFICULTY_OPTIONS else 0
    difficulty_selected = st.selectbox(
        "难易程度",
        DIFFICULTY_OPTIONS,
        index=difficulty_idx,
        key="inp_difficulty",
    )

    # 标签
    default_spice = "未设置"
    if "辣" in old_tags:
        default_spice = "辣"
    elif "不辣" in old_tags:
        default_spice = "不辣"

    spice_choice = st.radio(
        "辣度标签",
        ["未设置", "辣", "不辣"],
        index=["未设置", "辣", "不辣"].index(default_spice),
        horizontal=True,
        key="inp_spice_tag",
    )
    child_friendly = st.checkbox(
        "适合儿童",
        value=("适合儿童" in old_tags),
        key="inp_child_tag",
    )

    all_tags = storage.get_all_recipe_tags(recipes)
    extra_tag_options = [t for t in all_tags if t not in BASE_TAG_OPTIONS]
    default_extra_tags = [t for t in old_tags if t not in BASE_TAG_OPTIONS]
    selected_extra_tags = st.multiselect(
        "其他标签（可多选）",
        options=extra_tag_options,
        default=[t for t in default_extra_tags if t in extra_tag_options],
        key="inp_extra_tags",
    )
    custom_tags_text = st.text_input(
        "新增标签（可选，多个用逗号/顿号分隔）",
        key="inp_custom_tags",
        placeholder="例如：下饭、节日、15分钟",
    )

    ingredients_input = st.text_input(
        "主要食材（用逗号或顿号分隔）",
        value=st.session_state.form_ingredients,
        key="inp_ingredients",
        placeholder="例如：番茄、鸡蛋",
    )

    steps_input = st.text_area(
        "制作要点（每行写一条，建议 3~5 条）",
        value=st.session_state.form_steps,
        height=240,
        key="inp_steps",
        placeholder="例如：\n食材切配大小一致\n先炒主料再合炒\n出锅前尝味调整",
    )

    col_save, col_cancel, _ = st.columns([1, 1, 4])
    with col_save:
        save_clicked = st.button("保存", type="primary", use_container_width=True, key="save_recipe")
    with col_cancel:
        cancel_clicked = st.button("取消", use_container_width=True, key="cancel_recipe")

    if save_clicked:
        final_name = name_input.strip()
        final_text = steps_input.strip()
        if not final_name or not final_text:
            st.error("请填写菜名和至少一条制作要点！")
        else:
            lines = [line.strip() for line in final_text.split("\n") if line.strip()]
            if len(lines) < 3 or len(lines) > 5:
                st.error("制作要点请控制在 3~5 条。")
                return

            numbered = [f"{i}. {strip_number_prefix(line)}" for i, line in enumerate(lines, 1)]
            parsed_ings = parse_ingredients(ingredients_input)
            final_group, final_cuisine = _resolve_cuisine(group_selected, cuisine_selected, custom_cuisine)
            final_tags = _build_final_tags(
                spice_choice=spice_choice,
                child_friendly=child_friendly,
                selected_extra_tags=selected_extra_tags,
                custom_tags_text=custom_tags_text,
            )

            if is_editing and final_name != st.session_state.form_name:
                recipes.pop(st.session_state.form_name, None)

            owner = old_owner if is_editing else current_user
            recipes[final_name] = {
                "steps": numbered,
                "ingredients": parsed_ings,
                "cuisine_group": final_group,
                "cuisine": final_cuisine,
                "tags": final_tags,
                "difficulty": difficulty_selected,
                "owner": owner,
                "is_builtin": False,
                "builtin_version": "",
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
    for key in [
        "inp_name",
        "inp_cuisine_group",
        "inp_cuisine",
        "inp_custom_cuisine",
        "inp_difficulty",
        "inp_spice_tag",
        "inp_child_tag",
        "inp_extra_tags",
        "inp_custom_tags",
        "inp_ingredients",
        "inp_steps",
    ]:
        if key in st.session_state:
            del st.session_state[key]
