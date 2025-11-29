"""
PreTrainer - 预训练模块

职责: 多场景训练，筛选优秀基因，建立基因库
"""

import json
import random
from typing import List, Dict
from .gene import Gene
from .strategy import Strategy
from .agent import Agent
from .system import PrometheusV3


class PreTrainer:
    """预训练器"""
    
    def __init__(self, config: Dict):
        """
        Args:
            config: 预训练配置
        """
        self.config = config
        self.agents = []
        self.scenario_results = {}
    
    def generate_initial_population(self) -> List[Gene]:
        """
        生成初始随机基因种群
        
        Returns:
            基因列表
        """
        print(f"Generating {self.config['initial_population']} random genes...")
        
        genes = []
        for i in range(self.config['initial_population']):
            gene = Gene.random()
            genes.append(gene)
        
        print(f"✅ Generated {len(genes)} genes")
        return genes
    
    def generate_synthetic_prices(self, scenario: Dict) -> List[Dict]:
        """
        生成合成价格数据
        
        Args:
            scenario: 场景配置
        
        Returns:
            价格列表 [{'date': 'YYYY-MM-DD', 'price': float}, ...]
        """
        duration = scenario['duration']
        trend = scenario['trend']
        volatility = scenario['volatility']
        
        prices = []
        current_price = 50000.0  # 起始价格
        
        for day in range(duration + 1):
            # 日期
            date = f"2024-01-{day+1:02d}" if day < 31 else f"2024-{(day//30)+1:02d}-{(day%30)+1:02d}"
            
            # 价格
            prices.append({
                'date': date,
                'price': current_price
            })
            
            # 下一天价格
            # 趋势分量
            trend_change = trend / duration
            
            # 随机波动
            random_change = random.gauss(0, volatility)
            
            # 总变化
            total_change = trend_change + random_change
            
            current_price *= (1 + total_change)
            current_price = max(1000, current_price)  # 最低价格
        
        return prices
    
    def train_scenario(self, scenario: Dict, genes: List[Gene]) -> Dict:
        """
        在单个场景中训练所有基因
        
        Args:
            scenario: 场景配置
            genes: 基因列表
        
        Returns:
            场景结果
        """
        print(f"\n{'='*60}")
        print(f"Training Scenario: {scenario['name']}")
        print(f"Description: {scenario['description']}")
        print(f"{'='*60}")
        
        # 加载或生成价格数据
        if scenario.get('type') == 'synthetic':
            prices = self.generate_synthetic_prices(scenario)
            print(f"Generated {len(prices)} days of synthetic data")
        else:
            with open(scenario['data'], 'r') as f:
                prices = json.load(f)
            print(f"Loaded {len(prices)} days of historical data")
        
        # 创建训练配置（宽松版）
        training_config = self.config['training_config'].copy()
        training_config['initial_capital'] = self.config['initial_capital_per_agent'] * len(genes)
        training_config['initial_agents'] = 0  # 手动初始化
        
        # 创建系统
        system = PrometheusV3(training_config)
        
        # 创建智能体
        for i, gene in enumerate(genes):
            strategy = Strategy(gene, training_config['agent_manager']['strategy'])
            capital = system.capital_pool.withdraw(
                self.config['initial_capital_per_agent'],
                'initialization'
            )
            
            agent = Agent(
                agent_id=i,
                gene=gene,
                initial_capital=capital,
                strategy=strategy
            )
            
            system.agent_manager.agents.append(agent)
            system.agent_manager.next_agent_id += 1
            system.agent_manager.stats['total_births'] += 1
        
        print(f"Created {len(system.agent_manager.agents)} agents")
        
        # 运行模拟
        print(f"Running simulation...")
        total_days = len(prices) - 1
        
        for day in range(1, total_days + 1):
            system.run_day(prices, day)
            
            if day % 500 == 0 or day == total_days:
                active = len([a for a in system.agent_manager.agents if a.is_alive])
                print(f"  Day {day}/{total_days} - Active: {active}/{len(genes)}")
        
        # 收集结果
        results = []
        for i, agent in enumerate(system.agent_manager.agents):
            results.append({
                'gene_index': i,
                'roi': agent.roi,
                'trades': agent.trade_count,
                'survived': agent.is_alive,
                'final_capital': agent.capital
            })
        
        # 统计
        survived = sum(1 for r in results if r['survived'])
        avg_roi = sum(r['roi'] for r in results if r['survived']) / max(1, survived)
        avg_trades = sum(r['trades'] for r in results if r['survived']) / max(1, survived)
        
        print(f"\n✅ Scenario Complete:")
        print(f"  Survived: {survived}/{len(genes)} ({survived/len(genes)*100:.1f}%)")
        print(f"  Avg ROI: {avg_roi:.2%}")
        print(f"  Avg Trades: {avg_trades:.1f}")
        
        return {
            'scenario': scenario['name'],
            'results': results,
            'stats': {
                'survived': survived,
                'avg_roi': avg_roi,
                'avg_trades': avg_trades
            }
        }
    
    def calculate_scores(self, genes: List[Gene]) -> List[Dict]:
        """
        计算每个基因的综合得分
        
        Args:
            genes: 基因列表
        
        Returns:
            得分列表
        """
        print(f"\n{'='*60}")
        print("Calculating Scores")
        print(f"{'='*60}")
        
        scores = []
        
        for i, gene in enumerate(genes):
            total_score = 0.0
            scenario_perfs = {}
            
            for scenario_name, scenario_result in self.scenario_results.items():
                # 找到这个基因的结果
                gene_result = next(
                    (r for r in scenario_result['results'] if r['gene_index'] == i),
                    None
                )
                
                if gene_result:
                    # 场景得分 = ROI × 存活 × 交易活跃度
                    roi_score = max(0, gene_result['roi'])
                    survival_score = 1.0 if gene_result['survived'] else 0.0
                    activity_score = min(1.0, gene_result['trades'] / 10.0)
                    
                    scenario_score = roi_score * survival_score * activity_score
                    
                    # 加权
                    scenario_config = next(
                        s for s in self.config['scenarios'] 
                        if s['name'] == scenario_name
                    )
                    weight = scenario_config['weight']
                    
                    total_score += scenario_score * weight
                    
                    scenario_perfs[scenario_name] = {
                        'roi': gene_result['roi'],
                        'trades': gene_result['trades'],
                        'survived': gene_result['survived'],
                        'score': scenario_score
                    }
            
            scores.append({
                'gene_index': i,
                'gene': gene,
                'total_score': total_score,
                'scenario_performance': scenario_perfs
            })
        
        # 排序
        scores.sort(key=lambda x: x['total_score'], reverse=True)
        
        print(f"✅ Calculated scores for {len(scores)} genes")
        print(f"  Top score: {scores[0]['total_score']:.4f}")
        print(f"  Median score: {scores[len(scores)//2]['total_score']:.4f}")
        print(f"  Bottom score: {scores[-1]['total_score']:.4f}")
        
        return scores
    
    def is_diverse(self, gene: Gene, selected_genes: List[Gene], threshold: float = 0.3) -> bool:
        """
        检查基因是否与已选基因足够不同
        
        Args:
            gene: 待检查基因
            selected_genes: 已选基因列表
            threshold: 多样性阈值
        
        Returns:
            是否足够不同
        """
        if not selected_genes:
            return True
        
        # 计算与所有已选基因的平均相似度
        similarities = []
        for selected_gene in selected_genes:
            similarity = gene.similarity(selected_gene)
            similarities.append(similarity)
        
        avg_similarity = sum(similarities) / len(similarities)
        
        return avg_similarity < (1.0 - threshold)
    
    def select_genes(self, scored_genes: List[Dict]) -> List[Dict]:
        """
        筛选优秀基因
        
        Args:
            scored_genes: 得分列表（已排序）
        
        Returns:
            筛选后的基因列表
        """
        print(f"\n{'='*60}")
        print("Selecting Genes")
        print(f"{'='*60}")
        
        selection_config = self.config['selection']
        
        # 1. 基本筛选
        candidates = []
        for item in scored_genes:
            # 检查最小ROI
            if not item['scenario_performance']:
                continue
            
            avg_roi = sum(
                perf['roi'] for perf in item['scenario_performance'].values()
            ) / len(item['scenario_performance'])
            
            if avg_roi < selection_config['min_roi']:
                continue
            
            # 检查最小交易次数
            total_trades = sum(
                perf['trades'] for perf in item['scenario_performance'].values()
            )
            
            if total_trades < selection_config['min_trades']:
                continue
            
            # 检查存活
            if selection_config['must_survive']:
                if not all(perf['survived'] for perf in item['scenario_performance'].values()):
                    continue
            
            candidates.append(item)
        
        print(f"After basic filtering: {len(candidates)} candidates")
        
        # 2. 多样性筛选
        selected = []
        diversity_threshold = selection_config['diversity_threshold']
        
        for item in candidates:
            if len(selected) >= selection_config['top_n']:
                break
            
            # 检查多样性
            if self.is_diverse(item['gene'], [s['gene'] for s in selected], diversity_threshold):
                selected.append(item)
        
        print(f"After diversity filtering: {len(selected)} selected")
        
        # 3. 如果数量不足，补充得分最高的
        for item in candidates:
            if len(selected) >= selection_config['top_n']:
                break
            
            if item not in selected:
                selected.append(item)
                print(f"  Added non-diverse gene (score: {item['total_score']:.4f})")
        
        print(f"\n✅ Selected {len(selected)} genes")
        
        return selected
    
    def save_gene_library(self, selected_genes: List[Dict], filename: str):
        """
        保存基因库
        
        Args:
            selected_genes: 筛选后的基因列表
            filename: 文件名
        """
        import time
        
        gene_library = {
            'metadata': {
                'version': '3.0',
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'initial_population': self.config['initial_population'],
                'selected_count': len(selected_genes),
                'scenarios': [s['name'] for s in self.config['scenarios']]
            },
            'genes': [
                {
                    'gene': item['gene'].to_dict(),
                    'total_score': item['total_score'],
                    'scenario_performance': item['scenario_performance']
                }
                for item in selected_genes
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(gene_library, f, indent=2)
        
        print(f"\n✅ Gene library saved to: {filename}")
    
    def run(self) -> str:
        """
        运行完整预训练流程
        
        Returns:
            基因库文件名
        """
        print(f"\n{'='*60}")
        print("PROMETHEUS V3.0 PRE-TRAINING")
        print(f"{'='*60}")
        
        # 1. 生成初始种群
        genes = self.generate_initial_population()
        
        # 2. 多场景训练
        for scenario in self.config['scenarios']:
            result = self.train_scenario(scenario, genes)
            self.scenario_results[scenario['name']] = result
        
        # 3. 计算得分
        scored_genes = self.calculate_scores(genes)
        
        # 4. 筛选基因
        selected_genes = self.select_genes(scored_genes)
        
        # 5. 保存基因库
        filename = '/home/ubuntu/v30_pretrained_gene_library.json'
        self.save_gene_library(selected_genes, filename)
        
        print(f"\n{'='*60}")
        print("PRE-TRAINING COMPLETE!")
        print(f"{'='*60}")
        print(f"Initial population: {self.config['initial_population']}")
        print(f"Selected genes: {len(selected_genes)}")
        print(f"Selection rate: {len(selected_genes)/self.config['initial_population']*100:.1f}%")
        print(f"Gene library: {filename}")
        
        return filename
