"""
英灵殿系统（Valhalla） - Prometheus v4.0

北欧神话中的战士殿堂，在此保存传奇Agent的基因和荣耀
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import logging
import numpy as np
import json

logger = logging.getLogger(__name__)


class HallLevel(Enum):
    """殿堂等级"""
    INNER_SANCTUM = "inner"      # 内殿 - 传奇英雄
    GREAT_HALL = "great"         # 中殿 - 精英战士
    OUTER_HALL = "outer"         # 外殿 - 荣誉战士


@dataclass
class Inscription:
    """
    英灵铭文
    
    记录Agent的传奇事迹，永久保存
    """
    agent_id: str
    legend_name: str              # 传奇名
    title: str                    # 称号
    hall_level: HallLevel         # 殿堂等级
    
    # 战绩
    days_survived: int
    total_return: float
    win_rate: float
    total_trades: int
    max_drawdown: float
    sharpe_ratio: float
    
    # 基因和性格
    gene: Dict
    personality: Dict
    gene_signature: str           # 基因特征摘要
    personality_summary: str      # 性格摘要
    
    # 传奇事迹
    legendary_moments: List[str]
    
    # 适应环境
    best_market_regime: str
    specialty: str                # 专长
    
    # 铭文内容（由LLM生成）
    inscription_text: str
    
    # 时间戳
    inducted_at: datetime
    birth_time: datetime
    death_time: Optional[datetime] = None
    
    # 奖章
    medals: List[str] = field(default_factory=list)
    
    # 繁衍统计
    offspring_count: int = 0
    legendary_offspring: List[str] = field(default_factory=list)
    times_used_for_breeding: int = 0
    last_breed_time: Optional[datetime] = None
    
    # 元数据
    generation: int = 1
    parent_genes: List[str] = field(default_factory=list)


class Valhalla:
    """
    英灵殿系统
    
    职责：
    1. 审核并接纳优秀Agent
    2. 赋予传奇名和称号
    3. 刻录铭文，永久保存
    4. 管理三层殿堂
    5. 为繁衍提供优质基因
    """
    
    def __init__(self, llm_oracle=None):
        """
        初始化英灵殿
        
        Args:
            llm_oracle: LLM Oracle实例（用于生成传奇名和铭文）
        """
        self.llm_oracle = llm_oracle
        
        # 三层殿堂
        self.inner_sanctum: List[Inscription] = []   # 内殿
        self.great_hall: List[Inscription] = []      # 中殿
        self.outer_hall: List[Inscription] = []      # 外殿
        
        # 容量限制
        self.max_inner = 5
        self.max_great = 20
        self.max_outer = 100
        
        # 统计
        self.total_inducted = 0
        self.induction_history = []
        
        logger.info("英灵殿已开启 - Valhalla awaits the worthy")
    
    def evaluate_eligibility(self, agent) -> Optional[HallLevel]:
        """
        评估Agent是否有资格入殿，以及应入哪一层
        
        Args:
            agent: Agent实例
            
        Returns:
            Optional[HallLevel]: 应入的殿堂等级，None表示不合格
        """
        stats = agent.get_stats()
        
        # 内殿标准（传奇英雄）
        if (stats['days_alive'] >= 100 and
            stats['total_return'] >= 2.0 and  # 200%
            stats['win_rate'] >= 0.65 and
            stats['max_drawdown'] <= 0.10 and
            len(agent.bulletin_processor.bulletin_history) > 0):  # 有战斗经历
            
            # 还需要特殊成就（由外部传入或检查奖章）
            if hasattr(agent, 'medals') and len(agent.medals) >= 8:
                return HallLevel.INNER_SANCTUM
        
        # 中殿标准（精英战士）
        if (stats['days_alive'] >= 60 and
            stats['total_return'] >= 1.0 and  # 100%
            stats['win_rate'] >= 0.60 and
            stats['max_drawdown'] <= 0.15):
            
            if hasattr(agent, 'medals') and len(agent.medals) >= 5:
                return HallLevel.GREAT_HALL
        
        # 外殿标准（荣誉战士）
        if (stats['days_alive'] >= 30 and
            stats['total_return'] >= 0.5 and  # 50%
            stats['win_rate'] >= 0.55 and
            stats['max_drawdown'] <= 0.20):
            
            if hasattr(agent, 'medals') and len(agent.medals) >= 3:
                return HallLevel.OUTER_HALL
        
        return None
    
    def induct_agent(self, agent, force_level: Optional[HallLevel] = None) -> Optional[Inscription]:
        """
        入殿仪式
        
        Args:
            agent: Agent实例
            force_level: 强制指定殿堂等级（主脑特权）
            
        Returns:
            Optional[Inscription]: 铭文，None表示未入选
        """
        # 1. 评估资格
        if force_level:
            hall_level = force_level
            logger.info(f"主脑特权：强制Agent {agent.agent_id} 入{hall_level.value}殿")
        else:
            hall_level = self.evaluate_eligibility(agent)
        
        if hall_level is None:
            logger.info(f"Agent {agent.agent_id} 未达到入殿标准")
            return None
        
        # 2. 检查容量
        if not self._has_capacity(hall_level):
            # 尝试替换最弱的成员
            if not self._try_replace_weakest(agent, hall_level):
                logger.warning(f"{hall_level.value}殿已满，且Agent不足以替换现有成员")
                return None
        
        # 3. 赋予传奇名
        legend_name = self._grant_legend_name(agent, hall_level)
        
        # 4. 颁发称号
        title = self._grant_title(agent, hall_level)
        
        # 5. 刻录铭文
        inscription = self._create_inscription(agent, legend_name, title, hall_level)
        
        # 6. 加入殿堂
        self._add_to_hall(inscription, hall_level)
        
        # 7. 记录历史
        self.induction_history.append({
            'agent_id': agent.agent_id,
            'legend_name': legend_name,
            'hall_level': hall_level.value,
            'inducted_at': datetime.now()
        })
        
        self.total_inducted += 1
        
        logger.info(
            f"⚔️ 【英灵入殿】 {legend_name} 荣登{self._hall_name_zh(hall_level)}！"
        )
        
        return inscription
    
    def _grant_legend_name(self, agent, hall_level: HallLevel) -> str:
        """
        赋予传奇名
        
        Args:
            agent: Agent实例
            hall_level: 殿堂等级
            
        Returns:
            str: 传奇名
        """
        if hall_level == HallLevel.OUTER_HALL:
            # 外殿：简单称号
            return self._generate_simple_name(agent)
        
        if self.llm_oracle:
            # 中殿和内殿：LLM生成传奇名
            prompt = self._create_naming_prompt(agent, hall_level)
            try:
                legend_name = self.llm_oracle.generate_legend_name(prompt)
                return legend_name
            except Exception as e:
                logger.warning(f"LLM生成传奇名失败: {e}，使用默认命名")
                return self._generate_default_legend_name(agent, hall_level)
        else:
            # 没有LLM，使用默认命名
            return self._generate_default_legend_name(agent, hall_level)
    
    def _generate_simple_name(self, agent) -> str:
        """生成简单称号（外殿）"""
        styles = [
            "稳健战士", "可靠者", "坚守者", "勇敢者", 
            "不屈者", "追随者", "守护者", "探索者"
        ]
        return np.random.choice(styles)
    
    def _generate_default_legend_name(self, agent, hall_level: HallLevel) -> str:
        """
        生成默认传奇名（无LLM时）
        
        基于Agent特征自动生成
        """
        # 分析交易风格
        gene = agent.gene
        personality = agent.personality
        
        # 风格前缀
        if personality.aggression > 0.7:
            prefix = "狂战士"
        elif personality.risk_tolerance < 0.3:
            prefix = "守护者"
        elif personality.contrarian > 0.7:
            prefix = "逆行者"
        elif personality.trend_following > 0.7:
            prefix = "追风者"
        else:
            prefix = "战士"
        
        # 特征后缀
        if agent.total_pnl / agent.initial_capital > 1.5:
            suffix = "·传奇"
        elif agent.win_rate > 0.65:
            suffix = "·精准"
        elif agent.days_alive > 80:
            suffix = "·不朽"
        else:
            suffix = "·荣耀"
        
        legend_name = f"{prefix}{suffix}"
        
        if hall_level == HallLevel.INNER_SANCTUM:
            legend_name = f"【史诗】{legend_name}"
        
        return legend_name
    
    def _create_naming_prompt(self, agent, hall_level: HallLevel) -> str:
        """创建LLM命名提示词"""
        stats = agent.get_stats()
        
        # 提取专长
        specialty = self._extract_specialty(agent)
        
        # 提取传奇时刻
        legendary_moments = self._extract_legendary_moments(agent)
        
        prompt = f"""
请为这位传奇Agent赋予一个响亮的传奇名。

Agent数据：
- ID: {agent.agent_id}
- 存活天数: {stats['days_alive']}
- 总收益: {stats['total_return']*100:.1f}%
- 胜率: {stats['win_rate']*100:.1f}%
- 专长: {specialty}
- 传奇时刻: {legendary_moments}

殿堂等级: {self._hall_name_zh(hall_level)}

命名要求：
1. 响亮有力，富有战斗气息
2. 体现Agent的特征和成就
3. 中文格式：「称号·名字」
4. {'史诗级传奇名' if hall_level == HallLevel.INNER_SANCTUM else '传奇名称'}

示例：
- "黑天鹅猎手·暗影"
- "不死战神·永恒"
- "破局者·天启"

请创造（只返回传奇名，不要其他内容）：
"""
        return prompt
    
    def _grant_title(self, agent, hall_level: HallLevel) -> str:
        """颁发称号"""
        if hall_level == HallLevel.INNER_SANCTUM:
            titles = ["传奇英雄", "不朽战神", "市场主宰", "史诗传奇"]
        elif hall_level == HallLevel.GREAT_HALL:
            titles = ["精英战士", "荣耀之刃", "大师级交易者", "传奇猎手"]
        else:  # OUTER_HALL
            titles = ["荣誉战士", "可靠守卫", "坚韧勇士", "忠诚战士"]
        
        return np.random.choice(titles)
    
    def _create_inscription(self, agent, legend_name: str, title: str, hall_level: HallLevel) -> Inscription:
        """
        创建铭文
        
        Args:
            agent: Agent实例
            legend_name: 传奇名
            title: 称号
            hall_level: 殿堂等级
            
        Returns:
            Inscription: 铭文
        """
        stats = agent.get_stats()
        
        # 提取传奇时刻
        legendary_moments = self._extract_legendary_moments(agent)
        
        # 分析专长
        specialty = self._extract_specialty(agent)
        best_regime = self._analyze_best_market(agent)
        
        # 生成基因特征摘要
        gene_sig = self._summarize_gene(agent.gene)
        
        # 生成性格摘要
        personality_sum = self._summarize_personality(agent.personality)
        
        # 生成铭文内容（如果有LLM）
        if self.llm_oracle:
            inscription_text = self._generate_inscription_text(
                agent, legend_name, legendary_moments, hall_level
            )
        else:
            inscription_text = self._generate_default_inscription(
                agent, legend_name, legendary_moments
            )
        
        # 收集奖章
        medals = getattr(agent, 'medals', [])
        
        inscription = Inscription(
            agent_id=agent.agent_id,
            legend_name=legend_name,
            title=title,
            hall_level=hall_level,
            days_survived=stats['days_alive'],
            total_return=stats['total_return'],
            win_rate=stats['win_rate'],
            total_trades=stats['trade_count'],
            max_drawdown=stats['max_drawdown'],
            sharpe_ratio=self._calculate_sharpe_ratio(agent),
            gene=agent.gene,
            personality=asdict(agent.personality),
            gene_signature=gene_sig,
            personality_summary=personality_sum,
            legendary_moments=legendary_moments,
            best_market_regime=best_regime,
            specialty=specialty,
            inscription_text=inscription_text,
            inducted_at=datetime.now(),
            birth_time=agent.birth_time,
            death_time=getattr(agent, 'death_time', None),
            medals=[str(m) for m in medals],
            generation=1,  # TODO: 从agent获取
            parent_genes=[]  # TODO: 从agent获取
        )
        
        return inscription
    
    def _extract_legendary_moments(self, agent) -> List[str]:
        """提取传奇时刻"""
        moments = []
        
        # 最佳单笔交易
        if hasattr(agent, 'best_trade') and agent.best_trade > 0.2:
            moments.append(f"单笔交易盈利{agent.best_trade*100:.1f}%")
        
        # 连胜记录
        if hasattr(agent, 'consecutive_wins') and agent.consecutive_wins > 5:
            moments.append(f"连续{agent.consecutive_wins}次成功交易")
        
        # 存活奇迹
        if agent.days_alive > 90:
            moments.append(f"在残酷市场中存活{agent.days_alive}天")
        
        # 涅槃重生（如果经历过last stand并成功）
        if hasattr(agent, 'last_stand_success_count') and agent.last_stand_success_count > 0:
            moments.append(f"经历{agent.last_stand_success_count}次拼死一搏并成功")
        
        if not moments:
            moments.append("凭借稳健策略和坚韧意志达成成就")
        
        return moments
    
    def _extract_specialty(self, agent) -> str:
        """提取专长"""
        gene = agent.gene
        personality = agent.personality
        
        if personality.contrarian > 0.7:
            return "逆向交易"
        elif personality.trend_following > 0.7:
            return "趋势跟踪"
        elif personality.risk_tolerance < 0.3:
            return "风险控制"
        elif personality.aggression > 0.7:
            return "激进进攻"
        elif agent.win_rate > 0.65:
            return "精准狙击"
        else:
            return "全能战士"
    
    def _analyze_best_market(self, agent) -> str:
        """分析最适合的市场环境"""
        # TODO: 实际实现应该分析agent的历史表现
        # 这里简化处理
        personality = agent.personality
        
        if personality.risk_tolerance > 0.7:
            return "volatile"  # 波动市
        elif personality.trend_following > 0.7:
            return "bull"  # 牛市
        elif personality.contrarian > 0.7:
            return "bear"  # 熊市
        else:
            return "ranging"  # 震荡市
    
    def _summarize_gene(self, gene: Dict) -> str:
        """基因特征摘要"""
        features = []
        
        if gene.get('leverage_appetite', 0.5) > 0.7:
            features.append("高杠杆偏好")
        
        if gene.get('signal_weights', {}).get('technical', 0.5) > 0.6:
            features.append("技术分析导向")
        
        if gene.get('signal_weights', {}).get('bulletin', 0.1) > 0.4:
            features.append("信息敏感")
        
        return " + ".join(features) if features else "均衡型"
    
    def _summarize_personality(self, personality) -> str:
        """性格摘要"""
        traits = []
        
        if personality.aggression > 0.7:
            traits.append("激进")
        elif personality.aggression < 0.3:
            traits.append("保守")
        
        if personality.discipline > 0.7:
            traits.append("高纪律")
        
        if personality.independence > 0.7:
            traits.append("独立")
        elif personality.herd_mentality > 0.7:
            traits.append("从众")
        
        return " + ".join(traits) if traits else "平衡型"
    
    def _generate_inscription_text(self, agent, legend_name: str, moments: List[str], hall_level: HallLevel) -> str:
        """生成铭文内容（LLM）"""
        if not self.llm_oracle:
            return self._generate_default_inscription(agent, legend_name, moments)
        
        # TODO: 实现LLM生成铭文
        return self._generate_default_inscription(agent, legend_name, moments)
    
    def _generate_default_inscription(self, agent, legend_name: str, moments: List[str]) -> str:
        """生成默认铭文"""
        moments_text = "\n   ".join(moments)
        
        inscription = f"""
"{legend_name}，{self._get_inscription_verse(agent)}"

传奇时刻：
   {moments_text}

—— 监督者记录，{datetime.now().strftime('%Y年%m月%d日')}
"""
        return inscription
    
    def _get_inscription_verse(self, agent) -> str:
        """获取铭文诗句"""
        verses = [
            "在市场的战场上留下了不朽的传奇",
            "以智慧和勇气铸就了辉煌的战绩",
            "在无数次交易中证明了自己的价值",
            "用坚韧和毅力书写了传奇的篇章",
            "在风险与机遇中找到了完美的平衡"
        ]
        return np.random.choice(verses)
    
    def _calculate_sharpe_ratio(self, agent) -> float:
        """计算夏普比率（简化版）"""
        if len(agent.capital_history) < 2:
            return 0.0
        
        returns = np.diff(agent.capital_history) / agent.capital_history[:-1]
        if len(returns) == 0:
            return 0.0
        
        avg_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        return avg_return / std_return
    
    def _has_capacity(self, hall_level: HallLevel) -> bool:
        """检查是否有容量"""
        if hall_level == HallLevel.INNER_SANCTUM:
            return len(self.inner_sanctum) < self.max_inner
        elif hall_level == HallLevel.GREAT_HALL:
            return len(self.great_hall) < self.max_great
        else:  # OUTER_HALL
            return len(self.outer_hall) < self.max_outer
    
    def _try_replace_weakest(self, agent, hall_level: HallLevel) -> bool:
        """尝试替换最弱的成员"""
        hall = self._get_hall(hall_level)
        
        if not hall:
            return False
        
        # 找到最弱的成员
        weakest = min(hall, key=lambda x: x.total_return)
        
        # 比较
        agent_return = agent.total_pnl / agent.initial_capital
        if agent_return > weakest.total_return:
            hall.remove(weakest)
            logger.info(f"替换{hall_level.value}殿最弱成员: {weakest.legend_name}")
            return True
        
        return False
    
    def _add_to_hall(self, inscription: Inscription, hall_level: HallLevel):
        """加入殿堂"""
        if hall_level == HallLevel.INNER_SANCTUM:
            self.inner_sanctum.append(inscription)
            self.inner_sanctum.sort(key=lambda x: x.total_return, reverse=True)
        elif hall_level == HallLevel.GREAT_HALL:
            self.great_hall.append(inscription)
            self.great_hall.sort(key=lambda x: x.total_return, reverse=True)
        else:  # OUTER_HALL
            self.outer_hall.append(inscription)
            self.outer_hall.sort(key=lambda x: x.total_return, reverse=True)
    
    def _get_hall(self, hall_level: HallLevel) -> List[Inscription]:
        """获取殿堂"""
        if hall_level == HallLevel.INNER_SANCTUM:
            return self.inner_sanctum
        elif hall_level == HallLevel.GREAT_HALL:
            return self.great_hall
        else:
            return self.outer_hall
    
    def _hall_name_zh(self, hall_level: HallLevel) -> str:
        """殿堂中文名"""
        names = {
            HallLevel.INNER_SANCTUM: "内殿（传奇英雄）",
            HallLevel.GREAT_HALL: "中殿（精英战士）",
            HallLevel.OUTER_HALL: "外殿（荣誉战士）"
        }
        return names[hall_level]
    
    def get_honor_wall(self) -> str:
        """
        获取荣誉墙文本
        
        Returns:
            str: 格式化的荣誉墙
        """
        lines = []
        lines.append("╔" + "═" * 58 + "╗")
        lines.append("║" + " " * 20 + "英灵殿 · 荣誉墙" + " " * 22 + "║")
        lines.append("╠" + "═" * 58 + "╣")
        lines.append("║" + " " * 58 + "║")
        
        # 内殿
        if self.inner_sanctum:
            lines.append("║  【内殿 - 传奇英雄】" + " " * 36 + "║")
            lines.append("║" + " " * 58 + "║")
            for ins in self.inner_sanctum[:3]:  # 只显示前3位
                name_display = f"  🏆 {ins.legend_name}"
                stats = f"存活{ins.days_survived}天 | 收益{ins.total_return*100:.0f}% | 胜率{ins.win_rate*100:.0f}%"
                lines.append(f"║  {name_display:<52}║")
                lines.append(f"║      {stats:<50}║")
            if len(self.inner_sanctum) > 3:
                lines.append(f"║      ... 共{len(self.inner_sanctum)}位传奇英雄" + " " * 32 + "║")
        
        # 中殿
        if self.great_hall:
            lines.append("║" + " " * 58 + "║")
            lines.append("║  " + "─" * 54 + "║")
            lines.append("║" + " " * 58 + "║")
            lines.append("║  【中殿 - 精英战士】" + " " * 36 + "║")
            lines.append("║" + " " * 58 + "║")
            for ins in self.great_hall[:3]:
                name_display = f"  ⚔️  {ins.legend_name}"
                stats = f"存活{ins.days_survived}天 | 收益{ins.total_return*100:.0f}% | 胜率{ins.win_rate*100:.0f}%"
                lines.append(f"║  {name_display:<52}║")
            if len(self.great_hall) > 3:
                lines.append(f"║      ... 共{len(self.great_hall)}位精英战士" + " " * 32 + "║")
        
        # 外殿统计
        if self.outer_hall:
            lines.append("║" + " " * 58 + "║")
            lines.append("║  " + "─" * 54 + "║")
            lines.append("║" + " " * 58 + "║")
            lines.append(f"║  【外殿 - 荣誉战士】共{len(self.outer_hall)}位" + " " * 30 + "║")
        
        lines.append("║" + " " * 58 + "║")
        lines.append("╚" + "═" * 58 + "╝")
        
        return "\n".join(lines)
    
    def get_best_genes_for_breeding(self, count: int = 5, market_regime: Optional[str] = None) -> List[Inscription]:
        """
        获取最适合繁衍的基因
        
        Args:
            count: 数量
            market_regime: 市场环境（可选筛选条件）
            
        Returns:
            List[Inscription]: 铭文列表
        """
        # 合并所有殿堂，内殿权重最高
        candidates = []
        
        for ins in self.inner_sanctum:
            candidates.append((ins, 5.0))  # 内殿权重5
        
        for ins in self.great_hall:
            candidates.append((ins, 3.0))  # 中殿权重3
        
        for ins in self.outer_hall:
            candidates.append((ins, 2.0))  # 外殿权重2
        
        # 如果指定市场环境，调整权重
        if market_regime:
            adjusted = []
            for ins, weight in candidates:
                if ins.best_market_regime == market_regime:
                    weight *= 1.5  # 匹配市场的权重提高
                adjusted.append((ins, weight))
            candidates = adjusted
        
        # 按权重排序
        candidates.sort(key=lambda x: x[1] * x[0].total_return, reverse=True)
        
        # 返回前count个
        selected = [ins for ins, weight in candidates[:count]]
        
        return selected
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            'total_inducted': self.total_inducted,
            'inner_sanctum_count': len(self.inner_sanctum),
            'great_hall_count': len(self.great_hall),
            'outer_hall_count': len(self.outer_hall),
            'total_heroes': len(self.inner_sanctum) + len(self.great_hall) + len(self.outer_hall),
            'avg_return_inner': np.mean([ins.total_return for ins in self.inner_sanctum]) if self.inner_sanctum else 0,
            'avg_return_great': np.mean([ins.total_return for ins in self.great_hall]) if self.great_hall else 0,
            'avg_return_outer': np.mean([ins.total_return for ins in self.outer_hall]) if self.outer_hall else 0
        }

