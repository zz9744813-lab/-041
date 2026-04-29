# Novel System – 个人小说创作系统

一个功能完整的个人小说创作系统，包含项目管理、三栏写作台、角色设定、世界观管理、数据看板等功能。

## 🚀 快速开始

### 后端启动
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8787 --reload
```

### 前端启动
```bash
cd frontend
npm install
npm run dev
```

前端开发服务器会运行在 `http://localhost:5173`，API 请求通过代理转发到后端 `http://localhost:8787`。

## 📦 功能特性

### 项目管理
- 新建/编辑/删除小说项目
- 按类型（长篇/短篇/随笔）分类
- 项目统计（字数、章节数）

### 三栏写作台
- 左侧：章节列表
- 中间：Markdown 编辑器（无干扰写作环境）
- 右侧：章节元数据（摘要、备注、视角、角色、地点）
- 实时保存（Ctrl+S）
- 字数统计

### 章节管理
- 创建/排序/删除章节
- 草稿->进行中->待修订->已完成 状态流
- 章节备份（每 30 秒自动保存）

### 角色设定
- 记录主要角色信息（年龄、性别、背景、性格、外貌）
- 按项目分组

### 世界观
- 管理地点、时间线、规则、背景设定
- Markdown 格式支持

### 数据看板
- 总体统计数据（项目数、总字数、总章节）
- 每日写作量图表
- 各项目进度概览

### 导出
- 导出为 TXT 格式（完整章节拼接）
- 未来：PDF、Epub、Word 导出

## 🗂️ 技术栈

**后端** (Python)
- FastAPI – API 框架
- SQLAlchemy – ORM
- SQLite – 数据库（`data/novel.db`）
- Pydantic – 数据验证
- 文件存储：章节正文存为 `novels/{project_id}/chapters/{chapter_id}.md`

**前端** (TypeScript)
- React 19 – UI 框架
- React Router – 路由
- TanStack Query – 数据同步
- Vite – 构建工具
- Tailwind CSS v4 – 样式
- 深色主题设计

## 📁 项目结构

```
novel-system/
├── backend/
│   ├── app/
│   │   ├── database.py          # 数据库连接
│   │   ├── models.py           # SQLAlchemy 模型
│   │   ├── schemas.py          # Pydantic 模型
│   │   ├── main.py            # FastAPI 入口
│   │   ├── routers/           # 路由模块
│   │   └── utils/             # 工具函数
│   ├── data/                  # SQLite 数据库目录
│   ├── novels/               # 章节正文文件目录
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── lib/               # API 客户端
│   │   ├── pages/             # 页面组件
│   │   ├── components/        # 可复用组件
│   │   ├── types/             # TypeScript 类型
│   │   └── router.tsx        # 路由配置
│   └── vite.config.ts        # Vite 配置
└── README.md
```

## 🔧 部署

### Systemd 服务
```bash
# 复制服务文件
sudo cp novel-system.service /etc/systemd/system/

# 启动
sudo systemctl daemon-reload
sudo systemctl enable novel-system
sudo systemctl start novel-system

# 查看状态
sudo systemctl status novel-system
```

### Nginx 反向代理（可选）
```
server {
    listen 80;
    server_name novels.yourdomain.com;

    location / {
        proxy_pass http://localhost:8787;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔄 数据备份

章节正文自动备份到 `novels/{project_id}/.backups/{chapter_id}/` 目录，时间戳命名。

## 🧪 API 文档

启动后端后访问：
- OpenAPI UI: `http://localhost:8787/docs`
- ReDoc: `http://localhost:8787/redoc`

## 📄 许可证

MIT