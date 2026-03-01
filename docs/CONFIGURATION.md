# 配置指南

本文档详细说明 openGecko 的配置选项。

## 环境变量配置

### 基础配置

复制示例配置文件：
```bash
cp backend/.env.example backend/.env
```

编辑 `backend/.env`：

```env
# 应用配置
APP_NAME=openGecko
DEBUG=False

# 数据库配置
DATABASE_URL=sqlite:///./opengecko.db

# JWT 认证配置
JWT_SECRET_KEY=your-super-secret-key-change-me-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 days

# CORS 配置
CORS_ORIGINS=["http://localhost:3000"]
```

### 数据库配置

#### 开发环境 (SQLite)

```env
DATABASE_URL=sqlite:///./opengecko.db
```

#### 生产环境 (PostgreSQL)

```env
DATABASE_URL=postgresql://user:password@localhost:5432/opengecko
```

### 微信公众号配置

在 [微信公众平台](https://mp.weixin.qq.com/) 获取 AppID 和 AppSecret：

```env
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret
```

配置后可通过 API 创建草稿并获取预览链接。

### Hugo 博客配置

```env
HUGO_REPO_PATH=/path/to/your/hugo/repo
HUGO_CONTENT_DIR=content/posts
HUGO_AUTHOR_NAME=Your Name
```

发布时自动：
- 生成 front matter (标题、日期、分类、标签)
- 提取并保存图片到 `static/images/`
- 支持 `git commit` 和 `git push` 自动化

### CSDN/知乎配置

CSDN 和知乎暂不支持 API 自动发布，系统提供格式化后的内容，支持一键复制：

```env
# 可选：配置默认作者信息
CSDN_USERNAME=your_username
ZHIHU_USERNAME=your_username
```

## 社区配置

### 创建社区

通过管理界面创建社区，配置：

- **社区名称**: 显示名称
- **Slug**: URL 友好的唯一标识符
- **描述**: 社区简介
- **Logo URL**: 社区标志图片链接
- **设置**: JSON 格式的自定义配置

### 渠道配置

为每个社区独立配置发布渠道：

```json
{
  "wechat": {
    "enabled": true,
    "app_id": "community_specific_app_id",
    "app_secret": "community_specific_secret"
  },
  "hugo": {
    "enabled": true,
    "repo_path": "/path/to/community/blog",
    "content_dir": "content/posts"
  }
}
```

## 用户管理

### 创建管理员

默认管理员账号：
- 用户名: `admin`
- 密码: `admin123`

**⚠️ 生产环境必须立即修改默认密码！**

### 添加新用户

通过管理界面或 API 创建用户：

```bash
POST /api/auth/register
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "secure_password",
  "full_name": "User Full Name"
}
```

### 用户权限

- **超级管理员**: 管理所有社区和用户
- **普通用户**: 只能访问授权的社区

## 安全配置

### JWT 密钥

**生产环境必须修改 JWT 密钥**：

```bash
# 生成随机密钥
openssl rand -hex 32
```

将生成的值设置为 `JWT_SECRET_KEY`。

### CORS 配置

生产环境配置实际的前端域名：

```env
CORS_ORIGINS=["https://your-domain.com"]
```

## 日志配置

配置日志级别和输出：

```env
LOG_LEVEL=INFO
LOG_FILE=logs/opengecko.log
```

日志级别: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

## 文件上传配置

```env
# 上传文件大小限制 (MB)
MAX_UPLOAD_SIZE=10

# 上传文件保存路径
UPLOAD_DIR=uploads

# 允许的文件类型
ALLOWED_EXTENSIONS=["jpg", "jpeg", "png", "gif", "docx", "md"]
```

## Docker 配置

编辑 `docker-compose.yml` 自定义部署：

```yaml
services:
  backend:
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/opengecko
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    ports:
      - "8000:8000"
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs

  db:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=opengecko
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

## 可选功能模块

### 洞察与人脉模块

该模块包含「人脉管理」和「生态洞察」功能，相对独立，可按需启用或禁用。

```env
# 禁用「洞察与人脉」模块（默认 true = 启用）
ENABLE_INSIGHTS_MODULE=false
```

关闭后效果：
- 后端不注册 `/api/people` 和 `/api/ecosystem` 路由（返回 404）
- 前端侧边栏隐藏「洞察与人脉」菜单
- 直接访问 `/people`、`/ecosystem` 等 URL 自动跳转至首页
- 数据库表保留，随时可重新开启

### 生态洞察自动采集服务（可选容器）

需单独启动 `collector` profile：

```bash
# 启动完整版（含自动采集）
docker compose --profile collector up -d
```

相关环境变量：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `GITHUB_TOKEN` | 空 | GitHub Personal Access Token；不填则受 60 req/h 匿名限速 |
| `GITEE_TOKEN` | 空 | Gitee 私人令牌（可选） |
| `COLLECTOR_SYNC_INTERVAL_HOURS` | `24` | 全局默认采集间隔（小时），各项目可单独覆盖 |
| `COLLECTOR_MAX_PROJECTS_PER_RUN` | `20` | 每次运行最多同步项目数，防止触发 API 速率限制 |

各项目的采集间隔可在「生态洞察 → 项目信息」页面单独设置，`null` 表示使用全局默认值。

## 故障排查

### 数据库连接失败

检查 DATABASE_URL 格式和数据库服务状态：

```bash
# SQLite: 确保路径可写
ls -la backend/

# PostgreSQL: 测试连接
psql $DATABASE_URL
```

### 微信公众号 API 报错

- 检查 AppID 和 AppSecret 是否正确
- 确认 IP 白名单配置
- 查看微信公众平台接口调用日志

### Hugo 发布失败

- 检查 HUGO_REPO_PATH 是否正确
- 确认有 Git 仓库写入权限
- 验证 HUGO_CONTENT_DIR 目录存在

## 性能优化

### 数据库连接池

```env
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
```

### 缓存配置

```env
CACHE_ENABLED=True
CACHE_TTL=3600
```

## 备份配置

### 自动备份

配置定时备份任务：

```bash
# 添加到 crontab
0 2 * * * /path/to/backup-script.sh
```

示例备份脚本：

```bash
#!/bin/bash
BACKUP_DIR=/path/to/backups
DATE=$(date +%Y%m%d_%H%M%S)

# 备份数据库
cp backend/opengecko.db $BACKUP_DIR/opengecko_$DATE.db

# 备份上传文件
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz backend/uploads/

# 删除 30 天前的备份
find $BACKUP_DIR -mtime +30 -delete
```
