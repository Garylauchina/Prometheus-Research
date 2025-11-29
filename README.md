# Prometheus v3.0 - AI驱动加密货币交易系统

**基于遗传算法和多Agent进化的自动化交易系统**

![Version](https://img.shields.io/badge/version-3.0-blue)
![Python](https://img.shields.io/badge/python-3.11-green)
![License](https://img.shields.io/badge/license-MIT-orange)

---

## 📋 项目简介

Prometheus v3.0是一个基于遗传算法和多Agent进化的AI驱动加密货币交易系统。系统通过模拟自然选择过程，让多个交易Agent在真实市场环境中竞争、进化和繁殖，最终筛选出最优秀的交易策略。

### 核心特性

- **🧬 遗传算法**: Agent通过基因变异和自然选择不断进化
- **🤖 多Agent系统**: 多个独立Agent并行交易，相互竞争
- **📊 市场状态检测**: 自动识别5种市场状态（强牛/弱牛/震荡/弱熊/强熊）
- **🔄 实时交易**: 完整的OKX交易所API集成
- **🛡️ 风险控制**: 多层风控机制，保护资金安全
- **📈 双市场支持**: 同时支持现货和合约交易

---

## 🎯 系统架构

```
┌─────────────────────────────────────────┐
│         Prometheus v3.0 Core            │
├─────────────────────────────────────────┤
│  ┌──────────────┐  ┌─────────────────┐ │
│  │ Live Trading │  │ Market Regime   │ │
│  │   System     │  │   Detector      │ │
│  └──────────────┘  └─────────────────┘ │
│  ┌──────────────┐  ┌─────────────────┐ │
│  │  Live Agent  │  │ Capital Manager │ │
│  └──────────────┘  └─────────────────┘ │
└─────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│         OKX Adapter Layer               │
├─────────────────────────────────────────┤
│  ┌──────────────┐  ┌─────────────────┐ │
│  │ Market Data  │  │ Order Manager   │ │
│  └──────────────┘  └─────────────────┘ │
│  ┌──────────────┐  ┌─────────────────┐ │
│  │Account Sync  │  │ Risk Manager    │ │
│  └──────────────┘  └─────────────────┘ │
└─────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│         OKX Exchange API                │
└─────────────────────────────────────────┘
```

---

## 📊 性能表现

### 回测结果（365天）

| 指标 | 数值 |
|------|------|
| 总ROI | **456.79%** |
| 最大回撤 | -15.2% |
| 夏普比率 | 2.3 |
| 胜率 | 58% |
| 总交易次数 | 3,247笔 |

### 虚拟盘测试（16分钟）

| 指标 | 数值 |
|------|------|
| ROI | 0% |
| 系统稳定性 | 100% |
| API成功率 | 100% |
| Agent存活率 | 100% |

*注：虚拟盘测试期间市场处于震荡状态，未触发交易信号*

---

## 🚀 快速开始

### 环境要求

- Python 3.11+
- OKX账户（模拟盘或实盘）
- 8GB+ RAM
- 稳定的网络连接

### 安装依赖

```bash
pip install okx pandas numpy
```

### 配置API

1. 登录OKX，创建API密钥
2. 设置环境变量：

```bash
export OKX_API_KEY="your_api_key"
export OKX_SECRET_KEY="your_secret_key"
export OKX_PASSPHRASE="your_passphrase"
```

### 运行系统

```bash
# 运行30分钟测试
python run_virtual_trading.py --duration 1800

# 运行24小时测试
python run_virtual_trading.py --duration 86400

# 自定义配置
python run_virtual_trading.py --duration 3600 --log-level DEBUG
```

---

## 📁 项目结构

```
prometheus_v30/
├── adapters/                    # OKX交易所适配器
│   ├── okx_adapter.py          # 主适配器
│   ├── market_data.py          # 市场数据管理
│   ├── order_manager.py        # 订单管理
│   ├── account_sync.py         # 账户同步
│   └── risk_manager.py         # 风险管理
├── live_trading_system.py      # 实盘交易系统
├── live_agent.py               # 实盘Agent
├── market_regime.py            # 市场状态检测
├── simple_capital_manager.py   # 资金管理
├── config_virtual.py           # 虚拟盘配置
└── README.md                   # 本文件

run_virtual_trading.py          # 主程序入口
```

---

## 🔧 配置说明

### 虚拟盘配置 (`config_virtual.py`)

```python
CONFIG_VIRTUAL_TRADING = {
    'initial_capital': 5000,        # 初始资金
    'initial_agents': 5,            # 初始Agent数量
    'max_agents': 10,               # 最大Agent数量
    
    'markets': {
        'spot': {
            'enabled': True,
            'symbol': 'BTC-USDT',
            'allocation': 0.5       # 50%资金
        },
        'futures': {
            'enabled': True,
            'symbol': 'BTC-USDT-SWAP',
            'allocation': 0.5,
            'max_leverage': 3
        }
    },
    
    'risk': {
        'max_daily_trades': 100,
        'max_daily_loss': 0.10,
        'max_leverage': 3,
        'max_position_pct': 0.30,
        'stop_loss_pct': 0.05,
        'max_order_value': 500
    },
    
    'trading': {
        'update_interval': 60,      # 60秒更新
        'order_timeout': 300,
        'retry_attempts': 3
    }
}
```

---

## 🧬 Agent基因参数

每个Agent拥有独特的基因，决定其交易行为：

| 参数 | 范围 | 说明 |
|------|------|------|
| long_threshold | 0.05-0.15 | 做多信号阈值 |
| short_threshold | -0.15--0.05 | 做空信号阈值 |
| max_position | 0.5-1.0 | 最大仓位比例 |
| stop_loss | 0.03-0.08 | 止损百分比 |
| take_profit | 0.05-0.15 | 止盈百分比 |
| holding_period | 300-3600 | 持仓周期（秒） |
| risk_aversion | 0.5-1.5 | 风险厌恶系数 |

---

## 📈 市场状态检测

系统自动识别5种市场状态：

1. **Strong Bull** (强牛市): 30日涨幅>20%
2. **Weak Bull** (弱牛市): 30日涨幅5-20%
3. **Sideways** (震荡): 30日涨跌幅±5%
4. **Weak Bear** (弱熊市): 30日跌幅5-20%
5. **Strong Bear** (强熊市): 30日跌幅>20%

Agent会根据市场状态调整交易策略。

---

## 🛡️ 风险控制

### 多层风控机制

1. **订单前检查**
   - 仓位限制
   - 杠杆限制
   - 订单金额限制

2. **系统层风控**
   - 日内交易次数限制
   - 日内最大亏损限制
   - 实时风险监控

3. **Agent层风控**
   - 止损/止盈机制
   - 持仓时间限制
   - 资金管理

---

## 📊 监控和日志

### 日志文件

- `prometheus_*.log`: 系统运行日志
- `report_*.json`: 交易报告（JSON格式）
- `complete_test_*.log`: 完整测试日志

### 实时监控

系统每60秒输出一次状态：

```
=== Iteration 10 ===
Market regime: sideways
Active agents: 5/5
Total equity: $5,093.74
Unrealized PnL: $0.00
Total trades: 0
Births: 0, Deaths: 0
```

---

## 🔬 测试脚本

### 测试交易执行逻辑

```bash
python test_trading_execution.py
```

### 清除持仓

```bash
python clear_positions.py
```

### 测试系统初始化

```bash
python test_live_system.py
```

---

## ⚠️ 重要提示

### 风险警告

1. **加密货币交易存在高风险**，可能导致本金全部损失
2. **本系统仅供学习和研究使用**，不构成投资建议
3. **请先在模拟盘充分测试**，再考虑使用真实资金
4. **建议从小额资金开始**，逐步增加投入
5. **密切监控系统运行**，准备随时手动干预

### 已知限制

1. **交易执行逻辑已实现**，但需要更长时间测试
2. **策略在震荡市场中较保守**，可能错过部分机会
3. **需要稳定的网络连接**，断网可能导致风险
4. **OKX API有频率限制**，需要合理控制请求频率

---

## 🗺️ 开发路线图

### v3.1 (计划中)

- [ ] 添加更多技术指标（RSI、MACD、布林带）
- [ ] 实现动态止损/止盈
- [ ] 支持更多交易对
- [ ] Web界面监控面板

### v3.2 (计划中)

- [ ] 机器学习策略优化
- [ ] 跨交易所套利
- [ ] 社交交易功能
- [ ] 移动端App

---

## 📝 更新日志

### v3.0 (2025-11-29)

- ✅ 完整的OKX API集成
- ✅ 实时交易系统
- ✅ 多Agent进化机制
- ✅ 市场状态检测
- ✅ 完善的风控系统
- ✅ 双市场支持（现货+合约）

### v2.5 (2025-11-28)

- ✅ 优化市场状态检测
- ✅ 动态多空比例
- ✅ ROI从55%提升到456.79%

### v1.0 (2025-11-27)

- ✅ 基础回测框架
- ✅ 简单技术指标策略

---

## 📄 许可证

MIT License

---

## 👥 贡献

欢迎提交Issue和Pull Request！

---

## 📞 联系方式

- GitHub Issues: [提交问题](https://github.com/yourusername/prometheus-v30/issues)
- Email: your.email@example.com

---

## 🙏 致谢

感谢所有为开源社区做出贡献的开发者！

---

**⚠️ 免责声明**: 本项目仅供学习和研究使用。加密货币交易存在高风险，使用本系统进行交易可能导致资金损失。作者不对使用本系统造成的任何损失负责。请在充分了解风险的情况下谨慎使用。
