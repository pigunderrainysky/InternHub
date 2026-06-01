# InternHub（实习雷达）— 实现计划

## Context

为肖康平（南京大学 信管 2027届）的第三个简历项目 —— 全栈 Web 应用"实习雷达"。该平台聚合多源实习信息、支持搜索筛选订阅推送、提供 Kanban 式投递管理。目标是展示 React + FastAPI + PostgreSQL 的全栈能力和产品思维。

**设计文档：** `D:\Resume_produce\docs\superpowers\specs\2026-06-01-internhub-design.md`

## Phase 1: 骨架搭建（Day 1-4）

### 1.1 项目初始化
- 创建 `internhub/` 根目录
- `frontend/`: Vite + React 18 + TypeScript + Tailwind CSS 4，安装 framer-motion、@dnd-kit/core、phosphor-icons、axios、react-router-dom、react-hook-form
- `backend/`: FastAPI 项目骨架，requirements.txt（fastapi、uvicorn、sqlalchemy、alembic、psycopg2、passlib、python-jose、httpx、beautifulsoup4）

### 1.2 数据库
- 创建 SQLAlchemy 模型：User、Job、Subscription、Application、DigestQueue
- Alembic 初始化 + 生成首次迁移
- 连接到 Supabase PostgreSQL（配置 DATABASE_URL）

### 1.3 认证系统
- `POST /api/auth/register` — 注册（bcrypt 哈希，token_version = 1）
- `POST /api/auth/login` — 登录返回 JWT（payload 含 token_version）
- `PUT /api/auth/password` — 改密自增 token_version
- JWT 中间件：验证 token + 比对 token_version
- 前端 LoginPage + RegisterPage（蓝白 Apple 风格表单）

**关键文件：**
- `backend/app/models/user.py`
- `backend/app/services/auth_service.py`
- `backend/app/routers/auth.py`
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/pages/RegisterPage.tsx`

## Phase 2: 爬虫 Worker（Day 5-7）

### 2.1 爬虫基础设施
- `BaseScraper` 基类：fetch / parse / clean_url / dedup_key
- URL 清洗函数：剥离 `utm_source`、`ref`、`spm`、`track`、`timestamp` 等参数
- 双重去重：`source_hash = SHA256(clean_url)` + `dedup_key = SHA256(company + title_norm + city)`
- 入库 upsert：dedup_key 存在？更新 → 否则 INSERT

### 2.2 数据源（先实现 3 个）
- `shixiseng.py` — 实习僧（httpx + HTML 解析）
- `niuke.py` — 牛客网校招板块（httpx + HTML 解析）
- `github_jobs.py` — GitHub SimplifyJobs 仓库（GitHub API / raw JSON）

### 2.3 Worker 入口脚本
- `backend/scraper/worker.py` — 单次运行脚本，供 Cron 触发
- 执行：scrape_all() → validate_active() → cleanup_digest_queue()
- validate_active()：HEAD 请求近 30 天岗位 → 404 标记 is_active=false → 联动关闭相关 application 为 closed
- cleanup_digest_queue()：**时间门控** — 仅在当月 1 日执行（代码内校验当前日期），避免每 8h 重复扫描数据库

**关键文件：**
- `backend/app/scraper/base.py`
- `backend/app/scraper/shixiseng.py`
- `backend/app/scraper/niuke.py`
- `backend/app/scraper/github_jobs.py`
- `backend/app/scraper/worker.py`

## Phase 3: 岗位 API + 前端首页（Day 8-11）

### 3.1 岗位 API
- `GET /api/jobs` — 分页 + 筛选（job_type, city, salary_min, sort）+ 模糊搜索
- `GET /api/jobs/{id}` — 详情
- `GET /api/jobs/stats` — 各类型/城市统计
- 搜索使用 **pg_trgm** 扩展（Supabase 原生内置）：`title ILIKE '%keyword%'` 走 GIN trgm 索引，`description ILIKE` 作为长文本补充召回
- 数据库初始化时执行 `CREATE EXTENSION IF NOT EXISTS pg_trgm`

### 3.2 前端首页
- `JobCard` — 白卡片 + 16px 圆角，hover 上浮 4px（Framer Motion spring），显示公司/标题/城市/薪资/技能标签/时间
- `JobList` — 2 列卡片网格，stagger 逐项淡入（`staggerChildren=0.08`）
- `JobFilters` — 分类标签（横向滚动胶囊按钮）、城市下拉、排序下拉
- `SearchInput` — 全局搜索框，聚焦态蓝色边框微发光
- `HeroSection` — 标题 + 副标题 + 大搜索框
- 导航栏毛玻璃：`backdrop-blur(20px)` + `bg-white/70`

**关键文件：**
- `backend/app/services/job_service.py`
- `backend/app/routers/jobs.py`
- `frontend/src/components/jobs/JobCard.tsx`
- `frontend/src/components/jobs/JobList.tsx`
- `frontend/src/components/jobs/JobFilters.tsx`
- `frontend/src/pages/HomePage.tsx`

## Phase 4: 岗位详情 + 投递管理（Day 12-14）

### 4.1 岗位详情页
- 侧边栏布局：左侧 JD 原文（保留换行），右侧公司信息 + 技能标签 + 跳转原文
- "投递此岗位" 蓝色渐变胶囊按钮 → 触发 POST /api/applications

### 4.2 投递管理 Dashboard
- `KanbanBoard` — 6 列看板（applied → screening → interview → offer → rejected → closed）
- `KanbanColumn` — 列头显示状态名 + 计数，Framer Motion layout 属性负责卡片放置后的弹性动画
- `ApplicationCard` — 使用 **@dnd-kit/core** 处理可拖拽跨列移动（拖拽状态管理、碰撞检测、占位符），放置后 PATCH /api/applications/:id/status 更新状态
- Modal：新增投递（选择已有岗位）+ 编辑备注
- API 端：
  - `POST /api/applications`
  - `GET /api/applications`
  - `PATCH /api/applications/{id}/status`
  - `PUT /api/applications/{id}`
  - `DELETE /api/applications/{id}`

**关键文件：**
- `frontend/src/components/applications/KanbanBoard.tsx`
- `frontend/src/components/applications/KanbanColumn.tsx`
- `frontend/src/components/applications/ApplicationCard.tsx`
- `frontend/src/pages/DashboardPage.tsx`
- `backend/app/routers/applications.py`

## Phase 5: 订阅推送（Day 15-16）

### 5.1 订阅设置
- 前端 `SubscriptionForm`：关键词输入 + 城市多选 + 频率勾选（每日/每周）
- API：`POST /api/subscriptions` + `GET /api/subscriptions`

### 5.2 Digest 邮件推送
- Worker 中的 digest 匹配逻辑：每次 scrape_all 后，遍历已订阅用户 → 关键词/城市匹配新岗位 → 写入 digest_queue
- 每晚 20:00 聚合任务：SELECT digest_queue WHERE is_sent=false GROUP BY user_id → 每个用户组装一封 HTML 邮件
- Resend API 发送 → 标记 is_sent=true
- 每月清理（时间门控，仅当月 1 日实际执行）：DELETE digest_queue WHERE is_sent=true AND matched_at < NOW() - 30 days

**关键文件：**
- `frontend/src/components/subscriptions/SubscriptionForm.tsx`
- `frontend/src/pages/SubscriptionPage.tsx`
- `backend/app/routers/subscriptions.py`
- `backend/app/services/digest_service.py`

## Phase 6: 打磨部署（Day 17-19）

### 6.1 打磨
- 动画微调：页面切换过渡、加载骨架屏、空状态插画
- 响应式适配：平板单列卡片、手机版汉堡菜单
- 错误处理：404/500 页面、网络异常 toast、表单校验提示
- 通用 UI 组件：Button、Tag、Badge、SearchInput

### 6.2 部署
- 前端 → Vercel（`vite build` + 自动部署）
- 后端 → Railway（Dockerfile 或 nixpacks）
- 数据库 → Supabase（执行迁移 + 启用 pg_trgm 扩展）
- Worker → Railway Cron Jobs 每 8h 触发 worker.py（cleanup 内部含时间门控，仅当月 1 日实际执行）
- 邮件 → Resend（配置 API key 环境变量）

### 6.3 开源
- GitHub 仓库：`pigunderrainysky/InternHub`
- README：功能截图 + 技术栈 + 本地运行指南 + 架构图
- 项目标签：React, FastAPI, PostgreSQL, Web Scraping, Full-Stack

## 技术栈总览

| 层 | 技术 |
|------|------|
| 前端 | React 18, TypeScript, Tailwind CSS 4, Framer Motion, @dnd-kit/core, Phosphor Icons, React Router, React Hook Form, axios |
| 后端 | FastAPI, SQLAlchemy 2.0, Alembic, python-jose (JWT), passlib (bcrypt) |
| 爬虫 | httpx, BeautifulSoup 4 |
| 数据库 | PostgreSQL (Supabase) + pg_trgm 中文模糊搜索扩展 |
| 部署 | Vercel (前端), Railway (后端+Worker), Supabase (DB), Resend (邮件) |
| 开发工具 | Vite, ESLint, Prettier |

## 验证方式

1. **本地开发**：`uvicorn main:app --reload` + `npm run dev` → localhost:5173
2. **爬虫测试**：`python worker.py` 手动执行，验证数据入库 + 去重 + 前端渲染
3. **API 文档**：FastAPI 自动生成 http://localhost:8000/docs
4. **Kanban 拖拽**：拖拽卡片跨列，刷新页面确认状态持久化
5. **搜索验证**：输入"前端" → 确认返回中文分词正确结果
6. **订阅 Digest**：手动触发 digest 任务 → 检查 Resend 发送日志
7. **部署验证**：Vercel/Railway 生产环境可公开访问
