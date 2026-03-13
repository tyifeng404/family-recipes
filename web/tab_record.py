"""
web/tab_record.py —— Tab 2：做菜记录入口（新建 / 历史）
"""

import os

import streamlit as st

import storage
from config import BASE_DIR, PHOTOS_DIR
from web.record_edit_dialog import render_edit_record_dialog
from web.record_new_dialog import render_new_record_dialog
from web.record_shared import remove_photo_file


def _can_edit(rec: dict, current_user: str, is_admin_user: bool) -> bool:
    owner = rec.get("owner", "admin")
    return is_admin_user or owner == current_user


def render_record_tab(
    recipes: dict,
    visible_recipes: dict,
    records: list,
    visible_records: list,
    ingredients_data: list,
    visible_ingredients: list,
    current_user: str,
    is_admin_user: bool,
):
    """渲染做菜记录 Tab 的全部内容。"""
    st.subheader("📋 做菜记录")

    start_recipe = st.session_state.pop("start_cooking_recipe", None)
    if start_recipe:
        st.session_state["open_new_record_dialog"] = True
        st.session_state["new_rec_prefill_recipe"] = start_recipe

    if st.button(
        "➕ 新建做菜记录",
        type="primary",
        use_container_width=True,
        key="btn_new_record",
    ):
        st.session_state["open_new_record_dialog"] = True

    st.divider()
    _render_history(records, visible_records, current_user, is_admin_user)

    if st.session_state.get("open_new_record_dialog", False):
        render_new_record_dialog(
            visible_recipes,
            records,
            ingredients_data,
            visible_ingredients,
            current_user,
            is_admin_user,
        )

    edit_idx = st.session_state.get("editing_record_idx", -1)
    if 0 <= edit_idx < len(records):
        render_edit_record_dialog(records, current_user, is_admin_user)


def _render_history(
    records: list,
    visible_records: list,
    current_user: str,
    is_admin_user: bool,
):
    if not visible_records:
        st.info("暂无做菜记录，快去做一道菜并记录吧！")
        return

    index_map = {id(rec): idx for idx, rec in enumerate(records)}
    for rec in visible_records:
        i = index_map.get(id(rec), -1)
        if i == -1:
            continue
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

        with st.expander("".join(label_parts)):
            owner = rec.get("owner", "admin")
            if owner != current_user:
                st.caption(f"来源账号：{owner}")
            for step in rec["steps"]:
                st.markdown(f"&emsp;{step['text']}")
                if step["note"]:
                    st.markdown(f"&emsp;&emsp;💬 _{step['note']}_")

            if rec.get("note"):
                st.markdown(f"**整体备注：** {rec['note']}")
            else:
                st.caption("整体备注：（无）")

            photos = rec.get("photos", [])
            if photos:
                st.markdown(f"**📷 照片（{len(photos)} 张）：**")
                n_cols = min(len(photos), 3)
                cols = st.columns(n_cols)
                for j, path in enumerate(photos):
                    full_path = os.path.join(BASE_DIR, path)
                    col = cols[j % n_cols]
                    if os.path.isfile(full_path):
                        col.image(full_path, caption=os.path.basename(path))
                    else:
                        col.warning(f"文件缺失: {os.path.basename(path)}")

            col_edit, col_del, _ = st.columns([1, 1, 4])
            with col_edit:
                if _can_edit(rec, current_user, is_admin_user) and st.button(
                    "✏️ 编辑备注/照片", key=f"edit_rec_{i}"
                ):
                    st.session_state["editing_record_idx"] = i
                    st.session_state["edit_rec_loaded_idx"] = -1
                    st.rerun()
                elif not _can_edit(rec, current_user, is_admin_user):
                    st.caption("仅创建者或管理员可编辑")
            with col_del:
                if _can_edit(rec, current_user, is_admin_user):
                    with st.popover("🗑️ 删除"):
                        st.warning("确认删除此记录？删除后不可恢复。")
                        if st.button("确认删除", key=f"confirm_del_{i}"):
                            _delete_record(records, i, rec)


def _delete_record(records: list, idx: int, rec: dict):
    for path in rec.get("photos", []):
        remove_photo_file(path)

    record_id = rec.get("id")
    if record_id:
        photo_dir = os.path.join(PHOTOS_DIR, record_id)
        if os.path.isdir(photo_dir) and not os.listdir(photo_dir):
            os.rmdir(photo_dir)

    records.pop(idx)
    storage.save_records(records)
    storage.records = records
    st.session_state.save_msg = "记录已删除"
    st.rerun()
