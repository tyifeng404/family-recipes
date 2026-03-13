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

import hashlib
import hmac
import os
import secrets
from copy import deepcopy
from datetime import datetime

from builtin_recipes import BUILTIN_RECIPES, BUILTIN_RECIPE_VERSION
from cuisine import (
    infer_cuisine_group,
    normalize_cuisine,
    normalize_cuisine_group,
    normalize_difficulty,
    normalize_tags,
)
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
        section = None
        try:
            if section_name in secrets:
                section = secrets[section_name]
        except Exception:
            pass
        if section is None:
            try:
                upper_key = section_name.upper()
                if upper_key in secrets:
                    section = secrets[upper_key]
            except Exception:
                section = None
        if section is None or isinstance(section, str):
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

    url = _read_setting("SUPABASE_URL", "").rstrip("/")
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


def _switch_to_local_backend(reason: str):
    global _backend, _backend_diagnostic
    if getattr(_backend, "name", "") == "local":
        return
    _backend = LocalJsonBackend()
    _backend_diagnostic = f"{reason}，已自动回退 local"
    print(f"[storage] {reason}，已自动回退本地 JSON 后端。")


def _call_backend(method_name: str, *args):
    method = getattr(_backend, method_name)
    try:
        return method(*args)
    except Exception as exc:
        if getattr(_backend, "name", "") == "supabase":
            reason = f"Supabase 调用失败（{exc.__class__.__name__}: {exc}）"
            _switch_to_local_backend(reason)
            return getattr(_backend, method_name)(*args)
        raise


def backend_name() -> str:
    """返回当前启用的后端名称（local / supabase）。"""
    return getattr(_backend, "name", "unknown")


def backend_diagnostic() -> str:
    """返回后端诊断信息（用于页面排查配置问题）。"""
    return _backend_diagnostic


def _ensure_recipe_meta(recipes_data: dict) -> tuple[dict, bool]:
    """
    统一补齐菜谱元信息：
    - cuisine_group / cuisine
    - tags / difficulty
    """
    changed = False
    for name, recipe in list(recipes_data.items()):
        if not isinstance(recipe, dict):
            continue

        normalized = _normalize_recipe_payload(recipe)
        if normalized != recipe:
            recipe = normalized
            changed = True

        recipes_data[name] = recipe
    return recipes_data, changed


def _normalize_recipe_payload(recipe: dict) -> dict:
    data = dict(recipe)

    # 兼容旧字段：西餐经典 -> 外国菜/西餐
    cuisine = normalize_cuisine(data.get("cuisine"))
    cuisine_group = normalize_cuisine_group(data.get("cuisine_group"))
    if cuisine_group == "家常特色":
        cuisine_group = infer_cuisine_group(cuisine)

    tags = normalize_tags(data.get("tags") if isinstance(data.get("tags"), list) else [])
    difficulty = normalize_difficulty(data.get("difficulty"))

    data["cuisine"] = cuisine
    data["cuisine_group"] = cuisine_group
    data["tags"] = tags
    data["difficulty"] = difficulty
    data["is_builtin"] = bool(data.get("is_builtin", False))
    data["builtin_version"] = _as_clean_str(data.get("builtin_version"))
    return data


def _sync_builtin_recipes(recipes_data: dict) -> tuple[dict, bool]:
    changed = False
    # 先清理已经下架的旧版内置菜谱（仅清理 system / is_builtin 数据）
    for name in list(recipes_data.keys()):
        if name in BUILTIN_RECIPES:
            continue
        existing = recipes_data.get(name)
        if not isinstance(existing, dict):
            continue
        owner = _as_clean_str(existing.get("owner"))
        is_builtin = bool(existing.get("is_builtin")) or owner == "system"
        if is_builtin:
            recipes_data.pop(name, None)
            changed = True

    for name, builtin_recipe in BUILTIN_RECIPES.items():
        existing = recipes_data.get(name)
        if existing is not None and not isinstance(existing, dict):
            continue

        should_add = existing is None
        should_upgrade = False
        if isinstance(existing, dict):
            owner = _as_clean_str(existing.get("owner"))
            is_builtin = bool(existing.get("is_builtin")) or owner == "system"
            builtin_version = _as_clean_str(existing.get("builtin_version"))
            should_upgrade = is_builtin and builtin_version != BUILTIN_RECIPE_VERSION

        if should_add or should_upgrade:
            recipes_data[name] = deepcopy(builtin_recipe)
            changed = True

    return recipes_data, changed


def _merge_builtin_recipes(recipes_data: dict) -> tuple[dict, bool]:
    # 兼容旧调用，内部改为“新增 + 版本升级”
    return _sync_builtin_recipes(recipes_data)


def get_all_recipe_tags(recipes_data: dict) -> list[str]:
    tags: set[str] = set()
    for recipe in recipes_data.values():
        if not isinstance(recipe, dict):
            continue
        for tag in recipe.get("tags", []):
            t = _as_clean_str(tag)
            if t:
                tags.add(t)
    return sorted(tags)


def load_recipes():
    recipes_data = _call_backend("load_recipes")
    if not isinstance(recipes_data, dict):
        return recipes_data

    recipes_data, changed_meta = _ensure_recipe_meta(recipes_data)
    recipes_data, changed_builtin = _merge_builtin_recipes(recipes_data)
    if changed_meta or changed_builtin:
        _call_backend("save_recipes", recipes_data)
    return recipes_data


def save_recipes(recipes):
    _call_backend("save_recipes", recipes)


def load_records():
    return _call_backend("load_records")


def save_records(records):
    _call_backend("save_records", records)


def load_ingredients():
    return _call_backend("load_ingredients")


def save_ingredients(ingredients):
    _call_backend("save_ingredients", ingredients)


def load_accounts():
    return _call_backend("load_accounts")


def save_accounts(accounts):
    _call_backend("save_accounts", accounts)


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _default_share_settings() -> dict:
    return {"recipes": False, "records": False, "ingredients": False}


def _hash_password(password: str, salt_hex: str | None = None) -> str:
    salt_hex = salt_hex or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_hex.encode("utf-8"),
        200_000,
    ).hex()
    return f"pbkdf2_sha256${salt_hex}${digest}"


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        algo, salt_hex, digest = password_hash.split("$", 2)
    except Exception:
        return False
    if algo != "pbkdf2_sha256":
        return False
    expected = _hash_password(password, salt_hex=salt_hex).split("$", 2)[2]
    return hmac.compare_digest(expected, digest)


def _normalize_account(account: dict) -> dict:
    data = dict(account)
    data["username"] = _as_clean_str(data.get("username")).lower()
    data["real_name"] = _as_clean_str(data.get("real_name"))
    data["phone"] = _as_clean_str(data.get("phone"))
    data["is_admin"] = bool(data.get("is_admin", False))
    data["approved"] = bool(data.get("approved", False))
    data["status"] = _as_clean_str(data.get("status") or ("active" if data["approved"] else "pending")) or "pending"
    shares = data.get("share_settings") or {}
    default_shares = _default_share_settings()
    default_shares.update({k: bool(v) for k, v in shares.items() if k in default_shares})
    data["share_settings"] = default_shares
    data["password_hash"] = _as_clean_str(data.get("password_hash"))
    data["created_at"] = _as_clean_str(data.get("created_at") or _now_str())
    data["updated_at"] = _as_clean_str(data.get("updated_at") or _now_str())
    return data


def _get_admin_seed() -> tuple[str, str]:
    admin_username = _read_setting("ADMIN_USERNAME", "admin").lower()
    admin_password = _read_setting("ADMIN_PASSWORD", "admin123456")
    return admin_username or "admin", admin_password


def ensure_admin_account() -> list:
    """
    确保至少存在一个管理员账号。
    首次自动创建 admin（密码来自 ADMIN_PASSWORD，默认 admin123456）。
    """
    accounts = [_normalize_account(a) for a in load_accounts()]
    admin_username, admin_password = _get_admin_seed()
    changed = False

    if not accounts:
        accounts.append(
            _normalize_account(
                {
                    "username": admin_username,
                    "real_name": "管理员",
                    "phone": "",
                    "password_hash": _hash_password(admin_password),
                    "is_admin": True,
                    "approved": True,
                    "status": "active",
                    "share_settings": {
                        "recipes": True,
                        "records": True,
                        "ingredients": True,
                    },
                    "created_at": _now_str(),
                    "updated_at": _now_str(),
                }
            )
        )
        changed = True

    if not any(a.get("is_admin") for a in accounts):
        accounts[0]["is_admin"] = True
        accounts[0]["approved"] = True
        accounts[0]["status"] = "active"
        changed = True

    if changed:
        save_accounts(accounts)
    return accounts


def find_account(accounts: list, username: str) -> dict | None:
    key = _as_clean_str(username).lower()
    for account in accounts:
        if _as_clean_str(account.get("username")).lower() == key:
            return account
    return None


def is_admin(accounts: list, username: str) -> bool:
    account = find_account(accounts, username)
    return bool(account and account.get("is_admin"))


def register_account(username: str, password: str, real_name: str, phone: str) -> tuple[bool, str]:
    accounts = [_normalize_account(a) for a in load_accounts()]
    username = _as_clean_str(username).lower()
    if len(username) < 3:
        return False, "账户名称至少 3 个字符。"
    if len(password) < 6:
        return False, "密码至少 6 位。"
    if not real_name.strip():
        return False, "真实姓名不能为空。"
    if find_account(accounts, username):
        return False, "该账户名称已存在。"

    accounts.append(
        _normalize_account(
            {
                "username": username,
                "real_name": real_name.strip(),
                "phone": phone.strip(),
                "password_hash": _hash_password(password),
                "is_admin": False,
                "approved": False,
                "status": "pending",
                "share_settings": _default_share_settings(),
                "created_at": _now_str(),
                "updated_at": _now_str(),
            }
        )
    )
    save_accounts(accounts)
    return True, "注册成功，等待管理员审核通过。"


def authenticate(username: str, password: str) -> tuple[bool, str, dict | None]:
    accounts = [_normalize_account(a) for a in load_accounts()]
    account = find_account(accounts, username)
    if not account:
        return False, "账号不存在。", None
    if not _verify_password(password, account.get("password_hash", "")):
        return False, "密码错误。", None
    if not account.get("approved"):
        return False, "账号尚未通过管理员审核。", None
    return True, "登录成功。", account


def set_account_status(username: str, approved: bool, actor_username: str) -> tuple[bool, str]:
    accounts = [_normalize_account(a) for a in load_accounts()]
    if not is_admin(accounts, actor_username):
        return False, "仅管理员可审核账号。"
    account = find_account(accounts, username)
    if not account:
        return False, "账号不存在。"
    account["approved"] = bool(approved)
    account["status"] = "active" if approved else "rejected"
    account["updated_at"] = _now_str()
    save_accounts(accounts)
    return True, "已更新账号状态。"


def update_account_profile(
    actor_username: str,
    target_username: str,
    new_username: str,
    real_name: str,
    phone: str,
    password: str,
    share_settings: dict | None = None,
) -> tuple[bool, str]:
    accounts = [_normalize_account(a) for a in load_accounts()]
    actor = find_account(accounts, actor_username)
    target = find_account(accounts, target_username)
    if not actor or not target:
        return False, "账号不存在。"

    actor_is_admin = bool(actor.get("is_admin"))
    if actor_username != target_username and not actor_is_admin:
        return False, "只能修改自己的资料。"

    final_username = _as_clean_str(new_username).lower() or target_username
    if len(final_username) < 3:
        return False, "账户名称至少 3 个字符。"
    exists = find_account(accounts, final_username)
    if exists and exists is not target:
        return False, "新的账户名称已存在。"

    old_username = target["username"]
    target["username"] = final_username
    target["real_name"] = real_name.strip()
    target["phone"] = phone.strip()
    if password.strip():
        target["password_hash"] = _hash_password(password.strip())

    if share_settings is not None:
        current = target.get("share_settings") or _default_share_settings()
        for key in _default_share_settings():
            if key in share_settings:
                current[key] = bool(share_settings[key])
        target["share_settings"] = current

    target["updated_at"] = _now_str()
    save_accounts(accounts)

    if final_username != old_username:
        all_recipes = load_recipes()
        recipes_changed = False
        for recipe in all_recipes.values():
            if _as_clean_str(recipe.get("owner")).lower() == old_username:
                recipe["owner"] = final_username
                recipes_changed = True
        if recipes_changed:
            save_recipes(all_recipes)

        all_records = load_records()
        records_changed = False
        for record in all_records:
            if _as_clean_str(record.get("owner")).lower() == old_username:
                record["owner"] = final_username
                records_changed = True
        if records_changed:
            save_records(all_records)

        all_ingredients = load_ingredients()
        ingredients_changed = False
        for ing in all_ingredients:
            if _as_clean_str(ing.get("owner")).lower() == old_username:
                ing["owner"] = final_username
                ingredients_changed = True
        if ingredients_changed:
            save_ingredients(all_ingredients)

    return True, "资料已更新。"


def _owner_name(item: dict, default_owner: str) -> str:
    owner = _as_clean_str(item.get("owner"))
    return owner or default_owner


def migrate_data_owners(default_owner: str = "admin"):
    """
    为历史数据补 owner 字段，保证共享和权限逻辑可用。
    """
    changed = False
    current_recipes = load_recipes()
    for name, recipe in current_recipes.items():
        if not isinstance(recipe, dict):
            continue
        if not _as_clean_str(recipe.get("owner")):
            recipe["owner"] = default_owner
            changed = True
    if changed:
        save_recipes(current_recipes)

    current_records = load_records()
    records_changed = False
    for record in current_records:
        if not _as_clean_str(record.get("owner")):
            record["owner"] = default_owner
            records_changed = True
    if records_changed:
        save_records(current_records)

    current_ingredients = load_ingredients()
    ingredients_changed = False
    for ing in current_ingredients:
        if not _as_clean_str(ing.get("owner")):
            ing["owner"] = default_owner
            ingredients_changed = True
    if ingredients_changed:
        save_ingredients(current_ingredients)


def can_view_owner_data(accounts: list, owner: str, data_type: str) -> bool:
    account = find_account(accounts, owner)
    if not account:
        return True
    shares = account.get("share_settings") or {}
    return bool(shares.get(data_type, False))


def can_edit_owner_data(accounts: list, actor_username: str, owner: str) -> bool:
    if actor_username == owner:
        return True
    return is_admin(accounts, actor_username)


def get_visible_recipes(recipes_data: dict, accounts: list, current_user: str) -> dict:
    if is_admin(accounts, current_user):
        return recipes_data
    visible = {}
    for name, recipe in recipes_data.items():
        owner = _owner_name(recipe if isinstance(recipe, dict) else {}, "admin")
        if owner == current_user or can_view_owner_data(accounts, owner, "recipes"):
            visible[name] = recipe
    return visible


def get_visible_records(records_data: list, accounts: list, current_user: str) -> list:
    if is_admin(accounts, current_user):
        return records_data
    visible = []
    for record in records_data:
        owner = _owner_name(record, "admin")
        if owner == current_user or can_view_owner_data(accounts, owner, "records"):
            visible.append(record)
    return visible


def get_visible_ingredients(ingredients_data: list, accounts: list, current_user: str) -> list:
    if is_admin(accounts, current_user):
        return ingredients_data
    visible = []
    for ing in ingredients_data:
        owner = _owner_name(ing, "admin")
        if owner == current_user or can_view_owner_data(accounts, owner, "ingredients"):
            visible.append(ing)
    return visible


# -------------------- 模块级数据加载 --------------------
recipes = load_recipes()
records = load_records()
ingredients = load_ingredients()
accounts = load_accounts() if hasattr(_backend, "load_accounts") else []
