# Helper: attach AgentAccountSystem to agents with PublicLedger
from typing import List
from prometheus.core.ledger_system import AgentAccountSystem


def attach_accounts(agents: List, public_ledger) -> None:
    """
    为一组Agent挂载账簿（幂等）
    - 如已存在 agent.account 则跳过
    - public_ledger 由上层传入（Supervisor/Moirai持有）
    """
    for agent in agents:
        if getattr(agent, "account", None):
            # 已有账户：绝不重建/替换，保持私账引用稳定
            continue

        init_cap = getattr(agent, "initial_capital", 0) or getattr(agent, "current_capital", 0) or 10000.0
        account = AgentAccountSystem(agent_id=agent.agent_id, initial_capital=init_cap, public_ledger=public_ledger)
        agent.account = account
        agent.private_ledger = account.private_ledger
        agent.public_ledger = public_ledger

