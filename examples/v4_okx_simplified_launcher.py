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
from config.okx_config import OKX_PAPER_TRADING, TEST_CONFIG
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

# 其他模块降低到WARNING
logging.getLogger('prometheus.core.supervisor').setLevel(logging.INFO)
logging.getLogger('prometheus.core.bulletin_board_v4').setLevel(logging.WARNING)
logging.getLogger('prometheus.core.agent_v4').setLevel(logging.WARNING)
logging.getLogger('prometheus.core.market_state_analyzer').setLevel(logging.WARNING)
logging.getLogger('prometheus.core.ledger_system').setLevel(logging.WARNING)
logging.getLogger('prometheus.core.mastermind').setLevel(logging.WARNING)
logging.getLogger('prometheus.core.indicator_calculator').setLevel(logging.WARNING)
logging.getLogger('prometheus.core.medal_system').setLevel(logging.WARNING)
logging.getLogger('prometheus.core.trading_permissions').setLevel(logging.WARNING)


class OKXPaperTrading:
    """OKX模拟盘交易接口"""
    
    def __init__(self):
        self.exchange = ccxt.okx({
            'apiKey': OKX_PAPER_TRADING['api_key'],
            'secret': OKX_PAPER_TRADING['api_secret'],
            'password': OKX_PAPER_TRADING['passphrase'],
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })
        self.exchange.set_sandbox_mode(True)
        logger.info("OKX模拟盘已连接")
    
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
            
            # 只在日志文件中记录，不输出到控制台
            action = "平仓" if reduce_only else "开仓"
            # logger.info不再输出（已设为WARNING级别）
            return order
        
        except Exception as e:
            logger.error(f"❌ 下单失败: {e}")
            return None
    
    def close_all_positions(self):
        """清理所有持仓"""
        try:
            positions = self.exchange.fetch_positions(['BTC/USDT:USDT'])
            
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
        
        # 1. 创建OKX交易接口并清理持仓
        self.okx = OKXPaperTrading()
        self.okx.close_all_positions()
        
        # 2. 创建系统组件
        self.bulletin_board = BulletinBoardV4()
        
        self.mastermind = Mastermind(
            initial_capital=100000.0,
            decision_mode="human",
            bulletin_board=self.bulletin_board
        )
        
        self.supervisor = Supervisor(
            bulletin_board=self.bulletin_board
        )
        
        # 3. 创建Agent群体
        self.agents = self._create_agents(config['agent_count'])
        
        # 4. 配置Supervisor
        self.supervisor.set_components(
            okx_trading=self.okx,
            mastermind=self.mastermind,
            agents=self.agents,
            config=config
        )
        
        logger.info(f"系统初始化完成: {config['agent_count']}个Agent")
    
    def _create_agents(self, count):
        """创建Agent群体"""
        agents = []
        
        for i in range(count):
            agent_id = f"LiveAgent_{i+1:02d}"
            
            # 创建基因（随机）
            gene = Gene.random()
            
            # 将Gene对象转换为字典（Agent代码期望字典格式）
            gene_dict = gene.to_dict()
            
            # 创建个性（AgentV4会自动生成随机个性，不需要传入）
            # personality参数在AgentV4中是可选的，会自动生成
            
            # 创建Agent
            agent = AgentV4(
                agent_id=agent_id,
                gene=gene_dict,  # 传入字典格式的基因
                personality=None,  # 让Agent自己生成随机个性
                initial_capital=10000,
                bulletin_board=self.bulletin_board
            )
            
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
    # 配置（优化版）
    config = {
        'agent_count': TEST_CONFIG.get('agent_count', 10),
        'initial_capital_per_agent': 10000,
        'duration_minutes': None,  # 无限运行，直到按Ctrl+C
        'check_interval': 20,  # 20秒间隔（快速迭代）
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

