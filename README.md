# NovelForge - AI 小说生成管理系统

基于 FastAPI + React 19 的 AI 驱动小说创作平台，支持从"一句话创意"到"完整小说导出"的全流程 AI 生成。

## 🚀 快速开始

### 后端启动
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8788 --reload
```

### 前端启动
```bash
cd frontend
npm install
npm run dev
```

前端开发服务器运行在 `http://localhost:5173`，API 请求通过代理转发到后端 `http://localhost:8788`。

## 📖 使用流程

### 1. 配置模型
1. 进入"模型配置"页面
2. 添加 API 地址（支持任何 OpenAI-compatible API，如 SiliconFlow、DeepSeek 等）
3. 填入 API Key 和模型名
4. 点击"测试连接"验证
5. 设为默认模型

### 2. 创建项目并填入创意
1. 新建项目
2. 填写项目标题、题材、风格
3. 在"一句话创意"中输入故事核心创意

### 3. 生成设定
点击"生成设定"→ AI 自动生成：
- 世界观
- 力量体系
- 主线剧情
- 角色列表

### 4. 生成大纲
点击"生成大纲"→ AI 自动生成：
- 分卷结构
- 各章节大纲

### 5. 生成章节
- 点击章节的"生成正文"→ AI 根据设定和大纲生成正文
- 支持续写、润色、一致性检查

### 6. 导出
- TXT 导出（纯文本格式）
- Markdown 导出（带 YAML frontmatter）

## 🧠 AI 生成能力

| 功能 | 说明 |
|------|------|
| 设定生成 | 根据创意生成世界观、角色、主线 |
| 大纲生成 | 根据设定生成分卷和章节大纲 |
| 章节生成 | 根据大纲+前情生成正文 |
| 续写 | 在已有内容基础上继续写作 |
| 润色 | 修改语病、优化文笔 |
| 摘要提取 | 自动提取章节摘要 |
| 一致性检查 | 检查章节内容与设定是否矛盾 |
| 版本管理 | 每次生成保存为新版本，不覆盖旧内容 |

## 🗂️ 技术栈

**后端**
- FastAPI - API 框架
- SQLAlchemy - ORM（SQLite + WAL 模式）
- Pydantic - 数据验证
- httpx - LLM API 调用

**前端**
- React 19 - UI 框架
- React Router - 路由
- TanStack Query - 数据同步
- Vite - 构建工具
- Tailwind CSS v4 - 样式

## ⚙️ 配置

后端默认端口 8788，通过环境变量配置：
- `DATABASE_URL` - 数据库路径（默认 `sqlite:///data/novel.db`）
- `APP_HOST` - 监听地址
- `APP_PORT` - 监听端口
- `REQUEST_TIMEOUT_SECONDS` - LLM 请求超时

## 📁 项目结构

```
novelforge/
├── backend/
│   ├── app/
│   │   ├── models.py       # SQLAlchemy 模型（12个表）
│   │   ├── schemas.py      # Pydantic 验证模型
│   │   ├── main.py         # FastAPI 入口
│   │   ├── database.py     # 数据库连接（WAL模式）
│   │   ├── routers/        # API 路由
│   │   ├── services/       # 业务逻辑层
│   │   └── prompts/        # AI 提示词模板
│   ├── data/               # SQLite 数据库
│   └── requirements.txt
├── frontend/               # React 前端
└── README.md
```

## 🔧 常见错误

**"No default model configured"**
→ 先在模型配置页面添加并设为默认模型。

**"Project has no idea set"**
→ 在项目编辑页面填写"一句话创意"。

**"LLM API call failed"**
→ 检查 API Key 是否正确，模型名是否支持，网络是否可达。

**端口冲突**
→ 设置环境变量 `APP_PORT=8788` 避免与 Hermes Bridge（8787）冲突。

## 📄 许可证

MIT
