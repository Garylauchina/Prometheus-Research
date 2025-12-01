"""
Account Sync for OKX API
"""

import logging
# 使用兼容性模块来解决导入问题
from .okx_compat import Account
from .errors import APIError

logger = logging.getLogger(__name__)


class AccountSync:
    """账户同步器"""
    
    def __init__(self, config):
        """
        初始化
        
        Args:
            config: 配置字典
                - api_key: API密钥
                - secret_key: 密钥
                - passphrase: 密码
                - flag: '0'实盘, '1'模拟盘
        """
        self.config = config
        # 确保flag始终是字符串类型
        flag = str(config.get('flag', '1'))
        self.account_api = Account.AccountAPI(
            config['api_key'],
            config['secret_key'],
            config['passphrase'],
            flag=flag
        )
        self.balance_cache = {}
        self.positions_cache = {}
        
        logger.info(f"账户同步器初始化完成 (flag={config.get('flag', '1')})")
    
    def get_balance(self, ccy=None):
        """
        获取账户余额
        
        Args:
            ccy: 币种（可选），如'USDT'。如果不指定则返回所有币种
        
        Returns:
            dict: 余额信息
                - available: 可用余额
                - frozen: 冻结余额
                - equity: 权益
        """
        try:
            result = self.account_api.get_account_balance(ccy=ccy)
            
            if result['code'] == '0' and len(result['data']) > 0:
                balances = {}
                
                for item in result['data'][0]['details']:
                    currency = item['ccy']
                    balances[currency] = {
                        'available': float(item.get('availBal', 0)),
                        'frozen': float(item.get('frozenBal', 0)),
                        'equity': float(item.get('eq', 0))
                    }
                
                # 更新缓存
                self.balance_cache = balances
                
                # 如果指定了币种，只返回该币种
                if ccy:
                    return balances.get(ccy, {'available': 0, 'frozen': 0, 'equity': 0})
                
                return balances
            else:
                error_msg = result.get('msg', 'Unknown error')
                logger.error(f"Failed to get balance: {error_msg}")
                # 返回缓存
                if ccy:
                    return self.balance_cache.get(ccy, {'available': 0, 'frozen': 0, 'equity': 0})
                return self.balance_cache
        
        except Exception as e:
            logger.error(f"Exception in get_balance: {e}")
            # 返回缓存
            if ccy:
                return self.balance_cache.get(ccy, {'available': 0, 'frozen': 0, 'equity': 0})
            return self.balance_cache
    
    def get_positions(self, inst_type=None):
        """
        获取持仓
        
        Args:
            inst_type: 产品类型（可选）
                - 'spot': 现货
                - 'swap': 永续合约
                - 'futures': 交割合约
        
        Returns:
            dict: 持仓信息
                - size: 持仓数量
                - avg_price: 平均价格
                - unrealized_pnl: 未实现盈亏
                - leverage: 杠杆倍数
                - side: 持仓方向
        """
        try:
            # 确保inst_type参数值转换为大写，符合OKX API要求
            if inst_type is not None:
                inst_type = inst_type.upper()
            result = self.account_api.get_positions(instType=inst_type)
            
            if result['code'] == '0':
                positions = {}
                
                for pos in result['data']:
                    inst_id = pos['instId']
                    
                    # 只记录有持仓的
                    pos_size = float(pos.get('pos', 0))
                    if pos_size == 0:
                        continue
                    
                    positions[inst_id] = {
                        'size': pos_size,
                        'avg_price': float(pos.get('avgPx', 0)),
                        'unrealized_pnl': float(pos.get('upl', 0)),
                        'leverage': float(pos.get('lever', 1)),
                        'side': pos.get('posSide', 'unknown')
                    }
                
                # 更新缓存
                self.positions_cache = positions
                
                return positions
            else:
                error_msg = result.get('msg', 'Unknown error')
                logger.error(f"Failed to get positions: {error_msg}")
                # 返回缓存
                return self.positions_cache
        
        except Exception as e:
            logger.error(f"Exception in get_positions: {e}")
            # 返回缓存
            return self.positions_cache
    
    def get_account_summary(self):
        """
        获取账户摘要
        
        Returns:
            dict: 账户摘要
                - total_equity: 总权益
                - total_unrealized_pnl: 总未实现盈亏
                - balance: 余额详情
                - positions: 持仓详情
        """
        try:
            balance = self.get_balance()
            positions = self.get_positions()
            
            # 计算总权益
            total_equity = sum(b['equity'] for b in balance.values())
            
            # 计算总未实现盈亏
            total_unrealized_pnl = sum(p['unrealized_pnl'] for p in positions.values())
            
            summary = {
                'total_equity': total_equity,
                'total_unrealized_pnl': total_unrealized_pnl,
                'balance': balance,
                'positions': positions
            }
            
            logger.info(f"账户摘要: equity={total_equity:.2f}, unrealized_pnl={total_unrealized_pnl:.2f}")
            
            return summary
        
        except Exception as e:
            logger.error(f"获取账户摘要错误: {e}")
            raise
    
    def get_usdt_balance(self):
        """
        获取USDT余额（快捷方法）
        
        Returns:
            float: USDT可用余额
        """
        balance = self.get_balance(ccy='USDT')
        return balance.get('available', 0.0)
