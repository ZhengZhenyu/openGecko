# 项目结构说明

本文档描述 openGecko 项目的目录结构和组织方式。

## 根目录结构

```
openGecko/
├── backend/                    # Python FastAPI 后端
├── frontend/                   # Vue 3 前端
├── docs/                       # 项目文档
├── data/                       # 数据库持久化目录（SQLite 模式）
├── uploads/                    # 用户上传文件（.gitkeep 占位）
├── scripts/                    # 工具脚本
├── docker-compose.yml          # 开发环境 Docker Compose
├── docker-compose.prod.yml     # 生产环境 Docker Compose
├── docker-compose.override.yml # 本地覆盖配置
├── Makefile                    # 常用命令快捷入口
├── CLAUDE.md                   # Claude Code 项目指引
├── README.md                   # 主文档
└── LICENSE                     # MIT License
```

---

## 后端结构（backend/）

```
backend/
├── app/
│   ├── api/                    # FastAPI 路由层（22 个模块）
│   │   ├── __init__.py
│   │   ├── admin.py            # 平台管理（superuser）
│   │   ├── analytics.py        # 内容分析统计
│   │   ├── assets.py           # 素材库
│   │   ├── auth.py             # 认证（登录、注册、Token）
│   │   ├── campaigns.py        # Campaign 触达活动
│   │   ├── channels.py         # 渠道配置
│   │   ├── committees.py       # 委员会管理
│   │   ├── communities.py      # 社区管理
│   │   ├── community_dashboard.py  # 社区总览仪表板
│   │   ├── contents.py         # 内容 CRUD
│   │   ├── dashboard.py        # 个人仪表板（prefix: /api/users/me）
│   │   ├── design_tasks.py     # 设计任务
│   │   ├── ecosystem.py        # 生态项目
│   │   ├── event_templates.py  # SOP 模板
│   │   ├── events.py           # 活动管理
│   │   ├── meetings.py         # 会议管理
│   │   ├── notifications.py    # 消息通知
│   │   ├── people.py           # 人脉档案
│   │   ├── publish.py          # 多渠道发布
│   │   ├── upload.py           # 文件上传（prefix: /api/contents）
│   │   └── wechat_stats.py     # 微信数据统计
│   │
│   ├── models/                 # SQLAlchemy ORM 模型（17 个模块，43 张表）
│   │   ├── __init__.py         # 统一导出所有模型
│   │   ├── audit.py            # AuditLog
│   │   ├── campaign.py         # Campaign, CampaignContact, CampaignActivity, CampaignTask
│   │   ├── channel.py          # ChannelConfig
│   │   ├── committee.py        # Committee, CommitteeMember
│   │   ├── community.py        # Community, CommunityUser
│   │   ├── content.py          # Content, ContentCollaborator, ContentAssignee, ContentCommunity, ContentAnalytics
│   │   ├── design.py           # DesignTask
│   │   ├── ecosystem.py        # EcosystemProject, EcosystemSnapshot, EcosystemContributor
│   │   ├── event.py            # Event, EventTemplate, ChecklistTemplateItem, ChecklistItem,
│   │   │                       # EventTask, EventPersonnel, EventAttendee, FeedbackItem, IssueLink
│   │   ├── meeting.py          # Meeting, MeetingParticipant, MeetingAssignee, MeetingReminder
│   │   ├── notification.py     # Notification
│   │   ├── password_reset.py   # PasswordResetToken
│   │   ├── people.py           # PersonProfile, CommunityRole
│   │   ├── publish_record.py   # PublishRecord
│   │   ├── upload.py           # Asset, ContentAsset
│   │   ├── user.py             # User
│   │   └── wechat_stats.py     # WechatArticleStat, WechatStatsAggregate
│   │
│   ├── schemas/                # Pydantic v2 请求/响应 Schema
│   │   ├── auth.py
│   │   ├── campaign.py
│   │   ├── channel.py
│   │   ├── committee.py
│   │   ├── community.py
│   │   ├── content.py
│   │   ├── design.py
│   │   ├── ecosystem.py
│   │   ├── event.py
│   │   ├── meeting.py
│   │   ├── notification.py
│   │   ├── people.py
│   │   ├── publish.py
│   │   ├── upload.py
│   │   ├── user.py
│   │   └── wechat_stats.py
│   │
│   ├── services/               # 业务逻辑与外部集成
│   │   ├── converter.py        # DOCX/MD → HTML 格式转换
│   │   ├── csdn.py             # CSDN 格式适配
│   │   ├── email.py            # SMTP 邮件发送
│   │   ├── hugo.py             # Hugo .md 文件生成
│   │   ├── ics.py              # ICS 日历文件生成
│   │   ├── notification.py     # 会议提醒通知
│   │   ├── wechat.py           # 微信公众号 API
│   │   ├── zhihu.py            # 知乎格式适配
│   │   └── ecosystem/          # 生态洞察服务
│   │       ├── collector.py    # GitHub API 数据采集
│   │       └── sync.py         # 定时同步调度
│   │
│   ├── insights/               # 生态洞察分析器
│   │   └── analyzers/
│   │       ├── __init__.py
│   │       ├── corporate.py    # 企业分布分析
│   │       ├── influence.py    # 贡献者影响力
│   │       └── trend.py        # 趋势分析
│   │
│   ├── core/
│   │   ├── dependencies.py     # FastAPI Depends（认证、RBAC、社区隔离）
│   │   ├── logging.py          # 结构化日志
│   │   └── security.py         # JWT、bcrypt、Fernet 加密
│   │
│   ├── config.py               # Pydantic Settings（读取 .env）
│   ├── database.py             # DB 连接、Session、init_db()
│   └── main.py                 # FastAPI app，路由注册
│
├── alembic/                    # 数据库迁移
│   ├── versions/
│   │   └── 001_initial_schema.py   # 全量建表（43 张，当前唯一迁移文件）
│   ├── env.py
│   └── alembic.ini
│
├── tests/                      # pytest 测试套件（768 个测试）
│   ├── conftest.py             # 共享 fixture（测试 DB、测试用户、测试社区）
│   ├── test_auth_api.py
│   ├── test_campaigns_api.py
│   ├── test_community_api.py
│   ├── test_contents_api.py
│   ├── test_design_tasks_api.py
│   ├── test_ecosystem_api.py
│   ├── test_events_api.py
│   ├── test_meetings_api.py
│   ├── test_notifications_api.py
│   ├── test_people_api.py
│   ├── test_publish_api.py
│   ├── test_rbac_collaboration.py
│   ├── test_services.py
│   ├── test_upload_api.py
│   ├── test_wechat_service.py
│   ├── test_wechat_stats_api.py
│   └── ...
│
├── uploads/
│   ├── images/                 # 上传图片
│   └── covers/                 # 内容封面图
│
├── .env.example                # 环境变量模板
└── requirements.txt            # Python 依赖
```

---

## 前端结构（frontend/src/）

```
frontend/src/
├── api/                        # Axios 请求模块（自动附加 JWT + X-Community-Id）
│   ├── auth.ts
│   ├── campaign.ts
│   ├── channel.ts
│   ├── committee.ts
│   ├── community.ts
│   ├── content.ts
│   ├── dashboard.ts
│   ├── design.ts
│   ├── ecosystem.ts
│   ├── event.ts
│   ├── meeting.ts
│   ├── notification.ts
│   ├── people.ts
│   ├── publish.ts
│   ├── upload.ts
│   ├── user.ts
│   └── wechat_stats.ts
│
├── stores/                     # Pinia 状态管理
│   ├── auth.ts                 # token, user, isLoggedIn
│   ├── community.ts            # currentCommunity, communities
│   ├── user.ts                 # profile
│   └── features.ts             # enableInsightsModule 等功能开关
│
├── views/                      # 页面组件（40 个）
│   ├── Login.vue
│   ├── ForgotPassword.vue
│   ├── ResetPassword.vue
│   ├── InitialSetup.vue
│   ├── Dashboard.vue           # 个人仪表板
│   ├── MyWork.vue              # 个人工作台
│   ├── Profile.vue
│   ├── WorkloadOverview.vue    # 工作量总览（superuser）
│   │
│   ├── ContentList.vue
│   ├── ContentEdit.vue
│   ├── ContentCalendar.vue
│   ├── PublishView.vue
│   ├── AssetLibrary.vue
│   ├── DesignTasks.vue
│   │
│   ├── Events.vue
│   ├── EventDetail.vue
│   ├── EventTemplates.vue
│   │
│   ├── People.vue
│   ├── PeopleDetail.vue
│   ├── Campaigns.vue
│   ├── CampaignDetail.vue
│   │
│   ├── EcosystemList.vue
│   ├── EcosystemDetail.vue
│   ├── InsightsDashboard.vue
│   │
│   ├── CommitteeList.vue
│   ├── CommitteDetail.vue
│   ├── CommitteeMemberManage.vue
│   ├── MeetingDetail.vue
│   ├── MeetingCalendar.vue
│   ├── GovernanceOverview.vue
│   │
│   ├── Analytics.vue
│   ├── WechatStats.vue
│   │
│   ├── CommunityManage.vue
│   ├── CommunityOverview.vue
│   ├── CommunitySettings.vue
│   ├── CommunityWizard.vue
│   ├── CommunitySandbox.vue
│   │
│   ├── UserManage.vue          # 用户管理（superuser）
│   ├── AuditLogs.vue
│   └── Settings.vue
│
├── components/                 # 共享组件
│   ├── calendar/               # 日历相关组件
│   └── campaign/               # Campaign 相关组件
│
├── router/
│   └── index.ts                # Vue Router（路由守卫：认证 + 社区校验）
│
├── types/                      # TypeScript 类型定义
└── utils/                      # 工具函数
```

---

## 文档结构（docs/）

```
docs/
├── README.md                   # 文档索引
├── CONFIGURATION.md            # 环境变量与渠道配置指南
├── CONTRIBUTING.md             # 贡献流程（英文）
├── DEVELOPMENT.md              # 开发环境搭建与规范（中文）
├── PROJECT_STRUCTURE.md        # 本文件
├── PRE_COMMIT_SETUP.md         # pre-commit hooks 配置指南
│
├── api/                        # API 文档
│   ├── README.md               # API 文档索引
│   ├── auth-api.md
│   ├── community-api.md
│   ├── content-api.md
│   ├── analytics-api.md
│   ├── governance-api.md
│   ├── publish-api.md
│   ├── upload-api.md
│   └── schemas/
│       ├── common-schemas.md   # 通用数据模型
│       └── error-responses.md  # 错误响应格式
│
├── design/                     # 设计文档
│   ├── 01-系统架构设计.md       # 架构、API 路由、安全机制、部署（v4.0）
│   └── 02-数据库详细设计.md     # 43 张表结构、ER 图、索引策略（v4.0）
│
├── requirements/               # 需求文档
│   └── 01-需求分析文档.md       # PRD，Phase 1-4 完整需求记录（v4.0）
│
├── plannings/                  # 规划文档
│   └── 01-产品路线图.md         # 已交付里程碑 + 未来规划（v4.0）
│
└── uml/                        # UML 图
    └── 01-类图与时序图.md        # 领域模型类图、时序图（v3.0，待更新）
```

---

## 命名约定

| 类型 | 规范 | 示例 |
|------|------|------|
| Python 文件/目录 | snake_case | `content_api.py` |
| Python 类 | PascalCase | `ContentService` |
| Python 函数/变量 | snake_case | `get_current_user` |
| Python 常量 | UPPER_SNAKE_CASE | `JWT_SECRET_KEY` |
| Vue 文件 | PascalCase | `ContentEdit.vue` |
| TypeScript 接口 | PascalCase | `ContentResponse` |
| CSS 类名 | kebab-case | `.section-card` |
| API 路由路径 | kebab-case | `/api/event-templates` |
| 数据库表名 | snake_case | `content_assignees` |
| Alembic 迁移文件 | `NNN_description.py` | `001_initial_schema.py` |
| Git 分支 | `type/description` | `feat/asset-library` |
| 提交信息 | Conventional Commits + 中文 | `feat: 新增素材库功能` |
