"""
storage.py —— 数据持久化模块

负责菜谱、做菜记录和可用食材三种数据的 JSON 读写。
同时在模块级别加载数据，供其他模块通过 `import storage` 访问：
    storage.recipes      —— 当前菜谱字典
    storage.records      —— 当前做菜记录列表
    storage.ingredients  —— 当前可用食材列表
"""

import json
import os

from config import DATA_FILE, RECORDS_FILE, INGREDIENTS_FILE, DEFAULT_RECIPES


# -------------------- 菜谱读写 --------------------


def _migrate_recipes(data):
    """将旧格式 {name: [steps]} 自动转为新格式 {name: {"steps": [...], "ingredients": [...]}}"""
    migrated = False
    for name in list(data.keys()):
        if isinstance(data[name], list):
            data[name] = {"steps": data[name], "ingredients": []}
            migrated = True
    return data, migrated


def load_recipes():
    """
    从 recipes.json 加载菜谱数据，自动迁移旧格式。

    返回值:
        dict —— 键为菜名，值为 {"steps": [...], "ingredients": [...]}
    """
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        data, migrated = _migrate_recipes(data)
        if migrated:
            save_recipes(data)
        return data
    recipes = dict(DEFAULT_RECIPES)
    save_recipes(recipes)
    return recipes


def save_recipes(recipes):
    """将菜谱数据写入 recipes.json。"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(recipes, f, ensure_ascii=False, indent=2)


# -------------------- 做菜记录读写 --------------------


def load_records():
    """从 records.json 加载做菜记录列表。"""
    if os.path.exists(RECORDS_FILE):
        with open(RECORDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_records(records):
    """将做菜记录列表写入 records.json。"""
    with open(RECORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


# -------------------- 可用食材读写 --------------------


def load_ingredients():
    """
    从 ingredients.json 加载可用食材列表。

    返回值:
        list —— 食材字典列表，每项包含 name（名称）和 date（购买日期）
    """
    if os.path.exists(INGREDIENTS_FILE):
        with open(INGREDIENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_ingredients(ingredients):
    """将可用食材列表写入 ingredients.json。"""
    with open(INGREDIENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(ingredients, f, ensure_ascii=False, indent=2)


# -------------------- 模块级数据加载 --------------------

recipes = load_recipes()
records = load_records()
ingredients = load_ingredients()
