"""
多样性可视化器 (Diversity Visualizer) - Prometheus v5.2 Day 3

核心功能：
1. 生成多样性趋势图表
2. 可视化警报历史
3. 生成多样性热力图
"""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 非交互式后端，适合服务器环境
import numpy as np
from typing import List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DiversityVisualizer:
    """
    多样性可视化器
    
    职责：
    1. 绘制多样性趋势图
    2. 绘制警报历史图
    3. 保存为图片文件
    """
    
    def __init__(self, output_dir: str = "./results/diversity"):
        """
        初始化可视化器
        
        Args:
            output_dir: 图片输出目录
        """
        self.output_dir = output_dir
        
        # 创建输出目录
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # 设置中文字体（如果可用）
        try:
            plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
        except:
            pass
        
        logger.info(f"多样性可视化器已初始化 | 输出目录: {output_dir}")
    
    def plot_diversity_trends(self, 
                             metrics_history: List,
                             save_path: Optional[str] = None) -> str:
        """
        绘制多样性趋势图
        
        Args:
            metrics_history: DiversityMetrics历史记录
            save_path: 保存路径（可选）
        
        Returns:
            str: 保存的文件路径
        """
        if not metrics_history:
            logger.warning("无历史数据，无法绘制趋势图")
            return ""
        
        # 提取数据
        cycles = [m.cycle for m in metrics_history]
        gene_entropy = [m.gene_entropy for m in metrics_history]
        strategy_entropy = [m.strategy_entropy for m in metrics_history]
        lineage_entropy = [m.lineage_entropy for m in metrics_history]
        diversity_score = [m.diversity_score for m in metrics_history]
        active_families = [m.active_families for m in metrics_history]
        
        # 创建图表
        fig, axes = plt.subplots(3, 2, figsize=(14, 12))
        fig.suptitle('多样性监控趋势', fontsize=16, fontweight='bold')
        
        # 1. 基因熵
        axes[0, 0].plot(cycles, gene_entropy, 'b-', linewidth=2, marker='o')
        axes[0, 0].set_title('基因熵')
        axes[0, 0].set_xlabel('周期')
        axes[0, 0].set_ylabel('熵值')
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].axhline(y=2.0, color='r', linestyle='--', alpha=0.5, label='最低阈值')
        axes[0, 0].legend()
        
        # 2. 策略熵
        axes[0, 1].plot(cycles, strategy_entropy, 'g-', linewidth=2, marker='s')
        axes[0, 1].set_title('策略熵')
        axes[0, 1].set_xlabel('周期')
        axes[0, 1].set_ylabel('熵值')
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].axhline(y=1.5, color='r', linestyle='--', alpha=0.5, label='最低阈值')
        axes[0, 1].legend()
        
        # 3. 血统熵
        axes[1, 0].plot(cycles, lineage_entropy, 'orange', linewidth=2, marker='^')
        axes[1, 0].set_title('血统熵')
        axes[1, 0].set_xlabel('周期')
        axes[1, 0].set_ylabel('熵值')
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].axhline(y=2.5, color='r', linestyle='--', alpha=0.5, label='最低阈值')
        axes[1, 0].legend()
        
        # 4. 活跃家族数
        axes[1, 1].plot(cycles, active_families, 'purple', linewidth=2, marker='d')
        axes[1, 1].set_title('活跃家族数量')
        axes[1, 1].set_xlabel('周期')
        axes[1, 1].set_ylabel('数量')
        axes[1, 1].grid(True, alpha=0.3)
        axes[1, 1].axhline(y=10, color='r', linestyle='--', alpha=0.5, label='最低阈值')
        axes[1, 1].legend()
        
        # 5. 综合多样性得分
        axes[2, 0].plot(cycles, diversity_score, 'red', linewidth=3, marker='o')
        axes[2, 0].set_title('综合多样性得分', fontweight='bold')
        axes[2, 0].set_xlabel('周期')
        axes[2, 0].set_ylabel('得分')
        axes[2, 0].grid(True, alpha=0.3)
        axes[2, 0].axhline(y=0.5, color='r', linestyle='--', alpha=0.5, label='最低阈值')
        axes[2, 0].fill_between(cycles, diversity_score, 0, alpha=0.3, color='red')
        axes[2, 0].legend()
        
        # 6. 健康状态分布
        healthy_count = sum(1 for m in metrics_history if m.is_healthy)
        unhealthy_count = len(metrics_history) - healthy_count
        
        axes[2, 1].bar(['健康', '不健康'], 
                      [healthy_count, unhealthy_count],
                      color=['green', 'red'])
        axes[2, 1].set_title('健康状态分布')
        axes[2, 1].set_ylabel('数量')
        axes[2, 1].grid(True, alpha=0.3, axis='y')
        
        # 添加数值标签
        for i, (label, count) in enumerate([('健康', healthy_count), ('不健康', unhealthy_count)]):
            axes[2, 1].text(i, count, str(count), ha='center', va='bottom')
        
        plt.tight_layout()
        
        # 保存
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = f"{self.output_dir}/diversity_trends_{timestamp}.png"
        
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"✅ 趋势图已保存: {save_path}")
        return save_path
    
    def plot_alert_timeline(self,
                           alerts_history: List,
                           save_path: Optional[str] = None) -> str:
        """
        绘制警报时间线
        
        Args:
            alerts_history: 警报历史记录
            save_path: 保存路径
        
        Returns:
            str: 保存的文件路径
        """
        if not alerts_history:
            logger.warning("无警报数据，跳过警报图绘制")
            return ""
        
        # 按周期分组统计
        cycles = sorted(set(a.cycle for a in alerts_history))
        warning_counts = []
        critical_counts = []
        
        for cycle in cycles:
            cycle_alerts = [a for a in alerts_history if a.cycle == cycle]
            warning_counts.append(sum(1 for a in cycle_alerts if a.alert_type == 'warning'))
            critical_counts.append(sum(1 for a in cycle_alerts if a.alert_type == 'critical'))
        
        # 绘制堆叠柱状图
        fig, ax = plt.subplots(figsize=(12, 6))
        
        width = 0.6
        ax.bar(cycles, warning_counts, width, label='警告', color='orange', alpha=0.8)
        ax.bar(cycles, critical_counts, width, bottom=warning_counts, 
               label='严重', color='red', alpha=0.8)
        
        ax.set_xlabel('周期')
        ax.set_ylabel('警报数量')
        ax.set_title('多样性警报时间线', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        # 保存
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = f"{self.output_dir}/alert_timeline_{timestamp}.png"
        
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"✅ 警报图已保存: {save_path}")
        return save_path
    
    def plot_diversity_heatmap(self,
                              metrics_history: List,
                              save_path: Optional[str] = None) -> str:
        """
        绘制多样性热力图
        
        显示各指标随时间的变化热力图
        
        Args:
            metrics_history: 历史记录
            save_path: 保存路径
        
        Returns:
            str: 保存的文件路径
        """
        if not metrics_history or len(metrics_history) < 2:
            logger.warning("数据不足，无法绘制热力图")
            return ""
        
        # 提取数据
        cycles = [m.cycle for m in metrics_history]
        
        # 归一化到0-1范围（用于热力图）
        data = np.array([
            [self._normalize(m.gene_entropy, 0, 4) for m in metrics_history],
            [self._normalize(m.strategy_entropy, 0, 7) for m in metrics_history],
            [self._normalize(m.lineage_entropy, 0, 6) for m in metrics_history],
            [self._normalize(m.active_families, 0, 50) for m in metrics_history],
            [m.diversity_score for m in metrics_history],
            [1.0 if m.is_healthy else 0.0 for m in metrics_history]
        ])
        
        # 绘制热力图
        fig, ax = plt.subplots(figsize=(14, 6))
        
        im = ax.imshow(data.T, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
        
        # 设置标签
        ax.set_yticks(range(6))
        ax.set_yticklabels(['基因熵', '策略熵', '血统熵',
                           '活跃家族', '多样性得分', '健康状态'])
        
        # X轴显示周期（每5个显示一次）
        step = max(1, len(cycles) // 10)
        ax.set_xticks(range(0, len(cycles), step))
        ax.set_xticklabels([cycles[i] for i in range(0, len(cycles), step)])
        
        ax.set_xlabel('周期')
        ax.set_title('多样性指标热力图', fontsize=14, fontweight='bold')
        
        # 添加颜色条
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('归一化值', rotation=270, labelpad=15)
        
        plt.tight_layout()
        
        # 保存
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = f"{self.output_dir}/diversity_heatmap_{timestamp}.png"
        
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"✅ 热力图已保存: {save_path}")
        return save_path
    
    def generate_dashboard(self,
                          metrics_history: List,
                          alerts_history: List,
                          save_path: Optional[str] = None) -> str:
        """
        生成综合仪表板
        
        Args:
            metrics_history: 指标历史
            alerts_history: 警报历史
            save_path: 保存路径
        
        Returns:
            str: 保存的文件路径
        """
        if not metrics_history:
            logger.warning("无数据，无法生成仪表板")
            return ""
        
        # 生成所有图表
        trends_path = self.plot_diversity_trends(metrics_history)
        
        if alerts_history:
            alert_path = self.plot_alert_timeline(alerts_history)
        
        heatmap_path = self.plot_diversity_heatmap(metrics_history)
        
        logger.info(f"✅ 仪表板已生成:")
        logger.info(f"   - 趋势图: {trends_path}")
        if alerts_history:
            logger.info(f"   - 警报图: {alert_path}")
        logger.info(f"   - 热力图: {heatmap_path}")
        
        return trends_path
    
    @staticmethod
    def _normalize(value: float, min_val: float, max_val: float) -> float:
        """归一化到0-1范围"""
        if max_val == min_val:
            return 0.5
        return np.clip((value - min_val) / (max_val - min_val), 0, 1)

