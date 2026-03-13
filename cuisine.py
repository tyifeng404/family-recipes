"""菜系与标签常量、归一化工具。"""

from __future__ import annotations

DEFAULT_CUISINE_GROUP = "家常特色"
DEFAULT_CUISINE = "家常特色"
DEFAULT_DIFFICULTY = "简单"

CUISINE_GROUP_OPTIONS = [
    DEFAULT_CUISINE_GROUP,
    "中餐",
    "外国菜",
]

CHINESE_CUISINE_OPTIONS = [
    "中餐经典",
    "川菜",
    "粤菜",
    "湘菜",
    "鲁菜",
    "淮扬菜",
    "浙菜",
    "闽菜",
    "徽菜",
]

FOREIGN_CUISINE_OPTIONS = [
    "西餐",
    "日本菜",
    "朝鲜菜",
    "东南亚菜",
    "其他地区",
]

DIFFICULTY_OPTIONS = ["简单", "中等", "进阶"]
BASE_TAG_OPTIONS = ["辣", "不辣", "适合儿童"]


def normalize_cuisine_group(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return DEFAULT_CUISINE_GROUP
    if text == "西餐经典":
        return "外国菜"
    return text


def normalize_cuisine(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return DEFAULT_CUISINE
    if text == "西餐经典":
        return "西餐"
    return text


def infer_cuisine_group(cuisine: str) -> str:
    c = normalize_cuisine(cuisine)
    if c in FOREIGN_CUISINE_OPTIONS:
        return "外国菜"
    if c in CHINESE_CUISINE_OPTIONS:
        return "中餐"
    return DEFAULT_CUISINE_GROUP


def normalize_difficulty(value: str) -> str:
    text = str(value or "").strip()
    if text in DIFFICULTY_OPTIONS:
        return text
    return DEFAULT_DIFFICULTY


def normalize_tags(tags: list[str] | None) -> list[str]:
    if not tags:
        return []

    seen: set[str] = set()
    normalized: list[str] = []
    for tag in tags:
        t = str(tag or "").strip()
        if not t or t in seen:
            continue
        seen.add(t)
        normalized.append(t)

    if "辣" in normalized and "不辣" in normalized:
        normalized = [t for t in normalized if t != "不辣"]

    return normalized


def all_builtin_cuisine_options() -> list[str]:
    return [DEFAULT_CUISINE] + CHINESE_CUISINE_OPTIONS + FOREIGN_CUISINE_OPTIONS
