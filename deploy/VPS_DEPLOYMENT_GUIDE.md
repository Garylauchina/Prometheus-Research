# 🚀 Prometheus VPS部署指南

**更新日期**: 2025-12-06  
**目标**: 在VPS上运行OKX虚拟盘交易

---

## 📋 前置准备

### 1. VPS要求

```
操作系统: Ubuntu 22.04 LTS
CPU: 2核
内存: 4GB
硬盘: 20GB
网络: 稳定连接
地理位置: 香港/新加坡（推荐，靠近OKX）

推荐服务商:
- Vultr ($12-24/月)
- DigitalOcean ($12-24/月)
- 阿里云 (¥60-100/月)
```

### 2. OKX账户

```
1. 注册OKX账户
2. 开启API权限
3. 创建API Key（需要3个：key, secret, passphrase）
4. 权限设置：
   ✅ 读取（必需）
   ✅ 交易（必需）
   ❌ 提币（禁用，安全第一）

⚠️  重要：
- 保存好API密钥（只显示一次）
- 不要泄露给任何人
- 可以设置IP白名单（推荐）
```

---

## 🔧 部署步骤

### 步骤1: 连接VPS

```bash
# SSH连接
ssh root@your_vps_ip

# 或使用密钥
ssh -i ~/.ssh/your_key.pem root@your_vps_ip
```

---

### 步骤2: 运行环境搭建脚本

```bash
# 下载搭建脚本
wget https://raw.githubusercontent.com/YOUR_REPO/deploy/vps_setup.sh

# 或者手动创建（如果无法下载）
vim vps_setup.sh
# 粘贴脚本内容

# 添加执行权限
chmod +x vps_setup.sh

# 运行
./vps_setup.sh
```

**预计耗时**: 5-10分钟

---

### 步骤3: 上传Prometheus代码

#### 方案A: 使用Git（推荐）

```bash
cd ~/prometheus

# 克隆仓库
git clone https://github.com/YOUR_REPO/Prometheus-Quant.git .

# 切换到正确分支
git checkout develop/v5.0
```

#### 方案B: 使用SCP（本地上传）

```bash
# 在本地电脑运行
cd /Users/liugang/Cursor_Store/Prometheus-Quant

# 压缩代码（排除不必要的文件）
tar -czf prometheus.tar.gz \
    prometheus/ \
    config/ \
    vps_main.py \
    requirements.txt \
    --exclude '*.pyc' \
    --exclude '__pycache__' \
    --exclude '.git' \
    --exclude 'data/' \
    --exclude 'logs/'

# 上传到VPS
scp prometheus.tar.gz root@your_vps_ip:~/prometheus/

# 在VPS上解压
ssh root@your_vps_ip
cd ~/prometheus
tar -xzf prometheus.tar.gz
```

---

### 步骤4: 配置API密钥

```bash
cd ~/prometheus

# 编辑配置文件
vim config/vps_config.json

# 填入OKX API信息:
{
  "okx": {
    "api_key": "YOUR_REAL_API_KEY",
    "api_secret": "YOUR_REAL_API_SECRET",
    "passphrase": "YOUR_REAL_PASSPHRASE",
    "paper_trading": true,  # 虚拟盘，安全！
    "testnet": false
  },
  ...
}

# 保存并退出 (:wq)
```

⚠️  **重要**: 确保 `paper_trading: true`（虚拟盘）

---

### 步骤5: 安装Python依赖

```bash
cd ~/prometheus

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 或手动安装
pip install ccxt numpy pandas scipy matplotlib
```

---

### 步骤6: 测试连接

```bash
# 测试OKX API连接
python -c "
from prometheus.exchange.okx_api import OKXExchange
import json

with open('config/vps_config.json') as f:
    config = json.load(f)

exchange = OKXExchange(
    api_key=config['okx']['api_key'],
    api_secret=config['okx']['api_secret'],
    passphrase=config['okx']['passphrase'],
    paper_trading=True
)

if exchange.test_connection():
    print('✅ OKX连接成功！')
else:
    print('❌ OKX连接失败！')
"
```

**预期输出**: `✅ OKX连接成功！`

---

### 步骤7: 启动系统（测试模式）

```bash
# 短期测试（5分钟）
python vps_main.py --config config/vps_config.json

# 观察输出
# 按Ctrl+C停止

# 检查日志
tail -f logs/*.log
```

---

### 步骤8: 后台运行（生产模式）

```bash
# 使用nohup后台运行
nohup python vps_main.py --config config/vps_config.json > output.log 2>&1 &

# 记录PID
echo $! > prometheus.pid

# 查看实时日志
tail -f output.log

# 或使用screen（推荐）
screen -S prometheus
python vps_main.py --config config/vps_config.json

# 按Ctrl+A, D退出screen（程序继续运行）
# 重新连接: screen -r prometheus
```

---

## 🔍 监控和管理

### 查看运行状态

```bash
# 检查进程是否运行
ps aux | grep vps_main

# 查看实时日志
tail -f output.log
tail -f prometheus_vps.log

# 查看交易日志
tail -f logs/trades_*.json

# 查看盈亏日志
tail -f logs/pnl_*.json
```

---

### 停止系统

```bash
# 方法1: 如果使用screen
screen -r prometheus
# 按Ctrl+C

# 方法2: 如果使用nohup
kill $(cat prometheus.pid)

# 方法3: 强制停止（不推荐）
pkill -f vps_main.py
```

---

### 重启系统

```bash
# 停止
kill $(cat prometheus.pid)

# 等待3秒
sleep 3

# 重启
nohup python vps_main.py --config config/vps_config.json > output.log 2>&1 &
echo $! > prometheus.pid
```

---

## 📊 每日检查清单

### 每天早上

```bash
# 1. 检查系统是否运行
ps aux | grep vps_main

# 2. 查看账户总价值
python -c "
from prometheus.exchange.okx_api import OKXExchange
import json

with open('config/vps_config.json') as f:
    config = json.load(f)

exchange = OKXExchange(
    api_key=config['okx']['api_key'],
    api_secret=config['okx']['api_secret'],
    passphrase=config['okx']['passphrase'],
    paper_trading=True
)

value = exchange.get_account_value()
print(f'账户总价值: \${value:,.2f}')
"

# 3. 查看日志中是否有错误
tail -100 prometheus_vps.log | grep ERROR

# 4. 查看每日报告
cat logs/report_$(date +%Y%m%d).json | python -m json.tool
```

---

## 🚨 异常处理

### 问题1: 连接失败

```bash
# 检查网络
ping api.okx.com

# 检查API密钥是否正确
# 重新配置 config/vps_config.json

# 检查防火墙
sudo ufw status
```

---

### 问题2: 内存不足

```bash
# 查看内存使用
free -h

# 如果不足，增加swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

### 问题3: 进程崩溃

```bash
# 查看崩溃日志
tail -200 output.log

# 查看系统日志
tail -100 /var/log/syslog

# 设置自动重启（使用systemd）
# 见下方"生产环境配置"
```

---

## 🏭 生产环境配置

### 使用systemd（推荐）

创建服务文件：

```bash
sudo vim /etc/systemd/system/prometheus.service
```

内容：

```ini
[Unit]
Description=Prometheus Quant Trading System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/prometheus
Environment="PATH=/root/prometheus/venv/bin"
ExecStart=/root/prometheus/venv/bin/python vps_main.py --config config/vps_config.json
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务：

```bash
# 重载systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start prometheus

# 设置开机自启
sudo systemctl enable prometheus

# 查看状态
sudo systemctl status prometheus

# 查看日志
sudo journalctl -u prometheus -f
```

---

## 📈 性能优化

### 1. 减少日志输出

```python
# 修改 prometheus_vps.log 的级别
logging.basicConfig(level=logging.WARNING)
```

### 2. 增加交易周期

```json
// config/vps_config.json
{
  "trading": {
    "interval": 300,  // 5分钟一次（减少频率）
    ...
  }
}
```

### 3. 减少Agent数量

```json
{
  "agents": {
    "initial_count": 20,  // 从50减少到20
    ...
  }
}
```

---

## 🔒 安全建议

1. **API密钥安全** ⭐⭐⭐⭐⭐
   - 不要提交到Git
   - 设置IP白名单
   - 定期更换

2. **虚拟盘先行** ⭐⭐⭐⭐⭐
   - 至少运行1个月
   - 确认稳定再考虑实盘

3. **资金控制** ⭐⭐⭐⭐⭐
   - 实盘从小金额开始（$1000-5000）
   - 设置最大亏损限制
   - 随时可以紧急停止

4. **备份数据** ⭐⭐⭐⭐
   - 定期备份日志
   - 定期备份Agent状态
   - 可以恢复现场

---

## 📞 故障排查

### 常见问题

1. **ImportError: No module named 'ccxt'**
   ```bash
   source venv/bin/activate
   pip install ccxt
   ```

2. **Permission denied**
   ```bash
   chmod +x vps_main.py
   ```

3. **Port already in use**
   ```bash
   # 查找占用端口的进程
   lsof -i :PORT
   # 杀死进程
   kill PID
   ```

---

## 📊 监控指标

建议监控的关键指标：

1. **系统指标**
   - CPU使用率
   - 内存使用率
   - 磁盘空间

2. **交易指标**
   - 账户总价值
   - 每日盈亏
   - 交易次数

3. **Agent指标**
   - 存活数量
   - 平均资金
   - 进化次数

---

## 🎯 测试计划

### 第1周: 小规模测试

```json
{
  "agents": {
    "initial_count": 10,
    "initial_capital": 1000.0
  },
  "trading": {
    "interval": 300,  // 5分钟
    "max_leverage": 5.0
  }
}
```

**目标**: 验证系统稳定性

---

### 第2-3周: 中规模测试

```json
{
  "agents": {
    "initial_count": 30,
    "initial_capital": 5000.0
  },
  "trading": {
    "interval": 60,  // 1分钟
    "max_leverage": 10.0
  }
}
```

**目标**: 验证策略有效性

---

### 第4周: 接近实盘规模

```json
{
  "agents": {
    "initial_count": 50,
    "initial_capital": 10000.0
  },
  "trading": {
    "interval": 60,
    "max_leverage": 10.0
  }
}
```

**目标**: 压力测试

---

## ✅ 验收标准

### 虚拟盘成功标准

在进入实盘前，必须满足：

1. ✅ 连续运行30天无崩溃
2. ✅ 盈利率 > 70%
3. ✅ 年化收益 > 50%
4. ✅ 最大回撤 < 30%
5. ✅ 无严重错误日志

---

## 📝 注意事项

1. **配置文件安全**
   - 不要提交包含API密钥的配置到Git
   - 使用 `.gitignore` 排除 `config/*.json`

2. **资源管理**
   - 定期清理日志文件
   - 监控磁盘空间
   - 设置日志轮转

3. **定期更新**
   - 从本地同步最新代码
   - 测试后再部署
   - 保留回滚方案

4. **应急预案**
   - 准备紧急停止脚本
   - 保存重要数据
   - 随时可以平仓退出

---

**部署指南完成！祝您部署顺利！** 🚀

