"""
Main entry point for Prometheus v3.0 Virtual Trading
"""

import os
import sys
import logging
import argparse
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.abspath('.'))

from live_trading_system import LiveTradingSystem
from config_virtual import CONFIG_VIRTUAL_TRADING


def setup_logging(config):
    """设置日志"""
    # 获取日志目录，支持相对路径和绝对路径
    log_dir = config['logging']['dir']
    # 如果是Linux风格的绝对路径且在Windows环境下运行，转换为Windows风格路径
    if os.name == 'nt' and log_dir.startswith('/'):
        # 将Linux路径转换为Windows路径（例如 /home/user 转换为 C:\home\user）
        log_dir = 'C:' + log_dir.replace('/', '\\')
    # 如果是相对路径，则相对于当前脚本所在目录
    if not os.path.isabs(log_dir):
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), log_dir)
    
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(
        log_dir,
        f"{config['logging']['file_prefix']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    
    # 创建logger实例
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config['logging']['level']))
    
    # 清除现有handler
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 创建格式器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 创建文件handler，支持日志轮转
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=config['logging'].get('max_size_mb', 100) * 1024 * 1024,
        backupCount=config['logging'].get('backup_count', 10)
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 创建控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 使用根logger或特定logger都可以，这里保持返回__name__ logger以保持一致性
    app_logger = logging.getLogger(__name__)
    app_logger.info(f"Logging to {log_file}")
    
    return app_logger


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
    logger.info("Prometheus v3.0 虚拟交易系统")
    logger.info("=" * 60)
    logger.info(f"运行时长: {args.duration} 秒 ({args.duration/60:.1f} 分钟)")
    logger.info(f"初始资金: ${CONFIG_VIRTUAL_TRADING['initial_capital']}")
    logger.info(f"初始代理数量: {CONFIG_VIRTUAL_TRADING['initial_agents']}")
    logger.info("=" * 60)
    
    # 从配置文件获取OKX API凭证
    okx_config = CONFIG_VIRTUAL_TRADING['okx_api'].copy()
    okx_config['risk_config'] = CONFIG_VIRTUAL_TRADING['risk']
    
    # 验证API凭证
    if not all([okx_config['api_key'], okx_config['secret_key'], okx_config['passphrase']]):
        logger.error("在config_virtual.py中未找到OKX API凭证")
        logger.error("请检查config_virtual.py中的okx_api部分")
        sys.exit(1)
    
    try:
        # 创建交易系统
        system = LiveTradingSystem(CONFIG_VIRTUAL_TRADING, okx_config)
        
        # 运行交易
        system.run(duration_seconds=args.duration)
        
        logger.info("交易成功完成")
        
    except KeyboardInterrupt:
        logger.info("用户中断程序")
    except Exception as e:
        logger.error(f"致命错误: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
