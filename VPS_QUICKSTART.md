# 🚀 VPS快速启动指南

**更新**: 2025-12-06  
**适用**: OKX虚拟盘交易

---

## ⚡ 5分钟快速启动

### 前置条件

✅ VPS已准备好（Ubuntu 22.04）  
✅ OKX API密钥已获取  
✅ 本地代码已最新

---

## 📦 步骤1: 环境搭建（VPS上）

```bash
# 连接VPS
ssh root@your_vps_ip

# 运行一键搭建脚本
curl -sL https://YOUR_REPO/deploy/vps_setup.sh | bash

# 或手动执行：
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.12 python3.12-venv git
mkdir -p ~/prometheus && cd ~/prometheus
python3.12 -m venv venv
source venv/bin/activate
pip install ccxt numpy pandas scipy matplotlib
```

---

## 📤 步骤2: 上传代码（本地电脑）

```bash
# 方法A: 使用Git（推荐）
# 在VPS上：
cd ~/prometheus
git clone https://github.com/YOUR_REPO/Prometheus-Quant.git .

# 方法B: 使用SCP
# 在本地：
cd /Users/liugang/Cursor_Store/Prometheus-Quant
tar -czf prome.tar.gz prometheus/ config/ vps_main.py \
  --exclude '*.pyc' --exclude '__pycache__' --exclude '.git'
scp prome.tar.gz root@your_vps_ip:~/prometheus/
# 在VPS上：
cd ~/prometheus && tar -xzf prome.tar.gz
```

---

## 🔑 步骤3: 配置API密钥（VPS上）

```bash
cd ~/prometheus

# 复制配置模板
cp config/vps_config.json config/my_config.json

# 编辑配置
vim config/my_config.json

# 修改以下3项：
{
  "okx": {
    "api_key": "YOUR_API_KEY",      # ← 改这里
    "api_secret": "YOUR_API_SECRET", # ← 改这里
    "passphrase": "YOUR_PASSPHRASE", # ← 改这里
    "paper_trading": true  # ← 确保是true（虚拟盘）
  }
}

# 保存退出 (:wq)
```

---

## ✅ 步骤4: 测试连接（VPS上）

```bash
cd ~/prometheus
source venv/bin/activate

# 测试OKX连接
python prometheus/exchange/okx_api.py

# 预期输出：
# ✅ OKX连接成功 - BTC价格: $89,677.20
```

---

## 🚀 步骤5: 启动系统（VPS上）

### 测试运行（5分钟）

```bash
# 前台运行，观察输出
python vps_main.py --config config/my_config.json

# 看到正常运行后，按Ctrl+C停止
```

---

### 生产运行（后台持续）

```bash
# 使用screen（推荐）
screen -S prometheus
python vps_main.py --config config/my_config.json

# 按Ctrl+A, D 退出（程序继续运行）
# 重新连接：screen -r prometheus

# 或使用nohup
nohup python vps_main.py --config config/my_config.json > output.log 2>&1 &
echo $! > prometheus.pid
```

---

## 📊 步骤6: 监控状态（VPS上）

```bash
# 查看实时日志
tail -f output.log
# 或
tail -f prometheus_vps.log

# 查看进程
ps aux | grep vps_main

# 停止系统
kill $(cat prometheus.pid)
# 或
screen -r prometheus  # 然后按Ctrl+C
```

---

## 🎯 核心文件说明

```
~/prometheus/
├── prometheus/
│   ├── exchange/
│   │   └── okx_api.py          # OKX交易所API
│   ├── trading/
│   │   └── live_engine.py      # 实盘交易引擎
│   ├── monitoring/
│   │   └── system_monitor.py   # 监控系统
│   └── core/                   # Prometheus核心
│
├── config/
│   ├── vps_config.json         # 配置模板
│   └── my_config.json          # 你的配置（不要提交到Git）
│
├── vps_main.py                 # VPS主程序 ⭐
├── deploy/
│   ├── vps_setup.sh            # 环境搭建脚本
│   └── VPS_DEPLOYMENT_GUIDE.md # 详细文档
│
└── logs/                       # 日志目录（自动创建）
    ├── trades_*.json           # 交易记录
    ├── pnl_*.json              # 盈亏记录
    └── report_*.json           # 每日报告
```

---

## 🔧 常用命令

```bash
# 连接VPS
ssh root@your_vps_ip

# 激活虚拟环境
cd ~/prometheus && source venv/bin/activate

# 启动系统
python vps_main.py --config config/my_config.json

# 后台启动
screen -S prometheus
python vps_main.py --config config/my_config.json
# Ctrl+A, D 退出

# 重新连接
screen -r prometheus

# 查看日志
tail -f output.log

# 查看账户价值
python -c "
from prometheus.exchange.okx_api import OKXExchange
import json
with open('config/my_config.json') as f:
    cfg = json.load(f)
ex = OKXExchange(**cfg['okx'])
print(f'账户: \${ex.get_account_value():,.2f}')
"

# 更新代码（如果使用Git）
cd ~/prometheus
git pull origin develop/v5.0

# 重启系统
kill $(cat prometheus.pid)
nohup python vps_main.py --config config/my_config.json > output.log 2>&1 &
echo $! > prometheus.pid
```

---

## 📋 配置参数说明

```json
{
  "okx": {
    "api_key": "...",           # OKX API Key
    "api_secret": "...",        # OKX API Secret
    "passphrase": "...",        # OKX API Passphrase
    "paper_trading": true,      # true=虚拟盘，false=实盘
    "testnet": false            # true=测试网，false=正式网
  },
  "trading": {
    "symbol": "BTC/USDT",       # 交易对
    "interval": 60,             # 交易周期（秒）
    "evolution_interval": 86400,# 进化周期（秒），86400=1天
    "max_position_size": 0.01,  # 最大持仓（BTC）
    "max_leverage": 10.0        # 最大杠杆
  },
  "agents": {
    "initial_count": 50,        # 初始Agent数量
    "initial_capital": 10000.0  # 每个Agent初始资金
  },
  "monitoring": {
    "log_dir": "./logs",        # 日志目录
    "enable_alerts": true,      # 启用告警
    "alert_on_loss": true,      # 亏损时告警
    "max_drawdown": 0.3         # 最大回撤阈值
  }
}
```

---

## 🔒 安全检查清单

在启动前，请确认：

- [ ] `paper_trading: true` ✅（虚拟盘）
- [ ] API密钥正确填写
- [ ] API权限：只读+交易（不要开启提币）
- [ ] 配置文件未提交到Git
- [ ] VPS防火墙已配置
- [ ] 设置了IP白名单（可选）

---

## 🚨 常见问题

### 1. 连接失败

```bash
# 检查网络
ping api.okx.com

# 检查API密钥
# 重新复制配置到config/my_config.json
```

### 2. 模块导入错误

```bash
# 激活虚拟环境
source venv/bin/activate

# 重新安装依赖
pip install ccxt numpy pandas scipy matplotlib
```

### 3. 进程崩溃

```bash
# 查看错误日志
tail -100 output.log
tail -100 prometheus_vps.log

# 检查系统资源
free -h
df -h
```

---

## 📞 获取帮助

1. 查看详细文档：`deploy/VPS_DEPLOYMENT_GUIDE.md`
2. 检查日志文件：`logs/` 目录
3. 测试API连接：`python prometheus/exchange/okx_api.py`

---

## ✅ 成功标志

系统正常运行时，您应该看到：

```
================================================================================
🚀 Prometheus VPS交易系统
================================================================================

📋 配置信息:
   交易模式: 虚拟盘
   交易对: BTC/USDT
   交易周期: 60秒
   进化周期: 86400秒 (24.0小时)
   初始Agent: 50个
   初始资金: $500,000

✅ OKX交易所初始化完成
✅ 监控器初始化完成 - 日志目录: ./logs
✅ 初始Agent创建完成: 50个
✅ 实盘交易引擎初始化完成
🚀 交易引擎启动

============================================================
🔄 交易周期 #1 - 2025-12-06 18:30:00
📊 当前价格: $89,677.20
👥 活跃Agent数量: 50
💰 账户总价值: $500,000.00
...
```

---

**快速启动完成！祝交易顺利！** 🚀

