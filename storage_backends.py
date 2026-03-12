"""
storage_backends.py —— 数据后端实现

提供两种可切换后端：
  - LocalJsonBackend: 本地 JSON 文件（默认）
  - SupabaseStateBackend: Supabase 单表状态存储
"""

import copy
import json
import os

from config import DATA_FILE, DEFAULT_RECIPES, INGREDIENTS_FILE, RECORDS_FILE


def _migrate_recipes(data: dict) -> tuple[dict, bool]:
    """
    将旧格式 {name: [steps]} 自动迁移为新格式
    {name: {"steps": [...], "ingredients": [...]}}
    """
    migrated = False
    for name in list(data.keys()):
        if isinstance(data[name], list):
            data[name] = {"steps": data[name], "ingredients": []}
            migrated = True
    return data, migrated


def _load_json_file(path: str, default):
    if not os.path.exists(path):
        return copy.deepcopy(default)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json_file(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class LocalJsonBackend:
    """本地 JSON 文件后端。"""

    name = "local"

    def load_recipes(self) -> dict:
        data = _load_json_file(DATA_FILE, None)
        if data is None:
            data = copy.deepcopy(DEFAULT_RECIPES)
            self.save_recipes(data)
            return data
        if not isinstance(data, dict):
            raise RuntimeError(f"{DATA_FILE} 数据格式错误，期望 dict")
        data, migrated = _migrate_recipes(data)
        if migrated:
            self.save_recipes(data)
        return data

    def save_recipes(self, recipes: dict) -> None:
        _save_json_file(DATA_FILE, recipes)

    def load_records(self) -> list:
        data = _load_json_file(RECORDS_FILE, [])
        if isinstance(data, list):
            return data
        raise RuntimeError(f"{RECORDS_FILE} 数据格式错误，期望 list")

    def save_records(self, records: list) -> None:
        _save_json_file(RECORDS_FILE, records)

    def load_ingredients(self) -> list:
        data = _load_json_file(INGREDIENTS_FILE, [])
        if isinstance(data, list):
            return data
        raise RuntimeError(f"{INGREDIENTS_FILE} 数据格式错误，期望 list")

    def save_ingredients(self, ingredients: list) -> None:
        _save_json_file(INGREDIENTS_FILE, ingredients)


class SupabaseStateBackend:
    """
    Supabase 后端：将三个状态块保存到同一张表（默认 app_state）中。

    表结构示例见 scripts/supabase_init.sql。
    """

    name = "supabase"

    def __init__(self, url: str, key: str, table: str = "app_state"):
        try:
            from supabase import create_client
        except ImportError as exc:
            raise RuntimeError(
                "未安装 supabase，请先执行: pip3 install supabase"
            ) from exc
        self._client = create_client(url, key)
        self._table = table

    def _read_state(self, key: str, default):
        result = (
            self._client
            .table(self._table)
            .select("value")
            .eq("key", key)
            .limit(1)
            .execute()
        )
        rows = result.data or []
        if not rows:
            return copy.deepcopy(default)
        value = rows[0].get("value")
        if value is None:
            return copy.deepcopy(default)
        return value

    def _upsert_state(self, key: str, value) -> None:
        (
            self._client
            .table(self._table)
            .upsert({"key": key, "value": value}, on_conflict="key")
            .execute()
        )

    def load_recipes(self) -> dict:
        data = self._read_state("recipes", None)
        if data is None:
            data = copy.deepcopy(DEFAULT_RECIPES)
            self.save_recipes(data)
            return data
        if not isinstance(data, dict):
            raise RuntimeError("Supabase app_state.recipes 数据格式错误，期望 dict")
        data, migrated = _migrate_recipes(data)
        if migrated:
            self.save_recipes(data)
        return data

    def save_recipes(self, recipes: dict) -> None:
        self._upsert_state("recipes", recipes)

    def load_records(self) -> list:
        data = self._read_state("records", [])
        if isinstance(data, list):
            return data
        raise RuntimeError("Supabase app_state.records 数据格式错误，期望 list")

    def save_records(self, records: list) -> None:
        self._upsert_state("records", records)

    def load_ingredients(self) -> list:
        data = self._read_state("ingredients", [])
        if isinstance(data, list):
            return data
        raise RuntimeError("Supabase app_state.ingredients 数据格式错误，期望 list")

    def save_ingredients(self, ingredients: list) -> None:
        self._upsert_state("ingredients", ingredients)
