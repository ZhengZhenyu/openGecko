# openGecko LFX Insights 浅色设计系统

本项目前端统一使用 **LFX Insights 浅色主题**风格。所有页面、组件需严格遵循以下规范。

---

## 技术栈

- Vue 3 + TypeScript + Element Plus
- `<style scoped>` 或 `<style lang="scss">` (FullCalendar 等需要穿透时)
- CSS 变量作用域：定义在各组件的根选择器上（如 `.content-list`），**不使用 `:root`**

---

## 设计令牌 (Design Tokens)

每个页面组件的 `<style>` 中以 CSS 变量声明：

```css
.page-root {
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  --blue: #0095ff;
  --green: #22c55e;
  --orange: #f59e0b;
  --red: #ef4444;
  --border: #e2e8f0;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-hover: 0 4px 12px rgba(0, 0, 0, 0.08);
  --radius: 12px;
}
```

### 颜色映射

| 用途 | 色值 | 变量 |
|------|------|------|
| 页面背景 | `#f5f7fa` | — (在 App.vue `.app-main`) |
| 卡片/白色背景 | `#ffffff` | — |
| 主要文字 | `#1e293b` | `--text-primary` |
| 次要文字 | `#64748b` | `--text-secondary` |
| 弱化文字 | `#94a3b8` | `--text-muted` |
| 品牌蓝 | `#0095ff` | `--blue` |
| 品牌蓝 hover | `#0080e6` | — |
| 成功绿 | `#22c55e` | `--green` |
| 警告橙 | `#f59e0b` | `--orange` |
| 危险红 | `#ef4444` | `--red` |
| 边框 | `#e2e8f0` | `--border` |
| 内部分割线 | `#f1f5f9` | — |
| 浅底色背景 | `#f8fafc` | — |
| 蓝色浅底 | `#eff6ff` | — |
| 绿色浅底 | `#f0fdf4` | — |
| 橙色浅底 | `#fffbeb` | — |
| 红色浅底 | `#fef2f2` | — |

---

## 布局规范

### 页面容器

```css
.page-root {
  padding: 32px 40px 60px;
  max-width: 1400px;  /* 或 1440px */
  margin: 0 auto;
}
```

### 页面标题

```css
.page-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
}

.page-title h2 {
  margin: 0 0 6px;
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.page-title .subtitle {
  margin: 0;
  font-size: 15px;
  color: var(--text-secondary);
}
```

### 区块卡片 (Section Card)

```css
.section-card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius);        /* 12px */
  padding: 24px 28px;
  margin-bottom: 24px;
  box-shadow: var(--shadow);
  transition: all 0.2s ease;
}

.section-card:hover {
  box-shadow: var(--shadow-hover);
}
```

### 区块标题

```css
.section-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}
/* 注意：section-header 无 border-bottom、无 padding-bottom */
```

---

## 组件细节规范

### 徽章 (Badge / Tag)

- 圆角: `6px`
- **无边框** (border: none)
- 使用 浅底色 + 深文字 配色：
  - 蓝: `bg: #eff6ff; color: #1d4ed8`
  - 绿: `bg: #f0fdf4; color: #15803d`
  - 橙: `bg: #fffbeb; color: #b45309`
  - 灰: `bg: #f1f5f9; color: #64748b`

### 按钮

```css
:deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.15s ease;
}

/* 主按钮 */
:deep(.el-button--primary) {
  background: var(--blue);    /* #0095ff */
  border-color: var(--blue);
}
:deep(.el-button--primary:hover) {
  background: #0080e6;
  border-color: #0080e6;
}

/* 默认按钮 */
:deep(.el-button--default) {
  background: #ffffff;
  border: 1px solid var(--border);
  color: var(--text-primary);
}
:deep(.el-button--default:hover) {
  border-color: #cbd5e1;
  background: #f8fafc;
}
```

- **禁止** 使用 `transform: translateY()` hover 效果
- 文字链接按钮使用 `link` 属性，hover 加浅底色

### 输入框

```css
:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--border);
  border-radius: 8px;
}
:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--blue), 0 0 0 3px rgba(0, 149, 255, 0.1);
}
```

### 表格

```css
:deep(.el-table th) {
  background: #f8fafc;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border);
}

:deep(.el-table td) {
  border-bottom: 1px solid #f1f5f9;
}

:deep(.el-table .el-table__row:hover > td) {
  background: #f8fafc !important;
}
```

### 对话框

```css
:deep(.el-dialog) {
  border-radius: var(--radius);
}
:deep(.el-dialog__header) {
  border-bottom: 1px solid #f1f5f9;
}
```

### 分页

```css
:deep(.el-pagination .el-pager li.is-active) {
  background: var(--blue);
  color: white;
}
```

---

## 侧边栏 (App.vue)

- 背景: `#ffffff`
- 右边框: `1px solid #e2e8f0`
- Logo 区域: 白色背景 + `border-bottom: 1px solid #e2e8f0`
- 菜单项文字: `#64748b`，激活: `#0095ff`
- 菜单项 hover: `background: #f8fafc; color: #1e293b`
- 菜单项 active: `background: #eff6ff; color: #0095ff`
- 菜单项圆角: `8px`，margin: `2px 8px`
- el-menu 内联属性: `background-color="#ffffff"` `text-color="#64748b"` `active-text-color="#0095ff"`

---

## 登录页

- 容器背景: `#f5f7fa` + 柔和径向渐变装饰
- 卡片: 白色实底 + `border: 1px solid #e2e8f0` + `border-radius: 20px`
- 标题: `#1e293b`，副标题: `#64748b`
- 输入框: `bg: #f8fafc`, focus 白底 + `#0095ff` 边框 + 蓝色光晕
- 登录按钮: `#0095ff`，无 transform 动效

---

## 响应式断点

```css
@media (max-width: 1200px) {
  .page-root { padding: 28px 24px; }
}
@media (max-width: 734px) {
  .page-root { padding: 20px 16px; }
  .page-title h2 { font-size: 22px; }
  .section-card { padding: 16px; }
}
```

---

## 禁止使用的旧色值

以下为 Element Plus 默认色或旧深色主题残留，**不得出现**：

| 旧色值 | 应替换为 |
|--------|----------|
| `#409EFF` | `#0095ff` (--blue) |
| `#303133` | `#1e293b` (--text-primary) |
| `#606266` | `#64748b` (--text-secondary) |
| `#909399` | `#94a3b8` (--text-muted) |
| `#dcdfe6` / `#ebeef5` | `#e2e8f0` (--border) |
| `#f0f0f0` | `#e2e8f0` (--border) 或 `#f1f5f9` |
| `#1d2129` | `#1e293b` (--text-primary) |
| `#86909c` | `#64748b` (--text-secondary) |
| `#0071e3` | `#0095ff` (--blue) |
| `--el-color-primary` | 直接用 `var(--blue)` |
| `--el-text-color-*` | 直接用对应 `--text-*` 变量 |
| `--el-fill-color-*` | 直接用 `#f8fafc` 或 `#f1f5f9` |

---

## 检查清单

新建或修改页面时，确保：

- [ ] 组件根选择器中声明了完整的 CSS 变量
- [ ] 页面 padding 为 `32px 40px 60px`，max-width `1400px`
- [ ] h2 标题: `28px / 700 / letter-spacing: -0.02em`
- [ ] subtitle: `15px / --text-secondary`
- [ ] 卡片使用 `--border` + `--shadow` + `--radius`
- [ ] 按钮圆角 `8px`，transition `0.15s ease`
- [ ] 无 `transform: translateY` 的 hover 效果
- [ ] 徽章/Tag 无边框
- [ ] 未使用任何"禁止色值"
- [ ] Element Plus 深度覆盖使用 `:deep()` 语法
