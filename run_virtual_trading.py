"""
Main entry point for Prometheus v3.0 Virtual Trading
"""

import os
import sys
import logging
import argparse
from datetime import datetime

# Add prometheus_v30 to path
sys.path.insert(0, '/home/ubuntu')

from prometheus_v30.live_trading_system import LiveTradingSystem
from prometheus_v30.config_virtual import CONFIG_VIRTUAL_TRADING


def setup_logging(config):
    """设置日志"""
    log_dir = config['logging']['dir']
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(
        log_dir,
        f"{config['logging']['file_prefix']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    
    # 配置日志格式
    logging.basicConfig(
        level=getattr(logging, config['logging']['level']),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging to {log_file}")
    
    return logger


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Prometheus v3.0 Virtual Trading')
    parser.add_argument('--duration', type=int, default=3600, help='Trading duration in seconds (default: 3600)')
    parser.add_argument('--log-level', type=str, default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], help='Log level')
    args = parser.parse_args()
    
    # 更新配置
    CONFIG_VIRTUAL_TRADING['logging']['level'] = args.log_level
    
    # 设置日志
    logger = setup_logging(CONFIG_VIRTUAL_TRADING)
    
    logger.info("=" * 60)
    logger.info("Prometheus v3.0 Virtual Trading System")
    logger.info("=" * 60)
    logger.info(f"Duration: {args.duration} seconds ({args.duration/60:.1f} minutes)")
    logger.info(f"Initial capital: ${CONFIG_VIRTUAL_TRADING['initial_capital']}")
    logger.info(f"Initial agents: {CONFIG_VIRTUAL_TRADING['initial_agents']}")
    logger.info("=" * 60)
    
    # 获取OKX API凭证
    okx_config = {
        'api_key': os.getenv('OKX_API_KEY'),
        'secret_key': os.getenv('OKX_SECRET_KEY'),
        'passphrase': os.getenv('OKX_PASSPHRASE'),
        'flag': '1',  # 模拟盘
        'risk_config': CONFIG_VIRTUAL_TRADING['risk']
    }
    
    # 验证API凭证
    if not all([okx_config['api_key'], okx_config['secret_key'], okx_config['passphrase']]):
        logger.error("OKX API credentials not found in environment variables")
        logger.error("Please set: OKX_API_KEY, OKX_SECRET_KEY, OKX_PASSPHRASE")
        sys.exit(1)
    
    try:
        # 创建交易系统
        system = LiveTradingSystem(CONFIG_VIRTUAL_TRADING, okx_config)
        
        # 运行交易
        system.run(duration_seconds=args.duration)
        
        logger.info("Trading completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
