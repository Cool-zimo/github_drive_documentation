# 分享格式规范

GitHub Drive 的分享使用标准格式，方便搜索和发现。

## 仓库命名
```
gd-share-{自定义名称}-{时间戳}
```
- 前缀固定为 `gd-share-`
- 名称为小写字母、数字、连字符
- 时间戳为 base36 编码的 Unix 时间

示例：`gd-share-my-files-abc123`

## 仓库结构
```
gd-share-xxx/
├── index.html      # 分享下载页面（自动生成）
├── README.md       # 说明文档
├── share.json      # 标准元数据（用于搜索验证）
├── status.js       # Pages 就绪探针
└── [用户文件...]   # 分享的实际文件
```

## share.json 格式
```json
{
  "version": "1.0",
  "type": "github-drive-share",
  "name": "分享名称",
  "description": "分享简介",
  "author": "github-username",
  "createdAt": "2026-08-27T14:00:00.000Z",
  "fileCount": 3,
  "files": [
    { "name": "file.pdf", "size": 1048576 }
  ]
}
```

## 搜索发现
发现分享功能通过 GitHub Search API 搜索：
```
q=gd-share in:name
```
然后读取每个仓库的 `share.json`，验证 `type === "github-drive-share"`。

只有符合标准格式的分享才会出现在「发现分享」页面。
