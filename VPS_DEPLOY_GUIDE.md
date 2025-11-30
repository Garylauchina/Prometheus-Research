# VPS部署指南

本文档提供在VPS上部署Prometheus交易系统的详细步骤，特别包含了解决OKX包导入问题的方法。

## 1. 准备工作

### 1.1 系统要求

- 操作系统：Ubuntu 20.04+ 或 CentOS 8+
- Python版本：3.8-3.11
- 内存：至少2GB RAM
- 存储空间：至少10GB

### 1.2 更新系统

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS
sudo yum update -y
```

### 1.3 安装Python和依赖

```bash
# Ubuntu/Debian
sudo apt install -y python3 python3-pip python3-venv git

# CentOS
sudo yum install -y python3 python3-pip git
```

## 2. 克隆项目

```bash
git clone https://your-repository-url/prometheus-v30.git
cd prometheus-v30
```

## 3. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或在Windows上: venv\Scripts\activate
```

## 4. 安装依赖

### 4. 安装依赖

使用以下命令安装项目依赖：

```bash
pip install -r requirements.txt
# 确保安装正确的OKX SDK库
pip install python-okx>=0.4.0
```

> **重要说明**：项目需要使用正确的OKX SDK库名称python-okx，最新稳定版本为0.4.0。requirements.txt中已指定此依赖。


如果需要手动安装特定版本，可以使用：

```bash
pip install python-okx>=0.4.0
```

## 5. 配置项目

### 5.1 设置配置文件

根据您的交易需求修改配置文件：

```bash
cp config_virtual.py config.py
# 编辑config.py设置您的API密钥和交易参数
nano config.py
```

### 5.2 API密钥设置

确保您的OKX API密钥具有适当的权限，并在配置文件中正确设置：

```python
API_KEY = "your_api_key"
API_SECRET = "your_api_secret"
API_PASSPHRASE = "your_api_passphrase"
FLAG = "1"  # 模拟盘环境，"0"为实盘环境
```

## 6. 验证安装

### 6.1 运行兼容性测试

在启动交易系统之前，建议先运行测试脚本验证环境配置是否正确：

```bash
# 运行兼容性测试脚本
python test_okx_v1_compatibility.py

# 如果遇到问题，还可以运行详细的兼容性测试
python test_full_compatibility.py
```

如果测试通过，说明环境配置正确，可以继续。

### 6.2 运行虚拟交易

```bash
python run_virtual_trading.py
```

## 7. 设置为系统服务（推荐）

为确保交易系统在重启后自动运行，建议将其设置为系统服务。

### 7.1 创建服务文件

```bash
sudo nano /etc/systemd/system/prometheus.service
```

### 7.2 添加服务配置

```
[Unit]
Description=Prometheus Trading Bot
After=network.target

[Service]
User=root
WorkingDirectory=/root/prometheus-v30
ExecStart=/root/prometheus-v30/venv/bin/python run_virtual_trading.py
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=prometheus-bot

[Install]
WantedBy=multi-user.target
```

### 7.3 启用并启动服务

```bash
sudo systemctl daemon-reload
sudo systemctl enable prometheus.service
sudo systemctl start prometheus.service
```

### 7.4 查看服务状态

```bash
sudo systemctl status prometheus.service
```

## 8. 日志监控

### 8.1 查看系统日志

```bash
sudo journalctl -u prometheus.service -f
```

### 8.2 设置监控脚本

使用项目中的监控脚本定期检查系统状态：

```bash
chmod +x monitor.sh
./monitor.sh
```

## 9. 故障排除

### 9.1 常见错误及解决方案

#### API连接错误

如果遇到API连接问题：
- 检查API密钥和密码是否正确
- 验证IP白名单设置（如果已启用）
- 检查网络连接

#### 版本兼容性问题

如果遇到与OKX包版本相关的问题，请确保：
1. 使用`okx>=1.0.9`版本
2. 检查兼容性模块的日志输出，它会自动尝试多种导入方式
3. 如仍有问题，系统会自动切换到后备方案，确保基本功能可用

#### 导入错误解决

如果遇到类似`AttributeError: module 'okx.MarketData' has no attribute 'MarketAPI'`的错误：
1. 确认安装了正确版本的OKX包
2. 兼容性模块已经实现了智能后备方案，应该能够自动解决这个问题
3. 检查日志以获取详细的导入尝试结果

#### 测试失败

如果测试脚本失败，请查看详细的错误日志，并按照以下步骤操作：
1. 确认Python环境和依赖版本
2. 尝试重新安装OKX包：`pip uninstall okx && pip install okx>=1.0.9`
3. 检查`adapters/okx_compat.py`文件是否正确更新

### 9.2 查看详细日志

设置日志级别为DEBUG以获取更多信息：

```bash
export LOG_LEVEL=DEBUG
python run_virtual_trading.py
```

## 10. 更新系统

### 10.1 拉取最新代码

```bash
git pull
```

### 10.2 重启服务

```bash
sudo systemctl restart prometheus.service
```

## 11. 安全最佳实践

- 定期更新系统和依赖
- 使用强密码和API密钥
- 启用SSH密钥认证，禁用密码登录
- 限制防火墙规则，只开放必要的端口
- 定期备份配置和数据

## 12. 资源监控

设置定期监控系统资源使用情况：

```bash
# 安装监控工具
sudo apt install -y htop glances

# 或使用psutil（已在requirements.txt中）
python -c "import psutil; print(f'CPU: {psutil.cpu_percent()}%, 内存: {psutil.virtual_memory().percent}%')"
```

---

按照以上步骤操作，您应该能够在VPS上成功部署和运行Prometheus交易系统，并且解决OKX包导入问题。如果您有任何问题，请参考项目文档或提交issue。