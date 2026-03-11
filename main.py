"""
main.py —— 程序入口模块

包含主菜单显示和主循环，是用户与程序交互的顶层控制器。
根据用户输入分发到各功能模块（菜谱管理、做菜记录）。

运行方式: python3 main.py
"""

# 导入共享数据，用于在主菜单中显示菜谱列表
import storage
# 导入菜谱管理的五个操作函数
from recipes import show_recipe, add_recipe, update_recipe, import_recipe, delete_recipe
# 导入做菜记录的子菜单入口
from records import record_menu


def show_menu():
    """
    打印主菜单：列出所有已收录的菜品，以及可用的快捷操作。
    每次主循环迭代开始时调用。
    """
    print("\n===== 家庭食谱 =====")
    print("当前收录的菜品：")
    # 用 enumerate 从 1 开始编号，遍历菜谱字典的键（菜名）
    for i, name in enumerate(storage.recipes, 1):
        print(f"  {i}. {name}")
    # 分隔线之下是操作选项
    print("-" * 20)
    print("  [a] 导入新菜谱")
    print("  [d] 删除菜谱")
    print("  [r] 做菜记录")
    print("  [q] 退出程序")
    print("=" * 20)


def main():
    """
    主循环：反复显示菜单、读取用户输入、分发到对应功能。
    输入 'q' 退出程序。
    """
    while True:
        # 每次循环开头刷新菜单（菜谱可能已被增删改）
        show_menu()
        # 读取用户输入，strip() 去除首尾空白
        query = input("\n请输入菜名或选项: ").strip()

        # ---- 快捷操作 ----

        # 退出程序
        if query.lower() == "q":
            print("再见，祝你做饭愉快！")
            break

        # 进入导入新菜谱模式
        if query.lower() == "a":
            import_recipe()
            continue

        # 进入删除菜谱模式
        if query.lower() == "d":
            delete_recipe()
            continue

        # 进入做菜记录子菜单
        if query.lower() == "r":
            record_menu()
            continue

        # 空输入，跳过本次循环
        if not query:
            continue

        # ---- 菜名查询 ----

        if query in storage.recipes:
            # 菜名存在：先展示做法，再询问是否更新
            show_recipe(query)
            update_recipe(query)
        else:
            # 菜名不存在：询问是否添加
            add_recipe(query)


# 仅当直接运行本文件时才启动主循环（被 import 时不会执行）
if __name__ == "__main__":
    main()
