---
layout: default
title: 版本切换
---

# 版本切换

GitHub Drive 支持加载他人改进的版本，通过**预览分支**机制实现。

## 版本类型

| 类型 | 分支 | 说明 |
|---|---|---|
| 官方版本 | `main` | 通过 GitHub Pages 部署 |
| 预览版本 | `preview/{author}/{branch}` | 由 CI/CD 在 PR 时自动创建 |

## 如何切换

### 方法一：通过设置页

1. 点击左下角 **设置**
2. 选择 **🔀 版本切换**
3. 在列表中点击可用分支，或手动输入分支名
4. 点击 **切换分支**
5. 页面自动刷新，加载新版本

### 方法二：URL 参数

```
https://cool-zimo.github.io/github_drive/?branch=preview/username/feature-name
```

### 恢复官方版本

- 设置 → 版本切换 → **🏠 恢复官方版**
- 或控制台执行：`localStorage.removeItem('gd_custom_branch')`

## 分支命名格式

```
preview/{author}/{sanitized-branch-name}
```

示例：`preview/cool-zimo/dark-mode`

版本切换页面会自动列出所有 `preview/` 开头的分支。

## 技术实现

检测到自定义分支时：

1. 从 `localStorage` 读取 `gd_custom_branch`
2. 或从 URL 参数 `?branch=` 读取
3. 动态从 `raw.githubusercontent.com/Cool-zimo/github_drive/{branch}/` 加载 CSS 和 JS

## 注意事项

- `raw.githubusercontent.com` 在国内可能较慢
- 预览分支**不会**触发 GitHub Pages 部署，资源直接从 GitHub 加载
- 分支不存在时页面会加载失败
- 切换分支**不影响**你的文件（文件存在 GitHub 仓库里，与应用版本无关），
  本地数据（token、配置等）也保持不变

## 常见问题

**Q: 切换后页面空白？**
A: 预览分支不存在或代码有错误。恢复官方版本，或检查分支名。

**Q: 切换后我的文件还在吗？**
A: 在。文件存在 GitHub 仓库中，与应用版本无关。

**Q: 预览版本安全吗？**
A: 预览版本是第三方提交的未验证代码，请谨慎使用。官方版本始终在 `main` 分支。

**Q: 怎么知道有哪些预览分支可用？**
A: 版本切换页面会自动列出，也可访问仓库 Branches 页面查看。

想提交自己的改进？见 [贡献指南](contributing.html)。
