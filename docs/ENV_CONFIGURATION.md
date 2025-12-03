# Prometheus v4.0 环境配置指南

## 📋 **快速开始**

### 1. 创建 `.env` 文件

在项目根目录创建 `.env` 文件：

```bash
# 复制模板文件
cp env.example .env
```

### 2. 填写 API 配置

编辑 `.env` 文件，填入您的 OKX API 密钥：

```bash
# OKX API 配置
OKX_API_KEY=your_api_key_here
OKX_API_SECRET=your_api_secret_here
OKX_PASSPHRASE=your_passphrase_here

# 交易模式 (True=模拟盘, False=实盘)
OKX_SANDBOX=True

# 日志级别 (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
```

### 3. 验证配置

运行以下命令验证配置是否正确：

```python
python -c "from config.config import validate_config; validate_config(); print('✅ 配置验证通过！')"
```

---

## 🔐 **安全注意事项**

### ✅ **推荐做法**

1. **永远不要提交 `.env` 文件到 Git**
   - `.env` 已在 `.gitignore` 中
   - 确保敏感信息不会泄露

2. **使用模拟盘测试**
   - 设置 `OKX_SANDBOX=True`
   - 在模拟环境中充分测试

3. **定期轮换 API 密钥**
   - OKX 支持创建多个 API 密钥
   - 定期更新提高安全性

### ❌ **禁止行为**

1. **不要**在代码中硬编码 API 密钥
2. **不要**将 `.env` 文件分享给他人
3. **不要**在公共仓库中提交配置文件

---

## 🔧 **配置说明**

### OKX API 配置

| 配置项 | 说明 | 必填 |
|--------|------|------|
| `OKX_API_KEY` | OKX API 密钥 | ✅ |
| `OKX_API_SECRET` | OKX API 秘密 | ✅ |
| `OKX_PASSPHRASE` | OKX API 口令 | ✅ |

**获取方式**：
1. 登录 [OKX 官网](https://www.okx.com)
2. 进入"账户" -> "API 管理"
3. 选择"模拟交易" -> "创建 API"
4. 保存 API Key、Secret 和 Passphrase

### 系统配置

| 配置项 | 说明 | 默认值 | 可选值 |
|--------|------|--------|--------|
| `OKX_SANDBOX` | 交易模式 | `True` | `True`/`False` |
| `LOG_LEVEL` | 日志级别 | `INFO` | `DEBUG`/`INFO`/`WARNING`/`ERROR` |

---

## 🚀 **从旧配置迁移**

如果您之前使用的是 `config/okx_config.py`，请按以下步骤迁移：

### 步骤 1：创建 `.env` 文件

```bash
# 从 okx_config.py 提取信息
API_KEY=$(grep -oP "(?<='api_key': ').*(?=')" config/okx_config.py)
API_SECRET=$(grep -oP "(?<='api_secret': ').*(?=')" config/okx_config.py)
PASSPHRASE=$(grep -oP "(?<='passphrase': ').*(?=')" config/okx_config.py)

# 创建 .env 文件
cat > .env << EOF
OKX_API_KEY=$API_KEY
OKX_API_SECRET=$API_SECRET
OKX_PASSPHRASE=$PASSPHRASE
OKX_SANDBOX=True
LOG_LEVEL=INFO
EOF
```

### 步骤 2：删除旧配置文件

```bash
# 备份旧配置（可选）
mv config/okx_config.py config/okx_config.py.backup

# 确认 .env 正确后，可以删除备份
# rm config/okx_config.py.backup
```

### 步骤 3：更新导入

**旧代码**：
```python
from config.okx_config import OKX_PAPER_TRADING
```

**新代码**：
```python
from config.config import OKX_PAPER_TRADING, validate_config
validate_config()  # 验证配置
```

---

## 🐛 **常见问题**

### Q1: 提示"缺少必要的环境变量"

**A**: 检查 `.env` 文件是否存在，且包含所有必填配置。

### Q2: API 连接失败

**A**: 
1. 确认 API 密钥正确
2. 确认已启用"交易"权限
3. 确认 `OKX_SANDBOX=True`（使用模拟盘）

### Q3: Windows 控制台编码问题

**A**: 已在 v4.0 中修复，使用了编码错误处理。如仍有问题，设置环境变量：
```powershell
$env:PYTHONIOENCODING="utf-8"
```

---

## 📚 **参考资料**

- [OKX API 文档](https://www.okx.com/docs-v5/zh/)
- [python-dotenv 文档](https://github.com/theskumar/python-dotenv)
- [12-Factor App: 配置](https://12factor.net/zh_cn/config)

---

**上次更新**: 2025-12-04  
**文档版本**: v4.0

