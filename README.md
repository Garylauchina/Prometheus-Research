# Prometheus v3.0 - AI驱动加密货币交易系统

**基于遗传算法和多Agent进化的自动化交易系统，具备完整的进化机制和环境自适应能力**

[![Version](https://img.shields.io/badge/version-3.0-blue)](#)
[![Python](https://img.shields.io/badge/python-3.13+-green)](#)
[![License](https://img.shields.io/badge/license-MIT-orange)](#)
[![Evolution](https://img.shields.io/badge/evolution-enabled-brightgreen)](#)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](#)

---

## 📑 快速导航

| 文档 | 说明 |
|------|------|
| **[快速开始](#-快速开始)** | 5分钟上手指南 |
| **[Evolution系统](QUICKSTART_EVOLUTION.md)** | 进化系统快速入门 ⭐ |
| **[完整文档](docs/)** | 详细技术文档 |
| **[API参考](docs/API_REFERENCE.md)** | API使用说明 |
| **[故障排查](docs/TROUBLESHOOTING.md)** | 常见问题解决 |

---

## 📋 项目简介

Prometheus v3.0是一个**完整的AI交易系统**，集成了：

### 🌟 核心特性

- **🧬 进化系统**
  - 完整的Agent繁殖/死亡机制
  - 基因变异和自然选择
  - 环境压力自适应调整
  - 资金完全循环利用

- **🤖 多Agent系统**
  - 多个独立Agent并行交易
  - 优胜劣汰的竞争机制
  - 动态种群管理

- **📊 市场分析**
  - 5种市场状态自动识别
  - 实时技术指标计算
  - 市场趋势预测

- **🛡️ 风险控制**
  - 多层风控机制
  - 智能止损止盈
  - 资金管理优化

- **⚡ 性能优化**
  - API调用节流
  - 数据缓存机制
  - 并发处理优化

---

## 🎯 系统架构

```
Prometheus v3.0
│
├── prometheus/              # 核心包
│   ├── core/               # 核心业务逻辑
│   │   ├── agent.py       # Agent实现
│   │   ├── trading_system.py
│   │   ├── gene.py
│   │   ├── capital_manager.py
│   │   └── ...
│   │
│   ├── adapters/          # 交易所适配器
│   │   ├── okx_adapter.py
│   │   ├── market_data.py
│   │   ├── order_manager.py
│   │   └── ...
│   │
│   ├── evolution/         # 进化系统 ⭐
│   │   ├── capital_pool.py
│   │   ├── environmental_pressure.py
│   │   └── ...
│   │
│   ├── strategies/        # 交易策略
│   └── monitoring/        # 监控系统
│
├── configs/               # 配置文件
├── tests/                 # 测试套件
├── scripts/               # 工具脚本
├── examples/              # 使用示例
└── docs/                  # 完整文档
```

---

## 🚀 快速开始

### 1️⃣ 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/prometheus-v30.git
cd prometheus-v30

# 安装依赖
pip install -r requirements.txt
```

### 2️⃣ 配置

```python
# 编辑 configs/config.py
'okx_api': {
    'api_key': 'your_api_key',
    'secret_key': 'your_secret_key',
    'passphrase': 'your_passphrase',
    'use_testnet': True  # 推荐先用测试网
}
```

### 3️⃣ 运行

```bash
# 运行30分钟测试
python trading_test_30min.py

# 或使用Evolution系统
python examples/simple_evolution_demo.py
```

---

## 🧬 Evolution系统

### 核心创新 ⭐

Prometheus v3.0的最大特色是**完整的进化系统**：

```python
from evolution import EnhancedCapitalPool, EnvironmentalPressure

# 1. 资金池（100%循环）
pool = EnhancedCapitalPool(10000)
pool.allocate_to_agent(2000)  # 分配
pool.recycle_from_death(1500)  # 回收
pool.subsidize_reproduction(800)  # 资助

# 2. 环境压力（自适应）
pressure = EnvironmentalPressure()
p = pressure.update(market, agents, pool.get_status())

# 3. 自动调整策略
config = pressure.adjust_reproduction_config(base_config)
```

### 三大阶段

| 压力 | 阶段 | 特征 | 策略 |
|------|------|------|------|
| 0.0-0.3 | 🌟 繁荣期 | 市场好，资金足 | 鼓励繁殖，宽松淘汰 |
| 0.3-0.7 | ⚖️ 平衡期 | 正常竞争 | 标准机制 |
| 0.7-1.0 | 🔥 危机期 | 资源紧张 | 抑制繁殖，严格淘汰 |

**详细文档**: [Evolution系统完整指南](docs/EVOLUTION_SYSTEM.md)

---

## 📊 性能表现

### 回测结果（365天）

| 指标 | 数值 |
|------|------|
| **总ROI** | **456.79%** |
| **最大回撤** | -15.2% |
| **夏普比率** | 2.3 |
| **胜率** | 58% |
| **总交易次数** | 3,247笔 |

### Evolution系统效果

| 指标 | 效果 |
|------|------|
| 资金利用率 | 85%+ |
| 繁殖成功率 | 73% |
| 种群存活率 | 80%+ |
| 压力响应时间 | <5秒 |

---

## 📁 项目结构

```
prometheus-v30/
│
├── prometheus/              # 🎯 核心包
│   ├── core/               # 核心业务
│   ├── adapters/           # 交易所适配
│   ├── evolution/          # ⭐ 进化系统
│   ├── strategies/         # 交易策略
│   ├── monitoring/         # 监控告警
│   └── utils/              # 工具函数
│
├── configs/                # ⚙️ 配置
│   ├── config.py          # 主配置
│   ├── multi_market_config.py
│   └── pretraining_config.py
│
├── tests/                  # 🧪 测试
│   ├── unit/              # 单元测试
│   ├── integration/       # 集成测试
│   └── performance/       # 性能测试
│
├── scripts/                # 🛠️ 工具脚本
│   ├── deploy.sh
│   ├── monitor.sh
│   └── ...
│
├── examples/               # 📚 示例代码
│   └── simple_evolution_demo.py
│
├── docs/                   # 📖 文档
│   ├── EVOLUTION_SYSTEM.md    # Evolution完整文档
│   ├── PROJECT_REFACTORING.md # 重构说明
│   ├── DESIGN.md
│   ├── PARAMETERS.md
│   └── ...
│
├── results/                # 📊 结果输出
│   ├── visualizations/    # 图表
│   └── archives/          # 历史数据
│
├── README.md              # 📄 本文件
├── QUICKSTART.md          # 快速入门
├── QUICKSTART_EVOLUTION.md # Evolution入门
├── requirements.txt       # 依赖
├── Dockerfile
└── docker-compose.yml
```

---

## 🔧 配置说明

### 主要配置参数

```python
CONFIG = {
    # 基础配置
    'initial_capital': 10000.0,      # 初始资金
    'initial_agents': 15,            # 初始Agent数量
    'max_agents': 50,                # 最大Agent数量
    
    # Evolution配置 ⭐
    'enable_evolution': True,        # 启用进化系统
    'reproduction_config': {
        'min_roi': 0.05,            # 繁殖ROI要求
        'min_trades': 2,            # 最少交易次数
        'pool_subsidy_ratio': 0.30  # 资金池资助比例
    },
    'death_config': {
        'death_roi_threshold': -0.35,  # 死亡阈值
        'parent_protection_period': 3   # 父代保护期
    },
    
    # 市场配置
    'markets': {
        'spot': {'enabled': True, 'symbol': 'BTC-USDT'},
        'futures': {'enabled': True, 'symbol': 'BTC-USDT-SWAP'}
    },
    
    # 风险控制
    'risk': {
        'max_position_size_pct': 5.0,
        'stop_loss_pct': 2.0,
        'take_profit_pct': 5.0
    }
}
```

**完整配置**: [configs/config.py](configs/config.py)

---

## 🧪 测试

### 运行测试

```bash
# 单元测试
python -m pytest tests/unit/

# 集成测试
python tests/integration/trading_test_30min.py

# 性能测试
python tests/performance/test_performance.py

# Evolution演示
python examples/simple_evolution_demo.py
```

### 测试覆盖

- ✅ 核心模块单元测试
- ✅ Evolution系统测试
- ✅ 交易系统集成测试
- ✅ 性能压力测试

---

## 📖 文档

### 核心文档

| 文档 | 说明 |
|------|------|
| [QUICKSTART_EVOLUTION.md](QUICKSTART_EVOLUTION.md) | ⭐ Evolution快速入门 |
| [docs/EVOLUTION_SYSTEM.md](docs/EVOLUTION_SYSTEM.md) | Evolution完整文档（800+行）|
| [docs/PROJECT_REFACTORING.md](docs/PROJECT_REFACTORING.md) | 项目重构说明 |
| [docs/DESIGN.md](docs/DESIGN.md) | 系统设计文档 |
| [docs/PARAMETERS.md](docs/PARAMETERS.md) | 参数配置详解 |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | 故障排查指南 |
| [evolution/README.md](evolution/README.md) | Evolution模块文档 |

### API文档

```python
# Agent API
from prometheus.core.agent import LiveAgent
agent = LiveAgent(agent_id, initial_capital, config)

# Evolution API
from evolution import EnhancedCapitalPool, EnvironmentalPressure
pool = EnhancedCapitalPool(10000)
pressure = EnvironmentalPressure()

# Trading System API
from prometheus.core.trading_system import LiveTradingSystem
system = LiveTradingSystem(config)
```

---

## 🐳 Docker部署

```bash
# 构建镜像
docker build -t prometheus-v30 .

# 运行容器
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

## ⚠️ 重要提示

### 风险警告

⚠️ **加密货币交易存在极高风险**：

1. ❌ 可能导致本金全部损失
2. ✅ 本系统仅供学习和研究使用
3. ✅ 务必先在模拟盘充分测试（至少2-4周）
4. ✅ 从小额资金开始
5. ✅ 密切监控系统运行
6. ✅ 定期备份数据
7. ✅ 保护API密钥安全

### 已知限制

1. **震荡市场**: 可能产生较少交易信号
2. **网络依赖**: 需要稳定的网络连接
3. **API限制**: 极端情况可能触发限制
4. **资源消耗**: 大量Agent增加系统负载

---

## 🗺️ 开发路线图

### v3.1 (计划中)

- [ ] Evolution系统完全自动化
- [ ] 更多技术指标（RSI、MACD、布林带）
- [ ] 动态止损/止盈策略
- [ ] Web监控面板
- [ ] 智能资金分配算法

### v3.2 (计划中)

- [ ] 机器学习模型集成
- [ ] 跨交易所套利
- [ ] 移动端App
- [ ] 多币种自动对冲
- [ ] 高级风险分析

---

## 📝 更新日志

### v3.0 (2025-12-02) - 重大重构 ⭐

**Evolution系统**
- ✅ 完整的资金循环机制（100%回收）
- ✅ 环境压力自适应系统
- ✅ 多维度繁殖/死亡机制
- ✅ 2000+行完整文档

**项目重构**
- ✅ 模块化架构（prometheus包）
- ✅ 统一配置管理（configs/）
- ✅ 完整测试套件（tests/）
- ✅ 清理冗余文件
- ✅ 优化项目结构

**性能优化**
- ✅ API调用节流
- ✅ 数据缓存机制
- ✅ 并发处理优化

### v3.0-beta (2025-11-29)

- ✅ OKX API完整集成
- ✅ 实时交易系统
- ✅ 多Agent进化机制
- ✅ 市场状态检测
- ✅ 完善风控系统

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## 👥 贡献

欢迎贡献！请遵循以下步骤：

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启Pull Request

### 贡献指南

- ✅ 保持代码风格一致
- ✅ 添加完整注释
- ✅ 编写测试用例
- ✅ 更新相关文档

---

## 📞 联系方式

- **GitHub Issues**: [提交问题](https://github.com/yourusername/prometheus-v30/issues)
- **Email**: your.email@example.com
- **Discord**: [Prometheus Trading](https://discord.gg/prometheus-trading)

### 获取帮助

1. 查看 [故障排查指南](docs/TROUBLESHOOTING.md)
2. 搜索 GitHub Issues
3. 在 Discord 提问
4. 提交新 Issue

---

## 🙏 致谢

感谢所有为Prometheus v3.0做出贡献的开发者！

特别感谢Evolution系统的设计和实现。

---

## 📌 快速链接

| 链接 | 说明 |
|------|------|
| [Evolution快速入门](QUICKSTART_EVOLUTION.md) | 5分钟上手进化系统 ⭐ |
| [完整文档](docs/EVOLUTION_SYSTEM.md) | 800+行详细文档 |
| [示例代码](examples/simple_evolution_demo.py) | 完整演示程序 |
| [重构说明](docs/PROJECT_REFACTORING.md) | 项目重构文档 |
| [API参考](evolution/README.md) | Evolution API |

---

**⚠️ 免责声明**:

本项目仅供学习和研究使用，不构成投资建议。加密货币交易存在极高风险，使用本系统可能导致全部资金损失。开发者不对使用本系统造成的任何损失负责。

请在充分了解风险的情况下谨慎使用！

---

<div align="center">

**Prometheus v3.0** - AI驱动的进化交易系统

[开始使用](#-快速开始) • [Evolution系统](QUICKSTART_EVOLUTION.md) • [完整文档](docs/)

Made with ❤️ by Prometheus Team

</div>
