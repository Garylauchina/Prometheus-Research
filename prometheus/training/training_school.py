"""
Mock训练学校

渐进式多情境训练系统
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

from .regime_generators import (
    RegimeGenerator,
    BullMarketGenerator,
    BearMarketGenerator,
    VolatilityGenerator,
    SidewaysGenerator,
    MultiRegimeGenerator,
    create_standard_multi_regime
)

logger = logging.getLogger(__name__)


@dataclass
class TrainingSession:
    """训练课程"""
    
    name: str
    description: str
    regime_generator: RegimeGenerator
    duration_days: int
    difficulty: int  # 1-5
    pass_criteria: Dict  # 通过标准


class TrainingCurriculum:
    """
    训练课程体系
    
    渐进式训练，从简单到复杂
    """
    
    def __init__(self):
        """初始化课程体系"""
        self.sessions = self._create_sessions()
        self.current_session_idx = 0
    
    def _create_sessions(self) -> List[TrainingSession]:
        """创建训练课程"""
        sessions = []
        
        # 第1课：牛市生存
        sessions.append(TrainingSession(
            name="第1课：牛市生存",
            description="学会在持续上涨的市场中获利",
            regime_generator=BullMarketGenerator(
                drift=0.002,
                volatility=0.02,
                pullback_prob=0.1
            ),
            duration_days=100,
            difficulty=1,
            pass_criteria={
                'min_roi': 0,  # 不亏钱
                'beat_market_rate': 0.3  # 30%跑赢市场
            }
        ))
        
        # 第2课：熊市生存
        sessions.append(TrainingSession(
            name="第2课：熊市生存",
            description="学会在持续下跌的市场中生存",
            regime_generator=BearMarketGenerator(
                drift=-0.003,
                volatility=0.04,
                bounce_prob=0.15
            ),
            duration_days=100,
            difficulty=2,
            pass_criteria={
                'min_roi': -20,  # 最多亏20%
                'beat_market_rate': 0.5  # 50%跑赢市场
            }
        ))
        
        # 第3课：震荡市生存
        sessions.append(TrainingSession(
            name="第3课：震荡市生存",
            description="学会在高波震荡中短线交易",
            regime_generator=VolatilityGenerator(
                volatility=0.06,
                momentum=0.3
            ),
            duration_days=100,
            difficulty=3,
            pass_criteria={
                'min_roi': 5,  # 至少赚5%
                'beat_market_rate': 0.6  # 60%跑赢市场
            }
        ))
        
        # 第4课：盘整市生存
        sessions.append(TrainingSession(
            name="第4课：盘整市生存",
            description="学会在低波盘整中控制成本",
            regime_generator=SidewaysGenerator(
                volatility=0.01,
                mean_reversion=0.05
            ),
            duration_days=100,
            difficulty=2,
            pass_criteria={
                'min_roi': -5,  # 最多亏5%
                'beat_market_rate': 0.4  # 40%跑赢市场
            }
        ))
        
        # 第5课：Regime切换（简单）
        sessions.append(TrainingSession(
            name="第5课：Regime切换（简单）",
            description="学会应对市场环境变化",
            regime_generator=MultiRegimeGenerator(
                regimes=[
                    BullMarketGenerator(),
                    BearMarketGenerator()
                ],
                switch_probability=0.03  # 3%切换概率
            ),
            duration_days=200,
            difficulty=3,
            pass_criteria={
                'min_roi': 0,
                'beat_market_rate': 0.5
            }
        ))
        
        # 第6课：Regime切换（复杂）
        sessions.append(TrainingSession(
            name="第6课：Regime切换（复杂）",
            description="掌握所有市场环境的适应能力",
            regime_generator=create_standard_multi_regime(),
            duration_days=365,
            difficulty=5,
            pass_criteria={
                'min_roi': 10,  # 至少赚10%
                'beat_market_rate': 0.7  # 70%跑赢市场
            }
        ))
        
        return sessions
    
    def get_session(self, idx: int) -> Optional[TrainingSession]:
        """获取指定课程"""
        if 0 <= idx < len(self.sessions):
            return self.sessions[idx]
        return None
    
    def get_current_session(self) -> TrainingSession:
        """获取当前课程"""
        return self.sessions[self.current_session_idx]
    
    def next_session(self) -> bool:
        """
        进入下一课程
        
        Returns:
            是否有下一课程
        """
        if self.current_session_idx < len(self.sessions) - 1:
            self.current_session_idx += 1
            return True
        return False
    
    def reset(self):
        """重置到第一课"""
        self.current_session_idx = 0
    
    def get_progress(self) -> Dict:
        """获取学习进度"""
        return {
            'current_session': self.current_session_idx + 1,
            'total_sessions': len(self.sessions),
            'progress_pct': (self.current_session_idx + 1) / len(self.sessions) * 100,
            'current_name': self.sessions[self.current_session_idx].name
        }


class MockTrainingSchool:
    """
    Mock训练学校
    
    提供完整的训练环境和评估体系
    """
    
    def __init__(self):
        """初始化"""
        self.curriculum = TrainingCurriculum()
        self.training_history = []
        
        logger.info("="*70)
        logger.info("🏫 Mock训练学校初始化")
        logger.info("="*70)
        logger.info(f"课程总数: {len(self.curriculum.sessions)}个")
        logger.info(f"训练模式: 渐进式（从简单到复杂）")
    
    def train_session(
        self,
        agent_system,  # Agent系统（进化管理器）
        session: TrainingSession,
        verbose: bool = True
    ) -> Dict:
        """
        运行单个训练课程
        
        Args:
            agent_system: Agent系统
            session: 训练课程
            verbose: 是否详细输出
            
        Returns:
            训练结果
        """
        if verbose:
            logger.info(f"\n{'='*70}")
            logger.info(f"📚 {session.name}")
            logger.info(f"{'='*70}")
            logger.info(f"描述: {session.description}")
            logger.info(f"难度: {'⭐' * session.difficulty}")
            logger.info(f"天数: {session.duration_days}天")
        
        # 生成价格序列
        if isinstance(session.regime_generator, MultiRegimeGenerator):
            prices, regime_history = session.regime_generator.generate_series(
                days=session.duration_days
            )
        else:
            prices = session.regime_generator.generate_series(session.duration_days)
            regime_history = None
        
        market_roi = (prices[-1] / prices[0] - 1) * 100
        
        if verbose:
            logger.info(f"\n市场环境:")
            logger.info(f"  起始价格: ${prices[0]:,.0f}")
            logger.info(f"  结束价格: ${prices[-1]:,.0f}")
            logger.info(f"  市场ROI: {market_roi:+.1f}%")
        
        # 运行训练（这里需要agent_system实现）
        # 简化版本：模拟结果
        result = self._simulate_training(prices, market_roi, session)
        
        # 评估表现
        passed = self._evaluate_performance(result, session.pass_criteria, market_roi)
        result['passed'] = passed
        result['session_name'] = session.name
        
        if verbose:
            logger.info(f"\n训练结果:")
            logger.info(f"  系统ROI: {result['roi']:+.1f}%")
            logger.info(f"  超额收益: {result['excess_return']:+.1f}%")
            logger.info(f"  跑赢率: {result['beat_market_pct']:.0f}%")
            logger.info(f"  存活Agent: {result['survivors']}/{result['total_agents']}")
            logger.info(f"\n评估结果: {'✅ 通过' if passed else '❌ 未通过'}")
        
        # 记录历史
        self.training_history.append(result)
        
        return result
    
    def _simulate_training(self, prices: np.ndarray, market_roi: float, session: TrainingSession) -> Dict:
        """
        模拟训练（简化版本）
        
        实际应该调用agent_system进行真实训练
        """
        # 这里是简化的模拟
        # 实际应该运行完整的进化系统
        
        num_agents = 50
        
        # 根据难度调整表现
        difficulty_factor = 1.0 - (session.difficulty - 1) * 0.1
        
        # 模拟ROI
        base_roi = market_roi * 0.5  # 基础表现是市场的50%
        noise = np.random.normal(0, 10)  # 随机噪声
        roi = (base_roi + noise) * difficulty_factor
        
        # 模拟存活率
        survival_rate = max(0.5, difficulty_factor)
        survivors = int(num_agents * survival_rate)
        
        # 模拟跑赢率
        beat_market_pct = np.clip(50 + (roi - market_roi), 0, 100)
        
        return {
            'roi': roi,
            'market_roi': market_roi,
            'excess_return': roi - market_roi,
            'survivors': survivors,
            'total_agents': num_agents,
            'beat_market_pct': beat_market_pct,
            'difficulty': session.difficulty
        }
    
    def _evaluate_performance(
        self,
        result: Dict,
        criteria: Dict,
        market_roi: float
    ) -> bool:
        """
        评估表现是否达标
        
        Args:
            result: 训练结果
            criteria: 通过标准
            market_roi: 市场ROI
            
        Returns:
            是否通过
        """
        # 检查ROI标准
        if result['roi'] < criteria['min_roi']:
            return False
        
        # 检查跑赢率标准
        if result['beat_market_pct'] / 100 < criteria['beat_market_rate']:
            return False
        
        return True
    
    def run_full_curriculum(
        self,
        agent_system,
        early_stop: bool = False
    ) -> Dict:
        """
        运行完整课程
        
        Args:
            agent_system: Agent系统
            early_stop: 是否在失败时提前停止
            
        Returns:
            总体结果
        """
        logger.info("="*70)
        logger.info("🎓 开始完整课程训练")
        logger.info("="*70)
        
        self.curriculum.reset()
        results = []
        
        for i, session in enumerate(self.curriculum.sessions):
            logger.info(f"\n进度: {i+1}/{len(self.curriculum.sessions)}")
            
            result = self.train_session(agent_system, session, verbose=True)
            results.append(result)
            
            if early_stop and not result['passed']:
                logger.info(f"\n❌ 未通过{session.name}，提前终止")
                break
        
        # 总结
        passed_count = sum(1 for r in results if r['passed'])
        total_count = len(results)
        
        logger.info(f"\n{'='*70}")
        logger.info("🎊 训练总结")
        logger.info(f"{'='*70}")
        logger.info(f"完成课程: {total_count}/{len(self.curriculum.sessions)}")
        logger.info(f"通过课程: {passed_count}/{total_count}")
        logger.info(f"通过率: {passed_count/total_count*100:.0f}%")
        
        if passed_count == len(self.curriculum.sessions):
            logger.info(f"\n🏆 恭喜！完成所有课程训练！")
        
        return {
            'total_sessions': total_count,
            'passed_sessions': passed_count,
            'pass_rate': passed_count / total_count * 100,
            'results': results
        }
    
    def get_report(self) -> Dict:
        """获取训练报告"""
        if not self.training_history:
            return {'message': '暂无训练记录'}
        
        return {
            'total_sessions': len(self.training_history),
            'passed_sessions': sum(1 for r in self.training_history if r['passed']),
            'avg_roi': np.mean([r['roi'] for r in self.training_history]),
            'avg_excess_return': np.mean([r['excess_return'] for r in self.training_history]),
            'history': self.training_history
        }

