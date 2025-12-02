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
from prometheus.agents.live_agent_v4 import LiveAgentV4
from prometheus.core.gene import Gene
from config.okx_config import OKX_CONFIG, TEST_CONFIG
import ccxt
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OKXPaperTrading:
    """OKX模拟盘交易接口"""
    
    def __init__(self):
        self.exchange = ccxt.okx({
            'apiKey': OKX_CONFIG['api_key'],
            'secret': OKX_CONFIG['secret_key'],
            'password': OKX_CONFIG['passphrase'],
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })
        self.exchange.set_sandbox_mode(True)
        logger.info("✅ OKX模拟盘已连接")
    
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
            
            action = "平仓" if reduce_only else "开仓"
            logger.info(f"✅ {action} {side} {amount} {symbol} 成功")
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
                    logger.info(f"✅ 已平仓: {side} {contracts} BTC")
            
            logger.info("✅ 所有持仓已清理")
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
        logger.info("="*70)
        logger.info("  Prometheus v4.0 - 简化启动器")
        logger.info("="*70)
        
        self.config = config
        
        # 1. 创建OKX交易接口
        logger.info("1. 创建OKX交易接口...")
        self.okx = OKXPaperTrading()
        self.okx.close_all_positions()  # 清理持仓
        
        # 2. 创建系统组件
        logger.info("2. 创建系统组件...")
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
        logger.info(f"3. 创建Agent群体 ({config['agent_count']}个)...")
        self.agents = self._create_agents(config['agent_count'])
        
        # 4. 配置Supervisor
        logger.info("4. 配置Supervisor...")
        self.supervisor.set_components(
            okx_trading=self.okx,
            mastermind=self.mastermind,
            agents=self.agents,
            config=config
        )
        
        logger.info("✅ 所有组件已初始化")
        logger.info("="*70)
    
    def _create_agents(self, count):
        """创建Agent群体"""
        agents = []
        
        for i in range(count):
            agent_id = f"LiveAgent_{i+1:02d}"
            
            # 创建基因
            gene = Gene.create_genesis_gene(agent_id)
            
            # 创建个性
            personality = {
                'risk_tolerance': 0.5 + (i * 0.05),
                'optimism': 0.5 + (i * 0.03),
                'discipline': 0.7 + (i * 0.02),
            }
            
            # 创建Agent
            agent = LiveAgentV4(
                agent_id=agent_id,
                gene=gene,
                personality=personality,
                initial_capital=10000,
                bulletin_board=self.bulletin_board
            )
            
            agents.append(agent)
        
        logger.info(f"✅ 创建了{count}个Agent")
        return agents
    
    def run(self, duration_minutes=None, check_interval=60):
        """
        启动系统（委托给Supervisor）
        
        Args:
            duration_minutes: 运行时长（分钟）
            check_interval: 检查间隔（秒）
        """
        logger.info("启动Supervisor运营系统...")
        
        # 委托给Supervisor运营
        self.supervisor.run(
            duration_minutes=duration_minutes,
            check_interval=check_interval
        )


def main():
    """主函数"""
    # 配置
    config = {
        'agent_count': TEST_CONFIG.get('agent_count', 10),
        'initial_capital_per_agent': 10000,
        'duration_minutes': TEST_CONFIG.get('duration_minutes'),
        'check_interval': TEST_CONFIG.get('check_interval', 120),
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

