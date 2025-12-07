"""
多样性监控器 (Diversity Monitor) - Prometheus v5.2 Day 3

核心功能：
1. 实时监控种群多样性（基因熵、策略熵）
2. 检测多样性下降趋势
3. 触发强制多样性保护机制

设计哲学：
- "多样性是进化的基础"
- "防止单一策略统治"
- "保持生态平衡"
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
from scipy.stats import entropy as shannon_entropy

logger = logging.getLogger(__name__)


@dataclass
class DiversityMetrics:
    """多样性指标快照"""
    cycle: int
    timestamp: datetime
    
    # 基因多样性
    gene_entropy: float  # Shannon熵（基因向量）
    gene_simpson: float  # Simpson多样性指数
    avg_gene_distance: float  # 平均基因距离
    
    # 策略多样性
    strategy_entropy: float  # 策略分布熵
    unique_strategies: int  # 独特策略数量
    
    # 血统多样性
    lineage_entropy: float  # 血统分布熵
    active_families: int  # 活跃家族数量
    
    # 综合评分
    diversity_score: float  # 综合多样性得分 (0-1)
    is_healthy: bool  # 是否健康
    
    def __repr__(self):
        return (f"DiversityMetrics(cycle={self.cycle}, "
                f"gene_entropy={self.gene_entropy:.3f}, "
                f"strategy_entropy={self.strategy_entropy:.3f}, "
                f"diversity_score={self.diversity_score:.3f}, "
                f"healthy={'✅' if self.is_healthy else '⚠️'})")


@dataclass
class DiversityAlert:
    """多样性警报"""
    cycle: int
    alert_type: str  # 'warning', 'critical'
    metric_name: str  # 触发警报的指标
    current_value: float
    threshold: float
    message: str
    suggested_action: str


class DiversityMonitor:
    """
    多样性监控器
    
    职责：
    1. 计算多种多样性指标
    2. 实时监控多样性变化
    3. 检测多样性危机
    4. 触发保护机制
    """
    
    # 默认阈值
    DEFAULT_THRESHOLDS = {
        'gene_entropy_min': 2.0,  # 基因熵最低阈值（log2(N)的一定比例）
        'strategy_entropy_min': 1.5,  # 策略熵最低阈值
        'lineage_entropy_min': 2.5,  # 血统熵最低阈值
        'active_families_min': 10,  # 活跃家族最少数量
        'diversity_score_min': 0.5,  # 综合得分最低阈值
        'decline_rate_max': 0.2,  # 最大下降速率（每周期）
    }
    
    def __init__(self, 
                 thresholds: Optional[Dict[str, float]] = None,
                 history_length: int = 100):
        """
        初始化多样性监控器
        
        Args:
            thresholds: 自定义阈值（覆盖默认值）
            history_length: 历史记录保留长度
        """
        self.thresholds = {**self.DEFAULT_THRESHOLDS}
        if thresholds:
            self.thresholds.update(thresholds)
        
        self.history_length = history_length
        
        # 历史记录
        self.metrics_history: List[DiversityMetrics] = []
        self.alerts_history: List[DiversityAlert] = []
        
        # 统计
        self.total_alerts = 0
        self.critical_alerts = 0
        
        logger.info(f"多样性监控器已初始化 | 阈值: {self.thresholds}")
    
    # ==================== 核心监控方法 ====================
    
    def monitor(self, agents: List, cycle: int) -> DiversityMetrics:
        """
        监控当前种群多样性
        
        Args:
            agents: Agent列表
            cycle: 当前周期
        
        Returns:
            DiversityMetrics: 多样性指标
        """
        if not agents:
            logger.warning(f"周期 {cycle}: 种群为空，无法监控")
            return self._create_empty_metrics(cycle)
        
        # 1. 计算各项指标
        gene_entropy = self._calculate_gene_entropy(agents)
        gene_simpson = self._calculate_simpson_index(agents)
        avg_gene_distance = self._calculate_avg_gene_distance(agents)
        
        strategy_entropy = self._calculate_strategy_entropy(agents)
        unique_strategies = self._count_unique_strategies(agents)
        
        lineage_entropy = self._calculate_lineage_entropy(agents)
        active_families = self._count_active_families(agents)
        
        # 2. 计算综合得分
        diversity_score = self._calculate_diversity_score(
            gene_entropy, strategy_entropy, lineage_entropy,
            active_families, len(agents)
        )
        
        # 3. 判断健康状态
        is_healthy = self._check_health(
            gene_entropy, strategy_entropy, lineage_entropy,
            active_families, diversity_score
        )
        
        # 4. 创建指标对象
        metrics = DiversityMetrics(
            cycle=cycle,
            timestamp=datetime.now(),
            gene_entropy=gene_entropy,
            gene_simpson=gene_simpson,
            avg_gene_distance=avg_gene_distance,
            strategy_entropy=strategy_entropy,
            unique_strategies=unique_strategies,
            lineage_entropy=lineage_entropy,
            active_families=active_families,
            diversity_score=diversity_score,
            is_healthy=is_healthy
        )
        
        # 5. 保存历史
        self._add_to_history(metrics)
        
        # 6. 检测警报
        alerts = self._check_alerts(metrics)
        for alert in alerts:
            self._add_alert(alert)
        
        logger.info(f"周期 {cycle} | {metrics}")
        
        return metrics
    
    # ==================== 熵值计算 ====================
    
    def _calculate_gene_entropy(self, agents: List) -> float:
        """
        计算基因Shannon熵
        
        方法：对每个基因维度计算熵，然后取平均
        """
        if not agents:
            return 0.0
        
        try:
            # 提取所有基因向量
            gene_vectors = np.array([agent.genome.vector for agent in agents])
            
            # 对每个维度计算熵
            dimension_entropies = []
            for dim in range(gene_vectors.shape[1]):
                values = gene_vectors[:, dim]
                # 离散化（分成10个bins）
                hist, _ = np.histogram(values, bins=10, range=(0, 1))
                hist = hist / hist.sum()  # 归一化
                ent = shannon_entropy(hist, base=2)
                dimension_entropies.append(ent)
            
            # 返回平均熵
            avg_entropy = np.mean(dimension_entropies)
            return float(avg_entropy)
        
        except Exception as e:
            logger.error(f"计算基因熵失败: {e}")
            return 0.0
    
    def _calculate_simpson_index(self, agents: List) -> float:
        """
        计算Simpson多样性指数
        
        Simpson指数 = 1 - Σ(pi^2)
        其中 pi 是第i个类型的比例
        
        这里我们基于主导家族来分类
        """
        if not agents:
            return 0.0
        
        try:
            # 统计每个主导家族的数量
            family_counts = {}
            for agent in agents:
                # 获取主导家族
                dominant_family = agent.lineage.get_dominant_family()
                family_counts[dominant_family] = family_counts.get(dominant_family, 0) + 1
            
            # 计算Simpson指数
            n = len(agents)
            simpson = 1.0 - sum((count/n)**2 for count in family_counts.values())
            
            return float(simpson)
        
        except Exception as e:
            logger.error(f"计算Simpson指数失败: {e}")
            return 0.0
    
    def _calculate_avg_gene_distance(self, agents: List) -> float:
        """
        计算平均基因距离（欧氏距离）
        
        采样方法：随机选择100对计算平均
        """
        if len(agents) < 2:
            return 0.0
        
        try:
            # 提取基因向量
            gene_vectors = np.array([agent.genome.vector for agent in agents])
            
            # 如果Agent数量较少，计算所有对
            if len(agents) <= 20:
                distances = []
                for i in range(len(agents)):
                    for j in range(i+1, len(agents)):
                        dist = np.linalg.norm(gene_vectors[i] - gene_vectors[j])
                        distances.append(dist)
                return float(np.mean(distances))
            
            # 否则随机采样100对
            sample_size = min(100, len(agents) * (len(agents) - 1) // 2)
            distances = []
            for _ in range(sample_size):
                i, j = np.random.choice(len(agents), 2, replace=False)
                dist = np.linalg.norm(gene_vectors[i] - gene_vectors[j])
                distances.append(dist)
            
            return float(np.mean(distances))
        
        except Exception as e:
            logger.error(f"计算平均基因距离失败: {e}")
            return 0.0
    
    def _calculate_strategy_entropy(self, agents: List) -> float:
        """
        计算策略分布熵
        
        策略由fear_of_death和risk_appetite定义
        将策略空间分成网格，计算分布熵
        """
        if not agents:
            return 0.0
        
        try:
            # 提取fear和risk
            fears = [agent.instinct.fear_of_death for agent in agents]
            risks = [agent.instinct.risk_appetite for agent in agents]
            
            # 创建2D直方图（10x10网格）
            hist, _, _ = np.histogram2d(fears, risks, bins=10, range=[[0, 2], [0, 1]])
            hist = hist.flatten()
            hist = hist / hist.sum()  # 归一化
            
            # 计算Shannon熵
            ent = shannon_entropy(hist, base=2)
            
            return float(ent)
        
        except Exception as e:
            logger.error(f"计算策略熵失败: {e}")
            return 0.0
    
    def _count_unique_strategies(self, agents: List) -> int:
        """
        统计独特策略数量
        
        策略定义：(fear四舍五入到0.1, risk四舍五入到0.1)
        """
        if not agents:
            return 0
        
        try:
            strategies = set()
            for agent in agents:
                fear = round(agent.instinct.fear_of_death, 1)
                risk = round(agent.instinct.risk_appetite, 1)
                strategies.add((fear, risk))
            
            return len(strategies)
        
        except Exception as e:
            logger.error(f"统计独特策略失败: {e}")
            return 0
    
    def _calculate_lineage_entropy(self, agents: List) -> float:
        """
        计算血统分布熵
        
        基于每个Agent的血统向量，计算种群级别的血统分布熵
        """
        if not agents:
            return 0.0
        
        try:
            # 汇总所有血统向量
            lineage_vectors = np.array([agent.lineage.vector for agent in agents])
            # 计算平均血统分布
            avg_lineage = lineage_vectors.mean(axis=0)
            
            # 计算熵
            ent = shannon_entropy(avg_lineage, base=2)
            
            return float(ent)
        
        except Exception as e:
            logger.error(f"计算血统熵失败: {e}")
            return 0.0
    
    def _count_active_families(self, agents: List) -> int:
        """
        统计活跃家族数量
        
        活跃家族：至少有一个Agent的血统向量中该家族占比>5%
        """
        if not agents:
            return 0
        
        try:
            # 汇总血统向量
            lineage_vectors = np.array([agent.lineage.vector for agent in agents])
            
            # 统计每个家族在种群中的总占比
            family_totals = lineage_vectors.sum(axis=0)
            
            # 活跃家族：总占比 > 动态阈值
            # 原始阈值0.05*len(agents)在“家族数接近种群数”的场景过高
            # 这里放宽为：max(1, 0.01 * len(agents))，避免创世阶段刷屏
            threshold = max(1.0, 0.01 * len(agents))
            active = (family_totals > threshold).sum()
            
            return int(active)
        
        except Exception as e:
            logger.error(f"统计活跃家族失败: {e}")
            return 0
    
    # ==================== 综合评估 ====================
    
    def _calculate_diversity_score(self, 
                                   gene_entropy: float,
                                   strategy_entropy: float,
                                   lineage_entropy: float,
                                   active_families: int,
                                   population_size: int) -> float:
        """
        计算综合多样性得分 (0-1)
        
        权重分配：
        - 基因熵：30%
        - 策略熵：30%
        - 血统熵：20%
        - 活跃家族：20%
        """
        # 归一化各指标到 [0, 1]
        # 基因熵：理论最大值 ≈ log2(10) ≈ 3.32（10个bins）
        gene_score = min(gene_entropy / 3.32, 1.0)
        
        # 策略熵：理论最大值 ≈ log2(100) ≈ 6.64（10x10网格）
        strategy_score = min(strategy_entropy / 6.64, 1.0)
        
        # 血统熵：理论最大值 ≈ log2(50) ≈ 5.64（50个家族）
        lineage_score = min(lineage_entropy / 5.64, 1.0)
        
        # 活跃家族：理论最大值 = 50
        family_score = min(active_families / 50.0, 1.0)
        
        # 加权求和
        diversity_score = (
            0.30 * gene_score +
            0.30 * strategy_score +
            0.20 * lineage_score +
            0.20 * family_score
        )
        
        return float(diversity_score)
    
    def _check_health(self,
                     gene_entropy: float,
                     strategy_entropy: float,
                     lineage_entropy: float,
                     active_families: int,
                     diversity_score: float) -> bool:
        """
        检查多样性健康状态
        
        健康标准：所有关键指标都高于阈值
        """
        checks = [
            gene_entropy >= self.thresholds['gene_entropy_min'],
            strategy_entropy >= self.thresholds['strategy_entropy_min'],
            lineage_entropy >= self.thresholds['lineage_entropy_min'],
            active_families >= self.thresholds['active_families_min'],
            diversity_score >= self.thresholds['diversity_score_min']
        ]
        
        return all(checks)
    
    # ==================== 警报系统 ====================
    
    def _check_alerts(self, metrics: DiversityMetrics) -> List[DiversityAlert]:
        """
        检查是否需要发出警报
        
        返回所有触发的警报
        """
        alerts = []
        
        # 检查基因熵
        if metrics.gene_entropy < self.thresholds['gene_entropy_min']:
            severity = 'critical' if metrics.gene_entropy < self.thresholds['gene_entropy_min'] * 0.7 else 'warning'
            alerts.append(DiversityAlert(
                cycle=metrics.cycle,
                alert_type=severity,
                metric_name='gene_entropy',
                current_value=metrics.gene_entropy,
                threshold=self.thresholds['gene_entropy_min'],
                message=f"基因熵过低: {metrics.gene_entropy:.3f} < {self.thresholds['gene_entropy_min']:.3f}",
                suggested_action="增加变异率或引入新基因"
            ))
        
        # 检查策略熵
        if metrics.strategy_entropy < self.thresholds['strategy_entropy_min']:
            severity = 'critical' if metrics.strategy_entropy < self.thresholds['strategy_entropy_min'] * 0.7 else 'warning'
            alerts.append(DiversityAlert(
                cycle=metrics.cycle,
                alert_type=severity,
                metric_name='strategy_entropy',
                current_value=metrics.strategy_entropy,
                threshold=self.thresholds['strategy_entropy_min'],
                message=f"策略熵过低: {metrics.strategy_entropy:.3f} < {self.thresholds['strategy_entropy_min']:.3f}",
                suggested_action="保护少数策略或强制多样化繁殖"
            ))
        
        # 检查血统熵
        if metrics.lineage_entropy < self.thresholds['lineage_entropy_min']:
            severity = 'critical' if metrics.lineage_entropy < self.thresholds['lineage_entropy_min'] * 0.7 else 'warning'
            alerts.append(DiversityAlert(
                cycle=metrics.cycle,
                alert_type=severity,
                metric_name='lineage_entropy',
                current_value=metrics.lineage_entropy,
                threshold=self.thresholds['lineage_entropy_min'],
                message=f"血统熵过低: {metrics.lineage_entropy:.3f} < {self.thresholds['lineage_entropy_min']:.3f}",
                suggested_action="保护弱势家族或引入新家族"
            ))
        
        # 检查活跃家族数量
        if metrics.active_families < self.thresholds['active_families_min']:
            severity = 'critical' if metrics.active_families < self.thresholds['active_families_min'] * 0.5 else 'warning'
            alerts.append(DiversityAlert(
                cycle=metrics.cycle,
                alert_type=severity,
                metric_name='active_families',
                current_value=float(metrics.active_families),
                threshold=self.thresholds['active_families_min'],
                message=f"活跃家族过少: {metrics.active_families} < {int(self.thresholds['active_families_min'])}",
                suggested_action="降低弱势家族淘汰率"
            ))
        
        # 检查综合得分
        if metrics.diversity_score < self.thresholds['diversity_score_min']:
            severity = 'critical' if metrics.diversity_score < self.thresholds['diversity_score_min'] * 0.7 else 'warning'
            alerts.append(DiversityAlert(
                cycle=metrics.cycle,
                alert_type=severity,
                metric_name='diversity_score',
                current_value=metrics.diversity_score,
                threshold=self.thresholds['diversity_score_min'],
                message=f"多样性综合得分过低: {metrics.diversity_score:.3f} < {self.thresholds['diversity_score_min']:.3f}",
                suggested_action="启动强制多样性保护机制"
            ))
        
        # 检查下降趋势
        if len(self.metrics_history) >= 3:
            recent_scores = [m.diversity_score for m in self.metrics_history[-3:]]
            decline_rate = (recent_scores[0] - recent_scores[-1]) / recent_scores[0] if recent_scores[0] > 0 else 0
            
            if decline_rate > self.thresholds['decline_rate_max']:
                alerts.append(DiversityAlert(
                    cycle=metrics.cycle,
                    alert_type='warning',
                    metric_name='diversity_decline',
                    current_value=decline_rate,
                    threshold=self.thresholds['decline_rate_max'],
                    message=f"多样性快速下降: {decline_rate:.1%} > {self.thresholds['decline_rate_max']:.1%}",
                    suggested_action="立即干预，防止多样性崩溃"
                ))
        
        return alerts
    
    # ==================== 历史管理 ====================
    
    def _add_to_history(self, metrics: DiversityMetrics):
        """添加到历史记录"""
        self.metrics_history.append(metrics)
        
        # 限制历史长度
        if len(self.metrics_history) > self.history_length:
            self.metrics_history.pop(0)
    
    def _add_alert(self, alert: DiversityAlert):
        """添加警报"""
        self.alerts_history.append(alert)
        self.total_alerts += 1
        
        if alert.alert_type == 'critical':
            self.critical_alerts += 1
            logger.error(f"🚨 严重警报 | {alert.message} | {alert.suggested_action}")
        else:
            logger.warning(f"⚠️ 警告 | {alert.message} | {alert.suggested_action}")
        
        # 限制历史长度
        if len(self.alerts_history) > self.history_length:
            self.alerts_history.pop(0)
    
    def _create_empty_metrics(self, cycle: int) -> DiversityMetrics:
        """创建空指标对象"""
        return DiversityMetrics(
            cycle=cycle,
            timestamp=datetime.now(),
            gene_entropy=0.0,
            gene_simpson=0.0,
            avg_gene_distance=0.0,
            strategy_entropy=0.0,
            unique_strategies=0,
            lineage_entropy=0.0,
            active_families=0,
            diversity_score=0.0,
            is_healthy=False
        )
    
    # ==================== 查询方法 ====================
    
    def get_latest_metrics(self) -> Optional[DiversityMetrics]:
        """获取最新的多样性指标"""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_recent_alerts(self, count: int = 5) -> List[DiversityAlert]:
        """获取最近的警报"""
        return self.alerts_history[-count:]
    
    def get_metrics_history(self, cycles: int = None) -> List[DiversityMetrics]:
        """获取历史指标"""
        if cycles is None:
            return self.metrics_history
        return self.metrics_history[-cycles:]
    
    def get_trend_summary(self, cycles: int = 10) -> Dict:
        """
        获取趋势摘要
        
        Returns:
            Dict: 包含各指标的趋势信息
        """
        if len(self.metrics_history) < 2:
            return {}
        
        recent = self.metrics_history[-cycles:]
        
        if len(recent) < 2:
            return {}
        
        def calc_trend(values):
            """计算趋势（上升/下降/稳定）"""
            if len(values) < 2:
                return "稳定"
            change = (values[-1] - values[0]) / values[0] if values[0] != 0 else 0
            if change > 0.1:
                return "上升"
            elif change < -0.1:
                return "下降"
            else:
                return "稳定"
        
        return {
            'gene_entropy_trend': calc_trend([m.gene_entropy for m in recent]),
            'strategy_entropy_trend': calc_trend([m.strategy_entropy for m in recent]),
            'lineage_entropy_trend': calc_trend([m.lineage_entropy for m in recent]),
            'diversity_score_trend': calc_trend([m.diversity_score for m in recent]),
            'total_alerts': self.total_alerts,
            'critical_alerts': self.critical_alerts
        }
    
    # ==================== 统计报告 ====================
    
    def generate_report(self) -> str:
        """
        生成多样性监控报告
        
        Returns:
            str: 格式化的报告文本
        """
        if not self.metrics_history:
            return "暂无监控数据"
        
        latest = self.metrics_history[-1]
        trend = self.get_trend_summary()
        
        report = f"""
{'='*80}
🧬 多样性监控报告
{'='*80}

📊 最新指标（周期 {latest.cycle}）
{'─'*80}
  基因多样性:
    • Shannon熵: {latest.gene_entropy:.3f}
    • Simpson指数: {latest.gene_simpson:.3f}
    • 平均基因距离: {latest.avg_gene_distance:.3f}
  
  策略多样性:
    • 策略熵: {latest.strategy_entropy:.3f}
    • 独特策略: {latest.unique_strategies}
  
  血统多样性:
    • 血统熵: {latest.lineage_entropy:.3f}
    • 活跃家族: {latest.active_families}
  
  综合评估:
    • 多样性得分: {latest.diversity_score:.3f}
    • 健康状态: {'✅ 健康' if latest.is_healthy else '⚠️ 需要关注'}

📈 趋势分析（最近10个周期）
{'─'*80}
  • 基因熵: {trend.get('gene_entropy_trend', 'N/A')}
  • 策略熵: {trend.get('strategy_entropy_trend', 'N/A')}
  • 血统熵: {trend.get('lineage_entropy_trend', 'N/A')}
  • 综合得分: {trend.get('diversity_score_trend', 'N/A')}

🚨 警报统计
{'─'*80}
  • 总警报数: {trend.get('total_alerts', 0)}
  • 严重警报: {trend.get('critical_alerts', 0)}
  • 最近警报: {len(self.get_recent_alerts())}

{'='*80}
"""
        
        # 添加最近警报详情
        recent_alerts = self.get_recent_alerts(3)
        if recent_alerts:
            report += "\n⚠️ 最近警报:\n" + "─"*80 + "\n"
            for alert in recent_alerts:
                icon = "🚨" if alert.alert_type == 'critical' else "⚠️"
                report += f"  {icon} 周期{alert.cycle}: {alert.message}\n"
                report += f"     建议: {alert.suggested_action}\n\n"
        
        return report

