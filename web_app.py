"""
web_app.py —— 基于 Streamlit 的家庭菜谱 Web 界面（入口）

运行方式: streamlit run web_app.py
"""

import streamlit as st

import storage
from web.auth import (
    current_user,
    current_user_is_admin,
    ensure_auth_state,
    is_logged_in,
    render_auth_page,
)
from web.sidebar import render_sidebar
from web.tab_recipe import render_recipe_tab
from web.tab_record import render_record_tab
from web.tab_ingredients import render_ingredients_tab
from web.tab_account import render_account_tab
from web.account_dialog import render_account_dialog
from web.daily_recommend import render_daily_recommendations

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
    "form_all_ingredients": "",
    "form_tips": "",
    "save_msg": "",
    "editing_record_idx": -1,
    "creating_new_record": False,
    "open_account_dialog": False,
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

ensure_auth_state()

# ───────── 账号初始化与登录门禁 ─────────

accounts = storage.ensure_admin_account()

if not is_logged_in():
    render_auth_page()
    st.stop()

user = current_user()
is_admin_user = current_user_is_admin()

# ───────── 加载数据（每次 rerun 都从文件读最新） ─────────

recipes = storage.load_recipes()
records = storage.load_records()
ingredients_data = storage.load_ingredients()
accounts = storage.load_accounts()

visible_recipes = storage.get_visible_recipes(recipes, accounts, user)
visible_records = storage.get_visible_records(records, accounts, user)
visible_ingredients = storage.get_visible_ingredients(ingredients_data, accounts, user)

# ───────── 保存成功提示 ─────────

if st.session_state.save_msg:
    st.success(st.session_state.save_msg)
    st.balloons()
    st.session_state.save_msg = ""

# ───────── 侧边栏 ─────────

render_sidebar(
    visible_recipes,
    visible_ingredients,
    visible_records,
    current_user=user,
    is_admin=is_admin_user,
)

if st.session_state.get("open_account_dialog", False):
    render_account_dialog(user)

# ───────── 每日推荐菜谱 ─────────

render_daily_recommendations(visible_recipes, visible_ingredients)

# ═══════════════════════════════════════════
#  三个主 Tab
# ═══════════════════════════════════════════

tab_recipe, tab_record, tab_ingredients, tab_account = st.tabs(
    ["🍳 菜谱管理", "📝 做菜记录", "🥬 可用食材", "👤 账号管理"]
)

with tab_recipe:
    render_recipe_tab(recipes, visible_recipes, visible_records, user, is_admin_user)

with tab_record:
    render_record_tab(
        recipes,
        visible_recipes,
        records,
        visible_records,
        ingredients_data,
        visible_ingredients,
        user,
        is_admin_user,
    )

with tab_ingredients:
    render_ingredients_tab(
        visible_recipes,
        ingredients_data,
        visible_ingredients,
        user,
        is_admin_user,
    )

with tab_account:
    render_account_tab(user, is_admin_user)
