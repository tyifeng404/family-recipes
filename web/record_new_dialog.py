"""
web/record_new_dialog.py —— 新建做菜记录弹窗
"""

from datetime import date, datetime

import streamlit as st

import storage
from config import PHOTO_EXTS
from web.record_shared import (
    NEW_REC_PHOTOS_KEY,
    append_photo_item,
    close_new_record_dialog,
    ensure_state_list,
    save_photo_items,
)
from web.ui_helpers import ingredient_tags_html


def _render_new_record_photo_picker():
    st.markdown("**📷 添加照片（可选）**")
    photo_items = ensure_state_list(NEW_REC_PHOTOS_KEY)

    col_cam, col_upload = st.columns(2)
    with col_cam:
        with st.popover("📸 拍照", use_container_width=True):
            camera_photo = st.camera_input("调用系统相机拍照", key="new_rec_camera")
            if st.button("添加这张照片", type="primary", key="new_rec_add_camera"):
                if camera_photo:
                    append_photo_item(
                        NEW_REC_PHOTOS_KEY,
                        f"camera_{len(photo_items) + 1}.jpg",
                        camera_photo.getvalue(),
                    )
                    if "new_rec_camera" in st.session_state:
                        del st.session_state["new_rec_camera"]
                    st.toast("📸 已添加拍照图片")
                    st.rerun()
                else:
                    st.warning("请先拍照后再添加。")

    with col_upload:
        with st.popover("📁 上传照片", use_container_width=True):
            uploaded = st.file_uploader(
                "选择照片（支持多张）",
                accept_multiple_files=True,
                type=[e.lstrip(".") for e in PHOTO_EXTS],
                key="new_rec_upload_files",
            )
            if st.button("添加所选照片", type="primary", key="new_rec_add_upload"):
                if uploaded:
                    for file in uploaded:
                        append_photo_item(NEW_REC_PHOTOS_KEY, file.name, file.getvalue())
                    if "new_rec_upload_files" in st.session_state:
                        del st.session_state["new_rec_upload_files"]
                    st.toast(f"📁 已添加 {len(uploaded)} 张图片")
                    st.rerun()
                else:
                    st.warning("请先选择照片。")

    if not photo_items:
        st.caption("当前没有添加照片")
        return

    st.caption(f"已添加 {len(photo_items)} 张照片")
    for i, item in enumerate(photo_items):
        col_img, col_del = st.columns([5, 1])
        with col_img:
            st.image(item["data"], caption=item["name"])
        with col_del:
            if st.button("删除", key=f"new_rec_del_photo_{i}"):
                photo_items.pop(i)
                st.rerun()


def _save_new_record(
    selected: str,
    steps: list[str],
    records: list,
    ingredients_data: list,
    matching_ings: list[str],
):
    step_notes = [
        st.session_state.get(f"new_rec_note_{i}", "").strip()
        for i in range(len(steps))
    ]
    overall = st.session_state.get("new_rec_overall", "").strip()

    record_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    photo_items = list(st.session_state.get(NEW_REC_PHOTOS_KEY, []))
    photo_paths = save_photo_items(record_id, photo_items, start_index=1)

    record = {
        "id": record_id,
        "name": selected,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "steps": [
            {"text": step, "note": note}
            for step, note in zip(steps, step_notes)
        ],
        "note": overall,
        "photos": photo_paths,
    }
    records.append(record)
    storage.save_records(records)
    storage.records = records

    used_up = [
        name
        for name in matching_ings
        if st.session_state.get(f"new_rec_used_{name}", False)
    ]
    if used_up:
        updated_ings = [
            ing for ing in ingredients_data if ing["name"] not in set(used_up)
        ]
        storage.save_ingredients(updated_ings)
        storage.ingredients = updated_ings

    used_msg = f"，已清除 {len(used_up)} 种用完的食材" if used_up else ""
    st.session_state.save_msg = (
        f"「{selected}」的做菜记录已保存！（含 {len(photo_paths)} 张照片{used_msg}）"
    )
    close_new_record_dialog()
    st.rerun()


@st.dialog("📝 新建做菜记录")
def render_new_record_dialog(
    recipes: dict,
    records: list,
    ingredients_data: list,
):
    if not recipes:
        st.warning("请先在「菜谱管理」中添加菜谱，再来创建记录。")
        if st.button("关闭", key="new_rec_close_no_recipe", use_container_width=True):
            close_new_record_dialog()
            st.rerun()
        return

    recipe_names = list(recipes.keys())
    prefill_recipe = st.session_state.pop("new_rec_prefill_recipe", None)
    if prefill_recipe in recipe_names:
        st.session_state["new_rec_select"] = prefill_recipe
    if "new_rec_select" not in st.session_state:
        st.session_state["new_rec_select"] = recipe_names[0]

    selected = st.selectbox("选择菜谱", recipe_names, key="new_rec_select")
    recipe_data = recipes[selected]
    steps = recipe_data["steps"]
    recipe_ings = recipe_data.get("ingredients", [])

    today_str = date.today().strftime("%Y-%m-%d")
    st.markdown(f"📋 **本次记录：{selected} - {today_str}**")
    if recipe_ings:
        st.markdown(
            f"**主要食材：** {ingredient_tags_html(recipe_ings)}",
            unsafe_allow_html=True,
        )

    st.markdown("**步骤备注（可选）**")
    for i, step in enumerate(steps):
        st.markdown(f"&emsp;{step}")
        st.text_input(
            f"第 {i + 1} 步备注",
            key=f"new_rec_note_{i}",
            placeholder="可选",
            label_visibility="collapsed",
        )

    st.text_area("整体备注", placeholder="可选", key="new_rec_overall")

    _render_new_record_photo_picker()

    matching_ings: list[str] = []
    if recipe_ings and ingredients_data:
        avail_names = {ing["name"] for ing in ingredients_data}
        matching_ings = [n for n in recipe_ings if n in avail_names]

    if matching_ings:
        st.divider()
        st.markdown("**🥬 以下主要食材是否已基本用完？**")
        for ing_name in matching_ings:
            st.checkbox(ing_name, key=f"new_rec_used_{ing_name}")

    st.divider()
    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button(
            "💾 保存记录",
            type="primary",
            use_container_width=True,
            key="save_new_record",
        ):
            _save_new_record(
                selected,
                steps,
                records,
                ingredients_data,
                matching_ings,
            )
    with col_cancel:
        with st.popover("❌ 取消", use_container_width=True):
            st.warning("确认取消？已填写内容不会保存。")
            if st.button(
                "确认取消",
                type="secondary",
                use_container_width=True,
                key="confirm_cancel_new_rec",
            ):
                close_new_record_dialog()
                st.rerun()
