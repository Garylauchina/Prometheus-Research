# V6 Facade（初稿）：统一入口，减少多继承与接口分叉
from typing import Optional, Dict, List
import logging
from pathlib import Path
import json
import time
import uuid
from datetime import datetime

from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
from prometheus.core.bulletin_board import BulletinBoard, BulletinType, Priority
# AlphaZero式：移除diversity_monitor
# from prometheus.core.diversity_monitor import DiversityMonitor, DiversityMetrics
from prometheus.exchange.okx_api import OKXExchange
from prometheus.exchange.okx_api import OKXExchange as OKXExchangeType  # alias for type hints
from prometheus.core.ledger_system import PublicLedger, PrivateLedger, LedgerReconciler, TradeRecord, Role
from prometheus.ledger.attach_accounts import attach_accounts
# ✅ v6.0: 资金池系统
from prometheus.core.capital_pool import CapitalPool
# ✅ v6.0: 资金配置系统
from prometheus.config.capital_config import SystemCapitalConfig

# ✅ WorldSignature系统（Prophet的世界认知）
try:
    from prometheus.world_signature.generator import StreamingSignatureGenerator
    from prometheus.world_signature.signature import WorldSignature_V2
    WORLD_SIGNATURE_AVAILABLE = True
except ImportError:
    WORLD_SIGNATURE_AVAILABLE = False
    WorldSignature_V2 = None
    StreamingSignatureGenerator = None

# 轻量回测/Mock 交易封装（接口与 OKXExchange 的主要方法对齐，便于替换）
class _BaseSimExchange:
    def __init__(self, fee_rate: float = 0.0005, slippage: float = 0.0):
        self.fee_rate = fee_rate
        self.slippage = slippage
        self.positions = []  # 简单记录多空持仓
        self.trades = []

    def _fill(self, symbol: str, side: str, amount: float, price: float, agent_id: Optional[str] = None):
        if price <= 0:
            raise ValueError("price must be positive for simulated fill")
        # 简单滑点模型
        fill_price = price * (1 + self.slippage if side == "buy" else 1 - self.slippage)
        fee = abs(amount * fill_price) * self.fee_rate
        trade = {
            "symbol": symbol,
            "side": side,
            "amount": amount,
            "price": fill_price,
            "fee": fee,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
        }
        self.trades.append(trade)
        # 持仓更新（单向持仓的简单示例）
        net = sum(t["amount"] if t["side"] == "buy" else -t["amount"] for t in self.trades)
        self.positions = [{"symbol": symbol, "net": net, "price": fill_price}]
        return trade, fee

    def create_market_order(self, symbol: str, side: str, amount: float, params: Optional[Dict] = None, price: Optional[float] = None, agent_id: Optional[str] = None):
        # 兼容 ccxt 调用习惯，价格可从 params 或显式传入
        p = price or (params.get("price") if params else None)
        if p is None:
            raise ValueError("Sim exchange requires 'price' for market order")
        return self._fill(symbol, side, amount, p, agent_id=agent_id)

    def place_order(self, symbol: str, side: str, order_type: str, amount: float, price: Optional[float] = None, params: Optional[Dict] = None, agent_id: Optional[str] = None):
        # 兼容 OKXExchange.place_order 接口
        if order_type != "market":
            raise NotImplementedError("Sim exchange only supports market orders in this stub")
        if price is None and params:
            price = params.get("price")
        if price is None:
            raise ValueError("Sim exchange requires price for market simulation")
        return self._fill(symbol, side, amount, price, agent_id=agent_id)

    def fetch_positions(self):
        return self.positions

    def close_all_positions(self):
        self.positions = []


class BacktestExchange(_BaseSimExchange):
    def __init__(self, data_source=None, fee_rate: float = 0.0005, slippage: float = 0.0):
        super().__init__(fee_rate=fee_rate, slippage=slippage)
        self.data_source = data_source  # callable(symbol)->price 或对象提供当前价

    def _get_price(self, symbol: str) -> Optional[float]:
        if callable(self.data_source):
            try:
                return self.data_source(symbol)
            except Exception:
                return None
        if isinstance(self.data_source, dict):
            return self.data_source.get(symbol)
        return None

    def create_market_order(self, symbol: str, side: str, amount: float, params: Optional[Dict] = None, price: Optional[float] = None, agent_id: Optional[str] = None):
        p = price or (params.get("price") if params else None) or self._get_price(symbol)
        if p is None:
            raise ValueError("BacktestExchange requires price (param or data_source)")
        return super().create_market_order(symbol, side, amount, params=params, price=p, agent_id=agent_id)


class MockExchange(_BaseSimExchange):
    def __init__(self, scenario=None, fee_rate: float = 0.0005, slippage: float = 0.0, reject_rate: float = 0.0):
        super().__init__(fee_rate=fee_rate, slippage=slippage)
        self.scenario = scenario
        self.reject_rate = reject_rate

    def create_market_order(self, symbol: str, side: str, amount: float, params: Optional[Dict] = None, price: Optional[float] = None, agent_id: Optional[str] = None):
        import random
        if random.random() < self.reject_rate:
            raise Exception("Mock rejection (simulated)")
        p = price or (params.get("price") if params else None)
        if p is None:
            raise ValueError("MockExchange requires price for simulation")
        return super().create_market_order(symbol, side, amount, params=params, price=p, agent_id=agent_id)
from prometheus.core.ledger_system import PublicLedger, PrivateLedger, LedgerReconciler, TradeRecord, Role
from prometheus.ledger.attach_accounts import attach_accounts

logger = logging.getLogger(__name__)


class V6Facade:
    """
    统一入口：
    - init_population: 创世 + 账簿挂载 + 监控/公告初始化
    - run_cycle: 监督→决策→下单→记账→监控→进化（外部可传 market_data/bulletins）
    - maybe_inject_immigrants: 先知策略触发的多样性干预
    - reconcile/close_all: 对账与清仓（调用交易封装）
    - report_status: 输出人口/多样性/资金摘要
    """

    def __init__(self,
                 num_families: int = 50,
                 exchange: Optional[OKXExchange] = None,
                 bulletin_board: Optional[BulletinBoard] = None,
                 match_config: Optional[Dict] = None,
                 elite_ratio: float = 0.2,
                 elimination_rate: float = 0.3,
                 experience_db=None):
        self.bulletin_board = bulletin_board or BulletinBoard(board_name="facade_board")
        
        # ✅ v6.0: 初始化资金池
        self.capital_pool = CapitalPool()
        
        # ✨ v6.0: 初始化经验数据库（智能创世）
        self.experience_db = experience_db
        
        # ✨ v6.0: 初始化先知（Prophet - 战略层）
        from prometheus.core.prophet import Prophet
        self.prophet = Prophet(
            bulletin_board=self.bulletin_board
        )
        
        self.moirai: Moirai = Moirai(
            bulletin_board=self.bulletin_board,
            num_families=num_families,
            exchange=exchange,
            match_config=match_config,
            capital_pool=self.capital_pool,  # ✅ 传递资金池
            experience_db=self.experience_db  # ✨ 传递经验数据库
        )
        self.evolution = EvolutionManagerV5(
            moirai=self.moirai, 
            num_families=num_families,
            elite_ratio=elite_ratio,  # ✅ 传递精英比例
            elimination_ratio=elimination_rate,  # ✅ 传递淘汰率
            capital_pool=self.capital_pool  # ✅ 传递资金池
        )
        # AlphaZero式：移除diversity_monitor
        # self.diversity_monitor = self.evolution.diversity_monitor
        self.public_ledger = PublicLedger()
        # 让 moirai 持有同一公共账簿，供 attach_accounts 使用
        self.moirai.public_ledger = self.public_ledger
        self.exchange = exchange  # 可为 OKXExchange 或 MockExchange，需兼容接口
        # AlphaZero式：移除metrics_history
        # self.metrics_history: List[DiversityMetrics] = []
        
        # ✅ Prophet（先知）- 市场分析专家，生成WorldSignature
        if WORLD_SIGNATURE_AVAILABLE:
            self.prophet = StreamingSignatureGenerator(
                instrument="BTC-USDT",
                macro_window_hours=24,  # 24小时宏观窗口
                micro_window_minutes=5   # 5分钟微观窗口
            )
        else:
            self.prophet = None
            logger.warning("WorldSignature模块未安装，将使用简化市场分析")
        
        # 运行配置
        self.default_cycles = 0
        self.evo_interval = 1
        # 归档配置
        self.run_dir: Optional[Path] = None
        
        # 🎲 随机种子配置（由build_facade设置）
        self.genesis_seed: Optional[int] = None
        self.evolution_seed: Optional[int] = None
        self.seed_config: Dict = {}
        
        # 🎭 场景类型（由build_facade设置）
        self.scenario: str = "backtest"  # backtest/mock/live_demo

    def invest_system_capital(
        self,
        total_amount: float,
        allocation_ratio: float = 1.0,
        purpose: str = "investment",
        reason: str = ""
    ) -> Dict:
        """
        💰 系统注资统一入口（v6.0核心封装）
        
        功能：
        - 创世时调用（allocation_ratio=0.2，80%储备）
        - 中途追加投资（allocation_ratio=1.0，全部可用）
        - 紧急救援（allocation_ratio=1.0，立即可用）
        - Mock模拟场景
        
        Args:
            total_amount: 系统注资总额
            allocation_ratio: 立即可用比例（0.0-1.0）
                             剩余部分进入储备池
            purpose: 注资目的 (genesis/expansion/rescue/mock/adjustment)
            reason: 详细原因说明
        
        Returns:
            dict: {
                "invested": float,           # 本次注资
                "immediate_available": float,# 立即可用
                "reserved": float,           # 进入储备
                "pool_balance": float,       # 资金池余额
                "allocation_ratio": float,   # 分配比例
                "timestamp": str            # 时间戳
            }
        
        示例：
            # 创世注资（20%配资，80%储备）
            result = facade.invest_system_capital(
                total_amount=500000,
                allocation_ratio=0.2,
                purpose="genesis"
            )
            
            # 中途追加投资（100%可用）
            result = facade.invest_system_capital(
                total_amount=100000,
                allocation_ratio=1.0,
                purpose="expansion",
                reason="bull_market_opportunity"
            )
            
            # 紧急救援（100%立即可用）
            result = facade.invest_system_capital(
                total_amount=50000,
                allocation_ratio=1.0,
                purpose="rescue",
                reason="capital_pool_depleted"
            )
        """
        # 参数验证
        if total_amount <= 0:
            raise ValueError(f"total_amount必须 > 0，当前: {total_amount}")
        
        if not (0 <= allocation_ratio <= 1.0):
            raise ValueError(f"allocation_ratio必须在[0, 1]之间，当前: {allocation_ratio}")
        
        # 1. 注资到资金池
        source_label = f"{purpose}_{reason}" if reason else purpose
        self.capital_pool.invest(
            amount=total_amount,
            source=source_label
        )
        
        # 2. 计算分配和储备
        immediate_available = total_amount * allocation_ratio
        reserved = total_amount - immediate_available
        
        # 3. 生成时间戳
        timestamp = datetime.now().isoformat()
        
        # 4. 日志输出
        logger.info(f"💰 系统注资: ${total_amount:,.2f}")
        logger.info(f"   目的: {purpose} {f'({reason})' if reason else ''}")
        logger.info(f"   立即可用: ${immediate_available:,.2f} ({allocation_ratio:.0%})")
        logger.info(f"   进入储备: ${reserved:,.2f} ({(1-allocation_ratio):.0%})")
        logger.info(f"   资金池余额: ${self.capital_pool.available_pool:,.2f}")
        
        # 5. 返回结果
        return {
            "invested": total_amount,
            "immediate_available": immediate_available,
            "reserved": reserved,
            "pool_balance": self.capital_pool.available_pool,
            "allocation_ratio": allocation_ratio,
            "purpose": purpose,
            "reason": reason,
            "timestamp": timestamp
        }
    
    def init_population(
        self, 
        agent_count: int, 
        capital_per_agent: float, 
        full_genome_unlock: bool = False,
        genesis_allocation_ratio: float = 0.2
    ):
        """
        🌱 创世：初始化Agent种群（创世探索方案）
        
        ✅ v6.0流程（使用统一注资接口）：
        1. ✅ 系统注资（调用invest_system_capital）
        2. ✅ 创世时只分配部分资金（默认20%，探索阶段）
        3. ✅ 保留大部分资金作为储备（80%，支持长期演化）
        4. 调用Moirai创建Agents（从资金池分配）
        5. 挂载账簿系统
        6. 初始化适应度
        7. 验证创世质量
        
        Args:
            agent_count: Agent数量
            capital_per_agent: 系统目标规模（每个Agent的理论资金规模）
            full_genome_unlock: 是否解锁所有50个基因参数（激进模式）
            genesis_allocation_ratio: 创世配资比例（默认0.2=20%）
                                     剩余资金留在资金池作为储备
        
        示例：
            agent_count=50, capital_per_agent=10000, genesis_allocation_ratio=0.2
            → 系统注资: $500,000
            → 创世分配: $100,000 (20%)
            → 每个Agent: $2,000
            → 资金池储备: $400,000 (80%)
        """
        # ✨ v6.0: Step 0 - Prophet分析市场并制定创世策略
        # 这一步会让Prophet计算WorldSignature并发布到公告板
        # Moirai稍后会读取这个策略来决定是使用历史基因还是随机创世
        if self.prophet:
            try:
                # Prophet需要初始市场数据，如果有exchange则从exchange获取
                # 如果没有，则跳过（将使用随机创世）
                initial_market_data = None
                if self.exchange and hasattr(self.exchange, 'get_recent_klines'):
                    initial_market_data = self.exchange.get_recent_klines()
                
                if initial_market_data is not None:
                    logger.info("   🔮 Prophet正在分析市场...")
                    self.prophet.genesis_strategy(
                        initial_market_data=initial_market_data,
                        genesis_mode='adaptive'  # 默认智能创世
                    )
                    logger.info("   ✅ Prophet创世策略已发布到公告板")
                else:
                    logger.info("   ⏭️ 无市场数据，跳过Prophet策略（将使用随机创世）")
            except Exception as e:
                logger.warning(f"   ⚠️ Prophet创世策略失败（{e}），将使用随机创世")
        
        # ✅ v6.0: Step 1 - 使用统一注资接口
        total_system_capital = agent_count * capital_per_agent
        
        investment_result = self.invest_system_capital(
            total_amount=total_system_capital,
            allocation_ratio=genesis_allocation_ratio,
            purpose="genesis",
            reason="initial_population"
        )
        
        # ✅ v6.0: Step 2 - 计算每个Agent实际资金
        actual_capital_per_agent = investment_result['immediate_available'] / agent_count
        
        logger.info(f"   每个Agent实际资金: ${actual_capital_per_agent:,.2f}")
        
        # Step 4 - 创建Agents（moirai会从资金池分配实际金额）
        # 此时Moirai会读取公告板上的Prophet策略，决定是否使用智能创世
        agents = self.moirai._genesis_create_agents(
            agent_count=agent_count,
            gene_pool=None,
            capital_per_agent=actual_capital_per_agent,  # ✅ 使用实际配资金额（而非目标规模）
            full_genome_unlock=full_genome_unlock
        )
        self.moirai.agents = agents
        
        # Step 3 - 挂载账簿系统
        attach_accounts(agents, self.public_ledger)
        
        # Step 4 - 初始化适应度
        for agent in agents:
            if not hasattr(agent, "fitness"):
                agent.fitness = 1.0
        
        # Step 5 - 创世验证
        self._validate_genesis(agents)
        
        # ✅ v6.0: 显示资金池状态
        pool_summary = self.capital_pool.get_summary()
        logger.info(f"💰 资金池状态: 已分配${pool_summary['total_allocated']:,.2f}, 余额${pool_summary['available_pool']:,.2f}")
        
        logger.info(f"✅ 创世完成并通过验证：{len(agents)} agents")
        return agents
    
    def _validate_genesis(self, agents):
        """
        验证创世质量
        
        检查项：
        1. 家族分布是否合理
        2. 账簿是否全部挂载
        3. 基因多样性是否足够
        4. 本能多样性是否足够
        """
        if len(agents) == 0:
            raise RuntimeError("❌ 创世失败：Agent数量为0")
        
        # 1. 家族分布检查
        family_counts = {}
        for agent in agents:
            fid = getattr(agent.lineage, 'family_id', None)
            if fid is not None:
                family_counts[fid] = family_counts.get(fid, 0) + 1
        
        active_families = len(family_counts)
        logger.info(f"   📊 家族分布: {active_families}个活跃家族")
        
        if active_families < min(10, len(agents) // 5):
            logger.warning(f"   ⚠️ 家族数量偏低: {active_families}（建议至少{min(10, len(agents)//5)}个）")
        
        # 2. 账簿挂载检查
        no_account = [a for a in agents if not hasattr(a, 'account') or not a.account]
        if no_account:
            logger.error(f"   ❌ {len(no_account)}个Agent未挂载账簿!")
            raise RuntimeError("创世验证失败：账簿挂载不完整")
        
        logger.info(f"   ✅ 账簿挂载: {len(agents)}/{len(agents)}个Agent")
        
        # 3. 基因多样性检查
        import numpy as np
        genome_vectors = []
        for agent in agents:
            if hasattr(agent, 'genome') and hasattr(agent.genome, 'vector'):
                # 只取前3个解锁的基因参数
                genome_vectors.append(tuple(agent.genome.vector[:3].round(2)))
        
        unique_genomes = len(set(genome_vectors))
        genome_diversity = unique_genomes / len(agents) if len(agents) > 0 else 0
        logger.info(f"   📈 基因多样性: {genome_diversity:.1%} ({unique_genomes}/{len(agents)}个独特基因组)")
        
        if genome_diversity < 0.3:
            logger.warning(f"   ⚠️ 基因多样性偏低: {genome_diversity:.1%}（建议>30%）")
        
        # 4. 策略参数多样性检查（AlphaZero式）
        strategy_vectors = []
        for agent in agents:
            if hasattr(agent, 'strategy_params'):
                sp = agent.strategy_params
                strategy_vectors.append((
                    round(sp.position_size_base, 1),
                    round(sp.holding_preference, 1),
                    round(sp.directional_bias, 1)
                ))
        
        unique_strategies = len(set(strategy_vectors))
        strategy_diversity = unique_strategies / len(agents) if len(agents) > 0 else 0
        logger.info(f"   🧠 策略多样性: {strategy_diversity:.1%} ({unique_strategies}/{len(agents)}个独特策略)")
        
        if strategy_diversity < 0.3:
            logger.warning(f"   ⚠️ 策略多样性偏低: {strategy_diversity:.1%}（建议>30%）")
        
        # 5. 整体评估
        overall_score = (
            min(active_families / min(50, len(agents)), 1.0) * 0.3 +
            genome_diversity * 0.35 +
            strategy_diversity * 0.35
        )
        
        logger.info(f"   🎯 创世质量评分: {overall_score:.1%}")
        
        if overall_score < 0.4:
            logger.warning(f"   ⚠️ 创世质量偏低，可能影响进化潜力")
        elif overall_score > 0.7:
            logger.info(f"   🌟 创世质量优秀！")
        
        return True

    def run_cycle(self,
                  market_data: Optional[Dict] = None,
                  bulletins: Optional[Dict] = None,
                  cycle_count: int = 0,
                  scenario: str = "backtest",
                  breeding_tax_rate: float = None):
        """
        ⚖️ Moirai统一执行周期 + 动态税收调控
        
        流程：
        0. 增强market_data（补充必要字段）⭐
        1. 更新公告板（Prophet生成WorldSignature）
        2. Agent决策
        3. Moirai撮合交易（统一入口）
        4. 多样性监控
        5. 进化（含动态税收调控）⭐
        
        Args:
            market_data: 市场数据（至少包含price）
            bulletins: 公告板信息（可选，不提供则自动获取）
            cycle_count: 周期计数
            scenario: 场景类型（backtest/mock/live_demo）
            breeding_tax_rate: 繁殖税率（None=自动计算，目标80%利用率）
        """
        # 0. ⭐ 增强market_data - 统一封装！补充Daimon决策所需的所有字段
        if market_data:
            market_data = self._enrich_market_data(market_data, cycle_count)
        
        # 1. 更新公告板
        if market_data and self.bulletin_board:
            self._update_bulletin_board(market_data, cycle_count)
        
        # 2. 获取公告板信息
        if self.bulletin_board and not bulletins:
            bulletins = self._get_bulletins_for_agents()
        
        # 3. Agent决策 + Moirai撮合
        price = (market_data or {}).get("price")
        if not price or price <= 0:
            logger.warning(f"❌ 价格非法: {price}，跳过本周期")
            return None
        
        decision_count = 0
        match_success_count = 0
        match_fail_count = 0
        
        agents_no_decision_count = 0
        for agent in self.moirai.agents:
            try:
                # 3.1 Agent决策
                decision = agent.make_trading_decision(
                    market_data=market_data or {},
                    bulletins=bulletins or {},
                    cycle_count=cycle_count
                )
                
                if not decision:
                    agents_no_decision_count += 1
                    logger.debug(f"Agent {agent.agent_id}: 无决策（hold或保护期）")
                    continue
                
                decision_count += 1
                logger.debug(f"Agent {agent.agent_id}: 决策={decision.get('action')} 数量={decision.get('amount')}")
                
                # 3.2 补充price到decision（如果Agent没有提供）
                if "price" not in decision or not decision.get("price"):
                    decision["price"] = price
                
                # 3.3 Moirai撮合交易（统一入口，包含风控+记账）
                trade_result = self.moirai.match_trade(
                    agent=agent,
                    decision=decision,
                    market_data=market_data or {},
                    scenario=scenario
                )
                
                if trade_result:
                    if trade_result.get("success"):
                        match_success_count += 1
                    else:
                        match_fail_count += 1
                        logger.debug(f"❌ 交易失败: Agent {agent.agent_id} - {trade_result.get('error', 'UNKNOWN')}")
                
            except Exception as e:
                logger.error(f"❌ Agent {agent.agent_id} 执行周期失败: {e}")
                continue
        
        # 3.4 周期统计
        total_agents = len(self.moirai.agents)
        if cycle_count % 100 == 0 or decision_count > 0:  # 每100个周期或有决策时输出
            logger.info(f"📊 周期 {cycle_count} 交易统计: Agent总数={total_agents}, 无决策={agents_no_decision_count}, 有决策={decision_count}, 成功={match_success_count}, 失败={match_fail_count}")
        
        # 3.5 ✅ 更新Agent统计数据（关键！）
        for agent in self.moirai.agents:
            try:
                # 检查是否有持仓
                has_position = False
                if hasattr(agent, 'account') and agent.account:
                    ledger = agent.account.private_ledger
                    has_position = (
                        (ledger.long_position and ledger.long_position.amount > 0) or
                        (ledger.short_position and ledger.short_position.amount > 0)
                    )
                
                # 更新统计
                agent.update_cycle_statistics(has_position=has_position)
                
                # ✅ 同步current_capital（关键！）
                if hasattr(agent, 'account') and agent.account:
                    agent.current_capital = agent.account.private_ledger.virtual_capital
                    
            except Exception as e:
                logger.error(f"更新Agent {agent.agent_id} 统计数据失败: {e}")
        
        # AlphaZero式：移除多样性监控
        # metrics = self.diversity_monitor.monitor(self.moirai.agents, cycle_count)
        # self.metrics_history.append(metrics)
        
        # 5. 进化（税收机制已封装在Moirai内部）
        if self.evo_interval and self.evo_interval > 0:
            if cycle_count % self.evo_interval == 0:
                if hasattr(self.evolution, "run_evolution_cycle"):
                    self.evolution.run_evolution_cycle(
                        current_price=price
                        # ❌ breeding_tax_rate已废除，税收由Moirai内部管理
                    )
                elif hasattr(self.evolution, "evolve_population"):
                    self.evolution.evolve_population()
        
        # AlphaZero式：不再返回metrics
        return None

    # ========== 数据增强（统一封装）==========
    def _enrich_market_data(self, market_data: Dict, cycle_count: int) -> Dict:
        """
        ⭐ 增强market_data - 统一数据封装的核心方法！
        
        **问题根源**：Daimon的各个voice需要特定字段（trend, volatility等），
        但外部调用者不知道需要提供哪些字段，导致决策失败。
        
        **解决方案**：外部只需提供最基本的 {"price": xxx}，
        Facade自动补充所有必要字段！
        
        补充字段：
        - trend: 趋势（bullish/bearish/neutral）
        - price_change: 价格变化率
        - volatility: 波动率
        - cycle: 周期数
        
        Returns:
            Dict: 增强后的market_data，包含所有Daimon决策所需字段
        """
        enriched = market_data.copy()
        
        # 1. 验证price字段
        if "price" not in enriched or enriched["price"] is None or enriched["price"] <= 0:
            logger.error(f"❌ market_data必须包含有效的price字段！当前: {enriched.get('price')}")
            return enriched
        
        current_price = enriched["price"]
        
        # 2. 补充cycle（如果没有）
        if "cycle" not in enriched:
            enriched["cycle"] = cycle_count
        
        # 3. 计算trend和price_change（如果没有）
        if "trend" not in enriched or "price_change" not in enriched:
            if hasattr(self, '_price_history') and len(self._price_history) > 0:
                prev_price = self._price_history[-1]
                price_change = (current_price - prev_price) / prev_price
                
                # 趋势判断（阈值1%）
                if price_change > 0.01:
                    trend = 'bullish'
                elif price_change < -0.01:
                    trend = 'bearish'
                else:
                    trend = 'neutral'
                
                enriched["price_change"] = price_change
                enriched["trend"] = trend
            else:
                # 第一个周期，默认值
                enriched["price_change"] = 0.0
                enriched["trend"] = 'neutral'
            
            # 更新价格历史（保留最近100个）
            if not hasattr(self, '_price_history'):
                self._price_history = []
            self._price_history.append(current_price)
            if len(self._price_history) > 100:
                self._price_history.pop(0)
        
        # 4. 补充volatility（如果没有）
        if "volatility" not in enriched:
            if hasattr(self, '_price_history') and len(self._price_history) > 10:
                # 从历史价格计算波动率（20期标准差）
                import numpy as np
                prices = self._price_history[-20:]
                returns = np.diff(prices) / prices[:-1]
                enriched["volatility"] = float(np.std(returns)) if len(returns) > 0 else 0.02
            else:
                # 默认波动率2%
                enriched["volatility"] = 0.02
        
        return enriched

    def _update_bulletin_board(self, market_data: Dict, cycle_count: int):
        """
        通过Prophet生成WorldSignature并发布到公告板
        
        ⚠️ 数据封装原则:
        1. 原始市场数据只给Prophet
        2. Prophet生成WorldSignature（世界认知）
        3. WorldSignature发布到公告板（公共信息）
        4. Agent只接收公告板信息，看不到原始数据
        
        Args:
            market_data: 原始市场数据（只给Prophet）
            cycle_count: 当前周期数
        """
        # ========== Prophet生成WorldSignature ==========
        if self.prophet and WORLD_SIGNATURE_AVAILABLE:
            try:
                # Prophet分析市场，生成世界签名
                world_signature = self.prophet.update(
                    market_data=market_data,
                    funding_rate=market_data.get('funding_rate', 0.0),
                    open_interest=market_data.get('open_interest', 0.0)
                )
                
                # 发布WorldSignature到公告板
                content = f"世界签名: {world_signature.to_compact_string()}"
                bulletin = self.bulletin_board.post(
                    content=content,
                    type=BulletinType.MASTERMIND_STRATEGIC,
                    priority=Priority.HIGH,
                    source='Prophet'
                )
                
                # 在bulletin的元数据中保存完整的WorldSignature
                # ⚠️ 注意: 只保存在公告板，不直接传给Agent
                if hasattr(bulletin, 'tags'):
                    bulletin.tags = ['world_signature']
                if hasattr(bulletin, 'sentiment'):
                    # 根据WorldSignature的评分设置情绪
                    if world_signature.opportunity_index > 0.7:
                        bulletin.sentiment = 'positive'
                    elif world_signature.danger_index > 0.7:
                        bulletin.sentiment = 'negative'
                    else:
                        bulletin.sentiment = 'neutral'
                
                # 保存WorldSignature对象供Agent获取（通过公告板）
                if not hasattr(self, '_latest_world_signature'):
                    self._latest_world_signature = {}
                self._latest_world_signature[cycle_count] = world_signature
                
            except Exception as e:
                logger.warning(f"Prophet生成WorldSignature失败: {e}")
                # 降级到简单模式
                self._simple_market_bulletin(market_data, cycle_count)
        else:
            # 无Prophet时使用简化公告
            self._simple_market_bulletin(market_data, cycle_count)
        
        # 周期性战略公告（每30个周期）
        if cycle_count % 30 == 0:
            content = f"周期 {cycle_count}: 系统运行正常，种群健康度监控中"
            self.bulletin_board.post(
                content=content,
                type=BulletinType.MASTERMIND_STRATEGIC,
                priority=Priority.MEDIUM,
                source='System'
            )
    
    def _simple_market_bulletin(self, market_data: Dict, cycle_count: int):
        """
        简化市场公告（当Prophet不可用时）
        """
        price = market_data.get('price', 0)
        price_change = market_data.get('price_change', 0)
        
        if abs(price_change) > 0.05:  # 5%以上变化
            sentiment = 'positive' if price_change > 0 else 'negative'
            impact = 'high' if abs(price_change) > 0.10 else 'medium'
            
            content = f"市场{'暴涨' if price_change > 0 else '暴跌'} {abs(price_change):.1%}，当前价格 ${price:.2f}"
            self.bulletin_board.post(
                content=content,
                type=BulletinType.MARKET_EVENT,
                sentiment=sentiment,
                impact_level=impact,
                priority=Priority.HIGH if impact == 'high' else Priority.MEDIUM,
                source='Market'
            )
    
    def _get_bulletins_for_agents(self) -> Dict:
        """
        从公告板获取最新公告，转换为Agent可用格式
        
        ⚠️ 数据封装原则:
        1. Agent只接收公共信息（公告板）
        2. 不传递原始市场数据
        3. 不传递其他Agent的私有信息
        
        Returns:
            Dict: 公告字典，包含WorldSignature（如果有）
        """
        recent_bulletins = self.bulletin_board.get_recent(hours=1)
        
        # 转换为简化格式
        bulletins = {
            'market_events': [],
            'strategic': [],
            'risk_warnings': [],
            'world_signature': None,  # ✅ Prophet的世界认知
            'count': len(recent_bulletins)
        }
        
        for b in recent_bulletins:
            bulletin_data = {
                'content': b.content,
                'priority': b.priority.value if hasattr(b.priority, 'value') else b.priority,
                'sentiment': getattr(b, 'sentiment', None),
                'impact': getattr(b, 'impact_level', None)
            }
            
            # 检查是否是WorldSignature公告
            tags = getattr(b, 'tags', [])
            if 'world_signature' in tags and hasattr(self, '_latest_world_signature'):
                # ✅ 传递Prophet的世界认知（公共信息）
                # 只传递必要字段，不是完整对象（数据封装）
                if self._latest_world_signature:
                    latest_sig = list(self._latest_world_signature.values())[-1]
                    bulletins['world_signature'] = {
                        'regime_id': latest_sig.regime_id,
                        'regime_confidence': latest_sig.regime_confidence,
                        'danger_index': latest_sig.danger_index,
                        'opportunity_index': latest_sig.opportunity_index,
                        'stability_score': latest_sig.stability_score,
                        'novelty_score': latest_sig.novelty_score,
                        # ❌ 不传递: macro_vec, micro_vec (原始特征，Agent不需要)
                    }
            
            # 根据类型分类
            btype = b.type.value if hasattr(b.type, 'value') else b.type
            if btype == 'market':
                bulletins['market_events'].append(bulletin_data)
            elif btype == 'global':
                bulletins['strategic'].append(bulletin_data)
            elif btype == 'system':
                bulletins['risk_warnings'].append(bulletin_data)
        
        return bulletins
    
    def maybe_inject_immigrants(self, metrics: Optional[Dict] = None, force: bool = False):
        """AlphaZero式：不使用Immigration机制"""
        logger.debug("AlphaZero式：Immigration已禁用")
        return []

    def run(self, total_cycles: int, market_feed=None, evo_interval: int = 1):
        """
        简单主循环：按 total_cycles 运行，可选外部 market_feed 生成器
        market_feed: callable(cycle) -> market_data, bulletins
        """
        self.evo_interval = max(1, evo_interval)
        for c in range(1, total_cycles + 1):
            md, bb = ({}, {}) if market_feed is None else market_feed(c)
            result = self.run_cycle(
                market_data=md, 
                bulletins=bb, 
                cycle_count=c,
                scenario=self.scenario  # ✅ 传递场景类型
            )
            # AlphaZero式：不再记录diversity metrics
            # if result:
            #     logger.debug(f"cycle {c}: diversity_score={result.diversity_score:.3f}")

    def reconcile(self, current_price: float = 0):
        """
        完整对账：Agent级 + 系统级
        
        Args:
            current_price: 当前市场价格（用于计算未实现盈亏）
        
        Returns:
            dict: {
                "all_passed": bool,          # 是否所有对账都通过
                "agent_reconcile": {...},    # Agent级对账结果
                "system_reconcile": {...}    # 系统级对账结果
            }
        """
        # ========== Agent级对账（私有 vs 公共账簿）==========
        rec = LedgerReconciler()
        details = {}
        passed_count = 0
        failed_count = 0
        
        for agent in getattr(self.moirai, "agents", []):
            acct = getattr(agent, "account", None)
            if not acct or not hasattr(acct, "private_ledger"):
                logger.warning(f"对账跳过: Agent {agent.agent_id} 无account/private_ledger")
                continue
            
            private_ledger = acct.private_ledger
            public_ledger = self.public_ledger
            actions = rec.reconcile_all(agent.agent_id, private_ledger, public_ledger, okx_position=None)
            
            # 判断是否通过：actions为空或只包含NO_ACTION
            action_values = [a.value for a in actions]
            passed = (len(actions) == 0 or 
                     all(a == ReconciliationAction.NO_ACTION.value for a in action_values))
            
            if passed:
                passed_count += 1
            else:
                failed_count += 1
                logger.warning(f"⚠️ Agent级对账未通过: {agent.agent_id} - 修复动作: {action_values}")
            
            details[agent.agent_id] = {
                "passed": passed,
                "actions": action_values
            }
        
        total = passed_count + failed_count
        agent_all_passed = (failed_count == 0 and total > 0)
        
        agent_reconcile = {
            "all_passed": agent_all_passed,
            "total_agents": total,
            "passed_agents": passed_count,
            "failed_agents": failed_count,
            "details": details
        }
        
        if agent_all_passed:
            logger.info(f"✅ Agent级对账全部通过: {total} agents")
        else:
            logger.warning(f"⚠️ Agent级对账发现问题: {failed_count}/{total} agents 未通过")
        
        # ========== 系统级对账（资金守恒验证）==========
        system_reconcile = self.capital_pool.reconcile(
            agents=self.moirai.agents,
            current_price=current_price
        )
        
        # ========== 综合判断 ==========
        all_passed = agent_all_passed and system_reconcile["passed"]
        
        if all_passed:
            logger.info("🎉 对账全部通过（Agent级 + 系统级）")
        else:
            logger.error("❌ 对账失败:")
            if not agent_all_passed:
                logger.error(f"   - Agent级: {failed_count}/{total} agents 未通过")
            if not system_reconcile["passed"]:
                logger.error(f"   - 系统级: 资金差异 ${system_reconcile['discrepancy']:.2f}")
        
        return {
            "all_passed": all_passed,
            "agent_reconcile": agent_reconcile,
            "system_reconcile": system_reconcile
        }

    def close_all(self):
        """
        清仓接口：调用交易封装 close_all_positions（如支持）。
        """
        if not self.exchange:
            logger.warning("清仓跳过：未配置交易封装")
            return
        if hasattr(self.exchange, "close_all_positions"):
            self.exchange.close_all_positions()
            logger.info("已调用交易封装清仓")
        else:
            logger.warning("清仓跳过：交易封装未提供 close_all_positions")
    
    def get_capital_report(self, current_price: float = 0) -> Dict:
        """
        生成完整的资金统计报告
        
        Args:
            current_price: 当前市场价格（用于计算未实现盈亏）
        
        Returns:
            dict: {
                "system": {
                    "total_invested": float,      # 系统总注资
                    "total_agent_capital": float, # Agent总资金（实盈+浮盈）
                    "pool_balance": float,        # 资金池余额
                    "system_total": float,        # 系统总资金
                    "roi_pct": float              # 系统ROI
                },
                "agents": {
                    "total_count": int,
                    "total_initial": float,       # Agent初始资金总和
                    "total_realized": float,      # 已实现总资金
                    "total_unrealized_pnl": float,# 未实现盈亏
                    "avg_roi_pct": float          # 平均ROI
                },
                "pool": {
                    "total_invested": float,      # 总注资
                    "available": float,           # 可用余额
                    "allocated": float,           # 累计分配
                    "reclaimed": float,           # 累计回收
                    "net_flow": float             # 净流出
                }
            }
        """
        # 1. 资金池统计
        pool_summary = self.capital_pool.get_summary()
        
        # 2. Agent统计
        total_count = len(self.moirai.agents)
        total_initial = 0.0
        total_realized = 0.0
        total_unrealized_pnl = 0.0
        
        for agent in self.moirai.agents:
            if hasattr(agent, 'account') and agent.account:
                total_initial += agent.account.private_ledger.initial_capital
                total_realized += agent.account.private_ledger.virtual_capital
                
                if current_price > 0 and hasattr(agent, 'calculate_unrealized_pnl'):
                    total_unrealized_pnl += agent.calculate_unrealized_pnl(current_price)
        
        # 3. 系统级统计
        total_agent_capital = total_realized + total_unrealized_pnl
        system_total = total_agent_capital + pool_summary['available_pool']
        
        system_roi = 0.0
        if pool_summary['total_invested'] > 0:
            system_roi = ((system_total - pool_summary['total_invested']) / 
                         pool_summary['total_invested'] * 100)
        
        avg_roi = 0.0
        if total_count > 0 and total_initial > 0:
            avg_roi = ((total_agent_capital - total_initial) / total_initial * 100)
        
        return {
            "system": {
                "total_invested": pool_summary['total_invested'],
                "total_agent_capital": total_agent_capital,
                "pool_balance": pool_summary['available_pool'],
                "system_total": system_total,
                "roi_pct": system_roi
            },
            "agents": {
                "total_count": total_count,
                "total_initial": total_initial,
                "total_realized": total_realized,
                "total_unrealized_pnl": total_unrealized_pnl,
                "avg_roi_pct": avg_roi
            },
            "pool": {
                "total_invested": pool_summary['total_invested'],
                "available": pool_summary['available_pool'],
                "allocated": pool_summary['total_allocated'],
                "reclaimed": pool_summary['total_reclaimed'],
                "net_flow": pool_summary['net_flow']
            }
        }

    def report_status(self) -> Dict:
        """
        获取系统状态报告
        
        Returns:
            Dict: 包含Agent数量、资金、交易、多样性等信息
        """
        agents = self.moirai.agents
        
        # 统计Agent数量
        agent_count = len(agents)
        
        # 统计总资金和平均资金
        total_capital = 0
        for agent in agents:
            if hasattr(agent, 'account') and agent.account:
                total_capital += agent.account.private_ledger.virtual_capital
            elif hasattr(agent, 'current_capital'):
                total_capital += agent.current_capital
        
        avg_capital = total_capital / agent_count if agent_count > 0 else 0
        
        # 统计总交易数
        total_trades = 0
        for agent in agents:
            if hasattr(agent, 'account') and agent.account:
                total_trades += len(agent.account.private_ledger.trade_history)
        
        # 多样性评分
        # AlphaZero式：不再记录diversity metrics
        diversity_score = 0
        
        return {
            "agent_count": agent_count,
            "total_capital": total_capital,
            "avg_capital": avg_capital,
            "total_trades": total_trades,
            "diversity_score": diversity_score,
            "families": self.moirai.num_families if hasattr(self.moirai, "num_families") else 0
        }

    # ========== 交易记录写入 ==========
    def _record_trade_to_ledgers(self, agent, trade: Dict, is_real: bool = False):
        """
        将模拟/回测成交写入私账与公账，便于对账
        """
        trade_id = str(uuid.uuid4())
        trade_type = trade.get("side")
        amount = abs(trade.get("amount", 0))
        price = trade.get("price", 0)
        if not trade_type or amount <= 0 or price <= 0:
            return
        position_side = "long" if trade_type in ("buy", "cover") else "short"
        tr = TradeRecord(
            agent_id=agent.agent_id,
            trade_id=trade_id,
            trade_type=trade_type,
            amount=amount,
            price=price,
            timestamp=datetime.now(),
            confidence=trade.get("confidence", 1.0),
            pnl=None,
            is_real=is_real,
            position_side=position_side,
            okx_order_id=None
        )
        # 写私账
        acct = getattr(agent, "account", None)
        if acct and getattr(acct, "private_ledger", None):
            try:
                acct.private_ledger.record_trade(tr, caller_role=Role.SUPERVISOR)
            except Exception as e:
                logger.warning(f"私账记账失败 {agent.agent_id}: {e}")
        # 写公账
        try:
            self.public_ledger.record_trade(tr, caller_role=Role.SUPERVISOR)
        except Exception as e:
            logger.warning(f"公共账簿记账失败 {agent.agent_id}: {e}")

    # ========== 模拟撮合并记账 ==========
    def simulate_and_record(self, agent, symbol: str, side: str, amount: float, price: float):
        """
        针对回测/Mock场景：直接使用撮合结果写入账簿
        """
        sim_trade = {
            "symbol": symbol,
            "side": side,
            "amount": amount,
            "price": price,
            "fee": abs(amount * price) * 0.0005,
            "confidence": 1.0
        }
        self._record_trade_to_ledgers(agent, sim_trade, is_real=False)
        return sim_trade

    # ========== 结果归档相关 ==========
    def _init_run_dir(self, mode: str, scenario: str = "default"):
        ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        base = Path("results") / mode / ts[:8] / f"{scenario}_{ts}"
        base.mkdir(parents=True, exist_ok=True)
        (base / "artifacts").mkdir(exist_ok=True)
        self.run_dir = base
        logger.info(f"结果归档目录: {base}")
        return base

    def save_config(self, cfg: Dict):
        if not self.run_dir:
            return
        path = self.run_dir / "config.json"
        with open(path, "w") as f:
            json.dump(cfg, f, indent=2)
        logger.info(f"已保存配置: {path}")

    def save_metrics(self, metrics: Dict):
        if not self.run_dir:
            return
        path = self.run_dir / "metrics.json"
        with open(path, "w") as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"已保存指标: {path}")
    
    # ========== v6.0 市场数据生成统一入口（Stage 1.1封装改进）==========
    def generate_training_market(
        self,
        market_type: str = 'stage1_switching',
        total_bars: int = 5000,
        structures: list = None,
        bars_per_structure: int = 300,
        random_seed: int = None,
        save_path: str = None
    ) -> 'pd.DataFrame':
        """
        生成训练市场数据（v6.0统一封装入口）
        
        封装原则（三大铁律第1条）：
        1. 统一入口，禁止旁路调用
        2. 所有市场数据生成通过此方法
        3. 支持多种市场类型和配置
        
        Args:
            market_type: 市场类型
                - 'stage1_switching': Stage 1结构切换市场（默认）
                - 'bull': 纯牛市
                - 'bear': 纯熊市
                - 'range': 纯震荡
                - 'fake_breakout': 纯假突破
            total_bars: 总bars数
            structures: 结构序列（仅stage1_switching需要）
            bars_per_structure: 每个结构bars数
            random_seed: 随机种子（可复现性）
            save_path: 保存路径（可选）
            
        Returns:
            pd.DataFrame: 市场数据（包含timestamp/open/high/low/close/volume/structure_type）
            
        示例：
            >>> facade = V6Facade(...)
            >>> # 生成Stage 1标准市场
            >>> market_data = facade.generate_training_market(
            ...     market_type='stage1_switching',
            ...     total_bars=5000,
            ...     random_seed=42
            ... )
            >>> # 运行训练
            >>> result = facade.run_mock_training(market_data, config)
        """
        import pandas as pd
        from prometheus.utils.market_generator import MarketStructureGenerator
        
        logger.info("="*80)
        logger.info("市场数据生成 - v6.0统一封装入口")
        logger.info("="*80)
        logger.info(f"市场类型: {market_type}")
        logger.info(f"总bars数: {total_bars}")
        
        if market_type == 'stage1_switching':
            # Stage 1: 结构切换市场
            generator = MarketStructureGenerator(
                base_price=40000.0,
                base_volatility=0.003,  # 0.3% ATR
                random_seed=random_seed
            )
            
            if structures is None:
                structures = ['trend_up', 'range', 'trend_down', 'fake_breakout']
            
            logger.info(f"结构序列: {structures}")
            logger.info(f"每结构bars: {bars_per_structure}")
            
            market_data = generator.generate_switching_market(
                structures=structures,
                bars_per_structure=bars_per_structure,
                total_bars=total_bars,
                structure_cycle=True
            )
            
        elif market_type == 'bull':
            # 纯牛市
            generator = MarketStructureGenerator(
                base_price=40000.0,
                base_volatility=0.003,
                random_seed=random_seed
            )
            market_data = generator.generate_switching_market(
                structures=['trend_up'],
                bars_per_structure=total_bars,
                total_bars=total_bars,
                structure_cycle=False
            )
            
        elif market_type == 'bear':
            # 纯熊市
            generator = MarketStructureGenerator(
                base_price=40000.0,
                base_volatility=0.003,
                random_seed=random_seed
            )
            market_data = generator.generate_switching_market(
                structures=['trend_down'],
                bars_per_structure=total_bars,
                total_bars=total_bars,
                structure_cycle=False
            )
            
        elif market_type == 'range':
            # 纯震荡
            generator = MarketStructureGenerator(
                base_price=40000.0,
                base_volatility=0.003,
                random_seed=random_seed
            )
            market_data = generator.generate_switching_market(
                structures=['range'],
                bars_per_structure=total_bars,
                total_bars=total_bars,
                structure_cycle=False
            )
            
        elif market_type == 'fake_breakout':
            # 纯假突破
            generator = MarketStructureGenerator(
                base_price=40000.0,
                base_volatility=0.003,
                random_seed=random_seed
            )
            market_data = generator.generate_switching_market(
                structures=['fake_breakout'],
                bars_per_structure=total_bars,
                total_bars=total_bars,
                structure_cycle=False
            )
            
        else:
            raise ValueError(f"不支持的市场类型: {market_type}")
        
        # 保存数据（可选）
        if save_path:
            market_data.to_csv(save_path, index=False)
            logger.info(f"✅ 市场数据已保存: {save_path}")
        
        logger.info(f"✅ 市场数据生成完成: {len(market_data)} bars")
        logger.info(f"   价格范围: [{market_data['low'].min():.2f}, {market_data['high'].max():.2f}]")
        
        return market_data
    
    # ========== v6.0 Mock训练统一入口 ==========
    def run_mock_training(
        self,
        market_data: 'pd.DataFrame',
        config: 'MockTrainingConfig'
    ) -> 'MockTrainingResult':
        """
        运行Mock训练（v6.0统一封装入口）
        
        严格封装原则（三大铁律第1条）：
        1. 所有底层模块均在内部创建和管理
        2. 不对外暴露任何底层模块的引用
        3. 只返回结果数据，不返回模块实例
        
        Args:
            market_data: 市场K线数据（必须包含timestamp/open/high/low/close/volume）
            config: Mock训练配置
        
        Returns:
            MockTrainingResult: 训练结果（完全封装）
        """
        # 延迟导入以避免循环依赖
        import pandas as pd
        from prometheus.config.mock_training_config import MockTrainingConfig, MockTrainingResult
        from prometheus.core.world_signature_simple import WorldSignatureSimple
        from prometheus.core.experience_db import ExperienceDB
        
        logger.info("="*80)
        logger.info("Mock训练 - v6.0统一封装入口")
        logger.info("="*80)
        logger.info(f"训练配置:")
        logger.info(f"  周期数: {config.cycles}")
        logger.info(f"  系统资金: ${config.total_system_capital:,.0f}")
        logger.info(f"  Agent数量: {config.agent_count}")
        logger.info(f"  创世配比: {config.genesis_allocation_ratio*100:.0f}%给Agent，{(1-config.genesis_allocation_ratio)*100:.0f}%资金池")
        logger.info(f"  进化间隔: {config.evolution_interval}周期")
        logger.info(f"  市场类型: {config.market_type}")
        logger.info("")
        
        # 0. 重新初始化EvolutionManagerV5，使用config中的参数
        from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
        self.evolution = EvolutionManagerV5(
            moirai=self.moirai,
            num_families=len(self.moirai.families) if hasattr(self.moirai, 'families') else 50,
            elite_ratio=config.elite_ratio,
            elimination_ratio=config.elimination_rate,
            capital_pool=self.capital_pool
        )
        logger.info(f"✅ EvolutionManagerV5已重新初始化（精英{config.elite_ratio:.0%}，淘汰{config.elimination_rate:.0%}）")
        logger.info("")
        
        # 1. 初始化ExperienceDB（如果需要）
        if config.experience_db_path:
            self.experience_db = ExperienceDB(db_path=config.experience_db_path)
            # 将experience_db传递给Moirai（用于智能创世）
            self.moirai.experience_db = self.experience_db
            logger.info(f"✅ ExperienceDB已加载: {config.experience_db_path}")
        else:
            self.experience_db = None
            self.moirai.experience_db = None
            logger.info("⏭️  未指定ExperienceDB，将使用随机创世")
        
        # ✨ 1.5. Prophet分析初始市场数据（为创世准备）
        if self.prophet and len(market_data) > 0:
            try:
                logger.info("🔮 Prophet正在分析初始市场...")
                # 取前100根K线作为初始分析数据
                initial_data = market_data.head(min(100, len(market_data)))
                self.prophet.genesis_strategy(
                    initial_market_data=initial_data,
                    genesis_mode=config.genesis_strategy
                )
                logger.info("✅ Prophet创世策略已发布")
            except Exception as e:
                logger.warning(f"⚠️  Prophet创世策略失败（{e}），将使用默认随机创世")
        
        # 2. 创世（使用已有的init_population方法，内部会自动调用invest_system_capital）
        capital_per_agent = config.total_system_capital / config.agent_count
        
        self.init_population(
            agent_count=config.agent_count,
            capital_per_agent=capital_per_agent,
            full_genome_unlock=config.full_genome_unlock,  # ✅ 使用配置参数
            genesis_allocation_ratio=config.genesis_allocation_ratio
        )
        
        logger.info(f"✅ 创世完成: {len(self.moirai.agents)}个Agent")
        logger.info("")
        
        # 4. 运行训练循环
        from datetime import datetime
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        logger.info(f"🏃 开始训练循环: {config.cycles}周期")
        logger.info(f"Run ID: {run_id}")
        logger.info("")
        
        for cycle in range(config.cycles):
            # 获取当前K线
            if cycle >= len(market_data):
                logger.warning(f"市场数据耗尽，在周期{cycle}停止训练")
                break
            
            kline = market_data.iloc[cycle]
            current_price = float(kline['close'])
            
            # 简化的市场数据格式
            market_data_dict = {
                'open': float(kline['open']),
                'high': float(kline['high']),
                'low': float(kline['low']),
                'close': current_price,
                'price': current_price,  # ✅ 添加price字段（run_cycle需要）
                'volume': float(kline['volume']),
                'timestamp': kline['timestamp'] if 'timestamp' in kline else cycle
            }
            
            # 运行一个周期（使用已有的run_cycle方法）
            try:
                self.run_cycle(
                    market_data=market_data_dict,
                    bulletins={},  # 简化：不使用公告板
                    cycle_count=cycle
                )
            except Exception as e:
                logger.error(f"Cycle {cycle} 失败: {e}")
                continue
            
            # 进化
            if cycle > 0 and cycle % config.evolution_interval == 0:
                try:
                    self.evolution.run_evolution_cycle(current_price=current_price)
                except Exception as e:
                    logger.error(f"进化失败 (cycle {cycle}): {e}")
            
            # 间隔保存ExperienceDB
            if self.experience_db and config.save_experience_interval > 0:
                if cycle > 0 and cycle % config.save_experience_interval == 0:
                    try:
                        # 计算当前WorldSignature
                        start_idx = max(0, cycle - config.ws_window_size + 1)
                        ws_data = market_data.iloc[start_idx:cycle+1]
                        ws = WorldSignatureSimple.from_market_data(ws_data)
                        
                        # 排序Agent
                        alive_agents = [a for a in self.moirai.agents if a.state.value != 'dead']
                        sorted_agents = sorted(
                            alive_agents,
                            key=lambda a: (a.account.private_ledger.virtual_capital - a.initial_capital) / a.initial_capital if hasattr(a, 'account') and a.account else 0,
                            reverse=True
                        )
                        
                        # 保存当前最佳Agent
                        if len(sorted_agents) > 0:
                            self.experience_db.save_best_genomes(
                                run_id=f"{run_id}_cycle{cycle}",
                                market_type=config.market_type,
                                world_signature=ws,
                                agents=sorted_agents,
                                top_k=config.top_k_to_save
                            )
                            logger.info(f"💾 Cycle {cycle}: 已保存{min(len(sorted_agents), config.top_k_to_save)}个最佳Agent到ExperienceDB")
                    except Exception as e:
                        logger.warning(f"ExperienceDB保存失败 (cycle {cycle}): {e}")
            
            # 定期日志
            if cycle % config.log_interval == 0:
                alive_count = sum(1 for a in self.moirai.agents if a.state.value != 'dead')
                logger.info(f"Cycle {cycle:4d}: 存活Agent={alive_count}")
        
        logger.info("")
        logger.info("✅ 训练循环完成")
        logger.info("")
        
        # 5. 计算最终指标
        final_price = float(market_data.iloc[-1]['close']) if len(market_data) > 0 else current_price
        
        # Agent统计
        alive_agents = [a for a in self.moirai.agents if a.state.value != 'dead']
        if alive_agents:
            # 计算每个Agent的ROI
            agent_rois = []
            for agent in alive_agents:
                if hasattr(agent, 'account') and agent.account:
                    final_capital = agent.account.private_ledger.virtual_capital
                    roi = (final_capital - agent.initial_capital) / agent.initial_capital if agent.initial_capital > 0 else 0.0
                    agent_rois.append(roi)
            
            agent_avg_roi = sum(agent_rois) / len(agent_rois) if agent_rois else 0.0
            agent_median_roi = sorted(agent_rois)[len(agent_rois)//2] if agent_rois else 0.0
            agent_best_roi = max(agent_rois) if agent_rois else 0.0
        else:
            agent_avg_roi = agent_median_roi = agent_best_roi = 0.0
        
        # 系统ROI
        agent_total_capital = sum(
            a.account.private_ledger.virtual_capital 
            for a in self.moirai.agents 
            if hasattr(a, 'account') and a.account
        )
        pool_balance = self.capital_pool.available_pool
        system_total_capital = agent_total_capital + pool_balance
        system_roi = (system_total_capital - config.total_system_capital) / config.total_system_capital
        
        # BTC基准
        initial_price = float(market_data.iloc[0]['close'])
        btc_benchmark_roi = (final_price - initial_price) / initial_price
        
        # 6. 保存到ExperienceDB（如果需要）
        if self.experience_db and config.top_k_to_save > 0:
            # 计算WorldSignature
            ws = WorldSignatureSimple.from_market_data(
                market_data.tail(config.ws_window_size)
            )
            
            # 排序Agent
            sorted_agents = sorted(
                alive_agents,
                key=lambda a: (a.account.private_ledger.virtual_capital - a.initial_capital) / a.initial_capital if hasattr(a, 'account') and a.account else 0,
                reverse=True
            )
            
            # 保存最佳Agent
            if self.experience_db:
                self.experience_db.save_best_genomes(
                    run_id=run_id,
                market_type=config.market_type,
                world_signature=ws,
                agents=sorted_agents,
                top_k=config.top_k_to_save
            )
            logger.info(f"✅ 已保存{config.top_k_to_save}个最佳Agent到ExperienceDB")
        
        # 7. 对账验证
        reconciliation_passed = True
        reconciliation_details = {}
        try:
            recon_result = self.reconcile(final_price)
            reconciliation_passed = recon_result.get('all_passed', False)
            reconciliation_details = recon_result
        except Exception as e:
            logger.error(f"对账失败: {e}")
            reconciliation_passed = False
            reconciliation_details = {'error': str(e)}
        
        # 8. 构建结果
        result = MockTrainingResult(
            run_id=run_id,
            actual_cycles=cycle + 1,
            system_roi=system_roi,
            system_total_capital=system_total_capital,
            btc_benchmark_roi=btc_benchmark_roi,
            outperformance=system_roi - btc_benchmark_roi,
            agent_count_final=len(alive_agents),
            agent_avg_roi=agent_avg_roi,
            agent_median_roi=agent_median_roi,
            agent_best_roi=agent_best_roi,
            agent_avg_trade_count=0.0,  # TODO: 计算平均交易次数
            capital_pool_balance=pool_balance,
            capital_utilization=agent_total_capital / system_total_capital if system_total_capital > 0 else 0,
            best_agents=[],  # TODO: 返回最佳Agent信息
            experience_db_records=self.experience_db.get_statistics(config.market_type)['total_records'] if self.experience_db else 0,
            experience_saved=self.experience_db is not None and config.top_k_to_save > 0,
            log_file="",  # TODO: 日志文件路径
            report_file="",  # TODO: 报告文件路径
            reconciliation_passed=reconciliation_passed,
            reconciliation_details=reconciliation_details
        )
        
        # 9. 清理
        if self.experience_db:
            self.experience_db.close()
        
        # 10. 打印总结
        logger.info("="*80)
        logger.info("Mock训练完成")
        logger.info("="*80)
        logger.info(f"Run ID: {run_id}")
        logger.info(f"系统ROI: {system_roi:+.2%}")
        logger.info(f"BTC基准: {btc_benchmark_roi:+.2%}")
        logger.info(f"超越BTC: {result.outperformance:+.2%}")
        logger.info(f"Agent平均ROI: {agent_avg_roi:+.2%}")
        logger.info(f"最佳Agent ROI: {agent_best_roi:+.2%}")
        logger.info(f"资金池余额: ${pool_balance:,.0f} ({result.capital_utilization*100:.1f}%资金利用)")
        logger.info(f"对账验证: {'✅ 通过' if reconciliation_passed else '❌ 失败'}")
        logger.info("="*80)
        
        return result


def build_facade(mode: str,
                 num_families: int = 50,
                 agent_count: int = 50,
                 capital_per_agent: float = 10000.0,
                 exchange_config: Optional[Dict] = None,
                 data_source=None,
                 scenario=None,
                 evo_interval: int = 1,
                 seed: Optional[int] = None,
                 genesis_seed: Optional[int] = None,
                 evolution_seed: Optional[int] = None,
                 full_genome_unlock: bool = False) -> V6Facade:
    """
    统一构建 Facade：
    mode: okx_paper / backtest / mock
    
    随机种子控制：
    - seed: 主种子（同时控制创世和演化）
    - genesis_seed: 创世专用种子（优先级高于seed）
    - evolution_seed: 演化专用种子（优先级高于seed）
    """
    import random
    import numpy as np
    
    # ========== 创世种子设置 ==========
    actual_genesis_seed = genesis_seed if genesis_seed is not None else seed
    if actual_genesis_seed is not None:
        random.seed(actual_genesis_seed)
        np.random.seed(actual_genesis_seed)
        logger.info(f"🎲 创世种子已设置: {actual_genesis_seed}")
    
    # ========== 构建交易所 ==========
    exchange = None
    exchange_config = exchange_config or {}
    if mode == "okx_paper":
        exchange = OKXExchange(
            api_key=exchange_config.get("api_key"),
            secret_key=exchange_config.get("secret_key"),
            passphrase=exchange_config.get("passphrase"),
            sandbox=True
        )
    elif mode == "backtest":
        exchange = BacktestExchange(data_source=data_source)
    elif mode == "mock":
        exchange = MockExchange(scenario=scenario)
    else:
        raise ValueError(f"未知模式: {mode}")
    
    # ========== 初始化Facade ==========
    facade = V6Facade(num_families=num_families, exchange=exchange)
    
    # ========== 设置场景类型 ==========
    if mode == "okx_paper":
        facade.scenario = "live_demo"
    elif mode == "backtest":
        facade.scenario = "backtest"
    elif mode == "mock":
        facade.scenario = "mock"
    
    # ========== 创世（使用创世种子） ==========
    facade.init_population(
        agent_count=agent_count, 
        capital_per_agent=capital_per_agent,
        full_genome_unlock=full_genome_unlock  # ✨ 激进模式：解锁所有50个基因参数
    )
    facade.evo_interval = max(1, evo_interval)
    
    # ========== 演化种子设置（创世后重置） ==========
    # ⭐ 关键修复：区分"未传入"和"显式为None"
    # - 未传入（默认值_USE_SEED_SENTINEL）：使用seed参数
    # - 显式为None：使用真随机
    # - 显式为具体值：使用该值
    if evolution_seed is _USE_SEED_SENTINEL:
        # 未显式指定evolution_seed，使用seed参数
        actual_evolution_seed = seed
    elif evolution_seed is None:
        # 显式指定为None，使用真随机
        actual_evolution_seed = None
    else:
        # 显式指定了具体值
        actual_evolution_seed = evolution_seed
    
    if actual_evolution_seed is not None:
        # 显式设置演化seed
        random.seed(actual_evolution_seed)
        np.random.seed(actual_evolution_seed)
        logger.info(f"🎲 演化种子已设置: {actual_evolution_seed}")
    else:
        # 使用真随机！
        import time
        random_seed = int(time.time() * 1000000) % (2**32)
        random.seed(random_seed)
        np.random.seed(random_seed)
        logger.info(f"🎲 演化种子已重置为真随机: {random_seed}")
        actual_evolution_seed = random_seed  # 记录使用的seed
    
    # ========== 保存种子信息到Facade ==========
    facade.genesis_seed = actual_genesis_seed
    facade.evolution_seed = actual_evolution_seed
    facade.seed_config = {
        'main_seed': seed,
        'genesis_seed': actual_genesis_seed,
        'evolution_seed': actual_evolution_seed,
        'timestamp': datetime.now().isoformat()
    }
    
    return facade


_USE_SEED_SENTINEL = object()  # 哨兵对象，用于区分"未传入"和"显式为None"

def run_scenario(mode: str,
                 total_cycles: int,
                 market_feed=None,
                 num_families: int = 50,
                 agent_count: int = 50,
                 capital_per_agent: float = 10000.0,
                 exchange_config: Optional[Dict] = None,
                 data_source=None,
                 scenario=None,
                 evo_interval: int = 1,
                 seed: Optional[int] = None,
                 genesis_seed: Optional[int] = None,
                 evolution_seed = _USE_SEED_SENTINEL,
                 full_genome_unlock: bool = False):
    """
    场景化启动入口：根据 mode 装配交易封装与数据源，运行主循环
    
    Args:
        seed: 主随机种子（同时控制创世和演化，优先级低于专用seed）
        genesis_seed: 创世专用种子（仅控制初始种群生成）
        evolution_seed: 演化专用种子（仅控制进化过程）
        full_genome_unlock: 是否解锁所有50个基因参数（激进模式 vs 渐进式）
                           - False（默认）：渐进式解锁（创世3个→进化到50个）
                           - True：激进模式（创世直接解锁所有50个）
        
    实验设计：
        场景A - 固定创世，观察演化多样性:
            run_scenario(..., genesis_seed=1000, evolution_seed=None)  # 每次演化结果不同
        
        场景B - 不同创世，观察最终差异:
            run_scenario(..., genesis_seed=1000, evolution_seed=2000)  # vs
            run_scenario(..., genesis_seed=2000, evolution_seed=2000)  # 对比
        
        场景C - 完全可重复实验:
            run_scenario(..., seed=1000)  # 每次完全相同
    """
    facade = build_facade(
        mode=mode,
        num_families=num_families,
        agent_count=agent_count,
        capital_per_agent=capital_per_agent,
        exchange_config=exchange_config,
        data_source=data_source,
        scenario=scenario,
        evo_interval=evo_interval,
        seed=seed,
        genesis_seed=genesis_seed,
        evolution_seed=evolution_seed,
        full_genome_unlock=full_genome_unlock  # ✨ 传递激进式参数
    )
    facade._init_run_dir(mode=mode, scenario=scenario or "default")
    facade.save_config({
        "mode": mode,
        "num_families": num_families,
        "agent_count": agent_count,
        "capital_per_agent": capital_per_agent,
        "evo_interval": evo_interval,
        "exchange_config": exchange_config,
        "scenario": scenario,
        "seed_config": facade.seed_config  # ✅ 保存种子配置
    })
    facade.run(total_cycles=total_cycles, market_feed=market_feed, evo_interval=evo_interval)
    # AlphaZero式：移除多样性指标记录
    # if facade.metrics_history:
    #     m = facade.metrics_history[-1]
    #     facade.save_metrics({
    #         "cycle": m.cycle,
    #         "diversity_score": m.diversity_score,
    #         "gene_entropy": m.gene_entropy,
    #         "lineage_entropy": m.lineage_entropy,
    #         "active_families": m.active_families
    #     })
    return facade


def run_seed_experiment(
    mode: str,
    total_cycles: int,
    market_feed,
    num_families: int = 50,
    agent_count: int = 50,
    capital_per_agent: float = 10000.0,
    exchange_config: Optional[Dict] = None,
    data_source=None,
    evo_interval: int = 1,
    experiment_type: str = "fixed_genesis",
    num_runs: int = 3,
    base_seed: int = 1000
) -> List[Dict]:
    """
    ✅ 统一封装的种子实验入口
    
    实验类型：
    - "fixed_genesis": 固定创世，观察演化多样性
    - "different_genesis": 不同创世，观察最终差异
    - "fully_reproducible": 完全可重复实验
    
    Args:
        experiment_type: 实验类型
        num_runs: 运行次数
        base_seed: 基础种子
        
    Returns:
        List[Dict]: 每次运行的结果摘要
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"🧪 种子实验: {experiment_type}")
    logger.info(f"   运行次数: {num_runs}")
    logger.info(f"   基础种子: {base_seed}")
    logger.info(f"{'='*80}\n")
    
    results = []
    
    for run_idx in range(num_runs):
        logger.info(f"\n--- 运行 #{run_idx+1}/{num_runs} ---")
        
        # 根据实验类型设置种子
        if experiment_type == "fixed_genesis":
            # 固定创世，随机演化
            genesis_seed = base_seed
            evolution_seed = None
            scenario_name = f"fixed_genesis_run_{run_idx+1}"
            logger.info(f"   创世种子: {genesis_seed} (固定)")
            logger.info(f"   演化种子: None (随机)")
            
        elif experiment_type == "different_genesis":
            # 不同创世，固定演化
            genesis_seed = base_seed + run_idx * 1000
            evolution_seed = base_seed + 10000
            scenario_name = f"diff_genesis_{genesis_seed}"
            logger.info(f"   创世种子: {genesis_seed} (变化)")
            logger.info(f"   演化种子: {evolution_seed} (固定)")
            
        elif experiment_type == "fully_reproducible":
            # 完全固定
            main_seed = base_seed
            genesis_seed = None
            evolution_seed = None
            scenario_name = f"reproducible_run_{run_idx+1}"
            logger.info(f"   主种子: {main_seed} (固定)")
        else:
            raise ValueError(f"未知实验类型: {experiment_type}")
        
        try:
            # ✅ 通过统一入口运行
            if experiment_type == "fully_reproducible":
                facade = run_scenario(
                    mode=mode,
                    total_cycles=total_cycles,
                    market_feed=market_feed,
                    num_families=num_families,
                    agent_count=agent_count,
                    capital_per_agent=capital_per_agent,
                    exchange_config=exchange_config,
                    data_source=data_source,
                    scenario=scenario_name,
                    evo_interval=evo_interval,
                    seed=main_seed
                )
            else:
                facade = run_scenario(
                    mode=mode,
                    total_cycles=total_cycles,
                    market_feed=market_feed,
                    num_families=num_families,
                    agent_count=agent_count,
                    capital_per_agent=capital_per_agent,
                    exchange_config=exchange_config,
                    data_source=data_source,
                    scenario=scenario_name,
                    evo_interval=evo_interval,
                    genesis_seed=genesis_seed,
                    evolution_seed=evolution_seed
                )
            
            # 收集结果
            summary = facade.report_status()
            
            run_result = {
                "run_id": run_idx + 1,
                "experiment_type": experiment_type,
                "seed_config": facade.seed_config,
                "final_agents": summary.get("agent_count", 0),
                "avg_capital": summary.get("avg_capital", 0),
                "total_trades": summary.get("total_trades", 0),
                # AlphaZero式：移除diversity_score
                # "diversity_score": facade.metrics_history[-1].diversity_score if facade.metrics_history else 0,
                "run_dir": str(facade.run_dir) if facade.run_dir else None
            }
            
            results.append(run_result)
            logger.info(f"✅ 运行 #{run_idx+1} 完成")
            logger.info(f"   最终资金: {run_result['avg_capital']:.2f}")
            logger.info(f"   多样性: {run_result['diversity_score']:.2%}")
            
        except Exception as e:
            logger.error(f"❌ 运行 #{run_idx+1} 失败: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "run_id": run_idx + 1,
                "experiment_type": experiment_type,
                "error": str(e)
            })
    
    # 保存实验结果摘要
    _save_experiment_summary(experiment_type, results, base_seed)
    
    # 分析结果
    _analyze_experiment_results(experiment_type, results)
    
    return results


def _save_experiment_summary(experiment_type: str, results: List[Dict], base_seed: int):
    """保存实验结果摘要"""
    output_dir = Path("results/seed_experiments")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f"{experiment_type}_{base_seed}_{timestamp}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n📊 实验结果已保存: {output_file}")


def _analyze_experiment_results(experiment_type: str, results: List[Dict]):
    """分析实验结果"""
    import numpy as np
    
    logger.info(f"\n{'='*80}")
    logger.info(f"📈 实验分析: {experiment_type}")
    logger.info(f"{'='*80}")
    
    successful_runs = [r for r in results if "error" not in r]
    
    if len(successful_runs) == 0:
        logger.error("❌ 所有运行都失败了！")
        return
    
    # 计算统计量
    capitals = [r["avg_capital"] for r in successful_runs]
    diversities = [r["diversity_score"] for r in successful_runs]
    
    logger.info(f"成功运行: {len(successful_runs)}/{len(results)}")
    logger.info(f"\n平均资金:")
    logger.info(f"  均值: {np.mean(capitals):.2f}")
    logger.info(f"  标准差: {np.std(capitals):.2f}")
    logger.info(f"  范围: [{np.min(capitals):.2f}, {np.max(capitals):.2f}]")
    
    logger.info(f"\n多样性评分:")
    logger.info(f"  均值: {np.mean(diversities):.2%}")
    logger.info(f"  标准差: {np.std(diversities):.2%}")
    logger.info(f"  范围: [{np.min(diversities):.2%}, {np.max(diversities):.2%}]")
    
    # 特定实验类型的分析
    if experiment_type == "fully_reproducible":
        # 检查可重复性
        if len(successful_runs) >= 2:
            if all(abs(r["avg_capital"] - successful_runs[0]["avg_capital"]) < 0.01 for r in successful_runs):
                logger.info(f"\n✅ 可重复性验证通过！所有运行结果完全相同。")
            else:
                logger.warning(f"\n⚠️ 可重复性验证失败！不同运行结果不同。")
                for i, r in enumerate(successful_runs):
                    logger.info(f"   运行 #{i+1}: 资金={r['avg_capital']:.2f}")
    
    elif experiment_type == "fixed_genesis":
        # 分析演化多样性
        capital_std = np.std(capitals)
        capital_mean = np.mean(capitals)
        cv = capital_std / capital_mean if capital_mean > 0 else 0
        
        logger.info(f"\n演化多样性分析:")
        logger.info(f"  变异系数 (CV): {cv:.2%}")
        if cv > 0.1:
            logger.info(f"  💡 演化路径显著影响最终结果！")
        else:
            logger.info(f"  💡 演化路径影响较小，结果相对稳定。")
    
    elif experiment_type == "different_genesis":
        # 分析创世影响
        logger.info(f"\n创世影响分析:")
        for i, r in enumerate(successful_runs):
            logger.info(f"  创世 {r['seed_config'].get('genesis_seed')}: 资金={r['avg_capital']:.2f}")
        
        capital_std = np.std(capitals)
        capital_mean = np.mean(capitals)
        cv = capital_std / capital_mean if capital_mean > 0 else 0
        
        logger.info(f"  变异系数 (CV): {cv:.2%}")
        if cv > 0.15:
            logger.info(f"  💡 创世配置对最终结果有显著影响！")
        else:
            logger.info(f"  💡 进化能力较强，能弥补不同的初始条件。")
    
    logger.info(f"{'='*80}\n")


    # ========== 交易记录写入 ==========
    def _record_trade_to_ledgers(self, agent, trade: Dict, is_real: bool = False):
        """
        将模拟/回测成交写入私账与公账，便于对账
        """
        trade_id = str(uuid.uuid4())
        trade_type = trade.get("side")
        amount = abs(trade.get("amount", 0))
        price = trade.get("price", 0)
        if not trade_type or amount <= 0 or price <= 0:
            return
        position_side = "long" if trade_type in ("buy", "cover") else "short"
        tr = TradeRecord(
            agent_id=agent.agent_id,
            trade_id=trade_id,
            trade_type=trade_type,
            amount=amount,
            price=price,
            timestamp=datetime.now(),
            confidence=trade.get("confidence", 1.0),
            pnl=None,
            is_real=is_real,
            position_side=position_side,
            okx_order_id=None
        )
        # 写私账
        acct = getattr(agent, "account", None)
        if acct and getattr(acct, "private_ledger", None):
            try:
                acct.private_ledger.record_trade(tr, caller_role=Role.SUPERVISOR)
            except Exception as e:
                logger.warning(f"私账记账失败 {agent.agent_id}: {e}")
        # 写公账
        try:
            self.public_ledger.record_trade(tr, caller_role=Role.SUPERVISOR)
        except Exception as e:
            logger.warning(f"公共账簿记账失败 {agent.agent_id}: {e}")

    # ========== 模拟撮合并记账 ==========
    def simulate_and_record(self, agent, symbol: str, side: str, amount: float, price: float):
        """
        针对回测/Mock场景：直接使用撮合结果写入账簿
        """
        sim_trade = {
            "symbol": symbol,
            "side": side,
            "amount": amount,
            "price": price,
            "fee": abs(amount * price) * 0.0005,
            "confidence": 1.0
        }
        self._record_trade_to_ledgers(agent, sim_trade, is_real=False)
        return sim_trade

    # ========== 结果归档相关 ==========
    def _init_run_dir(self, mode: str, scenario: str = "default"):
        ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        base = Path("results") / mode / ts[:8] / f"{scenario}_{ts}"
        base.mkdir(parents=True, exist_ok=True)
        (base / "artifacts").mkdir(exist_ok=True)
        self.run_dir = base
        logger.info(f"结果归档目录: {base}")
        return base

    def save_config(self, cfg: Dict):
        if not self.run_dir:
            return
        path = self.run_dir / "config.json"
        with open(path, "w") as f:
            json.dump(cfg, f, indent=2)
        logger.info(f"已保存配置: {path}")

    def save_metrics(self, metrics: Dict):
        if not self.run_dir:
            return
        path = self.run_dir / "metrics.json"
        with open(path, "w") as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"已保存指标: {path}")

