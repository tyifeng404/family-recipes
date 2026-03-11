"""
web/tab_record.py —— Tab 2：做菜记录（新建 / 历史 / 编辑备注）
"""

import os
from datetime import datetime

import streamlit as st

import storage
from config import BASE_DIR, PHOTOS_DIR, PHOTO_EXTS
from web.ui_helpers import ingredient_tags_html


def render_record_tab(
    recipes: dict, records: list, ingredients_data: list
):
    """渲染做菜记录 Tab 的全部内容。"""
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

    # 从推荐跳转时强制进入新建模式（radio 组件可能未及时响应 session state）
    if start_recipe:
        rec_mode = "➕ 新建记录"

    st.divider()

    if rec_mode == "➕ 新建记录":
        _render_new_record(recipes, records, ingredients_data, start_recipe)
    else:
        _render_history(records)


# ────────────────────────────────────────────
#  新建记录
# ────────────────────────────────────────────


def _render_new_record(
    recipes: dict,
    records: list,
    ingredients_data: list,
    start_recipe: str | None,
):
    st.subheader("📝 新建做菜记录")

    if not recipes:
        st.warning("请先在「菜谱管理」中添加菜谱，再来创建记录")
        return

    recipe_names = list(recipes.keys())
    if start_recipe and start_recipe in recipe_names:
        st.session_state["new_rec_select"] = start_recipe
    selected = st.selectbox("选择菜谱", recipe_names, key="new_rec_select")

    if not selected:
        return

    recipe_data = recipes[selected]
    steps = recipe_data["steps"]
    recipe_ings = recipe_data.get("ingredients", [])

    if recipe_ings:
        st.markdown(
            f"**主要食材：** {ingredient_tags_html(recipe_ings)}",
            unsafe_allow_html=True,
        )

    # 逐步备注
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

    overall = st.text_area("整体备注", placeholder="可选", key="new_rec_overall")

    # 照片
    st.markdown("**📷 添加照片（可选）**")
    camera_photo = st.camera_input("拍一张照片", key="new_rec_camera")
    uploaded = st.file_uploader(
        "或从相册选择（支持多张）",
        accept_multiple_files=True,
        type=[e.lstrip(".") for e in PHOTO_EXTS],
        key="new_rec_photos",
    )

    # 食材消耗检查
    matching_ings: list[str] = []
    if recipe_ings and ingredients_data:
        avail_names = {ing["name"] for ing in ingredients_data}
        matching_ings = [n for n in recipe_ings if n in avail_names]

    if matching_ings:
        st.divider()
        st.markdown("**🥬 以下主要食材是否已基本用完？**")
        for ing_name in matching_ings:
            st.checkbox(f"{ing_name}", key=f"new_rec_used_{ing_name}")

    # 保存
    if st.button("保存记录", type="primary", key="save_new_record"):
        _save_new_record(
            selected, steps, step_notes, overall,
            camera_photo, uploaded, records, ingredients_data, matching_ings,
        )


def _save_new_record(
    selected, steps, step_notes, overall,
    camera_photo, uploaded, records, ingredients_data, matching_ings,
):
    record_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 保存照片
    photo_paths: list[str] = []
    all_photo_items: list[tuple[str, bytes]] = []
    if camera_photo:
        all_photo_items.append(("camera.jpg", camera_photo.getvalue()))
    if uploaded:
        for file in uploaded:
            all_photo_items.append((file.name, file.getvalue()))
    if all_photo_items:
        dest_dir = os.path.join(PHOTOS_DIR, record_id)
        os.makedirs(dest_dir, exist_ok=True)
        for j, (fname, fdata) in enumerate(all_photo_items, 1):
            ext = os.path.splitext(fname)[1].lower() or ".jpg"
            dest_name = f"{j}{ext}"
            with open(os.path.join(dest_dir, dest_name), "wb") as f:
                f.write(fdata)
            photo_paths.append(os.path.join("photos", record_id, dest_name))

    # 组装记录
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

    # 处理食材消耗
    used_up = []
    if matching_ings:
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

    # 清理 session state
    for k in list(st.session_state):
        if k.startswith("new_rec_"):
            del st.session_state[k]

    used_msg = f"，已清除 {len(used_up)} 种用完的食材" if used_up else ""
    st.session_state.save_msg = (
        f"「{selected}」的做菜记录已保存！"
        f"（含 {len(photo_paths)} 张照片{used_msg}）"
    )
    st.rerun()


# ────────────────────────────────────────────
#  历史记录
# ────────────────────────────────────────────


def _render_history(records: list):
    st.subheader("📋 历史做菜记录")

    if not records:
        st.info("暂无做菜记录，快去做一道菜并记录吧！")
        return

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
                        _delete_record(records, i, rec)

    # ── 编辑记录备注表单 ──
    _render_edit_form(records)


def _delete_record(records: list, idx: int, rec: dict):
    for p in rec.get("photos", []):
        fp = os.path.join(BASE_DIR, p)
        if os.path.isfile(fp):
            os.remove(fp)
    rid = rec.get("id")
    if rid:
        pd = os.path.join(PHOTOS_DIR, rid)
        if os.path.isdir(pd) and not os.listdir(pd):
            os.rmdir(pd)
    records.pop(idx)
    storage.save_records(records)
    storage.records = records
    st.session_state.save_msg = "记录已删除"
    st.rerun()


def _render_edit_form(records: list):
    edit_idx = st.session_state.editing_record_idx
    if not (0 <= edit_idx < len(records)):
        return

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
            st.session_state.save_msg = f"「{rec['name']}」的备注已更新！"
            st.rerun()
    with col_c:
        if st.button("取消", use_container_width=True, key="cancel_edit_rec"):
            st.session_state.editing_record_idx = -1
            st.rerun()
