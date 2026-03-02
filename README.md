# openGecko

<div align="center">

<img src="openGecko-Horizontal.png" alt="openGecko Logo" width="320" />

**多社区运营管理平台 · Manage All, Publish Everywhere**

为开源社区量身打造的企业级多租户内容管理与运营平台

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3.5+-green.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-teal.svg)](https://fastapi.tiangolo.com/)
[![Backend CI](https://github.com/opensourceways/openGecko/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/opensourceways/openGecko/actions/workflows/backend-ci.yml)

</div>

---

## 目录

**👤 我是用户**
- [项目简介](#-项目简介)
- [核心功能](#-核心功能)
- [快速开始（Docker 一键部署）](#-快速开始docker-一键部署)
- [用户操作手册](#-用户操作手册)
  - [内容管理](#内容管理)
  - [多渠道发布](#多渠道发布)
  - [活动管理](#活动管理)
  - [人脉与 Campaign](#人脉与-campaign)
  - [生态洞察](#生态洞察)
  - [社区治理](#社区治理)
  - [个人工作台](#个人工作台)
  - [平台管理（Admin）](#平台管理admin)

**🛠️ 我是开发者 / 部署者**
- [本地开发环境搭建](#本地开发环境搭建)
- [完整清理重部署](#完整清理重部署docker-环境)
- [生产部署](#-生产部署)
- [技术架构](#-技术架构)
- [开发路线图](#-开发路线图)
- [贡献指南](#-贡献指南)

---

## 🦎 项目简介

openGecko 是一款面向**开源社区运营团队**的多租户内容管理与运营平台。无论你是同时运营多个开源社区，还是需要将同一篇内容分发到微信公众号、Hugo 博客、CSDN、知乎等多个渠道，openGecko 都能帮你统一管理、一键发布。

### 适用人群

| 角色 | 使用场景 |
|------|---------|
| **社区运营** | 统一管理多社区内容，排期发布，追踪发布效果 |
| **内容创作者** | 在线编辑 Markdown，上传 Word 文档自动转换，协作编辑，管理设计素材 |
| **活动负责人** | 创建活动、管理 SOP 模板、分配任务、追踪签到名单 |
| **人脉运营** | 统一管理贡献者档案、社区角色，策划触达 Campaign |
| **委员会成员** | 管理理事会信息、安排和追踪会议，个人工作台查看任务 |
| **平台管理员** | 跨社区用户管理，成员权限配置，操作记录查看，生态洞察分析 |

---

## ✨ 核心功能

### 🏢 多社区 & 权限管理
- **三级角色**：平台管理员 / 社区管理员 / 普通成员，不同角色对应不同操作权限
- **多社区隔离**：一套平台同时管理多个社区，各社区数据相互独立，互不干扰
- **内容归属**：内容支持指定负责人、转让所有权，多人可同时协作编辑同一篇内容

### 📝 内容管理
- **多格式上传**：支持 `.docx` / `.md` 文件上传，自动提取图片、转换格式
- **富文本编辑**：基于 md-editor-v3 的在线 Markdown 编辑器，实时预览
- **素材库**：统一管理图片/文档素材，编辑器内一键插入
- **设计任务**：内容关联设计需求，指定设计师，追踪设计进度
- **内容工作流**：`draft → reviewing → approved → published` 状态流转
- **日历排期**：FullCalendar 可视化内容排期，支持拖拽调整发布时间

### 🚀 多渠道发布

| 渠道 | 能力 |
|------|------|
| **微信公众号** | 调用 API 创建草稿，自动上传图片，封面图管理 |
| **Hugo** | 生成带 front matter 的 `.md` 文件，直接写入博客仓库 |
| **CSDN** | 一键复制适配格式，支持 Cookie 认证 |
| **知乎** | 一键复制适配格式 |

### 🎪 活动管理
- **活动全生命周期**：活动创建、议程管理、人员分工、签到名单、反馈收集
- **SOP 模板**：可复用的活动 Checklist 模板，支持强制项、负责角色、截止偏移天数
- **Issue 关联**：活动反馈自动关联 GitHub Issue，闭环追踪

### 👥 人脉与 Campaign
- **人脉档案**：统一管理贡献者信息（GitHub/Gitee handle、公司、标签）
- **社区角色**：记录每个人在各社区的角色与任期
- **Campaign**：创建触达活动，管理目标联系人和执行状态，追踪接触记录

### 🌍 生态洞察
- **生态项目管理**：追踪社区生态项目，支持全字段编辑和贡献者管理
- **数据快照**：定期采集项目 Star/Fork/Issue 等指标，生成趋势对比
- **自动同步**：可配置定时同步间隔，与 GitHub API 集成

### 🏛️ 社区治理
- **委员会管理**：创建委员会、管理成员，支持多届 / 多类型委员会，关联人脉档案
- **会议管理**：安排会议、追踪进度（计划中 / 进行中 / 已完成），支持导出 ICS 日历
- **个人工作台**：跨社区汇总「我负责的」内容与会议，工作状态统计

### 📊 数据 & 安全
- **微信数据统计**：文章阅读数、点赞数等数据录入与趋势分析
- **洞察仪表板**：贡献者影响力分析、企业分布、趋势图表
- **发布记录追踪**：完整的发布历史，渠道维度统计
- **审计日志**：关键操作全量记录，支持追溯
- **安全认证**：JWT Token 认证，渠道凭证 Fernet 加密存储，密码安全哈希
- **邮件通知**：SMTP 密码重置邮件，会议提醒通知

---

## � 快速开始（Docker 一键部署）

> 适合运营人员、管理员快速体验。开发者本地搭建见[开发者指南](#本地开发环境搭建)。

**前置条件**：Docker 20.10+ & Docker Compose v2+

```bash
# 1. 克隆项目
git clone https://github.com/opensourceways/openGecko.git
cd openGecko

# 2. 初始化配置文件
cp backend/.env.example backend/.env

# 3. 构建并启动（首次或代码更新后必须加 --build）
docker compose up -d --build
```

启动后访问：
- 🖥️ **平台界面**：http://localhost
- 📖 **API 文档**：http://localhost:8000/docs

### 首次使用流程

1. 用默认账号 `admin` / `admin123` 登录
2. 系统自动引导创建**正式管理员账号**（用户名、密码、邮箱）
3. 正式账号创建后，`admin` 默认账号**自动删除**（不可跳过）
4. 进入「社区管理」创建第一个社区，设置社区名称和 Slug
5. 进入「设置」→「渠道配置」填写发布渠道凭证（微信 AppID 等）
6. 邀请成员加入：「社区设置」→「成员管理」→ 填写成员邮箱或用户名

### 渠道凭证获取

| 渠道 | 所需凭证 | 获取方式 |
|------|---------|---------|
| 微信公众号 | AppID + AppSecret | 微信公众平台 → 开发 → 基本配置 |
| Hugo | 博客仓库绝对路径 | 运行平台的服务器上 Hugo 仓库路径 |
| CSDN | Cookie | 浏览器 DevTools → Application → Cookies |
| 知乎 | Cookie | 浏览器 DevTools → Application → Cookies |

> 所有渠道凭证均 Fernet 加密存储，API 返回时自动脱敏末 4 位，不以明文传输。

---

## 📖 用户操作手册

以下为各功能模块的详细操作流程，面向**社区运营人员**、**内容创作者**、**活动负责人**等最终用户。

---

### 内容管理

**入口**：侧边栏 → 内容管理

#### 创建内容

1. 点击右上角「新建内容」
2. 选择创建方式：
   - **在线编辑**：直接在 Markdown 编辑器中编写
   - **上传 Word**：上传 `.docx` 文件，系统自动提取图片并转换为 Markdown
   - **上传 Markdown**：上传 `.md` 文件直接导入
3. 填写标题、标签、封面图、计划发布时间
4. 点击「保存草稿」

#### 协作编辑

- 进入内容详情 → 「协作者」标签页 → 搜索并添加协作者
- 协作者与内容 owner 均可编辑
- 内容 owner 可通过「转让所有权」将内容转给其他成员

#### 内容状态流转

```
草稿 (draft)  →  审核中 (reviewing)  →  已批准 (approved)  →  已发布 (published)
```

- 工作状态（独立于内容状态，用于追踪执行进度）：`planning / in_progress / completed`
- **权限**：`reviewing → approved` 需要社区 admin 或 superuser 操作

#### 日历排期

- 入口：「内容管理」→「日历视图」
- 已设置「计划发布时间」的内容会出现在日历中
- 支持拖拽修改排期日期
- 颜色区分内容状态

#### 素材库

- 入口：侧边栏 → 素材库
- 上传图片/文档素材，支持按类型过滤
- 在内容编辑器中点击「插入素材」可一键插入图片链接

#### 设计任务

- 内容详情 → 「设计任务」标签页 → 新建设计需求
- 填写描述、截止日期、指定设计师
- 设计师收到通知后可更新状态至「完成」

---

### 多渠道发布

**入口**：内容详情页顶部 → 「发布」按钮，或侧边栏 → 发布

#### 发布流程

1. 打开一篇状态为 `approved` 的内容
2. 点击「发布」→ 选择目标渠道（可多选）
3. 根据渠道调整参数（如微信的封面图、摘要）
4. 点击「提交发布」
5. 查看发布结果：成功 ✅ / 失败 ❌（失败时显示错误原因）

#### 各渠道说明

| 渠道 | 实际效果 | 注意事项 |
|------|---------|---------|
| **微信公众号** | 自动创建草稿，图片上传至微信 CDN | 需在微信后台手动点「发布」完成正式推送 |
| **Hugo** | 在仓库指定目录生成 `.md` 文件 | 需手动 `git commit & push` 到博客仓库 |
| **CSDN** | 格式化内容，一键复制到剪贴板 | 需在 CSDN 编辑器粘贴后手动发布 |
| **知乎** | 格式化内容，一键复制到剪贴板 | 需在知乎编辑器粘贴后手动发布 |

#### 发布记录

- 入口：侧边栏 → 发布记录
- 查看所有渠道的完整发布历史
- 支持按渠道类型、时间范围筛选

---

### 活动管理

**入口**：侧边栏 → 活动

#### 创建 SOP 模板（可复用 Checklist）

1. 「活动」→「SOP 模板」→「新建模板」
2. 填写模板名称、描述
3. 添加模板项：
   - **标题**：任务名称
   - **是否强制**（`is_mandatory`）：必须完成才能进入下一阶段
   - **负责角色**：如「主持人」「志愿者」
   - **截止偏移天数**：活动日期前 N 天完成
   - **预估工时**（小时）

#### 创建活动

1. 「活动」→「新建活动」
2. 填写活动信息（名称、日期、地点、类型）
3. 选择 SOP 模板（可选）：系统自动生成任务清单
4. 添加议程：时间段 + 议题 + 负责人
5. 分配人员：主持人 / 嘉宾 / 志愿者
6. 保存并发布

#### 执行追踪

- 「活动详情」→「任务清单」：勾选已完成项
- 「活动详情」→「签到名单」：管理线下/线上签到
- 「活动详情」→「反馈」：收集反馈，可关联 GitHub Issue 追踪闭环

---

### 人脉与 Campaign

**入口**：侧边栏 → 人脉 / Campaign（需平台开启「洞察与人脉」模块）

#### 人脉档案

1. 「人脉」→「新建档案」
2. 填写基本信息：姓名、GitHub/Gitee Handle、公司、邮箱、技术标签
3. 「社区角色」标签页 → 添加在各社区的角色与任期（如「openEuler 技术委员会委员，2024.01—至今」）
4. 人脉档案可关联：委员会成员 / 活动人员 / 生态贡献者 / Campaign 联系人

#### Campaign 触达活动

1. 「Campaign」→「新建 Campaign」，填写名称和目标描述
2. 「联系人」标签页 → 从人脉档案中添加目标联系人
3. 「接触记录」→「记录接触」：填写接触方式（邮件/电话/见面）、时间、备注
4. 查看 Campaign 整体进度

---

### 生态洞察

**入口**：侧边栏 → 生态洞察

#### 添加生态项目

1. 「生态洞察」→「新建项目」
2. 填写项目信息：名称、GitHub/Gitee 仓库 URL、描述、分类、健康度评分
3. 配置自动采集：
   - **采集间隔**：设置每隔多少小时同步一次（留空表示使用全局默认值 24h）
4. 点击「立即同步」手动触发第一次采集

#### 查看数据快照

- 「项目详情」→「数据快照」：查看 Star / Fork / Issue / PR 历史趋势
- 「项目详情」→「贡献者」：查看贡献者列表、企业分布

#### Insights 仪表板

- 入口：侧边栏 → 生态洞察 → Insights
- 查看跨项目汇总：贡献者影响力排名、企业分布饼图、活跃度趋势

---

### 社区治理

**入口**：侧边栏 → 治理

#### 委员会管理

1. 「治理」→「委员会」→「新建委员会」
2. 填写名称、类型（技术委员会 / 理事会等）、描述
3. 「成员管理」→「添加成员」：从人脉档案中选择，填写角色和任期

#### 会议管理

1. 「治理」→「会议」→「安排会议」
2. 关联委员会，填写标题、时间、地点类型（线上 / 线下 / 混合）
3. 添加议题和参会人员
4. 点击「导出 ICS」→ 将日历事件导入 Google Calendar / Outlook

#### 会议日历

- 入口：「会议」→「日历视图」
- 可视化查看所有委员会的会议安排
- 点击会议卡片进入详情，更新状态（计划中 / 进行中 / 已完成）

---

### 个人工作台

**入口**：侧边栏 → 仪表板 / 我的工作

#### 个人仪表板

- 显示「分配给我的内容」数量、「即将到来的会议」、「待完成任务」
- 快速跳转到对应内容或会议详情

#### My Work（我的工作）

- 汇总**跨社区**所有分配给我的内容（含协作内容）
- 筛选条件：社区 / 状态 / 工作状态 / 时间范围
- 适合需要同时参与多个社区的成员

#### 微信数据统计

- 入口：侧边栏 → 微信统计
- 手动录入每篇文章的阅读数、点赞数、转发数
- 查看趋势折线图，对比不同文章的传播效果

---

### 平台管理（Admin）

> 仅 **superuser**（平台超级管理员）或 **community admin**（社区管理员）可访问相关功能。

#### 用户管理（仅 superuser）

- 入口：侧边栏 → 用户管理
- 查看所有注册用户，可启用/禁用账号，修改角色

#### 审计日志

- 入口：侧边栏 → 审计日志（admin+）
- 查看所有关键操作记录（内容创建/删除、发布、权限变更等）
- 支持按用户、操作类型、时间范围筛选

#### 工作量总览（仅 superuser）

- 入口：侧边栏 → 工作量总览
- 跨社区查看所有成员的内容分配情况，评估工作负载

---

### 本地开发环境搭建

```bash
# 1. 克隆项目
git clone https://github.com/opensourceways/openGecko.git
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

### 完整清理重部署（Docker 环境）

升级遇到问题或需要全量重置时使用：

```bash
docker compose down
docker rmi opengecko-backend opengecko-frontend 2>/dev/null || true
rm -f data/opengecko.db   # ⚠️ 数据不可恢复，SQLite 模式才需要此步骤
docker compose up -d --build
```

### 环境变量

复制并编辑 `backend/.env`（完整模板见 `backend/.env.example`）：

```env
# 数据库 — 开发用 SQLite，生产换 PostgreSQL
DATABASE_URL=sqlite:///./data/opengecko.db

# ⚠️ 生产环境必须改为强随机字符串（openssl rand -hex 32）
JWT_SECRET_KEY=change-me-in-production-please-use-a-strong-secret-key

# 默认管理员（仅首次启动时创建，创建正式账号后自动删除）
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin123
DEFAULT_ADMIN_EMAIL=admin@example.com

# CORS（逗号分隔字符串，非 JSON 数组；生产必须填写实际域名）
# CORS_ORIGINS=https://your-domain.com

# （可选）SMTP 邮件 — 用于密码重置和会议通知
# SMTP_HOST=smtp.example.com
# SMTP_PORT=587
# SMTP_USER=your-email@example.com
# SMTP_PASSWORD=your-email-password
# SMTP_FROM_EMAIL=noreply@example.com
# FRONTEND_URL=https://your-domain.com

# （可选）功能模块开关 — 设为 false 则禁用「洞察与人脉」菜单及 API
# ENABLE_INSIGHTS_MODULE=true

# （可选）生态洞察自动采集
# GITHUB_TOKEN=ghp_xxxx
# COLLECTOR_SYNC_INTERVAL_HOURS=24
```

完整配置说明见 [docs/CONFIGURATION.md](docs/CONFIGURATION.md)。

### 项目结构

```
openGecko/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI 路由（22 个，薄层，不含业务逻辑）
│   │   ├── models/       # SQLAlchemy ORM 模型（17 个模块，43 张表）
│   │   ├── schemas/      # Pydantic 请求/响应 Schema
│   │   ├── services/     # 业务逻辑、外部集成（微信、Hugo、ICS、邮件等）
│   │   ├── insights/     # 生态洞察分析器
│   │   ├── core/         # 安全（JWT/bcrypt/Fernet）、依赖注入、日志
│   │   ├── config.py     # Pydantic Settings（读取 .env）
│   │   └── database.py   # 数据库连接、Session、初始化
│   ├── alembic/          # 数据库迁移（001_initial_schema.py）
│   ├── tests/            # pytest 测试套件（768 个测试，覆盖率 ≥ 80%）
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/          # Axios 请求模块（自动附加 JWT + X-Community-Id）
│       ├── stores/       # Pinia 状态（auth、community、user、features）
│       ├── views/        # 页面组件（40 个）
│       ├── components/   # 共享组件（日历、Campaign 等）
│       └── router/       # Vue Router（含路由守卫）
├── docs/                 # 设计文档、需求文档、架构文档
├── docker-compose.yml
└── Makefile
```

### 数据库迁移

```bash
cd backend

# 修改 app/models/ 后，生成迁移文件（命名规范：NNN_description）
alembic revision --autogenerate -m "description"

# 检查生成的迁移文件（路径：alembic/versions/）后应用
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

# Lint（提交前必须通过）
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
feat: 新增活动签到名单导入功能
fix: 修复跨社区数据隔离漏洞
docs: 更新渠道配置说明
```

> `git push` 前请先确认是否与后续改动一并推送。

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
- [ ] 配置 SMTP 邮件（密码重置和通知功能需要）
- [ ] Nginx 配置 HTTPS（Let's Encrypt）
- [ ] 定期备份 `uploads/` 目录和数据库

### 数据持久化

Docker Compose 已配置以下挂载：

```yaml
volumes:
  - ./uploads:/app/uploads   # 上传文件（图片、文档、素材）
  - ./data:/app/data          # 数据库文件（SQLite 模式）
```

PostgreSQL 模式下请自行配置数据卷和备份策略。

---

## 🏗️ 技术架构

### 技术栈

| 层级 | 技术 | 版本 | 说明 |
|------|------|------|------|
| **前端框架** | Vue 3 + Vite | 3.5 / 6.x | Composition API，`<script setup lang="ts">` |
| **前端状态** | Pinia | 2.x | 按领域拆分 Store（auth / community / user / features）|
| **UI 组件库** | Element Plus | 2.x | 企业级组件，配合 LFX 浅色主题 |
| **HTTP 客户端** | Axios | 1.x | 拦截器自动附加 JWT Token 和 X-Community-Id |
| **后端框架** | FastAPI | 0.115+ | 异步，自动生成 OpenAPI 文档 |
| **ORM** | SQLAlchemy 2.0 | 2.x | 声明式模型，Alembic 迁移（单一初始 schema） |
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
- `assignees`：多对多，内容负责人（用于工作台汇总）

**渠道凭证安全**
凭证写入数据库之前用 Fernet（密钥由 `JWT_SECRET_KEY` 派生）加密，读取时解密使用，API 返回时对敏感字段脱敏（仅显示末 4 位）。

**人脉中台设计**
`PersonProfile` 作为统一的人脉数据库，委员会成员（`CommitteeMember`）、活动人员（`EventPersonnel`）、Campaign 联系人（`CampaignContact`）、生态贡献者（`EcosystemContributor`）均可关联同一个 PersonProfile，避免人员数据孤岛。

### API 文档

开发模式下访问 http://localhost:8000/docs 查看完整 Swagger UI，或访问 http://localhost:8000/redoc 查看 ReDoc 文档。

---

## 🗺️ 开发路线图

### 已交付功能 ✅

- ✅ JWT 认证 + 首次启动初始化流程、三级 RBAC、多租户数据隔离
- ✅ 内容全生命周期（上传、编辑、工作流、日历排期、多人协作）
- ✅ 微信公众号 / Hugo / CSDN / 知乎多渠道发布
- ✅ 活动管理（SOP 模板、任务分工、签到、反馈与 Issue 关联）
- ✅ 人脉档案、社区角色、Campaign 触达活动
- ✅ 生态项目管理、数据快照、洞察仪表板
- ✅ 素材库、设计任务、消息通知
- ✅ 委员会管理、会议管理（ICS 导出）、个人工作台
- ✅ 微信数据统计、审计日志、操作追踪

### 规划中 📋

- [ ] 内容模板库与批量操作
- [ ] Webhook / 外部集成
- [ ] Kanban 看板视图
- [ ] 监控告警接入（Prometheus + Grafana）
- [ ] HTTPS / Let's Encrypt 配置向导

详见 [docs/plannings/01-产品路线图.md](docs/plannings/01-产品路线图.md)

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
| [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) | 目录结构详解 |
| [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) | 贡献流程 |
| [docs/design/01-系统架构设计.md](docs/design/01-系统架构设计.md) | 系统架构设计（技术栈、API 端点、前端结构、安全机制）|
| [docs/design/02-数据库详细设计.md](docs/design/02-数据库详细设计.md) | 数据库详细设计（43 张表结构、ER 图、索引策略）|
| [docs/requirements/01-需求分析文档.md](docs/requirements/01-需求分析文档.md) | 产品需求分析文档（PRD，与代码实现同步）|
| [docs/plannings/01-产品路线图.md](docs/plannings/01-产品路线图.md) | 已交付里程碑 + 未来规划 |

---

## 📄 License

[MIT License](LICENSE) © openGecko Contributors

---

<div align="center">

**openGecko** — Manage All, Publish Everywhere 🦎

Made with ❤️ for Open Source Communities

</div>
