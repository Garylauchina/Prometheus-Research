#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
30分钟交易测试脚本
功能：
1. 连接到OKX模拟盘
2. 平掉所有现有持仓
3. 创世生成5个Agent
4. 运行30分钟的交易测试
5. 记录详细交易日志
"""

import sys
import os
import time
import logging
import json
from datetime import datetime, timedelta
import random

# 添加项目路径
project_path = 'E:\\Trae_store\\prometheus-v30\\'
if os.path.exists(project_path):
    sys.path.insert(0, project_path)
else:
    print(f"错误: 项目路径不存在: {project_path}")
    sys.exit(1)

# 添加当前项目路径（用于导入evolution模块）
current_project = os.path.dirname(os.path.abspath(__file__))
if current_project not in sys.path:
    sys.path.insert(0, current_project)

# 导入进化系统模块
try:
    from evolution import EnhancedCapitalPool, EnvironmentalPressure
    print("[OK] Evolution模块导入成功")
except ImportError as e:
    print(f"[WARNING] Evolution模块导入失败: {e}")
    print("[INFO] 将使用本地定义的类")
    EnhancedCapitalPool = None
    EnvironmentalPressure = None

# 导入所需模块 - 使用与check_positions.py相同的导入方式
try:
    from adapters.okx_adapter import OKXTradingAdapter
    from config import CONFIG_V3 as CONFIG
    # 由于agent、gene等模块可能存在相对导入问题，我们将创建简化版本
    print("[OK] 必要模块导入成功")
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    # 打印导入路径帮助调试
    print(f"当前Python路径: {sys.path}")
    print(f"当前工作目录: {os.getcwd()}")
    sys.exit(1)

# 创建简化版的核心类，避免导入问题
class SimpleGene:
    """简化版的基因类（优化版）"""
    def __init__(self):
        self.preferences = {}
        self.strategy_type = None
    
    @classmethod
    def random(cls):
        """生成随机基因，但带有策略类型倾向"""
        gene = cls()
        
        # 随机选择一个策略类型（40%概率有明确类型，60%平衡型）
        strategy_types = [
            'aggressive_bull',    # 激进多头
            'defensive_bull',     # 防守多头
            'aggressive_bear',    # 激进空头
            'defensive_bear',     # 防守空头
            'volatility_hunter',  # 波动率猎手
            'trend_follower',     # 趋势跟随
            'mean_reversion',     # 均值回归
            'balanced'            # 平衡型
        ]
        
        # 40%概率选择特定类型，60%平衡型
        if random.random() < 0.4:
            gene.strategy_type = random.choice(strategy_types[:-1])
        else:
            gene.strategy_type = 'balanced'
        
        # 根据策略类型生成偏好
        gene.preferences = gene._generate_preferences_by_type(gene.strategy_type)
        
        return gene
    
    def _generate_preferences_by_type(self, strategy_type):
        """根据策略类型生成合理的偏好"""
        base_prefs = {}
        
        if strategy_type == 'aggressive_bull':
            # 激进多头：强烈偏好各种牛市特征
            base_prefs = {
                'strong_bull': random.uniform(0.8, 1.0),
                'bull': random.uniform(0.7, 0.9),
                'weak_bull': random.uniform(0.5, 0.7),
                'sideways': random.uniform(0.2, 0.4),
                'weak_bear': random.uniform(0.1, 0.3),
                'bear': random.uniform(0.0, 0.2),
                'strong_bear': random.uniform(0.0, 0.1),
                'breakout': random.uniform(0.7, 1.0),
                'high_vol': random.uniform(0.6, 0.9),
                'greed': random.uniform(0.6, 0.9)
            }
        
        elif strategy_type == 'defensive_bull':
            # 防守多头：偏好牛市但谨慎
            base_prefs = {
                'strong_bull': random.uniform(0.5, 0.7),
                'bull': random.uniform(0.6, 0.8),
                'weak_bull': random.uniform(0.7, 0.9),
                'sideways': random.uniform(0.4, 0.6),
                'weak_bear': random.uniform(0.2, 0.4),
                'bear': random.uniform(0.1, 0.3),
                'strong_bear': random.uniform(0.0, 0.2),
                'low_vol': random.uniform(0.6, 0.9),
                'neutral': random.uniform(0.5, 0.8)
            }
        
        elif strategy_type == 'aggressive_bear':
            # 激进空头：强烈偏好熊市
            base_prefs = {
                'strong_bull': random.uniform(0.0, 0.1),
                'bull': random.uniform(0.0, 0.2),
                'weak_bull': random.uniform(0.1, 0.3),
                'sideways': random.uniform(0.2, 0.4),
                'weak_bear': random.uniform(0.5, 0.7),
                'bear': random.uniform(0.7, 0.9),
                'strong_bear': random.uniform(0.8, 1.0),
                'breakdown': random.uniform(0.7, 1.0),
                'fear': random.uniform(0.7, 1.0)
            }
        
        elif strategy_type == 'volatility_hunter':
            # 波动率猎手：偏好高波动环境
            base_prefs = {
                'strong_bull': random.uniform(0.6, 0.8),
                'bull': random.uniform(0.4, 0.6),
                'weak_bull': random.uniform(0.3, 0.5),
                'sideways': random.uniform(0.1, 0.3),
                'weak_bear': random.uniform(0.3, 0.5),
                'bear': random.uniform(0.4, 0.6),
                'strong_bear': random.uniform(0.6, 0.8),
                'high_vol': random.uniform(0.8, 1.0),
                'extreme_high_vol': random.uniform(0.7, 0.9),
                'breakout': random.uniform(0.7, 0.9),
                'breakdown': random.uniform(0.7, 0.9)
            }
        
        elif strategy_type == 'trend_follower':
            # 趋势跟随：偏好明确趋势
            base_prefs = {
                'strong_bull': random.uniform(0.7, 0.9),
                'bull': random.uniform(0.6, 0.8),
                'weak_bull': random.uniform(0.3, 0.5),
                'sideways': random.uniform(0.1, 0.3),
                'weak_bear': random.uniform(0.3, 0.5),
                'bear': random.uniform(0.6, 0.8),
                'strong_bear': random.uniform(0.7, 0.9),
                'breakout': random.uniform(0.8, 1.0),
                'breakdown': random.uniform(0.8, 1.0)
            }
        
        elif strategy_type == 'mean_reversion':
            # 均值回归：偏好极端后的回归
            base_prefs = {
                'strong_bull': random.uniform(0.2, 0.4),
                'bull': random.uniform(0.3, 0.5),
                'weak_bull': random.uniform(0.5, 0.7),
                'sideways': random.uniform(0.7, 0.9),
                'weak_bear': random.uniform(0.5, 0.7),
                'bear': random.uniform(0.3, 0.5),
                'strong_bear': random.uniform(0.2, 0.4),
                'extreme_fear': random.uniform(0.8, 1.0),
                'extreme_greed': random.uniform(0.8, 1.0),
                'pullback': random.uniform(0.7, 0.9)
            }
        
        else:  # balanced
            # 平衡型：所有特征都有中等偏好
            all_features = ['strong_bull', 'bull', 'weak_bull', 'sideways', 
                          'weak_bear', 'bear', 'strong_bear']
            base_prefs = {feature: random.uniform(0.4, 0.6) for feature in all_features}
        
        # 添加一些随机性避免完全相同
        for key in base_prefs:
            noise = random.gauss(0, 0.05)  # 5%标准差的噪音
            base_prefs[key] = max(0.0, min(1.0, base_prefs[key] + noise))
        
        return base_prefs
    
    def get_top_preferences(self, count=3):
        return sorted(self.preferences.items(), key=lambda x: x[1], reverse=True)[:count]
    
    def generate_species_name(self):
        return f"Species_{random.randint(1000, 9999)}"

class SimpleStrategy:
    """简化版的策略类"""
    def __init__(self, gene, config):
        self.gene = gene
        self.config = config

# ===================================================================
# 如果evolution模块未导入，使用本地定义
# ===================================================================
if EnhancedCapitalPool is None:
    class EnhancedCapitalPool:
        """增强的资金池系统（本地定义）"""
        def __init__(self, initial_capital):
            self.initial_capital = initial_capital
            self.total_capital = initial_capital
            self.allocated_capital = 0      # 已分配给Agent
            self.available_capital = initial_capital  # 可用资金
            self.recycled_capital = 0       # 回收资金累计
            self.subsidized_capital = 0     # 资助资金累计
        
        def allocate_to_agent(self, amount):
            """分配给Agent"""
            if self.available_capital >= amount:
                self.available_capital -= amount
                self.allocated_capital += amount
                return True
            return False
        
        def recycle_from_death(self, amount, recovery_rate=1.0):
            """从死亡Agent回收"""
            recycled = amount * recovery_rate
            self.available_capital += recycled
            self.allocated_capital -= amount
            self.recycled_capital += recycled
            return recycled
        
        def subsidize_reproduction(self, amount):
            """资助繁殖"""
            actual_subsidy = min(amount, self.available_capital)
            if actual_subsidy > 0:
                self.available_capital -= actual_subsidy
                self.allocated_capital += actual_subsidy
                self.subsidized_capital += actual_subsidy
            return actual_subsidy
        
        def get_status(self):
            """资金池状态"""
            return {
                'total': self.total_capital,
                'available': self.available_capital,
                'allocated': self.allocated_capital,
                'utilization': self.allocated_capital / self.total_capital if self.total_capital > 0 else 0,
                'recycled': self.recycled_capital,
                'subsidized': self.subsidized_capital
            }

if EnvironmentalPressure is None:
    class EnvironmentalPressure:
        """环境压力系统（本地定义）"""
        def __init__(self):
            self.pressure = 0.5  # 初始中等压力
            self.history = []
        
        def update(self, market_features, agents, capital_pool_status):
            """动态更新压力"""
            import numpy as np
            
            # 1. 市场因素（40%）
            market_volatility = market_features.get('high_vol', 0) + market_features.get('extreme_high_vol', 0) * 0.5
            market_fear = market_features.get('fear', 0) + market_features.get('extreme_fear', 0) * 0.5
            market_factor = (market_volatility * 0.6 + market_fear * 0.4) * 0.4
            
            # 2. 种群因素（30%）
            alive_agents = [a for a in agents if a.is_alive]
            if alive_agents:
                avg_roi = np.mean([a.roi for a in alive_agents])
                survival_rate = len(alive_agents) / len(agents)
                # ROI越低压力越大，存活率越低压力越大
                population_factor = ((1 - min(max(avg_roi, -1), 1)) * 0.6 + (1 - survival_rate) * 0.4) * 0.3
            else:
                population_factor = 1.0 * 0.3
            
            # 3. 资金池因素（30%）
            utilization = capital_pool_status.get('utilization', 0.5)
            # 资金利用率过高（>90%）或过低（<30%）都增加压力
            if utilization > 0.9:
                capital_factor = (utilization - 0.5) * 0.3
            elif utilization < 0.3:
                capital_factor = (0.5 - utilization) * 0.3
            else:
                capital_factor = 0
            
            # 综合计算（平滑处理）
            new_pressure = market_factor + population_factor + capital_factor
            
            # 平滑：70%旧值 + 30%新值
            self.pressure = self.pressure * 0.7 + new_pressure * 0.3
            
            # 限制在0-1范围
            self.pressure = max(0.0, min(1.0, self.pressure))
            
            self.history.append(self.pressure)
            if len(self.history) > 20:
                self.history = self.history[-20:]
            
            return self.pressure
        
        def get_phase(self):
            """获取当前阶段"""
            if self.pressure < 0.3:
                return "prosperity", "🌟 繁荣期"
            elif self.pressure < 0.7:
                return "normal", "⚖️ 平衡期"
            else:
                return "crisis", "🔥 危机期"
        
        def adjust_reproduction_config(self, config):
            """根据压力调整繁殖配置"""
            adjusted = config.copy()
            
            if self.pressure < 0.3:  # 繁荣期 - 鼓励繁殖
                adjusted['min_roi'] *= 0.7
                adjusted['min_trades'] = max(1, adjusted['min_trades'] - 1)
                adjusted['pool_subsidy_ratio'] = adjusted.get('pool_subsidy_ratio', 0.30) * 1.5
            elif self.pressure > 0.7:  # 危机期 - 抑制繁殖
                adjusted['min_roi'] *= 1.3
                adjusted['min_trades'] += 1
                adjusted['pool_subsidy_ratio'] = adjusted.get('pool_subsidy_ratio', 0.30) * 0.5
            
            return adjusted
        
        def adjust_death_config(self, config):
            """根据压力调整死亡配置"""
            adjusted = config.copy()
            
            if self.pressure < 0.3:  # 繁荣期 - 宽松淘汰
                adjusted['death_roi_threshold'] *= 1.2  # -35% → -42%
                adjusted['parent_protection_period'] = adjusted.get('parent_protection_period', 3) + 2
                adjusted['elite_roi_threshold'] *= 0.8   # 20% → 16%
            elif self.pressure > 0.7:  # 危机期 - 严格淘汰
                adjusted['death_roi_threshold'] *= 0.8  # -35% → -28%
                adjusted['parent_protection_period'] = max(1, adjusted.get('parent_protection_period', 3) - 1)
                adjusted['elite_roi_threshold'] *= 1.2  # 20% → 24%
                adjusted['crisis_mode'] = True
            
            return adjusted

class SimpleAgent:
    """简化版的Agent类（优化版）"""
    def __init__(self, agent_id, gene, initial_capital, strategy):
        self.id = agent_id
        self.gene = gene
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.strategy = strategy
        self.is_alive = True
        self.death_reason = None
        self.roi = 0
        self.trade_count = 0
        self.age = 0
        self.long_ratio = 0
        self.short_ratio = 0
        self.roi_history = []  # ROI历史记录
        self.children_count = 0  # 繁殖次数
        self.parent_id = None  # 父代ID
        self.last_reproduction_age = 0  # 最后一次繁殖的年龄
    
    def update(self, market_features, price_change):
        # 简化的更新逻辑
        self.age += 1
        # 随机调整资金变化
        capital_change = self.capital * random.uniform(-0.05, 0.05)
        self.capital += capital_change
        self.roi = (self.capital - self.initial_capital) / self.initial_capital
        
        # 记录ROI历史（用于波动率计算）
        self.roi_history.append(self.roi)
        if len(self.roi_history) > 20:  # 只保留最近20个
            self.roi_history = self.roi_history[-20:]
        
        # 模拟交易
        if random.random() < 0.3:  # 30%概率执行交易
            self.trade_count += 1
        # 随机调整仓位比例
        self.long_ratio = random.uniform(0, 1)
        self.short_ratio = random.uniform(0, 1 - self.long_ratio)
    
    def should_die(self, death_config, all_agents=None):
        """
        多维度死亡判断机制
        
        Args:
            death_config: 死亡配置
            all_agents: 所有Agent列表（用于相对排名）
            
        Returns:
            bool: 是否应该死亡
        """
        # === 1. 绝对ROI淘汰（基础保护）===
        absolute_threshold = death_config.get('death_roi_threshold', -0.35)  # 提高到-35%
        if self.roi < absolute_threshold:
            self.death_reason = f"ROI低于绝对阈值: {self.roi:.2%} < {absolute_threshold:.2%}"
            return True
        
        # === 2. 年龄保护（新Agent免死金牌）===
        min_age = death_config.get('min_age_for_death', 3)
        if self.age < min_age:
            return False  # 太年轻，给机会成长
        
        # === 2.5. 父代保护（繁殖后保护期）===
        parent_protection_period = death_config.get('parent_protection_period', 3)
        if hasattr(self, 'last_reproduction_age') and self.last_reproduction_age > 0:
            cycles_since_reproduction = self.age - self.last_reproduction_age
            if cycles_since_reproduction < parent_protection_period:
                return False  # 繁殖后保护期内，免于淘汰
        
        # === 3. 相对排名淘汰（进化核心）===
        if all_agents and len(all_agents) > 5:
            # 计算相对排名
            alive_agents = [a for a in all_agents if a.is_alive]
            if len(alive_agents) > 5:
                # === 3.1. 精英特权（ROI>20%免除相对淘汰）===
                elite_threshold = death_config.get('elite_roi_threshold', 0.20)
                if self.roi > elite_threshold:
                    return False  # 精英免于相对排名淘汰
                
                # 按ROI排序
                sorted_agents = sorted(alive_agents, key=lambda x: x.roi, reverse=True)
                my_rank = sorted_agents.index(self) + 1
                
                # 淘汰后20%且ROI为负的Agent
                bottom_threshold = int(len(alive_agents) * 0.8)
                if my_rank > bottom_threshold and self.roi < -0.10:
                    self.death_reason = f"相对排名淘汰: 第{my_rank}/{len(alive_agents)}名, ROI={self.roi:.2%}"
                    return True
        
        # === 4. 长期低效淘汰 ===
        max_age = death_config.get('max_age_low_performance', 20)
        if self.age > max_age and self.roi < 0:
            self.death_reason = f"长期低效: 年龄{self.age}周期, ROI={self.roi:.2%}"
            return True
        
        # === 5. 极度波动淘汰（风险过高）===
        if hasattr(self, 'roi_history') and len(self.roi_history) > 5:
            import numpy as np
            roi_std = np.std(self.roi_history)
            if roi_std > 0.5 and self.roi < 0:  # 波动率>50%且亏损
                self.death_reason = f"波动过大且亏损: std={roi_std:.2%}, ROI={self.roi:.2%}"
                return True
        
        return False
    
    def die(self, capital_pool=None, recovery_rate=1.0):
        """
        Agent死亡处理
        
        Args:
            capital_pool: 资金池对象
            recovery_rate: 资金回收率（默认100%）
        """
        self.is_alive = False
        
        # 资金回收到资金池
        if capital_pool is not None and self.capital > 0:
            recycled = capital_pool.recycle_from_death(self.capital, recovery_rate)
            self.final_capital = self.capital
            self.capital = 0  # 资金已转移
            return recycled
        
        return 0
    
    def can_reproduce(self, reproduction_config):
        """
        判断是否可以繁殖
        
        Args:
            reproduction_config: 繁殖配置
            
        Returns:
            bool: 是否可以繁殖
        """
        if not self.is_alive:
            return False
        
        # === 1. 最低ROI要求 ===
        min_roi = reproduction_config.get('min_roi', 0.10)  # 默认10%
        if self.roi < min_roi:
            return False
        
        # === 2. 最低交易次数 ===
        min_trades = reproduction_config.get('min_trades', 5)
        if self.trade_count < min_trades:
            return False
        
        # === 3. 最低年龄 ===
        min_age = reproduction_config.get('min_age', 3)
        if self.age < min_age:
            return False
        
        # === 4. 繁殖冷却期 ===
        max_children = reproduction_config.get('max_children', 3)
        if self.children_count >= max_children:
            return False
        
        return True
    
    def reproduce(self, new_agent_id, reproduction_config, capital_pool=None):
        """
        繁殖新Agent（增强版：资金池资助）
        
        Args:
            new_agent_id: 新Agent的ID
            reproduction_config: 繁殖配置
            capital_pool: 资金池对象
            
        Returns:
            新的Agent实例
        """
        # 变异基因
        new_gene = self._mutate_gene(reproduction_config.get('mutation_rate', 0.15))
        
        # 1. 父代转移资金（降低到20%）
        parent_transfer_ratio = reproduction_config.get('parent_transfer_ratio', 0.20)
        parent_transfer = self.capital * parent_transfer_ratio
        
        # 2. 资金池资助（30%初始资金）
        pool_subsidy = 0
        if capital_pool is not None:
            pool_subsidy_ratio = reproduction_config.get('pool_subsidy_ratio', 0.30)
            requested_subsidy = self.initial_capital * pool_subsidy_ratio
            pool_subsidy = capital_pool.subsidize_reproduction(requested_subsidy)
        
        # 3. 子代总资金
        new_capital = parent_transfer + pool_subsidy
        
        # 4. 繁殖成本（父代支付）
        reproduction_cost = reproduction_config.get('reproduction_cost', 0.05)
        cost = self.capital * reproduction_cost
        
        # 从父代扣除资金
        self.capital -= (parent_transfer + cost)
        self.children_count += 1
        self.last_reproduction_age = self.age  # 记录繁殖年龄
        
        # 创建新Agent
        new_agent = SimpleAgent(
            agent_id=new_agent_id,
            gene=new_gene,
            initial_capital=new_capital,
            strategy=SimpleStrategy(new_gene, self.strategy.config)
        )
        new_agent.parent_id = self.id
        
        return new_agent
    
    def _mutate_gene(self, mutation_rate=0.15):
        """
        基因变异
        
        Args:
            mutation_rate: 变异率（0-1）
            
        Returns:
            变异后的新基因
        """
        new_gene = SimpleGene()
        
        # 继承父代基因，然后变异
        for feature, value in self.gene.preferences.items():
            if random.random() < mutation_rate:
                # 变异：高斯噪音
                mutation = random.gauss(0, 0.2)  # 标准差20%
                new_value = value + mutation
                # 限制在[0, 1]范围
                new_value = max(0.0, min(1.0, new_value))
                new_gene.preferences[feature] = new_value
            else:
                # 不变异，直接继承
                new_gene.preferences[feature] = value
        
        # 继承策略类型（有10%概率改变）
        if hasattr(self.gene, 'strategy_type'):
            if random.random() < 0.1:
                # 10%概率改变策略类型
                strategy_types = ['aggressive_bull', 'defensive_bull', 'aggressive_bear', 
                                'defensive_bear', 'volatility_hunter', 'trend_follower', 
                                'mean_reversion', 'balanced']
                new_gene.strategy_type = random.choice(strategy_types)
            else:
                new_gene.strategy_type = self.gene.strategy_type
        
        return new_gene

# 配置日志
log_dir = os.path.join(project_path, 'test_logs')
os.makedirs(log_dir, exist_ok=True)
log_filename = os.path.join(log_dir, f'trading_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

# 配置日志，确保使用UTF-8编码
file_handler = logging.FileHandler(log_filename, encoding='utf-8')
stream_handler = logging.StreamHandler()

# 设置日志级别为DEBUG，以便查看更多调试信息
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[file_handler, stream_handler]
)

logger = logging.getLogger('trading_test')

class TradingTest:
    def __init__(self, skip_position_check=False, use_real_data=True):
        """
        初始化交易测试
        
        Args:
            skip_position_check: 是否跳过持仓检查
            use_real_data: 是否使用真实OKX市场数据（默认True）
        """
        # 添加跳过持仓检查的选项
        self.skip_position_check = skip_position_check
        # 是否使用真实市场数据
        self.use_real_data = use_real_data
        
        # 使用从config.py导入的配置
        self.okx_config = CONFIG['okx_api'].copy()
        # 确保使用模拟盘
        self.okx_config['flag'] = 1
        
        # 如果配置中没有设置API密钥，则使用测试密钥
        if not self.okx_config['api_key']:
            self.okx_config.update({
                'api_key': "265a4c37-1dc1-40d8-80d0-11004026ca48",
                'secret_key': "0AD30E01A7B66FBBBEB7E30D8E0E18B4",
                'passphrase': "Garylauchina3.14"
            })
        
        self.adapter = None
        self.agents = []
        # 使用增强的资金池系统
        self.capital_pool = EnhancedCapitalPool(CONFIG['initial_capital'])
        # 不需要market对象，因为我们将使用模拟数据
        self.strategy_config = CONFIG['agent_manager']['strategy'].copy()
        
        # 环境压力系统
        self.environmental_pressure = EnvironmentalPressure()
        
        # 进化统计
        self.evolution_stats = {
            'total_births': 0,      # 总出生数
            'total_deaths': 0,      # 总死亡数
            'total_reproductions': 0,  # 总繁殖次数
            'generation_count': 0,  # 代数
            'best_roi_ever': -1.0,  # 历史最佳ROI
            'strategy_lineage': [],  # 策略谱系
            'pressure_history': []   # 压力历史
        }
    
    def connect_to_okx(self):
        """连接到OKX模拟盘"""
        logger.info("正在连接到OKX模拟盘...")
        try:
            self.adapter = OKXTradingAdapter(self.okx_config)
            logger.info("[OK] 成功连接到OKX模拟盘")
            return True
        except Exception as e:
            logger.error(f"❌ 连接OKX失败: {e}")
            return False
    
    def close_all_positions(self, max_attempts=3):
        """
        关闭所有当前持仓
        
        Args:
            max_attempts: 最大尝试次数
            
        Returns:
            成功平仓的持仓数量
        """
        logger.info("====== 开始平仓操作 ======")
        
        # 记录本次尝试的次数
        current_attempt = 1
        total_closed_positions = 0
        
        while current_attempt <= max_attempts:
            logger.info(f"====== 平仓尝试 {current_attempt}/{max_attempts} ======")
            logger.info("正在获取当前持仓...")
            try:
                # 修复：添加更强大的错误处理和重试机制
                positions = self.adapter.get_positions()
                
                # 处理不同的返回格式
                positions_to_close = []
                
                # 记录原始positions数据以便调试
                logger.info(f"原始持仓数据类型: {type(positions)}, 内容: {positions}")
                
                # 首先验证positions是否为有效数据
                if positions is None or (isinstance(positions, dict) and len(positions) == 0) or (isinstance(positions, list) and len(positions) == 0):
                    logger.info("未获取到持仓数据或持仓为空，继续执行测试")
                    return 0
                
                # 处理不同的返回格式并严格验证是否有实际持仓
                if isinstance(positions, dict):
                    for symbol, pos in positions.items():
                        # 记录原始持仓数据用于调试
                        logger.info(f"检查持仓 {symbol}: {pos}")
                        # 检查是否有实际持仓量，使用更严格的判断
                        try:
                            size_values = []
                            # 检查多种可能的字段名称
                            for key in ['size', 'pos', 'availPos', 'available', 'notional', 'notionalUsd']:
                                if key in pos and pos[key]:
                                    # 尝试转换为浮点数
                                    size = float(pos[key])
                                    if size > 0.000001:  # 设置一个极小值阈值，避免因精度问题误判
                                        size_values.append(size)
                            # 只有当有明显大于0的持仓量时才加入平仓列表
                            if size_values:
                                logger.info(f"发现有效持仓 {symbol}: {max(size_values)}")
                                positions_to_close.append((symbol, pos))
                            else:
                                logger.info(f"持仓 {symbol} 的持仓量为0或极小，无需平仓")
                        except (ValueError, TypeError) as e:
                            logger.info(f"持仓 {symbol} 的数据格式异常，跳过: {e}")
                            continue
                elif isinstance(positions, list):
                    for pos in positions:
                        if isinstance(pos, dict):
                            # 记录原始持仓数据用于调试
                            logger.info(f"检查持仓项: {pos}")
                            # 适配不同的字段名称
                            symbol_key = 'instId' if 'instId' in pos else 'symbol' if 'symbol' in pos else None
                            if symbol_key and pos.get(symbol_key):
                                try:
                                    # 检查是否有实际持仓量，使用更严格的判断
                                    size_values = []
                                    for key in ['size', 'pos', 'availPos', 'available', 'notional', 'notionalUsd']:
                                        if key in pos and pos[key]:
                                            size = float(pos[key])
                                            if size > 0.000001:  # 设置一个极小值阈值
                                                size_values.append(size)
                                    # 只有当有明显大于0的持仓量时才加入平仓列表
                                    if size_values:
                                        symbol = pos[symbol_key]
                                        logger.info(f"发现有效持仓 {symbol}: {max(size_values)}")
                                        positions_to_close.append((symbol, pos))
                                    else:
                                        logger.info(f"持仓项 {pos.get(symbol_key)} 的持仓量为0或极小，无需平仓")
                                except (ValueError, TypeError) as e:
                                    logger.info(f"持仓项数据格式异常，跳过: {e}")
                                    continue
                        else:
                            logger.info(f"非字典类型的持仓项: {pos}")
                
                # 再次验证实际有持仓的数量
                logger.info(f"找到 {len(positions_to_close)} 个有效持仓需要平仓")
                
                # 如果没有实际持仓，直接返回
                if len(positions_to_close) == 0:
                    logger.info("没有发现需要平仓的有效持仓，继续执行测试")
                    return 0
                
                closed_positions = 0
                for symbol, pos in positions_to_close:
                    try:
                        # 更全面地获取持仓信息
                        size = float(pos.get('size', pos.get('pos', pos.get('availPos', pos.get('available', 0)))))  
                        side = pos.get('side', pos.get('posSide', pos.get('direction', ''))).lower()
                        
                        if size <= 0 or not side:
                            logger.warning(f"持仓信息不完整: {symbol}, size={size}, side={side}")
                            continue
                        
                        logger.info(f"准备平掉持仓: {symbol}, 方向: {side}, 数量: {size}")
                        logger.info(f"持仓详细信息: {pos}")
                        
                        # 确定平仓方向和持仓方向
                        # 重要：OKX合约平仓时，side是交易方向，posSide是要平的仓位方向
                        # 平多仓：side='sell', posSide='long'
                        # 平空仓：side='buy', posSide='short'
                        close_side = 'buy' if side == 'short' else 'sell'
                        pos_side = side  # 保持原持仓方向
                        logger.info(f"平仓参数: side={close_side}, posSide={pos_side}")
                        
                        # 下单平仓 - 增加重试逻辑，先尝试市价单，失败后尝试限价单
                        max_retries = 3
                        retry_count = 0
                        order_success = False
                        order_type = 'market'  # 先尝试市价单
                        
                        while retry_count < max_retries and not order_success:
                            retry_count += 1
                            try:
                                # 如果市价单尝试2次都失败，改用限价单
                                if retry_count > 2:
                                    order_type = 'limit'
                                    try:
                                        # 获取当前市场价格
                                        current_price = self.adapter.get_current_price(symbol)
                                        # 设置有利的价格以确保成交：平多用稍低价格，平空用稍高价格
                                        if close_side == 'sell':  # 平多仓
                                            price = current_price * 0.998  # 比市价低0.2%
                                        else:  # 平空仓
                                            price = current_price * 1.002  # 比市价高0.2%
                                        logger.info(f"切换到限价单，使用价格: {price}")
                                    except Exception as price_e:
                                        logger.error(f"获取市场价格失败: {price_e}，继续使用市价单")
                                        order_type = 'market'
                                
                                order_request = {
                                    'market': 'futures',
                                    'symbol': symbol,
                                    'side': close_side,
                                    'pos_side': pos_side,  # 明确指定要平的仓位方向
                                    'order_type': order_type,
                                    'size': size
                                }
                                
                                # 如果是限价单，添加价格
                                if order_type == 'limit':
                                    order_request['price'] = price
                                
                                logger.info(f"订单请求: {order_request}")
                                
                                order = self.adapter.place_order(order_request)
                                logger.info(f"[OK] 平仓订单已提交 (尝试 {retry_count}/{max_retries}): {order.order_id}")
                                
                                # 等待订单完成
                                time.sleep(3)  # 增加等待时间
                                
                                # 修复：更灵活的订单状态检查
                                try:
                                    order_status = self.adapter.get_order_status(order.order_id, symbol)
                                    # 检查多种可能的订单状态格式
                                    status = getattr(order_status, 'status', None)
                                    if not status and isinstance(order_status, dict):
                                        status = order_status.get('status', order_status.get('ordStatus', None))
                                            
                                    if status in ['filled', 'filled_completely', 'filled_partially']:
                                        closed_positions += 1
                                        logger.info(f"[OK] {symbol} 持仓已完全平仓")
                                        order_success = True
                                    else:
                                        logger.warning(f"⚠️ {symbol} 平仓订单未完全成交: {status or 'unknown'}")
                                except Exception as status_e:
                                    logger.warning(f"检查订单状态时出错: {status_e}，尝试直接查询持仓")
                                    # 尝试直接重新查询持仓，检查是否已平仓
                                    new_positions = self.adapter.get_positions()
                                    if isinstance(new_positions, dict) and symbol not in new_positions:
                                        closed_positions += 1
                                        logger.info(f"[OK] {symbol} 持仓似乎已平仓 (通过重新查询确认)")
                                        order_success = True
                                    elif isinstance(new_positions, list):
                                        if not any(p.get('instId') == symbol or p.get('symbol') == symbol for p in new_positions):
                                            closed_positions += 1
                                            logger.info(f"[OK] {symbol} 持仓似乎已平仓 (通过重新查询确认)")
                                            order_success = True
                            except Exception as order_e:
                                logger.error(f"❌ 平仓订单提交失败 (尝试 {retry_count}/{max_retries}): {order_e}")
                                if retry_count < max_retries:
                                    logger.info(f"将在 2 秒后重试...")
                                    time.sleep(2)
                                else:
                                    order_success = False
                        
                        if not order_success:
                            logger.error(f"❌ {symbol} 平仓失败，已达到最大重试次数")
                            
                    except Exception as e:
                        logger.error(f"处理持仓 {symbol} 时出错: {e}")
                        continue
            except Exception as e:
                logger.error(f"平仓过程中发生错误: {e}")
                closed_positions = 0
                positions_to_close = []
            
            # 记录本次尝试的结果
            total_closed_positions += closed_positions
            positions_count = len(positions_to_close) if 'positions_to_close' in locals() else 0
            logger.info(f"平仓尝试 {current_attempt}/{max_attempts} 完成，本次成功平仓 {closed_positions}/{positions_count} 个持仓")
            
            # 再次检查是否还有持仓需要平仓
            if 'positions_to_close' in locals() and closed_positions == len(positions_to_close):
                logger.info("✅ 所有持仓已成功平仓！")
                return total_closed_positions
            
            # 如果还有持仓未平仓且未达到最大尝试次数，进行下一轮尝试
            if current_attempt < max_attempts:
                # 等待一段时间后重试
                wait_time = 5  # 5秒等待
                logger.info(f"还有持仓未平仓，{wait_time}秒后进行下一次尝试...")
                time.sleep(wait_time)
                
                # 重新获取持仓信息
                logger.info("重新获取持仓信息...")
                try:
                    positions = self.adapter.get_positions()
                    # 重新处理持仓数据
                    positions_to_close = []
                    if isinstance(positions, dict):
                        for symbol, pos in positions.items():
                            try:
                                size_values = []
                                for key in ['size', 'pos', 'availPos', 'available', 'notional', 'notionalUsd']:
                                    if key in pos and pos[key]:
                                        size = float(pos[key])
                                        if size > 0.000001:
                                            size_values.append(size)
                                if size_values:
                                    logger.info(f"仍有持仓需要平仓: {symbol}: {max(size_values)}")
                                    positions_to_close.append((symbol, pos))
                            except (ValueError, TypeError):
                                continue
                    elif isinstance(positions, list):
                        for pos in positions:
                            if isinstance(pos, dict):
                                symbol_key = 'instId' if 'instId' in pos else 'symbol' if 'symbol' in pos else None
                                if symbol_key and pos.get(symbol_key):
                                    try:
                                        size_values = []
                                        for key in ['size', 'pos', 'availPos', 'available', 'notional', 'notionalUsd']:
                                            if key in pos and pos[key]:
                                                size = float(pos[key])
                                                if size > 0.000001:
                                                    size_values.append(size)
                                        if size_values:
                                            symbol = pos[symbol_key]
                                            logger.info(f"仍有持仓需要平仓: {symbol}: {max(size_values)}")
                                            positions_to_close.append((symbol, pos))
                                    except (ValueError, TypeError):
                                        continue
                except Exception as e:
                    logger.error(f"重新获取持仓信息时出错: {e}")
            
            # 增加尝试次数
            current_attempt += 1
        
        logger.info(f"已达到最大平仓尝试次数，总计成功平仓 {total_closed_positions} 个持仓")
        return total_closed_positions
    
    def generate_initial_agents(self, count=5):
        """创世生成简化版Agent"""
        logger.info(f"正在创世生成 {count} 个Agent...")
        
        self.agents = []
        
        # 优化的资金分配策略（使用增强资金池）
        total_pool_capital = self.capital_pool.initial_capital  # 10,000
        
        # 有繁殖系统时：80%分配给初始Agent，20%留作繁殖资助和死亡回收
        allocation_ratio = 0.80
        purpose = "资金池循环系统，预留20%用于繁殖资助"
        
        agent_allocated_capital = total_pool_capital * allocation_ratio
        initial_capital = agent_allocated_capital / count
        
        # 检查单Agent资金占比（风险控制）
        single_agent_ratio = initial_capital / total_pool_capital
        if single_agent_ratio > 0.15:  # 单个Agent不应超过总资金15%
            logger.warning(f"⚠️ 单Agent资金占比过高: {single_agent_ratio:.1%}，建议增加Agent数量")
        
        logger.info(f"💰 资金分配策略: {purpose}")
        logger.info(f"📊 分配比例: Agent {allocation_ratio:.0%} vs 资金池 {1-allocation_ratio:.0%}")
        logger.info(f"💵 Agent初始资金: ${initial_capital:.2f}/个 (占总资金 {single_agent_ratio:.1%})")
        
        # 记录资金池状态
        pool_status = self.capital_pool.get_status()
        logger.info(f"🏦 资金池可用: ${pool_status['available']:.2f}")
        
        print(f"\n{'='*70}")
        print(f"🧬 开始创世生成 {count} 个Agent")
        print(f"{'='*70}\n")
        
        for i in range(count):
            try:
                # 生成随机基因（使用我们的简化版Gene类）
                gene = SimpleGene.random()
                
                # 创建策略（使用我们的简化版Strategy类）
                strategy = SimpleStrategy(gene, self.strategy_config)
                
                # 创建Agent（使用我们的简化版Agent类）
                agent = SimpleAgent(
                    agent_id=i + 1,
                    gene=gene,
                    initial_capital=initial_capital,
                    strategy=strategy
                )
                
                # 从资金池分配资金
                if self.capital_pool.allocate_to_agent(initial_capital):
                    self.agents.append(agent)
                else:
                    logger.error(f"资金池资金不足，无法创建Agent {i+1}")
                    break
                
                # === 建议2: 分析并显示Agent基因特征 ===
                species_name = agent.gene.generate_species_name()
                top_preferences = agent.gene.get_top_preferences(3)
                
                print(f"✅ Agent {agent.id} 创建成功")
                print(f"   🧬 物种名称: {species_name}")
                print(f"   💰 初始资金: ${initial_capital:.2f}")
                print(f"   🎯 基因特征分析:")
                
                for j, (feature, preference) in enumerate(top_preferences, 1):
                    # 根据特征类型添加表情
                    if 'bull' in feature:
                        emoji = "🐂"
                    elif 'bear' in feature:
                        emoji = "🐻"
                    elif 'fear' in feature:
                        emoji = "😨"
                    elif 'greed' in feature:
                        emoji = "🤑"
                    elif 'vol' in feature:
                        emoji = "📊"
                    elif 'breakout' in feature:
                        emoji = "🚀"
                    elif 'breakdown' in feature:
                        emoji = "📉"
                    else:
                        emoji = "🔹"
                    
                    print(f"      {j}. {emoji} {feature}: {preference:.3f}")
                
                # 判断Agent的交易风格
                bull_prefs = sum(v for k, v in gene.preferences.items() if 'bull' in k)
                bear_prefs = sum(v for k, v in gene.preferences.items() if 'bear' in k)
                
                if bull_prefs > bear_prefs * 1.5:
                    trading_style = "激进多头型 🚀"
                elif bear_prefs > bull_prefs * 1.5:
                    trading_style = "防守空头型 🛡️"
                elif abs(bull_prefs - bear_prefs) < 0.3:
                    trading_style = "平衡对冲型 ⚖️"
                else:
                    trading_style = "灵活机动型 🎯"
                
                print(f"   📊 交易风格: {trading_style}")
                print(f"   {'─'*60}\n")
                
                logger.info(f"Agent {agent.id} 创建成功: {species_name}, 风格: {trading_style}")
                
            except Exception as e:
                logger.error(f"❌ 创建Agent {i+1} 失败: {e}")
        
        # 更新进化统计
        self.evolution_stats['total_births'] = len(self.agents)
        self.evolution_stats['generation_count'] = 0  # 第0代
        
        print(f"{'='*70}")
        print(f"🎉 创世生成完成，成功创建 {len(self.agents)} 个Agent")
        print(f"{'='*70}\n")
        
        logger.info(f"创世生成完成，成功创建 {len(self.agents)} 个Agent")
        return len(self.agents)
    
    def run_trading_test(self, duration_minutes=30):
        """运行交易测试"""
        logger.info(f"开始 {duration_minutes} 分钟的交易测试...")
        
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        test_start_time = datetime.now()
        
        # 记录测试信息
        test_info = {
            'start_time': test_start_time.isoformat(),
            'duration_minutes': duration_minutes,
            'initial_agents_count': len(self.agents),
            'initial_capital_per_agent': [agent.initial_capital for agent in self.agents]
        }
        logger.info(f"测试配置: {json.dumps(test_info, indent=2)}")
        
        # 主循环
        cycle_count = 0
        while datetime.now() < end_time:
            cycle_count += 1
            current_time = datetime.now()
            elapsed = (current_time - test_start_time).total_seconds() / 60
            remaining = (end_time - current_time).total_seconds() / 60
            
            # 使用更醒目的交易周期标识
            cycle_header = f"\n======= 交易周期 {cycle_count} ======= (已运行 {elapsed:.1f} 分钟, 剩余 {remaining:.1f} 分钟) ======="
            print(cycle_header)  # 同时输出到控制台，确保用户能看到
            logger.info(cycle_header)
            
            try:
                # 获取市场数据（使用真实数据或模拟数据）
                market_features = self._get_current_market_features(use_real_data=self.use_real_data)
                
                # === 建议1: 实时显示交易指数、市场趋势、结论 ===
                # 计算交易指数 final_signal_trading
                # 方案1: 简单版（当前）
                simple_signal = market_features['bull'] - market_features['bear']
                
                # 方案2: 加权综合版（更准确）
                trend_component = (market_features['bull'] - market_features['bear']) * 0.5
                strength_component = (market_features['strong_bull'] - market_features['strong_bear']) * 0.2
                sentiment_component = (market_features.get('greed', 0) - market_features.get('fear', 0)) * 0.15
                pattern_component = (market_features.get('breakout', 0) - market_features.get('breakdown', 0)) * 0.15
                
                # 波动率抑制因子
                volatility_factor = 1.0 - market_features.get('extreme_high_vol', 0) * 0.3
                
                # 综合信号
                comprehensive_signal = (
                    trend_component + 
                    strength_component + 
                    sentiment_component + 
                    pattern_component
                ) * volatility_factor
                
                # 使用综合信号（可切换）
                use_comprehensive = True  # 设为False使用简单信号
                final_signal_trading = comprehensive_signal if use_comprehensive else simple_signal
                
                # 判断市场结论
                if final_signal_trading > 0.3:
                    market_conclusion = "🟢 强烈偏多市场"
                    conclusion_color = "\033[92m"  # 绿色
                elif final_signal_trading > 0.1:
                    market_conclusion = "🟢 偏多市场"
                    conclusion_color = "\033[92m"
                elif final_signal_trading > -0.1:
                    market_conclusion = "🟡 震荡市场"
                    conclusion_color = "\033[93m"  # 黄色
                elif final_signal_trading > -0.3:
                    market_conclusion = "🔴 偏空市场"
                    conclusion_color = "\033[91m"  # 红色
                else:
                    market_conclusion = "🔴 强烈偏空市场"
                    conclusion_color = "\033[91m"
                
                reset_color = "\033[0m"
                
                # 输出交易指数和市场结论（带颜色）
                print(f"\n{'='*60}")
                print(f"📊 交易指数: {conclusion_color}{final_signal_trading:+.4f}{reset_color}")
                print(f"📈 Bull力量: {market_features['bull']:.3f} | Bear力量: {market_features['bear']:.3f}")
                print(f"💡 市场结论: {conclusion_color}{market_conclusion}{reset_color}")
                print(f"{'='*60}\n")
                
                # 记录到日志
                logger.info(f"交易指数: {final_signal_trading:.4f}")
                logger.info(f"Bull力量: {market_features['bull']:.3f}, Bear力量: {market_features['bear']:.3f}")
                logger.info(f"市场结论: {market_conclusion}")
                
                # 计算并显示详细趋势值
                trend_values = {
                    'strong_bull': market_features['strong_bull'],
                    'bull': market_features['bull'],
                    'weak_bull': market_features['weak_bull'],
                    'sideways': market_features['sideways'],
                    'weak_bear': market_features['weak_bear'],
                    'bear': market_features['bear'],
                    'strong_bear': market_features['strong_bear']
                }
                
                # 构建趋势值显示信息
                trend_info = "📉 市场趋势详情: " + ", ".join([f"{k}={v:.3f}" for k, v in trend_values.items()])
                print(trend_info)
                logger.info(trend_info)
                
                # === 建议3: 显示Agent交易行为和判断逻辑 ===
                print(f"\n{'─'*60}")
                print(f"👥 Agent交易决策")
                print(f"{'─'*60}")
                
                # 更新所有Agent
                for agent in self.agents:
                    if agent.is_alive:
                        # 模拟价格变化率 (-0.02 到 +0.02)
                        price_change = random.uniform(-0.02, 0.02)
                        
                        # 记录更新前的状态
                        old_capital = agent.capital
                        old_roi = agent.roi
                        
                        # 更新Agent状态
                        agent.update(market_features, price_change)
                        
                        # 计算本周期盈亏
                        capital_change = agent.capital - old_capital
                        
                        # 检查是否需要死亡（优化的多维度判断）
                        death_config = {
                            'death_roi_threshold': -0.35,     # 提高阈值到-35%
                            'min_age_for_death': 3,           # 至少存活3个周期
                            'max_age_low_performance': 20,    # 长期低效淘汰
                            'parent_protection_period': 3,    # 父代繁殖后保护3周期
                            'elite_roi_threshold': 0.20       # 精英特权阈值（ROI>20%免淘汰）
                        }
                        if agent.should_die(death_config, self.agents):
                            recycled = agent.die(self.capital_pool, recovery_rate=1.0)
                            self.evolution_stats['total_deaths'] += 1  # 统计死亡
                            print(f"\n💀 Agent {agent.id} 死亡: {agent.death_reason}")
                            print(f"   💰 回收资金: ${recycled:.2f}")
                            logger.warning(f"Agent {agent.id} 死亡: {agent.death_reason}, 回收${recycled:.2f}")
                        else:
                            # 判断Agent对市场的看法（基于基因偏好）
                            bull_preference = agent.gene.preferences.get('bull', 0)
                            bear_preference = agent.gene.preferences.get('bear', 0)
                            
                            # Agent的市场判断
                            agent_signal = (market_features['bull'] * bull_preference - 
                                          market_features['bear'] * bear_preference)
                            
                            # 判断逻辑分析
                            if agent_signal > 0.2:
                                agent_view = "🟢 看多"
                            elif agent_signal > 0:
                                agent_view = "🟢 偏多"
                            elif agent_signal > -0.2:
                                agent_view = "🟡 观望"
                            else:
                                agent_view = "🔴 看空"
                            
                            # 显示Agent的实际交易决策
                            if agent.long_ratio > 0 and agent.short_ratio == 0:
                                action_desc = f"做多 {agent.long_ratio:.2%} 仓位"
                                action_emoji = "📈"
                            elif agent.short_ratio > 0 and agent.long_ratio == 0:
                                action_desc = f"做空 {agent.short_ratio:.2%} 仓位"
                                action_emoji = "📉"
                            elif agent.long_ratio > 0 and agent.short_ratio > 0:
                                action_desc = f"对冲 - 多: {agent.long_ratio:.2%}, 空: {agent.short_ratio:.2%}"
                                action_emoji = "⚖️"
                            else:
                                action_desc = "空仓观望"
                                action_emoji = "💤"
                            
                            # 盈亏显示
                            if capital_change > 0:
                                pnl_display = f"+${capital_change:.2f}"
                                pnl_emoji = "💰"
                            elif capital_change < 0:
                                pnl_display = f"-${abs(capital_change):.2f}"
                                pnl_emoji = "📉"
                            else:
                                pnl_display = "$0.00"
                                pnl_emoji = "➖"
                            
                            # ROI颜色
                            if agent.roi > 0.05:
                                roi_color = "\033[92m"  # 绿色
                            elif agent.roi < -0.05:
                                roi_color = "\033[91m"  # 红色
                            else:
                                roi_color = "\033[93m"  # 黄色
                            reset_color = "\033[0m"
                            
                            print(f"\n🤖 Agent {agent.id}:")
                            print(f"   💭 市场判断: {agent_view} (信号: {agent_signal:+.3f})")
                            print(f"   {action_emoji} 交易决策: {action_desc}")
                            print(f"   💼 资金状况: ${agent.capital:.2f} (ROI: {roi_color}{agent.roi:+.2%}{reset_color})")
                            print(f"   {pnl_emoji} 本周期盈亏: {pnl_display}")
                            
                            # 判断逻辑解释
                            reasons = []
                            if bull_preference > 0.7 and market_features['bull'] > 0.5:
                                reasons.append("基因偏好多头且市场看涨")
                            if bear_preference > 0.7 and market_features['bear'] > 0.5:
                                reasons.append("基因偏好空头且市场看跌")
                            if agent.long_ratio > 0.5:
                                reasons.append(f"多头信心{agent.long_ratio:.0%}")
                            if agent.short_ratio > 0.5:
                                reasons.append(f"空头信心{agent.short_ratio:.0%}")
                            
                            if reasons:
                                print(f"   🧠 判断依据: {', '.join(reasons)}")
                            
                            logger.info(f"Agent {agent.id} - {agent_view}, {action_desc}, 资金: ${agent.capital:.2f}, ROI: {agent.roi:+.2%}")
                
                print(f"\n{'─'*60}\n")
                
                # 记录总体统计（仅记录到日志，不输出到控制台）
                alive_agents_list = [agent for agent in self.agents if agent.is_alive]
                alive_count = len(alive_agents_list)
                total_capital = sum(agent.capital for agent in self.agents)
                logger.info(f"当前统计 - 存活Agent: {alive_count}, 总资金: ${total_capital:.2f}")
                
                # === 进化机制：每5个周期执行一次繁殖和淘汰 ===
                if cycle_count % 5 == 0 and alive_count > 0:
                    logger.info("\n🧬 ===== 开始进化周期 =====")
                    print(f"\n{'='*70}")
                    print(f"🧬 进化周期 {cycle_count // 5} - 自然选择与繁殖")
                    print(f"{'='*70}\n")
                    
                    # === 更新环境压力 ===
                    pool_status = self.capital_pool.get_status()
                    current_pressure = self.environmental_pressure.update(
                        market_features, 
                        self.agents,
                        pool_status
                    )
                    pressure_phase, pressure_name = self.environmental_pressure.get_phase()
                    self.evolution_stats['pressure_history'].append(current_pressure)
                    
                    print(f"🌡️ 环境压力: {current_pressure:.2%} - {pressure_name}")
                    print(f"💰 资金池状态: 可用${pool_status['available']:.2f} | "
                          f"已分配${pool_status['allocated']:.2f} | "
                          f"利用率{pool_status['utilization']:.1%}")
                    print(f"♻️ 累计回收${pool_status['recycled']:.2f} | "
                          f"累计资助${pool_status['subsidized']:.2f}\n")
                    
                    logger.info(f"环境压力: {current_pressure:.2%}, 阶段: {pressure_name}")
                    logger.info(f"资金池: {pool_status}")
                    
                    # 动态参数调整（基于测试进度）
                    test_progress = elapsed / duration_minutes  # 0.0 到 1.0
                    
                    # 根据进度动态调整参数（优化版）
                    if test_progress < 0.33:  # 探索期（前1/3）
                        phase = "探索期"
                        min_roi_req = 0.05  # 降低到5%（原6%）
                        mutation_rate = 0.20
                    elif test_progress < 0.67:  # 优化期（中1/3）
                        phase = "优化期"
                        min_roi_req = 0.07  # 降低到7%（原8%）
                        mutation_rate = 0.15
                    else:  # 精英期（后1/3）
                        phase = "精英期"
                        min_roi_req = 0.09  # 降低到9%（原10%）
                        mutation_rate = 0.10
                    
                    print(f"📍 当前阶段: {phase} ({test_progress:.1%} 完成)")
                    print(f"🎯 繁殖要求: ROI > {min_roi_req:.0%}, 变异率: {mutation_rate:.0%}\n")
                    
                    # 繁殖配置（优化版 + 资金池资助）
                    reproduction_config = {
                        'min_roi': min_roi_req,           # 动态ROI要求
                        'min_trades': 2,                  # 降低到2次（原3次）
                        'min_age': 3,                     # 最少3个周期
                        'max_children': 2,                # 最多繁殖2次
                        'mutation_rate': mutation_rate,   # 动态变异率
                        'parent_transfer_ratio': 0.20,    # 父代转移20%（降低负担）
                        'pool_subsidy_ratio': 0.30,       # 资金池资助30%初始资金
                        'reproduction_cost': 0.05         # 5%繁殖成本
                    }
                    
                    # === 根据环境压力调整配置 ===
                    reproduction_config = self.environmental_pressure.adjust_reproduction_config(reproduction_config)
                    death_config = self.environmental_pressure.adjust_death_config(death_config)
                    
                    # 检查可繁殖的Agent
                    eligible_agents = [a for a in alive_agents_list if a.can_reproduce(reproduction_config)]
                    
                    if eligible_agents:
                        # 按ROI排序，优先让表现最好的繁殖
                        eligible_agents.sort(key=lambda x: x.roi, reverse=True)
                        
                        # === 多样性保护：确保不同策略类型都有机会 ===
                        # 统计当前策略类型分布
                        strategy_distribution = {}
                        for agent in alive_agents_list:
                            stype = getattr(agent.gene, 'strategy_type', 'unknown')
                            strategy_distribution[stype] = strategy_distribution.get(stype, 0) + 1
                        
                        # 优先让稀缺策略繁殖（即使ROI不是最高）
                        rare_strategies = [s for s, count in strategy_distribution.items() if count <= 2]
                        if rare_strategies:
                            for agent in eligible_agents:
                                if getattr(agent.gene, 'strategy_type', None) in rare_strategies:
                                    # 稀缺策略加分（提升到列表前部）
                                    eligible_agents.remove(agent)
                                    eligible_agents.insert(0, agent)
                                    logger.info(f"🌟 稀缺策略保护: Agent {agent.id} ({agent.gene.strategy_type}) 优先繁殖")
                        
                        # 控制繁殖数量（最多繁殖当前数量的20%）
                        max_new_agents = max(1, int(alive_count * 0.2))
                        new_agents_count = min(len(eligible_agents), max_new_agents)
                        
                        print(f"🌟 {len(eligible_agents)} 个Agent符合繁殖条件")
                        print(f"📊 本轮将繁殖 {new_agents_count} 个新Agent\n")
                        
                        # 执行繁殖
                        for i in range(new_agents_count):
                            parent = eligible_agents[i]
                            new_agent_id = len(self.agents) + 1
                            
                            try:
                                child = parent.reproduce(new_agent_id, reproduction_config, self.capital_pool)
                                self.agents.append(child)
                                
                                # 更新进化统计
                                self.evolution_stats['total_births'] += 1
                                self.evolution_stats['total_reproductions'] += 1
                                
                                # 计算资金来源
                                parent_contribution = parent.initial_capital * reproduction_config.get('parent_transfer_ratio', 0.20)
                                pool_contribution = child.initial_capital - parent_contribution
                                
                                print(f"🐣 Agent {child.id} 诞生！")
                                print(f"   👨 父代: Agent {parent.id} (ROI: {parent.roi:+.2%})")
                                print(f"   💰 初始资金: ${child.initial_capital:.2f}")
                                print(f"      ├─ 父代转移: ${parent_contribution:.2f}")
                                print(f"      └─ 资金池资助: ${pool_contribution:.2f}")
                                print(f"   🧬 继承策略: {parent.gene.strategy_type if hasattr(parent.gene, 'strategy_type') else '未知'}")
                                print(f"   🎲 变异率: {reproduction_config['mutation_rate']:.0%}")
                                print(f"   🌳 家族: 第{parent.children_count}代传承\n")
                                
                                logger.info(f"Agent {child.id} 由 Agent {parent.id} 繁殖诞生，"
                                          f"初始资金: ${child.initial_capital:.2f} "
                                          f"(父代${parent_contribution:.2f} + 资金池${pool_contribution:.2f})")
                            except Exception as e:
                                logger.error(f"繁殖失败: {e}")
                        
                        print(f"✅ 繁殖完成！当前Agent总数: {len([a for a in self.agents if a.is_alive])}\n")
                    else:
                        print(f"⚠️ 暂无Agent符合繁殖条件 (需要ROI>{reproduction_config['min_roi']:.0%})\n")
                    
                    logger.info(f"进化周期完成 - 当前存活Agent: {len([a for a in self.agents if a.is_alive])}")
                
            except Exception as e:
                logger.error(f"❌ 交易周期 {cycle_count} 出错: {e}")
            
            # 每30秒执行一次交易周期
            time.sleep(30)
        
        logger.info("\n======= 交易测试完成 =======")
        
        # 生成测试报告
        self._generate_test_report(test_start_time)
        
        return True
    
    def _get_current_market_features(self, use_real_data=True):
        """
        获取当前市场特征
        
        Args:
            use_real_data: 是否使用真实OKX数据（默认True）
        
        Returns:
            市场特征字典
        """
        if use_real_data:
            try:
                logger.info("📡 正在从OKX获取真实市场数据...")
                return self._get_real_market_features()
            except Exception as e:
                logger.warning(f"⚠️ 获取真实数据失败: {e}，降级为模拟数据")
                return self._generate_mock_features()
        else:
            return self._generate_mock_features()
    
    def _get_real_market_features(self):
        """从OKX获取真实市场特征"""
        # 获取BTC-USDT的K线数据
        symbol = 'BTC-USDT-SWAP'
        
        try:
            # 获取1小时K线，100根
            candles = self.adapter.get_candles(symbol, bar='1H', limit=100)
            
            if not candles or len(candles) < 20:
                raise ValueError(f"K线数据不足: {len(candles) if candles else 0} 根")
            
            logger.info(f"✅ 成功获取 {len(candles)} 根K线数据")
            
            # 提取收盘价
            prices = [float(candle[4]) for candle in candles]  # candle[4] 是收盘价
            
            # 计算技术指标
            trend_strength = self._calculate_trend_strength(prices)
            volatility = self._calculate_volatility(prices)
            momentum = self._calculate_momentum(prices)
            rsi = self._calculate_rsi(prices)
            
            # 转换为市场特征
            market_features = self._convert_to_market_features(
                trend_strength, volatility, momentum, rsi
            )
            
            logger.info(f"📊 计算完成 - 趋势: {trend_strength:.3f}, 波动率: {volatility:.3f}, 动量: {momentum:.3f}, RSI: {rsi:.1f}")
            
            return market_features
            
        except Exception as e:
            logger.error(f"❌ 获取真实市场特征失败: {e}", exc_info=True)
            raise
    
    def _calculate_trend_strength(self, prices):
        """
        计算趋势强度
        
        Args:
            prices: 价格序列
            
        Returns:
            趋势强度 (-1到1, 负数=下跌趋势, 正数=上涨趋势)
        """
        if len(prices) < 20:
            return 0.0
        
        # 短期趋势 (最近10根K线)
        short_trend = (prices[-1] - prices[-10]) / prices[-10]
        
        # 中期趋势 (最近30根K线)
        if len(prices) >= 30:
            mid_trend = (prices[-1] - prices[-30]) / prices[-30]
        else:
            mid_trend = short_trend
        
        # 长期趋势 (最近60根K线)
        if len(prices) >= 60:
            long_trend = (prices[-1] - prices[-60]) / prices[-60]
        else:
            long_trend = mid_trend
        
        # 加权平均 (短期权重更大)
        trend_strength = (short_trend * 0.5 + mid_trend * 0.3 + long_trend * 0.2) * 10
        
        # 限制在 -1 到 1
        return max(-1.0, min(1.0, trend_strength))
    
    def _calculate_volatility(self, prices):
        """
        计算波动率
        
        Args:
            prices: 价格序列
            
        Returns:
            波动率 (0到1)
        """
        if len(prices) < 20:
            return 0.5
        
        # 计算最近20根K线的标准差
        recent_prices = prices[-20:]
        mean_price = sum(recent_prices) / len(recent_prices)
        variance = sum((p - mean_price) ** 2 for p in recent_prices) / len(recent_prices)
        std_dev = variance ** 0.5
        
        # 归一化为 0-1 (相对于均价的百分比)
        volatility = (std_dev / mean_price) * 10
        
        return max(0.0, min(1.0, volatility))
    
    def _calculate_momentum(self, prices):
        """
        计算动量指标
        
        Args:
            prices: 价格序列
            
        Returns:
            动量 (-1到1)
        """
        if len(prices) < 10:
            return 0.0
        
        # 计算价格相对于10日均线的位置
        ma_10 = sum(prices[-10:]) / 10
        momentum = (prices[-1] - ma_10) / ma_10 * 10
        
        return max(-1.0, min(1.0, momentum))
    
    def _calculate_rsi(self, prices, period=14):
        """
        计算RSI指标
        
        Args:
            prices: 价格序列
            period: RSI周期
            
        Returns:
            RSI值 (0到100)
        """
        if len(prices) < period + 1:
            return 50.0
        
        # 计算价格变化
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        # 分离上涨和下跌
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        
        # 计算平均上涨和下跌
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _convert_to_market_features(self, trend_strength, volatility, momentum, rsi):
        """
        将技术指标转换为市场特征
        
        Args:
            trend_strength: 趋势强度 (-1到1)
            volatility: 波动率 (0到1)
            momentum: 动量 (-1到1)
            rsi: RSI值 (0到100)
            
        Returns:
            市场特征字典
        """
        # 将RSI转换为0-1范围
        rsi_normalized = rsi / 100.0
        
        # 计算bull和bear值
        # bull值受正趋势、正动量、超买RSI影响
        bull_value = max(0, min(1, 
            0.5 + trend_strength * 0.3 + momentum * 0.2 + (rsi_normalized - 0.5) * 0.2
        ))
        
        # bear值与bull相反
        bear_value = 1.0 - bull_value
        
        # 根据趋势强度分配strong/weak
        if trend_strength > 0:
            strong_bull = bull_value * min(1.0, abs(trend_strength) * 1.5)
            weak_bull = bull_value * (1 - abs(trend_strength))
            strong_bear = bear_value * 0.3
            weak_bear = bear_value * 0.7
        else:
            strong_bear = bear_value * min(1.0, abs(trend_strength) * 1.5)
            weak_bear = bear_value * (1 - abs(trend_strength))
            strong_bull = bull_value * 0.3
            weak_bull = bull_value * 0.7
        
        # sideways值 - 当趋势不明显时较高
        sideways = max(0, 1 - abs(trend_strength) * 2)
        
        # 波动率分级
        if volatility < 0.2:
            vol_features = {'ultra_low_vol': 0.8, 'low_vol': 0.2, 'normal_vol': 0, 'high_vol': 0, 'extreme_high_vol': 0}
        elif volatility < 0.4:
            vol_features = {'ultra_low_vol': 0, 'low_vol': 0.8, 'normal_vol': 0.2, 'high_vol': 0, 'extreme_high_vol': 0}
        elif volatility < 0.6:
            vol_features = {'ultra_low_vol': 0, 'low_vol': 0, 'normal_vol': 0.8, 'high_vol': 0.2, 'extreme_high_vol': 0}
        elif volatility < 0.8:
            vol_features = {'ultra_low_vol': 0, 'low_vol': 0, 'normal_vol': 0, 'high_vol': 0.8, 'extreme_high_vol': 0.2}
        else:
            vol_features = {'ultra_low_vol': 0, 'low_vol': 0, 'normal_vol': 0, 'high_vol': 0.2, 'extreme_high_vol': 0.8}
        
        # RSI情绪指标
        if rsi < 30:
            sentiment = {'extreme_fear': 0.8, 'fear': 0.2, 'neutral': 0, 'greed': 0, 'extreme_greed': 0}
        elif rsi < 40:
            sentiment = {'extreme_fear': 0, 'fear': 0.8, 'neutral': 0.2, 'greed': 0, 'extreme_greed': 0}
        elif rsi < 60:
            sentiment = {'extreme_fear': 0, 'fear': 0, 'neutral': 0.8, 'greed': 0.2, 'extreme_greed': 0}
        elif rsi < 70:
            sentiment = {'extreme_fear': 0, 'fear': 0, 'neutral': 0.2, 'greed': 0.8, 'extreme_greed': 0}
        else:
            sentiment = {'extreme_fear': 0, 'fear': 0, 'neutral': 0, 'greed': 0.2, 'extreme_greed': 0.8}
        
        # 价格形态（基于动量和趋势）
        breakout = max(0, momentum * 0.5 + trend_strength * 0.5) if trend_strength > 0.3 else 0
        breakdown = max(0, -momentum * 0.5 - trend_strength * 0.5) if trend_strength < -0.3 else 0
        pullback = 0.5 if abs(momentum) < 0.2 and abs(trend_strength) > 0.3 else 0
        
        # 组合所有特征
        market_features = {
            'strong_bull': strong_bull,
            'bull': bull_value,
            'weak_bull': weak_bull,
            'sideways': sideways,
            'weak_bear': weak_bear,
            'bear': bear_value,
            'strong_bear': strong_bear,
            **vol_features,
            **sentiment,
            'breakout': breakout,
            'breakdown': breakdown,
            'pullback': pullback
        }
        
        return market_features
    
    def _generate_mock_features(self):
        """生成模拟市场特征（降级方案）"""
        # 生成更合理的市场特征数据，确保bull和bear有一定的相关性
        # 先生成一个基础趋势值
        trend_bias = random.uniform(-1, 1)
        
        # 基于趋势偏置生成bull和bear值
        bull_value = max(0, min(1, 0.5 + trend_bias * 0.3 + random.uniform(-0.2, 0.2)))
        bear_value = max(0, min(1, 0.5 - trend_bias * 0.3 + random.uniform(-0.2, 0.2)))
        
        # 生成其他相关特征
        market_features = {
            'strong_bull': bull_value * random.uniform(0.7, 1.0),
            'bull': bull_value,
            'weak_bull': bull_value * random.uniform(0.3, 0.7),
            'sideways': max(0, 1 - bull_value - bear_value),
            'weak_bear': bear_value * random.uniform(0.3, 0.7),
            'bear': bear_value,
            'strong_bear': bear_value * random.uniform(0.7, 1.0),
            'ultra_low_vol': random.uniform(0, 1),
            'low_vol': random.uniform(0, 1),
            'normal_vol': random.uniform(0, 1),
            'high_vol': random.uniform(0, 1),
            'extreme_high_vol': random.uniform(0, 1),
            'extreme_fear': random.uniform(0, 1),
            'fear': random.uniform(0, 1),
            'neutral': random.uniform(0, 1),
            'greed': random.uniform(0, 1),
            'extreme_greed': random.uniform(0, 1),
            'breakout': random.uniform(0, 1),
            'breakdown': random.uniform(0, 1),
            'pullback': random.uniform(0, 1)
        }
        
        return market_features
    
    def _generate_test_report(self, start_time):
        """生成测试报告"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() / 60
        
        report = {
            'test_summary': {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_minutes': duration,
                'initial_agents': 15,  # 创世Agent数量
                'final_agents': len(self.agents),  # 最终Agent总数
                'alive_agents': sum(1 for agent in self.agents if agent.is_alive),
                'dead_agents': sum(1 for agent in self.agents if not agent.is_alive)
            },
            'evolution_stats': {
                'total_births': self.evolution_stats['total_births'],
                'total_deaths': self.evolution_stats['total_deaths'],
                'total_reproductions': self.evolution_stats['total_reproductions'],
                'net_population_change': self.evolution_stats['total_births'] - 15,
                'survival_rate': sum(1 for agent in self.agents if agent.is_alive) / 15
            },
            'agents_final_status': []
        }
        
        # 记录每个Agent的最终状态
        for agent in self.agents:
            agent_report = {
                'id': agent.id,
                'species': agent.gene.generate_species_name(),
                'is_alive': agent.is_alive,
                'death_reason': agent.death_reason,
                'initial_capital': agent.initial_capital,
                'final_capital': agent.capital,
                'roi': agent.roi,
                'trade_count': agent.trade_count,
                'age': agent.age,
                'final_long_ratio': agent.long_ratio,
                'final_short_ratio': agent.short_ratio,
                'top_preferences': agent.gene.get_top_preferences(3)
            }
            report['agents_final_status'].append(agent_report)
        
        # 计算总体统计
        total_initial_capital = sum(agent.initial_capital for agent in self.agents)
        total_final_capital = sum(agent.capital for agent in self.agents)
        overall_roi = (total_final_capital - total_initial_capital) / total_initial_capital
        
        report['test_summary']['total_initial_capital'] = total_initial_capital
        report['test_summary']['total_final_capital'] = total_final_capital
        report['test_summary']['overall_roi'] = overall_roi
        
        # 保存报告
        report_filename = os.path.join(log_dir, f'test_report_{start_time.strftime("%Y%m%d_%H%M%S")}.json')
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"测试报告已保存: {report_filename}")
        
        # 打印摘要
        logger.info("\n======= 测试报告摘要 =======")
        logger.info(f"测试时长: {duration:.2f} 分钟")
        logger.info(f"初始资金: ${total_initial_capital:.2f}")
        logger.info(f"最终资金: ${total_final_capital:.2f}")
        logger.info(f"总体收益率: {overall_roi:.2%}")
        logger.info(f"存活Agent: {report['test_summary']['alive_agents']}")
        logger.info(f"死亡Agent: {report['test_summary']['dead_agents']}")
        
        # 进化统计
        logger.info("\n======= 进化统计 =======")
        logger.info(f"总出生数: {self.evolution_stats['total_births']} (创世15 + 繁殖{self.evolution_stats['total_births'] - 15})")
        logger.info(f"总死亡数: {self.evolution_stats['total_deaths']}")
        logger.info(f"繁殖次数: {self.evolution_stats['total_reproductions']}")
        logger.info(f"净增长: {self.evolution_stats['total_births'] - 15 - self.evolution_stats['total_deaths']}")
        logger.info(f"存活率: {report['evolution_stats']['survival_rate']:.1%}")
        
        # 打印表现最好的Agent
        alive_agents = [agent for agent in self.agents if agent.is_alive]
        if alive_agents:
            best_agent = max(alive_agents, key=lambda x: x.roi)
            logger.info(f"\n表现最好的Agent:")
            logger.info(f"Agent ID: {best_agent.id}")
            logger.info(f"物种: {best_agent.gene.generate_species_name()}")
            logger.info(f"ROI: {best_agent.roi:.2%}")
            logger.info(f"最终资金: ${best_agent.capital:.2f}")
            logger.info(f"交易次数: {best_agent.trade_count}")
    
    def run(self):
        """运行完整的测试流程"""
        logger.info("\n======= 开始30分钟交易测试 =======\n")
        
        try:
            # 1. 连接到OKX
            if not self.connect_to_okx():
                logger.error("无法连接到OKX，测试终止")
                return False
            
            # 2. 平掉所有持仓
            if not self.skip_position_check:
                try:
                    closed_positions = self.close_all_positions(max_attempts=5)  # 增加最大尝试次数
                    logger.info(f"平仓完成，成功平仓 {closed_positions} 个持仓")
                except KeyboardInterrupt:
                    logger.warning("用户中断平仓操作")
                    response = input("\n是否跳过平仓继续测试? (y/n): ")
                    if response.lower() != 'y':
                        logger.info("用户选择终止测试")
                        return False
                    logger.info("跳过平仓，继续测试...")
                except Exception as e:
                    logger.error(f"平仓过程出错: {e}")
                    response = input("\n平仓失败，是否跳过继续测试? (y/n): ")
                    if response.lower() != 'y':
                        logger.info("用户选择终止测试")
                        return False
                    logger.info("跳过平仓，继续测试...")
            else:
                logger.info("跳过持仓检查和平仓操作")
            
            # 3. 生成初始Agent（优化：从5个增加到15个）
            agent_count = self.generate_initial_agents(count=15)
            if agent_count == 0:
                logger.error("无法生成初始Agent，测试终止")
                return False
            
            # 4. 运行交易测试
            success = self.run_trading_test(duration_minutes=30)
            
            if success:
                logger.info("[OK] 30分钟交易测试成功完成")
            else:
                logger.error("❌ 交易测试失败")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ 测试过程中发生未预期错误: {e}", exc_info=True)
            return False
        finally:
            logger.info("\n======= 测试结束 =======\n")

if __name__ == "__main__":
    print("\n======= Prometheus V30 - 30分钟交易测试 =======\n")
    
    # 询问用户选择数据模式
    print("📊 数据模式选择:")
    print("1. 真实OKX市场数据 (推荐) - 基于真实K线计算技术指标")
    print("2. 模拟数据 - 随机生成市场特征（仅用于测试）")
    
    choice = input("\n请选择数据模式 (1/2，默认1): ").strip()
    use_real_data = choice != '2'
    
    if use_real_data:
        print("\n✅ 已选择: 真实OKX市场数据模式")
        print("   - 将从OKX获取BTC-USDT-SWAP的1小时K线")
        print("   - 基于真实数据计算趋势、波动率、RSI等指标")
    else:
        print("\n✅ 已选择: 模拟数据模式")
        print("   - 将随机生成市场特征")
    
    print("\n开始测试流程，请查看日志获取详细信息...")
    print(f"日志文件: {log_filename}")
    print("\n测试步骤:")
    print("1. 连接到OKX模拟盘")
    print("2. 平掉所有现有持仓")
    print("3. 创世生成15个Agent (8种策略类型) ⬆️ 升级")
    print(f"4. 运行30分钟交易测试 ({'真实数据' if use_real_data else '模拟数据'})")
    print("5. 生成详细测试报告")
    print("\n✨ 系统优化亮点:")
    print("  📊 综合交易指数（5因子加权模型）")
    print("  🧬 策略类型化基因（8种专业策略）")
    print("  💰 智能资金分配（95%利用率，风险可控）")
    print("  👥 15个Agent确保策略多样性和进化效率")
    print("\n请耐心等待测试完成...\n")
    
    # 创建交易测试实例
    test = TradingTest(skip_position_check=False, use_real_data=use_real_data)
    success = test.run()
    
    if success:
        print("\n[OK] 测试成功完成！")
        print(f"详细报告已保存到: {os.path.join(log_dir, 'test_report_*.json')}")
    else:
        print("\n❌ 测试失败，请检查日志获取详细信息")
    
    sys.exit(0 if success else 1)