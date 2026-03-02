# openGecko - 项目文档

<div align="center">
<img src="../openGecko.jpg" alt="openGecko Logo" width="100" height="100" />
</div>

本目录包含 openGecko 多租户开源社区管理平台的完整文档。

---

## 文档目录

### 需求与规划

| 文档 | 说明 |
|------|------|
| [需求分析文档](requirements/01-需求分析文档.md) | 完整的产品需求规格（PRD），含功能需求、用户故事、验收标准 |
| [产品路线图](plannings/01-产品路线图.md) | 已交付里程碑（Phase 1-3）与规划中功能（Phase 4-6）|

### 系统设计

| 文档 | 说明 |
|------|------|
| [系统架构设计](design/01-系统架构设计.md) | ADR 决策表、6 层架构图、安全威胁模型、可观测性、CI/CD、性能扩展（v5.0）|
| [数据库详细设计](design/02-数据库详细设计.md) | 全部 43 张表的结构定义（17 个模型模块）、关系、索引策略 |
| [UML 类图与时序图](uml/01-类图与时序图.md) | Mermaid 类图与核心业务流程时序图 |

### 开发指南

| 文档 | 说明 |
|------|------|
| [开发环境搭建](DEVELOPMENT.md) | 本地开发环境配置步骤 |
| [配置说明](CONFIGURATION.md) | 环境变量与 `.env` 配置项说明 |
| [Pre-commit 钩子配置](PRE_COMMIT_SETUP.md) | 代码质量检查工具安装与使用 |
| [贡献指南](CONTRIBUTING.md) | 如何参与项目贡献 |
| [项目目录结构](PROJECT_STRUCTURE.md) | 代码目录组织说明 |

### API 文档

| 文档 | 说明 |
|------|------|
| [API 文档索引](api/README.md) | 所有 REST API 端点总览 |
| [认证 API](api/auth-api.md) | 登录、登出、密码重置 |
| [社区 API](api/community-api.md) | 社区管理、成员管理 |
| [内容 API](api/content-api.md) | 内容 CRUD、状态流转、协作者 |
| [发布 API](api/publish-api.md) | 多渠道发布、发布记录 |
| [治理 API](api/governance-api.md) | 委员会、会议管理 |
| [分析 API](api/analytics-api.md) | 统计仪表板、发布趋势 |
| [上传 API](api/upload-api.md) | 文件与图片上传 |

---

## 项目概述

openGecko 是面向开源社区运营团队的多租户内容管理与治理平台，支持：

- **多渠道发布** — 微信公众号、Hugo、CSDN、知乎一键同步
- **内容工作流** — draft → reviewing → approved → published 状态机
- **内容日历** — FullCalendar 可视化排期与拖拽调整
- **治理模块** — 委员会管理、会议管理（状态追踪、议程纪要、ICS 导出）
- **个人工作台** — 跨社区内容与会议任务汇总
- **社区总览** — 统计仪表板、发布趋势、成员概况
- **三级 RBAC** — superuser / admin / user 权限体系
- **多租户隔离** — community_id 行级隔离 + X-Community-Id Header

**技术栈**：Python 3.11 + FastAPI + SQLAlchemy 2.0 / Vue 3 + TypeScript + Element Plus

---

**更新日期**: 2026-03-02
