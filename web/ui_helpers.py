"""
web/ui_helpers.py —— Web 端共享 UI 工具函数
"""

import re

import streamlit as st


def strip_number_prefix(step: str) -> str:
    """去掉 '1. ' 这类序号前缀，返回纯步骤内容。"""
    dot = step.find(". ")
    if dot != -1 and step[:dot].strip().isdigit():
        return step[dot + 2 :]
    return step


def enter_edit(name: str, recipe_data: dict):
    """进入菜谱编辑模式，设置表单相关 session state 后 rerun。"""
    st.session_state.show_form = True
    st.session_state.form_name = name
    st.session_state.form_steps = "\n".join(
        strip_number_prefix(s) for s in recipe_data["steps"]
    )
    st.session_state.form_ingredients = "、".join(
        recipe_data.get("ingredients", [])
    )
    st.session_state.form_all_ingredients = "、".join(
        recipe_data.get("all_ingredients", recipe_data.get("ingredients", []))
    )
    st.session_state.form_tips = "\n".join(
        strip_number_prefix(s) for s in recipe_data.get("tips", [])
    )
    st.rerun()


def parse_ingredients(text: str) -> list[str]:
    """将逗号/顿号/空格分隔的食材文本解析为列表。"""
    parts = re.split(r"[,，、\s]+", text.strip())
    return [p for p in parts if p]


def ingredient_tags_html(ingredients: list[str]) -> str:
    """将食材列表渲染为彩色标签 HTML。"""
    return " ".join(
        f'<span style="display:inline-block;background:#e8f5e9;color:#2e7d32;'
        f'padding:3px 10px;border-radius:12px;font-size:0.85em;margin:2px 3px;">'
        f'{name}</span>'
        for name in ingredients
    )
