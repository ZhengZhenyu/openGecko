# 项目结构说明

本文档描述 OmniContent 项目的目录结构和组织方式。

## 根目录结构

```
omnicontent/
├── .github/          # GitHub 配置（Actions、PR模板等）
├── backend/          # Python FastAPI 后端
├── frontend/         # Vue 3 前端
├── docs/             # 项目文档
├── scripts/          # 辅助脚本
├── Makefile          # 便捷命令
├── docker-compose.yml # Docker 编排
├── LICENSE           # MIT 许可证
└── README.md         # 项目说明
```

## Backend 后端结构

```
backend/
├── alembic/              # 数据库迁移
│   └── versions/         # 迁移版本文件
├── app/                  # 应用代码
│   ├── api/              # API 路由层
│   │   ├── auth.py       # 认证接口
│   │   ├── communities.py # 社区管理
│   │   ├── contents.py   # 内容管理
│   │   ├── publish.py    # 发布管理
│   │   └── analytics.py  # 数据分析
│   ├── core/             # 核心功能
│   │   ├── dependencies.py # 依赖注入（认证、社区）
│   │   └── security.py   # JWT、密码加密
│   ├── models/           # SQLAlchemy 数据模型
│   │   ├── user.py       # 用户模型
│   │   ├── community.py  # 社区模型
│   │   ├── content.py    # 内容模型
│   │   ├── channel.py    # 渠道配置
│   │   ├── publish_record.py # 发布记录
│   │   └── audit.py      # 审计日志
│   ├── schemas/          # Pydantic 数据验证
│   │   ├── auth.py       # 认证schemas
│   │   ├── user.py       # 用户schemas
│   │   ├── community.py  # 社区schemas
│   │   ├── content.py    # 内容schemas
│   │   └── publish.py    # 发布schemas
│   ├── services/         # 业务逻辑层
│   │   ├── wechat.py     # 微信公众号服务
│   │   ├── hugo.py       # Hugo 博客服务
│   │   ├── csdn.py       # CSDN 服务
│   │   ├── zhihu.py      # 知乎服务
│   │   └── converter.py  # 格式转换
│   ├── config.py         # 配置管理
│   ├── database.py       # 数据库连接
│   └── main.py           # FastAPI 应用入口
├── tests/                # 测试文件
│   ├── __init__.py       # 测试包初始化
│   ├── conftest.py       # Pytest 配置和共享 fixtures
│   ├── test_auth_api.py  # 认证 API 测试
│   ├── test_communities_api.py  # 社区管理 API 测试
│   ├── test_contents_api.py     # 内容管理 API 测试
│   ├── test_publish_api.py      # 发布管理 API 测试
│   ├── test_analytics_api.py    # 数据分析 API 测试
│   └── test_auth_integration.py # 认证和多租户集成测试
├── uploads/              # 文件上传目录
│   └── .gitkeep
├── .env.example          # 环境变量示例
├── pytest.ini            # Pytest 配置文件
├── requirements.txt      # Python 依赖
├── requirements-dev.txt  # 开发和测试依赖
├── TESTING.md            # 测试指南
└── pyproject.toml        # 项目配置（ruff、black等）
```

### Backend 关键目录说明

#### `api/` - API 路由层
- 定义 RESTful API 端点
- 处理请求参数验证
- 调用 service 层执行业务逻辑
- 返回响应数据

#### `core/` - 核心功能
- `dependencies.py`: FastAPI 依赖注入，实现认证和社区隔离
- `security.py`: JWT token 生成验证、密码哈希

#### `models/` - 数据模型
- SQLAlchemy ORM 模型
- 定义数据库表结构和关系
- 多租户隔离（community_id）

#### `schemas/` - 数据验证
- Pydantic 模型，用于请求/响应验证
- 定义 API 输入输出格式

#### `services/` - 业务逻辑
- 各渠道发布逻辑
- 内容格式转换
- 第三方 API 集成

#### `tests/` - 测试目录
- `conftest.py`: Pytest 配置和共享 fixtures（数据库、认证、测试数据）
- `test_*_api.py`: API 端点集成测试，覆盖所有 REST API
- `test_auth_integration.py`: 认证和多租户功能的集成测试
- 使用 SQLite 内存数据库进行测试，保证测试独立性
- 详细信息请参考 [`backend/TESTING.md`](../backend/TESTING.md)

## Frontend 前端结构

```
frontend/
├── public/               # 静态资源
├── src/
│   ├── api/              # API 客户端
│   │   ├── index.ts      # Axios 实例（拦截器）
│   │   ├── auth.ts       # 认证 API
│   │   ├── community.ts  # 社区 API
│   │   ├── content.ts    # 内容 API
│   │   └── publish.ts    # 发布 API
│   ├── assets/           # 资源文件（CSS、图片）
│   ├── components/       # 可复用组件
│   │   └── CommunitySwitcher.vue # 社区切换器
│   ├── composables/      # Vue Composition API 可复用逻辑
│   │   └── (待添加)
│   ├── router/           # 路由配置
│   │   └── index.ts      # 路由定义 + 认证守卫
│   ├── stores/           # Pinia 状态管理
│   │   ├── auth.ts       # 认证状态
│   │   └── community.ts  # 社区状态
│   ├── types/            # TypeScript 类型定义
│   │   └── (待添加)
│   ├── utils/            # 工具函数
│   │   └── (待添加)
│   ├── views/            # 页面组件
│   │   ├── Login.vue     # 登录页
│   │   ├── Dashboard.vue # 仪表板
│   │   ├── ContentList.vue # 内容列表
│   │   ├── ContentEdit.vue # 内容编辑
│   │   ├── PublishView.vue # 发布管理
│   │   └── Settings.vue  # 设置页
│   ├── App.vue           # 根组件
│   ├── main.ts           # 应用入口
│   └── env.d.ts          # 环境变量类型
├── package.json          # NPM 依赖
├── tsconfig.json         # TypeScript 配置
├── vite.config.ts        # Vite 构建配置
└── index.html            # HTML 模板
```

### Frontend 关键目录说明

#### `api/` - API 客户端
- `index.ts`: 统一的 axios 实例，配置拦截器（JWT、社区ID）
- 其他文件: 各模块的 API 调用函数

#### `components/` - 可复用组件
- 跨页面使用的 UI 组件
- 业务逻辑组件（如社区切换器）

#### `composables/` - 可复用逻辑
- Vue 3 Composition API 的可复用函数
- 示例: useAuth、usePermission、useDebounce

#### `stores/` - 状态管理
- Pinia store 模块
- 全局状态（用户、社区等）

#### `types/` - 类型定义
- 共享的 TypeScript 接口和类型
- API 响应类型、业务模型类型

#### `utils/` - 工具函数
- 通用工具函数
- 格式化、验证、日期处理等

#### `views/` - 页面组件
- 对应路由的页面级组件
- 组合使用 components、composables、stores

## Docs 文档结构

```
docs/
├── design/               # 设计文档
│   ├── 01-系统架构设计.md
│   └── 02-数据库详细设计.md
├── plannings/            # 实施计划
│   └── 01-实施计划.md
├── requirements/         # 需求文档
│   └── 01-需求分析文档.md
├── uml/                  # UML 图
│   └── 01-类图与时序图.md
├── CONFIGURATION.md      # 配置指南
├── CONTRIBUTING.md       # 贡献指南
├── DEVELOPMENT.md        # 开发指南
├── PROJECT_STRUCTURE.md  # 本文档
└── README.md             # 文档索引
```

## Scripts 脚本目录

```
scripts/
├── init_old_schema.py    # 初始化旧数据库模式（用于测试）
└── (其他辅助脚本)
```

## .github GitHub 配置

```
.github/
├── workflows/            # GitHub Actions
│   ├── backend-ci.yml    # 后端 CI
│   ├── frontend-ci.yml   # 前端 CI
│   ├── pr-checks.yml     # PR 检查
│   └── database-migration-check.yml # 迁移检查
├── PULL_REQUEST_TEMPLATE.md # PR 模板
├── CODEOWNERS            # 代码所有者
└── WORKFLOWS.md          # Workflows 说明
```

## 开发约定

### 命名规范

#### Python (Backend)
- **文件名**: snake_case (例如: `user_service.py`)
- **类名**: PascalCase (例如: `UserService`)
- **函数/变量**: snake_case (例如: `get_user`)

#### TypeScript/Vue (Frontend)
- **文件名**:
  - Vue 组件: PascalCase (例如: `CommunitySwitcher.vue`)
  - 其他文件: kebab-case 或 camelCase (例如: `auth.ts`)
- **组件名**: PascalCase (例如: `CommunitySwitcher`)
- **函数/变量**: camelCase (例如: `getUserInfo`)

### 目录使用建议

#### 何时创建新文件

1. **Backend**:
   - 新模块 → `api/`, `models/`, `schemas/`, `services/`
   - 测试 → `tests/`
   - 工具脚本 → `scripts/`

2. **Frontend**:
   - 可复用组件 → `components/`
   - 页面 → `views/`
   - 全局状态 → `stores/`
   - 可复用逻辑 → `composables/`
   - 类型定义 → `types/`
   - 工具函数 → `utils/`

### 多租户数据隔离

所有与用户数据相关的模型都包含 `community_id` 字段，通过 `get_current_community` 依赖注入实现社区级隔离。

### 认证流程

1. 用户登录 → 获取 JWT token
2. 前端存储 token 到 localStorage
3. 请求拦截器自动添加 `Authorization: Bearer <token>` 和 `X-Community-Id` 头
4. 后端依赖注入验证 token 和社区权限

## 常见任务

### 添加新 API 端点

1. 定义 Schema: `backend/app/schemas/`
2. 定义路由: `backend/app/api/`
3. (可选) 添加 Service: `backend/app/services/`
4. 添加前端 API: `frontend/src/api/`

### 添加新页面

1. 创建 Vue 组件: `frontend/src/views/`
2. 添加路由: `frontend/src/router/index.ts`
3. (可选) 添加 Store: `frontend/src/stores/`
4. (可选) 添加 API: `frontend/src/api/`

### 数据库迁移

```bash
# 创建迁移
cd backend
alembic revision --autogenerate -m "description"

# 应用迁移
alembic upgrade head
```

## 相关文档

- [开发指南](DEVELOPMENT.md) - 开发环境、工作流程
- [配置指南](CONFIGURATION.md) - 环境变量、渠道配置
- [贡献指南](CONTRIBUTING.md) - 如何贡献代码
