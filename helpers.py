"""
helpers.py —— 通用输入工具模块

提供三个在终端中反复使用的输入辅助函数：
  - input_with_prefill: 带预填充文本的 input，方便用户在原文上编辑
  - input_steps: 逐行输入菜谱步骤
  - pick_recipe: 从菜谱列表中选择一道菜
"""

# macOS 自带的 readline 底层是 libedit，insert_text 在 hook 中不生效，
# 因此优先导入 gnureadline（真正的 GNU readline），不可用时回退到系统自带版本
try:
    import gnureadline as readline  # type: ignore[import-not-found]
except ImportError:
    import readline

# 导入全局菜谱数据，pick_recipe 需要用它来显示列表和验证输入
import storage


def input_with_prefill(prompt, prefill=""):
    """
    带预填充文本的输入函数。

    参数:
        prompt:  str —— 输入提示语（如 "  第 1 步: "）
        prefill: str —— 预填充到输入行的文本，用户可直接用方向键编辑

    返回值:
        str —— 用户编辑后按回车确认的文本

    原理:
        利用 readline 的 startup_hook 机制，在每次 input() 调用前
        将 prefill 文本插入到输入缓冲区，实现"带默认值的可编辑输入"。
    """
    def hook():
        # 将预填充文本写入 readline 的行缓冲区
        readline.insert_text(prefill)
        # 强制刷新显示，确保用户能看到预填充的文本
        readline.redisplay()

    # 注册 startup hook，它会在下一次 input() 等待输入前被调用一次
    readline.set_startup_hook(hook)
    try:
        # 调用内置 input()，此时 hook 已将 prefill 填入，用户看到预填充文本
        return input(prompt)
    finally:
        # 无论是否异常，都必须清除 hook，否则后续普通 input() 也会被影响
        readline.set_startup_hook()


def input_steps(name):
    """
    逐行输入菜谱步骤，直到用户输入空行为止。

    参数:
        name: str —— 菜名，用于提示语显示

    返回值:
        list[str] —— 步骤列表，每条格式为 "序号. 内容"
    """
    print(f"请逐行输入「{name}」的步骤（输入空行结束）：")
    steps = []       # 存放最终的步骤列表
    step_num = 1     # 当前步骤序号，从 1 开始递增
    while True:
        # 提示用户输入当前步骤，strip() 去除首尾空白
        line = input(f"  第 {step_num} 步: ").strip()
        # 空行表示输入结束
        if not line:
            break
        # 将序号和内容拼接后加入列表
        steps.append(f"{step_num}. {line}")
        step_num += 1
    return steps


def pick_recipe(prompt):
    """
    显示菜谱列表并让用户选择一道菜。支持按序号或菜名选择。

    参数:
        prompt: str —— 输入提示语

    返回值:
        str | None —— 选中的菜名，取消或无效输入返回 None
    """
    # 引用全局菜谱数据
    recipes = storage.recipes
    # 如果菜谱为空，直接提示并返回
    if not recipes:
        print("当前没有任何菜谱。")
        return None
    # 列出所有菜谱，enumerate 从 1 开始编号
    for i, name in enumerate(recipes, 1):
        print(f"  {i}. {name}")
    # 等待用户输入
    choice = input(prompt).strip()
    # 空输入表示取消
    if not choice:
        return None
    # 如果输入的是纯数字，按序号查找
    if choice.isdigit():
        idx = int(choice) - 1          # 转为 0 基索引
        names = list(recipes)          # dict 的键转为列表以支持索引访问
        if 0 <= idx < len(names):
            return names[idx]          # 返回对应菜名
        print("序号无效。")
        return None
    # 如果输入的是菜名且存在于菜谱中，直接返回
    if choice in recipes:
        return choice
    # 都不匹配，提示未找到
    print(f"未找到「{choice}」。")
    return None
