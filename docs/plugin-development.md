# 插件开发指南

## 插件是什么
插件是一个独立的 HTML 文件，在 iframe 沙箱中运行，通过 postMessage 与 GitHub Drive 主应用交互。

## 开发步骤

### 1. 创建 HTML 文件
```html
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>我的插件</title></head>
<body>
  <button onclick="main()">运行</button>
  <script>
    // GitHub Drive 插件 API 封装
    const GD = {
      call(action, data = {}) {
        return new Promise((resolve, reject) => {
          const id = Date.now() + Math.random();
          const handler = (e) => {
            if (e.data.type === 'gd-response' && e.data.id === id) {
              window.removeEventListener('message', handler);
              if (e.data.error) reject(new Error(e.data.error));
              else resolve(e.data.result);
            }
          };
          window.addEventListener('message', handler);
          window.parent.postMessage({ type: 'gd-api', id, action, data }, '*');
        });
      },
      listFiles(path) { return this.call('listFiles', { path }); },
      downloadFile(path) { return this.call('downloadFile', { path }); },
      uploadFile(name, content, path) { return this.call('uploadFile', { name, content, path }); },
      showToast(msg, type) { return this.call('showToast', { message: msg, type }); },
      getCurrentPath() { return this.call('getCurrentPath'); },
      getToken() { return this.call('getToken'); }
    };

    async function main() {
      const files = await GD.listFiles('/drive_home');
      GD.showToast('找到 ' + files.length + ' 个文件', 'success');
    }
  </script>
</body>
</html>
```

### 2. 提交到插件市场
1. Fork [github_drive_plugins](https://github.com/Cool-zimo/github_drive_plugins)
2. 将插件 HTML 放入 `plugins/` 目录
3. 在 `plugins.json` 中添加插件元数据：
```json
{
  "id": "my-plugin",
  "name": "我的插件",
  "description": "插件功能描述",
  "author": "你的用户名",
  "version": "1.0.0",
  "icon": "🚀",
  "file": "plugins/my-plugin.html"
}
```
4. 提交 Pull Request

## 注意事项
- 插件在 iframe 中运行，无法直接访问主应用的 DOM
- 所有文件操作通过 `GD` API 完成
- 大文件操作可能较慢，建议显示加载状态
- 插件 HTML 大小建议控制在 100KB 以内
