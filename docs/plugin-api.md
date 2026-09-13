---
layout: default
title: 插件 API 参考
---

# 插件 API 参考

## 通信方式

插件运行在 **iframe** 中，与主应用通过 `postMessage` 双向通信。

> ⚠️ 早期文档写的「通过 `GD` 对象调用」是**错的** —— 实际并没有 `GD` 全局对象。
> 你需要自己封装一个 `call()`，下面有可直接复制的实现。

### 可直接复用的封装

把这段放进插件的 `<script>` 里：

```js
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
        // 超时保护：宿主无响应时不能让 Promise 永远挂着
        const timer = setTimeout(() => {
            window.removeEventListener('message', handler);
            reject(new Error('宿主响应超时'));
        }, 15000);
        window.addEventListener('message', handler);
        parent.postMessage({ type: 'gd-api', id, action, data }, '*');
    });
}
```

要点：

- 用**自增 id** 配对请求与响应，并发调用不会串台
- **必须**有超时保护，否则宿主没响应时 Promise 永远 pending
- 收到响应后要 `removeEventListener` + `clearTimeout`，否则监听器泄漏

### 协议格式

**请求**（插件 → 主应用）

```json
{ "type": "gd-api", "id": 1, "action": "listFiles", "data": { "path": "/drive_home" } }
```

**成功响应**（主应用 → 插件）

```json
{ "type": "gd-response", "id": 1, "result": [...] }
```

**失败响应**

```json
{ "type": "gd-response", "id": 1, "error": "错误信息" }
```

---

## 文件操作

### listFiles(path)

列出指定路径的文件和文件夹。

| 参数 | 类型 | 说明 |
|---|---|---|
| `path` | string | 虚拟路径，如 `/drive_home`，默认 `/drive_home` |

**返回**

```json
[
  { "name": "file.txt", "path": "/drive_home/file.txt", "isFolder": false, "size": 1024 },
  { "name": "文件夹", "path": "/drive_home/文件夹", "isFolder": true, "size": 0 }
]
```

### downloadFile(path)

下载文件内容（文本格式）。

| 参数 | 类型 | 说明 |
|---|---|---|
| `path` | string | 文件虚拟路径 |

**返回** (string) 文件文本内容

### uploadFile(name, content, path)

上传文件。

| 参数 | 类型 | 说明 |
|---|---|---|
| `name` | string | 文件名 |
| `content` | string | 文件内容（文本） |
| `path` | string | 目标目录，默认 `/drive_home` |

**返回** `{ "success": true }`

---

## 界面与环境

### showToast(message, type)

显示提示消息。

| 参数 | 类型 | 说明 |
|---|---|---|
| `message` | string | 消息内容 |
| `type` | string | `info`（默认） \| `success` \| `error` |

### getCurrentPath()

获取用户当前浏览的目录。

**返回** (string) 如 `/drive_home/文档`

### getToken()

获取用户的 GitHub Personal Access Token，插件可用它直接调 GitHub API。

**返回** (string) GitHub Token

> ⚠️ 请谨慎使用 Token，**不要上传到任何第三方服务器**。

### getBackendConfig()

获取后端服务配置（若用户配置了自建后端）。

**返回**

```json
{ "url": "http://localhost:8787", "token": "..." }
```

### backendRequest(path, method, body)

向后端服务发请求。

| 参数 | 类型 | 说明 |
|---|---|---|
| `path` | string | 接口路径，默认 `/` |
| `method` | string | 默认 `GET` |
| `body` | object | 请求体（可选） |

---

## 仓鼠联动

「仓鼠」是配套的 GitHub 仓库管理面板（<https://cool-zimo.github.io/cangshu/>）。
这组 API 让插件能读写它的管理配置。

**关键设计**：配置的真实来源是 GitHub 仓库 `cangshu-config/cangshu.json`，
**不是 localStorage** —— 所以跨设备一致，也不依赖同源（换浏览器照样读得到）。

### cangshu.status()

获取联动状态。

**返回**

```json
{
  "installed": true,
  "exists": true,
  "configRepo": "cangshu-config",
  "count": 3,
  "url": "https://cool-zimo.github.io/cangshu/",
  "tokenShared": true
}
```

| 字段 | 说明 |
|---|---|
| `installed` | 配置仓库是否存在 |
| `exists` | 配置文件是否已创建 |
| `count` | 已管理的仓库数 |
| `tokenShared` | 两个应用是否已共享令牌（决定是否免登录跳转） |

### cangshu.getConfig()

读取完整配置。

**返回**

```json
{
  "version": 1,
  "updatedAt": "2026-09-12T00:00:00Z",
  "managed": [
    { "owner": "Cool-zimo", "repo": "xiudao", "alias": "修道游戏", "note": "", "addedAt": "..." }
  ],
  "settings": { "configRepo": "cangshu-config", "theme": "auto" }
}
```

### cangshu.listRepos(detail)

列出被管理的仓库。

| 参数 | 类型 | 说明 |
|---|---|---|
| `detail` | boolean | `true` 时附带仓库详情（Pages / 体积 / 语言 / 星标），需额外请求 |

**不带详情**返回 `managed` 原样数组；**带详情**时每项追加：

```json
{
  "owner": "Cool-zimo", "repo": "xiudao",
  "html_url": "https://github.com/Cool-zimo/xiudao",
  "description": "...", "private": false,
  "language": "JavaScript", "stars": 3, "size": 2048,
  "default_branch": "main", "updated_at": "...",
  "pages": { "enabled": true, "url": "https://...", "status": "built" }
}
```

某个仓库已被删除时，该项带 `missing: true`。

### cangshu.addRepo(owner, repo, meta)

添加仓库到管理列表。

| 参数 | 类型 | 说明 |
|---|---|---|
| `owner` | string | 仓库所有者 |
| `repo` | string | 仓库名 |
| `meta` | object | `{ alias, note }`，可选 |

**返回** `{ "ok": true, "count": 4 }`

已存在时返回 `{ "ok": false, "error": "...", "duplicated": true }`。

### cangshu.removeRepo(owner, repo)

从管理列表移除。**只改配置，不会删除 GitHub 上的仓库。**

**返回** `{ "ok": true, "count": 3 }`

### cangshu.hasRepo(owner, repo)

**返回** (boolean) 是否已管理

### cangshu.setAlias(owner, repo, alias)

设置备注名（只影响显示，不改仓库真名）。

### cangshu.ensureConfig()

配置仓库不存在时自动创建（私有仓库 + 初始配置）。

**返回** `{ "ok": true, "created": true }` — `created` 为 `false` 表示原本就有。

### cangshu.open(params)

带上下文跳转到仓鼠。

| 参数 | 类型 | 说明 |
|---|---|---|
| `params.repo` | string | 如 `"Cool-zimo/xiudao"`，过去后自动定位并高亮该卡片 |

**返回** `{ "ok": true, "mode": "bridge" }` — `fallback` 表示降级为新窗口打开。

### cangshu.url

**返回** (string) 仓鼠页面地址

> 💡 **写操作注意**：内部会先取文件 `sha`，遇到 409（并发冲突）自动重试一次。
> 中文备注名走 UTF-8 base64 编码，不会乱码。

---

## 跨应用桥

两个应用同源于 `cool-zimo.github.io`，`localStorage` 天然共享，
所以**登录一次，两边都进**。这组 API 暴露了桥的能力。

### bridge.apps()

**返回**

```json
[
  { "id": "drive",   "name": "GitHub Drive", "icon": "📁" },
  { "id": "cangshu", "name": "仓鼠",         "icon": "🐹" }
]
```

### bridge.current()

**返回** (string) 当前应用 id，如 `"drive"`

### bridge.go(params)

跳转到另一个应用。

| 参数 | 类型 | 说明 |
|---|---|---|
| `params.repo` | string | 携带的仓库上下文 |

### bridge.getToken()

读取共享令牌（任一应用登录成功都会同步写入两边）。

### bridge.otherLoggedIn()

**返回** (boolean) 另一个应用是否已登录

---

## 自省

### api.listActions()

**返回** (string[]) 宿主支持的所有 action 名称

```js
const actions = await call('api.listActions');
if (actions.includes('cangshu.listRepos')) {
    // 支持仓鼠联动
} else {
    // 老版本宿主，降级处理
}
```

建议插件启动时先调用它做**能力探测**，避免调用不存在的 API 报错。

---

## 完整示例

一个最小可用的仓鼠联动插件：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>我的插件</title></head>
<body>
    <div id="list">加载中…</div>
    <script>
        let seq = 0;
        function call(action, data = {}) {
            return new Promise((resolve, reject) => {
                const id = ++seq;
                const handler = (e) => {
                    if (e.data && e.data.type === 'gd-response' && e.data.id === id) {
                        window.removeEventListener('message', handler);
                        clearTimeout(timer);
                        e.data.error ? reject(new Error(e.data.error)) : resolve(e.data.result);
                    }
                };
                const timer = setTimeout(() => {
                    window.removeEventListener('message', handler);
                    reject(new Error('宿主响应超时'));
                }, 15000);
                window.addEventListener('message', handler);
                parent.postMessage({ type: 'gd-api', id, action, data }, '*');
            });
        }

        const esc = (s) => String(s == null ? '' : s)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;');

        (async () => {
            // 先自省，再使用
            const actions = await call('api.listActions');
            if (!actions.includes('cangshu.listRepos')) {
                document.getElementById('list').textContent = '宿主版本过旧';
                return;
            }
            const repos = await call('cangshu.listRepos', { detail: true });
            document.getElementById('list').innerHTML = repos.map(r =>
                `<div>${esc(r.owner)}/${esc(r.alias || r.repo)}</div>`
            ).join('');
        })();
    </script>
</body>
</html>
```

> ⚠️ **安全提醒**：仓库名、备注名都来自用户配置，属于不可信输入。
> 插入 `innerHTML` 前**必须转义**，否则会造成存储型 XSS。

完整可运行版本见
[github_drive_plugins/plugins/cangshu-link.html](https://github.com/Cool-zimo/github_drive_plugins/blob/main/plugins/cangshu-link.html)。
