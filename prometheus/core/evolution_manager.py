"""
进化管理器 - 种群进化系统

核心功能：
1. 自然选择：淘汰表现差的Agent
2. 繁殖：优秀Agent交叉繁殖产生后代
3. 变异：后代基因发生变异
4. 统计：记录进化历史和多样性
"""

import random
import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


class EvolutionManager:
    """
    进化管理器
    
    负责：
    - 评估Agent适应度
    - 淘汰劣质Agent
    - 繁殖优秀Agent
    - 记录进化历史
    """
    
    def __init__(self, supervisor):
        """
        初始化进化管理器
        
        Args:
            supervisor: Supervisor实例
        """
        self.supervisor = supervisor
        self.generation = 0
        self.evolution_history: List[Dict] = []
        
        # 进化参数
        self.elimination_ratio = 0.30  # 淘汰后30%
        self.elite_ratio = 0.10        # 精英保留前10%
        self.mutation_rate = 0.20      # 20%概率变异
        
        logger.info("✅ 进化管理器初始化完成")
    
    def adjust_evolution_params_by_pressure(self, pressure: float) -> Dict:
        """
        根据环境压力动态调整进化参数（v4.1 OGAE系统）
        
        Args:
            pressure: 环境压力指数（0-1）
        
        Returns:
            Dict: 进化参数配置
                {
                    'elimination_ratio': 0.3,
                    'mutation_rate': 0.2,
                    'mode': '稳定优化'
                }
        """
        if pressure < 0.3:
            # 低压力：正常进化
            return {
                'elimination_ratio': 0.30,
                'mutation_rate': 0.15,
                'mode': '稳定优化🌊',
                'force_unlock': False
            }
        
        elif pressure < 0.6:
            # 中压力：适度加速
            return {
                'elimination_ratio': 0.25,
                'mutation_rate': 0.25,
                'mode': '适度适应⚡',
                'force_unlock': False
            }
        
        elif pressure < 0.8:
            # 高压力：快速变异
            return {
                'elimination_ratio': 0.20,
                'mutation_rate': 0.40,
                'mode': '应激进化🌪️',
                'force_unlock': False
            }
        
        else:
            # 极端压力：爆发式进化
            return {
                'elimination_ratio': 0.15,
                'mutation_rate': 0.60,
                'mode': '危机求生💀',
                'force_unlock': True  # 强制解锁稀有参数
            }
    
    def run_evolution_cycle(self, current_price: float = 0):
        """
        执行一轮进化周期
        
        流程：
        1. 评估所有Agent
        2. 淘汰表现最差的
        3. 选择优秀Agent繁殖
        4. 创建新Agent替代被淘汰的
        5. 记录统计数据
        
        Args:
            current_price: 当前市场价格
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"🧬 开始进化周期 - 第{self.generation + 1}代")
        logger.info(f"{'='*70}")
        
        # 1. 读取环境压力并调整进化参数（v4.1 OGAE）
        prophecy = self.supervisor.bulletin_board.get_latest('prophecy')
        environmental_pressure = 0.3  # 默认值
        
        if prophecy and 'environmental_pressure' in prophecy:
            environmental_pressure = prophecy['environmental_pressure']
            pressure_desc = prophecy.get('pressure_description', '')
            
            # 根据压力调整进化参数
            evolution_params = self.adjust_evolution_params_by_pressure(environmental_pressure)
            
            self.elimination_ratio = evolution_params['elimination_ratio']
            self.mutation_rate = evolution_params['mutation_rate']
            force_unlock = evolution_params.get('force_unlock', False)
            
            logger.info(f"🌍 环境压力: {environmental_pressure:.2f} ({pressure_desc})")
            logger.info(f"🔧 进化模式: {evolution_params['mode']}")
            logger.info(f"   变异率: {self.mutation_rate:.0%} | 淘汰率: {self.elimination_ratio:.0%}")
        else:
            force_unlock = False
            logger.info(f"🔧 进化模式: 正常模式（未检测到环境压力）")
        
        # 1.5 获取先知的进化提示（v4.2 自适应进化）
        evolution_hints = None
        if hasattr(self.supervisor, 'mastermind') and self.supervisor.mastermind:
            try:
                # 获取最新的市场数据
                market_data = prophecy if prophecy else {}
                evolution_hints = self.supervisor.mastermind.generate_evolution_hints(market_data)
            except Exception as e:
                logger.warning(f"获取进化提示失败: {e}")
                evolution_hints = None
        
        # 2. 评估Agent表现
        rankings = self.supervisor.rank_agent_performance(current_price)
        
        if not rankings:
            logger.warning("无Agent可进化")
            return
        
        total_agents = len(rankings)
        
        # 3. 识别精英、存活者和淘汰者
        elite_count = max(1, int(total_agents * self.elite_ratio))
        eliminate_count = max(1, int(total_agents * self.elimination_ratio))
        
        elite_agents = rankings[:elite_count]
        survivors = rankings[:-eliminate_count]
        eliminated = rankings[-eliminate_count:]
        
        logger.info(f"📊 种群评估:")
        logger.info(f"   总数: {total_agents}")
        logger.info(f"   精英: {elite_count} (永久保留)")
        logger.info(f"   存活: {len(survivors)}")
        logger.info(f"   淘汰: {eliminate_count}")
        
        # 4. 淘汰Agent
        eliminated_ids = []
        for agent_id, data in eliminated:
            eliminated_ids.append(agent_id)
            pnl = data.get('total_pnl', 0)
            logger.info(f"   💀 淘汰 {agent_id} (PnL=${pnl:+.2f})")
            
            # 从Supervisor中移除（agents是list，需要找到对象后remove）
            agent_to_remove = None
            for agent in self.supervisor.agents:
                if agent.agent_id == agent_id:
                    agent_to_remove = agent
                    break
            
            if agent_to_remove:
                self.supervisor.agents.remove(agent_to_remove)
                logger.debug(f"   已从agents列表移除: {agent_id}")
            
            # 移除账户系统（agent_accounts是dict）
            if agent_id in self.supervisor.agent_accounts:
                del self.supervisor.agent_accounts[agent_id]
                logger.debug(f"   已删除账户: {agent_id}")
        
        # 5. 繁殖新Agent
        new_agents = []
        
        # 创建agent_id到agent的映射（agents是list不是dict）
        agent_map = {agent.agent_id: agent for agent in self.supervisor.agents}
        
        for i in range(eliminate_count):
            # 选择两个优秀父母（禁止自交配）
            parent1_id, parent1_data = self._select_parent(survivors)
            
            # 选择第二个父母时，确保与第一个不同
            max_attempts = 10
            for attempt in range(max_attempts):
                parent2_id, parent2_data = self._select_parent(survivors)
                if parent2_id != parent1_id:
                    break
                if attempt == max_attempts - 1:
                    logger.warning(f"无法找到不同的父母，使用相同父母（种群太小）")
            
            parent1 = agent_map.get(parent1_id)
            parent2 = agent_map.get(parent2_id)
            
            if not parent1 or not parent2:
                logger.warning(f"找不到父母Agent: {parent1_id}, {parent2_id}")
                continue
            
            # 检查父母是否有EvolvableGene
            if not self._has_evolvable_gene(parent1) or not self._has_evolvable_gene(parent2):
                logger.warning(f"父母缺少可进化基因，跳过繁殖")
                continue
            
            # 如果还是相同父母，记录警告
            if parent1_id == parent2_id:
                logger.warning(f"⚠️ 自交配: {parent1_id} × {parent1_id}")
            else:
                logger.debug(f"✓ 交叉繁殖: {parent1_id} × {parent2_id}")
            
            # 交叉繁殖（传递父母的Agent ID）
            child_gene = parent1.gene.crossover(
                parent2.gene, 
                parent1_agent_id=parent1.agent_id,
                parent2_agent_id=parent2.agent_id
            )
            
            # 变异（提高变异率到50%，增大变异幅度到0.20，传递先知提示）
            is_mutated = False
            if random.random() < self.mutation_rate:
                child_gene = child_gene.mutate(
                    mutation_rate=0.5, 
                    mutation_strength=0.20,
                    environmental_hints=evolution_hints  # 传递先知提示
                )
                is_mutated = True
                logger.info(f"   🧬 基因变异: 第{child_gene.generation}代")
            
            # 极端压力下强制解锁稀有参数
            rare_unlocked = None
            if force_unlock and random.random() < 0.3:  # 30%概率
                if len(child_gene.active_params) < 12:  # 避免过度复杂
                    # 尝试解锁稀有参数
                    rare_params = ['market_timing', 'fear_control', 'profit_locking']
                    unlockable = [p for p in rare_params if p not in child_gene.active_params]
                    if unlockable:
                        new_param = random.choice(unlockable)
                        child_gene.active_params[new_param] = random.uniform(0.3, 0.7)
                        rare_unlocked = new_param
                        logger.info(f"   💎 危机解锁: {new_param} (稀有参数)")
            
            # 创建新Agent
            new_agent_id = f"Agent_{self.supervisor.next_agent_id:02d}"
            self.supervisor.next_agent_id += 1
            
            # 实际创建Agent实例
            from prometheus.core.agent_v4 import AgentV4
            from prometheus.core.ledger_system import AgentAccountSystem
            
            new_agent = AgentV4(
                agent_id=new_agent_id,
                gene=child_gene,
                personality=None,  # 随机生成
                initial_capital=self.supervisor.config.get('agent_initial_capital', 10000),
                bulletin_board=self.supervisor.bulletin_board
            )
            
            # 确保Agent有顿悟计数器
            if not hasattr(new_agent, 'epiphany_count'):
                new_agent.epiphany_count = 0
            
            # 添加到Supervisor的agents列表
            self.supervisor.agents.append(new_agent)
            
            # 创建账户系统
            account_system = AgentAccountSystem(
                agent_id=new_agent_id,
                initial_capital=self.supervisor.config.get('agent_initial_capital', 10000),
                public_ledger=self.supervisor.public_ledger
            )
            self.supervisor.agent_accounts[new_agent_id] = account_system
            
            # 构建Agent描述（带标注）
            generation_label = f"第{child_gene.generation}代"
            if is_mutated:
                generation_label += "（突变）"
            if rare_unlocked:
                generation_label += f"（稀有参数：{rare_unlocked}）"
            
            logger.info(f"   👶 新Agent诞生: {new_agent_id} "
                       f"(父母: {parent1_id} × {parent2_id}, "
                       f"{generation_label}, "
                       f"{child_gene.get_param_count()}参数)")
            
            new_agents.append((new_agent_id, child_gene))
        
        # 6. 记录进化统计
        self._record_generation_stats(rankings, elite_count, eliminate_count, new_agents)
        
        self.generation += 1
        
        logger.info(f"✅ 进化周期完成 - 进入第{self.generation}代")
        logger.info(f"{'='*70}\n")
    
    def _select_parent(self, survivors: List[Tuple]) -> Tuple[str, Dict]:
        """
        选择父母（锦标赛选择）
        
        从存活者中随机选择3个，取最优的
        
        Args:
            survivors: 存活者列表
        
        Returns:
            (agent_id, performance_data)
        """
        tournament_size = min(3, len(survivors))
        candidates = random.sample(survivors, tournament_size)
        
        # 选择得分最高的
        best = max(candidates, key=lambda x: x[1].get('score', 0))
        return best
    
    def _has_evolvable_gene(self, agent) -> bool:
        """检查Agent是否有可进化基因"""
        from prometheus.core.evolvable_gene import EvolvableGene
        
        return (hasattr(agent, 'gene') and 
                isinstance(agent.gene, EvolvableGene))
    
    def _record_generation_stats(self, rankings, elite_count, eliminate_count, new_agents):
        """记录每代统计数据"""
        # 🐛 修复：supervisor.agents是List，不是Dict，需要通过agent_id查找
        all_agents = []
        for agent_id, _ in rankings:
            # 从agents列表中找到对应的agent
            for agent in self.supervisor.agents:
                if hasattr(agent, 'agent_id') and agent.agent_id == agent_id:
                    all_agents.append(agent)
                    break
        
        # 计算参数复杂度
        param_counts = []
        for agent in all_agents:
            if self._has_evolvable_gene(agent):
                param_counts.append(agent.gene.get_param_count())
        
        # 计算盈亏统计
        all_pnl = [data.get('total_pnl', 0) for _, data in rankings]
        
        # 计算多样性（基因相似度）
        diversity = self._calculate_diversity(all_agents)
        
        stats = {
            'generation': self.generation,
            'timestamp': datetime.now().isoformat(),
            'population_size': len(rankings),
            'elite_count': elite_count,
            'eliminate_count': eliminate_count,
            'new_agents_count': len(new_agents),
            
            # 参数复杂度
            'avg_params': np.mean(param_counts) if param_counts else 3,
            'max_params': max(param_counts) if param_counts else 3,
            'min_params': min(param_counts) if param_counts else 3,
            
            # 性能统计
            'avg_pnl': np.mean(all_pnl) if all_pnl else 0,
            'max_pnl': max(all_pnl) if all_pnl else 0,
            'min_pnl': min(all_pnl) if all_pnl else 0,
            'profitable_ratio': sum(1 for pnl in all_pnl if pnl > 0) / len(all_pnl) if all_pnl else 0,
            
            # 多样性
            'gene_diversity': diversity,
        }
        
        self.evolution_history.append(stats)
        
        # 输出统计
        logger.info(f"📊 第{self.generation}代统计:")
        logger.info(f"   平均参数: {stats['avg_params']:.1f} (范围: {stats['min_params']}-{stats['max_params']})")
        logger.info(f"   平均PnL: ${stats['avg_pnl']:+.2f}")
        logger.info(f"   盈利比例: {stats['profitable_ratio']:.1%}")
        logger.info(f"   基因多样性: {stats['gene_diversity']:.2f}")
    
    def _calculate_diversity(self, agents: List) -> float:
        """
        计算种群基因多样性
        
        使用参数方差作为多样性指标
        
        Args:
            agents: Agent列表
        
        Returns:
            多样性得分 (0-1, 越高越多样)
        """
        if len(agents) < 2:
            logger.debug(f"[多样性计算] Agent数量<2: {len(agents)}")
            return 0.0
        
        # 收集所有Agent的所有参数
        all_param_values = {}
        agents_with_genes = 0
        
        for agent in agents:
            if not self._has_evolvable_gene(agent):
                logger.debug(f"[多样性计算] Agent {agent.agent_id} 无可进化基因")
                continue
            
            agents_with_genes += 1
            
            for param, value in agent.gene.active_params.items():
                if param not in all_param_values:
                    all_param_values[param] = []
                all_param_values[param].append(value)
        
        logger.debug(f"[多样性计算] 总Agent={len(agents)}, 有基因的Agent={agents_with_genes}, 参数种类={len(all_param_values)}")
        
        if not all_param_values:
            logger.warning(f"[多样性计算] 无有效参数值")
            return 0.0
        
        # DEBUG: 输出前5个Agent的基因ID和参数值
        if logger.isEnabledFor(logging.DEBUG):
            for i, agent in enumerate(agents[:5]):
                if self._has_evolvable_gene(agent):
                    logger.debug(f"  Agent {agent.agent_id}: gene_id={id(agent.gene)}, params={agent.gene.active_params}")
        
        # 计算每个参数的方差
        variances = []
        for param, values in all_param_values.items():
            if len(values) > 1:
                var = np.var(values)
                variances.append(var)
                logger.debug(f"[多样性计算] {param}: 方差={var:.6f}, 范围=[{min(values):.4f}, {max(values):.4f}], 样本数={len(values)}")
        
        if not variances:
            logger.warning(f"[多样性计算] 无方差数据")
            return 0.0
        
        # 平均方差作为多样性指标
        avg_variance = np.mean(variances)
        
        # 归一化到0-1（方差最大为0.25，当值在0和1之间均匀分布时）
        diversity = min(1.0, avg_variance / 0.25 * 2)
        
        logger.debug(f"[多样性计算] 平均方差={avg_variance:.6f}, 多样性={diversity:.4f}")
        
        return diversity
    
    def get_evolution_summary(self) -> Dict:
        """获取进化历史总结"""
        if not self.evolution_history:
            return {
                'total_generations': 0,
                'current_generation': 0
            }
        
        latest = self.evolution_history[-1]
        first = self.evolution_history[0]
        
        return {
            'total_generations': self.generation,
            'current_generation': self.generation,
            'population_size': latest['population_size'],
            
            # 进化趋势
            'param_growth': latest['avg_params'] - first['avg_params'],
            'performance_improvement': latest['avg_pnl'] - first['avg_pnl'],
            'diversity_trend': latest['gene_diversity'] - first.get('gene_diversity', 0),
            
            # 最佳记录
            'best_avg_pnl': max(h['avg_pnl'] for h in self.evolution_history),
            'best_diversity': max(h.get('gene_diversity', 0) for h in self.evolution_history),
        }
    
    def should_run_evolution(self, cycle_count: int, evolution_interval: int = 50) -> bool:
        """
        动态判断是否应该运行进化周期（v4.2智能调度）
        
        判断依据（满足任一即触发）：
        1. Agent平均交易次数达标（优先）
        2. 达到基础周期间隔（兜底）
        3. 种群危机紧急进化（应急）
        
        Args:
            cycle_count: 当前周期数
            evolution_interval: 默认进化间隔（被动态调整）
        
        Returns:
            是否应该进化
        """
        if cycle_count <= 0:
            return False
        
        # 获取交易模式
        trading_mode = self.supervisor.config.get('TRADING_MODE', 'okx')
        
        # 根据模式设置参数
        if trading_mode == 'mock':
            base_interval = 30       # Mock模式：30周期
            min_trades = 10          # 最少10笔交易
            emergency_interval = 15  # 危机：15周期
        else:
            base_interval = 100      # OKX模式：100周期
            min_trades = 15          # 最少15笔交易
            emergency_interval = 50  # 危机：50周期
        
        # 策略1：基于平均交易次数（优先）
        avg_trades = self._get_avg_trade_count()
        if avg_trades >= min_trades:
            logger.info(f"🎯 进化触发: 平均交易{avg_trades:.1f}笔≥{min_trades}笔")
            return True
        
        # 策略2：基于固定周期（兜底）
        if cycle_count % base_interval == 0:
            logger.info(f"🎯 进化触发: 达到基础周期{base_interval}")
            return True
        
        # 策略3：紧急进化（种群危机）
        if cycle_count >= emergency_interval:
            profitable_ratio = self._get_profitable_ratio()
            if profitable_ratio < 0.1:  # 盈利Agent<10%
                logger.warning(f"⚠️ 种群危机(盈利率{profitable_ratio:.1%})，触发紧急进化")
                return True
        
        return False
    
    def _get_avg_trade_count(self) -> float:
        """计算Agent平均交易次数"""
        total_trades = 0
        agent_count = 0
        
        for agent in self.supervisor.agents:
            agent_id = getattr(agent, 'agent_id', None)
            if agent_id and agent_id in self.supervisor.agent_accounts:
                account = self.supervisor.agent_accounts[agent_id]
                trade_count = len(account.private_ledger.trade_history)
                total_trades += trade_count
                agent_count += 1
        
        return total_trades / agent_count if agent_count > 0 else 0
    
    def _get_profitable_ratio(self) -> float:
        """计算盈利Agent的比例"""
        profitable_count = 0
        total_count = 0
        
        for agent in self.supervisor.agents:
            agent_id = getattr(agent, 'agent_id', None)
            if agent_id and agent_id in self.supervisor.agent_accounts:
                account = self.supervisor.agent_accounts[agent_id]
                total_pnl = account.private_ledger.total_pnl
                if total_pnl > 0:
                    profitable_count += 1
                total_count += 1
        
        return profitable_count / total_count if total_count > 0 else 0

