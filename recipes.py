"""
recipes.py —— 菜谱管理模块

提供菜谱的五个核心操作：
  - show_recipe:   查看某道菜的做法
  - add_recipe:    查询菜名不存在时，引导用户添加
  - update_recipe: 在原有步骤基础上逐步编辑（预填充）
  - import_recipe: 批量导入新菜谱
  - delete_recipe: 按菜名或序号删除菜谱

菜谱数据格式为 {name: {"steps": [...], "ingredients": [...]}}
"""

import re

import storage
from helpers import input_with_prefill, input_steps


def _parse_ingredients(text):
    """将逗号/顿号/空格分隔的食材文本解析为列表。"""
    if not text:
        return []
    parts = re.split(r"[,，、\s]+", text.strip())
    return [p for p in parts if p]


def show_recipe(name):
    """在终端打印指定菜谱的食材和步骤。"""
    recipe = storage.recipes[name]
    steps = recipe["steps"]
    ingredients = recipe.get("ingredients", [])

    print(f"\n「{name}」的做法：")
    if ingredients:
        print(f"  主要食材：{'、'.join(ingredients)}")
    for step in steps:
        print(f"  {step}")


def add_recipe(name):
    """当用户查询的菜名不存在时调用，询问是否添加新菜谱。"""
    choice = input(f"\n没有找到「{name}」的做法，是否要添加？(y/n): ").strip().lower()
    if choice != "y":
        print("好的，已取消。")
        return

    ing_text = input("请输入主要食材（用逗号或顿号分隔，直接回车跳过）: ").strip()
    ingredients = _parse_ingredients(ing_text)

    steps = input_steps(name)
    if steps:
        storage.recipes[name] = {"steps": steps, "ingredients": ingredients}
        storage.save_recipes(storage.recipes)
        print(f"已成功添加「{name}」！")
    else:
        print("未输入任何步骤，添加取消。")


def update_recipe(name):
    """更新已有菜谱：可修改主要食材和逐步编辑做法步骤。"""
    choice = input("\n是否需要更新这道菜的做法？(yes/no): ").strip().lower()
    if choice != "yes":
        return

    recipe = storage.recipes[name]
    old_steps = recipe["steps"]
    old_ingredients = recipe.get("ingredients", [])

    # 编辑主要食材
    ing_prefill = "、".join(old_ingredients)
    new_ing_text = input_with_prefill("  主要食材（用逗号或顿号分隔）: ", ing_prefill).strip()
    new_ingredients = _parse_ingredients(new_ing_text)

    # 从每个步骤中提取纯内容（去掉序号前缀），用于预填充
    old_contents = []
    for s in old_steps:
        dot_pos = s.find(". ")
        old_contents.append(s[dot_pos + 2 :] if dot_pos != -1 else s)

    print(f"\n逐步编辑「{name}」（可直接修改预填内容，清空整行则删除该步）：")
    new_steps = []
    step_num = 1

    for i, content in enumerate(old_contents):
        line = input_with_prefill(f"  第 {i + 1} 步: ", content).strip()
        if not line:
            continue
        new_steps.append(f"{step_num}. {line}")
        step_num += 1

    print("继续添加新步骤（输入空行结束）：")
    while True:
        line = input(f"  第 {step_num} 步: ").strip()
        if not line:
            break
        new_steps.append(f"{step_num}. {line}")
        step_num += 1

    if new_steps:
        storage.recipes[name] = {"steps": new_steps, "ingredients": new_ingredients}
        storage.save_recipes(storage.recipes)
        print(f"「{name}」的做法已更新！")
    else:
        print("所有步骤已被删除，更新取消。")


def import_recipe():
    """导入新菜谱模块：循环输入菜名、食材和步骤，直到用户输入空行返回。"""
    print("\n----- 导入新菜谱 -----")
    while True:
        name = input("请输入菜名（输入空行返回首页）: ").strip()
        if not name:
            break

        if name in storage.recipes:
            print(f"「{name}」已存在，如需修改请从首页进入。")
            continue

        ing_text = input("请输入主要食材（用逗号或顿号分隔，直接回车跳过）: ").strip()
        ingredients = _parse_ingredients(ing_text)

        steps = input_steps(name)
        if steps:
            storage.recipes[name] = {"steps": steps, "ingredients": ingredients}
            storage.save_recipes(storage.recipes)
            print(f"已成功导入「{name}」！")
        else:
            print("未输入任何步骤，导入取消。")


def delete_recipe():
    """删除菜谱：列出所有菜谱，支持按菜名或序号选择，删除前需二次确认。"""
    print("\n----- 删除菜谱 -----")
    recipes = storage.recipes

    if not recipes:
        print("当前没有任何菜谱。")
        return

    for i, name in enumerate(recipes, 1):
        print(f"  {i}. {name}")

    choice = input("\n请输入要删除的菜名或序号（输入空行取消）: ").strip()
    if not choice:
        print("已取消。")
        return

    if choice.isdigit():
        idx = int(choice) - 1
        names = list(recipes)
        if 0 <= idx < len(names):
            name = names[idx]
        else:
            print("序号无效。")
            return
    elif choice in recipes:
        name = choice
    else:
        print(f"未找到「{choice}」。")
        return

    confirm = input(f"确认删除「{name}」？此操作不可撤销 (y/n): ").strip().lower()
    if confirm == "y":
        del recipes[name]
        storage.save_recipes(recipes)
        print(f"「{name}」已删除。")
    else:
        print("已取消。")
