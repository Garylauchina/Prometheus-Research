"""
Prophet（先知）- 第1层：战略层
================================

职责：
1. 分析市场（计算WorldSignature）
2. 制定战略（创世、进化、风险管理）
3. 匹配历史经验（相似度计算）⭐ v6.0新增
4. 发布战略到BulletinBoard
5. 不涉及具体基因操作（由Moirai负责）

设计原则：
- 看宏观：市场趋势、风险、机会
- 出战略：进攻还是防守、激进还是保守
- 匹配经验：基于WorldSignature相似度
- 不管微观：不管用哪个基因（由Moirai决策）
"""

import logging
from typing import Optional, Dict, List, Tuple
import numpy as np
import json

from prometheus.core.world_signature_simple import WorldSignatureSimple
from prometheus.core.bulletin_board import BulletinBoard, BulletinType, Priority
from prometheus.core.experience_db import ExperienceDB

logger = logging.getLogger(__name__)


class Prophet:
    """
    先知（Prophet）- 战略层
    
    四层架构中的第1层，负责：
    - 市场分析：计算WorldSignature，识别市场状态
    - 战略制定：创世策略、进化策略、风险管理策略
    - 战略发布：通过BulletinBoard向Moirai和Agent发布战略
    
    不负责：
    - 具体基因操作（由Moirai负责）
    - Agent创建（由Moirai负责）
    - 交易执行（由Agent负责）
    """
    
    def __init__(
        self,
        bulletin_board: BulletinBoard,
        instrument: str = "BTC-USDT"
    ):
        """
        初始化Prophet
        
        Args:
            bulletin_board: 公告板（用于发布战略）
            instrument: 交易对
        """
        self.bulletin_board = bulletin_board
        self.instrument = instrument
        
        # 战略状态
        self.current_strategy = None
        self.current_ws = None
        self.market_state = None
        
        logger.info("🔮 Prophet（先知）已初始化")
        logger.info(f"   交易对: {instrument}")
        logger.info(f"   职责: 战略层（市场分析 + 战略制定）")
    
    # ========== 创世战略 ==========
    
    def genesis_strategy(
        self,
        initial_market_data,
        agent_count: int = 50,
        genesis_mode: str = 'adaptive'
    ) -> Dict:
        """
        制定创世战略
        
        流程：
        1. 计算初始WorldSignature
        2. 分析市场状态（牛市/熊市/震荡）
        3. 评估风险等级
        4. 制定创世策略（不包含具体基因）
        5. 发布到BulletinBoard
        
        Args:
            initial_market_data: 初始市场数据（DataFrame，前N根K线）
            agent_count: 计划创建的Agent数量
            genesis_mode: 创世模式
                - 'adaptive': 70%历史最佳 + 20%变异 + 10%随机（默认）
                - 'aggressive': 90%历史最佳 + 10%随机
                - 'exploratory': 50%历史最佳 + 50%随机
                - 'pure_random': 100%随机（无ExperienceDB时）
        
        Returns:
            创世战略字典
        """
        logger.info("="*70)
        logger.info("🔮 Prophet制定创世战略")
        logger.info("="*70)
        
        # 1. 计算初始WorldSignature
        try:
            # 使用前100根K线计算WorldSignature
            ws_window = initial_market_data.tail(100) if len(initial_market_data) > 100 else initial_market_data
            self.current_ws = WorldSignatureSimple.from_market_data(ws_window)
            
            logger.info(f"✅ WorldSignature计算完成（基于{len(ws_window)}根K线）")
            logger.info(f"   趋势7d: {self.current_ws.vector[0]:.2f}")
            logger.info(f"   趋势30d: {self.current_ws.vector[1]:.2f}")
            logger.info(f"   波动率: {self.current_ws.vector[2]:.2f}")
        except Exception as e:
            logger.warning(f"⚠️ WorldSignature计算失败: {e}，使用简化分析")
            self.current_ws = None
        
        # 2. 分析市场状态
        self.market_state = self._analyze_market_state(initial_market_data)
        logger.info(f"📊 市场状态: {self.market_state['state']} ({self.market_state['confidence']:.0%}置信度)")
        
        # 3. 评估风险等级
        risk_level = self._calculate_risk_level(initial_market_data)
        logger.info(f"⚠️ 风险等级: {risk_level}")
        
        # 4. 制定创世策略
        strategy = {
            # 市场分析
            'world_signature': self.current_ws,
            'market_state': self.market_state['state'],
            'market_confidence': self.market_state['confidence'],
            'risk_level': risk_level,
            
            # 创世参数（战略建议，不包含具体基因）
            'genesis_mode': genesis_mode,
            'agent_count': agent_count,
            
            # 战略建议
            'recommended_allocation': self._recommend_capital_allocation(risk_level),
            'recommended_leverage': self._recommend_leverage(risk_level, self.market_state['state']),
            'recommended_position_size': self._recommend_position_size(risk_level),
            
            # 元数据
            'timestamp': initial_market_data.iloc[-1]['timestamp'] if 'timestamp' in initial_market_data.columns else None,
            'data_points': len(initial_market_data)
        }
        
        self.current_strategy = strategy
        
        # 5. 发布到BulletinBoard（同时缓存WorldSignature对象）
        import json
        
        # 序列化WorldSignature
        ws_dict = self.current_ws.to_dict() if self.current_ws else {}
        
        # 发布JSON
        self.bulletin_board.post(
            content=json.dumps({
                'type': 'genesis_strategy',
                'world_signature': ws_dict,  # ✅ 序列化的WorldSignature
                'strategy': {
                    'market_state': strategy['market_state'],
                    'market_confidence': strategy['market_confidence'],
                    'risk_level': strategy['risk_level'],
                    'genesis_mode': strategy['genesis_mode'],
                    'agent_count': strategy['agent_count'],
                    'recommended_allocation': strategy['recommended_allocation'],
                    'recommended_leverage': strategy['recommended_leverage'],
                    'recommended_position_size': strategy['recommended_position_size']
                }
            }),
            priority=Priority.HIGH,
            source='Prophet',
            bulletin_type=BulletinType.MASTERMIND_STRATEGIC
        )
        
        # ✅ 同时缓存WorldSignature对象（避免重复解析）
        if self.current_ws:
            self.bulletin_board.cache_world_signature(self.current_ws)
        
        logger.info("="*70)
        logger.info("📜 创世战略已发布到BulletinBoard")
        logger.info(f"   市场: {strategy['market_state']}")
        logger.info(f"   模式: {genesis_mode}")
        logger.info(f"   风险: {risk_level}")
        logger.info(f"   配资建议: {strategy['recommended_allocation']*100:.0f}%")
        logger.info(f"   杠杆建议: {strategy['recommended_leverage']:.1f}x")
        logger.info("="*70)
        
        return strategy
    
    # ========== 运行时战略更新 ==========
    
    def update_strategy(
        self,
        current_market_data,
        current_cycle: int
    ) -> Dict:
        """
        更新战略（每个周期调用）
        
        Args:
            current_market_data: 当前市场数据
            current_cycle: 当前周期数
        
        Returns:
            更新后的战略
        """
        # 计算新的WorldSignature
        try:
            ws_window = current_market_data.tail(100) if len(current_market_data) > 100 else current_market_data
            self.current_ws = WorldSignatureSimple.from_market_data(ws_window)
        except:
            pass
        
        # 更新市场状态
        self.market_state = self._analyze_market_state(current_market_data)
        
        # 更新风险等级
        risk_level = self._calculate_risk_level(current_market_data)
        
        # 制定更新策略
        strategy = {
            'world_signature': self.current_ws,
            'market_state': self.market_state['state'],
            'market_confidence': self.market_state['confidence'],
            'risk_level': risk_level,
            'cycle': current_cycle,
            
            # 战略建议
            'recommended_leverage': self._recommend_leverage(risk_level, self.market_state['state']),
            'recommended_position_size': self._recommend_position_size(risk_level),
            
            'timestamp': current_market_data.iloc[-1]['timestamp'] if 'timestamp' in current_market_data.columns else None
        }
        
        self.current_strategy = strategy
        
        # 发布更新（同时缓存WorldSignature对象）
        import json
        
        # 序列化WorldSignature
        ws_dict = self.current_ws.to_dict() if self.current_ws else {}
        
        # 发布JSON
        self.bulletin_board.post(
            content=json.dumps({
                'type': 'strategy_update',
                'world_signature': ws_dict,  # ✅ 序列化的WorldSignature
                'strategy': {
                    'market_state': strategy['market_state'],
                    'market_confidence': strategy['market_confidence'],
                    'risk_level': strategy['risk_level'],
                    'cycle': strategy['cycle'],
                    'recommended_leverage': strategy['recommended_leverage'],
                    'recommended_position_size': strategy['recommended_position_size']
                }
            }),
            priority=Priority.MEDIUM,
            source='Prophet',
            bulletin_type=BulletinType.MASTERMIND_STRATEGIC
        )
        
        # ✅ 同时缓存WorldSignature对象（避免重复解析）
        if self.current_ws:
            self.bulletin_board.cache_world_signature(self.current_ws)
        
        return strategy
    
    # ========== 市场分析（私有方法）==========
    
    def _analyze_market_state(self, market_data) -> Dict:
        """
        分析市场状态
        
        Returns:
            {
                'state': 'bull' | 'bear' | 'sideways',
                'confidence': 0.0-1.0
            }
        """
        try:
            # 使用简单的趋势分析
            prices = market_data['close'].values
            
            # 计算不同周期的收益率
            returns_7d = (prices[-1] - prices[-7]) / prices[-7] if len(prices) > 7 else 0
            returns_30d = (prices[-1] - prices[-30]) / prices[-30] if len(prices) > 30 else 0
            
            # 牛市：短期和长期都上涨
            if returns_7d > 0.05 and returns_30d > 0.10:
                return {'state': 'bull', 'confidence': min(0.9, abs(returns_30d))}
            
            # 熊市：短期和长期都下跌
            elif returns_7d < -0.05 and returns_30d < -0.10:
                return {'state': 'bear', 'confidence': min(0.9, abs(returns_30d))}
            
            # 震荡市：其他情况
            else:
                return {'state': 'sideways', 'confidence': 0.6}
        
        except Exception as e:
            logger.warning(f"市场状态分析失败: {e}")
            return {'state': 'unknown', 'confidence': 0.5}
    
    def _calculate_risk_level(self, market_data) -> str:
        """
        计算风险等级
        
        Returns:
            'low' | 'moderate' | 'high' | 'extreme'
        """
        try:
            # 计算波动率（标准差）
            prices = market_data['close'].values
            returns = np.diff(prices) / prices[:-1]
            volatility = np.std(returns) if len(returns) > 0 else 0
            
            # 根据波动率判断风险
            if volatility < 0.01:
                return 'low'
            elif volatility < 0.02:
                return 'moderate'
            elif volatility < 0.05:
                return 'high'
            else:
                return 'extreme'
        
        except Exception as e:
            logger.warning(f"风险评估失败: {e}")
            return 'moderate'
    
    # ========== 战略建议（私有方法）==========
    
    def _recommend_capital_allocation(self, risk_level: str) -> float:
        """
        建议资金配置比例
        
        Returns:
            0.0-1.0（建议分配给Agent的比例）
        """
        allocation_map = {
            'low': 0.3,      # 低风险：30%给Agent，70%储备
            'moderate': 0.2, # 中风险：20%给Agent，80%储备
            'high': 0.15,    # 高风险：15%给Agent，85%储备
            'extreme': 0.10  # 极端风险：10%给Agent，90%储备
        }
        return allocation_map.get(risk_level, 0.2)
    
    def _recommend_leverage(self, risk_level: str, market_state: str) -> float:
        """
        建议杠杆倍数
        
        Returns:
            杠杆倍数（1.0-100.0）
        """
        # 基础杠杆（根据风险）
        base_leverage = {
            'low': 50.0,
            'moderate': 30.0,
            'high': 10.0,
            'extreme': 3.0
        }.get(risk_level, 20.0)
        
        # 市场状态调整
        if market_state == 'bull':
            return base_leverage * 1.2  # 牛市：提高20%
        elif market_state == 'bear':
            return base_leverage * 0.8  # 熊市：降低20%
        else:
            return base_leverage
    
    def _recommend_position_size(self, risk_level: str) -> float:
        """
        建议单次开仓比例
        
        Returns:
            0.0-1.0（占Agent总资金的比例）
        """
        position_map = {
            'low': 0.8,      # 低风险：可开80%仓位
            'moderate': 0.6, # 中风险：可开60%仓位
            'high': 0.4,     # 高风险：可开40%仓位
            'extreme': 0.2   # 极端风险：可开20%仓位
        }
        return position_map.get(risk_level, 0.5)
    
    # ========== 查询接口 ==========
    
    def get_current_strategy(self) -> Optional[Dict]:
        """获取当前战略"""
        return self.current_strategy
    
    def get_current_world_signature(self) -> Optional[WorldSignatureSimple]:
        """获取当前WorldSignature"""
        return self.current_ws
    
    def get_market_state(self) -> Optional[Dict]:
        """获取当前市场状态"""
        return self.market_state
    
    # ========== v6.0新增：智能匹配 ==========
    
    def query_similar_strategies(
        self,
        experience_db: ExperienceDB,
        current_ws: Optional[WorldSignatureSimple] = None,
        top_k: int = 10,
        min_similarity: float = 0.5,
        market_type: Optional[str] = None
    ) -> List[Dict]:
        """
        查询相似市场环境下的最佳策略
        
        ✨ v6.0核心方法：Prophet负责相似度匹配逻辑
        
        职责：
        1. 从ExperienceDB获取历史记录
        2. 计算相似度（使用WorldSignature.similarity()）
        3. 排序和筛选
        4. 返回Top K策略
        
        参数：
          - experience_db: 经验数据库
          - current_ws: 当前WorldSignature（默认使用self.current_ws）
          - top_k: 返回前K个策略
          - min_similarity: 最低相似度阈值（推荐0.5-0.6）
          - market_type: 市场类型过滤（可选，建议不限制）
        
        返回：
          - 策略列表，按相似度降序排序
            [
                {
                    'similarity': 0.95,
                    'strategy_params': {...},
                    'roi': 0.65,
                    'sharpe': 2.3,
                    'max_drawdown': -0.15,
                    'market_type': 'bull'
                },
                ...
            ]
        """
        # 使用当前WorldSignature（如果未指定）
        if current_ws is None:
            current_ws = self.current_ws
        
        if current_ws is None:
            logger.warning("⚠️ Prophet查询相似策略失败：当前WorldSignature为空")
            return []
        
        # 1. 从ExperienceDB获取所有历史记录（原始数据）
        if market_type:
            cursor = experience_db.conn.execute("""
                SELECT world_signature, genome, roi, sharpe, max_drawdown, market_type
                FROM best_genomes
                WHERE market_type = ?
            """, (market_type,))
        else:
            cursor = experience_db.conn.execute("""
                SELECT world_signature, genome, roi, sharpe, max_drawdown, market_type
                FROM best_genomes
            """)
        
        # 2. 计算相似度（Prophet负责）
        candidates = []
        for row in cursor:
            # 解析历史WorldSignature
            historical_ws = WorldSignatureSimple.from_dict(json.loads(row[0]))
            
            # ✨ 核心：使用加权欧氏距离计算相似度
            similarity = current_ws.similarity(historical_ws, use_weights=True)
            
            # 过滤低相似度记录
            if similarity >= min_similarity:
                candidates.append({
                    'similarity': similarity,
                    'strategy_params': json.loads(row[1]),  # StrategyParams
                    'roi': row[2],
                    'sharpe': row[3],
                    'max_drawdown': row[4],
                    'market_type': row[5]
                })
        
        # 3. 排序（先按相似度，再按ROI）
        candidates.sort(key=lambda x: (x['similarity'], x['roi']), reverse=True)
        
        logger.info(
            f"✅ Prophet查询相似策略: 找到{len(candidates)}个 "
            f"(阈值={min_similarity:.2f}, Top{top_k})"
        )
        
        # 4. 返回Top K
        return candidates[:top_k]
    
    def recommend_genesis_strategy(
        self,
        experience_db: ExperienceDB,
        min_similarity: float = 0.5
    ) -> Tuple[str, Optional[List[Dict]]]:
        """
        推荐创世策略
        
        基于当前WorldSignature，判断应该：
        - 'smart': 智能创世（有相似历史经验）
        - 'random': 随机创世（无相似历史经验）
        
        返回：
          - (strategy_type, strategies)
          - strategy_type: 'smart' 或 'random'
          - strategies: 如果是'smart'，返回推荐策略列表；否则为None
        """
        if self.current_ws is None:
            logger.warning("⚠️ Prophet推荐创世策略失败：当前WorldSignature为空")
            return ('random', None)
        
        # 查询相似策略
        similar_strategies = self.query_similar_strategies(
            experience_db=experience_db,
            current_ws=self.current_ws,
            top_k=20,  # 获取Top 20用于创世
            min_similarity=min_similarity,
            market_type=None  # 不限制市场类型（让相似度算法来判断）
        )
        
        if len(similar_strategies) >= 5:  # 至少5个相似策略才启用智能创世
            logger.info(
                f"✅ Prophet推荐：智能创世 (找到{len(similar_strategies)}个相似策略)"
            )
            return ('smart', similar_strategies)
        else:
            logger.info(
                f"⚠️ Prophet推荐：随机创世 (相似策略不足：{len(similar_strategies)}<5)"
            )
            return ('random', None)

