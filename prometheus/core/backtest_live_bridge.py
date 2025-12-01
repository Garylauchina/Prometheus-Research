"""
Backtest-Live Bridge Module

职责：提供回测与实盘交易系统之间的桥接功能，确保策略在两种环境下表现一致

设计思路：
1. 统一的市场数据接口：确保回测和实盘使用相同的数据结构和格式
2. 模拟订单执行：在回测环境中模拟实盘订单执行逻辑
3. 策略评估桥接：提供一致的策略评估和报告生成机制
4. 参数同步：确保回测和实盘使用相同的策略参数和风控规则
"""

import logging
import time
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class BacktestLiveBridge:
    """回测与实盘桥接器"""
    
    def __init__(self, config: Dict):
        """
        初始化桥接器
        
        Args:
            config: 配置字典，包含回测和实盘的配置
        """
        self.config = config
        self.mode = config.get('mode', 'backtest')  # 'backtest' 或 'live'
        self.price_history = []
        self.is_initialized = False
        self.bridge_stats = {
            'data_points_processed': 0,
            'orders_executed': 0,
            'simulated_slippage': 0.0,
            'bridge_errors': 0
        }
    
    def initialize(self):
        """初始化桥接器"""
        logger.info(f"初始化回测-实盘桥接器 (模式: {self.mode})")
        self.is_initialized = True
        return True
    
    def format_market_data(self, data: Any) -> Dict:
        """
        格式化市场数据，确保回测和实盘使用相同的数据结构
        
        Args:
            data: 原始市场数据（回测或实盘）
            
        Returns:
            标准化的市场数据字典
        """
        try:
            if self.mode == 'backtest':
                # 处理回测数据格式
                if isinstance(data, dict):
                    return {
                        'timestamp': data.get('timestamp', 0),
                        'price': data.get('price', 0.0),
                        'open': data.get('open', 0.0),
                        'high': data.get('high', 0.0),
                        'low': data.get('low', 0.0),
                        'close': data.get('close', 0.0),
                        'volume': data.get('volume', 0.0)
                    }
                elif isinstance(data, (int, float)):
                    # 简单价格格式
                    return {
                        'timestamp': int(time.time()),
                        'price': float(data),
                        'open': float(data),
                        'high': float(data),
                        'low': float(data),
                        'close': float(data),
                        'volume': 0.0
                    }
            else:
                # 处理实盘数据格式（假设来自OKX API）
                if isinstance(data, dict):
                    # 处理OKX API格式
                    return {
                        'timestamp': int(data.get('ts', time.time() * 1000)) // 1000,
                        'price': float(data.get('last', 0.0) or data.get('price', 0.0)),
                        'open': float(data.get('open24h', 0.0)),
                        'high': float(data.get('high24h', 0.0)),
                        'low': float(data.get('low24h', 0.0)),
                        'close': float(data.get('last', 0.0) or data.get('price', 0.0)),
                        'volume': float(data.get('vol24h', 0.0))
                    }
            
            # 默认返回
            return {
                'timestamp': int(time.time()),
                'price': 0.0,
                'open': 0.0,
                'high': 0.0,
                'low': 0.0,
                'close': 0.0,
                'volume': 0.0
            }
        except Exception as e:
            logger.error(f"格式化市场数据失败: {e}")
            self.bridge_stats['bridge_errors'] += 1
            return {
                'timestamp': int(time.time()),
                'price': 0.0,
                'open': 0.0,
                'high': 0.0,
                'low': 0.0,
                'close': 0.0,
                'volume': 0.0
            }
    
    def build_market_features(self, price_history: List[Dict], current_index: int) -> Dict[str, float]:
        """
        构建市场特征，为策略提供标准化的输入
        
        Args:
            price_history: 价格历史数据列表
            current_index: 当前索引
            
        Returns:
            市场特征字典
        """
        try:
            if current_index < 0 or current_index >= len(price_history):
                return {}
            
            features = {}
            
            # 提取价格序列
            prices = [item['price'] for item in price_history if 'price' in item and item['price'] > 0]
            
            if len(prices) < 2:
                return {}
            
            # 基本价格信息
            current_price = prices[current_index]
            features['current_price'] = current_price
            
            # 价格变化
            if current_index > 0:
                prev_price = prices[current_index - 1]
                features['price_change_pct'] = (current_price - prev_price) / prev_price
            
            # 移动平均线
            for window in [5, 10, 20, 50]:
                if current_index >= window - 1:
                    ma = sum(prices[current_index - window + 1:current_index + 1]) / window
                    features[f'ma_{window}'] = ma
                    features[f'price_ma_{window}_ratio'] = (current_price - ma) / ma
            
            # 波动率（标准差）
            volatility_window = 20
            if current_index >= volatility_window - 1:
                recent_prices = prices[current_index - volatility_window + 1:current_index + 1]
                mean_price = sum(recent_prices) / len(recent_prices)
                variance = sum((p - mean_price) ** 2 for p in recent_prices) / len(recent_prices)
                volatility = np.sqrt(max(0, variance)) / mean_price
                features['volatility'] = volatility
            
            # 趋势强度
            trend_window = 30
            if current_index >= trend_window - 1:
                start_price = prices[current_index - trend_window + 1]
                trend_strength = (current_price - start_price) / start_price
                features['trend_strength'] = trend_strength
            
            self.bridge_stats['data_points_processed'] += 1
            return features
        except Exception as e:
            logger.error(f"构建市场特征失败: {e}")
            self.bridge_stats['bridge_errors'] += 1
            return {}
    
    def execute_order(self, order: Dict, current_price: float) -> Dict:
        """
        执行订单（回测中模拟，实盘中调用API）
        
        Args:
            order: 订单信息字典
            current_price: 当前价格
            
        Returns:
            订单执行结果
        """
        try:
            order_id = f"order_{int(time.time() * 1000000)}"
            timestamp = int(time.time())
            
            if self.mode == 'backtest':
                # 回测模式：模拟订单执行
                # 添加滑点模拟
                slippage_pct = self.config.get('backtest', {}).get('slippage_pct', 0.001)
                side = order.get('side', 'buy')
                
                # 根据买卖方向添加滑点
                if side == 'buy':
                    executed_price = current_price * (1 + slippage_pct)
                else:
                    executed_price = current_price * (1 - slippage_pct)
                
                self.bridge_stats['simulated_slippage'] += abs(executed_price - current_price)
                
                # 模拟即时成交
                result = {
                    'order_id': order_id,
                    'status': 'filled',
                    'side': side,
                    'price': executed_price,
                    'quantity': order.get('quantity', 0.0),
                    'timestamp': timestamp,
                    'type': order.get('type', 'market'),
                    'filled_amount': order.get('quantity', 0.0),
                    'fee': executed_price * order.get('quantity', 0.0) * self.config.get('backtest', {}).get('fee_pct', 0.0002)
                }
            else:
                # 实盘模式：这里应该调用实际的交易适配器
                # 占位实现，实际应集成到live_trading_system中
                result = {
                    'order_id': order_id,
                    'status': 'submitted',  # 实际状态由交易所返回
                    'side': order.get('side', 'buy'),
                    'price': current_price,
                    'quantity': order.get('quantity', 0.0),
                    'timestamp': timestamp,
                    'type': order.get('type', 'market')
                }
            
            self.bridge_stats['orders_executed'] += 1
            return result
        except Exception as e:
            logger.error(f"执行订单失败: {e}")
            self.bridge_stats['bridge_errors'] += 1
            return {
                'order_id': f"failed_{int(time.time())}",
                'status': 'failed',
                'error': str(e),
                'timestamp': int(time.time())
            }
    
    def convert_strategy_signal(self, signal: float, market_regime: str = 'sideways') -> Dict:
        """
        将策略信号转换为标准化的交易指令
        
        Args:
            signal: 策略信号 (-1.0 到 1.0)
            market_regime: 市场状态
            
        Returns:
            交易指令字典
        """
        try:
            # 信号归一化
            normalized_signal = max(-1.0, min(1.0, signal))
            
            # 市场状态对应的信号阈值调整
            regime_adjustments = {
                'strong_bull': 0.1,    # 牛市信号更容易触发做多
                'weak_bull': 0.05,
                'sideways': 0.15,
                'weak_bear': -0.05,
                'strong_bear': -0.1    # 熊市信号更容易触发做空
            }
            
            adjustment = regime_adjustments.get(market_regime, 0.15)
            
            # 确定交易方向
            if normalized_signal > adjustment:
                side = 'buy'
                confidence = min(1.0, normalized_signal)
            elif normalized_signal < -adjustment:
                side = 'sell'
                confidence = min(1.0, abs(normalized_signal))
            else:
                side = 'hold'
                confidence = 0.0
            
            return {
                'side': side,
                'confidence': confidence,
                'signal_strength': normalized_signal,
                'market_regime': market_regime,
                'timestamp': int(time.time())
            }
        except Exception as e:
            logger.error(f"转换策略信号失败: {e}")
            self.bridge_stats['bridge_errors'] += 1
            return {
                'side': 'hold',
                'confidence': 0.0,
                'signal_strength': 0.0,
                'market_regime': 'unknown',
                'timestamp': int(time.time())
            }
    
    def validate_parameters(self, parameters: Dict) -> Tuple[bool, str]:
        """
        验证策略参数在回测和实盘环境中的有效性
        
        Args:
            parameters: 策略参数字典
            
        Returns:
            (是否有效, 错误信息)
        """
        try:
            # 检查必要参数
            required_params = ['long_threshold', 'short_threshold', 'stop_loss_pct', 'take_profit_pct']
            for param in required_params:
                if param not in parameters:
                    return False, f"缺少必要参数: {param}"
            
            # 检查参数范围
            if parameters.get('long_threshold', 0) < 0 or parameters.get('long_threshold', 0) > 1:
                return False, "long_threshold必须在0-1之间"
            
            if parameters.get('short_threshold', 0) < -1 or parameters.get('short_threshold', 0) > 0:
                return False, "short_threshold必须在-1-0之间"
            
            if parameters.get('stop_loss_pct', 0) <= 0 or parameters.get('stop_loss_pct', 0) > 1:
                return False, "stop_loss_pct必须在0-1之间"
            
            if parameters.get('take_profit_pct', 0) <= 0 or parameters.get('take_profit_pct', 0) > 10:
                return False, "take_profit_pct必须在0-10之间"
            
            # 实盘特有验证
            if self.mode == 'live':
                leverage = parameters.get('leverage', 1)
                if leverage < 1 or leverage > 100:
                    return False, "实盘杠杆必须在1-100之间"
            
            return True, "参数验证通过"
        except Exception as e:
            logger.error(f"验证参数失败: {e}")
            return False, f"验证错误: {str(e)}"
    
    def compare_performance(self, backtest_results: Dict, live_results: Dict) -> Dict:
        """
        比较回测和实盘性能
        
        Args:
            backtest_results: 回测结果
            live_results: 实盘结果
            
        Returns:
            性能比较报告
        """
        try:
            comparison = {
                'backtest_roi': backtest_results.get('system_roi', 0),
                'live_roi': live_results.get('system_roi', 0),
                'roi_difference': live_results.get('system_roi', 0) - backtest_results.get('system_roi', 0),
                'backtest_trades': backtest_results.get('total_trades', 0),
                'live_trades': live_results.get('total_trades', 0),
                'trade_frequency_ratio': live_results.get('total_trades', 0) / max(1, backtest_results.get('total_trades', 0)),
                'backtest_win_rate': backtest_results.get('win_rate', 0),
                'live_win_rate': live_results.get('win_rate', 0),
                'win_rate_difference': live_results.get('win_rate', 0) - backtest_results.get('win_rate', 0),
                'backtest_sharpe': backtest_results.get('sharpe_ratio', 0),
                'live_sharpe': live_results.get('sharpe_ratio', 0),
                'timestamp': int(time.time())
            }
            
            # 计算偏差分数
            deviation_score = (
                abs(comparison['roi_difference']) * 100 +
                abs(comparison['trade_frequency_ratio'] - 1) * 50 +
                abs(comparison['win_rate_difference']) * 20
            )
            
            comparison['deviation_score'] = deviation_score
            
            # 偏差评估
            if deviation_score < 10:
                comparison['deviation_level'] = 'low'
            elif deviation_score < 30:
                comparison['deviation_level'] = 'moderate'
            else:
                comparison['deviation_level'] = 'high'
            
            return comparison
        except Exception as e:
            logger.error(f"比较性能失败: {e}")
            return {
                'error': str(e),
                'timestamp': int(time.time())
            }
    
    def get_bridge_stats(self) -> Dict:
        """
        获取桥接器统计信息
        
        Returns:
            统计信息字典
        """
        return self.bridge_stats.copy()
    
    def reset(self):
        """
        重置桥接器状态
        """
        logger.info("重置回测-实盘桥接器")
        self.price_history = []
        self.bridge_stats = {
            'data_points_processed': 0,
            'orders_executed': 0,
            'simulated_slippage': 0.0,
            'bridge_errors': 0
        }
        return True


def create_bridge_adapter(config: Dict) -> BacktestLiveBridge:
    """
    创建桥接适配器工厂函数
    
    Args:
        config: 配置字典
        
    Returns:
        桥接适配器实例
    """
    bridge = BacktestLiveBridge(config)
    bridge.initialize()
    return bridge


def load_historical_data(file_path: str, format_type: str = 'csv') -> List[Dict]:
    """
    加载历史数据，为回测做准备
    
    Args:
        file_path: 文件路径
        format_type: 文件格式 ('csv', 'json')
        
    Returns:
        格式化的历史数据列表
    """
    try:
        data = []
        
        if format_type == 'csv':
            df = pd.read_csv(file_path)
            # 确保必要列存在
            required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in df.columns:
                    logger.warning(f"CSV文件缺少列: {col}")
            
            # 转换为标准格式
            for _, row in df.iterrows():
                entry = {
                    'timestamp': int(row.get('timestamp', 0)),
                    'price': float(row.get('close', 0) or row.get('price', 0)),
                    'open': float(row.get('open', 0)),
                    'high': float(row.get('high', 0)),
                    'low': float(row.get('low', 0)),
                    'close': float(row.get('close', 0) or row.get('price', 0)),
                    'volume': float(row.get('volume', 0))
                }
                data.append(entry)
        
        elif format_type == 'json':
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                if isinstance(raw_data, list):
                    for item in raw_data:
                        entry = {
                            'timestamp': int(item.get('timestamp', 0)),
                            'price': float(item.get('price', 0)),
                            'open': float(item.get('open', 0)),
                            'high': float(item.get('high', 0)),
                            'low': float(item.get('low', 0)),
                            'close': float(item.get('close', 0) or item.get('price', 0)),
                            'volume': float(item.get('volume', 0))
                        }
                        data.append(entry)
        
        logger.info(f"加载历史数据完成: {len(data)} 条记录")
        return data
    except Exception as e:
        logger.error(f"加载历史数据失败: {e}")
        return []


def convert_live_to_backtest_config(live_config: Dict) -> Dict:
    """
    将实盘配置转换为回测配置
    
    Args:
        live_config: 实盘配置
        
    Returns:
        回测配置
    """
    try:
        backtest_config = live_config.copy()
        
        # 修改模式
        backtest_config['mode'] = 'backtest'
        
        # 添加回测特定配置
        backtest_config['backtest'] = backtest_config.get('backtest', {})
        backtest_config['backtest'].update({
            'slippage_pct': 0.001,  # 1%滑点模拟
            'fee_pct': 0.0002,      # 0.02%手续费
            'start_date': 'auto',   # 自动从数据开始
            'end_date': 'auto'      # 自动到数据结束
        })
        
        # 禁用实时功能
        if 'live_only' in backtest_config:
            for key in backtest_config['live_only']:
                if key in backtest_config:
                    del backtest_config[key]
        
        return backtest_config
    except Exception as e:
        logger.error(f"转换配置失败: {e}")
        return live_config.copy()