# 🔍 VPS监控指南

**更新**: 2025-12-06  
**版本**: v2.0（自动密码登录）

---

## ⚡ 快速开始（3步）

### 步骤1: 安装依赖

```bash
pip install paramiko python-dotenv
```

---

### 步骤2: 创建配置文件

```bash
# 复制配置模板
cp vps_config_example.txt .env

# 编辑配置文件
vim .env
```

**填入以下内容**：
```
VPS_HOST=45.76.97.37
VPS_USER=root
VPS_PASSWORD=您的VPS密码
VPS_PORT=22
```

**保存退出**（`:wq`）

---

### 步骤3: 运行监控

```bash
python monitor_vps_v2.py
```

**预期输出**：
```
🔌 连接VPS: root@45.76.97.37...
✅ 连接成功

================================================================================
🚀 Prometheus VPS 实时监控 v2.0
================================================================================

📊 系统状态:
   ✅ 进程状态: 运行中
   ⏰ 启动时间: 2025-12-06 12:56:21
   ⏱️  运行时长: 15分钟
   ✅ 错误数量: 0条
   🧬 进化次数: 0次

📈 当前交易状态:
   🔄 交易周期: #15 (共15个周期)
   💰 BTC价格: $89,597.70
   📊 价格变化: +0.02%
   💼 账户总价值: $100,000.00
   👥 存活Agent: 50/50
   📊 平均资金: $10,001.23

📊 最近5个周期:
   周期#  11: $89,588.80 📉 -0.01% | Agent: 50/50 | 平均: $9,999.01
   周期#  12: $89,600.40 📈 +0.01% | Agent: 50/50 | 平均: $10,000.45
   周期#  13: $89,615.00 📈 +0.02% | Agent: 50/50 | 平均: $10,002.18
   周期#  14: $89,597.70 📉 -0.02% | Agent: 50/50 | 平均: $10,000.09
   周期#  15: $89,600.10 📈 +0.00% | Agent: 50/50 | 平均: $10,001.23

================================================================================

💡 更多操作:
   查看实时日志: ssh root@45.76.97.37 'tail -f ~/prometheus/prometheus_vps.log'
   重新连接screen: ssh root@45.76.97.37 -t 'screen -r prometheus'
   再次监控: python monitor_vps_v2.py
```

---

## 🔒 安全说明

### .env文件安全
- ✅ `.env`已在`.gitignore`中，**不会被提交到Git**
- ✅ 密码只存储在本地
- ⚠️ 不要分享`.env`文件
- ⚠️ 不要截图包含密码的内容

### 更安全的方式（可选）
使用SSH密钥代替密码：

```bash
# 1. 生成SSH密钥（如果没有）
ssh-keygen -t rsa -b 4096

# 2. 复制公钥到VPS
ssh-copy-id root@45.76.97.37

# 3. 测试免密登录
ssh root@45.76.97.37

# 成功后就不需要.env文件了
```

---

## 📊 监控功能

### 显示的信息
- ✅ 系统状态（运行/停止）
- ✅ 启动时间和运行时长
- ✅ 错误统计
- ✅ 进化次数
- ✅ 当前交易周期
- ✅ BTC实时价格和变化
- ✅ 账户总价值
- ✅ Agent存活情况
- ✅ 最近5个周期详情

---

## 🎯 使用场景

### 每天早上检查
```bash
python monitor_vps_v2.py
```

### 工作间隙快速查看
```bash
python monitor_vps_v2.py
```

### 24小时后检查进化
```bash
python monitor_vps_v2.py
# 查看"进化次数"是否>0
```

---

## 🔧 故障排查

### 问题1: 连接失败
```
❌ 连接失败: Authentication failed
```

**解决**:
- 检查`.env`中的密码是否正确
- 检查VPS是否在线：`ping 45.76.97.37`

---

### 问题2: 缺少依赖
```
❌ 缺少依赖库！
```

**解决**:
```bash
pip install paramiko python-dotenv
```

---

### 问题3: 未找到密码
```
❌ 未找到VPS密码！
```

**解决**:
```bash
# 确认.env文件存在
ls -la .env

# 如果不存在，创建它
cp vps_config_example.txt .env
vim .env
```

---

### 问题4: 进程未运行
```
❌ 进程状态: 未运行
```

**解决**:
```bash
# SSH登录VPS
ssh root@45.76.97.37

# 重新连接screen
screen -r prometheus

# 如果screen不存在，重新启动
cd ~/prometheus
source venv/bin/activate
screen -S prometheus
python vps_main.py --config config/vps_config.json
# Ctrl+A, D 退出
```

---

## 💡 高级用法

### 定时监控（每小时）
创建crontab任务：

```bash
# 编辑crontab
crontab -e

# 添加这行（每小时运行一次）
0 * * * * cd /Users/liugang/Cursor_Store/Prometheus-Quant && python3 monitor_vps_v2.py > monitor_log.txt 2>&1
```

### 监控并保存日志
```bash
python monitor_vps_v2.py | tee monitor_$(date +%Y%m%d_%H%M%S).log
```

### 只查看特定信息
修改`monitor_vps_v2.py`中的`display_status`方法，注释掉不需要的部分。

---

## 📋 文件说明

```
monitor_vps_v2.py          - 监控脚本（自动密码登录）
vps_config_example.txt     - 配置文件示例
.env                       - 实际配置文件（需自己创建）
VPS_MONITOR_GUIDE.md       - 本指南
```

---

## 🎯 对比旧版本

| 功能 | monitor_vps.py | monitor_vps_v2.py |
|------|----------------|-------------------|
| 密码输入 | 每次手动 | 自动读取.env |
| 连接方式 | SSH命令 | Python SSH库 |
| 显示详情 | 基础 | 详细 |
| 最近周期 | 无 | ✅ 显示5个 |
| 运行时长 | 无 | ✅ 自动计算 |

---

## ✅ 总结

**优点**：
- ✅ 自动登录，无需手动输入密码
- ✅ 显示详细信息
- ✅ 最近5个周期对比
- ✅ 运行时长自动计算
- ✅ 安全（.env不会提交到Git）

**使用流程**：
1. 安装依赖：`pip install paramiko python-dotenv`
2. 创建配置：`cp vps_config_example.txt .env`
3. 填入密码：`vim .env`
4. 运行监控：`python monitor_vps_v2.py`

---

**监控工具已就绪！** 🚀

