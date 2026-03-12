"""
web/tab_record.py —— Tab 2：做菜记录（新建 / 历史 / 编辑备注）
"""

import os
from datetime import datetime, date

import streamlit as st

import storage
from config import BASE_DIR, PHOTOS_DIR, PHOTO_EXTS
from web.ui_helpers import ingredient_tags_html


def render_record_tab(
    recipes: dict, records: list, ingredients_data: list
):
    """渲染做菜记录 Tab 的全部内容。"""
    start_recipe = st.session_state.pop("start_cooking_recipe", None)
    if start_recipe:
        st.session_state["creating_new_record"] = True

    if st.session_state.get("creating_new_record", False):
        _render_new_record(recipes, records, ingredients_data, start_recipe)
    else:
        _render_history_page(records)


# ────────────────────────────────────────────
#  历史记录页（含新建按钮）
# ────────────────────────────────────────────


def _render_history_page(records: list):
    st.subheader("📋 做菜记录")

    if st.button(
        "➕ 新建记录",
        type="primary",
        use_container_width=True,
        key="btn_new_record",
    ):
        st.session_state["creating_new_record"] = True
        st.rerun()

    st.divider()
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
        if st.button("← 返回", key="back_no_recipe"):
            st.session_state["creating_new_record"] = False
            st.rerun()
        return

    recipe_names = list(recipes.keys())
    if start_recipe and start_recipe in recipe_names:
        st.session_state["new_rec_select"] = start_recipe
    selected = st.selectbox("选择菜谱", recipe_names, key="new_rec_select")

    if not selected:
        return

    today_str = date.today().strftime("%Y-%m-%d")
    record_title = f"{selected} - {today_str}"
    st.markdown(
        f'<div style="background:#e8f5e9;padding:12px 16px;border-radius:8px;'
        f'margin:8px 0 16px 0;">'
        f'<span style="font-size:1.1em;font-weight:bold;color:#2e7d32;">'
        f'📋 本次记录：{record_title}</span></div>',
        unsafe_allow_html=True,
    )

    recipe_data = recipes[selected]
    steps = recipe_data["steps"]
    recipe_ings = recipe_data.get("ingredients", [])

    if recipe_ings:
        st.markdown(
            f"**主要食材：** {ingredient_tags_html(recipe_ings)}",
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

    overall = st.text_area("整体备注", placeholder="可选", key="new_rec_overall")

    st.markdown("**📷 添加照片（可选）**")

    if "new_rec_captured_photos" not in st.session_state:
        st.session_state["new_rec_captured_photos"] = []
    captured_photos = st.session_state["new_rec_captured_photos"]

    if captured_photos:
        st.info(f"📸 已拍摄 {len(captured_photos)} 张照片")

    col_cam, col_upl = st.columns(2)
    with col_cam:
        if st.button("📸 拍照", use_container_width=True, key="new_rec_btn_camera"):
            st.session_state["new_rec_show_camera"] = True
            st.rerun()
    with col_upl:
        if st.button("📁 上传照片", use_container_width=True, key="new_rec_btn_upload"):
            st.session_state["new_rec_show_upload"] = True
            st.rerun()

    if st.session_state.get("new_rec_show_camera", False):
        with st.container(border=True):
            camera_photo = st.camera_input(
                "对准目标，点击下方按钮拍照", key="new_rec_camera"
            )
            if camera_photo:
                captured_photos.append({
                    "name": f"camera_{len(captured_photos) + 1}.jpg",
                    "data": camera_photo.getvalue(),
                })
                st.session_state["new_rec_show_camera"] = False
                if "new_rec_camera" in st.session_state:
                    del st.session_state["new_rec_camera"]
                st.toast("📸 照片已拍摄！")
                st.rerun()
            if st.button("关闭相机", key="new_rec_close_camera"):
                st.session_state["new_rec_show_camera"] = False
                st.rerun()

    uploaded = None
    if st.session_state.get("new_rec_show_upload", False):
        with st.container(border=True):
            uploaded = st.file_uploader(
                "从相册选择（支持多张）",
                accept_multiple_files=True,
                type=[e.lstrip(".") for e in PHOTO_EXTS],
                key="new_rec_photos",
            )
            if st.button("收起", key="new_rec_close_upload"):
                st.session_state["new_rec_show_upload"] = False
                st.rerun()

    matching_ings: list[str] = []
    if recipe_ings and ingredients_data:
        avail_names = {ing["name"] for ing in ingredients_data}
        matching_ings = [n for n in recipe_ings if n in avail_names]

    if matching_ings:
        st.divider()
        st.markdown("**🥬 以下主要食材是否已基本用完？**")
        for ing_name in matching_ings:
            st.checkbox(f"{ing_name}", key=f"new_rec_used_{ing_name}")

    # ── 保存 & 取消 ──
    st.divider()
    col_save, col_cancel, _ = st.columns([1, 1, 3])
    with col_save:
        if st.button(
            "💾 保存记录",
            type="primary",
            use_container_width=True,
            key="save_new_record",
        ):
            _save_new_record(
                selected, steps, step_notes, overall,
                uploaded, records,
                ingredients_data, matching_ings,
            )
    with col_cancel:
        with st.popover("❌ 取消", use_container_width=True):
            st.warning("确认取消？已填写的内容将不会保存。")
            if st.button("确认取消", key="confirm_cancel_new_rec"):
                _cancel_new_record()


def _cancel_new_record():
    """取消新建记录，清理状态并返回历史列表。"""
    for k in list(st.session_state):
        if k.startswith("new_rec_"):
            del st.session_state[k]
    st.session_state["creating_new_record"] = False
    st.rerun()


def _save_new_record(
    selected, steps, step_notes, overall,
    uploaded, records, ingredients_data, matching_ings,
):
    record_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    photo_paths: list[str] = []
    all_photo_items: list[tuple[str, bytes]] = []
    for photo in st.session_state.get("new_rec_captured_photos", []):
        all_photo_items.append((photo["name"], photo["data"]))
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

    for k in list(st.session_state):
        if k.startswith("new_rec_"):
            del st.session_state[k]
    st.session_state["creating_new_record"] = False

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
