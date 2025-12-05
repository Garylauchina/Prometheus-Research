# Cursor 字体大小完整调整指南

## 🎯 AI 交互界面字体调整

### 方法1: 通过设置菜单（推荐）

1. **打开设置**
   - 按 `Cmd+,` 或点击左下角齿轮图标

2. **搜索 AI Chat 相关设置**
   在搜索框输入以下任一关键词：
   - `chat font`
   - `chat editor font size`
   - `composer font`

3. **调整以下设置**
   - `Chat: Editor Font Size` → 改为 **16** 或 **18**
   - `Chat: Font Size` → 改为 **16** 或 **18**
   - `Composer: Font Size` → 改为 **16** 或 **18**

### 方法2: 编辑用户设置JSON（快速）

1. **打开命令面板**
   - 按 `Cmd+Shift+P`

2. **输入并选择**
   ```
   Preferences: Open User Settings (JSON)
   ```

3. **添加以下配置**
   ```json
   {
     "chat.editor.fontSize": 18,
     "chat.fontSize": 18,
     "composer.fontSize": 18,
     "aichat.fontSize": 18,
     "cursor.chat.fontSize": 18
   }
   ```

### 方法3: 使用缩放快捷键（临时）

在 AI Chat 面板激活时：
- **放大**: `Cmd +`
- **缩小**: `Cmd -`
- **重置**: `Cmd 0`

---

## 📊 完整字体大小参考

### 推荐配置（大字体）

```json
{
  // ========== 代码编辑器 ==========
  "editor.fontSize": 18,
  "editor.lineHeight": 26,
  
  // ========== AI Chat/对话 ==========
  "chat.editor.fontSize": 18,
  "chat.fontSize": 18,
  "composer.fontSize": 18,
  "aichat.fontSize": 18,
  
  // ========== 终端 ==========
  "terminal.integrated.fontSize": 16,
  
  // ========== 调试/输出 ==========
  "debug.console.fontSize": 16,
  
  // ========== Markdown ==========
  "markdown.preview.fontSize": 18,
  
  // ========== 整体缩放 ==========
  "window.zoomLevel": 1
}
```

### 字体大小对照表

| 大小 | 适用场景 | 效果 |
|------|---------|------|
| 12 | 默认 | 标准，可能偏小 |
| 14 | 舒适 | 适合长时间编码 |
| 16 | 大字 | 清晰易读 |
| 18 | 超大 | 演示/展示用 |
| 20+ | 巨大 | 视力需求/演讲 |

---

## 🔧 故障排除

### 问题1: 设置后没有效果

**解决方案**:
1. 完全关闭并重启 Cursor（不是重新加载窗口）
2. 确保修改的是**用户设置**而非工作区设置

### 问题2: 找不到 Chat 字体设置

**原因**: Cursor 版本可能不同

**解决方案**: 尝试以下所有配置项
```json
{
  "chat.editor.fontSize": 18,
  "chat.fontSize": 18,
  "composer.fontSize": 18,
  "aichat.fontSize": 18,
  "cursor.chat.fontSize": 18,
  "cursor.composer.fontSize": 18,
  "aiChat.fontSize": 18
}
```

### 问题3: 只有部分界面字体变大

**解决方案**: 使用整体缩放
```json
{
  "window.zoomLevel": 1  // 或 1.5, 2
}
```

---

## ⚡ 快速操作步骤

### 立即调整 AI Chat 字体（60秒）

1. **按 `Cmd+Shift+P`**
2. **输入**: `user settings json`
3. **按回车**打开设置文件
4. **在文件中添加**:
   ```json
   "chat.editor.fontSize": 18,
   "chat.fontSize": 18,
   ```
5. **保存** (`Cmd+S`)
6. **重启** Cursor

---

## 💡 额外提示

### 提高整体可读性

除了字体大小，还可以调整：

```json
{
  // 字体粗细
  "editor.fontWeight": "500",
  
  // 字体家族（使用更清晰的字体）
  "editor.fontFamily": "Monaco, 'Courier New', monospace",
  
  // 行间距
  "editor.lineHeight": 1.6,
  
  // 字符间距
  "editor.letterSpacing": 0.5,
  
  // 主题（深色主题可能更护眼）
  "workbench.colorTheme": "Dark+"
}
```

---

## 🎯 推荐配置模板

### 配置A: 清晰舒适型
```json
{
  "editor.fontSize": 16,
  "chat.fontSize": 16,
  "terminal.integrated.fontSize": 14,
  "window.zoomLevel": 0
}
```

### 配置B: 大字型
```json
{
  "editor.fontSize": 18,
  "chat.fontSize": 18,
  "terminal.integrated.fontSize": 16,
  "window.zoomLevel": 0.5
}
```

### 配置C: 演示型
```json
{
  "editor.fontSize": 20,
  "chat.fontSize": 20,
  "terminal.integrated.fontSize": 18,
  "window.zoomLevel": 1
}
```

---

**最后更新**: 2025-12-05

