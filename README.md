# 🚀 InternHub（实习雷达）

> 面向高校学生的实习信息聚合平台 — 多源抓取 + 智能筛选 + 投递追踪

## ✨ 功能特性

- 📡 **多源聚合** — 自动抓取实习僧、牛客网、GitHub SimplifyJobs 等平台的实习岗位
- 🔍 **智能搜索** — pg_trgm 中文模糊搜索 + 类型/城市/薪资筛选 + 多维度排序
- 📋 **投递追踪** — 6 阶段 Kanban 看板，拖拽管理投递进度
- 🔔 **订阅推送** — 关键词/城市/类型订阅，每日/每周 Digest 邮件
- 🎨 **Apple 风格** — 蓝白配色、Framer Motion 动画、毛玻璃导航栏

## 🛠 技术栈

| 层 | 技术 |
|----|------|
| 前端 | React 18, TypeScript, Tailwind CSS 4, Framer Motion, @dnd-kit/core, Phosphor Icons, React Router 7, React Hook Form, axios |
| 后端 | FastAPI, SQLAlchemy 2.0, Alembic, python-jose (JWT), bcrypt |
| 爬虫 | httpx + BeautifulSoup 4, GitHub API |
| 数据库 | PostgreSQL (Supabase) + pg_trgm 中文模糊搜索 |
| 部署 | Vercel (前端), Railway (后端+Worker), Supabase (DB), Resend (邮件) |

## 🏗 项目结构

```
internhub/
├── frontend/                  # React SPA
│   ├── src/
│   │   ├── components/
│   │   │   ├── applications/  # KanbanBoard, KanbanColumn, ApplicationCard, ApplicationForm
│   │   │   ├── jobs/          # JobCard, JobList, JobFilters, HeroSection, JobDetail
│   │   │   ├── layout/        # Navbar, Footer, Layout
│   │   │   ├── subscriptions/ # SubscriptionForm
│   │   │   └── ui/            # Button, Tag, Badge, SearchInput, Pagination, JobCardSkeleton
│   │   ├── hooks/             # useAuth, useJobs, useApplications
│   │   ├── lib/               # api client, constants
│   │   └── pages/             # 8 pages: Home, JobDetail, Dashboard, Subscription, Login, Register, 404, Error
│   └── vercel.json
├── backend/
│   ├── app/
│   │   ├── models/            # User, Job, Subscription, Application, DigestQueue
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── routers/           # auth, jobs, applications, subscriptions
│   │   ├── services/          # Business logic: auth, jobs, applications, subscriptions, scraper, digest
│   │   └── scraper/           # Base scraper + shixiseng + niuke + github_jobs
│   ├── scraper/worker.py      # Cron worker: scrape → validate → digest match → cleanup
│   ├── alembic/               # Database migrations
│   └── Dockerfile
└── docs/                      # Design spec + implementation plan
```

## 🚦 快速开始

### 环境要求

- Node.js >= 18
- Python >= 3.12
- PostgreSQL (推荐 [Supabase](https://supabase.com) 免费版)

### 1. 克隆项目

```bash
git clone https://github.com/pigunderrainysky/InternHub.git
cd InternHub
```

### 2. 后端设置

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 Supabase URL、JWT Secret、Resend API Key

# 运行数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload
# API 文档 → http://localhost:8000/docs
```

### 3. 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
# 浏览器打开 → http://localhost:5173
```

### 4. 运行爬虫（可选）

```bash
cd backend

# 完整抓取（需要配置数据库）
python scraper/worker.py --scrape-only

# 发送订阅 Digest（需要 Resend API Key）
python scraper/worker.py --digest-send
```

## 🚀 部署

### 前端 → Vercel

1. 将项目推送到 GitHub
2. 在 [Vercel](https://vercel.com) 导入仓库
3. 设置 Root Directory 为 `frontend`
4. 配置 `vercel.json` 中的 API 代理地址指向 Railway 后端

### 后端 → Railway

1. 在 [Railway](https://railway.app) 新建项目
2. 设置 Root Directory 为 `backend`
3. 配置环境变量：`DATABASE_URL`, `JWT_SECRET_KEY`, `RESEND_API_KEY`, `CORS_ORIGINS`
4. Railway 会自动检测 Dockerfile 并构建

### 定时任务 → Railway Cron Jobs

```bash
# 每 8 小时抓取岗位（在 Railway 项目中添加 Cron Job）
python scraper/worker.py

# 每晚 20:00 发送 Digest 邮件
python scraper/worker.py --digest-send
```

### 数据库 → Supabase

1. 创建 [Supabase](https://supabase.com) 项目
2. 在 SQL Editor 中执行：`CREATE EXTENSION IF NOT EXISTS pg_trgm;`
3. 将连接字符串设置为 `DATABASE_URL` 环境变量
4. 运行 `alembic upgrade head` 或由 entrypoint.sh 自动执行

## 📡 API 端点

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| POST | `/api/auth/register` | ✗ | 注册 |
| POST | `/api/auth/login` | ✗ | 登录 |
| GET | `/api/auth/me` | ✓ | 当前用户信息 |
| PUT | `/api/auth/password` | ✓ | 修改密码（撤销所有 Token） |
| GET | `/api/jobs` | ✗ | 岗位搜索 + 分页 |
| GET | `/api/jobs/{id}` | ✗ | 岗位详情 |
| GET | `/api/jobs/stats` | ✗ | 统计摘要 |
| GET | `/api/applications` | ✓ | 投递记录（按状态分组） |
| POST | `/api/applications` | ✓ | 新增投递 |
| PATCH | `/api/applications/{id}/status` | ✓ | 更新状态（拖拽） |
| PUT | `/api/applications/{id}` | ✓ | 编辑备注 |
| DELETE | `/api/applications/{id}` | ✓ | 删除 |
| GET | `/api/subscriptions` | ✓ | 获取订阅 |
| POST | `/api/subscriptions` | ✓ | 创建/更新订阅 |

## 🔐 安全

- 密码 bcrypt 哈希存储
- JWT access token 15min + refresh token 7d
- `token_version` 机制：修改密码后所有旧 Token 立即失效
- API 输入 Pydantic 校验，ORM 参数化防 SQL 注入
- CORS 白名单

## 📝 License

MIT

---

**作者：** 肖康平 · 南京大学 信息管理学院 2027届

🤖 部分代码由 [Claude Code](https://claude.com/claude-code) 辅助生成
