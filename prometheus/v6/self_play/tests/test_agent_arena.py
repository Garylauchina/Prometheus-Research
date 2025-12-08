"""
AgentArena测试套件

测试内容：
  1. 1v1对决
  2. 小组赛
  3. 锦标赛
  4. 排行榜
  5. ELO评级系统
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock

from prometheus.v6.self_play import (
    AgentArena,
    Leaderboard,
    MatchRecord,
    AgentStats
)


# ===== 测试数据 =====

@pytest.fixture
def market_data():
    """模拟市场数据"""
    dates = pd.date_range('2024-01-01', periods=100, freq='H')
    return pd.DataFrame({
        'timestamp': dates,
        'open': np.random.uniform(40000, 50000, 100),
        'high': np.random.uniform(40000, 50000, 100),
        'low': np.random.uniform(40000, 50000, 100),
        'close': np.random.uniform(40000, 50000, 100),
        'volume': np.random.uniform(1000, 5000, 100),
    })


@pytest.fixture
def mock_agents():
    """创建模拟Agent"""
    agents = []
    for i in range(10):
        agent = Mock()
        agent.agent_id = f'Agent{i:03d}'
        agents.append(agent)
    return agents


# ===== Leaderboard测试 =====

def test_leaderboard_initialization():
    """测试排行榜初始化"""
    leaderboard = Leaderboard(k_factor=32.0)
    assert leaderboard.k_factor == 32.0
    assert len(leaderboard.stats) == 0


def test_leaderboard_add_result():
    """测试添加对战结果"""
    leaderboard = Leaderboard()
    
    # 添加胜利
    leaderboard.add_result('Agent001', is_win=True, is_draw=False, score=100.0, pnl=500.0)
    
    assert 'Agent001' in leaderboard.stats
    assert leaderboard.stats['Agent001'].wins == 1
    assert leaderboard.stats['Agent001'].total_matches == 1
    assert leaderboard.stats['Agent001'].win_rate == 1.0


def test_leaderboard_elo_rating():
    """测试ELO评级系统"""
    leaderboard = Leaderboard(k_factor=32.0)
    
    # 添加两个Agent
    leaderboard.add_result('Agent001', is_win=True, is_draw=False, score=100.0, pnl=500.0, opponent_id='Agent002')
    leaderboard.add_result('Agent002', is_win=False, is_draw=False, score=50.0, pnl=-500.0, opponent_id='Agent001')
    
    # 检查ELO评级
    rating1 = leaderboard.get_rating('Agent001')
    rating2 = leaderboard.get_rating('Agent002')
    
    assert rating1 > 1500.0  # 胜者评级上升
    assert rating2 < 1500.0  # 负者评级下降
    assert rating1 + rating2 == pytest.approx(3000.0, rel=0.01)  # 总评级守恒


def test_leaderboard_rankings():
    """测试排名"""
    leaderboard = Leaderboard()
    
    # 添加多个Agent
    for i in range(5):
        leaderboard.add_result(
            f'Agent{i:03d}',
            is_win=(i % 2 == 0),
            is_draw=False,
            score=100.0 * (i + 1),
            pnl=500.0 * (i + 1)
        )
    
    # 获取排名
    rankings = leaderboard.get_rankings(sort_by='total_pnl')
    
    assert len(rankings) == 5
    assert rankings[0].agent_id == 'Agent004'  # 最高PnL
    assert rankings[0].total_pnl == 2500.0


def test_leaderboard_top_k():
    """测试TopK"""
    leaderboard = Leaderboard()
    
    # 添加10个Agent
    for i in range(10):
        leaderboard.add_result(
            f'Agent{i:03d}',
            is_win=(i % 2 == 0),
            is_draw=False,
            score=100.0 * (i + 1),
            pnl=500.0 * (i + 1)
        )
    
    # 获取Top3
    top3 = leaderboard.get_top_k(k=3, sort_by='total_pnl')
    
    assert len(top3) == 3
    assert top3[0].agent_id == 'Agent009'


# ===== AgentArena测试 =====

def test_arena_initialization():
    """测试竞技场初始化"""
    arena = AgentArena()
    assert arena.leaderboard is not None
    assert len(arena.match_history) == 0
    assert arena.next_match_id == 0


def test_arena_duel_1v1(mock_agents, market_data):
    """测试1v1对决"""
    arena = AgentArena()
    agent1 = mock_agents[0]
    agent2 = mock_agents[1]
    
    # 进行1v1对决
    match = arena.duel_1v1(agent1, agent2, market_data)
    
    # 检查对战记录
    assert match.match_type == 'duel'
    assert len(match.participants) == 2
    assert match.winner is not None
    assert match.loser is not None
    
    # 检查排行榜
    assert len(arena.leaderboard.stats) == 2


def test_arena_group_battle(mock_agents, market_data):
    """测试小组赛"""
    arena = AgentArena()
    
    # 进行小组赛
    matches = arena.group_battle(
        agents=mock_agents,
        market_data=market_data,
        group_size=5,
        advance_count=2
    )
    
    # 检查对战记录
    assert len(matches) == 2  # 10个Agent分2组
    assert all(m.match_type == 'group' for m in matches)
    
    # 检查排行榜
    assert len(arena.leaderboard.stats) > 0


def test_arena_tournament(mock_agents, market_data):
    """测试锦标赛"""
    arena = AgentArena()
    
    # 准备8个Agent（2的幂次方）
    agents_8 = mock_agents[:8]
    
    # 进行锦标赛
    final_match = arena.tournament(agents_8, market_data)
    
    # 检查决赛记录
    assert final_match is not None
    assert final_match.winner is not None
    
    # 检查对战记录（应该有7场比赛：4+2+1）
    assert len(arena.match_history) == 7


def test_arena_get_leaderboard(mock_agents, market_data):
    """测试获取排行榜"""
    arena = AgentArena()
    
    # 进行多场对决
    for i in range(5):
        arena.duel_1v1(mock_agents[i], mock_agents[i+1], market_data)
    
    # 获取排行榜
    rankings = arena.get_leaderboard(sort_by='rating', top_k=3)
    
    assert len(rankings) <= 3
    assert all(isinstance(r, AgentStats) for r in rankings)


def test_arena_get_match_history(mock_agents, market_data):
    """测试获取对战历史"""
    arena = AgentArena()
    
    # 进行多场对决
    arena.duel_1v1(mock_agents[0], mock_agents[1], market_data)
    arena.duel_1v1(mock_agents[0], mock_agents[2], market_data)
    
    # 获取Agent001的历史
    history = arena.get_match_history(agent_id='Agent000')
    
    assert len(history) == 2
    assert all('Agent000' in m.participants for m in history)


def test_arena_get_statistics(mock_agents, market_data):
    """测试获取统计信息"""
    arena = AgentArena()
    
    # 进行各种对战
    arena.duel_1v1(mock_agents[0], mock_agents[1], market_data)
    arena.group_battle(mock_agents, market_data, group_size=5, advance_count=2)
    
    # 获取统计信息
    stats = arena.get_statistics()
    
    assert 'total_matches' in stats
    assert 'total_agents' in stats
    assert 'duel_matches' in stats
    assert 'group_matches' in stats


def test_arena_reset(mock_agents, market_data):
    """测试竞技场重置"""
    arena = AgentArena()
    
    # 进行对决
    arena.duel_1v1(mock_agents[0], mock_agents[1], market_data)
    
    # 重置
    arena.reset()
    
    assert len(arena.match_history) == 0
    assert len(arena.leaderboard.stats) == 0
    assert arena.next_match_id == 0


# ===== 集成测试 =====

def test_arena_full_workflow(mock_agents, market_data):
    """测试完整工作流"""
    arena = AgentArena()
    
    # 1. 进行小组赛
    group_matches = arena.group_battle(mock_agents, market_data, group_size=5, advance_count=2)
    assert len(group_matches) == 2
    
    # 2. 获取排行榜
    rankings = arena.get_leaderboard(sort_by='rating')
    assert len(rankings) > 0
    
    # 3. 获取统计信息
    stats = arena.get_statistics()
    assert stats['total_matches'] == 2
    assert stats['group_matches'] == 2
    
    # 4. 获取对战历史
    history = arena.get_match_history()
    assert len(history) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

