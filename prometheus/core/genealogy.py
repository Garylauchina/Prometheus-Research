"""
族谱系统 (Genealogy System)
============================

追踪Agent的血缘关系，实现生殖隔离，防止近亲繁殖。

核心功能：
1. 追踪Agent的祖先和后代
2. 计算两个Agent之间的亲缘系数
3. 判断两个Agent是否可以交配
4. 管理家族和血统

Author: Prometheus-Quant Team
Version: 5.0.0
Date: 2025-12-04
"""

import uuid
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentGenealogy:
    """Agent族谱信息"""
    agent_id: str
    parent1_id: Optional[str] = None
    parent2_id: Optional[str] = None
    generation: int = 1
    birth_time: float = 0.0
    family_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """创世Agent（第1代）没有父母"""
        if self.generation == 1:
            self.parent1_id = None
            self.parent2_id = None
    
    def is_genesis(self) -> bool:
        """是否为创世Agent"""
        return self.generation == 1 and self.parent1_id is None
    
    def get_parents(self) -> List[str]:
        """获取父母ID列表"""
        parents = []
        if self.parent1_id:
            parents.append(self.parent1_id)
        if self.parent2_id:
            parents.append(self.parent2_id)
        return parents


@dataclass
class Family:
    """家族 - 代表一个遗传群体"""
    family_id: str
    founder_id: str
    members: List[str] = field(default_factory=list)
    generation_count: int = 1
    traits: Dict = field(default_factory=dict)
    
    def add_member(self, agent_id: str):
        """添加家族成员"""
        if agent_id not in self.members:
            self.members.append(agent_id)
    
    def get_size(self) -> int:
        """获取家族规模"""
        return len(self.members)


class GenealogyTree:
    """
    族谱树 - 追踪Agent血缘关系的核心类
    
    使用方法：
    ```python
    tree = GenealogyTree()
    
    # 添加创世Agent
    tree.add_genesis_agent('Agent_01')
    tree.add_genesis_agent('Agent_02')
    
    # 添加后代
    tree.add_agent('Agent_03', 'Agent_01', 'Agent_02', generation=2)
    
    # 检查是否可以交配
    can_mate = tree.can_mate('Agent_03', 'Agent_01')  # False (父子关系)
    
    # 获取族谱信息
    lineage = tree.get_lineage('Agent_03', depth=3)
    ```
    """
    
    def __init__(self, max_kinship: float = 0.125):
        """
        初始化族谱树
        
        Args:
            max_kinship: 最大允许亲缘系数，默认0.125（堂兄妹级别）
                        0.5 = 父母/子女
                        0.25 = 兄弟姐妹/祖父母
                        0.125 = 堂兄妹/叔侄
        """
        self.agents: Dict[str, AgentGenealogy] = {}
        self.families: Dict[str, Family] = {}
        self.max_kinship = max_kinship
        
        # 缓存：避免重复计算亲缘系数
        self._kinship_cache: Dict[Tuple[str, str], float] = {}
        
        logger.info(f"🧬 族谱系统初始化完成 (最大亲缘系数: {max_kinship})")
    
    def add_genesis_agent(self, agent_id: str, birth_time: float = 0.0):
        """
        添加创世Agent（第1代，无父母）
        
        Args:
            agent_id: Agent ID
            birth_time: 出生时间（周期数或时间戳）
        """
        if agent_id in self.agents:
            logger.warning(f"Agent {agent_id} 已存在于族谱中")
            return
        
        # 创建族谱信息
        genealogy = AgentGenealogy(
            agent_id=agent_id,
            generation=1,
            birth_time=birth_time
        )
        
        # 创建家族（创世Agent是新家族的创始人）
        family_id = f"F{uuid.uuid4().hex[:8]}"
        family = Family(
            family_id=family_id,
            founder_id=agent_id,
            members=[agent_id]
        )
        
        genealogy.family_id = family_id
        
        self.agents[agent_id] = genealogy
        self.families[family_id] = family
        
        logger.debug(f"🌱 创世Agent {agent_id} 加入族谱 (家族: {family_id})")
    
    def add_agent(
        self,
        agent_id: str,
        parent1_id: str,
        parent2_id: str,
        generation: int,
        birth_time: float = 0.0
    ):
        """
        添加Agent到族谱（有父母的后代）
        
        Args:
            agent_id: Agent ID
            parent1_id: 父母1的ID
            parent2_id: 父母2的ID
            generation: 代数
            birth_time: 出生时间
        """
        if agent_id in self.agents:
            logger.warning(f"Agent {agent_id} 已存在于族谱中")
            return
        
        # 验证父母存在
        if parent1_id not in self.agents:
            logger.error(f"父母 {parent1_id} 不存在于族谱中")
            return
        if parent2_id not in self.agents:
            logger.error(f"父母 {parent2_id} 不存在于族谱中")
            return
        
        # 创建族谱信息
        genealogy = AgentGenealogy(
            agent_id=agent_id,
            parent1_id=parent1_id,
            parent2_id=parent2_id,
            generation=generation,
            birth_time=birth_time
        )
        
        # 确定家族（继承父母1的家族）
        parent1_family_id = self.agents[parent1_id].family_id
        genealogy.family_id = parent1_family_id
        
        # 添加到家族
        if parent1_family_id and parent1_family_id in self.families:
            self.families[parent1_family_id].add_member(agent_id)
            self.families[parent1_family_id].generation_count = max(
                self.families[parent1_family_id].generation_count,
                generation
            )
        
        # 更新父母的子女列表
        self.agents[parent1_id].children_ids.append(agent_id)
        self.agents[parent2_id].children_ids.append(agent_id)
        
        self.agents[agent_id] = genealogy
        
        # 清除相关的亲缘系数缓存
        self._invalidate_kinship_cache_for(agent_id)
        
        logger.debug(
            f"👶 Agent {agent_id} 加入族谱 "
            f"(父母: {parent1_id} × {parent2_id}, 第{generation}代)"
        )
    
    def calculate_kinship(self, agent1_id: str, agent2_id: str) -> float:
        """
        计算两个Agent之间的亲缘系数 (Coefficient of Kinship)
        
        亲缘系数定义：
        - 0.0 = 完全无关
        - 0.5 = 父母/子女（一级亲属）
        - 0.25 = 兄弟姐妹/祖父母（二级亲属）
        - 0.125 = 堂兄妹/叔侄（三级亲属）
        
        Args:
            agent1_id: Agent 1的ID
            agent2_id: Agent 2的ID
        
        Returns:
            float: 亲缘系数 (0.0-1.0)
        """
        # 相同Agent，亲缘系数为1.0
        if agent1_id == agent2_id:
            return 1.0
        
        # 检查缓存
        cache_key = tuple(sorted([agent1_id, agent2_id]))
        if cache_key in self._kinship_cache:
            return self._kinship_cache[cache_key]
        
        # 确保两个Agent都存在
        if agent1_id not in self.agents or agent2_id not in self.agents:
            return 0.0
        
        agent1 = self.agents[agent1_id]
        agent2 = self.agents[agent2_id]
        
        # 如果两个Agent来自不同家族，亲缘系数为0
        if agent1.family_id != agent2.family_id:
            kinship = 0.0
        else:
            # 计算亲缘系数
            kinship = self._calculate_kinship_recursive(agent1_id, agent2_id, set())
        
        # 缓存结果
        self._kinship_cache[cache_key] = kinship
        
        return kinship
    
    def _calculate_kinship_recursive(
        self,
        agent1_id: str,
        agent2_id: str,
        visited: Set[str]
    ) -> float:
        """
        递归计算亲缘系数（简化版本）
        
        注：完整的亲缘系数计算较为复杂，此处使用简化算法：
        1. 检查直系关系（父子/祖孙）
        2. 检查旁系关系（兄弟姐妹）
        3. 使用共同祖先路径长度估算
        """
        # 防止无限递归
        if agent1_id in visited or agent2_id in visited:
            return 0.0
        
        visited.add(agent1_id)
        visited.add(agent2_id)
        
        agent1 = self.agents[agent1_id]
        agent2 = self.agents[agent2_id]
        
        # 检查是否为父子关系
        if agent1_id in agent2.get_parents():
            return 0.5  # 父母-子女
        if agent2_id in agent1.get_parents():
            return 0.5  # 子女-父母
        
        # 检查是否为兄弟姐妹
        if agent1.parent1_id and agent2.parent1_id:
            if (agent1.parent1_id == agent2.parent1_id or 
                agent1.parent1_id == agent2.parent2_id or
                agent1.parent2_id == agent2.parent1_id or
                agent1.parent2_id == agent2.parent2_id):
                return 0.25  # 兄弟姐妹
        
        # 查找共同祖先
        ancestors1 = self._get_ancestors(agent1_id, depth=5)
        ancestors2 = self._get_ancestors(agent2_id, depth=5)
        
        common_ancestors = ancestors1.intersection(ancestors2)
        
        if not common_ancestors:
            return 0.0  # 无共同祖先
        
        # 计算到最近共同祖先的距离
        min_distance = float('inf')
        for ancestor_id in common_ancestors:
            dist1 = self._get_distance_to_ancestor(agent1_id, ancestor_id)
            dist2 = self._get_distance_to_ancestor(agent2_id, ancestor_id)
            total_dist = dist1 + dist2
            min_distance = min(min_distance, total_dist)
        
        # 亲缘系数 ≈ 0.5^(距离)
        if min_distance < float('inf'):
            return 0.5 ** min_distance
        
        return 0.0
    
    def can_mate(self, agent1_id: str, agent2_id: str) -> bool:
        """
        判断两个Agent是否可以交配（生殖隔离检查）
        
        Args:
            agent1_id: Agent 1的ID
            agent2_id: Agent 2的ID
        
        Returns:
            bool: True表示可以交配，False表示不可以（近亲）
        """
        if agent1_id == agent2_id:
            return False  # 不能自交
        
        kinship = self.calculate_kinship(agent1_id, agent2_id)
        can_mate = kinship < self.max_kinship
        
        if not can_mate:
            logger.debug(
                f"🚫 生殖隔离: {agent1_id} × {agent2_id} "
                f"(亲缘系数 {kinship:.3f} ≥ {self.max_kinship})"
            )
        
        return can_mate
    
    def get_lineage(self, agent_id: str, depth: int = 5) -> Dict:
        """
        获取Agent的祖先谱系
        
        Args:
            agent_id: Agent ID
            depth: 追溯深度（代数）
        
        Returns:
            Dict: 谱系信息
            {
                'agent_id': str,
                'generation': int,
                'parents': [str, str],
                'grandparents': [...],
                'ancestors': {...},
                'family_id': str
            }
        """
        if agent_id not in self.agents:
            return {}
        
        agent = self.agents[agent_id]
        lineage = {
            'agent_id': agent_id,
            'generation': agent.generation,
            'family_id': agent.family_id,
            'is_genesis': agent.is_genesis(),
            'parents': agent.get_parents(),
            'ancestors': {}
        }
        
        # 递归获取祖先
        if depth > 0 and not agent.is_genesis():
            ancestors = self._get_ancestors_recursive(agent_id, depth)
            lineage['ancestors'] = ancestors
        
        return lineage
    
    def _get_ancestors(self, agent_id: str, depth: int = 5) -> Set[str]:
        """获取所有祖先的ID集合"""
        ancestors = set()
        
        def collect_ancestors(aid: str, current_depth: int):
            if current_depth <= 0 or aid not in self.agents:
                return
            
            agent = self.agents[aid]
            for parent_id in agent.get_parents():
                ancestors.add(parent_id)
                collect_ancestors(parent_id, current_depth - 1)
        
        collect_ancestors(agent_id, depth)
        return ancestors
    
    def _get_ancestors_recursive(self, agent_id: str, depth: int) -> Dict:
        """递归获取祖先信息"""
        if depth <= 0 or agent_id not in self.agents:
            return {}
        
        agent = self.agents[agent_id]
        ancestors = {}
        
        for parent_id in agent.get_parents():
            if parent_id in self.agents:
                ancestors[parent_id] = {
                    'generation': self.agents[parent_id].generation,
                    'parents': self.agents[parent_id].get_parents(),
                    'children': self._get_ancestors_recursive(parent_id, depth - 1)
                }
        
        return ancestors
    
    def _get_distance_to_ancestor(self, agent_id: str, ancestor_id: str) -> int:
        """计算到祖先的距离（代数）"""
        if agent_id == ancestor_id:
            return 0
        
        if agent_id not in self.agents:
            return 999
        
        agent = self.agents[agent_id]
        
        # BFS 搜索
        from collections import deque
        queue = deque([(agent_id, 0)])
        visited = set()
        
        while queue:
            current_id, dist = queue.popleft()
            
            if current_id == ancestor_id:
                return dist
            
            if current_id in visited:
                continue
            visited.add(current_id)
            
            if current_id in self.agents:
                for parent_id in self.agents[current_id].get_parents():
                    queue.append((parent_id, dist + 1))
        
        return 999  # 未找到路径
    
    def _invalidate_kinship_cache_for(self, agent_id: str):
        """清除与指定Agent相关的亲缘系数缓存"""
        keys_to_remove = [
            key for key in self._kinship_cache.keys()
            if agent_id in key
        ]
        for key in keys_to_remove:
            del self._kinship_cache[key]
    
    def get_statistics(self) -> Dict:
        """
        获取族谱统计信息
        
        Returns:
            Dict: 统计信息
            {
                'total_agents': int,
                'total_families': int,
                'avg_family_size': float,
                'max_generation': int,
                'genesis_agents': int
            }
        """
        genesis_count = sum(1 for a in self.agents.values() if a.is_genesis())
        max_gen = max((a.generation for a in self.agents.values()), default=0)
        
        family_sizes = [f.get_size() for f in self.families.values()]
        avg_family_size = sum(family_sizes) / len(family_sizes) if family_sizes else 0
        
        return {
            'total_agents': len(self.agents),
            'total_families': len(self.families),
            'avg_family_size': avg_family_size,
            'max_generation': max_gen,
            'genesis_agents': genesis_count
        }
    
    def clear_cache(self):
        """清空亲缘系数缓存"""
        self._kinship_cache.clear()
        logger.debug("🧹 族谱缓存已清空")


# 使用示例
if __name__ == "__main__":
    # 创建族谱
    tree = GenealogyTree(max_kinship=0.125)
    
    # 添加创世Agent
    tree.add_genesis_agent('Agent_01')
    tree.add_genesis_agent('Agent_02')
    tree.add_genesis_agent('Agent_03')
    
    # 添加第2代
    tree.add_agent('Agent_04', 'Agent_01', 'Agent_02', generation=2)
    tree.add_agent('Agent_05', 'Agent_01', 'Agent_03', generation=2)
    
    # 添加第3代
    tree.add_agent('Agent_06', 'Agent_04', 'Agent_05', generation=3)
    
    # 测试亲缘系数
    print("\n亲缘系数测试:")
    print(f"Agent_01 × Agent_04 (父子): {tree.calculate_kinship('Agent_01', 'Agent_04'):.3f}")
    print(f"Agent_04 × Agent_05 (兄弟姐妹): {tree.calculate_kinship('Agent_04', 'Agent_05'):.3f}")
    print(f"Agent_01 × Agent_06 (祖孙): {tree.calculate_kinship('Agent_01', 'Agent_06'):.3f}")
    print(f"Agent_02 × Agent_03 (无关): {tree.calculate_kinship('Agent_02', 'Agent_03'):.3f}")
    
    # 测试生殖隔离
    print("\n生殖隔离测试:")
    print(f"Agent_01 × Agent_04 可以交配: {tree.can_mate('Agent_01', 'Agent_04')}")
    print(f"Agent_02 × Agent_03 可以交配: {tree.can_mate('Agent_02', 'Agent_03')}")
    print(f"Agent_04 × Agent_05 可以交配: {tree.can_mate('Agent_04', 'Agent_05')}")
    
    # 获取谱系
    print("\nAgent_06 的谱系:")
    lineage = tree.get_lineage('Agent_06', depth=3)
    print(f"代数: {lineage['generation']}")
    print(f"父母: {lineage['parents']}")
    
    # 统计信息
    print("\n族谱统计:")
    stats = tree.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

