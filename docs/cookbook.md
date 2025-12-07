# API Cookbook（调用速查）

面向“直接抄代码即可用”，覆盖易遗忘/易踩坑的调用。

## OKX 虚拟盘 / 永续合约下单
```python
from prometheus.exchange.okx_api import OKXExchange

okx = OKXExchange(
    api_key="YOUR_KEY",
    secret_key="YOUR_SECRET",
    passphrase="YOUR_PASSPHRASE",
    sandbox=True,               # 顶层启用 sandbox
)

# 市价多/空（双向持仓）
order = okx.place_order(
    symbol="BTC/USDT",
    side="buy",                 # or "sell"
    order_type="market",
    size=0.01,                  # BTC数量，会转换为合约张数
    leverage=5,
    params={
        "tdMode": "cross",
        "posSide": "long",      # long / short
        "instId": "BTC-USDT-SWAP"
    }
)
```

## 双账簿挂载（必备）
```python
from prometheus.ledger.public_ledger import PublicLedger
from prometheus.ledger.agent_account import AgentAccountSystem

public_ledger = PublicLedger()
for agent in agents:
    account = AgentAccountSystem(agent_id=agent.agent_id, public_ledger=public_ledger)
    agent.account = account  # 挂载到Agent
```

## 创世（含 family_id）与移民
```python
from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5

moirai = Moirai(num_families=50)
agents = moirai._genesis_create_agents(agent_count=50, gene_pool=None, capital_per_agent=10000)
moirai.agents = agents

evo = EvolutionManagerV5(moirai=moirai, num_families=50)
new_agents = evo._inject_immigrants(num=5)  # 自动分配 family_id
moirai.agents.extend(new_agents)
```

## 监督循环（标准顺序）
```python
# 前置：已挂载 ledgers / bulletin / diversity_monitor / evolution_manager
for cycle in range(total_cycles):
    moirai.run_cycle()  # 内部：监督→决策→下单→记账→监控→淘汰
    if cycle % evo_interval == 0:
        evo.evolve_population()
```

## 多样性监控阈值（活跃家族已放宽）
```python
from prometheus.core.diversity_monitor import DiversityMonitor

monitor = DiversityMonitor()
metrics = monitor.monitor(agents, cycle=cycle)
# 低于阈值会发出警告/严重警报：gene_entropy, strategy_entropy,
# lineage_entropy, active_families, diversity_score
```

## 标准测试模板入口
使用 `templates/STANDARD_TEST_TEMPLATE.py` 作为新测试骨架，只改业务逻辑，不改骨架，以避免遗漏 Supervisor/双账簿/多样性/进化等关键环节。

