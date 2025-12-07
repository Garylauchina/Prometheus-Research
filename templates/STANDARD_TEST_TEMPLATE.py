#!/usr/bin/env python3
"""
Prometheus 标准测试模板 (v6.0)
============================================

⚠️ 重要: 从 v6.0 开始,所有测试必须使用 v6 Facade 统一入口!
         本模板已过时,仅作为底层组件参考!

✅ 新版推荐: 使用 test_ultimate_v6_CORRECT.py 作为模板
         使用 run_scenario(mode=...) 统一入口

============================================
📋 Prometheus 代码三大铁律 (2025-12-07)
============================================

1. 🔒 统一封装,统一调用,严禁旁路
   ✅ 必须使用: v6 Facade 统一入口 (run_scenario/build_facade)
   ❌ 严禁: 自己写循环直接调用底层模块
   原因: test_ultimate_1000x_COMPLETE.py 的惨痛教训
        - 自己写循环导致只开仓不平仓
        - 账簿累积数千条空记录
        - 虽然"测试通过"但数据不可信

2. 📐 严格执行测试规范
   ✅ 必须基于: STANDARD_TEST_TEMPLATE.py (旧) 或 test_ultimate_v6_CORRECT.py (新)
   ✅ 必须包含: 完整架构初始化 + 双账簿验证 + 对账验证
   ❌ 严禁: 自创简化版测试
   原因: 简化版会省略关键模块,导致测试结果不可信

3. 🚫 不可为测试通过而简化底层机制
   ✅ 必须使用: 完整交易生命周期 (开仓→持仓→平仓)
   ✅ 必须使用: 完整账簿系统 (不手动修改current_capital)
   ✅ 必须使用: 完整进化机制 (不省略Immigration/多样性监控)
   ❌ 严禁: 为了让测试通过而删减机制
   原因: 账簿一致性是金融系统生命线,任何妥协都可能导致灾难

============================================
执行标准: 每个测试必须过三关
============================================
✅ 第1关: 使用 Facade 入口 (不自己写循环)
✅ 第2关: 基于标准模板 (不自创简化版)
✅ 第3关: 对账验证无误 (账簿完全一致)

违反后果: 产生不可信的测试结果,浪费大量调试时间!

============================================

基于 v4_okx_simplified_launcher.py 的完整架构
确保所有核心模块都被正确使用

架构完整性：A (9/10)
唯一缺失：WorldSignature（可选，根据测试目的添加）

核心模块清单（9/10）：
✅ 1. Supervisor           # 监督层核心
✅ 2. Mastermind           # 战略层核心
✅ 3. BulletinBoard        # 信息架构
✅ 4. PublicLedger         # 公共账簿（通过Supervisor.genesis()自动）
✅ 5. PrivateLedger        # 私有账簿（通过AgentAccountSystem自动）
✅ 6. Moirai               # 生命周期（Supervisor内部）
✅ 7. EvolutionManager     # 进化管理（Supervisor内部）
✅ 8. AgentV5/AgentV4      # Agent
✅ 9. OKXExchange/回测引擎  # 交易执行
⚪ 10. WorldSignature      # 市场感知（可选）

使用方式：
1. ⚠️ 推荐: 直接使用 test_ultimate_v6_CORRECT.py
2. 如必须自定义: 复制此模板并严格遵守三大铁律
3. 可选：添加WorldSignature
4. 运行测试前必须对账验证

⚠️ 警告：不要为了"简化"而删除任何核心模块！
         不要手动修改 agent.current_capital！
         不要只开仓不平仓！
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ==================== 核心模块导入 ====================
from prometheus.core.supervisor import Supervisor
from prometheus.core.mastermind import Mastermind
from prometheus.core.bulletin_board_v4 import BulletinBoardV4
from prometheus.core.agent_v5 import AgentV5  # 或 agent_v4.AgentV4
from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5

# ==================== 可选模块 ====================
# from prometheus.world_signature import WorldSignature
# from prometheus.world_signature.generator import WorldSignatureGenerator

# ==================== 交易接口 ====================
from prometheus.exchange.okx_api import OKXExchange
# 或使用回测引擎：
# from prometheus.backtest.historical_backtest import HistoricalBacktest

import logging
from datetime import datetime
import time

# ==================== 日志配置 ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

# 根据需要调整各模块日志级别
logging.getLogger('prometheus.core.supervisor').setLevel(logging.INFO)
logging.getLogger('prometheus.core.mastermind').setLevel(logging.INFO)
logging.getLogger('prometheus.core.bulletin_board_v4').setLevel(logging.WARNING)
logging.getLogger('prometheus.core.agent_v5').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class StandardTestRunner:
    """
    标准测试运行器
    
    使用完整的Prometheus架构
    确保所有核心模块都被正确初始化和使用
    """
    
    def __init__(self, config: dict):
        """
        初始化测试运行器
        
        Args:
            config: 测试配置字典，必须包含：
                - trading_mode: 'okx_sandbox' | 'okx_real' | 'backtest'
                - agent_count: Agent数量
                - initial_capital_per_agent: 每个Agent初始资金
                - duration_minutes: 测试时长（分钟）
                - ... 其他配置
        """
        self.config = config
        self.start_time = datetime.now()
        
        logger.info("=" * 80)
        logger.info("🚀 Prometheus 标准测试")
        logger.info("=" * 80)
        logger.info(f"开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"测试模式: {config['trading_mode']}")
        logger.info("=" * 80)
        
        # ==================== 第一步：初始化基础组件 ====================
        self._initialize_components()
        
        # ==================== 第二步：执行创世 ====================
        self._run_genesis()
        
    def _initialize_components(self):
        """初始化所有核心组件"""
        logger.info("\n【步骤1】初始化核心组件...")
        
        # 1. 信息架构（BulletinBoard）
        self.bulletin_board = BulletinBoardV4(max_bulletins_per_tier=50)
        logger.info("   ✅ BulletinBoard初始化完成")
        
        # 2. 战略层（Mastermind）
        self.mastermind = Mastermind(
            initial_capital=self.config.get('total_capital', 100000.0),
            decision_mode="human",  # 或 "auto"
            bulletin_board=self.bulletin_board
        )
        logger.info("   ✅ Mastermind初始化完成")
        
        # 3. 监督层（Supervisor）- 核心！
        self.supervisor = Supervisor(
            bulletin_board=self.bulletin_board
        )
        logger.info("   ✅ Supervisor初始化完成")
        
        # 4. 交易接口
        self._initialize_trading_interface()
        
        # 5. 可选：WorldSignature
        # self._initialize_world_signature()
        
    def _initialize_trading_interface(self):
        """初始化交易接口（OKX或回测）"""
        trading_mode = self.config['trading_mode']
        
        if trading_mode == 'okx_sandbox':
            # OKX模拟盘
            sys.path.insert(0, 'config')
            from okx_config import OKX_PAPER_TRADING
            
            self.exchange = OKXExchange(
                api_key=OKX_PAPER_TRADING['api_key'],
                api_secret=OKX_PAPER_TRADING['api_secret'],
                passphrase=OKX_PAPER_TRADING['passphrase'],
                paper_trading=False,
                testnet=True
            )
            logger.info("   ✅ OKX Sandbox连接成功")
            
        elif trading_mode == 'okx_real':
            # OKX实盘（需要实盘API密钥）
            raise NotImplementedError("实盘模式需要额外配置")
            
        elif trading_mode == 'backtest':
            # 历史回测
            from prometheus.backtest.historical_backtest import HistoricalBacktest
            self.exchange = HistoricalBacktest(
                data_path=self.config.get('backtest_data_path'),
                start_date=self.config.get('backtest_start_date'),
                end_date=self.config.get('backtest_end_date')
            )
            logger.info("   ✅ 回测引擎初始化完成")
            
        else:
            raise ValueError(f"不支持的trading_mode: {trading_mode}")
    
    def _initialize_world_signature(self):
        """可选：初始化WorldSignature市场感知系统"""
        # from prometheus.world_signature.generator import WorldSignatureGenerator
        # self.ws_generator = WorldSignatureGenerator()
        # logger.info("   ✅ WorldSignature初始化完成")
        pass
    
    def _run_genesis(self):
        """
        执行创世（完整的世界初始化）
        
        ⚠️ 关键：使用Supervisor.genesis()自动初始化：
        - PublicLedger（公共账簿）
        - PrivateLedger（每个Agent一本）
        - AgentAccountSystem（账户系统）
        - agent.account（自动挂载）
        """
        logger.info("\n【步骤2】执行创世...")
        
        # 创世配置
        genesis_config = {
            'min_agent_count': self.config.get('agent_count', 10),
            'max_agent_count': self.config.get('agent_count', 10),
            'min_capital_per_agent': self.config.get('initial_capital_per_agent', 10000),
            'capital_reserve_ratio': 0.1,
            'history_days': 7,
            'initial_capital_per_agent': self.config.get('initial_capital_per_agent', 10000),
        }
        
        # 执行创世
        genesis_result = self.supervisor.genesis(
            okx_trading=self.exchange,
            mastermind=self.mastermind,
            bulletin_board=self.bulletin_board,
            config=genesis_config,
            agent_factory=self._create_agent  # Agent工厂函数
        )
        
        if not genesis_result['success']:
            logger.error(f"❌ 创世失败: {genesis_result['errors']}")
            raise Exception("创世失败")
        
        self.agents = self.supervisor.agents
        logger.info(f"   ✅ 创世成功：{len(self.agents)} 个Agent")
        
        # ✅ 挂载并验证双账簿系统
        self._attach_and_verify_ledgers()
    
    def _attach_and_verify_ledgers(self):
        """为全体Agent挂载账簿并验证（防遗漏）"""
        logger.info("\n【验证】双账簿系统...")
        
        # 检查Supervisor的PublicLedger
        if not hasattr(self.supervisor, 'public_ledger'):
            raise Exception("❌ Supervisor缺少public_ledger！")
        public_ledger = self.supervisor.public_ledger
        logger.info("   ✅ PublicLedger存在")
        
        # 强制为所有Agent挂账簿（如已存在则跳过）
        for agent in self.agents:
            if getattr(agent, "account", None) is None:
                account = AgentAccountSystem(agent_id=agent.agent_id, public_ledger=public_ledger)
                agent.account = account
        
        # 检查账簿挂载
        for agent in self.agents:
            if not getattr(agent, "account", None):
                raise Exception(f"❌ Agent {agent.agent_id} 缺少account！")
            if not hasattr(agent.account, 'private_ledger'):
                raise Exception(f"❌ Agent {agent.agent_id} 的account缺少private_ledger！")
        
        logger.info(f"   ✅ 所有Agent都有account和private_ledger")
        logger.info("   ✅ 双账簿系统验证通过")
    
    def _create_agent(self, agent_id: str, gene, capital: float):
        """
        Agent工厂函数
        
        根据测试需要选择AgentV4或AgentV5
        """
        # 使用AgentV5（推荐）
        from prometheus.core.lineage import LineageVector
        from prometheus.core.genome import GenomeVector
        from prometheus.core.instinct import Instinct
        
        # 创建Agent的基因组件
        lineage = LineageVector.create_genesis(
            family_id=0,  # 创世Agent
            generation=0
        )
        
        genome = GenomeVector.create_genesis()
        instinct = Instinct.create_genesis()
        
        agent = AgentV5(
            agent_id=agent_id,
            lineage=lineage,
            genome=genome,
            instinct=instinct,
            initial_capital=capital,
            bulletin_board=self.bulletin_board
        )
        
        return agent
        
        # 或使用AgentV4（如果需要）
        # from prometheus.core.agent_v4 import AgentV4
        # agent = AgentV4(
        #     agent_id=agent_id,
        #     gene=gene,
        #     personality=None,
        #     initial_capital=capital,
        #     bulletin_board=self.bulletin_board
        # )
        # return agent
    
    def run(self):
        """
        运行测试主循环
        
        ⚠️ 重要：使用Supervisor.run()或自定义主循环
        """
        logger.info("\n【步骤3】开始测试...")
        
        # 方式1：使用Supervisor.run()（推荐）
        # self.supervisor.run(
        #     duration_minutes=self.config.get('duration_minutes'),
        #     check_interval=self.config.get('check_interval', 60)
        # )
        
        # 方式2：自定义主循环（用于特殊测试）
        self._custom_test_loop()
    
    def _custom_test_loop(self):
        """
        自定义测试循环
        
        ⚠️ 注意：即使自定义循环，也要使用账簿系统！
        """
        symbol = 'BTC/USDT:USDT'
        duration_cycles = self.config.get('duration_cycles', 100)
        
        for cycle in range(1, duration_cycles + 1):
            logger.info(f"\n=== 周期 {cycle}/{duration_cycles} ===")
            
            # 1. 获取市场数据
            ticker = self.exchange.get_ticker(symbol)
            current_price = ticker['last']
            
            # 2. 可选：生成WorldSignature
            # world_signature = self._generate_world_signature(current_price)
            
            # 3. Supervisor分析市场并发布公告
            # self.supervisor.comprehensive_monitoring(market_data)
            
            # 4. Mastermind战略决策（每N周期）
            if cycle % 5 == 0:
                # self.mastermind.strategic_decision()
                pass
            
            # 5. Agent决策和交易
            for agent in self.agents:
                # ✅ 使用账簿系统获取Agent状态
                if hasattr(agent, 'account'):
                    agent_status = agent.account.get_status_for_decision(
                        current_price=current_price,
                        caller_role='SUPERVISOR'  # 从ledger_system导入Role
                    )
                    
                    # Agent决策
                    decision = agent.decide(
                        market_data={'price': current_price},
                        account_status=agent_status
                    )
                    
                    # 执行交易（通过Supervisor或直接）
                    # self.supervisor.receive_trade_request(...)
                    # 或
                    # self._execute_trade(agent, decision, current_price)
            
            # 6. 进化（每N周期）
            if cycle % 30 == 0:
                # self.supervisor.evolution_manager.evolve(self.agents)
                pass
            
            # 7. 统计和日志
            self._log_cycle_stats(cycle)
            
            # 8. 延迟（如果需要）
            time.sleep(self.config.get('cycle_delay', 0))
        
        # 测试结束
        self._finalize_test()
    
    def _execute_trade(self, agent, decision, current_price):
        """
        执行交易
        
        ⚠️ 重要：使用账簿系统记录交易！
        """
        if decision['action'] == 'buy':
            # 执行买入
            order = self.exchange.place_order(
                symbol='BTC/USDT:USDT',
                side='buy',
                size=decision['size'],
                leverage=decision.get('leverage', 1.0)
            )
            
            if order and hasattr(agent, 'account'):
                # ✅ 记录到账簿系统
                agent.account.record_trade(
                    trade_type='buy',
                    amount=decision['size'],
                    price=current_price,
                    confidence=decision.get('confidence', 0.5),
                    is_real=True,
                    caller_role='SUPERVISOR',  # 从ledger_system导入Role
                    okx_order_id=order.get('order_id')
                )
                
                # ✅ 同步资金
                agent.current_capital = agent.account.private_ledger.virtual_capital
        
        # 类似处理sell, short, cover
    
    def _log_cycle_stats(self, cycle):
        """记录周期统计"""
        # 从账簿系统获取统计
        if hasattr(self.supervisor, 'public_ledger'):
            total_trades = len(self.supervisor.public_ledger.all_trades)
            logger.info(f"   总交易数: {total_trades}")
        
        # Agent资金统计
        capitals = [agent.current_capital for agent in self.agents if hasattr(agent, 'current_capital')]
        if capitals:
            avg_capital = sum(capitals) / len(capitals)
            logger.info(f"   平均资金: ${avg_capital:,.2f}")
    
    def _finalize_test(self):
        """测试结束，保存结果"""
        logger.info("\n" + "=" * 80)
        logger.info("🎉 测试完成")
        logger.info("=" * 80)
        
        end_time = datetime.now()
        duration = end_time - self.start_time
        logger.info(f"运行时长: {duration}")
        
        # 保存结果
        result = {
            'start_time': self.start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration.total_seconds(),
            'agent_count': len(self.agents),
            'total_trades': len(self.supervisor.public_ledger.all_trades) if hasattr(self.supervisor, 'public_ledger') else 0,
            # ... 其他统计
        }
        
        # 保存到JSON文件
        import json
        result_file = f"test_result_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"结果已保存: {result_file}")


def main():
    """
    标准测试入口
    
    使用方式：
    1. 配置测试参数
    2. 创建TestRunner
    3. 运行测试
    """
    
    # 测试配置
    config = {
        # 交易模式
        'trading_mode': 'okx_sandbox',  # 'okx_sandbox' | 'okx_real' | 'backtest'
        
        # Agent配置
        'agent_count': 10,
        'initial_capital_per_agent': 10000.0,
        
        # 测试配置
        'duration_cycles': 100,  # 测试周期数
        'cycle_delay': 1,  # 每周期延迟（秒）
        
        # 总资金
        'total_capital': 100000.0,
        
        # 回测配置（如果使用backtest模式）
        # 'backtest_data_path': 'data/okx/BTC-USDT-SWAP_1h.csv',
        # 'backtest_start_date': '2023-01-01',
        # 'backtest_end_date': '2023-12-31',
    }
    
    # 创建并运行测试
    try:
        runner = StandardTestRunner(config)
        runner.run()
    except KeyboardInterrupt:
        logger.info("\n⚠️ 用户中断测试")
    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

