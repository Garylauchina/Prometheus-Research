# Prometheus v3.0 - 快速开始

![QuickStart](https://img.shields.io/badge/Quick-Start-green)
![Documentation](https://img.shields.io/badge/Documentation-Complete-blue)

## 📑 目录

- [🚀 一键部署](#-一键部署)
- [📋 手动部署](#-手动部署)
- [🐳 Docker部署](#-docker部署)
- [📊 监控系统](#-监控系统)
- [🔧 常用命令](#-常用命令)
- [📝 配置说明](#-配置说明)
- [⚙️ 快速配置示例](#-快速配置示例)
- [⚠️ 注意事项](#-注意事项)
- [🆘 故障排查](#-故障排查)
- [❓ 常见问题](#-常见问题)
- [📚 更多资源](#-更多资源)

## 🚀 一键部署

我们提供了强大的一键部署脚本，支持多种部署模式和选项。

### 标准部署

```bash
# 从GitHub直接运行（推荐）
curl -sSL https://raw.githubusercontent.com/Garylauchina/prometheus-v30/main/deploy.sh | bash
```

或者先克隆仓库：

```bash
git clone https://github.com/Garylauchina/prometheus-v30.git
cd prometheus-v30
chmod +x deploy.sh
./deploy.sh
```

### 自定义部署选项

```bash
# 指定部署模式：virtual（默认）或 docker
./deploy.sh --mode=docker

# 指定日志级别
./deploy.sh --log-level=DEBUG

# 自动创建API配置文件
./deploy.sh --api-key="your_key" --api-secret="your_secret" --passphrase="your_passphrase"

# 禁用系统服务创建（仅安装）
./deploy.sh --no-service
```

### 脚本功能概述

一键部署脚本自动完成以下任务：

✅ **环境检测与准备**
- 检查操作系统兼容性（Ubuntu/Debian/CentOS）
- 安装系统依赖（Python、Git、必要系统包）
- 创建专用用户和目录权限

✅ **依赖管理**
- 创建并配置Python虚拟环境
- 安装最新版本的项目依赖
- 验证OKX SDK兼容性

✅ **配置设置**
- 引导用户配置API凭证
- 设置适当的安全权限
- 生成初始配置文件

✅ **服务配置**
- 创建systemd服务（可选）
- 设置自动启动和日志管理
- 配置防火墙规则

✅ **验证部署**
- 运行健康检查
- 验证API连接
- 确认系统正常运行

---

## 📋 手动部署

如果您想手动控制每一步，请参考 [DEPLOY.md](DEPLOY.md) 获取详细指南。

---

## 🐳 Docker部署

Docker部署提供了环境隔离和简化管理的优势，特别适合生产环境。

### 使用Docker Compose（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/Garylauchina/prometheus-v30.git
cd prometheus-v30

# 2. 配置API凭证和环境变量
cp .env.example .env
nano .env  # 编辑配置文件

# 3. 启动服务（包含健康检查）
docker-compose up -d

# 4. 验证部署状态
docker-compose ps

# 5. 查看日志
docker-compose logs -f
```

#### 高级Docker Compose选项

```bash
# 构建并重新创建容器
docker-compose up -d --build --force-recreate

# 查看详细健康检查状态
docker inspect --format='{{json .State.Health}}' prometheus

# 停止并移除所有相关容器
docker-compose down -v
```

### 使用纯Docker

```bash
# 构建镜像
docker build -t prometheus-v30 .

# 运行容器（包含健康检查和资源限制）
docker run -d \
  --name prometheus-v30 \
  --restart always \
  --health-cmd="python health_check.py" \
  --health-interval=60s \
  --health-timeout=10s \
  --health-retries=3 \
  --memory=2g \
  --cpus=1 \
  -e OKX_API_KEY="your_api_key" \
  -e OKX_SECRET_KEY="your_secret_key" \
  -e OKX_PASSPHRASE="your_passphrase" \
  -e LOG_LEVEL="INFO" \
  -v $(pwd)/trading_logs:/app/trading_logs \
  -v $(pwd)/config:/app/config \
  prometheus-v30

# 验证容器健康状态
docker healthcheck ls
```

### Docker部署注意事项

- **持久化数据**：使用卷挂载保存日志和配置
- **资源限制**：根据您的VPS规格调整内存和CPU限制
- **健康检查**：定期验证容器健康状态
- **网络安全**：考虑使用网络隔离或VPN连接
```

---

## 📊 监控系统

监控系统是确保交易系统稳定运行的关键组件。我们提供了多种监控工具和方法。

### 基本监控

```bash
# 使用内置监控脚本
./monitor.sh

# 实时监控（每5秒刷新一次）
./monitor.sh --interval=5

# 详细监控模式
./monitor.sh --verbose
```

### 监控指标详解

| 监控类别 | 关键指标 | 说明 |
|---------|---------|------|
| **系统状态** | 服务运行状态、启动时间、进程ID | 基本运行信息 |
| **资源使用** | CPU使用率、内存使用、磁盘空间 | 系统资源状况 |
| **API连接** | 连接状态、响应时间、错误率 | 交易所连接质量 |
| **交易性能** | ROI、交易数量、胜率 | 策略效果评估 |
| **Agent状态** | 活跃/非活跃比例、策略成功率 | AI交易代理状态 |
| **健康检查** | 网络连通性、依赖服务状态 | 系统整体健康度 |

### 高级监控选项

#### Docker环境监控

```bash
# 查看容器详细状态
docker stats prometheus

# 检查容器健康状态历史
docker inspect --format='{{json .State.Health.Log}}' prometheus
```

#### 自定义监控配置

编辑`config/monitor_config.py`文件，可以：
- 设置告警阈值（CPU、内存、错误率）
- 配置通知方式（邮件、Telegram）
- 调整监控间隔和保留策略

#### 实时告警设置

```bash
# 配置监控告警（需要提前设置通知方式）
./monitor.sh --setup-alerts

# 查看告警日志
cat logs/monitor_alerts.log
```

### 监控输出示例

```
============================================================
  Prometheus v3.0 - 系统监控
============================================================

[服务状态]
✅ Prometheus服务: 运行中
   启动时间: 2025-11-29 15:00:00
   运行时长: 2d 14h 30m

[系统资源]
CPU使用率: 15.2% (阈值: 80%)
内存使用: 512MB/2GB (25%)
磁盘使用: 5GB/20GB (25%)

[API连接]
OKX连接状态: 正常
响应时间: 120ms
API错误率: 0%

[交易统计]
ROI: 2.08%
总交易: 45
胜率: 68%
活跃Agent: 5/5

[健康状态]
系统健康评分: 98/100
最近检查: 2分钟前
告警状态: 无告警
```

---

## 🔧 常用命令

### 服务管理

```bash
# 查看状态
sudo systemctl status prometheus.service

# 启动服务
sudo systemctl start prometheus.service

# 停止服务
sudo systemctl stop prometheus.service

# 重启服务
sudo systemctl restart prometheus.service

# 查看实时日志
sudo journalctl -u prometheus.service -f
```

### Docker管理

```bash
# 查看容器状态
docker ps

# 查看日志
docker logs -f prometheus-v30

# 停止容器
docker stop prometheus-v30

# 启动容器
docker start prometheus-v30

# 重启容器
docker restart prometheus-v30
```

---

## 📝 配置说明

### 基本配置参数

| 参数 | 描述 | 默认值 | 如何配置 |
|------|------|--------|----------|
| 运行时长 | 系统连续运行时间（秒） | 2592000 (30天) | 命令行参数或配置文件 |
| 日志级别 | 日志详细程度 | INFO | 环境变量或命令行参数 |
| API超时 | API请求超时时间（秒） | 30 | 配置文件 |
| 重试次数 | API请求失败重试次数 | 3 | 配置文件 |
| Agent数量 | 交易代理数量 | 5 | 配置文件 |

### 运行时长配置

```bash
# 使用命令行参数设置运行时长
python run_virtual_trading.py --duration 86400  # 24小时

# 使用配置文件设置（推荐）
# 编辑 config/default_config.py
RUN_DURATION = 86400
```

**Systemd服务配置**:
```bash
# 编辑服务文件
sudo nano /etc/systemd/system/prometheus.service

# 修改ExecStart行
ExecStart=/home/user/prometheus-v30/venv/bin/python /home/user/prometheus-v30/run_virtual_trading.py --duration 86400 --config config/production_config.py

# 重新加载systemd配置
sudo systemctl daemon-reload
```

### 日志配置

```bash
# 设置日志级别（DEBUG/INFO/WARNING/ERROR）
python run_virtual_trading.py --log-level DEBUG

# 或使用环境变量
export LOG_LEVEL=DEBUG
python run_virtual_trading.py
```

### 环境变量配置

创建`.env`文件或设置系统环境变量：

```ini
# API凭证
OKX_API_KEY="your_api_key"
OKX_SECRET_KEY="your_secret_key"
OKX_PASSPHRASE="your_passphrase"

# 运行配置
LOG_LEVEL="INFO"
RUN_MODE="production"
AGENT_COUNT="5"

# 风险配置
MAX_DRAWDOWN="0.05"  # 5%
MAX_POSITION_SIZE="0.1"  # 10%

# 网络配置
API_PROXY=""
TIMEOUT="30"
```

### 配置文件层级

系统配置按以下优先级加载（从高到低）：
1. 命令行参数
2. 环境变量
3. 指定的配置文件（--config参数）
4. 默认配置文件（config/default_config.py）

## ⚙️ 快速配置示例

### 基础配置（推荐新手）

```python
# 创建简单配置文件: config/my_config.py

# 基础设置
RUN_DURATION = 86400  # 24小时
LOG_LEVEL = "INFO"
LOG_FILE = "trading_logs/prometheus.log"

# API配置
API_RETRY_COUNT = 3
API_TIMEOUT = 30

# Agent配置
AGENT_COUNT = 3  # 新手建议从较少数量开始
AGENT_INITIAL_BUDGET = 1000  # 每个Agent的初始预算

# 风险控制
MAX_POSITION_SIZE = 0.05  # 最大仓位5%
STOP_LOSS_RATIO = 0.02  # 止损比例2%
TAKE_PROFIT_RATIO = 0.05  # 止盈比例5%
```

### 高级配置（适合有经验的用户）

```python
# 创建高级配置: config/advanced_config.py

# 基础设置
RUN_DURATION = 604800  # 7天
LOG_LEVEL = "DEBUG"  # 更详细的日志
LOG_ROTATION = "100MB"  # 日志大小轮转

# API优化
API_RETRY_COUNT = 5
API_TIMEOUT = 45
API_REQUEST_INTERVAL = 0.5  # 避免API限流
RATE_LIMIT_ADJUSTMENT = True  # 自动调整请求速率

# Agent配置
AGENT_COUNT = 5
AGENT_INITIAL_BUDGET = 5000
AGENT_EVOLUTION_RATE = 0.1  # 进化速率10%
ENABLE_ADAPTIVE_STRATEGY = True

# 风险控制
MAX_DRAWDOWN = 0.08  # 最大回撤8%
MAX_DAILY_LOSS = 0.03  # 每日最大亏损3%
MAX_OPEN_POSITIONS = 10
USE_STOP_LOSS = True
USE_TRAILING_STOP = True  # 使用追踪止损

# 性能优化
DATA_CACHE_SIZE = 10000
ENABLE_MULTITHREADING = True
MAX_WORKERS = 4
```

### 使用自定义配置运行

```bash
# 使用自定义配置文件
python run_virtual_trading.py --config config/my_config.py

# 结合命令行参数
python run_virtual_trading.py --config config/advanced_config.py --duration 3600
```

## ⚠️ 注意事项

### API安全最佳实践

- **凭证保护**
  - 永远不要将`.env`文件提交到Git仓库
  - 使用`.gitignore`确保敏感文件不会被跟踪
  - 定期轮换API密钥（建议每30-90天）
  - 限制API密钥权限，仅授予必要权限（读取+交易）

- **环境安全**
  - 在OKX账户中启用IP白名单
  - 为VPS配置防火墙规则
  - 使用强密码和SSH密钥登录
  - 定期更新系统和依赖包

### 资源管理

- **监控与维护**
  - 设置自动化监控和告警
  - 配置日志轮转避免磁盘空间耗尽
  - 定期清理旧日志和临时文件
  - 监控内存泄漏和资源占用异常

- **扩展规划**
  - 根据交易量增长规划资源扩展
  - 考虑水平扩展多实例架构
  - 准备高可用方案应对单点故障

### 网络与连接

- **稳定性保障**
  - 使用高可靠的VPS提供商
  - 监控网络延迟和丢包率
  - 实现API调用退避策略
  - 考虑使用冗余网络连接

- **性能优化**
  - 将VPS部署在靠近OKX服务器的区域
  - 优化网络配置减少延迟
  - 避免高峰期大量数据传输

### 数据管理

- **备份策略**
  - 定期备份交易记录和配置
  - 使用加密存储敏感数据
  - 测试备份恢复流程
  - 考虑使用云存储异地备份

- **数据安全**
  - 加密存储API凭证
  - 匿名化处理交易日志（如需共享）
  - 限制数据访问权限
  - 定期审查数据访问记录

---

## 🆘 故障排查

### 快速诊断

```bash
# 运行诊断脚本（推荐）
./diagnose.sh

# 检查服务状态
systemctl status prometheus.service

# 查看关键日志
tail -n 100 logs/prometheus.log | grep -i "error"
```

### 常见问题与解决方案

#### 1. 服务启动问题

**症状**: 服务无法启动或立即崩溃

**排查步骤**:

```bash
# 查看详细错误日志
sudo journalctl -u prometheus.service -n 100

# 手动测试启动命令
sudo -u prometheus /path/to/venv/bin/python /path/to/run_virtual_trading.py --config /path/to/config.py

# 检查配置文件语法
python -m py_compile config/config.py

# 检查文件权限
find /path/to/prometheus-v30 -type f -name "*.py" -exec chmod 644 {} \;
find /path/to/prometheus-v30 -type d -exec chmod 755 {} \;
```

**常见原因**:
- 配置文件格式错误
- 权限问题（文件或目录）
- Python环境问题
- 端口冲突

#### 2. API连接失败

**症状**: 系统无法连接到OKX API

**排查步骤**:

```bash
# 验证网络连接
ping -c 4 okx.com

# 测试API端口连通性
telnet api.okx.com 443

# 验证API凭证
python test_api_connection.py

# 检查API限制和配额
python check_api_usage.py
```

**解决方案**:
- 检查`.env`文件中的API凭证是否正确
- 验证IP是否在OKX白名单中
- 确认API密钥权限设置正确
- 检查网络代理设置
- 减少API调用频率避免限流

#### 3. 性能问题

**症状**: 系统响应缓慢或占用过多资源

**排查步骤**:

```bash
# 检查系统资源使用
top -p $(pgrep -f "python run_virtual_trading")

# 分析内存使用
ps aux | grep python

# 检查日志大小
ls -lh trading_logs/

# 查看慢查询或操作
python analyze_performance.py
```

**优化建议**:
- 减少Agent数量（在配置文件中修改AGENT_COUNT）
- 降低数据缓存大小
- 增加日志轮转频率
- 优化策略参数减少计算复杂度
- 升级VPS资源

#### 4. Docker环境问题

**症状**: 容器启动失败或功能异常

**排查步骤**:

```bash
# 查看容器日志
docker logs -f prometheus

# 检查容器健康状态
docker ps | grep prometheus

# 进入容器调试
docker exec -it prometheus bash

# 验证卷挂载
ls -la /app/trading_logs
```

**解决方案**:
- 重建Docker镜像
- 检查环境变量配置
- 验证卷挂载权限
- 增加容器资源限制
- 检查健康检查配置

### 高级故障排除

#### 日志分析

```bash
# 分析错误日志模式
grep -i "error" logs/prometheus.log | sort | uniq -c | sort -nr

# 查看API错误统计
grep -i "api error" logs/prometheus.log | wc -l

# 检查性能瓶颈
grep -i "timeout\|slow" logs/prometheus.log
```

#### 系统监控

```bash
# 长期监控系统资源
./monitor.sh --continuous --output logs/system_monitor.log

# 检查磁盘空间
df -h

# 检查进程状态
ps -ef | grep python
```

#### 应急恢复

```bash
# 紧急停止服务
systemctl stop prometheus.service

# 备份当前状态
./backup_state.sh

# 恢复到已知良好配置
cp config/bak/good_config.py config/current_config.py

# 重启服务
systemctl start prometheus.service
```

## ❓ 常见问题

### 配置与运行

**Q: 如何调整交易策略参数？**
A: 编辑`config/strategy_config.py`文件中的参数，或创建自定义配置文件并使用`--config`参数指定。

**Q: 如何设置不同的交易对？**
A: 在配置文件中修改`TRADING_PAIRS`列表，例如：`TRADING_PAIRS = ["BTC-USDT", "ETH-USDT", "SOL-USDT"]`

**Q: 如何控制交易风险？**
A: 调整配置文件中的风险参数：
- `MAX_POSITION_SIZE`: 单个交易最大比例
- `MAX_DRAWDOWN`: 最大回撤限制
- `STOP_LOSS_RATIO`: 止损比例
- `DAILY_LOSS_LIMIT`: 每日最大亏损限制

### Docker相关

**Q: Docker部署与直接部署有什么区别？**
A: Docker提供了环境隔离，避免依赖冲突，简化部署和迁移，但需要额外学习Docker相关知识。

**Q: 如何在Docker中查看和修改配置？**
A: 使用卷挂载持久化配置目录，然后在主机上直接编辑文件：
```bash
# 编辑配置文件
nano config/config.py

# 重启容器应用更改
docker-compose restart
```

**Q: 如何备份Docker部署的数据？**
A: 备份挂载的卷目录：
```bash
# 备份日志和数据
tar -czf prometheus_backup.tar.gz trading_logs/ config/
```

### 性能优化

**Q: 如何提高系统性能？**
A: 
- 调整`config/performance_config.py`中的参数
- 增加VPS资源（内存和CPU）
- 启用多线程处理（设置`ENABLE_MULTITHREADING = True`）
- 优化日志级别（生产环境使用INFO而非DEBUG）

**Q: 如何降低API调用频率？**
A: 
- 增加`API_REQUEST_INTERVAL`值（秒）
- 启用`RATE_LIMIT_ADJUSTMENT = True`
- 减少`AGENT_COUNT`数量
- 优化数据获取频率

### 安全相关

**Q: 如何保护API凭证？**
A: 
- 使用`.env`文件并添加到`.gitignore`
- 启用OKX的IP白名单功能
- 定期更换API密钥
- 设置最小权限原则

**Q: 如何防止系统被黑客攻击？**
A: 
- 保持系统和依赖包更新
- 配置防火墙限制访问
- 使用SSH密钥而非密码登录VPS
- 定期检查异常活动

## 📚 更多资源

### 文档

- [完整部署指南](DEPLOY.md)
- [项目README](README.md)
- [API兼容性说明](adapters/README_OKX_COMPAT.md)
- [故障排除详细指南](docs/TROUBLESHOOTING.md)

### 高级文档

- [系统设计文档](docs/DESIGN.md)
- [Agent进化机制](docs/EVOLUTION.md)
- [参数调优指南](docs/PARAMETERS.md)

### 开发资源

- [GitHub仓库](https://github.com/Garylauchina/prometheus-v30)
- [贡献指南](CONTRIBUTING.md)
- [代码示例](examples/)

---

**祝您交易顺利！** 🚀

如果您需要帮助，请通过Issues或Discussions联系我们。
