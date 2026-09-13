---
layout: default
title: 贡献指南
---

# 贡献指南

感谢你对 GitHub Drive 的贡献！本文档说明如何提交改进，以及 CI/CD 的自动审批流程。

## 快速开始

1. Fork [github_drive](https://github.com/Cool-zimo/github_drive)
2. 创建功能分支：`git checkout -b feature/amazing-feature`
3. 提交改动：`git commit -m 'Add amazing feature'`
4. **创建 `config.json` 配置文件**（必须，见下）
5. 推送：`git push origin feature/amazing-feature`
6. 开启 Pull Request

## config.json（必须）

所有 Pull Request 必须在仓库根目录包含 `config.json`，**否则会被自动关闭**。

```json
{
  "author": "your-github-username",
  "name": "My Awesome Feature",
  "branch": "my-feature-branch",
  "description": "Describe what this version improves or adds",
  "version": "1.0.0",
  "contact": "your-email@example.com"
}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `author` | ✅ | 你的 GitHub 用户名 |
| `name` | ✅ | 版本/功能名称 |
| `branch` | ✅ | 分支名（用于生成预览分支） |
| `description` | ⬜ | 改进描述 |
| `version` | ⬜ | 版本号 |
| `contact` | ⬜ | 联系方式 |

## CI/CD 自动流程

提交 PR 后，GitHub Actions 会依次执行：

**1. 验证 config.json**

- 检查文件是否存在
- 校验必填字段（author、name、branch）
- **缺少则自动关闭 PR**

**2. 创建预览分支**

验证通过后自动创建 `preview/{author}/{branch}` 并推送你的代码。

**3. 自动评论**

在 PR 下评论预览分支名、测试方法与访问链接。

## 如何测试他人的改进版本

见 [版本切换](version-switch.html)。

## 代码规范

- 保持代码简洁可读，遵循现有风格
- 关键逻辑加注释，说明**为什么**这么写而不是写了什么
- 改动涉及核心流程时，补充或更新对应测试
- 版本号同步更新 `js/version.js`，并 bump `index.html` 的缓存串 `?v=`
  （只改 JS 不 bump 缓存串的话，用户会一直加载旧文件）

## 问题反馈

遇到问题请在 GitHub 提交 Issue。

---

## 📄 文档站维护（维护者）

文档主站在 [github_drive_documentation](https://github.com/Cool-zimo/github_drive_documentation)，
另有一个镜像站 `Github_Drive-Documentation`（旧地址，保留给已收藏的用户）。

### 自动同步

改完主站文档推送到 main 后，GitHub Actions 会自动同步到镜像站：

- 脚本：`tools/sync_docs.py`
- 工作流：`.github/workflows/sync-docs.yml`

| 触发方式 | 行为 |
|---|---|
| push 到 main（md/assets 变更） | 真正同步 |
| Pull Request | 只跑 `--dry-run` 检查，不写入 |
| 手动 `workflow_dispatch` | 可选 dry_run / rollback |
| 每 6 小时定时 | 兜底，补跑失败或遗漏的同步 |

### 本地也能跑

```bash
export GITHUB_TOKEN=你的 token
python3 tools/sync_docs.py              # 同步
python3 tools/sync_docs.py --dry-run    # 只看差异
python3 tools/sync_docs.py --history    # 看回滚点
python3 tools/sync_docs.py --rollback   # 回滚镜像站
```

### 冲突策略：强制覆盖

镜像站如果被单独改过，同步时**直接覆盖**，不提示冲突。
这是刻意的——主站是唯一真实来源，镜像站不该有独立内容。

### 回滚

每次同步前会把镜像站 `main` 压到 `sync-backup` 分支，作为回滚点。

```bash
python3 tools/sync_docs.py --rollback            # 回到上次同步前
python3 tools/sync_docs.py --rollback <sha>      # 回到指定版本
```

> CI 环境每次都是全新的，本地 `.sync_rollback.json` 不会留存。
> 所以 `--rollback` 不带参数时会自动回落到 `sync-backup` 分支 ——
> 那个分支指向的正是上次同步前的状态，不依赖任何本地文件。

### 需要的 Secret

`SYNC_TOKEN` —— 需要对 `Github_Drive-Documentation` 的 **Contents 写权限**。

Token 轮换后记得同步更新：
**Settings → Secrets and variables → Actions → SYNC_TOKEN**

> 💡 建议用 fine-grained token，只勾 `Github_Drive-Documentation` 一个仓库、
> 只给 Contents 读写，比宽权限的经典 token 安全得多。
