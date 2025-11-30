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

### 4.1 安装特定版本的OKX包

重要：必须安装正确版本的OKX包以确保兼容性：

```bash
pip install okx==0.4.0
```

### 4.2 安装其他依赖

```bash
pip install -r requirements.txt
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

```bash
python test_compatibility_fix.py
```

如果测试通过，输出将显示：
```
🎉 所有测试都通过了！兼容性修复有效。
```

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

#### 导入错误

如果遇到OKX相关的导入错误，请确保：
- 已安装okx==0.4.0版本
- 虚拟环境已正确激活
- 兼容性模块`adapters/okx_compat.py`存在

#### API连接错误

如果遇到API连接问题：
- 检查API密钥和密码是否正确
- 验证IP白名单设置（如果已启用）
- 检查网络连接

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