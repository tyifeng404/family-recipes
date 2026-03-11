"""
config.py —— 项目配置模块

集中管理所有路径常量、默认菜谱数据和照片格式白名单。
其他模块通过 `from config import ...` 获取配置，避免硬编码散落各处。
"""

import os  # 用于路径拼接和获取文件所在目录

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

# -------------------- 默认菜谱 --------------------

# 程序首次运行时，如果 recipes.json 不存在，则用此字典初始化
# 键 = 菜名（str），值 = dict，包含 steps（步骤列表）和 ingredients（主要食材列表）
DEFAULT_RECIPES = {
    "番茄炒蛋": {
        "steps": [
            "1. 鸡蛋打散，加少许盐搅匀",
            "2. 番茄切块备用",
            "3. 热锅凉油，倒入蛋液炒至凝固后盛出",
            "4. 锅中再加少许油，放入番茄块翻炒出汁",
            "5. 加入适量盐和糖调味",
            "6. 倒回鸡蛋，翻炒均匀即可出锅",
        ],
        "ingredients": ["番茄", "鸡蛋"],
    },
    "南瓜馒头": {
        "steps": [
            "1. 南瓜去皮切片，上锅蒸熟后压成泥",
            "2. 南瓜泥放凉至温热，加入酵母粉搅匀",
            "3. 倒入面粉，边加边搅拌，揉成光滑面团",
            "4. 盖上湿布，温暖处发酵至两倍大",
            "5. 取出面团排气，分成小剂子，揉圆整形",
            "6. 放入蒸笼，二次醒发 15 分钟",
            "7. 大火烧开后转中火蒸 15 分钟，关火焖 3 分钟再揭盖",
        ],
        "ingredients": ["南瓜", "面粉", "酵母粉"],
    },
}

# -------------------- 照片格式白名单 --------------------

# 导入照片时只接受以下扩展名（全小写），用集合便于 O(1) 查找
PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".webp", ".gif", ".bmp", ".tiff"}
