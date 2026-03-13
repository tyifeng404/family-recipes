"""
config.py —— 项目配置模块

集中管理所有路径常量、默认菜谱数据和照片格式白名单。
其他模块通过 `from config import ...` 获取配置，避免硬编码散落各处。
"""

import os  # 用于路径拼接和获取文件所在目录

from builtin_recipes import BUILTIN_RECIPES

# -------------------- 路径常量 --------------------

# 获取当前脚本所在的目录，作为项目根目录
# os.path.abspath(__file__) 返回本文件的绝对路径
# os.path.dirname(...) 取其所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 菜谱数据文件的完整路径（存储所有菜谱的 JSON 文件）
DATA_FILE = os.path.join(BASE_DIR, "recipes.json")

# 做菜记录数据文件的完整路径（存储所有实践记录的 JSON 文件）
RECORDS_FILE = os.path.join(BASE_DIR, "records.json")

# 照片存储目录，每条记录的照片存放在 photos/<record_id>/ 子目录下
PHOTOS_DIR = os.path.join(BASE_DIR, "photos")

# 可用食材数据文件的完整路径
INGREDIENTS_FILE = os.path.join(BASE_DIR, "ingredients.json")

# 账号数据文件的完整路径
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")

# -------------------- 默认菜谱 --------------------

# 程序首次运行时，如果 recipes.json 不存在，则用此字典初始化
# 键 = 菜名（str），值 = dict，包含 steps（步骤列表）和 ingredients（主要食材列表）
DEFAULT_RECIPES = BUILTIN_RECIPES

# -------------------- 照片格式白名单 --------------------

# 导入照片时只接受以下扩展名（全小写），用集合便于 O(1) 查找
PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".webp", ".gif", ".bmp", ".tiff"}
