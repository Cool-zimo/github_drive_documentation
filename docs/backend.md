---
layout: default
title: 后端服务
---

# 后端服务

后端是**可选**的本地服务，用来突破浏览器限制（CORS、跨域请求等）。
不使用后端也能正常用 Drive 的全部核心功能；部分插件（如 B 站视频下载器）需要它才能运行。

- 默认地址：`http://localhost:8787`
- 源码仓库：[github-drive-server](https://github.com/Cool-zimo/github-drive-server)

## 安装与运行

### 下载

设置 → **⚙️ 后端服务** → 「⬇️ Download New」，选择对应系统的可执行文件。

### 运行

双击运行即可，服务会在 `http://localhost:8787` 启动，Drive 会自动连接。

## 管理面板

设置 → **⚙️ 后端服务**，可查看：

| 卡片 | 内容 |
|---|---|
| Status | 运行中 / 未连接 |
| Version | 后端版本 |
| Port | 监听端口 |
| Uptime | 已运行时长 |
| Executable Path | 可执行文件位置 |

下方还有**最近 100 条请求日志**，显示时间、状态码、方法、路径。

**可用操作**

- 🔄 Refresh — 刷新状态
- ⚙️ Config/Auth — 配置地址与鉴权
- ⬆️ Check Update — 检查更新
- ⏹️ Shutdown — 关闭服务
- ⬇️ Download New — 下载新版本

## 接口

| 接口 | 说明 |
|---|---|
| `GET /api/status` | 运行状态，返回 `status` / `version` / `port` / `uptime` / `exePath` |
| `GET /health` | 健康检查（旧版兼容，Drive 检测不到 `/api/status` 时回退到它） |
| `GET /api/logs` | 最近请求日志 |

> 后端地址与鉴权 token 保存在浏览器 `localStorage` 的 `gd_backend_config` 中。
> 若修改了端口，需在「Config/Auth」里同步修改。

## 插件如何调用

插件通过 `backendRequest` API 经主应用转发，不用自己处理跨域：

```js
const result = await call('backendRequest', {
    path: '/api/xxx',
    method: 'GET',       // 默认 GET
    body: { ... }        // 可选
});
```

主应用会自动附带 `Content-Type` 与 `X-Auth-Token`（若配置了 token）。

想先确认后端是否在线：

```js
const cfg = await call('getBackendConfig');
console.log(cfg.url || 'http://localhost:8787');
```

详见 [插件 API 参考](plugin-api.md#backendrequestpath-method-body)。

## 安全提示

后端运行在**你自己的电脑**上，默认只监听本地。
除非你明确知道自己在做什么，否则不要把它暴露到公网。
