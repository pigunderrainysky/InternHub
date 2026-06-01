# InternHub 本地测试报告

> 2026-06-01 | 测试环境：Windows 11 · Python 3.12.4 · SQLite 3.45.3 · Node.js 22.19.0

---

## 1. 测试策略

由于项目目标数据库为 **Supabase PostgreSQL**（含 pg_trgm、UUID、ARRAY、GIN 索引等扩展），本地无 PostgreSQL 环境，采用分层测试策略：

| 层 | 策略 | 工具 |
|----|------|------|
| 纯逻辑函数（密码、Token、URL清洗、薪资解析） | 直接单元测试 | pytest |
| ORM 依赖函数（CRUD、查询） | SQLite 内存库 + 测试模型适配 | pytest + SQLite |
| 路由/HTTP 层 | 暂未测试（需运行中的数据库） | FastAPI TestClient |
| 爬虫 | 暂未测试（需目标网站可访问） | 手动触发或 mock |
| 前端组件 | TypeScript 类型检查 + 构建通过 | tsc + vite build |

---

## 2. 测试基础设施

### 2.1 遇到的问题

#### 问题 1：SQLite 不支持 PostgreSQL ARRAY 类型

**现象：**
```
sqlalchemy.exc.CompileError: Compiler can't render element of type ARRAY
```

**原因：** 应用模型使用 `ARRAY(String)` 定义 `skills`、`keywords` 等字段，SQLite 不支持。

**解决措施：** 创建独立的测试模型（`tests/conftest.py`），将 `ARRAY(String)` 替换为 `JSON` 类型，`UUID` 替换为 `String(36)`，保持 ORM 兼容性。

#### 问题 2：passlib 与 bcrypt 5.x 不兼容

**现象：** 在 Phase 1 开发中已发现并修复。passlib 1.7.4 调用 `_bcrypt.__about__.__version__` 在 bcrypt 5.x 中不存在。

**解决措施：** `auth_service.py` 改用 `bcrypt` 库直接调用，不含 passlib 依赖。

#### 问题 3：测试数据污染导致断言不准确

**现象：** `test_keyword_no_match` 测试失败 — 测试认为"后端开发"不匹配关键词["前端", "设计"]，但默认 description 含"前端开发"，导致 keyword 匹配通过。

**解决措施：** 测试 fixture 使用显式参数，避免默认值中的隐藏匹配。

### 2.2 Pydantic V2 弃用警告

```
PydanticDeprecatedSince20: Support for class-based `config` is deprecated
```

- `config.py` 的 `Settings` 和 `schemas/subscription.py` 的 `SubscriptionOut` 使用 `class Config:` 语法
- 不影响功能，Pydantic V3 发布前需迁移到 `model_config = ConfigDict(...)`

---

## 3. 测试结果

### 3.1 通过情况

```
 65/65 测试全部通过
   执行时间：5.2s
   测试文件：3 个
   测试类：9 个
```

### 3.2 模块覆盖率

| 模块 | 语句 | 覆盖率 | 备注 |
|------|------|--------|------|
| `scraper/base.py` | 82 | **95%** | URL清洗/去重/薪资解析/类型推断/城市标准化 |
| `schemas/subscription.py` | 28 | **96%** | 含空订阅验证（Bug #4 修复） |
| `config.py` | 15 | **100%** | 配置加载 |
| `models/`（5个文件） | 84 | **100%** | 模型定义导入 |
| `services/auth_service.py` | 60 | 58% | 密码/JWT 函数全测，注册/认证需PG |
| `services/digest_service.py` | 120 | 30% | 匹配逻辑全测，邮件发送需Resend |
| Routers / 爬虫 / 其他 | 767 | 0% | 需运行中DB或外部服务 |

### 3.3 测试用例清单

**test_auth_service.py**（14 个测试）
```
TestPasswordHashing
  test_hash_and_verify            ✅ bcrypt 哈希 + 验证
  test_verify_wrong_password      ✅ 错误密码拒绝
  test_hash_truncation_72_bytes   ✅ bcrypt 72字节截断边界

TestTokenCreation
  test_access_token_contains_claims   ✅ 含 sub/type/tv/exp
  test_refresh_token_contains_claims  ✅ type=refresh
  test_decode_invalid_token           ✅ 无效token→None
  test_token_version_mismatch         ✅ version不匹配→拒绝

TestUserCRUDWithSQLite
  test_register_flow                  ✅ 完整注册流程
  test_duplicate_email_prevented      ✅ 重复邮箱→异常
  test_email_lowercase_normalized     ✅ 大小写+空白→标准化
  test_query_by_email                 ✅ 按邮箱查询
  test_authenticate_flow              ✅ 密码验证流程
  test_change_password_and_bump_version ✅ 改密+token_version+1
  test_wrong_old_password_no_change   ✅ 错误旧密码→不变更
```

**test_scraper_base.py**（30 个测试）
```
TestURLCleaning (6)
  - utm_params / ref / tracking_params 清理
  - 合法参数保留 / 无参数URL / fragment保存

TestDedup (5)
  - source_hash 确定性 / 不同URL不同hash
  - dedup_key 空白标准化 / 大小写不敏感 / 空城市

TestSalaryParsing (6)
  - 月薪范围 / 日薪转月薪(×20) / 单值
  - "面议"→None / 空值→None / 小数值

TestCityNormalization (4)
  - 去"市"后缀 / 区县级拒绝 / 正常城市 / 空值

TestJobTypeInference (9)
  - 前端/后端Java/算法→tech / 产品→product
  - 运营→operation / 金融→finance / 设计→design
  - 英文→tech / 未知→other
```

**test_subscription_validation.py**（21 个测试）
```
TestSubscriptionSchema (7)
  - 合法订阅 / 空订阅被拒(Bug#4) / 仅关键词/城市/类型
  - 无效频率 / 默认值

TestDigestMatching (14)
  - 标题匹配 / 描述匹配 / 无匹配
  - 城市精确+包含匹配 / job_type匹配
  - 多条件AND逻辑 / 部分不匹配→整体拒绝
  - 空条件→False(Bug#4双防) / 大小写 / null处理
```

---

## 4. 待完成测试

以下测试需要 PostgreSQL / Supabase 环境或外部服务才能运行：

| 模块 | 依赖 | 优先级 |
|------|------|--------|
| `routers/*.py`（API 端点） | Supabase PG | 高 |
| `services/job_service.py`（pg_trgm 搜索） | Supabase PG + pg_trgm | 高 |
| `services/application_service.py`（CRUD） | Supabase PG | 高 |
| `services/scraper_service.py`（upsert/validate） | Supabase PG | 中 |
| `services/digest_service.py`（Resend 邮件） | Resend API Key | 中 |
| `scraper/*.py`（三个爬虫） | 目标网站可访问 | 中 |
| 前端组件（React Testing Library） | vitest + jsdom | 中 |

### Supabase 环境就绪后的测试命令

```bash
# 1. 设置环境变量
export DATABASE_URL="postgresql://postgres:...@db.xxx.supabase.co:5432/postgres"

# 2. 数据库迁移
alembic upgrade head

# 3. 运行完整测试（含路由层）
pytest tests/ --cov=app --cov-report=html

# 4. API 文档检查
curl http://localhost:8000/api/health
open http://localhost:8000/docs
```

---

## 5. 前端验证

| 检查项 | 结果 |
|--------|------|
| TypeScript 类型检查 | ✅ 0 errors |
| Vite 生产构建 | ✅ 532KB JS + 35KB CSS |
| ESLint | ✅ 通过（无配置违规） |

---

## 6. 总结

- **通过率：** 65/65（100%）
- **发现 Bug：** 1 个（测试数据污染，非代码问题）
- **代码覆盖率：** 27%（纯逻辑模块 95%+，API/爬虫层需PG环境）
- **弃用警告：** 2 处（Pydantic V2 Config → ConfigDict）
- **结论：** 纯逻辑函数、密码加密、JWT令牌、订阅匹配引擎、爬虫工具函数均通过测试。路由层和数据库层测试需 Supabase 环境就绪后继续。
