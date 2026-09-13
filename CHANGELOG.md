---
layout: default
title: 更新日志
---

# 更新日志

## v0.0.37

- **插件统一全屏显示**：不再区分游戏/工具，所有插件都在全屏层运行
  - 顶部工具条显示图标 + 名称 + 版本号，支持 ESC 关闭
  - 修了多开时的生命周期 bug：此前弹窗类插件共用单个 `_pluginMessageHandler`
    变量，后开的会覆盖先开的，导致先开的插件再也收不到宿主响应
- 插件 `modalId` 加随机后缀（同毫秒连开两个会撞 id）

## v0.0.36

- **扩展 API：仓鼠联动**
  - 新增 `js/cangshu-link.js`，封装对仓鼠配置仓库的读写
  - `cangshu.*` 9 个 API：status / getConfig / listRepos / addRepo /
    removeRepo / hasRepo / setAlias / ensureConfig / open
  - `bridge.*` 5 个 API：apps / current / go / getToken / otherLoggedIn
  - `api.listActions`：插件可自省宿主能力
- 发布示例扩展「🐹 仓鼠联动」到插件市场

## v0.0.35

- **品牌图标**：替掉 emoji（各浏览器字形/配色不一致，且无法跟随暗色主题）
  - 两套专用 PNG 图标，13 种尺寸 + favicon + apple-touch-icon
  - 相关仓库 README 也挂上品牌图
- **分享进度弹窗**：原先 toast 刷屏（一次分享弹 5~10 条），
  改为进度条 + 5 步流程清单，每步三态
- **右键菜单二级分组**：11 项平铺改为分层，
  「更多操作 ▸」收纳重命名/移动/复制/编辑/标签/版本历史
- 新增统一图标集 `icons.js`（58 个 SVG，currentColor 跟随主题）
- 修菜单 bug：`show()` 内部清理误触发 `onClose`，导致菜单关不掉

## v0.0.34

- GitHub Drive 与仓鼠联动：同源 `localStorage` 共享，登录一次两边都进
  - 令牌互认 + 双向常驻切换按钮

## v0.0.33

- 修复分享页一直转圈：生成页内联脚本有语法错误（嵌套单引号导致
  模板字符串解析失败），整段 script 不执行
- 分享列表改为**生成期静态渲染**，脚本全挂也能下载
- 修标题显示明文 `<span>` 标签的问题

## v0.0.32

- 修复分享二进制文件（mp3 等）时的 404
  - 根因：合并分片后没带 `owner/repo`，请求打到
    `/repos/undefined/undefined/...`
  - 文本文件走 `content` 分支不受影响，所以只有 mp3 中招

## v20260827

- 修复二进制文件上传损坏（小分片改用 base64 二进制上传）
- 修复大文件下载（Git Data API 回退）
- 新增分享广场（标准 `gd-share-` 命名 + `share.json` 元数据 + 搜索发现）
- 新增插件广场（插件仓库 + postMessage API + 安装运行沙箱）
- 新增网格/列表视图切换
- 新增上传文件夹（保持目录结构）
- 新增批量操作（Ctrl 多选：删除/移动/复制/收藏/下载/分享）
- 新增拖拽移动（到文件夹/面包屑）
- 修复文件夹图标、删除文件夹、收藏文件夹
- 新增面包屑横向滚动
- 新增定时清理 Git 历史（GitHub Actions）
- 修复 CORS、缓存、移动路径重复等多个 bug
