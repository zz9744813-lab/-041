# ⚒️ NovelForge — AI 小说生成管理系统

NovelForge 是一个本地部署的 AI 小说生成工作流系统。它把"一句话创意 → 世界观/角色设定 → 分卷大纲 → 章节正文 → 版本管理 → 续写 → 审校 → 导出"变成稳定、可恢复、可编辑的自动化流程。

## ✨ 功能特性

- **一句话创意生成设定** — 输入核心创意，AI 自动生成世界观、角色卡、主线冲突
- **自动分卷大纲** — 基于设定生成完整的卷纲和章节细纲
- **逐章自动生成** — 每章独立生成，含前情提要，保持连贯性
- **章节版本管理** — 每次生成/润色/手动编辑都保留历史版本，可随时切换
- **断点续写** — 失败自动记录，支持重试；暂停后可恢复
- **批量生成** — 指定章节范围，自动逐章生成
- **润色优化** — 减少模板化表达，提升自然度
- **一致性检查** — 检测角色 OOC、世界观冲突、时间线矛盾
- **自动摘要提取** — 每章生成后自动提取摘要、关键事件、伏笔
- **多格式导出** — TXT、Markdown 格式导出完整小说
- **模型配置管理** — 支持任何 OpenAI 兼容 API（硅基流动、DeepSeek、OpenAI 等）

## 🚀 快速开始

### 1. 安装依赖

```bash
cd /opt/novelforge
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置环境变量（可选）

```bash
cp .env.example .env
# 根据需求修改配置
```

### 3. 启动系统

```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8788
```

浏览器打开 http://localhost:8788

### 4. 配置模型

1. 打开「设置」页面
2. 点击「添加模型」
3. 填写 Base URL（如 `https://api.siliconflow.cn/v1`）
4. 填写 API Key 和模型名称
5. 保存并设为默认

### 5. 创建小说项目

1. 点击「新建项目」
2. 填写名称、一句话创意、类型和风格
3. 创建后在项目详情页点击「生成设定」
4. 再点击「生成大纲」
5. 最后点击「生成下一章」自动逐章生成

## 🗂️ 项目结构

```
novelforge/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库初始化 (SQLite + WAL)
│   ├── models/              # 数据库模型（7个表）
│   ├── schemas/             # Pydantic 验证
│   ├── routers/             # Web 路由（7个模块）
│   ├── services/            # 业务逻辑（9个服务）
│   ├── prompts/             # AI 提示词模板（6个）
│   ├── templates/           # Jinja2 页面模板
│   └── static/              # 静态资源（CSS/JS）
├── data/                    # SQLite 数据库
│   └── faiss/               # 向量存储（预留）
├── exports/                 # 导出文件目录
├── systemd/                 # Systemd 服务配置
├── requirements.txt
├── .env.example
└── README.md
```

## 🔧 技术栈

- **后端**：FastAPI + SQLAlchemy + Pydantic
- **数据库**：SQLite（WAL 模式）
- **前端**：Jinja2 + HTML + CSS + 原生 JS
- **AI 接口**：OpenAI-compatible API
- **端口**：8788

## 📡 API 文档

启动后访问 `/docs` 查看自动生成的 API 文档。

## ⚙️ Systemd 部署

```bash
cp systemd/novelforge.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable novelforge
systemctl start novelforge
systemctl status novelforge
```

## 📄 License

MIT
