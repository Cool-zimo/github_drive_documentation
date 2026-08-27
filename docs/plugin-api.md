# 插件 API 参考

插件通过 `GD` 对象调用 API，所有方法返回 Promise。

## 文件操作

### listFiles(path)
列出指定路径的文件和文件夹。

**参数**
- `path` (string): 虚拟路径，如 `/drive_home` 或 `/drive_home/文档`

**返回**
```json
[
  { "name": "file.txt", "path": "/drive_home/file.txt", "isFolder": false, "size": 1024 },
  { "name": "文件夹", "path": "/drive_home/文件夹", "isFolder": true, "size": 0 }
]
```

### downloadFile(path)
下载文件内容（文本格式）。

**参数**
- `path` (string): 文件虚拟路径

**返回** (string): 文件文本内容

### uploadFile(name, content, path)
上传文件到 Drive。

**参数**
- `name` (string): 文件名
- `content` (string): 文件内容（文本）
- `path` (string): 目标目录路径，如 `/drive_home`

**返回**
```json
{ "success": true }
```

## 界面交互

### showToast(message, type)
显示提示消息。

**参数**
- `message` (string): 消息内容
- `type` (string): `info` | `success` | `error`

### getCurrentPath()
获取用户当前浏览的目录路径。

**返回** (string): 当前路径，如 `/drive_home/文档`

## 高级

### getToken()
获取用户的 GitHub Personal Access Token。插件可用此 Token 直接调用 GitHub API。

**返回** (string): GitHub Token

> ⚠️ 注意：请谨慎使用 Token，不要上传到第三方服务器。

## 通信协议

底层通过 postMessage 通信：

**请求**（插件 → 主应用）
```json
{ "type": "gd-api", "id": 123456, "action": "listFiles", "data": { "path": "/drive_home" } }
```

**响应**（主应用 → 插件）
```json
{ "type": "gd-response", "id": 123456, "result": [...] }
```

错误响应：
```json
{ "type": "gd-response", "id": 123456, "error": "错误信息" }
```
