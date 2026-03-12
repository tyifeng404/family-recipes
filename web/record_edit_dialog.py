"""
web/record_edit_dialog.py —— 历史记录编辑弹窗（备注 + 照片）
"""

import os
from datetime import datetime

import streamlit as st

import storage
from config import BASE_DIR, PHOTOS_DIR, PHOTO_EXTS
from web.record_shared import (
    EDIT_EXISTING_PHOTOS_KEY,
    EDIT_NEW_PHOTOS_KEY,
    append_photo_item,
    clear_state_by_prefix,
    close_edit_dialog,
    ensure_state_list,
    next_photo_index,
    remove_photo_file,
    save_photo_items,
)


def _init_edit_state(rec: dict, edit_idx: int):
    if st.session_state.get("edit_rec_loaded_idx") == edit_idx:
        return

    clear_state_by_prefix("edit_rec_note_")
    st.session_state["edit_rec_loaded_idx"] = edit_idx
    st.session_state["edit_rec_overall"] = rec.get("note", "")
    st.session_state[EDIT_EXISTING_PHOTOS_KEY] = list(rec.get("photos", []))
    st.session_state[EDIT_NEW_PHOTOS_KEY] = []
    for j, step in enumerate(rec["steps"]):
        st.session_state[f"edit_rec_note_{j}"] = step.get("note", "")


def _render_edit_photo_picker():
    existing = ensure_state_list(EDIT_EXISTING_PHOTOS_KEY)
    new_items = ensure_state_list(EDIT_NEW_PHOTOS_KEY)

    st.markdown("**📷 照片管理**")

    col_cam, col_upload = st.columns(2)
    with col_cam:
        with st.popover("📸 拍照添加", use_container_width=True):
            camera_photo = st.camera_input("调用系统相机拍照", key="edit_rec_camera")
            if st.button("添加这张照片", type="primary", key="edit_rec_add_camera"):
                if camera_photo:
                    append_photo_item(
                        EDIT_NEW_PHOTOS_KEY,
                        f"camera_{len(new_items) + 1}.jpg",
                        camera_photo.getvalue(),
                    )
                    if "edit_rec_camera" in st.session_state:
                        del st.session_state["edit_rec_camera"]
                    st.toast("📸 已添加拍照图片")
                    st.rerun()
                else:
                    st.warning("请先拍照后再添加。")

    with col_upload:
        with st.popover("📁 上传添加", use_container_width=True):
            uploaded = st.file_uploader(
                "选择照片（支持多张）",
                accept_multiple_files=True,
                type=[e.lstrip(".") for e in PHOTO_EXTS],
                key="edit_rec_upload_files",
            )
            if st.button("添加所选照片", type="primary", key="edit_rec_add_upload"):
                if uploaded:
                    for file in uploaded:
                        append_photo_item(
                            EDIT_NEW_PHOTOS_KEY, file.name, file.getvalue()
                        )
                    if "edit_rec_upload_files" in st.session_state:
                        del st.session_state["edit_rec_upload_files"]
                    st.toast(f"📁 已添加 {len(uploaded)} 张图片")
                    st.rerun()
                else:
                    st.warning("请先选择照片。")

    if existing:
        st.caption(f"当前已保存照片：{len(existing)} 张")
        for i, path in enumerate(existing):
            col_img, col_del = st.columns([5, 1])
            with col_img:
                full_path = os.path.join(BASE_DIR, path)
                if os.path.isfile(full_path):
                    st.image(full_path, caption=os.path.basename(path))
                else:
                    st.warning(f"文件缺失: {os.path.basename(path)}")
            with col_del:
                if st.button("删除", key=f"edit_rec_del_existing_{i}"):
                    existing.pop(i)
                    st.rerun()
    else:
        st.caption("当前没有已保存照片")

    if new_items:
        st.caption(f"待新增照片：{len(new_items)} 张")
        for i, item in enumerate(new_items):
            col_img, col_del = st.columns([5, 1])
            with col_img:
                st.image(item["data"], caption=f"待添加：{item['name']}")
            with col_del:
                if st.button("移除", key=f"edit_rec_del_new_{i}"):
                    new_items.pop(i)
                    st.rerun()


def _save_edit_record(records: list, edit_idx: int):
    rec = records[edit_idx]

    for j, step in enumerate(rec["steps"]):
        step["note"] = st.session_state.get(f"edit_rec_note_{j}", "").strip()
    rec["note"] = st.session_state.get("edit_rec_overall", "").strip()

    original_photos = list(rec.get("photos", []))
    kept_existing = list(st.session_state.get(EDIT_EXISTING_PHOTOS_KEY, []))
    new_items = list(st.session_state.get(EDIT_NEW_PHOTOS_KEY, []))

    removed = [p for p in original_photos if p not in kept_existing]
    for path in removed:
        remove_photo_file(path)

    record_id = rec.get("id")
    if (kept_existing or new_items) and not record_id:
        record_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        rec["id"] = record_id

    new_paths: list[str] = []
    if new_items:
        start_index = next_photo_index(kept_existing)
        new_paths = save_photo_items(record_id, new_items, start_index)

    rec["photos"] = kept_existing + new_paths

    if record_id and not rec["photos"]:
        photo_dir = os.path.join(PHOTOS_DIR, record_id)
        if os.path.isdir(photo_dir) and not os.listdir(photo_dir):
            os.rmdir(photo_dir)

    storage.save_records(records)
    storage.records = records
    st.session_state.save_msg = f"「{rec['name']}」的备注和照片已更新！"
    close_edit_dialog()
    st.rerun()


@st.dialog("✏️ 编辑记录（备注 + 照片）")
def render_edit_record_dialog(records: list):
    edit_idx = st.session_state.get("editing_record_idx", -1)
    if not (0 <= edit_idx < len(records)):
        return

    rec = records[edit_idx]
    _init_edit_state(rec, edit_idx)

    for j, step in enumerate(rec["steps"]):
        st.markdown(f"&emsp;{step['text']}")
        st.text_input(
            f"备注 {j + 1}",
            key=f"edit_rec_note_{j}",
            label_visibility="collapsed",
        )

    st.text_area("整体备注", key="edit_rec_overall")
    st.divider()

    _render_edit_photo_picker()

    st.divider()
    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button(
            "💾 保存修改",
            type="primary",
            use_container_width=True,
            key="save_edit_rec",
        ):
            _save_edit_record(records, edit_idx)
    with col_cancel:
        with st.popover("❌ 取消", use_container_width=True):
            st.warning("确认取消？未保存的备注和照片修改将丢失。")
            if st.button(
                "确认取消",
                type="secondary",
                use_container_width=True,
                key="cancel_edit_rec",
            ):
                close_edit_dialog()
                st.rerun()
