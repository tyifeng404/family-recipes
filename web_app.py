"""
web_app.py —— 基于 Streamlit 的家庭菜谱 Web 界面（入口）

运行方式: streamlit run web_app.py
"""

import streamlit as st

import storage
from web.sidebar import render_sidebar
from web.tab_recipe import render_recipe_tab
from web.tab_record import render_record_tab
from web.tab_ingredients import render_ingredients_tab

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

render_sidebar(recipes, ingredients_data, records)

# ═══════════════════════════════════════════
#  三个主 Tab
# ═══════════════════════════════════════════

tab_recipe, tab_record, tab_ingredients = st.tabs(
    ["🍳 菜谱管理", "📝 做菜记录", "🥬 可用食材"]
)

with tab_recipe:
    render_recipe_tab(recipes)

with tab_record:
    render_record_tab(recipes, records, ingredients_data)

with tab_ingredients:
    render_ingredients_tab(recipes, ingredients_data)
