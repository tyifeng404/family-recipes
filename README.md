# 家庭食谱（CLI + Web）

一个家庭菜谱管理项目，支持两种使用方式：

- 命令行版：快速维护菜谱与做菜记录
- Web 版（Streamlit）：图形化管理菜谱、食材、照片与推荐

## 功能概览

### 1) 菜谱管理

- 新增、查看、修改、删除菜谱
- 菜谱包含「步骤 + 主要食材」
- 支持从旧格式自动迁移（`{菜名: [步骤]}` -> 新格式）

### 2) 做菜记录

- 按菜谱创建一次做菜记录
- 对每一步添加备注，支持整体备注
- 支持拍照/上传照片并与记录关联
- 支持编辑备注、删除记录、自动清理关联照片

### 3) 可用食材管理与推荐（Web）

- 维护当前可用食材（名称 + 购买日期）
- 根据食材自动推荐可做菜谱（完全匹配/部分匹配）
- 提供每日推荐（优先食材匹配，不足时随机推荐）

## 技术栈

- Python 3.10+
- Streamlit（Web 界面）
- JSON 文件持久化（无数据库）

## 目录结构

```text
.
├── main.py                  # CLI 入口
├── web_app.py               # Streamlit 入口
├── config.py                # 路径、默认数据、照片格式白名单
├── storage.py               # recipes/records/ingredients 的读写与加载
├── helpers.py               # CLI 输入辅助（含预填充输入）
├── recipes.py               # CLI 菜谱管理
├── records.py               # CLI 做菜记录与照片管理
├── web/
│   ├── sidebar.py           # 侧边栏
│   ├── tab_recipe.py        # 菜谱管理页
│   ├── tab_record.py        # 做菜记录页
│   ├── tab_ingredients.py   # 可用食材页 + 推荐
│   ├── daily_recommend.py   # 每日推荐
│   └── ui_helpers.py        # Web 端通用函数
├── recipes.json             # 菜谱数据
├── records.json             # 做菜记录数据
├── ingredients.json         # 可用食材数据
└── photos/                  # 记录照片目录（按 record_id 分目录）
```

## 安装与运行

### 1) 安装依赖

```bash
pip3 install streamlit
```

可选（推荐，尤其是 macOS CLI 体验）：

```bash
pip3 install gnureadline
```

### 2) 启动命令行版

```bash
python3 main.py
```

### 3) 启动 Web 版

```bash
streamlit run web_app.py
```

默认会在本地打开浏览器页面（通常是 `http://localhost:8501`）。

## 快速演示流程（3 分钟上手）

### 路线 A：Web 版（推荐）

1. 启动 Web：
```bash
streamlit run web_app.py
```
2. 在 `🥬 可用食材` 标签页添加 2-3 个食材（如：番茄、鸡蛋）。
3. 切到 `🍳 菜谱管理`，新建一道菜并保存（或直接使用默认菜谱）。
4. 切到 `📝 做菜记录`，点 `➕ 新建记录`，选择菜谱，填写步骤备注并保存。
5. 回到记录列表，展开刚保存的记录，确认备注和照片（可选）已写入。

### 路线 B：命令行版

1. 启动 CLI：
```bash
python3 main.py
```
2. 在主菜单输入 `a`，导入一道新菜谱（菜名 + 食材 + 步骤）。
3. 输入 `r` 进入做菜记录，选择 `1` 新建记录并填写备注。
4. 返回记录菜单选择 `2` 查看历史记录，确认刚才的记录已保存。

完成以上任一路线后，你会在项目目录看到（或更新）：

- `recipes.json`
- `records.json`
- `ingredients.json`（Web 食材功能使用时）
- `photos/<record_id>/...`（上传/拍照后）

## 数据格式

### `recipes.json`

```json
{
  "番茄炒蛋": {
    "steps": [
      "1. 鸡蛋打散，加少许盐搅匀",
      "2. 番茄切块备用"
    ],
    "ingredients": ["番茄", "鸡蛋"]
  }
}
```

### `records.json`

```json
[
  {
    "id": "20260310_161333",
    "name": "番茄炒蛋",
    "date": "2026-03-10 16:13",
    "steps": [
      { "text": "1. 鸡蛋打散，加少许盐搅匀", "note": "鸡蛋打得更均匀" }
    ],
    "note": "这次火候更好",
    "photos": ["photos/20260310_161333/1.jpg"]
  }
]
```

### `ingredients.json`

```json
[
  { "name": "番茄", "date": "2026-03-10" },
  { "name": "鸡蛋", "date": "2026-03-10" }
]
```

## 注意事项

- 首次运行会自动生成默认菜谱（见 `config.py`）。
- 照片支持格式由 `PHOTO_EXTS` 控制：`.jpg/.jpeg/.png/.heic/.webp/.gif/.bmp/.tiff`。
- 数据以本地 JSON 文件保存，适合个人/家庭单机使用；多人并发编辑可能产生覆盖。
