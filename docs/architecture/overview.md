# System Architecture Overview | 系统架构总览

> **Prometheus v7.0 - Multi-Niche Architecture**
> 
> 多生态位架构：让智慧涌现，而非设计智慧

---

## 🎯 核心理念

**Prometheus不是传统的交易系统，而是一个进化引擎。**

我们不设计交易策略，我们创造让策略涌现的条件。

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                      Prophet (先知)                       │
│                    Observer, Not Controller              │
│                  观察者，不是控制者                        │
└─────────────────────────────────────────────────────────┘
                            ↓
                    World Signature
                    (世界签名)
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   Moirai (命运三女神)                      │
│              Birth, Life, Death Management               │
│              出生、生命、死亡管理                           │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  Agent Population (种群)                  │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐           │
│  │ Agent1 │ │ Agent2 │ │ Agent3 │ │ Agent4 │  ...      │
│  │  Gene  │ │  Gene  │ │  Gene  │ │  Gene  │           │
│  └────────┘ └────────┘ └────────┘ └────────┘           │
└─────────────────────────────────────────────────────────┘
                            ↓
                    Market (市场)
                   (BTC 7×24 Trading)
                            ↓
                    Profit / Loss
                    (盈利 / 亏损)
                            ↓
┌─────────────────────────────────────────────────────────┐
│                Natural Selection (自然选择)                │
│                                                           │
│  Good Performers → Survive & Reproduce                   │
│  Poor Performers → Die                                   │
│                                                           │
│  优秀表现者 → 生存并繁殖                                   │
│  差的表现者 → 死亡                                         │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              Experience DB (经验数据库)                    │
│                System's Memory & Wisdom                  │
│                系统的记忆和智慧                            │
└─────────────────────────────────────────────────────────┘
```

---

## 🔑 关键组件

### 1. Prophet（先知）- The Observer

**v6.0及之前**：主动控制者
- 计算最优参数
- 主动干预Agent
- 控制进化方向

**v7.0突破**：被动观察者
- 观察市场状态（World Signature）
- 记录什么有效
- 不主动干预
- "无形之手"

**核心理念**：先知不是上帝，是上帝之手。

### 2. Moirai（命运三女神）- Life Cycle Manager

- **Clotho（克洛托）** - 纺织生命线：创建新Agent
- **Lachesis（拉刻西斯）** - 分配命运：管理Agent生命周期
- **Atropos（阿特洛波斯）** - 剪断生命线：淘汰失败的Agent

**职责**：
- 出生：根据遗传和变异创建新Agent
- 生命：监控Agent表现
- 死亡：执行自然选择
- 繁殖：优秀基因传承

### 3. Agent（智能体）- Autonomous Traders

**基因结构**：
```python
Gene = {
    'trade_frequency': float,      # 交易频率
    'risk_appetite': float,        # 风险偏好
    'position_size': float,        # 仓位大小
    'hold_duration': float,        # 持仓时长
    'signal_sensitivity': float,   # 信号灵敏度
    ...
}
```

**v7.0特性**：零知识训练
- 不给技术指标
- 不给交易规则
- 只给原始价格数据
- 让策略自然涌现

### 4. World Signature（世界签名）

市场的"指纹"，包含：
- 价格波动率
- 成交量特征
- 趋势状态
- 市场情绪

**作用**：
- 让Prophet理解"当前是什么市场"
- 驱动不同策略的适应性
- 记录哪些基因在哪种市场有效

### 5. Experience DB（经验数据库）

系统的"长期记忆"：
- 哪些基因成功过
- 在什么市场条件下
- 盈亏记录
- 演化历史

**作用**：
- 系统学习的基础
- 避免重复失败
- 加速进化过程
- 知识积累

---

## 🔄 进化循环

```
1. Market Update (市场更新)
   ↓
2. Prophet Observes (先知观察)
   → 计算World Signature
   ↓
3. Agents Trade (Agent交易)
   → 根据基因和市场数据决策
   ↓
4. Profit/Loss Feedback (盈亏反馈)
   ↓
5. Natural Selection (自然选择)
   → 盈利者生存
   → 亏损者死亡
   ↓
6. Reproduction (繁殖)
   → 成功基因传承
   → 变异和组合
   ↓
7. Experience Recording (经验记录)
   → 更新ExperienceDB
   ↓
8. New Generation (新一代)
   → 回到步骤1

无限循环，持续进化
```

---

## 🌟 v7.0突破：多生态位架构

### 什么是多生态位？

不是让所有Agent都竞争同一个目标，而是：
- 10种不同的生态位（趋势、均值回归、牛市、熊市...）
- 每个Agent属于一个生态位
- Agent只和同生态位竞争
- Prophet根据市场分配资本到不同生态位

### 为什么？

**生态学原理**：
- 自然界的稳定性来自多样性
- 不同物种占据不同生态位
- 相互制衡，系统稳定

**应用到Prometheus**：
- 不同策略适应不同市场
- 系统不依赖单一策略
- 避免"单基因崩溃"
- 永续进化

---

## 💡 核心哲学

### 不设计策略，创造条件

```
传统方式：                      Prometheus方式：
设计最优策略                    创造进化条件
↓                              ↓
优化参数                        让策略涌现
↓                              ↓
回测验证                        自然选择
↓                              ↓
实盘应用                        持续进化
```

### 拥抱死亡

```
Agent死亡 ≠ 失败
Agent死亡 = 系统学习

死亡提供：
- 选择压力
- 进化动力
- 经验积累
- 种群优化
```

### 观察，不控制

```
Prophet的职责：
✅ 观察市场（World Signature）
✅ 记录有效策略（Experience DB）
✅ 提供环境反馈

Prophet不做：
❌ 设计策略
❌ 控制Agent
❌ 干预进化
```

---

## 📊 系统指标

### 健康指标

- **种群多样性** - 避免单一策略垄断
- **生存率** - 过高或过低都不好
- **繁殖率** - 优秀基因的传播速度
- **经验积累** - Experience DB增长

### 性能指标

- **盈利能力** - 整体资金增长
- **风险控制** - 最大回撤
- **适应性** - 不同市场表现
- **稳定性** - 长期持续性

---

## 🚀 后续阅读

- [Prophet Design](prophet_design.md) - Prophet的详细设计
- [Multi-Niche Architecture](multi_niche.md) - 多生态位架构详解
- [Evolution Mechanism](evolution_mechanism.md) - 进化机制实现
- [Memory System](memory_system.md) - Experience DB设计

---

## 📝 版本历史

- **v7.0** (2025-01) - 多生态位架构，零知识训练
- **v6.0** (2024-12) - 完整进化系统
- **v5.0** (2024-10) - 引入Prophet
- **v4.0** (2024-08) - 基础进化算法
- **v1.0-v3.0** (2024 Q1-Q2) - 早期探索

---

**Last Updated**: 2025-01-11  
**Author**: Prometheus Research Team

[⬅️ Back to Documentation](../README.md)

