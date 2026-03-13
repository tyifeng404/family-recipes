# 家庭食谱（CLI + Web）

一个家庭菜谱管理项目，支持两种使用方式：

- 命令行版：快速维护菜谱与做菜记录
- Web 版（Streamlit）：图形化管理菜谱、食材、照片与推荐

## 功能概览

### 1) 菜谱管理

- 新增、查看、修改、删除菜谱
- 菜谱包含「主要食材 + 全部食材 + 详细菜谱 + 要点 + 照片 + 标签 + 难度 + 菜系」
- 菜谱按分类分组展示，支持分类收起/展开
- 支持菜名/食材/菜系/标签/难度搜索
- 支持从旧格式自动迁移（`{菜名: [步骤]}` -> 新格式）
- 内置约 150 道经典菜谱（中餐约 100 + 外国菜约 50），首次加载自动补齐

### 2) 做菜记录

- 按菜谱创建一次做菜记录
- 对每一步添加备注，支持整体备注
- 支持拍照/上传照片并与记录关联
- 支持编辑备注、删除记录、自动清理关联照片

### 3) 可用食材管理与推荐（Web）

- 维护当前可用食材（名称 + 购买日期）
- 根据食材自动推荐可做菜谱（完全匹配/部分匹配）
- 提供每日推荐（优先食材匹配，不足时随机推荐）

### 4) 账号与共享（Web）

- 账号注册与登录（账户名称、密码、真实姓名、手机号）
- 管理员审核新账号（通过/拒绝）
- 账号管理页可修改注册信息与密码
- 侧边栏提供「账号管理」快捷选项，点击弹出独立界面修改当前账号信息
- 每个账号可配置是否共享：菜谱 / 做菜记录 / 食材

## 技术栈

- Python 3.10+
- Streamlit（Web 界面）
- JSON 文件持久化（默认）
- Supabase（可选云端同步）

## 目录结构

```text
.
├── main.py                  # CLI 入口
├── web_app.py               # Streamlit 入口
├── builtin_recipes.py       # 内置菜谱库（约 150 道）
├── cuisine.py               # 菜系常量与工具
├── config.py                # 路径、默认数据、照片格式白名单
├── storage.py               # 存储入口（可切本地 JSON / Supabase）
├── storage_backends.py      # 存储后端实现
├── helpers.py               # CLI 输入辅助（含预填充输入）
├── recipes.py               # CLI 菜谱管理
├── records.py               # CLI 做菜记录与照片管理
├── scripts/
│   ├── supabase_init.sql    # Supabase 初始化 SQL
│   └── migrate_local_to_supabase.py
├── web/
│   ├── auth.py              # 登录/注册
│   ├── sidebar.py           # 侧边栏
│   ├── tab_recipe.py        # 菜谱管理页
│   ├── tab_record.py        # 做菜记录页
│   ├── tab_ingredients.py   # 可用食材页 + 推荐
│   ├── tab_account.py       # 账号管理页
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

使用 Supabase 同步时，还需要：

```bash
pip3 install supabase
```

也可以直接使用项目依赖文件安装：

```bash
pip3 install -r requirements.txt
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

## 云端同步（Supabase）

当前版本已支持把菜谱/记录/食材切换到 Supabase 存储（用于多人共享同步）。

### 1) 初始化 Supabase 表

在 Supabase SQL Editor 执行：

- `scripts/supabase_init.sql`

### 2) 配置环境变量

```bash
export STORAGE_BACKEND=supabase
export SUPABASE_URL="https://<project-ref>.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="<your-service-role-key>"
# 可选：默认是 app_state
export SUPABASE_STATE_TABLE="app_state"
```

可选（管理员初始账号）：

```bash
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="admin123456"
```

> 如果未配置这些变量，程序会自动回退到本地 JSON 存储。

### 3) 迁移本地数据（一次性）

```bash
python3 scripts/migrate_local_to_supabase.py
```

### 4) 启动应用

```bash
streamlit run web_app.py
```

### 5) Streamlit Cloud 配置（部署端）

在 Streamlit Cloud 的应用设置中添加 Secrets（不是系统环境变量）：

```toml
STORAGE_BACKEND="supabase"
SUPABASE_URL="https://<project-ref>.supabase.co"
SUPABASE_SERVICE_ROLE_KEY="<your-service-role-key>"
SUPABASE_STATE_TABLE="app_state"
```

也支持分组写法：

```toml
[supabase]
url="https://<project-ref>.supabase.co"
service_role_key="<your-service-role-key>"
state_table="app_state"

[storage]
backend="supabase"
```

保存后 Reboot 应用，进入页面后在左侧底部确认显示：

- `存储后端：supabase`

### 6) 双账号同步验收（建议 3 分钟）

1. 账号 A 打开应用，新增一道菜谱（例如 `同步测试-今天日期`）。
2. 账号 B 刷新页面，确认能看到该菜谱。
3. 账号 B 新建一条做菜记录并保存。
4. 账号 A 刷新，确认记录列表出现该条记录。
5. 任一账号修改该记录备注，另一账号刷新确认变更可见。

如果左下角显示 `存储后端：local`，说明云端 Secrets 未生效或键名有误。

### 常见问题（ConnectError）

如果出现 `httpx.ConnectError`，优先检查：

1. `SUPABASE_URL` 必须是 API 域名：`https://<project-ref>.supabase.co`
2. 不要填 Dashboard 链接（如 `https://supabase.com/dashboard/...`）
3. `SUPABASE_SERVICE_ROLE_KEY` / `SUPABASE_ANON_KEY` 是否完整复制
4. Supabase 项目是否处于暂停状态（Free 计划长时间不用会暂停）

当前代码在 Supabase 不可达时会自动回退到 `local`，并在侧边栏显示诊断信息。

## 快速演示流程（3 分钟上手）

### 路线 A：Web 版（推荐）

1. 启动 Web：
```bash
streamlit run web_app.py
```
2. 在 `🥬 可用食材` 标签页添加 2-3 个食材（如：番茄、鸡蛋）。
3. 切到 `🍳 菜谱管理`，新建一道菜并保存（或直接使用默认菜谱）。
4. 切到 `📝 做菜记录`，点 `➕ 新建做菜记录`，选择菜谱，填写步骤备注并保存。
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
