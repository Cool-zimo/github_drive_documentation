---
layout: default
title: 插件开发指南
---

# 插件开发指南

## 插件是什么

插件是一个**独立的 HTML 文件**，在 iframe 沙箱中运行，通过 `postMessage` 与 GitHub Drive 主应用交互。

- 无法直接访问主应用的 DOM
- 所有数据操作通过 API 完成（见 [API 参考](plugin-api.html)）
- 自 v0.0.37 起，**所有插件统一全屏显示**

## 两种发布方式

### 🏛️ 官方插件（受信任）

- 提交到 [github_drive_plugins](https://github.com/Cool-zimo/github_drive_plugins)
- 经过审核，在插件广场「官方插件」Tab 显示
- 无安全警告，用户可直接安装

### 🌐 第三方插件（众筹模式）

- 任何人创建名为 `GD-Plugin-{插件名}` 的公开仓库即可发布
- 自动被搜索到，显示在「发现插件」Tab
- 安装时显示安全警告，需用户确认信任
- 无需申请，完全开放

---

## 开发步骤

### 1. 创建 HTML 文件

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我的插件</title>
</head>
<body>
    <button id="btn">读取文件</button>
    <div id="out"></div>

    <script>
        // ---- 与宿主通信的封装（可直接复制）----
        let seq = 0;
        function call(action, data = {}) {
            return new Promise((resolve, reject) => {
                const id = ++seq;
                const handler = (e) => {
                    if (e.data && e.data.type === 'gd-response' && e.data.id === id) {
                        window.removeEventListener('message', handler);
                        clearTimeout(timer);
                        if (e.data.error) reject(new Error(e.data.error));
                        else resolve(e.data.result);
                    }
                };
                // 必须有超时保护，否则宿主无响应时 Promise 永远 pending
                const timer = setTimeout(() => {
                    window.removeEventListener('message', handler);
                    reject(new Error('宿主响应超时'));
                }, 15000);
                window.addEventListener('message', handler);
                parent.postMessage({ type: 'gd-api', id, action, data }, '*');
            });
        }

        document.getElementById('btn').onclick = async () => {
            try {
                const files = await call('listFiles', { path: '/drive_home' });
                await call('showToast', { message: `找到 ${files.length} 个文件`, type: 'success' });
                document.getElementById('out').textContent = JSON.stringify(files, null, 2);
            } catch (e) {
                document.getElementById('out').textContent = '失败: ' + e.message;
            }
        };
    </script>
</body>
</html>
```

> 封装要点：
> - 用**自增 id** 配对请求与响应（并发调用不串台）
> - **必须**设超时，并同时 `clearTimeout` + `removeEventListener`
> - 用 `parent.postMessage`，不是 `window.parent.postMessage` 的父窗口自身

### 2. 能力探测（推荐）

不同版本的宿主支持的 API 不同。启动时先自省，避免调用不存在的 API 报错：

```js
const actions = await call('api.listActions');
if (actions.includes('cangshu.listRepos')) {
    // 支持仓鼠联动
} else {
    // 老版本宿主，降级
}
```

### 3. 提交到插件市场

1. Fork [github_drive_plugins](https://github.com/Cool-zimo/github_drive_plugins)
2. 把插件 HTML 放进 `plugins/` 目录
3. 在 `plugins.json` 中添加元数据：

```json
{
  "id": "my-plugin",
  "name": "我的插件",
  "description": "插件功能描述",
  "author": "你的用户名",
  "version": "1.0.0",
  "type": "tool",
  "icon": "🚀",
  "file": "plugins/my-plugin.html",
  "tags": ["工具", "示例"]
}
```

**字段说明**

| 字段 | 必填 | 说明 |
|---|---|---|
| `id` | ✅ | 唯一标识，只能用小写字母、数字、连字符 |
| `name` | ✅ | 显示名称，可带 emoji |
| `description` | ✅ | 一句话说明 |
| `author` | ✅ | 作者 |
| `version` | ✅ | 语义化版本号，会显示在全屏顶栏 |
| `file` | ✅ | 插件 HTML 在仓库中的路径 |
| `icon` | ⬜ | 显示在顶栏与卡片上，见下 |
| `type` | ⬜ | `tool`（默认）或 `game`，只影响**默认图标兜底** |
| `tags` | ⬜ | 字符串数组，用于筛选 |
| `externalUrl` | ⬜ | 直接用外部 URL 加载，不打包 HTML |

**icon 支持的格式**

- **Emoji**（推荐）：`"🚀"`、`"📺"`、`"🧩"`
- **图片 URL**：`"https://example.com/icon.png"`

未设置时按 type 兜底：游戏 🎮 ／工具 🔌。

4. 提交 Pull Request

### 发布第三方插件（众筹模式）

1. 创建公开仓库，命名 `GD-Plugin-{插件名}`，如 `GD-Plugin-CoolClock`
2. 根目录放 `plugin.json`：

```json
{
  "id": "your-plugin-id",
  "name": "插件名称",
  "description": "插件功能描述",
  "author": "你的GitHub用户名",
  "version": "1.0.0",
  "icon": "🧩",
  "type": "tool",
  "file": "index.html"
}
```

3. 创建插件 HTML（如 `index.html`）
4. 推送后即可在插件广场「发现插件」Tab 搜到

> ⚠️ 第三方插件安装时会显示安全警告。
> 请确保代码安全可信，**不要窃取用户 Token 或文件**。

---

## 运行方式：全屏

自 v0.0.37 起，所有插件统一**全屏显示**：

- 顶部有一条工具条，显示 **图标 + 名称 + 版本号**
- 右侧「✕ 关闭」按钮，或按 **ESC** 退出
- 打开期间锁定页面背景滚动
- 可同时打开多个插件，各自独立（互不影响通信）

> 早期版本只有 `type: "game"` 或 `fullscreen: true` 的插件全屏，
> 其余在 70vh 的弹窗里跑。`fullscreen` 字段现已**不再需要**，
> 保留也不会出错，但推荐删掉。

---

## 安全须知

**必须转义不可信输入。** 文件名、仓库名、备注名都来自用户配置，
直接拼进 `innerHTML` 会造成存储型 XSS：

```js
const esc = (s) => String(s == null ? '' : s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');

// ✅ 正确
el.innerHTML = `<div>${esc(repo.name)}</div>`;
// ❌ 危险
el.innerHTML = `<div>${repo.name}</div>`;
```

其他建议：

- **不要把 Token 发到第三方服务器**（`getToken()` 拿到的令牌）
- 插件 HTML 建议控制在 **100KB 以内**
- 大文件操作较慢，记得显示加载状态
- 网络请求要有超时与失败提示，不要静默吞掉错误

---

## 调试技巧

插件在 iframe 中，DevTools 里把控制台上下文切到插件的 frame 即可看到 `console.log`。

快速验证宿主是否收到消息：

```js
// 在插件里
parent.postMessage({ type: 'gd-api', id: 1, action: 'api.listActions', data: {} }, '*');
window.addEventListener('message', e => console.log('收到:', e.data));
```

若长时间无响应，检查：

1. `action` 名称拼写（用 `api.listActions` 核对）
2. 是否在 iframe 中运行（直接打开 HTML 文件拿不到响应）
3. 控制台有无跨域报错

---

## 示例

- [cangshu-link.html](https://github.com/Cool-zimo/github_drive_plugins/blob/main/plugins/cangshu-link.html)
  — 🐹 仓鼠联动，演示了完整的 `call()` 封装、能力探测、列表渲染与 XSS 转义
