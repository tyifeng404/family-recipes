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


def _build_backend():
    backend_name = os.getenv("STORAGE_BACKEND", "local").strip().lower()
    if backend_name != "supabase":
        return LocalJsonBackend()

    url = os.getenv("SUPABASE_URL", "").strip()
    key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.getenv("SUPABASE_ANON_KEY", "").strip()
    )
    table = os.getenv("SUPABASE_STATE_TABLE", "app_state").strip() or "app_state"

    if not url or not key:
        print(
            "[storage] 未配置 SUPABASE_URL / SUPABASE_*_KEY，"
            "已回退到本地 JSON 后端。"
        )
        return LocalJsonBackend()

    try:
        return SupabaseStateBackend(url=url, key=key, table=table)
    except Exception as exc:
        print(f"[storage] Supabase 初始化失败（{exc}），已回退到本地 JSON 后端。")
        return LocalJsonBackend()


_backend = _build_backend()


def backend_name() -> str:
    """返回当前启用的后端名称（local / supabase）。"""
    return getattr(_backend, "name", "unknown")


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
