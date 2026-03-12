"""
web/daily_recommend.py —— 首页：每日推荐菜谱
"""

import random
from datetime import date

import streamlit as st

_TAG_HAVE = (
    '<span style="display:inline-block;background:#c8e6c9;'
    'color:#2e7d32;padding:3px 10px;border-radius:12px;'
    'font-size:0.85em;margin:2px;">✓ {}</span>'
)
_TAG_NEED = (
    '<span style="display:inline-block;background:#ffcdd2;'
    'color:#c62828;padding:3px 10px;border-radius:12px;'
    'font-size:0.85em;margin:2px;">🛒 {}</span>'
)


def render_daily_recommendations(recipes: dict, ingredients_data: list):
    """在首页展示每日推荐菜谱（与已保存菜谱平级）。"""
    if not recipes:
        return

    avail_names = (
        {ing["name"] for ing in ingredients_data} if ingredients_data else set()
    )
    recommendations, is_matched = _get_recommendations(recipes, avail_names)

    if not recommendations:
        return

    st.subheader("🌟 每日推荐菜谱")
    if is_matched:
        st.caption("📦 根据您的已购食材，为您智能推荐")
    else:
        if avail_names:
            st.caption("暂无与已购食材匹配的菜谱，以下为今日随机推荐")
        else:
            st.caption("🎲 今日随机推荐，快来看看有什么好吃的！")

    cols = st.columns(min(len(recommendations), 3))
    for col, rec in zip(cols, recommendations):
        with col:
            with st.container(border=True):
                st.markdown(f"#### {rec['name']}")

                r_ings = rec["data"].get("ingredients", [])
                if r_ings:
                    tags = " ".join(
                        _TAG_HAVE.format(ig) if ig in avail_names
                        else _TAG_NEED.format(ig)
                        for ig in r_ings
                    )
                    st.markdown(tags, unsafe_allow_html=True)

                if rec["missing"]:
                    st.markdown(
                        f"**🛒 需采购：** {'、'.join(rec['missing'])}"
                    )
                else:
                    st.success("✅ 食材已齐全！")

                with st.expander("查看做法"):
                    for step in rec["data"]["steps"]:
                        st.markdown(f"&emsp;{step}")

    st.divider()


def _get_recommendations(recipes: dict, avail_names: set):
    """返回 (推荐列表, 是否为食材匹配推荐)。"""
    matching = []

    if avail_names:
        for r_name, r_data in recipes.items():
            r_ings = r_data.get("ingredients", [])
            if not r_ings:
                continue
            matched = [ig for ig in r_ings if ig in avail_names]
            missing = [ig for ig in r_ings if ig not in avail_names]
            if matched:
                matching.append({
                    "name": r_name,
                    "data": r_data,
                    "matched": matched,
                    "missing": missing,
                    "score": len(matched) / len(r_ings),
                })

    if matching:
        matching.sort(key=lambda x: (-x["score"], len(x["missing"])))
        return matching[:3], True

    # 随机推荐：使用当日日期作为种子，保证同一天结果一致
    all_recipes = list(recipes.items())
    rng = random.Random(date.today().toordinal())
    rng.shuffle(all_recipes)

    result = []
    for r_name, r_data in all_recipes[:3]:
        r_ings = r_data.get("ingredients", [])
        result.append({
            "name": r_name,
            "data": r_data,
            "matched": [],
            "missing": r_ings,
            "score": 0,
        })

    return result, False
