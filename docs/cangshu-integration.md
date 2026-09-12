# 仓鼠联动

「仓鼠」是配套的 GitHub 仓库管理面板，与 GitHub Drive 深度互通。

- 仓鼠：<https://cool-zimo.github.io/cangshu/>
- GitHub Drive：<https://cool-zimo.github.io/github_drive/>

## 为什么能联动

两个应用**同源**：

```
https://cool-zimo.github.io/github_drive/
https://cool-zimo.github.io/cangshu/
```

同 protocol、同 host、同 port → **`localStorage` 天然共享**。

所以真正的联动不是加个跳转链接，而是 **登录一次，两边都进**。

## 登录互认

| 你在 | 检测到 | 表现 |
|---|---|---|
| 仓鼠 | Drive 已登录 | 登录页出现「沿用该账号，免输入进入」 |
| Drive | 仓鼠已登录 | 同上，反向 |

点一下直接进，不用再去翻令牌粘贴。

任意一边登录成功，令牌会**同步写入两边的存储位置**，
对面打开就是已登录状态。

## 双向切换

- 仓鼠顶栏 → 📁 GitHub Drive
- Drive 侧边栏底部 → 🐹 仓鼠

跳转会带上当前仓库上下文（`?repo=owner/repo`），
过去后自动定位并高亮对应卡片。

## 数据存储

仓鼠把管理清单存在**私有仓库 `cangshu-config/cangshu.json`**：

```json
{
  "version": 1,
  "updatedAt": "2026-09-12T00:00:00Z",
  "managed": [
    {
      "owner": "Cool-zimo",
      "repo": "github_drive",
      "alias": "",
      "note": "",
      "addedAt": "2026-09-12T00:00:00Z"
    }
  ],
  "settings": {
    "configRepo": "cangshu-config",
    "theme": "auto"
  }
}
```

**为什么存 GitHub 而不是 localStorage**：

- 换设备、换浏览器照样读得到
- 跨应用共享不依赖同源
- GitHub Drive 的插件也能直接读写（见下文 API）

写操作会先取文件 `sha`，遇到 409（并发冲突）自动重试一次。

## 安全

- 令牌只存在**你自己的浏览器**，代码里没有任何外发请求
- 配置仓库是**私有**的
- 建议令牌**只给 `cangshu-config` 这一个仓库**的 Contents 读写权限

## 插件可用的 API

GitHub Drive 的插件可以直接读写仓鼠配置，详见
[插件 API 参考 · 仓鼠联动](plugin-api.md#仓鼠联动)。

简单的能力探测：

```js
const actions = await call('api.listActions');
if (actions.includes('cangshu.listRepos')) {
    const repos = await call('cangshu.listRepos', { detail: true });
}
```

## 配套扩展

插件市场里的「🐹 仓鼠联动」是完整示例，源码见
[cangshu-link.html](https://github.com/Cool-zimo/github_drive_plugins/blob/main/plugins/cangshu-link.html)。
