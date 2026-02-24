# openGecko LFX Insights Light Design System

This project's frontend uses the **LFX Insights light theme** throughout. All pages and components must strictly follow the specifications below.

---

## Tech Stack

- Vue 3 + TypeScript + Element Plus
- `<style scoped>` or plain `<style>` (prefer plain CSS; use `lang="scss"` only when `:deep()` penetration requires it)
- CSS variables scoped to the component root selector (e.g., `.content-list`) — **never on `:root`**

---

## Design Tokens

Declare CSS variables on the component root selector in every page component's `<style>`:

```css
.page-root {
  --text-primary:   #1e293b;
  --text-secondary: #64748b;
  --text-muted:     #94a3b8;
  --blue:           #0095ff;
  --green:          #22c55e;
  --orange:         #f59e0b;
  --red:            #ef4444;
  --border:         #e2e8f0;
  --shadow:         0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-hover:   0 4px 12px rgba(0, 0, 0, 0.08);
  --radius:         12px;
}
```

### Color Reference

| Purpose | Value | Variable |
|---------|-------|----------|
| Page background | `#f5f7fa` | — (set in `App.vue .app-main`) |
| Card / white background | `#ffffff` | — |
| Primary text | `#1e293b` | `--text-primary` |
| Secondary text | `#64748b` | `--text-secondary` |
| Muted text | `#94a3b8` | `--text-muted` |
| Brand blue | `#0095ff` | `--blue` |
| Brand blue hover | `#0080e6` | — |
| Success green | `#22c55e` | `--green` |
| Warning orange | `#f59e0b` | `--orange` |
| Danger red | `#ef4444` | `--red` |
| Border | `#e2e8f0` | `--border` |
| Divider | `#f1f5f9` | — |
| Subtle background | `#f8fafc` | — |
| Blue tint | `#eff6ff` | — |
| Green tint | `#f0fdf4` | — |
| Orange tint | `#fffbeb` | — |
| Red tint | `#fef2f2` | — |

---

## Layout

### Page Container

```css
.page-root {
  padding: 32px 40px 60px;
  max-width: 1400px;  /* or 1440px */
  margin: 0 auto;
}
```

### Page Title Row

```css
.page-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
}

.page-title-row h2 {
  margin: 0 0 6px;
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.page-title-row .subtitle {
  margin: 0;
  font-size: 15px;
  color: var(--text-secondary);
}
```

### Section Card

```css
.section-card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius);   /* 12px */
  padding: 24px 28px;
  margin-bottom: 24px;
  box-shadow: var(--shadow);
  transition: all 0.2s ease;
}
.section-card:hover {
  box-shadow: var(--shadow-hover);
}
```

### Section Header

```css
.section-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}
/* Note: section-header has no border-bottom and no padding-bottom */
```

---

## Component Specifications

### Badges / Tags

- Border-radius: `6px`; **no border**
- Use light-background + dark-text pairs:
  - Blue: `background: #eff6ff; color: #1d4ed8`
  - Green: `background: #f0fdf4; color: #15803d`
  - Orange: `background: #fffbeb; color: #b45309`
  - Gray: `background: #f1f5f9; color: #64748b`
  - Red: `background: #fef2f2; color: #dc2626`

### Buttons

```css
:deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.15s ease;
}

/* Primary button */
:deep(.el-button--primary) {
  background: var(--blue);
  border-color: var(--blue);
}
:deep(.el-button--primary:hover) {
  background: #0080e6;
  border-color: #0080e6;
}

/* Default button */
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

- **Never** use `transform: translateY()` on hover
- Text-link buttons use the `link` attribute; hover adds a subtle background tint
- **Caution**: `:deep(.el-button--primary)` background overrides also affect `text` type buttons — use custom CSS classes or `<span>` wrappers for text-style action links instead

### Inputs

```css
:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--border);
  border-radius: 8px;
}
:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--blue), 0 0 0 3px rgba(0, 149, 255, 0.1);
}
```

### Tables

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

### Dialogs

```css
:deep(.el-dialog) {
  border-radius: var(--radius);
}
:deep(.el-dialog__header) {
  border-bottom: 1px solid #f1f5f9;
}
```

### Pagination

```css
:deep(.el-pagination .el-pager li.is-active) {
  background: var(--blue);
  color: white;
}
```

---

## Sidebar (App.vue)

- Background: `#ffffff`; right border: `1px solid #e2e8f0`
- Logo area: white background + `border-bottom: 1px solid #e2e8f0`
- Menu item text: `#64748b`; active: `#0095ff`
- Menu item hover: `background: #f8fafc; color: #1e293b`
- Menu item active: `background: #eff6ff; color: #0095ff`
- Menu item border-radius: `8px`; margin: `2px 8px`
- `el-menu` inline props: `background-color="#ffffff"` `text-color="#64748b"` `active-text-color="#0095ff"`

---

## Login Page

- Container background: `#f5f7fa` + soft radial-gradient decoration
- Card: solid white + `border: 1px solid #e2e8f0` + `border-radius: 20px`
- Title: `#1e293b`; subtitle: `#64748b`
- Inputs: `background: #f8fafc`; focus: white background + `#0095ff` border + blue glow
- Login button: `#0095ff`; no transform animation

---

## Responsive Breakpoints

```css
@media (max-width: 1200px) {
  .page-root { padding: 28px 24px; }
}
@media (max-width: 734px) {
  .page-root { padding: 20px 16px; }
  .page-title-row h2 { font-size: 22px; }
  .section-card { padding: 16px; }
}
```

---

## Forbidden Colors

These are Element Plus defaults or old dark-theme remnants — **must not appear**:

| Forbidden | Replace with |
|-----------|-------------|
| `#409EFF` | `#0095ff` (`--blue`) |
| `#303133` | `#1e293b` (`--text-primary`) |
| `#606266` | `#64748b` (`--text-secondary`) |
| `#909399` | `#94a3b8` (`--text-muted`) |
| `#dcdfe6` / `#ebeef5` | `#e2e8f0` (`--border`) |
| `#f0f0f0` | `#e2e8f0` (`--border`) or `#f1f5f9` |
| `#1d2129` | `#1e293b` (`--text-primary`) |
| `#86909c` | `#64748b` (`--text-secondary`) |
| `#0071e3` | `#0095ff` (`--blue`) |
| `--el-color-primary` | `var(--blue)` |
| `--el-text-color-*` | corresponding `--text-*` variable |
| `--el-fill-color-*` | `#f8fafc` or `#f1f5f9` |
| `--el-border-color` | `var(--border)` |

---

## Design Checklist

When creating or modifying any page:

- [ ] CSS variables declared on component root selector (not `:root`)
- [ ] Page padding: `32px 40px 60px`; max-width: `1400px`
- [ ] `h2`: `28px / 700 / letter-spacing: -0.02em`
- [ ] Subtitle: `15px / var(--text-secondary)`
- [ ] Cards use `--border` + `--shadow` + `--radius`
- [ ] Buttons: `border-radius: 8px`, `transition: 0.15s ease`
- [ ] No `transform: translateY` hover effects
- [ ] Badges/Tags: no border, light-bg + dark-text pairs
- [ ] No forbidden colors
- [ ] Element Plus overrides use `:deep()` syntax
- [ ] No `lang="scss"` unless strictly necessary
