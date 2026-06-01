# InternHub（实习雷达）— Design Spec

> 2026-06-01 | 肖康平 | 全栈 Web 应用 — 第三项目

---

## 1. 产品概述

### 1.1 一句话定义

面向高校学生的**实习信息聚合平台**，多源抓取 + 智能筛选 + 投递追踪，一站式解决实习信息碎片化问题。

### 1.2 目标用户

- 南京大学及周边高校在校生（大三/大四为主）
- 有主动求职意愿、需高效获取实习信息的同学

### 1.3 核心价值

| 痛点 | 解法 |
|------|------|
| 实习信息分散在多个网站 | 多源聚合，统一浏览 |
| 反复切换网站刷新效率低 | 一键搜索 + 多条件筛选 |
| 投递后难以追踪进度 | Kanban 式投递管理 |
| 错过想去的岗位 | 关键词订阅 + 邮件推送 |

### 1.4 MVP 功能范围

| 模块 | 功能 |
|------|------|
| 📡 数据抓取 | 定时抓取 3-5 个源（实习僧/牛客/GitHub 实习仓库等） |
| 🔧 数据处理 | URL 去重 + 字段标准化 + 自动标签（类型/城市/技能） |
| 🔍 浏览检索 | 首页卡片列表 + 关键词搜索 + 类型/城市/薪资筛选 + 排序 |
| 📋 岗位详情 | JD 原文 + 公司信息 + 发布时间 + 跳转原文链接 |
| 🔔 订阅推送 | 注册后按关键词/城市订阅，邮件通知新岗位 |
| 📝 投递追踪 | 五阶段状态看板 + 备注 + 时间线 |

### 1.5 MVP 不做

- AI 智能匹配/简历评分
- 评论/讨论/社区功能
- 公司评价/面经
- 移动端 App
- 第三方登录（OAuth）

---

## 2. 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                      前端 (Vercel)                       │
│   React 18 + TypeScript + Tailwind CSS 4 + Vite         │
│   Framer Motion (动画) · Phosphor Icons (图标)           │
│   ┌──────────┬──────────┬──────────┬──────────────┐    │
│   │ 首页列表  │  搜索筛选  │ 岗位详情  │ Dashboard    │    │
│   │ JobCard  │ Filters  │ Sidebar  │ Kanban 看板   │    │
│   └──────────┴──────────┴──────────┴──────────────┘    │
└────────────────────┬────────────────────────────────────┘
                     │ RESTful JSON API (JWT Bearer)
┌────────────────────▼────────────────────────────────────┐
│                  Web 服务 (Railway)                       │
│   FastAPI + SQLAlchemy + Alembic                        │
│   ┌──────────┬──────────┬──────────┬──────────────┐    │
│   │ Auth     │ 岗位 API  │ 订阅模块  │ 投递记录      │    │
│   │ JWT      │ CRUD+搜索 │ 关键词匹配 │ 狀態機        │    │
│   └──────────┴──────────┴──────────┴──────────────┘    │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
┌─────────────────────┐  ┌──────────────────────────────┐
│  Scraper Worker     │  │    PostgreSQL (Supabase)      │
│  (独立脚本/Cron触发)  │  │  users / jobs / subscriptions │
│                     │  │  applications / digest_queue  │
│  httpx → 清洗 →     │  └──────────────────────────────┘
│  双重去重 → 入库     │
│  + 存活性校验        │
└─────────────────────┘
```

> **架构关键变更：** 爬虫从 Web 进程中剥离为独立 Worker。Web 服务可安全扩容，爬虫单实例执行避免重复抓取。Worker 通过 Railway Cron Jobs 或独立 Service 触发，与 Web API 解耦。

### 2.1 关键技术决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 前端框架 | React 18 + Vite（非 Next.js） | SPA 足够，学习曲线更平滑 |
| 样式方案 | Tailwind CSS 4 | 原子化 CSS，快速迭代 |
| 动画库 | Framer Motion | spring physics，layout animation，stagger |
| 拖拽库 | @dnd-kit/core | 处理 Kanban 跨列拖拽的状态管理与碰撞检测，Framer Motion 仅负责放置后的弹性动画 |
| 后端框架 | FastAPI | Python 熟练，异步支持好，自带 OpenAPI 文档 |
| ORM | SQLAlchemy 2.0 | Python 生态标准，类型安全 |
| 迁移 | Alembic | SQLAlchemy 生态标配 |
| 数据库 | PostgreSQL (Supabase) | 免费额度够 MVP 使用 |
| 爬虫 | 独立 Worker（httpx + BeautifulSoup）| 与 Web 服务解耦，Railway Cron 触发，避免多实例重复抓取 |
| 认证 | JWT (access + refresh token) | 无状态，适合前后端分离 |

---

## 3. 前端设计

### 3.1 设计定位

> **明亮、开朗、蓝白调 · Apple 式轻奢交互**
> "像翻阅一本精心排版的杂志，而不是操作一个数据库工具"

### 3.2 配色方案

| 角色 | 色值 | Tailwind 映射 |
|------|------|--------------|
| 主背景 | `#F5F5F7` | apple-gray |
| 卡片 | `#FFFFFF` | white |
| 主蓝 | `#0071E3` | apple-blue |
| 浅蓝 | `#E8F4FD` | apple-blue-light |
| 渐变 | `#0071E3` → `#5AC8FA` | blue-gradient |
| 文字主 | `#1D1D1F` | apple-black |
| 文字次 | `#86868B` | apple-gray-text |
| 边框 | `#E5E7EB` | gray-200 |
| 成功 | `#34C759` | apple-green |
| 警告 | `#FF9500` | apple-orange |
| 错误 | `#FF3B30` | apple-red |

### 3.3 字体

| 用途 | 字体 | 回退 |
|------|------|------|
| 标题/Logo | SF Pro Display | PingFang SC, system-ui |
| 正文 | SF Pro Text | PingFang SC, system-ui |
| 代码 | SF Mono | Monaco, monospace |

### 3.4 间距与圆角（4px Base Grid）

| Token | 值 | 用途 |
|-------|-----|------|
| `xs` | 4px | 图标间距 |
| `sm` | 8px | 组件内紧凑间距 |
| `md` | 12px | 相关元素间 |
| `lg` | 16px | 卡片 padding |
| `xl` | 24px | 区块间距 |
| `2xl` | 32px | 大区块分离 |
| 卡片圆角 | 16px | 大卡片 |
| 小组件圆角 | 12px | Tag/Badge |
| 按钮圆角 | 9999px | 胶囊形 full |

### 3.5 动画规格（Framer Motion）

| 交互 | 实现 | 参数 |
|------|------|------|
| 页面加载 | 卡片 stagger 淡入上移 | `spring: stiffness=100, damping=15` |
| 卡片 hover | 上浮 4px + 阴影加深 | `spring: duration=0.3` |
| 卡片点击 | 微缩放 0.97 | `spring: duration=0.15` |
| 筛选标签切换 | 背景色平滑过渡 | `ease-out: duration=0.2` |
| 导航栏 | `backdrop-blur(20px)` 毛玻璃 | 静态 |
| 滚动揭示 | IntersectionObserver + stagger | `staggerChildren=0.08` |
| Kanban 拖拽 | @dnd-kit 处理拖拽状态 + Framer Motion layout 弹性动画 | `type: "spring"` |
| 搜索框聚焦 | 边框蓝变 + box-shadow 微发光 | `transition: duration=0.2` |

### 3.6 页面结构

**首页 — 实习列表：**
```
┌─────────────────────────────────────────────────────────┐
│  NAV: Logo | 搜索框 | 订阅 | 投递记录 | 登录/头像       │
│  (毛玻璃: backdrop-blur(20px), bg-white/70)              │
├─────────────────────────────────────────────────────────┤
│  Hero: "发现最适合你的实习机会" + 副标题                  │
│  [全部] [技术] [产品] [运营] [金融] [设计]  ← 分类标签    │
│  [📍 全部城市 ▾]  [🕐 最新发布 ▾]        ← 筛选排序     │
├─────────────────────────────────────────────────────────┤
│  JobCard Grid (2-3 col) - 瀑布流 stagger 加载            │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │ 🏢 字节跳动       │  │ 🏢 腾讯           │            │
│  │ 前端开发实习生     │  │ 产品经理实习生     │            │
│  │ 📍北京 · ¥400-500 │  │ 📍深圳 · ¥200-300 │            │
│  │ [React] [TS]     │  │ [产品] [数据]     │            │
│  │ 3h前 · 查看详情→  │  │ 5h前 · 查看详情→  │            │
│  └──────────────────┘  └──────────────────┘            │
├─────────────────────────────────────────────────────────┤
│  分页器 < 1 2 3 ... 10 >                               │
└─────────────────────────────────────────────────────────┘
```

**投递管理 — Kanban 看板：**
```
┌─────────────────────────────────────────────────────────┐
│  📝 我的投递                                    [+ 新增] │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ 📥 已投递 │  │ 👀 初筛中 │  │ 💬 面试中 │  │ ✅ Offer│ │
│  │  3       │  │  1       │  │  2       │  │  0      │ │
│  │          │  │          │  │          │  │        │ │
│  │ ┌──────┐ │  │ ┌──────┐ │  │ ┌──────┐ │  │        │ │
│  │ │字节  │ │  │ │美团  │ │  │ │腾讯  │ │  │        │ │
│  │ │前端  │ │  │ │后端  │ │  │ │PM    │ │  │        │ │
│  │ │06-01│ │  │ │05-28│ │  │ │05-25│ │  │        │ │
│  │ └──────┘ │  │ └──────┘ │  │ └──────┘ │  │        │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 3.7 组件树

```
App
├── Layout
│   └── Navbar (毛玻璃固定顶栏)
│       ├── Logo
│       ├── SearchInput (全局搜索)
│       └── NavLinks + Avatar
├── HomePage
│   ├── HeroSection
│   │   ├── Heading + Subheading
│   │   └── SearchInput (聚焦态)
│   ├── FilterBar
│   │   ├── JobTypeTabs (分类标签)
│   │   ├── CitySelect (城市下拉)
│   │   └── SortSelect (排序下拉)
│   ├── JobList (stagger 容器)
│   │   └── JobCard[] (hover 上浮动画)
│   └── Pagination
├── JobDetailPage
│   ├── JobDetailSidebar
│   │   ├── CompanyHeader
│   │   ├── JobDescription (JD 原文)
│   │   ├── SkillTags
│   │   └── ApplyButton (渐变胶囊)
│   └── RelatedJobs
├── DashboardPage (投递管理)
│   ├── KanbanBoard
│   │   └── KanbanColumn[] (5列，layout animation)
│   │       └── ApplicationCard[] (可拖拽)
│   └── ApplicationForm (新增/编辑 Modal)
├── SubscriptionPage
│   └── SubscriptionForm
│       ├── KeywordInput
│       ├── CityMultiSelect
│       └── FrequencyToggle
├── LoginPage
└── RegisterPage
```

### 3.8 技术栈

| 层 | 选型 | 版本 |
|------|------|------|
| 框架 | React | ^18 |
| 语言 | TypeScript | ^5 |
| 构建 | Vite | ^6 |
| 样式 | Tailwind CSS | ^4 |
| 动画 | Framer Motion | ^11 |
| 拖拽 | @dnd-kit/core | ^6 |
| 图标 | @phosphor-icons/react | ^2 |
| HTTP | axios | ^1 |
| 路由 | React Router | ^7 |
| 表单 | React Hook Form | ^7 |
| 状态 | React Context + useReducer | 内置 |

---

## 4. 数据库设计

### 4.1 ER 图

```
users ──┬── subscriptions (1:1)
        │
        ├── applications (1:N) ──── jobs (N:1)
        │
        ├── digest_queue (1:N) ──── jobs (N:1)
        │
jobs ─── (独立，爬虫写入/更新，is_active 软删除)
```

### 4.2 表结构

**users**
| 列 | 类型 | 说明 |
|------|------|------|
| id | UUID (PK) | |
| email | VARCHAR(255) UNIQUE NOT NULL | |
| password_hash | VARCHAR(255) NOT NULL | bcrypt |
| nickname | VARCHAR(100) | |
| token_version | INTEGER DEFAULT 1 | 修改密码时自增，旧 Token 立即失效 |
| created_at | TIMESTAMP DEFAULT NOW() | |
| updated_at | TIMESTAMP | |

**jobs**
| 列 | 类型 | 说明 |
|------|------|------|
| id | UUID (PK) | |
| title | VARCHAR(500) NOT NULL | 岗位名称 |
| company | VARCHAR(255) NOT NULL | 公司名 |
| city | VARCHAR(100) | city 标准化 |
| job_type | VARCHAR(50) | tech/product/operation/finance/design/other |
| salary_min | INTEGER | 月薪下限（nullable = 面议） |
| salary_max | INTEGER | 月薪上限 |
| description | TEXT | JD 原文 |
| skills | TEXT[] | PostgreSQL 数组 |
| source | VARCHAR(50) NOT NULL | shixiseng/niuke/github/... |
| source_url | TEXT NOT NULL | 原始链接（已清洗，剥离追踪参数） |
| source_hash | VARCHAR(64) UNIQUE NOT NULL | SHA256(清洗后的 source_url) — 源内去重 |
| dedup_key | VARCHAR(64) UNIQUE NOT NULL | SHA256(公司名 + 标准化岗位名 + 城市) — 跨源去重 |
| is_active | BOOLEAN DEFAULT true | 岗位是否仍有效 |
| posted_at | TIMESTAMP | 原始发布时间 |
| deadline | TIMESTAMP | 截止日期 (nullable) |
| created_at | TIMESTAMP DEFAULT NOW() | |
| updated_at | TIMESTAMP | |

> **去重机制：** ① URL 入库前清洗（剥离 `?utm_source`、`?ref` 等追踪参数）；② `source_hash` 防同一 URL 重复入库；③ `dedup_key` 基于「公司+岗位+城市」防跨源重复（同一岗位在多个平台发布）。入库时先查 `dedup_key`，命中则合并来源信息。

**subscriptions**
| 列 | 类型 | 说明 |
|------|------|------|
| id | UUID (PK) | |
| user_id | UUID (FK → users) UNIQUE | 1:1 |
| keywords | TEXT[] | 关键词数组 |
| cities | TEXT[] | 城市数组 |
| job_types | TEXT[] | 岗位类型数组 |
| frequency | ENUM('daily', 'weekly') | 推送频率 |
| enabled | BOOLEAN DEFAULT true | |
| last_sent_at | TIMESTAMP | 上次推送时间 |
| created_at | TIMESTAMP | |

**digest_queue**（邮件聚合暂存表）
| 列 | 类型 | 说明 |
|------|------|------|
| id | UUID (PK) | |
| user_id | UUID (FK → users) | |
| job_id | UUID (FK → jobs) | |
| is_sent | BOOLEAN DEFAULT false | 是否已包含在往期推送中 |
| matched_at | TIMESTAMP DEFAULT NOW() | 匹配时间 |

> **邮件聚合流程：** ① 每次爬虫入库后，对每个开启订阅的用户运行关键词/城市匹配；② 命中的岗位写入 `digest_queue`（去重：同一 user+job 只存一次）；③ 每晚 20:00 定时任务，将每个用户未发送的所有 digest_queue 聚合为 **一封 HTML Digest 邮件**（标题："今日 X 个新岗位匹配 —— InternHub"）；④ 发送成功后标记 `is_sent = true`。**单用户每天最多 1 封邮件**，100 封/天免费额度可覆盖 100 个活跃用户。

**applications**
| 列 | 类型 | 说明 |
|------|------|------|
| id | UUID (PK) | |
| user_id | UUID (FK → users) | |
| job_id | UUID (FK → jobs) | |
| status | ENUM('applied','screening','interview','offer','rejected','closed') | closed = 岗位下线自动关闭 |
| notes | TEXT | 用户备注 |
| applied_at | TIMESTAMP DEFAULT NOW() | |
| updated_at | TIMESTAMP | |

### 4.3 索引

```sql
CREATE INDEX idx_jobs_posted_at ON jobs (posted_at DESC);
CREATE INDEX idx_jobs_job_type ON jobs (job_type);
CREATE INDEX idx_jobs_city ON jobs (city);
CREATE INDEX idx_jobs_skills ON jobs USING GIN (skills);
CREATE INDEX idx_jobs_is_active_posted ON jobs (is_active, posted_at DESC) WHERE is_active = true;
-- 中文模糊检索索引（使用 pg_trgm 扩展，Supabase 原生内置支持）
-- CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_jobs_title_trgm ON jobs USING GIN (title gin_trgm_ops);
CREATE INDEX idx_jobs_company_trgm ON jobs USING GIN (company gin_trgm_ops);
CREATE INDEX idx_applications_user_status ON applications (user_id, status);
CREATE UNIQUE INDEX idx_digest_queue_unique ON digest_queue (user_id, job_id);
```

---

## 5. API 设计

### 5.1 认证

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| POST | `/api/auth/register` | ✗ | 注册（email + password + nickname） |
| POST | `/api/auth/login` | ✗ | 登录，返回 `{access_token, refresh_token}` |
| PUT | `/api/auth/password` | ✓ | 修改密码（自增 `token_version`，所有旧 Token 立即失效） |

**Token 撤销机制：**
- JWT payload 中包含 `token_version`（取自 `users.token_version`）
- 每次校验 Token 时，比对 payload 中的 `token_version` 与数据库当前值
- 用户修改密码 → `token_version` 自增 → 所有旧 Token 校验失败
- access_token 有效期 15min，refresh_token 有效期 7d，兼顾安全与体验

### 5.2 岗位

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| GET | `/api/jobs` | ✗ | 分页列表（仅 `is_active = true`） |
| GET | `/api/jobs/{id}` | ✗ | 详情 |
| GET | `/api/jobs/stats` | ✗ | 统计摘要 |

### 5.3 中文模糊搜索实现（pg_trgm）

> **⚠️ 关键：** 岗位内容以中文为主。PostgreSQL 默认的 `simple` 分词器不支持中文。**Supabase 官方托管云数据库不支持 zhparser 或 pg_jieba 扩展**，但原生内置 `pg_trgm`（Trigram 扩展）。它通过 N-gram 算法处理字符串，对中文等 CJK 字符支持良好，结合 GIN 索引进行模糊匹配，能够满足 MVP 阶段的搜索需求，且开箱即用。

```sql
-- 数据库初始化时执行（Supabase SQL Editor 或 Alembic 迁移）
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

```python
# job_service.py — 搜索逻辑
from sqlalchemy import func, or_

def search_jobs(keyword: str, ...):
    query = select(Job).where(Job.is_active == True)

    if keyword:
        # 使用 pg_trgm 进行模糊匹配：title 优先（相似度阈值），description 作为补充
        # 策略：title ILIKE（走 GIN trgm 索引）为主要命中路径，
        #       description ILIKE 为补充（长文本召回）
        pattern = f'%{keyword}%'
        query = query.where(
            or_(
                Job.title.ilike(pattern),       # GIN trgm 索引加速
                Job.company.ilike(pattern),     # GIN trgm 索引加速
                Job.description.ilike(pattern), # 长文本补充召回
            )
        )

    # 按 posted_at 降序排列
    query = query.order_by(Job.posted_at.desc())
    ...
```

> **pg_trgm 工作原理：** 将字符串切分为连续的 3-gram（三元组），例如"前端开发" → `{'前端开', '端开发'}`。查询时通过 GIN 索引快速定位包含相同 trigram 的行，再计算相似度。对中文的模糊匹配效果很好，且 Supabase 所有计划均原生支持。
>
> **进阶优化（可选）：** 若未来需要更精准的语义搜索，可在应用层使用 Python `jieba` 分词，将关键词拆分为独立词条后以 `&` 连接为 tsquery，配合 `simple` 分词器的 tsvector 使用。

**查询参数 — GET /api/jobs:**

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| page | int | 1 | |
| size | int | 20 | 最大 50 |
| keyword | str | — | 搜索 title + company + description（pg_trgm 模糊匹配，GIN 索引加速） |
| job_type | str | — | tech/product/operation/... |
| city | str | — | |
| salary_min | int | — | |
| sort | str | latest | latest / deadline / salary |

### 5.4 订阅

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| POST | `/api/subscriptions` | ✓ | 创建/覆盖更新 |
| GET | `/api/subscriptions` | ✓ | 获取当前订阅 |

### 5.5 投递记录

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| POST | `/api/applications` | ✓ | 新增投递 `{job_id}` |
| GET | `/api/applications` | ✓ | 列表（按 status 分组返回） |
| PATCH | `/api/applications/{id}/status` | ✓ | 更新状态 `{status}` |
| PUT | `/api/applications/{id}` | ✓ | 编辑 `{notes}` |
| DELETE | `/api/applications/{id}` | ✓ | 删除记录 |

### 5.6 统一响应格式

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

错误响应：
```json
{
  "code": 401,
  "message": "Invalid credentials",
  "data": null
}
```

### 5.7 分页响应

```json
{
  "code": 0,
  "data": {
    "items": [...],
    "total": 156,
    "page": 1,
    "size": 20,
    "pages": 8
  }
}
```

---

## 6. 爬虫设计

### 6.1 数据源（MVP 3-5 个）

| 源 | 类型 | 抓取方式 | 难度 |
|------|------|------|------|
| 实习僧 (shixiseng.com) | 招聘平台 | httpx + HTML 解析 | 中 |
| 牛客网 (nowcoder.com) | 校招社区 | httpx + HTML 解析 | 中 |
| GitHub SimplifyJobs | 开源仓库 | GitHub API / raw JSON | 低 |
| 企业校招官网 | 直招 | httpx + CSS 选择器 | 中高 |
| 北大/清华 BBS | 论坛 | httpx + HTML 解析 | 低 |

### 6.2 爬虫架构（独立 Worker）

```
Worker 进程 (/scraper/worker.py)
│
├── Cron 触发 → scrape_all()
│   ├── 1. fetch_all_sources()     # 并行抓取 3+ 源
│   ├── 2. normalize(job)          # 字段标准化
│   ├── 3. clean_url(url)          # 剥离追踪参数（?utm_*, ?ref, ?spm 等）
│   ├── 4. dedupe_check(job)       # 双重去重：
│   │   ├── source_hash = SHA256(cleaned_url)  → 源内去重
│   │   └── dedup_key   = SHA256(company + title_norm + city) → 跨源去重
│   └── 5. upsert(job)             # dedup_key 已存在？更新字段 : 新增
│
├── Cron 触发 → validate_active()
│   ├── SELECT jobs WHERE is_active AND posted_at > NOW() - INTERVAL '30 days'
│   ├── 对每个 URL 发 HEAD 请求，404/下线 → SET is_active = false
│   └── 联动关闭投递：岗位下线时，将该岗位所有 applied/screening 状态的
│       application 自动更新为 closed，并写入通知队列
│
├── Cron 触发 → cleanup_digest_queue()
│   ├── 时间门控：仅当月 1 日 06:00–08:00 窗口执行（避免每 8h 重复扫描）
│   └── DELETE FROM digest_queue WHERE is_sent = true AND matched_at < NOW() - INTERVAL '30 days'
│
└── 调度方式：Railway Cron Jobs（每 8h 触发 worker.py）
    或 GitHub Actions scheduled workflow（免费，无平台锁定）
    ⚠️ cleanup 逻辑内部含时间门控，每月仅实际执行 1 次
```

```python
# 基类
class BaseScraper:
    source: str                     # 来源标识（shixiseng/niuke/github）

    async def fetch() -> list[dict] # 抓取原始数据
    def parse(raw) -> list[dict]    # 解析为标准字段
    @staticmethod
    def clean_url(url: str) -> str  # 剥离追踪参数
    @staticmethod
    def dedup_key(company, title, city) -> str  # 跨源去重键

# URL 清洗规则
TRACKING_PARAMS = ['utm_source', 'utm_medium', 'utm_campaign',
                   'ref', 'spm', 'track', 'timestamp', '_t']
```

### 6.3 字段标准化映射

| 标准字段 | 实习僧 | 牛客 | GitHub |
|----------|--------|------|--------|
| title | `.job-title` | `.position` | `title` |
| company | `.company-name` | `.corp` | `company` |
| city | `.location` | `.city` | parse description |
| salary | `.salary` | `.pay` | manual parse |
| description | `.jd-content` | `.desc` | `body` |

---

## 7. 项目目录结构

```
internhub/
├── frontend/
│   ├── public/
│   │   └── og-image.png            # 社交分享图
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Navbar.tsx
│   │   │   │   ├── Footer.tsx
│   │   │   │   └── Layout.tsx
│   │   │   ├── jobs/
│   │   │   │   ├── JobCard.tsx
│   │   │   │   ├── JobList.tsx
│   │   │   │   ├── JobDetail.tsx
│   │   │   │   └── JobFilters.tsx
│   │   │   ├── applications/
│   │   │   │   ├── KanbanBoard.tsx
│   │   │   │   ├── KanbanColumn.tsx
│   │   │   │   └── ApplicationCard.tsx
│   │   │   ├── subscriptions/
│   │   │   │   └── SubscriptionForm.tsx
│   │   │   └── ui/
│   │   │       ├── Button.tsx
│   │   │       ├── Tag.tsx
│   │   │       ├── Badge.tsx
│   │   │       └── SearchInput.tsx
│   │   ├── hooks/
│   │   │   ├── useJobs.ts
│   │   │   ├── useApplications.ts
│   │   │   └── useAuth.ts
│   │   ├── pages/
│   │   │   ├── HomePage.tsx
│   │   │   ├── JobDetailPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── SubscriptionPage.tsx
│   │   │   ├── LoginPage.tsx
│   │   │   └── RegisterPage.tsx
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   └── constants.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── index.html
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── job.py
│   │   │   ├── subscription.py
│   │   │   └── application.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── job.py
│   │   │   └── application.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── jobs.py
│   │   │   ├── subscriptions.py
│   │   │   └── applications.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── job_service.py
│   │   │   └── scraper_service.py
│   │   └── scraper/
│   │       ├── __init__.py
│   │       ├── scheduler.py
│   │       ├── base.py
│   │       ├── shixiseng.py
│   │       ├── niuke.py
│   │       └── github_jobs.py
│   ├── alembic/
│   │   └── versions/
│   ├── alembic.ini
│   ├── requirements.txt
│   └── Dockerfile
│
└── README.md
```

---

## 8. 部署方案

| 层 | 平台 | 说明 |
|------|------|------|
| 前端 | **Vercel** | 免费，自动 GitHub 部署，全球 CDN |
| 后端 | **Railway** | FastAPI 部署，环境变量管理，免费额度 |
| 数据库 | **Supabase** | 免费 PostgreSQL，500MB，自动备份 |
| 邮件 | **Resend** | 免费 100 封/天，API 简单 |

---

## 9. 开发路线图

### Phase 1：骨架搭建（Week 1-2）
- [ ] 项目初始化：Vite + Tailwind + FastAPI 项目结构
- [ ] 数据库表 + Alembic 迁移
- [ ] 用户注册/登录 API + JWT
- [ ] 前端 Login/Register 页面

### Phase 2：核心功能（Week 3-5）
- [ ] 爬虫模块：3 个数据源 + 定时调度
- [ ] 岗位 API（CRUD + 搜索 + 筛选 + 分页）
- [ ] 前端首页：JobCard + JobList + Filters
- [ ] 前端详情页：JobDetail
- [ ] 动画：stagger + hover + scroll-reveal

### Phase 3：用户功能（Week 6-7）
- [ ] 投递记录 API + Kanban 看板
- [ ] 订阅 API + 订阅表单页面
- [ ] 邮件推送服务（Resend 集成）

### Phase 4：打磨上线（Week 8）
- [ ] 动画微调、响应式适配
- [ ] 错误处理（404/500/网络异常）
- [ ] 部署：Vercel + Railway + Supabase
- [ ] README 撰写 + GitHub 开源

---

## 10. 自我审查记录

### 10.1 边界情况
- 爬虫目标站反爬 → 降低频率 + User-Agent 轮换 + 必要时用 Playwright
- **URL 追踪参数导致重复** → 入库前清洗追踪参数（`?utm_*`, `?ref`, `?spm` 等）
- **跨源重复岗位** → `dedup_key = SHA256(公司 + 标准化岗位名 + 城市)` 二级去重
- 空搜索结果 → 显示空状态插画 + "试试其他关键词？"
- **过期/下线岗位** → `is_active` 软删除 + 存活性校验 HEAD 请求，404 即标记失效；**联动关闭**所有关联的 applied/screening 状态投递记录为 closed
- 邮件推送频率超标 → Digest 聚合机制，单用户每天最多 1 封邮件
- **digest_queue 膨胀** → 每月定时清理 30 天前已发送记录
- 邮件推送失败 → 静默重试 3 次，失败记录日志，不阻塞其他用户
- JWT 过期 → 前端 axios interceptor 自动 refresh
- **多实例爬虫重复** → Worker 独立部署，单实例执行，避免 Web 扩容导致的并发爬取

### 10.2 安全措施
- 密码 bcrypt 哈希
- **JWT 强制撤销** → `token_version` 机制，修改密码后所有旧 Token 立即失效
- JWT access token 15min，refresh token 7d
- API 输入 Pydantic 校验，防 SQL 注入（ORM 参数化查询）
- CORS 白名单
- Railway 限流 + Supabase RLS（Row Level Security）

### 10.3 没有占位符
- ✅ 所有功能模块已明确
- ✅ 所有 API 端点已列出
- ✅ 所有数据库表结构已定义
- ✅ 技术栈版本已指定
- ✅ 部署方案已选型

---

> **下一步：** 请审核此设计文档。确认后将进入实现计划阶段。
