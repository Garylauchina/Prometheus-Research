# 🔥 Prometheus-Quant v5.0 - 下一代AI交易系统

> 💡 **在黑暗中寻找亮光**  
> 📐 **在混沌中寻找规则**  
> 💀→🌱 **在死亡中寻找生命**  
> 💰 **不忘初心，方得始终**

**完全重构的Agent系统 + 双熵遗传学 + 智能决策中枢**

[![Version](https://img.shields.io/badge/version-5.0_dev-blue)](#)
[![Python](https://img.shields.io/badge/python-3.13+-green)](#)
[![License](https://img.shields.io/badge/license-MIT-orange)](#)
[![Architecture](https://img.shields.io/badge/architecture-modular-brightgreen)](#)
[![Status](https://img.shields.io/badge/status-core_complete-yellow)](#)

---

## 🧭 开发者导航（快速入口）

### 🔴 必读：三大铁律（2025-12-07新增）
- **代码三大铁律**：统一封装 + 测试规范 + 不可简化
- **数据封装规范**：`docs/DATA_ENCAPSULATION_STANDARD.md` ⭐ **解决数据接口问题！**
- **账簿问题诊断与修复**：`docs/LEDGER_ISSUES_AND_FIXES.md` ⚠️
- **代码审查清单**：`docs/CODE_REVIEW_CHECKLIST.md` ✅
- **Daimon持有逻辑修复**：`docs/DAIMON_HOLD_FIX_20251207.md` 🆕 **解决交易频率过高！**
- **正确测试示例**：`test_ultimate_v6_CORRECT.py` （使用v6 Facade）

### 📚 架构与模块
- 一页架构/模块索引：`docs/module_registry.md`
- API/调用速查（OKX、双账簿、进化/创世、监督循环）：`docs/cookbook.md`
- 场景化Playbook目录（回测、实盘/虚拟盘、创世与移民、进化调优）：`docs/playbook_index.md`
- 全文档地图（按版本/主题索引）：`docs/DOCUMENT_MAP.md`
- v6 封装/兼容策略草案：`docs/V6_FACADE_PLAN.md`
- 🎲 **随机种子控制指南**：`docs/SEED_CONTROL_GUIDE.md` ⭐ NEW

### 🧪 测试与审计
- 标准测试模板：`templates/STANDARD_TEST_TEMPLATE.py` (v6.0已过时,使用下面的)
- ✅ v6正确测试：`test_ultimate_v6_CORRECT.py` **推荐使用**
- 审计与重写计划：`ARCHITECTURE_AUDIT_2025.md` · `CODE_AUDIT_REPORT.md` · `AUDIT_SUMMARY.md` · `templates/REWRITE_PLAN.md`

---

## 🎯 v5.0核心成就

v5.0是对整个Agent系统的**完全重构**，不向后兼容，追求最优架构设计。

### ⭐ 三大突破

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 模块化Agent架构
   从v4.0的单体决策系统 → v5.0的8大模块协作
   
2. 守护神决策系统（Daimon）
   6个"声音"投票机制 → 完全可解释的决策过程
   
3. 双熵遗传系统
   血统熵 + 基因熵 → 精确监控种群健康度
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 📊 当前状态

| 模块 | 状态 | 完成度 |
|------|------|--------|
| **核心模块开发** | ✅ 完成 | 100% (8/8) |
| **基础测试** | ✅ 通过 | 100% |
| **文档体系** | ✅ 完成 | 100% |
| **系统集成** | ⏳ 进行中 | 20% |
| **完整测试** | 📋 待开始 | 0% |
| **总体进度** | 🚀 | **65%** |

**最新更新**: 2025-12-04  
**分支**: `develop/v5.0`  
**下一步**: 系统集成（Supervisor + EvolutionManager）

---

## 🏗️ v5.0架构

### AgentV5内部结构

```
AgentV5（575行）
├── Lineage（血统）          - 固定，用于生殖隔离
├── Genome（基因组）         - 50维参数，4层解锁
├── Instinct（本能）         - 1级本能 + 5个2级本能
│   ├── fear_of_death        - 死亡恐惧（固定1.0）⭐
│   ├── reproductive_drive   - 繁殖欲望
│   ├── loss_aversion        - 损失厌恶
│   ├── risk_appetite        - 风险偏好
│   ├── curiosity            - 好奇心
│   └── time_preference      - 时间偏好
├── Strategy Pool（策略组）  - 3-5个策略，可切换
│   ├── TrendFollowing       - 趋势跟随
│   ├── MeanReversion        - 均值回归
│   └── GridTrading          - 网格交易
├── PersonalInsights（记忆） - 学习、冥思、顿悟
├── EmotionalState（情绪）   - 4种情绪状态
└── Daimon（守护神）         - 6个声音投票决策中枢 ⭐
```

### Daimon决策系统（核心创新）

```
6个"声音"加权投票机制:
┌─────────────────────────────────────────────────────────────┐
│ 1. Instinct Voice    权重1.0  │ 本能（死亡恐惧优先）      │
│ 2. Experience Voice  权重0.7  │ 历史经验                 │
│ 3. Prophecy Voice    权重0.6  │ 先知预言（战略）⭐        │
│ 4. Strategy Voice    权重0.5  │ 策略分析（战术）⭐        │
│ 5. Genome Voice      权重0.5  │ 基因偏好                 │
│ 6. Emotion Voice     权重0.3  │ 情绪状态                 │
└─────────────────────────────────────────────────────────────┘
                           ↓
            CouncilDecision（最终决策 + 完整推理）
```

**关键设计**: Strategy只提供"评分"，Daimon负责"决策"

---

## 🧬 双熵系统

监控种群健康的"验血系统"：

### 血统熵（Lineage Entropy）
```python
# 衡量家族分布多样性
血统熵 = -Σ(p_i * log(p_i))  # Shannon熵
健康标准: > 0.7 (家族分布均衡)
```

### 基因熵（Gene Entropy）
```python
# 衡量策略参数多样性
基因熵 = Variance(所有参数)  # 方差
健康标准: > 0.5 (参数充分多样)
```

---

## 📚 快速导航

### 核心文档

| 文档 | 内容 | 推荐 |
|------|------|------|
| [V5.0_PROGRESS_SUMMARY.md](V5.0_PROGRESS_SUMMARY.md) | 进度摘要（2分钟） | ⭐⭐⭐⭐⭐ |
| [V5.0_COMPLETION_REPORT.md](docs/V5.0_COMPLETION_REPORT.md) | 完成报告（10分钟） | ⭐⭐⭐⭐ |
| [V5.0_MODULE_REFERENCE.md](docs/V5.0_MODULE_REFERENCE.md) | 模块参考手册 | ⭐⭐⭐⭐⭐ |
| [V5.0_DESIGN_DECISIONS.md](docs/V5.0_DESIGN_DECISIONS.md) | 设计决策（深入） | ⭐⭐⭐ |

### 技术文档

- **架构设计**: [V5.0_DUAL_ENTROPY_DESIGN.md](docs/V5.0_DUAL_ENTROPY_DESIGN.md)
- **开发计划**: [V5.0_DEVELOPMENT_PLAN.md](docs/V5.0_DEVELOPMENT_PLAN.md)
- **启动文档**: [V5.0_DUAL_ENTROPY_KICKOFF.md](V5.0_DUAL_ENTROPY_KICKOFF.md)

---

## 🚀 快速开始（v5.0预览）

### 创建Agent

```python
from prometheus.core.agent_v5 import AgentV5

# 创建创世Agent
agent = AgentV5.create_genesis(
    agent_id="Agent_001",
    initial_capital=10000.0,
    family_id=0,        # 家族ID (0-49)
    num_families=50     # 总家族数
)

print(f"Agent创建成功: {agent.agent_id}")
print(f"策略池: {[s.name for s in agent.strategy_pool]}")
print(f"本能: {agent.instinct.describe_personality()}")
```

### Agent决策

```python
# 准备市场数据
market_data = {
    'price': 90000,
    'ohlcv': [...],
    'volume': 2000,
    'trend': 'bullish',
    'volatility': 0.05,
}

bulletins = {
    'minor_prophecy': {
        'trend': 'bullish',
        'confidence': 0.75,
        'environmental_pressure': 0.2,
    }
}

# Agent自主决策
decision = agent.make_trading_decision(
    market_data=market_data,
    bulletins=bulletins,
    cycle_count=10
)

if decision:
    print(f"决策: {decision['action']}")
    print(f"信心: {decision['confidence']:.1%}")
    print(f"推理: {decision['reasoning']}")
```

### 种群健康检查

```python
from prometheus.core.dual_entropy import PrometheusBloodLab

lab = PrometheusBloodLab(num_families=50)

# "验血"检查健康度
health = lab.test_population(agents)

print(f"血统熵: {health.lineage_entropy:.2f}")
print(f"基因熵: {health.gene_entropy:.2f}")
print(f"健康等级: {health.health_grade}")
```

---

## 🎯 v5.0 vs v4.0 对比

| 维度 | v4.0 | v5.0 | 改进 |
|------|------|------|------|
| **决策系统** | 单一方法 | Daimon（6声音） | ⭐⭐⭐⭐⭐ |
| **策略系统** | 无 | Strategy池 | ⭐⭐⭐⭐⭐ |
| **本能系统** | 混在情绪中 | 独立Instinct | ⭐⭐⭐⭐⭐ |
| **记忆系统** | 无 | PersonalInsights | ⭐⭐⭐⭐⭐ |
| **模块化** | 低 | 高 | ⭐⭐⭐⭐⭐ |
| **可测试性** | 难 | 易 | ⭐⭐⭐⭐⭐ |
| **可解释性** | 黑盒 | 完全透明 | ⭐⭐⭐⭐⭐ |
| **代码质量** | 中 | 高 | ⭐⭐⭐⭐⭐ |

---

## 📦 安装

### 前置要求

- Python 3.13+
- pip 或 conda

### 安装依赖

```bash
# 克隆仓库
git clone https://github.com/Garylauchina/Prometheus-Quant.git
cd Prometheus-Quant

# 切换到v5.0开发分支
git checkout develop/v5.0

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp env.example .env
# 编辑.env文件，填入OKX API密钥
```

---

## 🧪 测试

```bash
# 快速验证测试（推荐）
python tests/test_v5_quick.py

# 完整测试套件
python tests/test_agent_v5_complete.py

# Instinct+Daimon测试
python tests/test_v5_instinct_daimon.py
```

**测试结果**: ✅ 所有基础功能测试通过

---

## 🗺️ 路线图

### v5.0 - 核心系统（当前）✅ 65%

- ✅ 双熵系统（Lineage + Genome）
- ✅ Instinct本能系统
- ✅ Strategy策略系统
- ✅ PersonalInsights记忆系统
- ✅ Daimon守护神决策系统
- ✅ AgentV5完全重构
- ⏳ 系统集成（Supervisor + EvolutionManager）
- 📋 完整测试（500+代）

### v5.1 - 智能增强（计划中）

- Daimon短期记忆
- 自适应权重调整
- 高级风控系统（Sharpe、Drawdown、VaR）
- BulletinBoard记忆功能

### v5.2 - 生态扩展（计划中）

- 期权市场监控
- 多币种支持
- Elysium英灵殿（大灭绝恢复）

### v6.0 - 元认知（展望）

- Daimon元认知能力
- 自我反思和优化
- 模式识别

### v7.0 - LLM增强（展望）

- 外部智能咨询
- 自然语言推理
- 关键决策增强

---

## 📈 性能指标

### v4.3测试结果（722代）

```
运行时长: 约15小时
种群规模: 18个Agent
基因多样性: 0.12+（修复后）
盈利Agent比例: 55.6%
总体PnL: 负（仍在优化）
系统稳定性: ✅ 良好
```

### v5.0目标

- 基因多样性: > 0.15
- 盈利Agent比例: > 60%
- 决策可解释性: 100%
- 模块化程度: 100%

---

## 🤝 贡献

欢迎贡献！v5.0正在积极开发中。

### 当前需要帮助的领域

1. **系统集成** - Supervisor和EvolutionManager适配v5.0
2. **完整测试** - 单元测试覆盖率>80%
3. **性能优化** - 大规模Agent测试
4. **文档完善** - API文档和使用示例

### 如何贡献

```bash
# Fork项目
git clone https://github.com/YOUR_USERNAME/Prometheus-Quant.git

# 创建特性分支
git checkout -b feature/your-feature develop/v5.0

# 提交更改
git commit -m "feat: your feature"

# 推送并创建PR
git push origin feature/your-feature
```

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 📞 联系方式

- **项目主页**: [GitHub - Prometheus-Quant](https://github.com/Garylauchina/Prometheus-Quant)
- **问题反馈**: [Issues](https://github.com/Garylauchina/Prometheus-Quant/issues)
- **开发分支**: `develop/v5.0`

---

## 🌟 致谢

感谢所有为Prometheus项目做出贡献的开发者和测试者！

特别感谢：
- **v4.0**: 建立了完整的进化系统基础
- **v5.0**: 完全重构，追求卓越的代码质量

---

## 📝 更新日志

### v5.0.0-dev (2025-12-04) - 当前

**核心成就**:
- ✅ 8个核心模块完全重构（4537行高质量代码）
- ✅ Daimon守护神决策系统（6声音投票）
- ✅ 双熵遗传系统（血统熵 + 基因熵）
- ✅ 完整测试套件（所有基础测试通过）
- ✅ 5个核心文档（完整的技术文档体系）

**下一步**:
- ⏳ 系统集成（预计12-05完成）
- 📋 完整测试（预计12-06完成）
- 📋 v5.0正式发布（预计12-07）

### v4.3.0 (2025-12-03)

- 修复基因多样性计算BUG
- 添加系统总盈亏显示
- 优化日志输出

### v4.0.0 (2025-11)

- 完整的进化系统
- 多Agent并行交易
- 动态环境适应

---

**🎉 Prometheus v5.0 - 下一代AI交易系统正在构建中！**

欢迎关注我们的开发进展！⭐
