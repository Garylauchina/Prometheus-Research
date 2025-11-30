# Prometheus v3.0 部署指南

![Deployment](https://img.shields.io/badge/deployment-ready-green)
![Docker](https://img.shields.io/badge/docker-supported-blue)
![Security](https://img.shields.io/badge/security-enhanced-orange)

## 📑 目录

- [📋 部署概述](#-部署概述)
- [🔧 系统要求](#-系统要求)
- [💻 环境准备](#-环境准备)
  - [系统更新](#系统更新)
  - [Python环境配置](#python环境配置)
- [📁 代码部署](#-代码部署)
  - [克隆项目](#克隆项目)
  - [虚拟环境管理](#虚拟环境管理)
  - [依赖安装](#依赖安装)
- [⚙️ 配置设置](#-配置设置)
  - [配置文件说明](#配置文件说明)
  - [环境变量配置](#环境变量配置)
  - [安全凭证管理](#安全凭证管理)
- [🧪 部署前测试](#-部署前测试)
- [🚀 生产环境部署](#-生产环境部署)
  - [手动运行模式](#手动运行模式)
  - [Systemd服务配置](#systemd服务配置)
  - [服务管理命令](#服务管理命令)
- [🐳 Docker部署](#-docker部署)
  - [基础Docker部署](#基础docker部署)
  - [Docker Compose配置](#docker-compose配置)
  - [健康检查设置](#健康检查设置)
- [📊 监控与维护](#-监控与维护)
  - [日志管理](#日志管理)
  - [资源监控](#资源监控)
  - [系统备份](#系统备份)
- [🔄 项目更新](#-项目更新)
- [🛡️ 安全最佳实践](#️-安全最佳实践)
  - [API安全](#api安全)
  - [服务器安全](#服务器安全)
  - [数据安全](#数据安全)
- [🔧 故障排除](#-故障排除)
- [🌐 多环境部署策略](#-多环境部署策略)
  - [开发环境](#开发环境)
  - [测试环境](#测试环境)
  - [生产环境](#生产环境)

## 📋 部署概述

本文档提供了Prometheus v30系统的完整部署指南，包括多种部署方式、配置选项和最佳实践。系统支持传统服务器部署和Docker容器化部署，可适应不同的环境需求。

## 🔧 系统要求

### 硬件要求

- **CPU**：最低 2 核，推荐 4 核（支持并发处理）
- **内存**：最低 4GB RAM，推荐 8GB RAM（运行多个Agent更流畅）
- **存储**：最低 20GB SSD 存储（推荐，确保I/O性能）
- **网络**：稳定的互联网连接，低延迟，建议配置静态IP

### 软件要求

- **操作系统**：
  - Ubuntu 20.04 LTS / 22.04 LTS（推荐）
  - Debian 11+ / CentOS Stream 8+
  - 支持Windows Server 2019+（开发环境）
- **Python**：Python 3.10+（推荐 3.11，最新稳定版）
- **Docker**：Docker 20.10+（容器化部署可选）
- **Git**：用于代码管理

## 💻 环境准备

### 系统更新

#### Ubuntu/Debian

```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 安装必要的系统依赖
sudo apt install -y git python3-pip python3-venv build-essential curl wget

# 安装额外的监控和网络工具
sudo apt install -y htop iotop nload net-tools
```

#### CentOS/RHEL

```bash
# 更新系统包
sudo yum update -y

# 安装EPEL存储库
sudo yum install -y epel-release

# 安装必要的系统依赖
sudo yum install -y git python3-pip python3-virtualenv gcc gcc-c++ make curl wget
```

### Python环境配置

```bash
# 确保安装了正确版本的Python
python3 --version

# 升级pip
sudo pip3 install --upgrade pip setuptools wheel

# 验证pip版本
pip3 --version

# 安装虚拟环境工具（如果需要）
sudo pip3 install virtualenv
```
```

## 📁 代码部署

### 克隆项目

```bash
# 克隆仓库到本地
git clone https://github.com/yourusername/prometheus-v30.git
cd prometheus-v30

# 切换到特定版本（可选）
git checkout v3.0
```

### 虚拟环境管理

```bash
# 创建Python虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Linux/Mac
source venv/bin/activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

### 依赖安装

```bash
# 确保在虚拟环境中
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt

# 验证安装
pip list
```

## ⚙️ 配置设置

### 配置文件说明

项目支持多种配置文件，根据运行环境区分：

```bash
# 复制配置文件示例
cp config_virtual.py config_production.py
```

主要配置文件说明：
- `config_virtual.py`：虚拟交易环境配置
- `config_production.py`：生产环境配置（实盘）

### 环境变量配置

复制环境变量示例文件并编辑：

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑.env文件
nano .env
```

### 安全凭证管理

创建`.env`文件存储API凭证（确保不将此文件提交到版本控制）：

```bash
# 创建.env文件
cat > .env << EOF
# OKX API凭证
OKX_API_KEY=your_api_key
OKX_SECRET_KEY=your_api_secret
OKX_PASSPHRASE=your_passphrase
OKX_USE_TESTNET=false

# 系统配置
LOG_LEVEL=INFO
MAX_RETRY_ATTEMPTS=3
RETRY_DELAY=5

# 性能配置
API_CALL_LIMIT_PER_MINUTE=600
CACHE_TTL_SECONDS=10
EOF

# 设置文件权限，确保安全性
chmod 600 .env

# 确保.env文件已添加到.gitignore
cat .gitignore | grep -q '.env' || echo '.env' >> .gitignore
```
```

## 🧪 部署前测试

在正式部署前，建议运行以下测试确保系统正常工作：

```bash
# 激活虚拟环境（如果未激活）
source venv/bin/activate

# 运行OKX API兼容性测试
python test_okx_v1_compatibility.py

# 运行完整系统兼容性测试
python test_full_compatibility.py

# 进行性能测试（可选，建议在生产环境部署前运行）
python test_performance.py --duration 300
```

### 测试问题排查

如果测试失败，请检查以下方面：

1. API凭证是否正确配置
2. IP是否在OKX交易所白名单中
3. 网络连接是否正常
4. Python环境依赖是否完整安装
5. 检查日志文件获取详细错误信息

```bash
# 查看测试日志
cat logs/test_*.log
```

## 🚀 生产环境部署

### 手动运行模式

在开发、测试或临时部署阶段，可以手动运行系统：

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行系统（虚拟盘模式）
python run_virtual_trading.py --duration 86400

# 运行系统（自定义配置）
python run_virtual_trading.py --config config_production.py --log-level INFO
```

### Systemd服务配置

为了实现自动启动和故障恢复，推荐配置systemd服务：

```bash
# 创建服务文件
sudo nano /etc/systemd/system/prometheus.service
```

将以下内容粘贴到服务文件中，并根据实际情况修改路径和用户名：

```ini
[Unit]
Description=Prometheus Trading Bot v3.0
After=network.target
Wants=network-online.target

[Service]
# 用户和路径设置
User=your_username
WorkingDirectory=/path/to/prometheus-v30
Environment="PATH=/path/to/prometheus-v30/venv/bin"
EnvironmentFile=/path/to/prometheus-v30/.env

# 执行命令
ExecStart=/path/to/prometheus-v30/venv/bin/python run_virtual_trading.py --config config_production.py

# 重启策略
Restart=on-failure
RestartSec=10
StartLimitInterval=60
StartLimitBurst=5

# 资源限制
LimitNOFILE=4096
LimitNPROC=2048
CPUQuota=80%
MemoryLimit=6G

# 日志配置
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=prometheus

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true
RestrictAddressFamilies=AF_INET AF_INET6

[Install]
WantedBy=multi-user.target
```

### 服务管理命令

```bash
# 重新加载systemd配置
sudo systemctl daemon-reload

# 启用服务（开机自启）
sudo systemctl enable prometheus.service

# 启动服务
sudo systemctl start prometheus.service

# 查看服务状态
sudo systemctl status prometheus.service

# 查看详细服务日志
sudo journalctl -u prometheus.service -f -n 100

# 停止服务
sudo systemctl stop prometheus.service

# 临时禁用服务（下次开机不会自动启动）
sudo systemctl disable prometheus.service

# 查看服务启动时间和资源使用情况
sudo systemctl status prometheus.service | grep -E 'Active|Memory|CPU'
```
```

## 📊 监控与维护

### 日志管理

系统提供多层次的日志管理机制：

```bash
# 查看systemd服务日志
sudo journalctl -u prometheus.service -n 100 -f

# 查看应用程序日志（文件日志）
tail -f logs/prometheus.log

# 查看交易日志
tail -f logs/trading_logs/trading_*.log

# 查看错误日志
grep -i error logs/prometheus.log
```

配置日志轮转以防止磁盘空间耗尽：

```bash
# 创建日志轮转配置
sudo nano /etc/logrotate.d/prometheus
```

添加以下内容：

```
/path/to/prometheus-v30/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 your_username your_username
    size 100M
    postrotate
        systemctl reload prometheus.service > /dev/null 2>/dev/null || true
    endscript
}
```

### 资源监控

使用内置的监控脚本：

```bash
# 运行监控脚本（VPS模式）
./monitor.sh

# 运行监控脚本（Docker模式）
./monitor.sh --docker

# 生成详细报告
./monitor.sh --report > monitoring_report_$(date +%Y%m%d).txt

# 定期检查（添加到crontab）
0 * * * * /path/to/prometheus-v30/monitor.sh --report >> /path/to/prometheus-v30/reports/daily_$(date +\%Y\%m\%d).log
```

### 系统备份

定期备份关键配置和数据：

```bash
# 创建备份脚本
nano backup.sh
```

备份脚本内容：

```bash
#!/bin/bash

BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="prometheus_backup_$DATE.tar.gz"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 创建备份
tar -czf $BACKUP_DIR/$BACKUP_FILE \
    --exclude="venv" \
    --exclude="logs" \
    --exclude=".git" \
    --exclude="__pycache__" \
    /path/to/prometheus-v30/.env \
    /path/to/prometheus-v30/config_*.py \
    /path/to/prometheus-v30/reports

echo "备份完成：$BACKUP_DIR/$BACKUP_FILE"

# 删除7天前的备份
find $BACKUP_DIR -name "prometheus_backup_*.tar.gz" -mtime +7 -delete
```

设置执行权限并添加到crontab：

```bash
chmod +x backup.sh
echo "0 0 * * * /path/to/backup.sh" | crontab -```
```

## 🔄 项目更新

定期更新项目以获取最新功能和安全修复：

### 标准更新流程

```bash
# 停止服务
sudo systemctl stop prometheus.service

# 切换到项目目录
cd /path/to/prometheus-v30

# 创建备份
./backup.sh

# 拉取最新代码
git pull origin main

# 激活虚拟环境
source venv/bin/activate

# 更新依赖
pip install -r requirements.txt --upgrade

# 运行兼容性测试
python test_okx_v1_compatibility.py

# 重启服务
sudo systemctl start prometheus.service

# 验证服务状态
sudo systemctl status prometheus.service
```

### Docker环境更新

```bash
# 停止并移除现有容器
docker-compose down

# 拉取最新代码
git pull origin main

# 重新构建并启动容器
docker-compose up -d --build

# 查看日志确认启动成功
docker-compose logs -f
```
```

## 🐳 Docker部署

### 基础Docker部署

确保已安装Docker和Docker Compose：

```bash
# 安装Docker (Ubuntu)
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo \"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable\" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Docker Compose配置

```bash
# 复制环境变量文件示例
cp .env.example .env

# 编辑.env文件设置API凭证和配置
sudo nano .env

# 构建并启动容器
docker-compose up -d

# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止容器
docker-compose down

# 重新构建并启动
docker-compose up -d --build
```

### 健康检查设置

```bash
# 运行健康检查脚本
docker exec prometheus ./healthcheck.sh

# 或者使用Docker原生健康检查命令
docker inspect --format='{{json .State.Health.Status}}' prometheus
```

Docker部署的优势：
- 隔离的运行环境，避免依赖冲突
- 标准化的部署流程，简化环境配置
- 内置健康检查和自动重启机制
- 便于扩展和迁移
```

## 🛡️ 安全最佳实践

### API安全

1. **API密钥管理**：
   - 仅为API密钥分配必要的权限（优先使用读取和交易权限，避免提现权限）
   - 启用IP白名单功能，限制只允许特定IP访问API
   - 定期轮换API密钥（建议每30-90天）
   - 使用环境变量或密钥管理系统存储API凭证，避免硬编码

2. **API调用安全**：
   - 通过HTTPS发起所有API请求
   - 实现请求签名验证机制
   - 设置合理的API调用频率限制
   - 监控异常API调用模式

### 服务器安全

1. **基础安全配置**：
   - 禁用root远程登录
   - 使用SSH密钥认证，完全禁用密码登录
   - 定期更新系统和软件包
   - 配置防火墙规则，仅允许必要的端口（22用于SSH，443用于API调用）

2. **系统加固**：
   - 安装入侵检测系统如Fail2ban
   - 启用自动安全更新
   - 限制系统资源使用
   - 使用非特权用户运行交易服务

3. **容器安全**：
   - 使用最小基础镜像
   - 实施多阶段构建减少攻击面
   - 运行时以非root用户身份
   - 定期扫描容器漏洞

### 数据安全

1. **配置和凭证**：
   - 加密敏感配置数据
   - 使用专用的密钥管理服务
   - 严格控制配置文件权限
   - 不要在日志中记录完整的API密钥

2. **备份和恢复**：
   - 定期备份关键配置和交易记录
   - 加密备份数据
   - 测试恢复流程
   - 存储备份在安全位置

### 高级监控配置

对于生产环境，建议配置Prometheus + Grafana进行全面监控：

```bash
# 部署监控栈
sudo apt install -y prometheus grafana

# 启用并启动服务
sudo systemctl enable prometheus grafana-server
sudo systemctl start prometheus grafana-server

# 配置Node Exporter
sudo apt install -y prometheus-node-exporter
sudo systemctl enable prometheus-node-exporter
sudo systemctl start prometheus-node-exporter
```

配置Grafana：
1. 访问http://your_server_ip:3000
2. 登录（默认账号admin/admin）
3. 添加Prometheus数据源
4. 导入交易系统仪表盘模板
```

## 🔧 故障排除

### 常见问题及解决方案

#### 1. API连接问题

```bash
# 检查API连接
echo "测试网络连接" | python test_network.py

# 验证API凭证
python verify_api_credentials.py
```

- **问题**：API请求返回401错误
  **解决**：检查API密钥、密钥和密码是否正确

- **问题**：API请求返回403错误
  **解决**：验证IP是否在白名单中，检查API权限设置

- **问题**：API请求返回429错误
  **解决**：API调用超限，检查是否需要降低调用频率或增加重试间隔

#### 2. 服务启动失败

```bash
# 检查服务状态和日志
sudo systemctl status prometheus.service
sudo journalctl -u prometheus.service --since "10 minutes ago"
```

- **问题**：权限被拒绝错误
  **解决**：检查文件和目录权限，确保服务用户有正确的访问权限

- **问题**：依赖缺失
  **解决**：重新安装依赖，使用`pip install -r requirements.txt --upgrade`

- **问题**：端口冲突
  **解决**：检查是否有其他进程占用相同端口

#### 3. 交易执行问题

- **问题**：订单无法执行
  **解决**：检查账户余额、保证金、订单参数和市场状态

- **问题**：交易延迟
  **解决**：优化系统资源分配，检查网络连接质量

- **问题**：策略执行异常
  **解决**：检查Agent配置，分析历史交易日志

### 排查流程

1. **检查服务状态**
   ```bash
   systemctl status prometheus.service
   ```

2. **分析日志**
   ```bash
   journalctl -u prometheus.service -n 200
   cat logs/prometheus.log | grep -i error
   ```

3. **验证网络连接**
   ```bash
   ping www.okx.com
   curl -I https://www.okx.com
   ```

4. **检查系统资源**
   ```bash
   htop
   free -h
   df -h
   ```

5. **使用诊断脚本**
   ```bash
   python diagnostic_tool.py
   ```

### 获取支持

如果您遇到无法解决的问题：

1. 查看[故障排除指南](docs/TROUBLESHOOTING.md)获取更详细的帮助
2. 搜索项目的GitHub Issues寻找类似问题的解决方案
3. 提交新的Issue，包含详细的错误日志和环境信息
4. 加入项目的Discord社区寻求即时帮助

## 🌐 多环境部署策略

### 开发环境

```bash
# 克隆开发分支
git clone -b develop https://github.com/yourusername/prometheus-v30.git
cd prometheus-v30

# 使用开发配置
cp config_virtual.py config_dev.py

# 安装开发依赖
pip install -e .[dev]

# 运行开发模式
python run_virtual_trading.py --config config_dev.py --log-level DEBUG
```

### 测试环境

```bash
# 切换到项目目录
cd /path/to/prometheus-v30

# 使用测试配置
cp config_virtual.py config_test.py

# 配置测试环境变量
cat > .env.test << EOF
OKX_API_KEY=test_api_key
OKX_SECRET_KEY=test_secret_key
OKX_PASSPHRASE=test_passphrase
OKX_USE_TESTNET=true
LOG_LEVEL=INFO
EOF

# 运行测试模式
source venv/bin/activate
python run_virtual_trading.py --config config_test.py --env-file .env.test
```

### 生产环境

生产环境部署最佳实践：

1. 使用专用服务器或VPS，避免与其他应用共享资源
2. 实施严格的网络隔离和访问控制
3. 配置自动监控和告警
4. 建立详细的操作和维护文档
5. 定期进行安全审计和系统更新

### 部署清单

**部署前检查**：
- [ ] 系统环境符合要求
- [ ] 依赖已正确安装
- [ ] API凭证已安全配置
- [ ] 配置文件已根据环境调整
- [ ] 测试脚本运行正常

**部署后验证**：
- [ ] 服务成功启动且运行稳定
- [ ] 日志无错误
- [ ] 监控系统正常工作
- [ ] 备份机制已配置
- [ ] 安全措施已实施

**定期维护**：
- [ ] 检查系统更新
- [ ] 验证API凭证有效性
- [ ] 审查交易日志
- [ ] 备份重要数据
- [ ] 检查系统资源使用情况