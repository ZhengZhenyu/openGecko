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
| [系统架构设计](design/01-系统架构设计.md) | 技术栈、多租户架构、API 路由清单、安全机制、部署方案 |
| [数据库详细设计](design/02-数据库详细设计.md) | 全部 17 张表的结构定义、关系、索引策略 |
| [UML 类图与时序图](uml/01-类图与时序图.md) | Mermaid 类图与核心业务流程时序图 |

### 开发指南

| 文档 | 说明 |
|------|------|
| [开发环境搭建](DEVELOPMENT.md) | 本地开发环境配置步骤 |
| [配置说明](CONFIGURATION.md) | 环境变量与 `.env` 配置项说明 |
| [Pre-commit 钩子配置](PRE_COMMIT_SETUP.md) | 代码质量检查工具安装与使用 |
| [贡献指南](CONTRIBUTING.md) | 如何参与项目贡献 |
| [项目目录结构](PROJECT_STRUCTURE.md) | 代码目录组织说明 |

### 功能指南

| 文档 | 说明 |
|------|------|
| [微信公众号发布验证](WECHAT_PUBLISH_VERIFICATION.md) | 使用真实凭证验证微信发布功能的操作步骤 |

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

**更新日期**: 2026-02-21
