"""
storage.py —— 数据持久化入口模块

通过统一接口暴露菜谱/记录/食材读写，后端可切换：
  - 本地 JSON（默认）
  - Supabase（设置 STORAGE_BACKEND=supabase）

环境变量（Supabase）:
  - STORAGE_BACKEND=supabase
  - SUPABASE_URL=...
  - SUPABASE_SERVICE_ROLE_KEY=...  (或 SUPABASE_ANON_KEY)
  - SUPABASE_STATE_TABLE=app_state (可选)
"""

import os

from storage_backends import LocalJsonBackend, SupabaseStateBackend


_backend_diagnostic = ""


def _as_clean_str(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _get_from_mapping(mapping, keys: list[str]) -> str:
    try:
        for key in keys:
            if key in mapping:
                return _as_clean_str(mapping[key])
    except Exception:
        return ""
    return ""


def _read_setting(name: str, default: str = "") -> str:
    """
    读取配置项，优先级：
      1) 环境变量
      2) Streamlit secrets 顶层键
      3) Streamlit secrets 分组键（supabase/storage/app）
    """
    env_value = _as_clean_str(os.getenv(name, ""))
    if env_value:
        return env_value

    try:
        import streamlit as st

        secrets = st.secrets
    except Exception:
        return default

    top_value = _get_from_mapping(secrets, [name, name.lower(), name.upper()])
    if top_value:
        return top_value

    section_names = ["supabase", "storage", "app"]
    for section_name in section_names:
        section_value = _get_from_mapping(secrets, [section_name, section_name.upper()])
        if not section_value:
            # section 不是字符串时再尝试按映射读取
            try:
                section = secrets[section_name]
            except Exception:
                continue
            if isinstance(section, str):
                continue

            short_name = name.lower()
            if name.startswith("SUPABASE_"):
                short_name = name[len("SUPABASE_") :].lower()
            if name == "STORAGE_BACKEND":
                section_keys = [name, name.lower(), "backend", "storage_backend"]
            else:
                section_keys = [name, name.lower(), short_name]
            nested_value = _get_from_mapping(section, section_keys)
            if nested_value:
                return nested_value

    return default


def _build_backend():
    global _backend_diagnostic
    backend_name = _read_setting("STORAGE_BACKEND", "local").lower()
    if backend_name != "supabase":
        _backend_diagnostic = "当前使用本地存储（STORAGE_BACKEND != supabase）"
        return LocalJsonBackend()

    url = _read_setting("SUPABASE_URL", "")
    key = (
        _read_setting("SUPABASE_SERVICE_ROLE_KEY", "")
        or _read_setting("SUPABASE_ANON_KEY", "")
    )
    table = _read_setting("SUPABASE_STATE_TABLE", "app_state") or "app_state"

    if not url or not key:
        _backend_diagnostic = "缺少 SUPABASE_URL 或 SUPABASE_*_KEY，已回退 local"
        print(
            "[storage] 未配置 SUPABASE_URL / SUPABASE_*_KEY，"
            "已回退到本地 JSON 后端。"
        )
        return LocalJsonBackend()

    try:
        _backend_diagnostic = ""
        return SupabaseStateBackend(url=url, key=key, table=table)
    except Exception as exc:
        _backend_diagnostic = f"Supabase 初始化失败：{exc}"
        print(f"[storage] Supabase 初始化失败（{exc}），已回退到本地 JSON 后端。")
        return LocalJsonBackend()


_backend = _build_backend()


def backend_name() -> str:
    """返回当前启用的后端名称（local / supabase）。"""
    return getattr(_backend, "name", "unknown")


def backend_diagnostic() -> str:
    """返回后端诊断信息（用于页面排查配置问题）。"""
    return _backend_diagnostic


def load_recipes():
    return _backend.load_recipes()


def save_recipes(recipes):
    _backend.save_recipes(recipes)


def load_records():
    return _backend.load_records()


def save_records(records):
    _backend.save_records(records)


def load_ingredients():
    return _backend.load_ingredients()


def save_ingredients(ingredients):
    _backend.save_ingredients(ingredients)


# -------------------- 模块级数据加载 --------------------
recipes = load_recipes()
records = load_records()
ingredients = load_ingredients()
