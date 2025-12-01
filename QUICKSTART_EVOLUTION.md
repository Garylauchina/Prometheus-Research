# Evolution System 快速入门 🚀

## 5分钟快速上手

### 1️⃣ 导入模块

```python
from evolution import EnhancedCapitalPool, EnvironmentalPressure
```

### 2️⃣ 初始化系统

```python
# 创建资金池（初始$10,000）
pool = EnhancedCapitalPool(10000)

# 创建环境压力系统
pressure = EnvironmentalPressure()
```

### 3️⃣ 使用资金池

```python
# 分配资金
pool.allocate_to_agent(2000)

# 回收资金
pool.recycle_from_death(1500)

# 资助繁殖
pool.subsidize_reproduction(800)

# 查看状态
status = pool.get_status()
print(f"利用率: {status['utilization']:.1%}")
```

### 4️⃣ 使用环境压力

```python
# 更新压力
pressure_value = pressure.update(
    market_features={'high_vol': 0.3, 'fear': 0.2, ...},
    agents=agent_list,
    capital_pool_status=pool.get_status()
)

# 获取当前阶段
phase, name = pressure.get_phase()
print(f"当前: {name}")  # 🌟 繁荣期 / ⚖️ 平衡期 / 🔥 危机期

# 自动调整配置
config = pressure.adjust_reproduction_config({
    'min_roi': 0.05,
    'min_trades': 2,
    'pool_subsidy_ratio': 0.30
})
```

---

## 📚 完整示例

```python
from evolution import EnhancedCapitalPool, EnvironmentalPressure

# 初始化
pool = EnhancedCapitalPool(10000)
pressure = EnvironmentalPressure()
agents = []

# 创建Agent
for i in range(5):
    if pool.allocate_to_agent(1500):
        agent = Agent(i, 1500)
        agents.append(agent)

# 进化周期
def evolution_cycle(market_features):
    # 1. 更新压力
    p = pressure.update(market_features, agents, pool.get_status())
    phase, name = pressure.get_phase()
    print(f"压力: {p:.2%}, {name}")
    
    # 2. 调整配置
    repro_config = pressure.adjust_reproduction_config(base_config)
    death_config = pressure.adjust_death_config(base_config)
    
    # 3. 执行死亡
    for agent in agents:
        if agent.should_die(death_config, agents):
            recycled = agent.die(pool)
            print(f"Agent {agent.id} 死亡，回收${recycled:.2f}")
    
    # 4. 执行繁殖
    for agent in agents:
        if agent.can_reproduce(repro_config):
            child = agent.reproduce(len(agents), repro_config, pool)
            agents.append(child)
            print(f"Agent {child.id} 诞生!")
```

---

## 🎮 运行演示

```bash
# 完整演示程序
python examples/simple_evolution_demo.py

# 输出:
# 🎮 Evolution System 演示程序
# ============================================================
# 📊 资金池系统演示
# ...
# 🌡️ 环境压力系统演示
# ...
# 🚀 完整系统集成演示
# ...
```

---

## 📖 更多文档

| 文档 | 说明 |
|------|------|
| [evolution/README.md](evolution/README.md) | 模块文档 |
| [docs/EVOLUTION_SYSTEM.md](docs/EVOLUTION_SYSTEM.md) | 完整系统文档 |
| [docs/PROJECT_REFACTORING.md](docs/PROJECT_REFACTORING.md) | 重构说明 |
| [examples/simple_evolution_demo.py](examples/simple_evolution_demo.py) | 完整示例代码 |

---

## ⚡ 快速参考

### 资金池API

| 方法 | 用途 | 示例 |
|------|------|------|
| `allocate_to_agent(amount)` | 分配资金 | `pool.allocate_to_agent(2000)` |
| `recycle_from_death(amount)` | 回收资金 | `pool.recycle_from_death(1500)` |
| `subsidize_reproduction(amount)` | 资助繁殖 | `pool.subsidize_reproduction(800)` |
| `get_status()` | 查询状态 | `status = pool.get_status()` |

### 环境压力API

| 方法 | 用途 | 示例 |
|------|------|------|
| `update(market, agents, pool)` | 更新压力 | `p = pressure.update(...)` |
| `get_phase()` | 获取阶段 | `phase, name = pressure.get_phase()` |
| `adjust_reproduction_config(config)` | 调整繁殖 | `config = pressure.adjust_reproduction_config(...)` |
| `adjust_death_config(config)` | 调整死亡 | `config = pressure.adjust_death_config(...)` |

### 压力阶段

| 范围 | 阶段 | 特征 |
|------|------|------|
| 0.0-0.3 | 🌟 繁荣期 | 鼓励繁殖，宽松淘汰 |
| 0.3-0.7 | ⚖️ 平衡期 | 正常竞争 |
| 0.7-1.0 | 🔥 危机期 | 抑制繁殖，严格淘汰 |

---

## 💡 提示

- ✅ 资金池利用率保持在30-90%为最优
- ✅ 每5-10个周期更新一次压力
- ✅ 根据压力动态调整繁殖/死亡参数
- ✅ 监控资金池状态，避免枯竭

---

**快速开始，立即使用！** 🎉

