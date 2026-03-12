"""
将本地 JSON 数据一次性迁移到 Supabase。

用法:
  1) 先在 Supabase 执行 scripts/supabase_init.sql
  2) 设置环境变量:
       export SUPABASE_URL=...
       export SUPABASE_SERVICE_ROLE_KEY=...   # 或 SUPABASE_ANON_KEY
       export SUPABASE_STATE_TABLE=app_state  # 可选
  3) 运行:
       python3 scripts/migrate_local_to_supabase.py
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storage_backends import LocalJsonBackend, SupabaseStateBackend


def main():
    url = os.getenv("SUPABASE_URL", "").strip()
    key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.getenv("SUPABASE_ANON_KEY", "").strip()
    )
    table = os.getenv("SUPABASE_STATE_TABLE", "app_state").strip() or "app_state"

    if not url or not key:
        raise RuntimeError(
            "缺少 SUPABASE_URL 或 SUPABASE_SERVICE_ROLE_KEY / SUPABASE_ANON_KEY"
        )

    local_backend = LocalJsonBackend()
    cloud_backend = SupabaseStateBackend(url=url, key=key, table=table)

    recipes = local_backend.load_recipes()
    records = local_backend.load_records()
    ingredients = local_backend.load_ingredients()

    cloud_backend.save_recipes(recipes)
    cloud_backend.save_records(records)
    cloud_backend.save_ingredients(ingredients)

    print("迁移完成：")
    print(f"- recipes: {len(recipes)}")
    print(f"- records: {len(records)}")
    print(f"- ingredients: {len(ingredients)}")
    print(f"- table: {table}")


if __name__ == "__main__":
    main()
