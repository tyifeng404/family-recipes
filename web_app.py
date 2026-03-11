"""
web_app.py —— 基于 Streamlit 的家庭菜谱 Web 界面

运行方式: streamlit run web_app.py
"""

import os
import re
from datetime import datetime, date

import streamlit as st

import storage
from config import BASE_DIR, PHOTOS_DIR, PHOTO_EXTS

# ───────── 页面配置 ─────────

st.set_page_config(page_title="家庭专属私房菜谱", page_icon="🍳", layout="centered")

st.markdown(
    """
    <style>
    [data-testid="stBaseButton-primary"] {
        background-color: #2e7d32 !important;
        border-color: #2e7d32 !important;
        color: white !important;
    }
    [data-testid="stBaseButton-primary"]:hover {
        background-color: #1b5e20 !important;
        border-color: #1b5e20 !important;
    }
    [data-testid="stBaseButton-primary"]:active {
        background-color: #1b5e20 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ───────── 大标题 ─────────

st.markdown(
    "<h1 style='text-align:center;'>🍳 家庭专属私房菜谱</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center; color:gray;'>记录家的味道，传承美食记忆</p>",
    unsafe_allow_html=True,
)
st.divider()

# ───────── Session State ─────────

_defaults = {
    "show_form": False,
    "form_name": "",
    "form_steps": "",
    "form_ingredients": "",
    "save_msg": "",
    "editing_record_idx": -1,
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ───────── 加载数据（每次 rerun 都从文件读最新） ─────────

recipes = storage.load_recipes()
records = storage.load_records()
ingredients_data = storage.load_ingredients()

# ───────── 保存成功提示 ─────────

if st.session_state.save_msg:
    st.success(st.session_state.save_msg)
    st.balloons()
    st.session_state.save_msg = ""

# ───────── 侧边栏 ─────────

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
        for _name, _data in recipes.items():
            _ings = _data.get("ingredients", [])
            if q in _name.lower() or any(q in ig.lower() for ig in _ings):
                sb_results.append((_name, _ings))
        if sb_results:
            for _name, _ings in sb_results:
                st.markdown(f"📖 **{_name}**")
                if _ings:
                    st.caption(f"食材：{'、'.join(_ings)}")
            st.caption(f"找到 {len(sb_results)} 道菜谱")
        else:
            st.caption("未找到匹配的菜谱")
    else:
        st.caption(f"共收录 {len(recipes)} 道菜谱")

    st.divider()

    # ── 可用食材目录 ──
    st.header("🥬 可用食材")
    if ingredients_data:
        for _ing in ingredients_data:
            st.markdown(
                f"🏷️ **{_ing['name']}** &nbsp; "
                f"<span style='color:gray;font-size:0.8em;'>{_ing['date']}</span>",
                unsafe_allow_html=True,
            )
    else:
        st.caption("暂无可用食材")

    st.divider()
    st.caption(
        f"{len(recipes)} 道菜谱 · {len(records)} 条记录 · "
        f"{len(ingredients_data)} 种食材"
    )


# ───────── 工具函数 ─────────


def _strip_number_prefix(step: str) -> str:
    """去掉 '1. ' 这类序号前缀，返回纯步骤内容。"""
    dot = step.find(". ")
    if dot != -1 and step[:dot].strip().isdigit():
        return step[dot + 2 :]
    return step


def _enter_edit(name: str, recipe_data: dict):
    """进入菜谱编辑模式。"""
    st.session_state.show_form = True
    st.session_state.form_name = name
    st.session_state.form_steps = "\n".join(
        _strip_number_prefix(s) for s in recipe_data["steps"]
    )
    st.session_state.form_ingredients = "、".join(
        recipe_data.get("ingredients", [])
    )
    st.rerun()


def _parse_ingredients(text: str) -> list[str]:
    """将逗号/顿号/空格分隔的食材文本解析为列表。"""
    parts = re.split(r"[,，、\s]+", text.strip())
    return [p for p in parts if p]


def _ingredient_tags_html(ingredients: list[str]) -> str:
    """将食材列表渲染为彩色标签 HTML。"""
    return " ".join(
        f'<span style="display:inline-block;background:#e8f5e9;color:#2e7d32;'
        f'padding:3px 10px;border-radius:12px;font-size:0.85em;margin:2px 3px;">'
        f'{name}</span>'
        for name in ingredients
    )


# ═══════════════════════════════════════════
#  三个主 Tab
# ═══════════════════════════════════════════

tab_recipe, tab_record, tab_ingredients = st.tabs(
    ["🍳 菜谱管理", "📝 做菜记录", "🥬 可用食材"]
)

# ═══════════ Tab 1：菜谱管理 ═══════════

with tab_recipe:
    query = st.text_input(
        "🔍 搜索菜谱", placeholder="输入菜名关键字，如：番茄、排骨…"
    )

    if query:
        matches = [(n, d) for n, d in recipes.items() if query in n]
        if matches:
            st.success(f"找到 {len(matches)} 道相关菜谱")
            for name, data in matches:
                with st.container(border=True):
                    st.subheader(f"📖 {name}")
                    ings = data.get("ingredients", [])
                    if ings:
                        st.markdown(
                            f"**主要食材：** {_ingredient_tags_html(ings)}",
                            unsafe_allow_html=True,
                        )
                    for step in data["steps"]:
                        st.markdown(f"&emsp;{step}")
                    if st.button(f"✏️ 修改「{name}」", key=f"edit_{name}"):
                        _enter_edit(name, data)
        else:
            st.warning(f"没有找到包含「{query}」的菜谱，可以在下方直接添加 👇")
            if not st.session_state.show_form:
                st.session_state.show_form = True
                st.session_state.form_name = query
                st.session_state.form_steps = ""
                st.session_state.form_ingredients = ""
                st.rerun()
    else:
        if recipes:
            st.subheader("📚 全部菜谱")
            for name, data in recipes.items():
                with st.expander(f"📖 {name}"):
                    ings = data.get("ingredients", [])
                    if ings:
                        st.markdown(
                            f"**主要食材：** {_ingredient_tags_html(ings)}",
                            unsafe_allow_html=True,
                        )
                    for step in data["steps"]:
                        st.markdown(f"&emsp;{step}")
                    if st.button("✏️ 修改", key=f"edit_all_{name}"):
                        _enter_edit(name, data)
        else:
            st.info("还没有任何菜谱，快来添加第一道吧！")
            st.session_state.show_form = True

    # ── 添加 / 修改表单 ──

    if st.session_state.show_form:
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
                    f"{i}. {_strip_number_prefix(line)}"
                    for i, line in enumerate(lines, 1)
                ]
                parsed_ings = _parse_ingredients(ingredients_input)
                if is_editing and final_name != st.session_state.form_name:
                    recipes.pop(st.session_state.form_name, None)
                recipes[final_name] = {
                    "steps": numbered,
                    "ingredients": parsed_ings,
                }
                storage.save_recipes(recipes)
                storage.recipes = recipes
                st.session_state.show_form = False
                st.session_state.form_name = ""
                st.session_state.form_steps = ""
                st.session_state.form_ingredients = ""
                st.session_state.save_msg = f"「{final_name}」已保存成功！"
                st.rerun()

        if cancel_clicked:
            st.session_state.show_form = False
            st.session_state.form_name = ""
            st.session_state.form_steps = ""
            st.session_state.form_ingredients = ""
            st.rerun()

# ═══════════ Tab 2：做菜记录 ═══════════

with tab_record:
    # 检查是否从推荐菜谱跳转过来
    start_recipe = st.session_state.pop("start_cooking_recipe", None)
    if start_recipe:
        st.session_state["rec_mode_radio"] = "➕ 新建记录"

    rec_mode = st.radio(
        "操作",
        ["📋 历史记录", "➕ 新建记录"],
        horizontal=True,
        label_visibility="collapsed",
        key="rec_mode_radio",
    )
    st.divider()

    # ────────── 新建记录 ──────────

    if rec_mode == "➕ 新建记录":
        st.subheader("📝 新建做菜记录")

        if not recipes:
            st.warning("请先在「菜谱管理」中添加菜谱，再来创建记录")
        else:
            recipe_names = list(recipes.keys())
            if start_recipe and start_recipe in recipe_names:
                st.session_state["new_rec_select"] = start_recipe
            selected = st.selectbox("选择菜谱", recipe_names, key="new_rec_select")

            if selected:
                recipe_data = recipes[selected]
                steps = recipe_data["steps"]
                recipe_ings = recipe_data.get("ingredients", [])

                if recipe_ings:
                    st.markdown(
                        f"**主要食材：** {_ingredient_tags_html(recipe_ings)}",
                        unsafe_allow_html=True,
                    )

                st.markdown("**为每一步添加备注（可选，留空跳过）：**")
                step_notes = []
                for i, step in enumerate(steps):
                    st.markdown(f"&emsp;{step}")
                    note = st.text_input(
                        f"第 {i+1} 步备注",
                        key=f"new_rec_note_{i}",
                        placeholder="可选",
                        label_visibility="collapsed",
                    )
                    step_notes.append(note)

                overall = st.text_area(
                    "整体备注", placeholder="可选", key="new_rec_overall"
                )

                st.markdown("**📷 添加照片（可选）**")
                camera_photo = st.camera_input(
                    "拍一张照片", key="new_rec_camera"
                )
                uploaded = st.file_uploader(
                    "或从相册选择（支持多张）",
                    accept_multiple_files=True,
                    type=[e.lstrip(".") for e in PHOTO_EXTS],
                    key="new_rec_photos",
                )
                has_photos = bool(camera_photo) or bool(uploaded)

                # 食材消耗检查：有照片时显示
                matching_ings: list[str] = []
                if recipe_ings and ingredients_data and has_photos:
                    avail_names = {ing["name"] for ing in ingredients_data}
                    matching_ings = [n for n in recipe_ings if n in avail_names]

                if matching_ings:
                    st.divider()
                    st.markdown("**🥬 以下主要食材是否已基本用完？**")
                    for ing_name in matching_ings:
                        st.checkbox(
                            f"{ing_name}",
                            key=f"new_rec_used_{ing_name}",
                        )

                if st.button("保存记录", type="primary", key="save_new_record"):
                    record_id = datetime.now().strftime("%Y%m%d_%H%M%S")

                    photo_paths: list[str] = []
                    all_photo_items: list[tuple[str, bytes]] = []
                    if camera_photo:
                        all_photo_items.append(
                            ("camera.jpg", camera_photo.getvalue())
                        )
                    if uploaded:
                        for file in uploaded:
                            all_photo_items.append(
                                (file.name, file.getvalue())
                            )
                    if all_photo_items:
                        dest_dir = os.path.join(PHOTOS_DIR, record_id)
                        os.makedirs(dest_dir, exist_ok=True)
                        for j, (fname, fdata) in enumerate(all_photo_items, 1):
                            ext = os.path.splitext(fname)[1].lower() or ".jpg"
                            dest_name = f"{j}{ext}"
                            with open(
                                os.path.join(dest_dir, dest_name), "wb"
                            ) as f:
                                f.write(fdata)
                            photo_paths.append(
                                os.path.join("photos", record_id, dest_name)
                            )

                    record = {
                        "id": record_id,
                        "name": selected,
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "steps": [
                            {"text": step, "note": note.strip()}
                            for step, note in zip(steps, step_notes)
                        ],
                        "note": overall.strip(),
                        "photos": photo_paths,
                    }
                    records.append(record)
                    storage.save_records(records)
                    storage.records = records

                    # 处理食材消耗（仅在有照片时检查）
                    used_up = []
                    if photo_paths and matching_ings:
                        used_up = [
                            name
                            for name in matching_ings
                            if st.session_state.get(f"new_rec_used_{name}", False)
                        ]
                        if used_up:
                            updated_ings = [
                                ing
                                for ing in ingredients_data
                                if ing["name"] not in set(used_up)
                            ]
                            storage.save_ingredients(updated_ings)
                            storage.ingredients = updated_ings

                    for k in list(st.session_state):
                        if k.startswith("new_rec_"):
                            del st.session_state[k]

                    used_msg = (
                        f"，已清除 {len(used_up)} 种用完的食材" if used_up else ""
                    )
                    st.session_state.save_msg = (
                        f"「{selected}」的做菜记录已保存！"
                        f"（含 {len(photo_paths)} 张照片{used_msg}）"
                    )
                    st.rerun()

    # ────────── 历史记录 ──────────

    else:
        st.subheader("📋 历史做菜记录")

        if not records:
            st.info("暂无做菜记录，快去做一道菜并记录吧！")
        else:
            for i, rec in enumerate(records):
                notes_count = sum(1 for s in rec["steps"] if s["note"])
                photos_count = len(rec.get("photos", []))
                label_parts = [f"[{rec['date']}] {rec['name']}"]
                detail = []
                if notes_count:
                    detail.append(f"{notes_count} 条备注")
                if photos_count:
                    detail.append(f"{photos_count} 张照片")
                if detail:
                    label_parts.append(f"（{'，'.join(detail)}）")
                label = "".join(label_parts)

                with st.expander(label):
                    for s in rec["steps"]:
                        st.markdown(f"&emsp;{s['text']}")
                        if s["note"]:
                            st.markdown(f"&emsp;&emsp;💬 _{s['note']}_")

                    if rec.get("note"):
                        st.markdown(f"**整体备注：** {rec['note']}")
                    else:
                        st.caption("整体备注：（无）")

                    photos = rec.get("photos", [])
                    if photos:
                        st.markdown(f"**📷 照片（{len(photos)} 张）：**")
                        n_cols = min(len(photos), 3)
                        cols = st.columns(n_cols)
                        for j, p in enumerate(photos):
                            full_path = os.path.join(BASE_DIR, p)
                            col = cols[j % n_cols]
                            if os.path.isfile(full_path):
                                col.image(full_path, caption=os.path.basename(p))
                            else:
                                col.warning(f"文件缺失: {os.path.basename(p)}")

                    col_edit, col_del, _ = st.columns([1, 1, 4])
                    with col_edit:
                        if st.button("✏️ 编辑备注", key=f"edit_rec_{i}"):
                            st.session_state.editing_record_idx = i
                            st.rerun()
                    with col_del:
                        with st.popover("🗑️ 删除"):
                            st.warning("确认删除此记录？删除后不可恢复。")
                            if st.button("确认删除", key=f"confirm_del_{i}"):
                                for p in rec.get("photos", []):
                                    fp = os.path.join(BASE_DIR, p)
                                    if os.path.isfile(fp):
                                        os.remove(fp)
                                rid = rec.get("id")
                                if rid:
                                    pd = os.path.join(PHOTOS_DIR, rid)
                                    if os.path.isdir(pd) and not os.listdir(pd):
                                        os.rmdir(pd)
                                records.pop(i)
                                storage.save_records(records)
                                storage.records = records
                                st.session_state.save_msg = "记录已删除"
                                st.rerun()

            # ── 编辑记录备注表单 ──

            edit_idx = st.session_state.editing_record_idx
            if 0 <= edit_idx < len(records):
                rec = records[edit_idx]
                st.divider()
                st.subheader(f"✏️ 编辑「{rec['name']}」的备注")

                edited_notes = []
                for j, s in enumerate(rec["steps"]):
                    st.markdown(f"&emsp;{s['text']}")
                    note = st.text_input(
                        f"备注 {j+1}",
                        value=s["note"],
                        key=f"edit_rec_note_{j}",
                        label_visibility="collapsed",
                    )
                    edited_notes.append(note)

                edited_overall = st.text_area(
                    "整体备注", value=rec.get("note", ""), key="edit_rec_overall"
                )

                col_s, col_c, _ = st.columns([1, 1, 4])
                with col_s:
                    if st.button(
                        "保存",
                        type="primary",
                        use_container_width=True,
                        key="save_edit_rec",
                    ):
                        for j, s in enumerate(rec["steps"]):
                            s["note"] = edited_notes[j].strip()
                        rec["note"] = edited_overall.strip()
                        storage.save_records(records)
                        storage.records = records
                        st.session_state.editing_record_idx = -1
                        for k in list(st.session_state):
                            if k.startswith("edit_rec_"):
                                del st.session_state[k]
                        st.session_state.save_msg = (
                            f"「{rec['name']}」的备注已更新！"
                        )
                        st.rerun()
                with col_c:
                    if st.button(
                        "取消", use_container_width=True, key="cancel_edit_rec"
                    ):
                        st.session_state.editing_record_idx = -1
                        st.rerun()

# ═══════════ Tab 3：可用食材 ═══════════

with tab_ingredients:
    st.subheader("🥬 可用食材管理")

    # ── 添加食材 ──

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
            add_ing_clicked = st.button(
                "添加",
                type="primary",
                use_container_width=True,
                key="add_ing_btn",
            )

        if add_ing_clicked:
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

    # ── 当前食材清单 ──

    st.divider()
    st.markdown("**📦 当前可用食材清单**")

    if not ingredients_data:
        st.info("暂无可用食材，请在上方添加。")
    else:
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

    # ── 菜谱推荐 ──

    st.divider()
    st.markdown("**🍳 菜谱推荐**")
    st.caption("根据当前可用食材，为您推荐可以制作的菜谱")

    if not ingredients_data:
        st.info("请先添加可用食材，才能获得菜谱推荐。")
    else:
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

        if full_matches:
            st.success(f"🎉 有 {len(full_matches)} 道菜谱的食材已全部齐备！")
            for r_name, r_data, matched, _ in full_matches:
                with st.container(border=True):
                    st.markdown(f"### ✅ {r_name}")
                    st.markdown(
                        f"食材齐全（{len(matched)}/{len(matched)}）：&nbsp;"
                        + " ".join(
                            f'<span style="display:inline-block;background:#c8e6c9;'
                            f'color:#2e7d32;padding:3px 10px;border-radius:12px;'
                            f'font-size:0.85em;margin:2px;">✓ {n}</span>'
                            for n in matched
                        ),
                        unsafe_allow_html=True,
                    )
                    with st.expander("查看做法"):
                        for step in r_data["steps"]:
                            st.markdown(f"&emsp;{step}")
                    with st.popover("🍳 开始做菜"):
                        st.markdown(f"确认开始「{r_name}」的做菜记录？")
                        if st.button(
                            "确认开始",
                            key=f"confirm_cook_{r_name}",
                            type="primary",
                        ):
                            st.session_state.start_cooking_recipe = r_name
                            st.session_state.save_msg = (
                                f"已为您预选「{r_name}」，"
                                f"请点击「📝 做菜记录」标签页开始记录！"
                            )
                            st.rerun()
        else:
            st.info("暂无食材完全齐备的菜谱。")

        if partial_matches:
            st.markdown("---")
            st.markdown(f"**差一点就能做的菜（{len(partial_matches)} 道）：**")
            for r_name, r_data, matched, missing in partial_matches:
                with st.container(border=True):
                    total = len(matched) + len(missing)
                    st.markdown(f"### 📖 {r_name}")
                    tags_matched = " ".join(
                        f'<span style="display:inline-block;background:#c8e6c9;'
                        f'color:#2e7d32;padding:3px 10px;border-radius:12px;'
                        f'font-size:0.85em;margin:2px;">✓ {n}</span>'
                        for n in matched
                    )
                    tags_missing = " ".join(
                        f'<span style="display:inline-block;background:#ffcdd2;'
                        f'color:#c62828;padding:3px 10px;border-radius:12px;'
                        f'font-size:0.85em;margin:2px;">✗ {n}</span>'
                        for n in missing
                    )
                    st.markdown(
                        f"食材匹配（{len(matched)}/{total}）：&nbsp;"
                        f"{tags_matched} {tags_missing}",
                        unsafe_allow_html=True,
                    )
