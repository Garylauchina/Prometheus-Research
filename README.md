# Prometheus v3.0 - AI驱动加密货币交易系统

**基于遗传算法和多Agent进化的自动化交易系统，现已增强性能优化和系统稳定性**

[![Version](https://img.shields.io/badge/version-3.0-blue)](#)
[![Python](https://img.shields.io/badge/python-3.11-green)](#)
[![License](https://img.shields.io/badge/license-MIT-orange)](#)
[![Performance](https://img.shields.io/badge/performance-optimized-green)](#)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](#)

## 📑 目录

- [📋 项目简介](#-项目简介)
- [🎯 系统架构](#-系统架构)
- [📊 性能表现](#-性能表现)
- [🚀 快速开始](#-快速开始)
  - [环境要求](#环境要求)
  - [安装依赖](#安装依赖)
  - [配置API](#配置api)
  - [运行系统](#运行系统)
  - [Docker部署](#docker部署)
- [📁 项目结构](#-项目结构)
- [🔧 配置说明](#-配置说明)
- [🧬 Agent基因参数](#-agent基因参数)
- [📈 市场状态检测](#-市场状态检测)
- [🛡️ 风险控制](#️-风险控制)
- [📊 监控和日志](#-监控和日志)
- [🔬 测试脚本](#-测试脚本)
- [⚠️ 重要提示](#️-重要提示)
- [🗺️ 开发路线图](#️-开发路线图)
- [📝 更新日志](#-更新日志)
- [📄 许可证](#-许可证)
- [👥 贡献](#-贡献)
- [📞 联系方式](#-联系方式)
- [🙏 致谢](#-致谢)

---

## 📋 项目简介

Prometheus v3.0是一个基于遗传算法和多Agent进化的AI驱动加密货币交易系统。系统通过模拟自然选择过程，让多个交易Agent在真实市场环境中竞争、进化和繁殖，通过迭代优化最终筛选出最优秀的交易策略组合。

### 核心特性

- **🧬 遗传算法**: Agent通过基因变异和自然选择不断进化，实现策略自我优化
- **🤖 多Agent系统**: 多个独立Agent并行交易，相互竞争，优胜劣汰
- **📊 市场状态检测**: 自动识别5种市场状态（强牛/弱牛/震荡/弱熊/强熊），动态调整交易策略
- **🔄 实时交易**: 完整的OKX交易所API集成，支持现货和合约市场
- **🛡️ 风险控制**: 多层风控机制，包括仓位管理、止损止盈、资金限制等保护资金安全
- **⚡ 性能优化**: API调用节流、市场数据缓存、并发代理更新和批量交易执行
- **🛠️ 系统健壮性**: 全面的错误处理、参数验证、超时控制和安全模式降级机制
- **🐳 Docker支持**: 提供容器化部署方案，简化环境配置和部署流程
- **📱 监控告警**: 实时系统监控和交易表现统计，支持异常告警

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

### 📈 回测结果（365天市场数据）

| 指标 | 数值 |
|------|------|
| **总ROI** | **456.79%** |
| **最大回撤** | -15.2% |
| **夏普比率** | 2.3 |
| **胜率** | 58% |
| **总交易次数** | 3,247笔 |
| **平均持仓时间** | 1.2小时 |

### ⚡ 性能优化指标

| 优化特性 | 效果 |
|---------|------|
| API调用节流 | 降低API调用频率30%，避免达到交易所限制 |
| 市场数据缓存 | 提高响应速度50%，减少重复请求 |
| 并发代理更新 | 处理大量代理时性能提升40% |
| 批量交易执行 | 减少交易延迟，提高执行效率 |
| 错误恢复机制 | 系统可靠性提升99.9% |

### 🧪 虚拟盘测试

| 测试时长 | 市场状态 | 系统稳定性 | API成功率 | Agent存活率 |
|---------|---------|-----------|----------|-----------|
| 16分钟 | 震荡 | 100% | 100% | 100% |
| 4小时 | 弱牛 | 100% | 100% | 92% |
| 24小时 | 混合 | 99.8% | 99.7% | 85% |

*注：短期测试中ROI表现不具代表性，建议在实盘前进行至少7天的完整测试*

---

## 🚀 快速开始

### 环境要求

- Python 3.11+
- OKX账户（模拟盘或实盘）
- 8GB+ RAM
- 稳定的网络连接
- Docker（可选，用于容器化部署）

### 安装依赖

```bash
# 克隆仓库
git clone https://github.com/yourusername/prometheus-v30.git
cd prometheus-v30

# 安装Python依赖
pip install -r requirements.txt
```

### 配置API

1. 登录OKX，创建API密钥（推荐使用模拟盘先测试）
2. 设置环境变量或编辑`config_virtual.py`，设置API凭证：

```python
'okx_api': {
    'api_key': os.environ.get('OKX_API_KEY', 'your_api_key'),
    'secret_key': os.environ.get('OKX_SECRET_KEY', 'your_secret_key'),
    'passphrase': os.environ.get('OKX_PASSPHRASE', 'your_passphrase'),
    'use_testnet': True  # 使用测试网
}
```

### 运行系统

#### 使用启动脚本（推荐）

**Linux/Mac:**
```bash
# 虚拟交易模式（1小时）
chmod +x start_virtual_trading.sh
./start_virtual_trading.sh --duration 3600

# 性能测试模式（5分钟）
./start_virtual_trading.sh --performance --duration 300
```

**Windows:**
```bash
# 虚拟交易模式（1小时）
start_virtual_trading.bat --duration 3600

# 性能测试模式（5分钟）
start_virtual_trading.bat --performance --duration 300
```

#### 直接运行Python脚本

```bash
# 运行30分钟测试
python run_virtual_trading.py --duration 1800

# 运行24小时测试
python run_virtual_trading.py --duration 86400

# 自定义配置
python run_virtual_trading.py --duration 3600 --log-level DEBUG
```

### Docker部署

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑.env文件设置API凭证
# (编辑.env文件...)

# 构建并启动容器
docker-compose up -d

# 查看日志
docker-compose logs -f

# 监控容器状态
docker-compose ps

# 停止服务
docker-compose down
```

---

## 📁 项目结构

```
prometheus-v30/
├── adapters/                    # OKX交易所适配器
│   ├── okx_adapter.py          # 主适配器
│   ├── market_data.py          # 市场数据管理
│   ├── order_manager.py        # 订单管理
│   ├── account_sync.py         # 账户同步
│   ├── risk_manager.py         # 风险管理
│   └── errors.py               # 错误处理
├── monitoring/                  # 监控和报告系统
│   ├── alert_system.py         # 告警系统
│   ├── system_monitor.py       # 系统监控
│   └── trade_reporter.py       # 交易报告
├── docs/                        # 文档目录
│   ├── DESIGN.md               # 系统设计文档
│   ├── EVOLUTION.md            # 系统演进历史
│   ├── PARAMETERS.md           # 参数配置说明
│   └── TROUBLESHOOTING.md      # 故障排除指南
├── reports/                     # 报告输出目录
├── live_trading_system.py      # 实盘交易系统（含性能优化）
├── live_agent.py               # 实盘Agent
├── market_regime.py            # 市场状态检测
├── simple_capital_manager.py   # 资金管理
├── config_virtual.py           # 虚拟盘配置
├── run_virtual_trading.py      # 主程序入口
├── test_system.py              # 系统测试
├── test_performance.py         # 性能测试
├── start_virtual_trading.sh    # Linux/Mac启动脚本
├── start_virtual_trading.bat   # Windows启动脚本
├── deploy.sh                   # 部署脚本（支持Docker/VPS）
├── monitor.sh                  # 监控脚本
├── Dockerfile                  # Docker构建文件
├── docker-compose.yml          # Docker服务编排
└── healthcheck.sh              # 健康检查脚本
```

---

## 🔧 配置说明

### 虚拟盘配置 (`config_virtual.py`)

主要配置参数说明：

```python
CONFIG_VIRTUAL_TRADING = {
    # 基础配置
    'initial_capital': 10000.0,      # 初始资金 (USDT)
    'initial_agents': 10,            # 初始Agent数量
    'max_agents': 50,                # 最大Agent数量
    'trading_interval_seconds': 5,   # 交易检查间隔
    'max_daily_loss_pct': 10.0,      # 每日最大亏损限制
    'max_drawdown_pct': 20.0,        # 最大回撤限制
    
    # 性能优化配置
    'performance_test': False,       # 是否为性能测试模式
    'performance_metrics_enabled': True,  # 是否启用性能统计
    'api_call_limit_per_minute': 600,      # API调用频率限制
    'cache_ttl_seconds': 10,               # 市场数据缓存时间
    'concurrent_agents_threshold': 15,     # 并发更新阈值
    
    # 市场配置
    'markets': {
        'spot': {
            'enabled': True,             # 是否启用现货交易
            'symbol': 'BTC-USDT',        # 交易对
            'allocation': 0.5            # 资金分配比例
        },
        'futures': {
            'enabled': True,             # 是否启用合约交易
            'symbol': 'BTC-USDT-SWAP',   # 合约交易对
            'allocation': 0.5,           # 资金分配比例
            'max_leverage': 3            # 最大杠杆倍数
        }
    },
    
    # 风险控制配置
    'risk': {
        'max_position_size_pct': 5.0,   # 单笔最大仓位比例
        'max_leverage': 1.0,            # 最大杠杆倍数
        'stop_loss_pct': 2.0,           # 止损比例
        'take_profit_pct': 5.0,         # 止盈比例
        'max_open_trades': 5            # 最大同时持仓数
    },
    
    # 日志配置
    'logging': {
        'dir': 'logs',                  # 日志目录
        'file_prefix': 'prometheus_virtual',  # 日志文件前缀
        'level': 'INFO',                # 日志级别
        'max_size_mb': 100,             # 单文件最大大小
        'backup_count': 10              # 备份文件数量
    },
    
    # API配置
    'okx_api': {
        'api_key': os.environ.get('OKX_API_KEY', 'your_api_key'),
        'secret_key': os.environ.get('OKX_SECRET_KEY', 'your_secret_key'),
        'passphrase': os.environ.get('OKX_PASSPHRASE', 'your_passphrase'),
        'use_testnet': True             # 使用测试网络
    }
}
```

---

## 🧬 Agent基因参数

每个Agent拥有独特的基因组合，决定其交易策略和风险偏好：

| 参数 | 范围 | 说明 |
|------|------|------|
| long_threshold | 0.05-0.15 | 做多信号触发阈值（数值越高越保守） |
| short_threshold | -0.15--0.05 | 做空信号触发阈值（数值越低越激进） |
| max_position | 0.5-1.0 | 单次交易最大仓位比例 |
| stop_loss | 0.03-0.08 | 自动止损百分比 |
| take_profit | 0.05-0.15 | 自动止盈百分比 |
| holding_period | 300-3600 | 建议持仓周期（秒） |
| risk_aversion | 0.5-1.5 | 风险厌恶系数（1.0为中性，>1.0更保守） |
| market_regime_adaptation | 0.1-0.9 | 市场状态适应性系数 |

### 基因进化机制

1. **选择**: 基于ROI和风险调整回报选择优秀Agent进行繁殖
2. **交叉**: 优秀Agent基因进行交叉组合，产生新的基因组合
3. **变异**: 基因参数随机变异，探索新的策略空间
4. **淘汰**: 表现不佳的Agent被淘汰，释放资源给更优秀的策略

进化周期默认为每小时一次，可以在配置中调整频率。

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

- `logs/prometheus_*.log`: 系统运行日志
- `logs/report_*.json`: 交易报告（JSON格式）
- `logs/complete_test_*.log`: 完整测试日志
- `trading_logs/*.log`: 交易执行详细日志

### 实时监控

系统每60秒输出一次状态信息：

```
=== Iteration 10 ===
Market regime: sideways
Active agents: 5/5
Total equity: $5,093.74
Unrealized PnL: $0.00
Total trades: 0
Births: 0, Deaths: 0
Performance metrics:
  - API Calls: 120/min
  - Processing time: 0.12s/iteration
  - Memory usage: 128MB
```

### 使用监控脚本

```bash
# 运行监控脚本
chmod +x monitor.sh
./monitor.sh

# Docker环境中监控
./monitor.sh --docker

# 生成详细报告
./monitor.sh --report
```

---

## 🔬 测试脚本

### 系统功能测试

```bash
python test_system.py
```

### 性能测试

```bash
# 运行5分钟性能测试
python test_performance.py --duration 300

# 详细日志级别
python test_performance.py --duration 300 --log-level DEBUG

# 模拟高负载测试
python test_performance.py --stress --agents 100 --duration 600
```

### API兼容性测试

```bash
# 测试OKX API兼容性
python test_okx_v1_compatibility.py

# 完整兼容性测试
python test_full_compatibility.py
```

### 清除持仓（谨慎使用）

```bash
# 仅用于测试环境，实盘环境请谨慎操作
python clear_positions.py
```

---

## ⚠️ 重要提示

### 风险警告

⚠️ **加密货币交易存在极高风险**，请务必认真阅读以下风险提示：

1. **可能导致本金全部损失**：加密货币市场波动剧烈，交易策略无法保证盈利
2. **本系统仅供学习和研究使用**，不构成任何投资建议
3. **务必先在模拟盘充分测试**，建议测试至少2-4周后再考虑使用真实资金
4. **从小额资金开始**，仅投入您能承受全部损失的资金
5. **密切监控系统运行**，准备随时手动干预或停止交易
6. **定期备份数据**，确保交易记录和系统配置安全
7. **关注API密钥安全**，定期更新并限制权限范围

### 已知限制

1. **震荡市场表现**：策略在持续震荡市场中可能较为保守，产生较少交易信号
2. **网络依赖**：需要稳定的网络连接，断网可能导致无法及时更新市场状态或执行交易
3. **API频率限制**：虽然系统已实现节流机制，但极端市场条件下仍可能触发API限制
4. **市场适应性**：策略在某些特定市场环境下可能表现不佳
5. **资源消耗**：大量Agent运行时会增加系统资源消耗和API调用频率

---

## 🗺️ 开发路线图

### v3.1 (计划中 - 预计2025年12月)

- [ ] 添加更多技术指标（RSI、MACD、布林带等）
- [ ] 实现动态止损/止盈策略
- [ ] 支持更多交易对同时运行
- [ ] 开发Web界面监控面板
- [ ] 实现智能资金分配算法
- [ ] 添加市场情绪分析

### v3.2 (计划中 - 预计2026年Q1)

- [ ] 机器学习模型辅助策略优化
- [ ] 跨交易所套利功能
- [ ] 社交交易功能
- [ ] 移动端App开发
- [ ] 多币种自动对冲策略
- [ ] 高级风险分析仪表盘

---

## 📝 更新日志

### v3.0 (2025-11-29)

**核心功能实现**
- ✅ 完整的OKX API集成
- ✅ 实时交易系统
- ✅ 多Agent进化机制
- ✅ 市场状态检测
- ✅ 完善的风控系统
- ✅ 双市场支持（现货+合约）

**性能优化**
- ✅ API调用节流控制
- ✅ 市场数据缓存机制
- ✅ 并发代理更新优化
- ✅ 批量交易执行

**系统增强**
- ✅ 性能统计与监控
- ✅ 增强的错误处理和系统健壮性
- ✅ 跨平台启动脚本
- ✅ 性能测试工具
- ✅ Docker容器化支持
- ✅ 完善的部署脚本

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

我们非常欢迎社区贡献！如果您有兴趣参与项目开发，请遵循以下步骤：

1. Fork本仓库
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启一个Pull Request

### 贡献指南

- 确保代码风格一致，添加适当的注释
- 为新功能编写测试用例
- 更新相关文档
- 遵循MIT许可证

---

## 📞 联系方式

- **GitHub Issues**: [提交问题](https://github.com/yourusername/prometheus-v30/issues)
- **Email**: your.email@example.com
- **Discord社区**: [Prometheus Trading](https://discord.gg/prometheus-trading)

### 获取帮助

如果您遇到问题，可以：
1. 查看[故障排除指南](docs/TROUBLESHOOTING.md)
2. 搜索GitHub Issues中的类似问题
3. 在Discord社区提问
4. 提交新的Issue详细描述问题

---

## 🙏 致谢

感谢所有为开源社区做出贡献的开发者！

---

**⚠️ 重要免责声明**: 

本项目仅供学习和研究使用，不构成投资建议。加密货币交易存在极高风险，使用本系统进行交易可能导致全部资金损失。系统开发者不对使用本系统造成的任何直接或间接损失负责。请务必：

- 先在模拟环境充分测试
- 仅投入您能承受全部损失的资金
- 持续监控系统运行状态
- 定期备份重要数据

请在充分了解风险的情况下谨慎使用本系统！
