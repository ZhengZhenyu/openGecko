# openGecko

<div align="center">

<img src="openGecko-Horizontal.png" alt="openGecko Logo" width="320" />

**多社区运营管理平台 · Manage All, Publish Everywhere**

为开源社区量身打造的企业级多租户内容管理与运营平台

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3.5+-green.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-teal.svg)](https://fastapi.tiangolo.com/)
[![Backend CI](https://github.com/your-org/openGecko/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/your-org/openGecko/actions/workflows/backend-ci.yml)

</div>

---

## 目录

- [项目简介](#-项目简介)
- [核心功能](#-核心功能)
- [快速体验（普通用户）](#-快速体验普通用户)
- [开发者指南](#-开发者指南)
- [生产部署](#-生产部署)
- [功能模块详解](#-功能模块详解)
- [技术架构](#-技术架构)
- [开发路线图](#-开发路线图)
- [贡献指南](#-贡献指南)

---

## 🦎 项目简介

openGecko 是一款面向**开源社区运营团队**的多租户内容管理平台。无论你是同时运营多个开源社区，还是需要将同一篇内容分发到微信公众号、Hugo 博客、CSDN、知乎等多个渠道，openGecko 都能帮你统一管理、一键发布。

### 适用人群

| 角色 | 使用场景 |
|------|---------|
| **社区运营** | 统一管理多社区内容，排期发布，追踪发布效果 |
| **内容创作者** | 在线编辑 Markdown，上传 Word 文档自动转换，协作编辑 |
| **委员会成员** | 管理理事会信息、安排和追踪会议，个人工作台查看任务 |
| **平台管理员** | 跨社区用户管理，RBAC 权限分配，审计日志查看 |

---

## ✨ 核心功能

### 🏢 多租户 & 权限
- **三级 RBAC**：超级管理员 / 社区管理员 / 普通用户，FastAPI Depends 依赖注入强制鉴权
- **社区级数据隔离**：共享数据库，`community_id` 强过滤，跨社区数据零泄漏
- **内容所有权**：Owner + 协作者机制，支持所有权转让和多人协同编辑

### 📝 内容管理
- **多格式上传**：支持 `.docx` / `.md` 文件上传，自动提取图片、转换格式
- **富文本编辑**：基于 md-editor-v3 的在线 Markdown 编辑器，实时预览
- **内容工作流**：`draft → reviewing → approved → published` 状态流转
- **日历排期**：FullCalendar 可视化内容排期，支持拖拽调整发布时间

### 🚀 多渠道发布

| 渠道 | 能力 |
|------|------|
| **微信公众号** | 调用 API 创建草稿，自动上传图片，封面图管理 |
| **Hugo** | 生成带 front matter 的 `.md` 文件，直接写入博客仓库 |
| **CSDN** | 一键复制适配格式，支持 Cookie 认证 |
| **知乎** | 一键复制适配格式 |

### 🏛️ 社区治理
- **委员会管理**：创建委员会、管理成员，支持多届 / 多类型委员会
- **会议管理**：安排会议、追踪进度（计划中 / 进行中 / 已完成），支持导出 ICS 日历
- **个人工作台**：跨社区汇总「我负责的」内容与会议，工作状态统计

### 📊 数据 & 安全
- **发布记录追踪**：完整的发布历史，渠道维度统计
- **审计日志**：关键操作全量记录，支持追溯
- **加密存储**：渠道凭证 Fernet 加密；JWT 认证；bcrypt 密码哈希
- **邮件通知**：SMTP 密码重置邮件，可配置发件人

---

## 🖥️ 快速体验（普通用户）

### 系统要求

Docker 方式（推荐）：
- Docker 20.10+ & Docker Compose v2+

本地运行方式：
- Python 3.11+
- Node.js 20+ & npm
- Make（macOS / Linux 自带）

### Docker 一键启动

```bash
# 1. 克隆项目
git clone https://github.com/your-org/openGecko.git
cd openGecko

# 2. 初始化配置文件
cp backend/.env.example backend/.env
# ⚠️ 生产环境务必编辑 backend/.env，修改 JWT_SECRET_KEY 为强随机字符串

# 3. 启动
docker compose up -d
```

启动后访问：
- 🖥️ **平台界面**：http://localhost
- 📖 **API 文档**：http://localhost:8000/docs

### 首次使用流程

1. 使用 `.env` 中配置的默认账号登录（默认 `admin` / `admin123`）
2. 系统引导你**创建正式管理员账号**（用户名、密码、邮箱）
3. 正式账号创建后，默认 `admin` 账号**自动删除**（安全机制，不可跳过）
4. 进入「设置」→「渠道配置」，填写各发布渠道的凭证（微信 AppID/Secret 等）
5. 进入「社区管理」创建第一个社区，邀请成员加入

### 渠道配置说明

| 渠道 | 所需凭证 | 获取方式 |
|------|---------|---------|
| 微信公众号 | AppID + AppSecret | 微信公众平台 → 开发 → 基本配置 |
| Hugo | 博客仓库路径 | 本地 Hugo 仓库绝对路径 |
| CSDN | Cookie | 浏览器 DevTools → Application → Cookies |
| 知乎 | Cookie | 浏览器 DevTools → Application → Cookies |

> 所有凭证均使用 Fernet 对称加密存储，密钥派生自 `JWT_SECRET_KEY`。

---

## 🛠️ 开发者指南

### 本地开发环境搭建

```bash
# 1. 克隆项目
git clone https://github.com/your-org/openGecko.git
cd openGecko

# 2. 一键初始化（创建 Python venv、安装依赖、生成 .env）
make setup

# 3. 启动前后端开发服务器（热重载）
make dev
```

启动后：
- 🖥️ **前端 (Vite)**：http://localhost:3000
- 📖 **后端 API + Swagger 文档**：http://localhost:8000/docs

单独启动：

```bash
make dev-backend    # 仅启动 FastAPI（端口 8000）
make dev-frontend   # 仅启动 Vite（端口 3000）
```

### 环境变量

复制并编辑 `backend/.env`：

```env
# 数据库 — 开发用 SQLite，生产换 PostgreSQL
DATABASE_URL=sqlite:///./opengecko.db

# ⚠️ 生产环境必须改为强随机字符串
JWT_SECRET_KEY=your-secret-key-change-in-production

# 默认管理员（仅首次启动时创建，创建正式账号后自动删除）
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin123
DEFAULT_ADMIN_EMAIL=admin@example.com

# （可选）SMTP 邮件 — 用于密码重置
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-email-password
SMTP_FROM_EMAIL=noreply@example.com
```

完整配置说明见 [docs/CONFIGURATION.md](docs/CONFIGURATION.md)。

### 项目结构

```
openGecko/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI 路由（薄层，不含业务逻辑）
│   │   ├── models/       # SQLAlchemy ORM 模型
│   │   ├── schemas/      # Pydantic 请求/响应 Schema
│   │   ├── services/     # 业务逻辑、外部集成（微信、Hugo 等）
│   │   ├── core/         # 安全（JWT/bcrypt/Fernet）、依赖注入、日志
│   │   ├── config.py     # Pydantic Settings（读取 .env）
│   │   └── database.py   # 数据库连接、Session、初始化
│   ├── alembic/          # 数据库迁移文件
│   ├── tests/            # pytest 测试套件
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/          # Axios 请求模块（自动附加 JWT + X-Community-Id）
│       ├── stores/       # Pinia 状态（auth、community、user）
│       ├── views/        # 页面组件（21 个）
│       ├── components/   # 共享组件
│       └── router/       # Vue Router（含路由守卫）
├── docs/                 # 设计文档、需求文档、架构文档
├── docker-compose.yml
└── Makefile
```

### 数据库迁移

```bash
cd backend

# 修改 app/models/ 后，生成迁移文件
alembic revision --autogenerate -m "描述变更内容"

# 检查生成的迁移文件（路径：alembic/versions/）
# 然后应用
alembic upgrade head

# 回滚一个版本
alembic downgrade -1
```

### 测试

```bash
cd backend

# 运行全部测试（含覆盖率报告，要求 ≥ 80%）
pytest tests/ -v --cov=app --cov-report=term-missing

# 快速运行（不统计覆盖率）
pytest tests/ -q --no-cov

# 运行单个测试文件
pytest tests/test_contents_api.py -v --no-cov
```

### 代码质量

```bash
cd backend

# 格式化（line-length=120）
black app/

# Lint
ruff check app/

# 类型检查
mypy app/ --ignore-missing-imports
```

### Git 工作流

```
main          ← 生产就绪
develop       ← 功能集成
feature/xxx   ← 新功能
fix/xxx       ← Bug 修复
```

提交信息格式（Conventional Commits，中文描述）：

```
feat: 新增会议 ICS 导出功能
fix: 修复跨社区数据隔离漏洞
docs: 更新渠道配置说明
```

> `git push` 前请先确认是否与后续改动一并推送。详见 [docs/GIT_WORKFLOW.md](docs/GIT_WORKFLOW.md)。

---

## 🐳 生产部署

### 前置条件

- Docker 20.10+ & Docker Compose v2+
- 域名（可选，用于 HTTPS）
- PostgreSQL（可选，推荐替换 SQLite）

### 生产模式启动

```bash
# 1. 配置生产环境变量
cp backend/.env.example backend/.env
vim backend/.env
# 重要：修改 JWT_SECRET_KEY、DATABASE_URL、DEFAULT_ADMIN_PASSWORD

# 2. 以生产模式启动（Gunicorn + 资源限制 + 日志驱动）
make docker-prod

# 3. 查看服务状态
make docker-status

# 4. 查看日志
make docker-logs
```

访问地址：
- 🌐 **前端（Nginx 代理）**：http://localhost:80
- 🔧 **后端 API**：http://localhost:8000

停止服务：

```bash
make docker-prod-down
```

### 推荐生产配置清单

- [ ] `JWT_SECRET_KEY` 替换为 64 位以上随机字符串（`openssl rand -hex 32`）
- [ ] `DATABASE_URL` 切换为 PostgreSQL（`postgresql://user:pass@host/db`）
- [ ] `DEFAULT_ADMIN_PASSWORD` 修改为强密码
- [ ] 配置 SMTP 邮件（密码重置功能需要）
- [ ] Nginx 配置 HTTPS（Let's Encrypt）
- [ ] 定期备份 `uploads/` 目录和数据库

### 数据持久化

Docker Compose 已配置以下挂载：

```yaml
volumes:
  - ./uploads:/app/uploads   # 上传文件（图片、文档）
  - ./data:/app/data          # 数据库文件（SQLite 模式）
```

PostgreSQL 模式下请自行配置数据卷和备份策略。

---

## 📦 功能模块详解

### 内容管理

```
内容列表 → 新建/编辑内容 → 状态流转 → 发布
```

- **状态**：`draft（草稿）→ reviewing（审核中）→ approved（已批准）→ published（已发布）`
- **工作状态**（独立于内容状态）：`planning / in_progress / completed`
- **权限**：内容 owner、协作者、社区 admin、superuser 均可编辑
- **日历视图**：按 `scheduled_publish_at` 可视化排期，支持拖拽

### 渠道发布

```
内容详情页 → 选择渠道 → 填写参数 → 提交发布 → 查看发布记录
```

- 微信发布前会自动将本地图片上传至微信 CDN 并替换链接
- 发布失败时自动记录错误信息，方便排查

### 社区治理

- **委员会**：支持多个委员会，每个委员会独立管理成员
- **会议**：绑定委员会，支持设置地点类型（线上 / 线下 / 混合），导出 ICS 日历
- **工作台**：`/my-work` 页面汇总跨社区的所有分配任务

### 权限矩阵

| 操作 | superuser | community admin | user |
|------|:---------:|:---------------:|:----:|
| 创建/删除社区 | ✅ | ❌ | ❌ |
| 管理社区成员 | ✅ | ✅ | ❌ |
| 编辑任意内容 | ✅ | ✅ | 仅自己负责的 |
| 配置发布渠道 | ✅ | ✅ | ❌ |
| 查看审计日志 | ✅ | ✅ | ❌ |
| 工作量总览 | ✅ | ❌ | ❌ |

---

## 🏗️ 技术架构

### 技术栈

| 层级 | 技术 | 版本 | 说明 |
|------|------|------|------|
| **前端框架** | Vue 3 + Vite | 3.5 / 6.x | Composition API，`<script setup lang="ts">` |
| **前端状态** | Pinia | 2.x | 按领域拆分 Store（auth / community / user）|
| **UI 组件库** | Element Plus | 2.x | 企业级组件，配合 LFX 浅色主题 |
| **HTTP 客户端** | Axios | 1.x | 拦截器自动附加 JWT Token 和 X-Community-Id |
| **后端框架** | FastAPI | 0.115+ | 异步，自动生成 OpenAPI 文档 |
| **ORM** | SQLAlchemy 2.0 | 2.x | 声明式模型，Alembic 迁移 |
| **数据校验** | Pydantic v2 | 2.x | 请求/响应 Schema 全量校验 |
| **数据库** | SQLite / PostgreSQL | — | 开发用 SQLite，生产推荐 PostgreSQL |
| **认证** | JWT + bcrypt | — | `python-jose` + `passlib` |
| **加密** | Fernet | — | 渠道凭证加密，密钥派生自 JWT_SECRET_KEY |
| **容器化** | Docker Compose | v2 | 开发 / 生产双 compose 文件 |

### 关键设计决策

**多租户隔离**  
所有社区范围的数据查询都通过 `community_id` 列过滤。前端每个请求携带 `X-Community-Id` Header，后端通过 `get_current_community` 依赖注入强制隔离，API 层不信任前端传入的 community 参数。

**内容所有权模型**  
- `created_by_user_id`：不可变，记录谁创建了内容
- `owner_id`：可转让，控制谁有完整编辑权限
- `collaborators`：多对多，共同编辑者

**渠道凭证安全**  
凭证写入数据库之前用 Fernet（密钥由 `JWT_SECRET_KEY` 派生）加密，读取时解密使用，API 返回时对敏感字段脱敏（仅显示末 4 位）。

### API 文档

开发模式下访问 http://localhost:8000/docs 查看完整 Swagger UI，或访问 http://localhost:8000/redoc 查看 ReDoc 文档。

---

## 🗺️ 开发路线图

### Phase 1 — 基础认证、RBAC 与多租户 ✅

- ✅ JWT 认证 + 首次启动初始化流程
- ✅ 三级 RBAC（superuser / admin / user）
- ✅ 内容所有权与协作者机制
- ✅ 多租户数据隔离（community_id 强过滤）
- ✅ 社区管理 CRUD + 前端页面
- ✅ 用户管理 + 前端页面
- ✅ 审计日志系统
- ✅ 密码重置邮件（SMTP）

### Phase 2 — 内容管理与多渠道发布 ✅

- ✅ DOCX / Markdown 文件上传与格式转换
- ✅ 在线 Markdown 编辑器
- ✅ 内容工作流（draft → reviewing → approved → published）
- ✅ 微信公众号 API 发布（草稿 + 图片上传）
- ✅ Hugo / CSDN / 知乎发布
- ✅ 发布记录追踪与渠道统计
- ✅ 日历排期视图（FullCalendar）

### Phase 3 — 社区治理 ✅

- ✅ 委员会管理（多届 / 多类型）
- ✅ 会议管理（状态追踪 + ICS 导出）
- ✅ 个人工作台（跨社区任务汇总）
- ✅ 工作量总览（superuser 视角）

### Phase 4 — 可视化分析仪表板 📋

- [ ] ECharts 多维度内容分析图表
- [ ] 渠道 / 作者 / 分类维度统计
- [ ] 发布趋势时序分析
- [ ] 社区活跃度对比

### Phase 5 — 高级工作流 📋

- [ ] Kanban 看板视图，拖拽改变状态
- [ ] 批量操作（批量审批、批量发布）
- [ ] 内容模板库
- [ ] Webhook / 外部集成

详见 [docs/plannings/01-实施计划.md](docs/plannings/01-实施计划.md)

---

## 🤝 贡献指南

欢迎贡献代码！请先阅读以下指引：

1. Fork 本仓库，从 `develop` 分支创建特性分支
2. 遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范（中文描述）
3. 后端代码需通过 `pytest`（覆盖率 ≥ 80%）和 `ruff check`
4. 前端代码需通过 `npx vue-tsc --noEmit` 类型检查
5. 提交 PR 到 `develop` 分支，等待 CI 通过后请求 Review

更多细节见：
- [CONTRIBUTING.md](docs/CONTRIBUTING.md) — 贡献流程
- [DEVELOPMENT.md](docs/DEVELOPMENT.md) — 开发环境与规范
- [GIT_WORKFLOW.md](docs/GIT_WORKFLOW.md) — 分支策略与提交规范

### 本地 CI 快速验证

```bash
# 后端：格式 + Lint + 测试
cd backend
black app/ && ruff check app/ && pytest tests/ -q --no-cov

# 前端：类型检查 + 构建
cd frontend
npx vue-tsc --noEmit && npx vite build
```

---

## 📚 文档索引

| 文档 | 说明 |
|------|------|
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | 环境变量、渠道配置、部署配置 |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | 开发环境、代码规范、测试指南 |
| [docs/GIT_WORKFLOW.md](docs/GIT_WORKFLOW.md) | 分支策略与提交规范 |
| [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) | 目录结构详解 |
| [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) | 贡献流程 |
| [docs/design/01-系统架构设计.md](docs/design/01-系统架构设计.md) | 系统架构设计 |
| [docs/design/02-数据库详细设计.md](docs/design/02-数据库详细设计.md) | 数据库详细设计 |
| [docs/requirements/01-需求分析文档.md](docs/requirements/01-需求分析文档.md) | 需求分析文档 |
| [docs/plannings/01-实施计划.md](docs/plannings/01-实施计划.md) | 实施计划与路线图 |

---

## 📄 License

[MIT License](LICENSE) © openGecko Contributors

---

<div align="center">

**openGecko** — Manage All, Publish Everywhere 🦎

Made with ❤️ for Open Source Communities

</div>




