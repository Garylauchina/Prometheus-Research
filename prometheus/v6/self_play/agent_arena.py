"""
Agent竞技场

提供多种对抗模式，让Agent在竞争中进化：
  1. duel_1v1（1v1对决）- 直接竞争
  2. group_battle（小组赛）- 资源竞争
  3. tournament（锦标赛）- 淘汰赛

核心理念：
  - Agent vs Agent（不只是Agent vs Market）
  - 竞争压力驱动进化
  - 多样化的竞争模式
  - 记录对战历史

遵循三大铁律：
  - 铁律1: 通过SelfPlaySystem统一调用
  - 铁律2: 本模块为Self-Play内部实现
  - 铁律3: 所有对战结果可审计
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import random
import logging
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class MatchRecord:
    """
    对战记录
    
    属性：
      - match_id: 对战ID
      - match_type: 对战类型（'duel', 'group', 'tournament'）
      - participants: 参与者列表
      - winner: 获胜者
      - loser: 失败者（如果有）
      - scores: 各参与者得分
      - timestamp: 时间戳
      - metadata: 其他信息
    """
    match_id: str
    match_type: str
    participants: List[str]
    winner: Optional[str] = None
    loser: Optional[str] = None
    scores: Dict[str, float] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    metadata: Dict = field(default_factory=dict)


@dataclass
class AgentStats:
    """
    Agent统计信息
    
    属性：
      - agent_id: Agent ID
      - total_matches: 总对战数
      - wins: 胜场数
      - losses: 负场数
      - win_rate: 胜率
      - avg_score: 平均得分
      - total_pnl: 总盈亏
      - rating: 评级（ELO）
    """
    agent_id: str
    total_matches: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    win_rate: float = 0.0
    avg_score: float = 0.0
    total_pnl: float = 0.0
    rating: float = 1500.0  # ELO评级，初始1500
    
    def update(self, is_win: bool, is_draw: bool, score: float, pnl: float):
        """更新统计信息"""
        self.total_matches += 1
        if is_win:
            self.wins += 1
        elif is_draw:
            self.draws += 1
        else:
            self.losses += 1
        
        self.win_rate = self.wins / self.total_matches if self.total_matches > 0 else 0.0
        
        # 更新平均得分（移动平均）
        self.avg_score = (self.avg_score * (self.total_matches - 1) + score) / self.total_matches
        
        # 累计盈亏
        self.total_pnl += pnl


class Leaderboard:
    """
    排行榜
    
    功能：
      - 记录对战结果
      - 计算Agent统计数据
      - 维护排名
      - ELO评级系统
    """
    
    def __init__(self, k_factor: float = 32.0):
        """
        初始化排行榜
        
        参数：
          - k_factor: ELO系统的K因子（默认32）
        """
        self.stats: Dict[str, AgentStats] = {}
        self.k_factor = k_factor
        
        logger.info(f"排行榜初始化: K-factor={k_factor}")
    
    def add_result(
        self,
        agent_id: str,
        is_win: bool,
        is_draw: bool,
        score: float,
        pnl: float,
        opponent_id: Optional[str] = None
    ):
        """
        添加对战结果
        
        参数：
          - agent_id: Agent ID
          - is_win: 是否获胜
          - is_draw: 是否平局
          - score: 得分
          - pnl: 盈亏
          - opponent_id: 对手ID（用于ELO计算）
        """
        # 初始化统计数据
        if agent_id not in self.stats:
            self.stats[agent_id] = AgentStats(agent_id=agent_id)
        
        # 更新统计
        self.stats[agent_id].update(is_win, is_draw, score, pnl)
        
        # 更新ELO评级
        if opponent_id and opponent_id in self.stats:
            self._update_elo(agent_id, opponent_id, is_win, is_draw)
    
    def _update_elo(
        self,
        agent_id: str,
        opponent_id: str,
        is_win: bool,
        is_draw: bool
    ):
        """
        更新ELO评级
        
        ELO公式：
          R' = R + K * (S - E)
        
        其中：
          R: 当前评级
          K: K因子
          S: 实际得分（胜=1，平=0.5，负=0）
          E: 期望得分 = 1 / (1 + 10^((对手评级-自己评级)/400))
        """
        rating_a = self.stats[agent_id].rating
        rating_b = self.stats[opponent_id].rating
        
        # 计算期望得分
        expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
        expected_b = 1 / (1 + 10 ** ((rating_a - rating_b) / 400))
        
        # 实际得分
        if is_win:
            actual_a = 1.0
            actual_b = 0.0
        elif is_draw:
            actual_a = 0.5
            actual_b = 0.5
        else:
            actual_a = 0.0
            actual_b = 1.0
        
        # 更新评级
        self.stats[agent_id].rating = rating_a + self.k_factor * (actual_a - expected_a)
        self.stats[opponent_id].rating = rating_b + self.k_factor * (actual_b - expected_b)
    
    def get_rankings(self, sort_by: str = 'rating') -> List[AgentStats]:
        """
        获取排名
        
        参数：
          - sort_by: 排序依据（'rating', 'win_rate', 'total_pnl'）
        
        返回：
          - rankings: 排名列表
        """
        rankings = list(self.stats.values())
        
        if sort_by == 'rating':
            rankings.sort(key=lambda x: x.rating, reverse=True)
        elif sort_by == 'win_rate':
            rankings.sort(key=lambda x: (x.win_rate, x.total_matches), reverse=True)
        elif sort_by == 'total_pnl':
            rankings.sort(key=lambda x: x.total_pnl, reverse=True)
        
        return rankings
    
    def get_win_rate(self, agent_id: str) -> float:
        """获取胜率"""
        if agent_id in self.stats:
            return self.stats[agent_id].win_rate
        return 0.0
    
    def get_rating(self, agent_id: str) -> float:
        """获取ELO评级"""
        if agent_id in self.stats:
            return self.stats[agent_id].rating
        return 1500.0
    
    def get_top_k(self, k: int = 10, sort_by: str = 'rating') -> List[AgentStats]:
        """获取TopK"""
        rankings = self.get_rankings(sort_by)
        return rankings[:k]


class AgentArena:
    """
    Agent竞技场
    
    功能：
      1. duel_1v1（1v1对决）
      2. group_battle（小组赛）
      3. tournament（锦标赛）
      4. 记录对战历史
      5. 维护排行榜
    """
    
    def __init__(self):
        self.leaderboard = Leaderboard()
        self.match_history: List[MatchRecord] = []
        self.next_match_id = 0
        
        logger.info("Agent竞技场初始化完成")
    
    # ===== 1v1对决 =====
    
    def duel_1v1(
        self,
        agent1,
        agent2,
        market_data: pd.DataFrame,
        initial_capital: float = 10000.0
    ) -> MatchRecord:
        """
        1v1对决
        
        规则：
          - 相同的市场数据
          - 相同的初始资金
          - 最终PnL高者胜
          - 直接对比策略优劣
        
        参数：
          - agent1: Agent 1
          - agent2: Agent 2
          - market_data: 市场数据
          - initial_capital: 初始资金
        
        返回：
          - match_record: 对战记录
        """
        logger.info(
            f"1v1对决开始: {getattr(agent1, 'agent_id', 'Agent1')} vs "
            f"{getattr(agent2, 'agent_id', 'Agent2')}"
        )
        
        # 重置Agent状态
        # TODO: 实际实现需要调用Agent的reset方法
        # agent1.reset(initial_capital=initial_capital)
        # agent2.reset(initial_capital=initial_capital)
        
        # 运行模拟（简化版，实际需要完整的交易模拟）
        # TODO: 这里需要完整的交易执行逻辑
        # 当前只是占位符
        
        # 模拟结果（实际应该是真实交易结果）
        pnl1 = random.uniform(-1000, 3000)  # TODO: 替换为真实PnL
        pnl2 = random.uniform(-1000, 3000)  # TODO: 替换为真实PnL
        
        # 确定胜负
        winner = agent1 if pnl1 > pnl2 else agent2
        loser = agent2 if pnl1 > pnl2 else agent1
        winner_pnl = max(pnl1, pnl2)
        loser_pnl = min(pnl1, pnl2)
        
        # 记录结果
        agent1_id = getattr(agent1, 'agent_id', 'Agent1')
        agent2_id = getattr(agent2, 'agent_id', 'Agent2')
        winner_id = getattr(winner, 'agent_id', 'Winner')
        loser_id = getattr(loser, 'agent_id', 'Loser')
        
        match_record = MatchRecord(
            match_id=f"DUEL{self.next_match_id:06d}",
            match_type='duel',
            participants=[agent1_id, agent2_id],
            winner=winner_id,
            loser=loser_id,
            scores={
                agent1_id: pnl1,
                agent2_id: pnl2
            },
            metadata={
                'initial_capital': initial_capital,
                'market_cycles': len(market_data),
                'margin': abs(pnl1 - pnl2)
            }
        )
        
        self.next_match_id += 1
        self.match_history.append(match_record)
        
        # 更新排行榜
        self.leaderboard.add_result(
            agent1_id,
            is_win=(pnl1 > pnl2),
            is_draw=(pnl1 == pnl2),
            score=pnl1,
            pnl=pnl1,
            opponent_id=agent2_id
        )
        self.leaderboard.add_result(
            agent2_id,
            is_win=(pnl2 > pnl1),
            is_draw=(pnl1 == pnl2),
            score=pnl2,
            pnl=pnl2,
            opponent_id=agent1_id
        )
        
        logger.info(
            f"1v1对决结束: 获胜者={winner_id}, "
            f"PnL={winner_pnl:.2f} vs {loser_pnl:.2f}, "
            f"优势={abs(pnl1-pnl2):.2f}"
        )
        
        return match_record
    
    # ===== 小组赛 =====
    
    def group_battle(
        self,
        agents: List,
        market_data: pd.DataFrame,
        group_size: int = 5,
        advance_count: int = 2,
        initial_capital: float = 10000.0
    ) -> List[MatchRecord]:
        """
        小组赛
        
        规则：
          - 随机分组（每组group_size个Agent）
          - 每组前advance_count名晋级
          - 组内竞争激烈
          - 多样性得以保留（不同组的策略可能不同）
        
        参数：
          - agents: Agent列表
          - market_data: 市场数据
          - group_size: 每组人数
          - advance_count: 每组晋级人数
          - initial_capital: 初始资金
        
        返回：
          - match_records: 对战记录列表
        """
        logger.info(
            f"小组赛开始: {len(agents)}个Agent, "
            f"每组{group_size}人, 晋级{advance_count}人"
        )
        
        # 分组
        groups = self._split_into_groups(agents, group_size)
        
        match_records = []
        winners = []
        
        for group_idx, group in enumerate(groups):
            logger.info(f"小组{group_idx+1}开始: {len(group)}个Agent")
            
            # 小组内竞争（简化版）
            results = []
            for agent in group:
                # TODO: 运行完整的交易模拟
                pnl = random.uniform(-1000, 3000)
                agent_id = getattr(agent, 'agent_id', f'Agent{id(agent)}')
                results.append((agent, agent_id, pnl))
            
            # 排序，取前advance_count名
            results.sort(key=lambda x: x[2], reverse=True)
            
            # 记录小组赛结果
            group_record = MatchRecord(
                match_id=f"GROUP{self.next_match_id:06d}",
                match_type='group',
                participants=[r[1] for r in results],
                winner=results[0][1],  # 小组第一
                scores={r[1]: r[2] for r in results},
                metadata={
                    'group_id': group_idx,
                    'group_size': len(group),
                    'advance_count': advance_count
                }
            )
            
            self.next_match_id += 1
            match_records.append(group_record)
            self.match_history.append(group_record)
            
            # 晋级者
            for i, (agent, agent_id, pnl) in enumerate(results[:advance_count]):
                winners.append(agent)
                
                # 更新排行榜
                self.leaderboard.add_result(
                    agent_id,
                    is_win=(i == 0),  # 第一名算胜
                    is_draw=False,
                    score=pnl,
                    pnl=pnl
                )
            
            logger.info(
                f"小组{group_idx+1}结束: 晋级={[r[1] for r in results[:advance_count]]}"
            )
        
        logger.info(f"小组赛结束: {len(winners)}个Agent晋级")
        
        return match_records
    
    def _split_into_groups(self, agents: List, group_size: int) -> List[List]:
        """分组"""
        shuffled = agents.copy()
        random.shuffle(shuffled)
        
        groups = []
        for i in range(0, len(shuffled), group_size):
            group = shuffled[i:i+group_size]
            if len(group) >= 2:  # 至少2个Agent才能成组
                groups.append(group)
        
        return groups
    
    # ===== 锦标赛 =====
    
    def tournament(
        self,
        agents: List,
        market_data: pd.DataFrame,
        initial_capital: float = 10000.0
    ) -> MatchRecord:
        """
        锦标赛（淘汰赛）
        
        规则：
          - 单败淘汰
          - 1v1对决
          - 最后一个存活者获胜
          - 找到"最强策略"
          - 但可能损失多样性
        
        参数：
          - agents: Agent列表
          - market_data: 市场数据
          - initial_capital: 初始资金
        
        返回：
          - final_record: 决赛记录
        """
        logger.info(f"锦标赛开始: {len(agents)}个Agent参赛")
        
        remaining = agents.copy()
        round_num = 1
        
        while len(remaining) > 1:
            logger.info(f"第{round_num}轮: {len(remaining)}个Agent")
            
            # 配对
            pairs = self._pair_agents(remaining)
            next_round = []
            
            for agent1, agent2 in pairs:
                # 1v1对决
                match = self.duel_1v1(agent1, agent2, market_data, initial_capital)
                
                # 获胜者晋级
                winner_id = match.winner
                winner = agent1 if getattr(agent1, 'agent_id', '') == winner_id else agent2
                next_round.append(winner)
            
            remaining = next_round
            round_num += 1
        
        # 冠军
        champion = remaining[0]
        champion_id = getattr(champion, 'agent_id', 'Champion')
        
        logger.info(f"锦标赛结束: 冠军={champion_id}")
        
        # 返回最后一场（决赛）的记录
        if self.match_history:
            return self.match_history[-1]
        
        return None
    
    def _pair_agents(self, agents: List) -> List[Tuple]:
        """配对Agent"""
        shuffled = agents.copy()
        random.shuffle(shuffled)
        
        pairs = []
        for i in range(0, len(shuffled) - 1, 2):
            pairs.append((shuffled[i], shuffled[i+1]))
        
        # 如果Agent数量是奇数，最后一个Agent轮空（直接晋级）
        if len(shuffled) % 2 == 1:
            # TODO: 处理轮空
            pass
        
        return pairs
    
    # ===== 辅助方法 =====
    
    def get_leaderboard(self, sort_by: str = 'rating', top_k: int = None) -> List[AgentStats]:
        """
        获取排行榜
        
        参数：
          - sort_by: 排序依据
          - top_k: 只返回TopK
        """
        if top_k:
            return self.leaderboard.get_top_k(k=top_k, sort_by=sort_by)
        else:
            return self.leaderboard.get_rankings(sort_by=sort_by)
    
    def get_match_history(self, agent_id: Optional[str] = None) -> List[MatchRecord]:
        """
        获取对战历史
        
        参数：
          - agent_id: Agent ID（如果指定，只返回该Agent的历史）
        """
        if agent_id:
            return [m for m in self.match_history if agent_id in m.participants]
        else:
            return self.match_history
    
    def get_statistics(self) -> Dict:
        """获取竞技场统计信息"""
        return {
            'total_matches': len(self.match_history),
            'total_agents': len(self.leaderboard.stats),
            'duel_matches': sum(1 for m in self.match_history if m.match_type == 'duel'),
            'group_matches': sum(1 for m in self.match_history if m.match_type == 'group'),
            'tournament_matches': sum(1 for m in self.match_history if m.match_type == 'tournament'),
        }
    
    def reset(self):
        """重置竞技场"""
        self.leaderboard = Leaderboard()
        self.match_history.clear()
        self.next_match_id = 0
        logger.info("竞技场已重置")

