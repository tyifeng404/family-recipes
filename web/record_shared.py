"""
web/record_shared.py —— 做菜记录页的共享状态与照片工具
"""

import os

import streamlit as st

from config import BASE_DIR, PHOTOS_DIR, PHOTO_EXTS

NEW_REC_PHOTOS_KEY = "new_rec_photo_items"
EDIT_EXISTING_PHOTOS_KEY = "edit_rec_existing_photos"
EDIT_NEW_PHOTOS_KEY = "edit_rec_new_photo_items"


def ensure_state_list(key: str) -> list:
    if key not in st.session_state:
        st.session_state[key] = []
    return st.session_state[key]


def clear_state_by_prefix(prefix: str):
    for k in list(st.session_state):
        if k.startswith(prefix):
            del st.session_state[k]


def close_new_record_dialog():
    st.session_state["open_new_record_dialog"] = False
    clear_state_by_prefix("new_rec_")
    if NEW_REC_PHOTOS_KEY in st.session_state:
        del st.session_state[NEW_REC_PHOTOS_KEY]


def close_edit_dialog():
    st.session_state["editing_record_idx"] = -1
    clear_state_by_prefix("edit_rec_")
    if EDIT_EXISTING_PHOTOS_KEY in st.session_state:
        del st.session_state[EDIT_EXISTING_PHOTOS_KEY]
    if EDIT_NEW_PHOTOS_KEY in st.session_state:
        del st.session_state[EDIT_NEW_PHOTOS_KEY]


def append_photo_item(state_key: str, name: str, data: bytes):
    items = ensure_state_list(state_key)
    items.append({"name": name, "data": data})


def remove_photo_file(rel_path: str):
    full_path = os.path.join(BASE_DIR, rel_path)
    if os.path.isfile(full_path):
        os.remove(full_path)


def next_photo_index(photo_paths: list[str]) -> int:
    max_idx = 0
    for path in photo_paths:
        stem = os.path.splitext(os.path.basename(path))[0]
        if stem.isdigit():
            max_idx = max(max_idx, int(stem))
    return max_idx + 1


def save_photo_items(
    record_id: str,
    photo_items: list[dict],
    start_index: int,
) -> list[str]:
    if not photo_items:
        return []

    dest_dir = os.path.join(PHOTOS_DIR, record_id)
    os.makedirs(dest_dir, exist_ok=True)

    saved_paths: list[str] = []
    idx = start_index
    for item in photo_items:
        ext = os.path.splitext(item["name"])[1].lower() or ".jpg"
        if ext not in PHOTO_EXTS:
            ext = ".jpg"
        dest_name = f"{idx}{ext}"
        dest_path = os.path.join(dest_dir, dest_name)
        with open(dest_path, "wb") as f:
            f.write(item["data"])
        saved_paths.append(os.path.join("photos", record_id, dest_name))
        idx += 1
    return saved_paths
