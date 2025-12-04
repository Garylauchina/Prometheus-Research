# 📝 更新 .env 文件以使用模拟数据

## 操作步骤

### 1. 打开 `.env` 文件
在项目根目录找到 `.env` 文件并用文本编辑器打开。

### 2. 添加或修改 TRADING_MODE 配置

在文件顶部添加以下行：

```env
# 交易数据源选择
# mock: 模拟数据（快速调试，无需网络）
# okx: OKX模拟盘（真实环境测试）
TRADING_MODE=mock
```

### 3. 完整的 .env 示例

```env
# 交易数据源选择
TRADING_MODE=mock

# OKX API 配置（仅在TRADING_MODE=okx时需要）
OKX_API_KEY=your_api_key_here
OKX_API_SECRET=your_api_secret_here
OKX_PASSPHRASE=your_passphrase_here
OKX_SANDBOX=True

# 日志级别
LOG_LEVEL=INFO
```

## 模式说明

### Mock模式（当前选择）✅
- **优点**：
  - ⚡ 快速响应，无网络延迟
  - 🚀 可以快速测试系统逻辑
  - 💰 不受OKX API限流限制
  - 🎲 自动生成合理的价格波动

- **缺点**：
  - 📊 数据是随机生成的，不是真实市场
  - 🔄 无法测试与OKX的实际交互

### OKX模式
- **优点**：
  - 📈 真实市场数据
  - 🔄 真实的API交互
  - 🎯 更接近实盘环境

- **缺点**：
  - ⏱️ 受网络延迟影响
  - 🚦 受OKX API限流限制
  - 🔑 需要配置API密钥

## 切换模式

只需修改 `TRADING_MODE` 即可：

```bash
# 切换到模拟数据
TRADING_MODE=mock

# 切换到OKX模拟盘
TRADING_MODE=okx
```

保存后重启系统即可生效！

