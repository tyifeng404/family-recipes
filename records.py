"""
records.py —— 做菜记录模块

管理做菜实践记录的完整生命周期：
  - new_record:     新建记录（选菜谱 → 逐步备注 → 整体备注 → 导入照片 → 保存）
  - show_record:    展示单条记录详情
  - edit_record:    编辑记录中的备注（预填充原内容）
  - delete_record:  删除记录并清理关联照片
  - manage_photos:  追加 / 删除照片
  - import_photos:  从文件路径导入照片到项目目录
  - list_records:   列出所有历史记录
  - record_menu:    做菜记录子菜单入口
"""

import os      # 文件路径操作、目录创建、文件删除
import shutil  # 高级文件操作（复制照片）
from datetime import datetime  # 生成时间戳

# 项目配置：路径常量和照片格式白名单
from config import BASE_DIR, PHOTOS_DIR, PHOTO_EXTS
# 共享数据和持久化
import storage
# 输入工具：预填充编辑、选菜辅助
from helpers import input_with_prefill, pick_recipe


# ==================== 照片管理 ====================


def import_photos(record_id):
    """
    逐条导入照片：用户输入文件路径，程序验证后复制到 photos/<record_id>/ 目录下。

    参数:
        record_id: str —— 记录的唯一 ID，用作照片子目录名

    返回值:
        list[str] —— 已保存照片的相对路径列表（相对于项目根目录）
    """
    # 照片存放的目标目录
    dest_dir = os.path.join(PHOTOS_DIR, record_id)
    saved = []  # 收集成功保存的照片相对路径
    print("逐条输入照片路径（可从 Finder 拖入），输入空行结束：")
    idx = 1     # 照片编号，用于生成文件名
    while True:
        # 读取路径，strip("'\"") 去除 Finder 拖入时可能带上的引号
        path = input(f"  照片 {idx}: ").strip().strip("'\"")
        # 空行结束输入
        if not path:
            break
        # 检查文件是否存在
        if not os.path.isfile(path):
            print(f"    文件不存在：{path}")
            continue
        # 提取扩展名并转为小写
        ext = os.path.splitext(path)[1].lower()
        # 检查是否为支持的图片格式
        if ext not in PHOTO_EXTS:
            print(f"    不支持的格式（{ext}），支持：{', '.join(sorted(PHOTO_EXTS))}")
            continue
        # 创建目标目录（如果不存在的话），exist_ok=True 避免重复创建报错
        os.makedirs(dest_dir, exist_ok=True)
        # 用编号 + 原扩展名作为新文件名（如 1.jpg, 2.png）
        dest_name = f"{idx}{ext}"
        dest_path = os.path.join(dest_dir, dest_name)
        # copy2 会同时复制文件内容和元数据（修改时间等）
        shutil.copy2(path, dest_path)
        # 记录相对路径，便于 JSON 存储和跨目录访问
        rel_path = os.path.join("photos", record_id, dest_name)
        saved.append(rel_path)
        print(f"    已保存：{dest_name}")
        idx += 1
    return saved


def manage_photos(idx):
    """
    管理指定记录的照片：追加新照片或删除已有照片。

    参数:
        idx: int —— 记录在 storage.records 列表中的索引
    """
    record = storage.records[idx]
    # 获取记录 ID，旧记录可能没有 id 字段，用 legacy_<idx> 作为兜底
    record_id = record.get("id", f"legacy_{idx}")
    # 获取当前照片列表，旧记录可能没有 photos 字段
    photos = record.get("photos", [])

    while True:
        print(f"\n--- 照片管理（当前 {len(photos)} 张）---")
        # 列出现有照片（只显示文件名）
        for i, p in enumerate(photos, 1):
            print(f"  [{i}] {os.path.basename(p)}")
        print()
        print("  [a] 追加照片  [d] 删除照片  [b] 返回")
        action = input("请选择: ").strip().lower()

        if action == "a":
            # 追加新照片
            new_photos = import_photos(record_id)
            if new_photos:
                # 将新照片路径追加到列表
                photos.extend(new_photos)
                record["photos"] = photos
                # 立即保存
                storage.save_records(storage.records)
                print(f"已追加 {len(new_photos)} 张照片。")
        elif action == "d":
            if not photos:
                print("没有可删除的照片。")
                continue
            # 按序号删除
            num = input("输入要删除的照片序号: ").strip()
            if num.isdigit() and 1 <= int(num) <= len(photos):
                # 从列表中弹出被删除的照片路径
                removed = photos.pop(int(num) - 1)
                # 拼接完整路径并删除实际文件
                full_path = os.path.join(BASE_DIR, removed)
                if os.path.isfile(full_path):
                    os.remove(full_path)
                record["photos"] = photos
                storage.save_records(storage.records)
                print(f"已删除：{os.path.basename(removed)}")
            else:
                print("序号无效。")
        elif action == "b":
            # 返回上一级菜单
            break


# ==================== 记录 CRUD ====================


def new_record():
    """
    新建做菜记录的完整流程：
    选择菜谱 → 逐步添加备注 → 输入整体备注 → 可选导入照片 → 保存。
    """
    print("\n--- 新建做菜记录 ---")
    # 让用户从菜谱列表中选择一道菜
    name = pick_recipe("请输入菜名或序号（空行取消）: ")
    if not name:
        return

    # 获取该菜谱的步骤列表
    recipe_data = storage.recipes[name]
    steps = recipe_data["steps"]
    print(f"\n为「{name}」的每一步添加备注（直接回车跳过该步）：")
    step_notes = []  # 收集每步的备注
    for step in steps:
        # 先显示当前步骤内容
        print(f"  {step}")
        # 等待用户输入备注，空行表示不备注
        note = input("    备注: ").strip()
        step_notes.append(note)

    # 整体备注
    print()
    overall = input("整体备注（直接回车跳过）: ").strip()

    # 用当前时间戳生成唯一记录 ID（精确到秒）
    record_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 询问是否导入照片
    print()
    add_photo = input("是否导入照片？(y/n): ").strip().lower()
    photos = import_photos(record_id) if add_photo == "y" else []

    # 组装记录字典
    record = {
        "id": record_id,                                     # 唯一标识
        "name": name,                                        # 菜名
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),   # 可读日期
        "steps": [                                           # 步骤 + 备注列表
            {"text": step, "note": note}
            for step, note in zip(steps, step_notes)
        ],
        "note": overall,                                     # 整体备注
        "photos": photos,                                    # 照片路径列表
    }
    # 追加到全局记录列表并持久化
    storage.records.append(record)
    storage.save_records(storage.records)
    print(f"「{name}」的做菜记录已保存！（含 {len(photos)} 张照片）")


def show_record(record, idx):
    """
    在终端打印一条记录的完整详情。

    参数:
        record: dict —— 单条记录字典
        idx:    int  —— 记录在列表中的索引（用于显示编号）
    """
    print(f"\n===== 记录 #{idx + 1} =====")
    print(f"  菜名：{record['name']}")
    print(f"  日期：{record['date']}")
    # 打印每个步骤及其备注
    print("  步骤与备注：")
    for s in record["steps"]:
        print(f"    {s['text']}")
        # 有备注时用箭头标识
        if s["note"]:
            print(f"      → {s['note']}")
    # 整体备注
    if record["note"]:
        print(f"  整体备注：{record['note']}")
    else:
        print("  整体备注：（无）")
    # 照片列表
    photos = record.get("photos", [])
    if photos:
        print(f"  照片（{len(photos)} 张）：")
        for i, p in enumerate(photos, 1):
            # 检查照片文件是否实际存在
            full = os.path.join(BASE_DIR, p)
            exists = "✓" if os.path.isfile(full) else "✗ 文件缺失"
            print(f"    [{i}] {p}  ({exists})")
    else:
        print("  照片：（无）")


def edit_record(idx):
    """
    编辑记录中的备注内容（步骤备注 + 整体备注），使用预填充方便修改。

    参数:
        idx: int —— 记录在 storage.records 列表中的索引
    """
    record = storage.records[idx]
    print(f"\n编辑记录 #{idx + 1}「{record['name']}」的备注（可直接修改预填内容，清空则删除备注）：")

    # 逐步编辑备注
    for s in record["steps"]:
        # 显示步骤原文
        print(f"  {s['text']}")
        # 用 input_with_prefill 预填充原备注，用户可直接修改
        s["note"] = input_with_prefill("    备注: ", s["note"]).strip()

    # 编辑整体备注
    record["note"] = input_with_prefill("\n整体备注: ", record["note"]).strip()

    # 保存修改
    storage.save_records(storage.records)
    print("记录已更新！")


def delete_record(idx):
    """
    删除一条做菜记录，同时清理其关联的照片文件。

    参数:
        idx: int —— 记录在 storage.records 列表中的索引
    """
    record = storage.records[idx]
    photos = record.get("photos", [])
    # 确认提示中包含照片数量信息
    photo_hint = f"，含 {len(photos)} 张照片" if photos else ""
    confirm = input(
        f"确认删除「{record['name']}」({record['date']}) 的记录{photo_hint}？(y/n): "
    ).strip().lower()

    if confirm == "y":
        # 逐个删除照片文件
        for p in photos:
            full_path = os.path.join(BASE_DIR, p)
            if os.path.isfile(full_path):
                os.remove(full_path)
        # 如果照片子目录已空，也一并删除
        record_id = record.get("id")
        if record_id:
            photo_dir = os.path.join(PHOTOS_DIR, record_id)
            if os.path.isdir(photo_dir) and not os.listdir(photo_dir):
                os.rmdir(photo_dir)
        # 从列表中移除记录
        storage.records.pop(idx)
        # 持久化
        storage.save_records(storage.records)
        print("记录已删除。")
    else:
        print("已取消。")


# ==================== 记录列表与子菜单 ====================


def list_records():
    """
    列出所有历史做菜记录，选中后可查看详情并进行编辑/照片管理/删除操作。
    """
    if not storage.records:
        print("\n暂无做菜记录。")
        return

    print("\n--- 历史做菜记录 ---")
    for i, r in enumerate(storage.records):
        # 统计有备注的步骤数量
        notes_count = sum(1 for s in r["steps"] if s["note"])
        print(f"  {i + 1}. [{r['date']}] {r['name']}（{notes_count} 条步骤备注）")

    # 选择一条记录查看
    choice = input("\n输入序号查看详情（空行返回）: ").strip()
    if not choice or not choice.isdigit():
        return

    idx = int(choice) - 1
    if not (0 <= idx < len(storage.records)):
        print("序号无效。")
        return

    # 显示详情
    show_record(storage.records[idx], idx)
    # 提供操作选项
    action = input("\n操作：[e] 编辑备注  [p] 管理照片  [x] 删除记录  其他返回: ").strip().lower()
    if action == "e":
        edit_record(idx)
    elif action == "p":
        manage_photos(idx)
    elif action == "x":
        delete_record(idx)


def record_menu():
    """
    做菜记录的子菜单循环，提供新建记录和查看历史两个入口。
    输入 'b' 返回主菜单。
    """
    while True:
        print("\n===== 做菜记录 =====")
        print("  [1] 新建做菜记录")
        print("  [2] 查看历史记录")
        print("  [b] 返回首页")
        print("=" * 20)
        choice = input("\n请选择: ").strip().lower()
        if choice == "1":
            new_record()
        elif choice == "2":
            list_records()
        elif choice == "b":
            break
        else:
            print("无效选项，请重新选择。")
