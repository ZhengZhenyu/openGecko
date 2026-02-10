# 微信公众号发布功能验证指南

本文档指导如何使用真实的微信公众号凭证验证发布功能。

## 📋 前置准备

### 1. 微信公众号要求

- **账号类型**: 订阅号或服务号（个人订阅号也可以）
- **认证状态**: 已认证（推荐）或未认证均可
- **权限要求**: 需要开通**草稿箱**和**素材管理**功能

### 2. 获取微信公众号凭证

#### 步骤 A: 登录微信公众平台
1. 访问 [https://mp.weixin.qq.com](https://mp.weixin.qq.com)
2. 使用管理员微信扫码登录

#### 步骤 B: 获取开发者凭证
1. 在左侧菜单选择 **设置与开发** → **基本配置**
2. 在"开发者ID(AppID)"部分：
   - 复制 **AppID** (格式: `wx1234567890abcdef`)
   - 点击 **AppSecret** 右侧的 **重置** 按钮
   - 使用管理员微信扫码确认
   - 复制新的 **AppSecret** (格式: 32位随机字符串)

⚠️ **安全提示**:
- AppSecret 泄露后请立即重置
- 不要将凭证提交到 Git 仓库
- 重置后旧的 AppSecret 立即失效

#### 步骤 C: IP白名单配置（可选）
如果公众号开启了IP白名单，需要添加服务器IP：
1. 在 **基本配置** 页面找到 **IP白名单**
2. 点击 **修改**，添加你的服务器公网IP
3. 开发环境可以暂时留空或添加本地公网IP

### 3. 准备测试素材

准备以下测试内容：

- **封面图片**:
  - 格式: JPG/PNG
  - 尺寸: 建议 900x500 像素
  - 大小: < 2MB
  - 存放位置: `backend/uploads/test_cover.jpg`

- **内容图片**（如果测试图片上传功能）:
  - 格式: JPG/PNG/GIF
  - 大小: < 2MB
  - 存放位置: `backend/uploads/test_image1.jpg`

---

## 🔧 配置步骤

### 方法一: 使用 API 配置（推荐）

#### 1. 启动后端服务

```bash
cd /root/omnicontent/content-phase2/backend

# 启动 FastAPI 服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. 获取访问令牌

```bash
# 登录获取 token
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'

# 记录返回的 access_token
```

#### 3. 配置微信渠道

```bash
# 设置环境变量
export TOKEN="your_access_token_here"
export COMMUNITY_ID="1"  # 你的社区ID

# 创建微信渠道配置
curl -X POST "http://localhost:8000/api/communities/${COMMUNITY_ID}/channels" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "X-Community-Id: ${COMMUNITY_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "wechat",
    "config": {
      "app_id": "wx1234567890abcdef",
      "app_secret": "your_real_app_secret_here"
    },
    "enabled": true
  }'
```

### 方法二: 直接操作数据库（仅开发环境）

```bash
cd /root/omnicontent/content-phase2/backend

# 进入 Python Shell
python

# 执行以下代码
```

```python
from app.database import SessionLocal
from app.models.channel import ChannelConfig
from app.core.security import encrypt_value

# 创建数据库会话
db = SessionLocal()

# 加密 AppSecret
encrypted_secret = encrypt_value("your_real_app_secret_here")

# 创建或更新微信配置
config = db.query(ChannelConfig).filter(
    ChannelConfig.community_id == 1,
    ChannelConfig.channel == "wechat"
).first()

if config:
    # 更新现有配置
    config.config = {
        "app_id": "wx1234567890abcdef",
        "app_secret": encrypted_secret
    }
    config.enabled = True
else:
    # 创建新配置
    config = ChannelConfig(
        community_id=1,
        channel="wechat",
        config={
            "app_id": "wx1234567890abcdef",
            "app_secret": encrypted_secret
        },
        enabled=True
    )
    db.add(config)

db.commit()
print("✅ 微信渠道配置成功！")
db.close()
```

---

## 🧪 测试步骤

### 测试 1: 验证凭证加载

```bash
# 测试凭证是否能正确加载
python -c "
from app.services.wechat import wechat_service
from app.database import SessionLocal
import asyncio

async def test_credentials():
    try:
        token = await wechat_service._get_access_token(community_id=1)
        print(f'✅ Access Token 获取成功: {token[:20]}...')
    except Exception as e:
        print(f'❌ 失败: {e}')

asyncio.run(test_credentials())
"
```

**预期结果**: 显示 `✅ Access Token 获取成功: ACCESS_TOKEN_GOES...`

### 测试 2: 上传封面图

```bash
# 准备封面图
mkdir -p backend/uploads
# 将你的测试图片复制到 backend/uploads/test_cover.jpg

# 测试上传
python -c "
from app.services.wechat import wechat_service
import asyncio

async def test_upload():
    try:
        media_id = await wechat_service.upload_thumb_media(
            'backend/uploads/test_cover.jpg',
            community_id=1
        )
        print(f'✅ 封面图上传成功，media_id: {media_id}')
    except Exception as e:
        print(f'❌ 上传失败: {e}')

asyncio.run(test_upload())
"
```

**预期结果**: 显示 `✅ 封面图上传成功，media_id: xxxx`

### 测试 3: 创建测试内容

```bash
# 使用 API 创建测试内容
curl -X POST "http://localhost:8000/api/contents" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "X-Community-Id: ${COMMUNITY_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "【测试】微信发布功能验证",
    "content_markdown": "# 这是标题\n\n这是测试内容。\n\n- 列表项 1\n- 列表项 2\n\n```python\nprint(\"Hello WeChat!\")\n```",
    "author": "测试作者",
    "cover_image": "/uploads/test_cover.jpg",
    "source_type": "contribution",
    "status": "draft"
  }'

# 记录返回的内容 ID
export CONTENT_ID="返回的id字段"
```

### 测试 4: 预览微信格式

```bash
# 预览转换后的HTML
curl -X GET "http://localhost:8000/api/publish/${CONTENT_ID}/preview/wechat" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "X-Community-Id: ${COMMUNITY_ID}"
```

**预期结果**: 返回带有微信样式的HTML内容

### 测试 5: 发布到微信草稿箱

```bash
# 执行发布
curl -X POST "http://localhost:8000/api/publish/${CONTENT_ID}/wechat" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "X-Community-Id: ${COMMUNITY_ID}"
```

**预期结果**:
```json
{
  "id": 1,
  "content_id": 1,
  "channel": "wechat",
  "status": "draft",
  "platform_article_id": "xxxx",  // 微信返回的 media_id
  "community_id": 1,
  "created_at": "2026-02-09T12:34:56"
}
```

### 测试 6: 在微信公众号后台验证

1. 登录微信公众平台 [https://mp.weixin.qq.com](https://mp.weixin.qq.com)
2. 进入 **素材管理** → **草稿箱**
3. 查看最新的草稿：
   - ✅ 标题正确: "【测试】微信发布功能验证"
   - ✅ 封面图显示正常
   - ✅ 内容格式正确（标题、段落、代码块样式）
   - ✅ 作者署名正确

### 测试 7: 测试图片URL替换功能

```bash
# 创建包含本地图片的内容
curl -X POST "http://localhost:8000/api/contents" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "X-Community-Id: ${COMMUNITY_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "【测试】图片上传功能",
    "content_markdown": "# 图片测试\n\n本地图片：\n![测试图片](/uploads/test_image1.jpg)\n\n外部图片（应保留）：\n![外部图片](https://example.com/image.jpg)",
    "author": "测试作者",
    "cover_image": "/uploads/test_cover.jpg",
    "source_type": "contribution"
  }'

# 发布
export CONTENT_ID2="返回的id"
curl -X POST "http://localhost:8000/api/publish/${CONTENT_ID2}/wechat" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "X-Community-Id: ${COMMUNITY_ID}"
```

**微信后台验证**:
- ✅ 本地图片已上传到微信服务器，URL 变为 `https://mmbiz.qpic.cn/...`
- ✅ 外部图片URL保持不变

### 测试 8: 查询发布记录

```bash
# 查询所有发布记录
curl -X GET "http://localhost:8000/api/publish/records" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "X-Community-Id: ${COMMUNITY_ID}"

# 按内容ID过滤
curl -X GET "http://localhost:8000/api/publish/records?content_id=${CONTENT_ID}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "X-Community-Id: ${COMMUNITY_ID}"

# 按渠道过滤
curl -X GET "http://localhost:8000/api/publish/records?channel=wechat" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "X-Community-Id: ${COMMUNITY_ID}"
```

**预期结果**:
```json
{
  "total": 2,
  "items": [
    {
      "id": 2,
      "content_id": 2,
      "channel": "wechat",
      "status": "draft",
      "platform_article_id": "xxxx",
      "community_id": 1
    },
    {
      "id": 1,
      "content_id": 1,
      "channel": "wechat",
      "status": "draft",
      "platform_article_id": "xxxx",
      "community_id": 1
    }
  ]
}
```

---

## 🔍 故障排除

### 问题 1: `获取access_token失败 [errcode=40001]: invalid credential`

**原因**: AppID 或 AppSecret 错误

**解决方案**:
1. 登录微信公众平台重新核对 AppID
2. 重置 AppSecret 并更新配置
3. 确认没有多余的空格或换行符
4. 重新配置渠道

### 问题 2: `获取access_token失败 [errcode=40164]: invalid ip`

**原因**: IP 未在白名单中

**解决方案**:
1. 登录微信公众平台
2. 在 **基本配置** → **IP白名单** 添加服务器IP
3. 或临时清空IP白名单（仅开发测试）

### 问题 3: `封面图上传失败: errcode=40007`

**原因**: media_id 不合法或已过期

**解决方案**:
1. 检查图片格式是否为 JPG/PNG
2. 检查图片大小是否 < 2MB
3. 确认图片文件路径正确
4. 使用新的图片重新上传

### 问题 4: `微信公众号未配置`

**原因**: 数据库中没有找到渠道配置

**解决方案**:
```bash
# 检查配置是否存在
python -c "
from app.database import SessionLocal
from app.models.channel import ChannelConfig

db = SessionLocal()
config = db.query(ChannelConfig).filter(
    ChannelConfig.community_id == 1,
    ChannelConfig.channel == 'wechat'
).first()

if config:
    print(f'✅ 配置存在: {config.config}')
else:
    print('❌ 配置不存在，请重新配置')
db.close()
"
```

### 问题 5: 草稿箱中看不到发布的内容

**可能原因**:
1. 发布返回了 `status: "failed"`，检查 `error_message`
2. 使用了错误的公众号登录
3. 草稿被自动清理（草稿有效期）

**检查方法**:
```bash
# 查看发布记录详情
curl -X GET "http://localhost:8000/api/publish/records?content_id=${CONTENT_ID}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "X-Community-Id: ${COMMUNITY_ID}"
```

### 问题 6: `微信API请求超时，请稍后重试`

**原因**: 网络问题或微信服务器响应慢

**解决方案**:
1. 检查服务器网络连接
2. 稍后重试
3. 如频繁出现，检查是否被微信限流

---

## ✅ 验证清单

完成以下检查项确保功能正常：

### 基础功能
- [ ] AppID 和 AppSecret 配置正确，能获取 access_token
- [ ] 封面图能成功上传到微信素材库
- [ ] Markdown 能正确转换为微信HTML格式
- [ ] 草稿能成功创建并在微信后台看到

### 高级功能
- [ ] 本地图片自动上传并替换URL
- [ ] 外部图片URL保持不变
- [ ] 发布记录正确保存到数据库
- [ ] `community_id` 字段正确关联
- [ ] 多租户隔离正常（不同社区看不到对方的记录）

### 错误处理
- [ ] 错误的 AppSecret 返回明确的错误信息
- [ ] 缺少封面图时返回 400 错误
- [ ] 不存在的内容返回 404 错误
- [ ] API 错误时记录 `error_message` 到数据库

### 安全性
- [ ] AppSecret 在数据库中是加密存储的
- [ ] 查询发布记录时有 `community_id` 过滤
- [ ] 不同社区的用户看不到对方的发布记录

---

## 📊 性能基准

以下是正常情况下的性能指标（供参考）：

| 操作 | 预期耗时 | 说明 |
|------|---------|------|
| 获取 access_token | < 2秒 | 首次获取或过期后 |
| 上传封面图（500KB） | < 3秒 | 取决于网络速度 |
| 创建草稿 | < 2秒 | 内容大小 < 50KB |
| 完整发布流程 | < 10秒 | 包含封面上传 + 草稿创建 |

如果超过预期耗时的 2 倍，建议检查网络连接。

---

## 📝 清理测试数据

测试完成后，可以清理测试数据：

### 清理微信草稿箱
1. 登录微信公众平台
2. 进入 **素材管理** → **草稿箱**
3. 勾选测试草稿，点击 **删除**

### 清理数据库记录
```bash
python -c "
from app.database import SessionLocal
from app.models.publish_record import PublishRecord
from app.models.content import Content

db = SessionLocal()

# 删除测试发布记录
db.query(PublishRecord).filter(
    PublishRecord.content_id.in_([1, 2])  # 替换为实际的测试内容ID
).delete()

# 删除测试内容
db.query(Content).filter(
    Content.title.like('%测试%')
).delete()

db.commit()
print('✅ 测试数据已清理')
db.close()
"
```

---

## 🚀 生产环境部署建议

1. **环境变量管理**: 使用 `.env` 文件管理敏感配置，不要硬编码
2. **日志监控**: 配置日志收集，监控发布成功率
3. **限流控制**: 微信API有调用频率限制，建议添加队列
4. **错误告警**: 发布失败时发送通知（邮件/webhook）
5. **定期测试**: 每月至少执行一次完整验证流程

---

## 📚 参考文档

- [微信公众平台接口调试工具](https://mp.weixin.qq.com/debug/)
- [微信公众平台官方文档 - 草稿箱](https://developers.weixin.qq.com/doc/offiaccount/Draft_Box/Add_draft.html)
- [微信公众平台官方文档 - 素材管理](https://developers.weixin.qq.com/doc/offiaccount/Asset_Management/New_temporary_materials.html)

---

**编写时间**: 2026-02-09
**适用版本**: OmniContent v2.0+
**维护者**: 内容与发布专家 (角色2)
