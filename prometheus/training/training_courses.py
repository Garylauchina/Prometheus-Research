"""
训练课程系统 - 基于RealisticMockMarket

提供渐进式训练课程，让Agent从简单到复杂逐步学习
"""

from typing import List, Dict, Callable, Optional
from dataclasses import dataclass
import numpy as np

from .realistic_mock_market import (
    RegimeBasedMockMarket,
    create_bull_market,
    create_bear_market,
    create_volatile_market,
    create_sideways_market
)


@dataclass
class CourseConfig:
    """课程配置"""
    name: str
    description: str
    regime_type: str
    num_steps: int
    initial_price: float
    passing_score: float  # 及格分数（胜率）
    difficulty: int  # 1-5
    

@dataclass
class CourseResult:
    """课程结果"""
    course_name: str
    passed: bool
    score: float
    profit: float
    win_rate: float
    details: Dict


class TrainingCourse:
    """
    单个训练课程
    
    一个课程包含：
    - 特定的市场环境（Regime）
    - 训练步数
    - 评估标准
    """
    
    def __init__(self, config: CourseConfig):
        """
        初始化课程
        
        Args:
            config: 课程配置
        """
        self.config = config
        self.market = self._create_market()
        
    def _create_market(self) -> RegimeBasedMockMarket:
        """创建市场环境"""
        if self.config.regime_type == 'bull':
            return create_bull_market(self.config.initial_price)
        elif self.config.regime_type == 'bear':
            return create_bear_market(self.config.initial_price)
        elif self.config.regime_type == 'volatile':
            return create_volatile_market(self.config.initial_price)
        elif self.config.regime_type == 'sideways':
            return create_sideways_market(self.config.initial_price)
        else:
            raise ValueError(f"Unknown regime type: {self.config.regime_type}")
    
    def run(
        self,
        agent_decision_func: Callable,
        initial_capital: float = 10000.0
    ) -> CourseResult:
        """
        运行课程
        
        Args:
            agent_decision_func: Agent决策函数 (market_state) -> action
            initial_capital: 初始资金
            
        Returns:
            CourseResult: 课程结果
        """
        # 重置市场
        self.market.reset(self.config.initial_price)
        
        # 初始化Agent状态
        capital = initial_capital
        position = 0.0  # 持仓数量
        entry_price = 0.0
        
        trades = []
        
        # 运行模拟
        for step in range(self.config.num_steps):
            # 生成市场状态
            market_state = self.market.step()
            
            # Agent决策
            action = agent_decision_func(market_state)
            
            # 执行交易
            if action == 'buy' and position == 0:
                # 开多
                position = capital / market_state.close
                entry_price = market_state.close
                capital = 0
                
            elif action == 'sell' and position == 0:
                # 开空（简化：只记录）
                position = -capital / market_state.close
                entry_price = market_state.close
                capital = 0
                
            elif action == 'close' and position != 0:
                # 平仓
                if position > 0:
                    # 平多
                    pnl = position * (market_state.close - entry_price)
                else:
                    # 平空
                    pnl = -position * (entry_price - market_state.close)
                
                capital = initial_capital + pnl
                
                # 记录交易
                trades.append({
                    'entry_price': entry_price,
                    'exit_price': market_state.close,
                    'pnl': pnl,
                    'win': pnl > 0
                })
                
                position = 0
        
        # 如果还有持仓，强制平仓
        if position != 0:
            final_state = self.market.price_history[-1]
            if position > 0:
                pnl = position * (final_state.close - entry_price)
            else:
                pnl = -position * (entry_price - final_state.close)
            
            capital = initial_capital + pnl
            trades.append({
                'entry_price': entry_price,
                'exit_price': final_state.close,
                'pnl': pnl,
                'win': pnl > 0
            })
        
        # 计算结果
        total_profit = capital - initial_capital
        win_count = sum(1 for t in trades if t['win'])
        win_rate = win_count / len(trades) if trades else 0.0
        
        # 计算分数（基于胜率和收益）
        score = (win_rate * 0.6 + (1 if total_profit > 0 else 0) * 0.4)
        
        # 判断是否通过
        passed = score >= self.config.passing_score
        
        return CourseResult(
            course_name=self.config.name,
            passed=passed,
            score=score,
            profit=total_profit,
            win_rate=win_rate,
            details={
                'trades': len(trades),
                'win_count': win_count,
                'final_capital': capital,
                'roi': total_profit / initial_capital
            }
        )


# 预定义课程
COURSE_CATALOG = {
    # Level 1: 基础课程（单一Regime生存）
    'bull_101': CourseConfig(
        name='牛市101',
        description='学习在牛市中获利',
        regime_type='bull',
        num_steps=50,
        initial_price=50000,
        passing_score=0.5,
        difficulty=1
    ),
    
    'bear_101': CourseConfig(
        name='熊市101',
        description='学习在熊市中生存',
        regime_type='bear',
        num_steps=50,
        initial_price=50000,
        passing_score=0.4,  # 熊市更难
        difficulty=2
    ),
    
    'volatile_101': CourseConfig(
        name='震荡101',
        description='学习在高波动中交易',
        regime_type='volatile',
        num_steps=50,
        initial_price=50000,
        passing_score=0.45,
        difficulty=3
    ),
    
    'sideways_101': CourseConfig(
        name='盘整101',
        description='学习在盘整市场中获利',
        regime_type='sideways',
        num_steps=50,
        initial_price=50000,
        passing_score=0.5,
        difficulty=1
    ),
}


class TrainingCurriculum:
    """
    训练课程表
    
    管理多个课程的学习路径
    """
    
    def __init__(self, courses: Optional[List[str]] = None):
        """
        初始化课程表
        
        Args:
            courses: 课程列表（使用COURSE_CATALOG中的key）
                    如果为None，使用默认Level 1课程
        """
        if courses is None:
            courses = ['bull_101', 'bear_101', 'volatile_101', 'sideways_101']
        
        self.courses = [
            TrainingCourse(COURSE_CATALOG[name])
            for name in courses
        ]
        
    def run_all(
        self,
        agent_decision_func: Callable,
        initial_capital: float = 10000.0
    ) -> List[CourseResult]:
        """
        运行所有课程
        
        Args:
            agent_decision_func: Agent决策函数
            initial_capital: 初始资金
            
        Returns:
            List[CourseResult]: 所有课程结果
        """
        results = []
        
        for course in self.courses:
            print(f"\n{'='*60}")
            print(f"📚 课程: {course.config.name}")
            print(f"   描述: {course.config.description}")
            print(f"   难度: {'⭐' * course.config.difficulty}")
            print(f"   步数: {course.config.num_steps}")
            print(f"{'='*60}")
            
            result = course.run(agent_decision_func, initial_capital)
            results.append(result)
            
            # 显示结果
            status = "✅ 通过" if result.passed else "❌ 未通过"
            print(f"\n{status}")
            print(f"   分数: {result.score:.1%}")
            print(f"   收益: ${result.profit:,.2f}")
            print(f"   胜率: {result.win_rate:.1%}")
            print(f"   交易次数: {result.details['trades']}")
            print(f"   ROI: {result.details['roi']:.1%}")
        
        return results
    
    def get_summary(self, results: List[CourseResult]) -> Dict:
        """获取总结"""
        passed_count = sum(1 for r in results if r.passed)
        avg_score = np.mean([r.score for r in results])
        total_profit = sum(r.profit for r in results)
        
        return {
            'total_courses': len(results),
            'passed': passed_count,
            'pass_rate': passed_count / len(results),
            'avg_score': avg_score,
            'total_profit': total_profit,
            'graduated': passed_count == len(results)
        }


# 示例Agent决策函数
def simple_trend_following_agent(market_state) -> str:
    """
    简单的趋势跟踪Agent
    
    策略：
    - 价格上涨 → 做多
    - 价格下跌 → 做空
    - 持有一段时间后平仓
    """
    # 这是一个示例，实际应该由真实Agent提供
    if not hasattr(simple_trend_following_agent, 'last_price'):
        simple_trend_following_agent.last_price = market_state.close
        simple_trend_following_agent.hold_time = 0
        return 'hold'
    
    # 检查是否该平仓
    simple_trend_following_agent.hold_time += 1
    if simple_trend_following_agent.hold_time > 10:
        simple_trend_following_agent.hold_time = 0
        return 'close'
    
    # 简单趋势判断
    if market_state.close > simple_trend_following_agent.last_price * 1.01:
        simple_trend_following_agent.last_price = market_state.close
        return 'buy'
    elif market_state.close < simple_trend_following_agent.last_price * 0.99:
        simple_trend_following_agent.last_price = market_state.close
        return 'sell'
    
    simple_trend_following_agent.last_price = market_state.close
    return 'hold'

