# 社区权限功能测试

## 修改内容

### 后端修改

1. **新增Schema** (`backend/app/schemas/community.py`):
   - 添加 `CommunityWithRole` schema，继承自 `CommunityBrief`，包含 `role` 字段

2. **修改权限检查** (`backend/app/api/communities.py`):
   - `update_community` 端点：只允许超级管理员和社区管理员编辑社区信息
   - 使用 `get_user_community_role` 函数检查用户在社区中的角色

3. **修改用户信息返回** (`backend/app/api/auth.py`):
   - `/me` 端点现在返回用户在每个社区的角色信息

### 前端修改

1. **类型定义** (`frontend/src/stores/auth.ts`):
   - `Community` 接口添加 `role` 字段

2. **权限判断** (`frontend/src/stores/user.ts`):
   - `isCommunityAdmin` 现在根据当前社区的实际角色判断，而不是只检查 `isSuperuser`

3. **UI权限控制** (`frontend/src/views/CommunityManage.vue`):
   - "新建社区" 按钮：仅超级管理员可见
   - "编辑" 菜单项：超级管理员和社区管理员可见
   - "成员管理" 菜单项：仅超级管理员可见
   - "停用/启用" 菜单项：超级管理员和社区管理员可见
   - "删除" 菜单项：仅超级管理员可见

## 权限矩阵

| 功能 | 超级管理员 | 社区管理员 | 普通成员 |
|------|-----------|-----------|---------|
| 新建社区 | ✅ | ❌ | ❌ |
| 编辑社区 | ✅ | ✅ (仅自己管理的社区) | ❌ |
| 删除社区 | ✅ | ❌ | ❌ |
| 停用/启用社区 | ✅ | ✅ (仅自己管理的社区) | ❌ |
| 成员管理 | ✅ | ❌ | ❌ |
| 渠道管理 | ✅ | ✅ | ✅ |

## 测试步骤

### 1. 测试超级管理员

1. 使用超级管理员账号登录
2. 访问社区管理页面
3. 验证：
   - ✅ 可以看到"新建社区"按钮
   - ✅ 可以看到所有社区
   - ✅ 每个社区都有完整的操作菜单（编辑、渠道管理、成员管理、停用/启用、删除）

### 2. 测试社区管理员

1. 创建一个普通用户并设置为某个社区的管理员
   ```bash
   # 在后端数据库中手动设置或通过API
   ```

2. 使用该账号登录
3. 访问社区管理页面
4. 验证：
   - ❌ 看不到"新建社区"按钮
   - ✅ 只能看到自己是成员的社区
   - ✅ 对于自己管理的社区：可以编辑、停用/启用、管理渠道
   - ❌ 看不到"成员管理"和"删除"选项

### 3. 测试普通成员

1. 创建一个普通用户并添加到社区（role='user'）
2. 使用该账号登录
3. 访问社区管理页面
4. 验证：
   - ❌ 看不到"新建社区"按钮
   - ✅ 只能看到自己是成员的社区
   - ❌ 看不到"编辑"选项
   - ✅ 可以看到"渠道管理"（但只读）
   - ❌ 看不到"停用/启用"、"成员管理"和"删除"选项

### 4. 测试API权限

使用curl或Postman测试：

```bash
# 获取token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password"}' \
  | jq -r '.access_token')

# 获取用户信息（应该包含role字段）
curl -s http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN" | jq

# 尝试编辑社区（普通用户应该被拒绝）
curl -X PUT http://localhost:8000/api/communities/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Updated Name"}' \
  | jq
```

预期结果：
- 超级管理员：成功编辑
- 社区管理员：成功编辑自己管理的社区
- 普通成员：返回403 Forbidden

## 已知问题

1. ~~前端只检查 `isSuperuser`，没有检查实际的社区角色~~ ✅ 已修复
2. ~~后端 `update_community` 允许所有社区成员编辑~~ ✅ 已修复
3. ~~`/me` 端点不返回用户在各社区的角色~~ ✅ 已修复

## 其他功能状态

当前社区管理功能包括：

✅ **已实现**：
- 创建社区（超级管理员）
- 编辑社区（超级管理员和社区管理员）
- 删除社区（超级管理员）
- 停用/启用社区（超级管理员和社区管理员）
- 成员管理（超级管理员）
  - 添加成员
  - 移除成员
  - 修改成员角色（admin/user）
- 渠道管理（所有成员）
  - 添加渠道配置
  - 编辑渠道配置
  - 删除渠道配置
  - 启用/停用渠道

❌ **未实现**：
- 社区设置（settings字段的UI管理）
- 社区统计信息（成员数、内容数等）
- 社区日志/审计记录
- 批量导入社区成员
