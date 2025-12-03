"""
Prometheus v4.0 - 简化启动器
主循环已移到Supervisor，这里只负责初始化和启动
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prometheus.core.supervisor import Supervisor
from prometheus.core.mastermind import Mastermind
from prometheus.core.bulletin_board_v4 import BulletinBoardV4
from prometheus.core.agent_v4 import AgentV4
from prometheus.core.gene import Gene
from prometheus.core.mock_trading import MockTrading  # ⭐ 模拟交易
from config.config import OKX_PAPER_TRADING, TEST_CONFIG, TRADING_MODE, validate_config
import ccxt
import logging

# 彻夜运行模式：只输出关键信息
logging.basicConfig(
    level=logging.WARNING,  # 全局WARNING级别，减少冗余日志
    format='%(asctime)s - %(levelname)s - %(message)s'  # 简化格式
)

# 设置关键模块的日志级别
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # 启动器保持INFO

# 关键模块保持INFO级别（需要看到输出）
logging.getLogger('prometheus.core.supervisor').setLevel(logging.INFO)
logging.getLogger('prometheus.core.mastermind').setLevel(logging.INFO)  # ⭐ 小预言输出
logging.getLogger('prometheus.core.evolution_manager').setLevel(logging.INFO)  # ⭐ 进化日志输出

# 其他模块降低到WARNING（减少冗余）
logging.getLogger('prometheus.core.bulletin_board_v4').setLevel(logging.WARNING)
logging.getLogger('prometheus.core.agent_v4').setLevel(logging.WARNING)
logging.getLogger('prometheus.core.market_state_analyzer').setLevel(logging.WARNING)
logging.getLogger('prometheus.core.ledger_system').setLevel(logging.WARNING)
logging.getLogger('prometheus.core.indicator_calculator').setLevel(logging.WARNING)
logging.getLogger('prometheus.core.medal_system').setLevel(logging.WARNING)
logging.getLogger('prometheus.core.trading_permissions').setLevel(logging.WARNING)


class OKXPaperTrading:
    """OKX模拟盘交易接口（永续合约）"""
    
    def __init__(self):
        self.exchange = ccxt.okx({
            'apiKey': OKX_PAPER_TRADING['api_key'],
            'secret': OKX_PAPER_TRADING['api_secret'],
            'password': OKX_PAPER_TRADING['passphrase'],
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap',  # 永续合约
                'hedged': True  # ✅ 启用双向持仓模式（可同时持有多空）
            }
        })
        self.exchange.set_sandbox_mode(True)
        logger.info("✅ OKX模拟盘已连接（双向持仓模式）")
    
    def place_market_order(self, symbol, side, amount, reduce_only=False, pos_side=None):
        """下市价单"""
        try:
            params = {
                'tdMode': 'cross'
            }
            
            if reduce_only:
                params['reduceOnly'] = True
            
            if pos_side:
                params['posSide'] = pos_side
            
            order = self.exchange.create_market_order(
                symbol=symbol,
                side=side,
                amount=amount,
                params=params
            )
            
            return order
        
        except Exception as e:
            logger.error(f"❌ 下单失败: {e}")
            return None
    
    def get_all_positions(self):
        """获取所有持仓"""
        try:
            positions = self.exchange.fetch_positions(['BTC/USDT:USDT'])
            return positions
        except Exception as e:
            logger.error(f"获取持仓失败: {e}")
            return []
    
    def close_all_positions(self):
        """清理所有持仓"""
        try:
            positions = self.get_all_positions()
            
            for pos in positions:
                contracts = float(pos.get('contracts', 0))
                if contracts > 0:
                    side = pos.get('side')
                    pos_side = 'long' if side == 'long' else 'short'
                    close_side = 'sell' if side == 'long' else 'buy'
                    
                    self.place_market_order(
                        symbol='BTC/USDT:USDT',
                        side=close_side,
                        amount=contracts,
                        reduce_only=True,
                        pos_side=pos_side
                    )
            
            logger.info("所有持仓已清理")
        except Exception as e:
            logger.error(f"清理持仓失败: {e}")


class PrometheusLauncher:
    """
    Prometheus v4.0 简化启动器
    
    职责：
    1. 初始化所有组件
    2. 配置Supervisor
    3. 启动Supervisor.run()
    """
    
    def __init__(self, config):
        """初始化启动器"""
        logger.info("Prometheus v4.0 - 彻夜运行模式")
        
        self.config = config
        
        # 创建日志目录
        import os
        from datetime import datetime
        log_dir = config.get('log_dir', 'logs/live_trading')
        os.makedirs(log_dir, exist_ok=True)
        
        # 生成日志文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_file = os.path.join(log_dir, f'okx_live_{timestamp}.txt')
        
        logger.info(f"日志: {self.log_file}")
        
        # 1. 创建基础组件（根据TRADING_MODE选择交易源）
        if TRADING_MODE == 'mock':
            logger.info("📊 使用模拟数据模式（快速调试）")
            self.okx = MockTrading(initial_balance=100000.0, initial_price=92800.0)
        else:  # okx
            logger.info("🌐 使用OKX模拟盘模式（真实环境）")
            self.okx = OKXPaperTrading()
        
        self.bulletin_board = BulletinBoardV4()
        
        self.mastermind = Mastermind(
            initial_capital=100000.0,
            decision_mode="human",
            bulletin_board=self.bulletin_board
        )
        
        self.supervisor = Supervisor(
            bulletin_board=self.bulletin_board
        )
        
        # 2. 创世配置
        genesis_config = {
            'min_agent_count': config.get('min_agent_count', 5),
            'max_agent_count': config.get('max_agent_count', 20),
            'min_capital_per_agent': config.get('min_capital_per_agent', 5000),
            'capital_reserve_ratio': config.get('capital_reserve_ratio', 0.1),
            'history_days': config.get('history_days', 7),
            'initial_capital_per_agent': config.get('initial_capital_per_agent', 10000),
            'TRADING_MODE': TRADING_MODE,  # ⭐ 传入交易模式用于动态进化周期
        }
        
        # 3. 执行创世（完整世界初始化）
        genesis_result = self.supervisor.genesis(
            okx_trading=self.okx,
            mastermind=self.mastermind,
            bulletin_board=self.bulletin_board,
            config=genesis_config,
            agent_factory=self._create_single_agent  # 传入Agent工厂函数
        )
        
        # 4. 保存创世结果
        self.genesis_result = genesis_result
        self.agents = self.supervisor.agents
        
        if not genesis_result['success']:
            logger.error(f"创世失败: {genesis_result['errors']}")
            raise Exception("创世失败")
        else:
            logger.info(f"系统初始化完成: {genesis_result['agent_count']}个Agent")
    
    def _create_single_agent(self, agent_id: str, gene, capital: float):
        """
        Agent工厂函数 - 创建单个Agent
        
        供genesis()调用
        """
        # v4.2: 直接传入EvolvableGene对象（不转换为字典）
        # 这样可以保持基因对象的完整性，包括多样性
        agent = AgentV4(
            agent_id=agent_id,
            gene=gene,  # ⭐ 直接传入EvolvableGene对象
            personality=None,  # 让Agent自己生成随机个性
            initial_capital=capital,
            bulletin_board=self.bulletin_board
        )
        
        return agent
    
    def _create_agents(self, count):
        """创建Agent群体（兼容旧代码）"""
        agents = []
        
        for i in range(count):
            agent_id = f"LiveAgent_{i+1:02d}"
            gene = Gene.random()
            agent = self._create_single_agent(agent_id, gene, 10000)
            agents.append(agent)
        
        return agents
    
    def run(self, duration_minutes=None, check_interval=60):
        """
        启动系统（委托给Supervisor）
        
        Args:
            duration_minutes: 运行时长（分钟）
            check_interval: 检查间隔（秒）
        """
        # 委托给Supervisor运营（减少启动日志）
        self.supervisor.run(
            duration_minutes=duration_minutes,
            check_interval=check_interval,
            log_file=self.log_file
        )


def main():
    """主函数"""
    # 验证环境配置
    try:
        validate_config()
    except ValueError as e:
        print(f"\n❌ 配置错误: {e}")
        print("\n请按照 docs/ENV_CONFIGURATION.md 配置 .env 文件")
        return
    
    # 根据交易模式动态调整周期
    trading_mode = os.getenv('TRADING_MODE', 'mock').lower()
    if trading_mode == 'mock':
        check_interval = 5  # Mock模式：5秒快速测试
        logger.info("⚡ Mock模式 - 使用5秒快速周期")
    else:
        check_interval = 20  # OKX模式：20秒正常周期
        logger.info("🌐 OKX模式 - 使用20秒标准周期")
    
    # 配置（优化版）
    config = {
        'agent_count': TEST_CONFIG.get('agent_count', 10),
        'initial_capital_per_agent': 10000,
        'duration_minutes': None,  # 无限运行，直到按Ctrl+C
        'check_interval': check_interval,  # 根据模式动态调整
        'log_dir': 'logs/live_trading'  # 日志目录
    }
    
    # 创建启动器
    launcher = PrometheusLauncher(config)
    
    # 启动运营
    launcher.run(
        duration_minutes=config['duration_minutes'],
        check_interval=config['check_interval']
    )


if __name__ == "__main__":
    main()

