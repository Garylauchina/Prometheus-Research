"""
ExperienceDB - 经验数据库

功能：
  1. 保存每次训练的最佳基因 + WorldSignature
  2. 查询相似市场环境下的最佳基因
  3. 智能创世（基于历史经验）
  4. 统计分析

这是MemoryLayer的极简子集，专注于解决0知识创世问题
"""

import sqlite3
import json
from typing import List, Dict, Optional
from datetime import datetime
import numpy as np
import logging

from .world_signature_simple import WorldSignatureSimple

logger = logging.getLogger(__name__)


class ExperienceDB:
    """
    经验数据库
    
    存储：
      - WorldSignature（市场状态）
      - Genome（最佳基因）
      - Performance（性能指标）
    
    查询：
      - 基于WorldSignature相似度
      - 返回相似市场环境下的最佳基因
    """
    
    def __init__(self, db_path: str = 'data/experience.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_tables()
        
        logger.info(f"ExperienceDB初始化: {db_path}")
    
    def _init_tables(self):
        """初始化数据库表（v6.0 Stage 1.1扩展 + v7.0扩展）"""
        # ===== 表1：best_genomes（Agent基因，保持不变）=====
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS best_genomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                market_type TEXT NOT NULL,
                world_signature TEXT NOT NULL,
                genome TEXT NOT NULL,
                roi REAL NOT NULL,
                sharpe REAL,
                max_drawdown REAL,
                trade_count INTEGER,
                profit_factor REAL,
                timestamp TEXT NOT NULL,
                -- ✅ v6.0 新增：奖章机制
                awards INTEGER DEFAULT 0,
                retirement_reason TEXT,
                agent_id TEXT,
                generation INTEGER
            )
        """)
        
        # ===== 表2：system_metrics（v7.0新增：三维异常检测）⭐⭐⭐ =====
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS system_metrics (
                -- 基础
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                cycle INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                
                -- 三维原始值⭐
                ws_score REAL,
                friction_index REAL,
                death_rate REAL,
                
                -- 三维异常标志⭐
                ws_anomaly INTEGER DEFAULT 0,
                friction_anomaly INTEGER DEFAULT 0,
                death_anomaly INTEGER DEFAULT 0,
                
                -- 综合结果⭐⭐⭐
                total_anomaly_dims INTEGER,
                risk_level TEXT,
                
                -- Prophet决策
                prophet_S REAL,
                prophet_E REAL,
                system_scale REAL,
                
                UNIQUE(run_id, cycle)
            )
        """)
        
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_market_type ON best_genomes(market_type)
        """)
        
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_roi ON best_genomes(roi DESC)
        """)
        
        # ✅ Stage 1.1: 添加Profit Factor索引（主要排序指标）
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_profit_factor ON best_genomes(profit_factor DESC)
        """)
        
        # ✅ v6.0: 添加奖章索引（退休机制）
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_awards ON best_genomes(awards DESC)
        """)
        
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_retirement_reason ON best_genomes(retirement_reason)
        """)
        
        # ===== v7.0: system_metrics表的索引 =====
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_system_metrics_run ON system_metrics(run_id)
        """)
        
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_system_metrics_cycle ON system_metrics(cycle)
        """)
        
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_system_metrics_risk ON system_metrics(risk_level)
        """)
        
        self.conn.commit()
    
    def save_best_genomes(
        self,
        run_id: str,
        market_type: str,
        world_signature: WorldSignatureSimple,
        agents: List,
        top_k: int = 10
    ):
        """
        保存最佳基因
        
        参数：
          - run_id: 训练ID
          - market_type: 市场类型（bull/bear/sideways/crash）
          - world_signature: 市场状态
          - agents: Agent列表（已按fitness排序）
          - top_k: 保存前K个
        """
        ws_json = json.dumps(world_signature.to_dict())
        timestamp = datetime.now().isoformat()
        
        for i, agent in enumerate(agents[:top_k]):
            # ✅ 关键修复：保存StrategyParams而不是Genome！
            # StrategyParams才是真正控制Agent行为的参数
            if hasattr(agent, 'strategy_params') and agent.strategy_params:
                genome_dict = agent.strategy_params.to_dict()
            elif hasattr(agent.genome, 'to_dict'):
                # 降级：如果没有strategy_params，保存genome
                genome_dict = agent.genome.to_dict()
            else:
                genome_dict = {}
            
            # ✅ 修复：从Agent的实际数据计算ROI
            initial_capital = getattr(agent, 'initial_capital', 1.0)
            # ✅ Stage 1.1 Bug修复：使用account.private_ledger.virtual_capital而不是current_capital
            # current_capital可能没被更新，真实资金在账簿中！
            if hasattr(agent, 'account') and agent.account:
                current_capital = agent.account.private_ledger.virtual_capital
            else:
                current_capital = getattr(agent, 'current_capital', 1.0)
            roi = (current_capital / initial_capital - 1.0) if initial_capital > 0 else 0.0
            
            # ✅ 修复：从Account获取交易统计（如果有）
            trade_count = 0
            total_profit = 0.0
            total_loss = 0.0
            
            if hasattr(agent, 'account') and agent.account:
                private_ledger = agent.account.private_ledger
                trade_count = len(private_ledger.trade_history)
                
                # ✅ Stage 1.1: 计算Profit Factor（主要指标）
                # PF = total_profit / abs(total_loss)
                # ⚠️ 重要：只统计平仓交易（closed=True），开仓交易pnl=None
                for trade in private_ledger.trade_history:
                    # 只统计平仓交易
                    if not getattr(trade, 'closed', False):
                        continue
                    
                    pnl = getattr(trade, 'pnl', 0.0)
                    if pnl is None:
                        pnl = 0.0  # ✅ 防止None值
                    if pnl > 0:
                        total_profit += pnl
                    elif pnl < 0:
                        total_loss += abs(pnl)
            
            # ✅ 计算Profit Factor
            if total_loss > 0:
                profit_factor = total_profit / total_loss
            elif total_profit > 0:
                profit_factor = total_profit  # 无亏损交易，PF = 总盈利
            else:
                profit_factor = 0.0  # 无交易或无盈亏
            
            # Sharpe和MaxDrawdown暂时简化（需要完整的PnL序列来计算）
            sharpe = roi / 0.1 if roi != 0 else 0.0  # 简化：假设波动率0.1
            max_drawdown = getattr(agent, 'max_drawdown', 0.0)
            
            self.conn.execute("""
                INSERT INTO best_genomes 
                (run_id, market_type, world_signature, genome, roi, sharpe, max_drawdown, trade_count, profit_factor, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                market_type,
                ws_json,
                json.dumps(genome_dict),
                roi,
                sharpe,
                max_drawdown,
                trade_count,
                profit_factor,
                timestamp
            ))
        
        self.conn.commit()
        logger.info(f"保存{top_k}个最佳基因: {run_id} ({market_type})")
    
    def save_retired_agent(
        self,
        agent,
        world_signature: Optional[WorldSignatureSimple],
        awards: int = 0,
        retirement_reason: str = 'unknown',
        generation: int = 0,
        run_id: str = 'unknown',
        market_type: str = 'unknown'
    ):
        """
        保存退休Agent到史册（v6.0 Stage 1.1新方法）
        
        🏆 专门用于退休机制：
        - 保存单个退休Agent（不是Top K列表）
        - 记录奖章数量
        - 记录退休原因（hero/age）
        - 记录Agent唯一标识
        
        参数：
          - agent: 退休的Agent
          - world_signature: 当前市场状态（可选）
          - awards: 获得的奖章数量
          - retirement_reason: 退休原因（'hero' or 'age'）
          - generation: 退休时的代数
          - run_id: 训练ID
          - market_type: 市场类型
        """
        # World Signature
        ws_json = json.dumps(world_signature.to_dict()) if world_signature else '{}'
        timestamp = datetime.now().isoformat()
        
        # Agent基因
        if hasattr(agent, 'strategy_params') and agent.strategy_params:
            genome_dict = agent.strategy_params.to_dict()
        elif hasattr(agent, 'genome') and hasattr(agent.genome, 'to_dict'):
            genome_dict = agent.genome.to_dict()
        else:
            genome_dict = {}
        
        # 性能指标
        initial_capital = getattr(agent, 'initial_capital', 1.0)
        if hasattr(agent, 'account') and agent.account:
            current_capital = agent.account.private_ledger.virtual_capital
        else:
            current_capital = getattr(agent, 'current_capital', 1.0)
        roi = (current_capital / initial_capital - 1.0) if initial_capital > 0 else 0.0
        
        # 交易统计
        trade_count = 0
        total_profit = 0.0
        total_loss = 0.0
        
        if hasattr(agent, 'account') and agent.account:
            private_ledger = agent.account.private_ledger
            trade_count = len([t for t in private_ledger.trade_history if getattr(t, 'closed', False)])
            
            # Profit Factor
            for trade in private_ledger.trade_history:
                if not getattr(trade, 'closed', False):
                    continue
                pnl = getattr(trade, 'pnl', 0.0) or 0.0
                if pnl > 0:
                    total_profit += pnl
                elif pnl < 0:
                    total_loss += abs(pnl)
        
        # Profit Factor
        if total_loss > 0:
            profit_factor = total_profit / total_loss
        elif total_profit > 0:
            profit_factor = total_profit
        else:
            profit_factor = 0.0
        
        # Sharpe和MaxDrawdown
        sharpe = roi / 0.1 if roi != 0 else 0.0
        max_drawdown = getattr(agent, 'max_drawdown', 0.0)
        
        # Agent ID
        agent_id = getattr(agent, 'agent_id', 'unknown')
        
        # 插入数据库
        self.conn.execute("""
            INSERT INTO best_genomes 
            (run_id, market_type, world_signature, genome, roi, sharpe, max_drawdown, 
             trade_count, profit_factor, timestamp, awards, retirement_reason, agent_id, generation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id,
            market_type,
            ws_json,
            json.dumps(genome_dict),
            roi,
            sharpe,
            max_drawdown,
            trade_count,
            profit_factor,
            timestamp,
            awards,
            retirement_reason,
            agent_id,
            generation
        ))
        
        self.conn.commit()
        
        if retirement_reason == 'hero':
            logger.info(f"🏆 {agent_id}载入史册: {awards}个奖章, ROI={roi*100:.2f}%, PF={profit_factor:.2f}")
        else:
            logger.info(f"📜 {agent_id}记录生平: ROI={roi*100:.2f}%, PF={profit_factor:.2f}")
    
    def query_similar_genomes(
        self,
        current_ws: WorldSignatureSimple,
        top_k: int = 50,
        min_similarity: float = 0.7,
        market_type: Optional[str] = None
    ) -> List[Dict]:
        """
        查询相似市场环境下的最佳基因
        
        参数：
          - current_ws: 当前市场的WorldSignature
          - top_k: 返回前K个
          - min_similarity: 最低相似度阈值
          - market_type: 市场类型过滤（可选）
        
        返回：
          - 基因列表（按相似度降序）
        """
        # 查询所有历史记录（✅ Stage 1.1: 添加profit_factor）
        if market_type:
            cursor = self.conn.execute("""
                SELECT world_signature, genome, roi, sharpe, max_drawdown, 
                       COALESCE(profit_factor, 0.0) as profit_factor
                FROM best_genomes
                WHERE market_type = ?
            """, (market_type,))
        else:
            cursor = self.conn.execute("""
                SELECT world_signature, genome, roi, sharpe, max_drawdown,
                       COALESCE(profit_factor, 0.0) as profit_factor
                FROM best_genomes
            """)
        
        # 计算相似度
        candidates = []
        for row in cursor:
            historical_ws = WorldSignatureSimple.from_dict(json.loads(row[0]))
            similarity = current_ws.similarity(historical_ws)
            
            if similarity >= min_similarity:
                candidates.append({
                    'similarity': similarity,
                    'genome': json.loads(row[1]),
                    'roi': row[2],
                    'sharpe': row[3],
                    'max_drawdown': row[4],
                    'profit_factor': row[5]  # ✅ Stage 1.1: 添加PF
                })
        
        # ✅ Stage 1.1: 排序改为先按相似度，再按Profit Factor（主要指标）
        candidates.sort(key=lambda x: (x['similarity'], x['profit_factor']), reverse=True)
        
        logger.info(
            f"查询相似基因: 找到{len(candidates)}个相似记录 "
            f"(min_similarity={min_similarity:.2f})"
        )
        
        return candidates[:top_k]
    
    def smart_genesis(
        self,
        current_ws: WorldSignatureSimple,
        count: int = 50,
        strategy: str = 'adaptive'
    ) -> List[Dict]:
        """
        智能创世
        
        策略：
          - 'adaptive': 70%历史最佳 + 20%变异 + 10%随机
          - 'aggressive': 90%历史最佳 + 10%随机
          - 'exploratory': 50%历史最佳 + 50%随机
        
        返回：
          - 基因字典列表
        """
        # 查询相似的历史经验
        similar = self.query_similar_genomes(
            current_ws,
            top_k=100,
            min_similarity=0.7
        )
        
        if not similar:
            logger.info(f"🆕 无相似历史经验，使用100%随机创世")
            return self._generate_random_genomes(count)
        
        logger.info(
            f"🧠 智能创世：基于{len(similar)}个相似经验 "
            f"(相似度: {similar[0]['similarity']:.2f}~{similar[-1]['similarity']:.2f})"
        )
        
        genomes = []
        
        if strategy == 'adaptive':
            # 70%历史最佳
            best_count = int(count * 0.70)
            for i in range(best_count):
                genome = similar[i % len(similar)]['genome']
                genomes.append(genome)
            
            # 20%变异
            mutated_count = int(count * 0.20)
            for i in range(mutated_count):
                base = similar[i % len(similar)]['genome']
                mutated = self._mutate_genome(base, mutation_rate=0.30)
                genomes.append(mutated)
            
            # 10%随机
            random_count = count - best_count - mutated_count
            genomes.extend(self._generate_random_genomes(random_count))
        
        elif strategy == 'aggressive':
            # 90%历史最佳 + 10%随机
            best_count = int(count * 0.90)
            for i in range(best_count):
                genome = similar[i % len(similar)]['genome']
                genomes.append(genome)
            
            random_count = count - best_count
            genomes.extend(self._generate_random_genomes(random_count))
        
        elif strategy == 'exploratory':
            # 50%历史最佳 + 50%随机
            best_count = int(count * 0.50)
            for i in range(best_count):
                genome = similar[i % len(similar)]['genome']
                genomes.append(genome)
            
            random_count = count - best_count
            genomes.extend(self._generate_random_genomes(random_count))
        
        return genomes
    
    def _generate_random_genomes(self, count: int) -> List[Dict]:
        """生成随机基因（占位符，实际由外部实现）"""
        return [{'random': True} for _ in range(count)]
    
    def _mutate_genome(self, genome: Dict, mutation_rate: float = 0.30) -> Dict:
        """变异基因（占位符，实际由外部实现）"""
        mutated = genome.copy()
        mutated['mutated'] = True
        return mutated
    
    def get_statistics(self, market_type: Optional[str] = None) -> Dict:
        """
        获取统计信息
        
        参数：
          - market_type: 市场类型过滤（可选）
        
        返回：
          - 统计字典
        """
        if market_type:
            cursor = self.conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    AVG(roi) as avg_roi,
                    MAX(roi) as max_roi,
                    MIN(roi) as min_roi,
                    AVG(sharpe) as avg_sharpe
                FROM best_genomes
                WHERE market_type = ?
            """, (market_type,))
        else:
            cursor = self.conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    AVG(roi) as avg_roi,
                    MAX(roi) as max_roi,
                    MIN(roi) as min_roi,
                    AVG(sharpe) as avg_sharpe
                FROM best_genomes
            """)
        
        row = cursor.fetchone()
        return {
            'total_records': row[0],
            'avg_roi': row[1] if row[1] else 0.0,
            'max_roi': row[2] if row[2] else 0.0,
            'min_roi': row[3] if row[3] else 0.0,
            'avg_sharpe': row[4] if row[4] else 0.0
        }
    
    # ========== v7.0新增：系统指标管理⭐⭐⭐ ==========
    
    def save_system_metrics(
        self,
        run_id: str,
        cycle: int,
        ws_score: float,
        friction_index: float,
        death_rate: float,
        ws_anomaly: bool,
        friction_anomaly: bool,
        death_anomaly: bool,
        total_anomaly_dims: int,
        risk_level: str,
        prophet_S: float,
        prophet_E: float,
        system_scale: float
    ):
        """
        保存系统指标（v7.0三维异常检测）⭐⭐⭐
        
        Args:
            run_id: 运行ID
            cycle: 周期编号
            ws_score: WorldSignature综合得分
            friction_index: 摩擦综合指数
            death_rate: 非正常死亡率
            ws_anomaly: WorldSignature异常标志
            friction_anomaly: 摩擦异常标志
            death_anomaly: 死亡率异常标志
            total_anomaly_dims: 异常维度数（0-3）
            risk_level: 风险等级（safe/warning/danger/critical）
            prophet_S: Prophet的S值
            prophet_E: Prophet的E值
            system_scale: 系统规模
        """
        try:
            self.conn.execute("""
                INSERT INTO system_metrics (
                    run_id, cycle, timestamp,
                    ws_score, friction_index, death_rate,
                    ws_anomaly, friction_anomaly, death_anomaly,
                    total_anomaly_dims, risk_level,
                    prophet_S, prophet_E, system_scale
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id, cycle, datetime.now().isoformat(),
                ws_score, friction_index, death_rate,
                int(ws_anomaly), int(friction_anomaly), int(death_anomaly),
                total_anomaly_dims, risk_level,
                prophet_S, prophet_E, system_scale
            ))
            self.conn.commit()
            logger.debug(f"💾 系统指标已保存: cycle={cycle}, risk={risk_level}")
        except sqlite3.IntegrityError:
            # 如果记录已存在，更新它
            self.conn.execute("""
                UPDATE system_metrics SET
                    ws_score=?, friction_index=?, death_rate=?,
                    ws_anomaly=?, friction_anomaly=?, death_anomaly=?,
                    total_anomaly_dims=?, risk_level=?,
                    prophet_S=?, prophet_E=?, system_scale=?,
                    timestamp=?
                WHERE run_id=? AND cycle=?
            """, (
                ws_score, friction_index, death_rate,
                int(ws_anomaly), int(friction_anomaly), int(death_anomaly),
                total_anomaly_dims, risk_level,
                prophet_S, prophet_E, system_scale,
                datetime.now().isoformat(),
                run_id, cycle
            ))
            self.conn.commit()
    
    def query_history(
        self,
        run_id: str,
        end_cycle: int,
        window: int = 100
    ) -> Dict[str, List[float]]:
        """
        查询历史数据（用于异常检测）⭐
        
        Args:
            run_id: 运行ID
            end_cycle: 结束周期
            window: 历史窗口大小（默认100）
        
        Returns:
            {
                'ws_scores': [0.05, 0.06, ...],
                'friction_indices': [0.02, 0.03, ...],
                'death_rates': [0.10, 0.12, ...]
            }
        """
        cursor = self.conn.execute("""
            SELECT ws_score, friction_index, death_rate
            FROM system_metrics
            WHERE run_id = ?
              AND cycle >= ?
              AND cycle < ?
            ORDER BY cycle ASC
        """, (run_id, max(0, end_cycle - window), end_cycle))
        
        rows = cursor.fetchall()
        
        if not rows:
            return {
                'ws_scores': [],
                'friction_indices': [],
                'death_rates': []
            }
        
        return {
            'ws_scores': [r[0] for r in rows if r[0] is not None],
            'friction_indices': [r[1] for r in rows if r[1] is not None],
            'death_rates': [r[2] for r in rows if r[2] is not None]
        }
    
    def get_risk_summary(self, run_id: str) -> Dict:
        """
        获取风险摘要统计⭐
        
        Args:
            run_id: 运行ID
        
        Returns:
            统计信息
        """
        cursor = self.conn.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN risk_level='safe' THEN 1 ELSE 0 END) as safe_count,
                SUM(CASE WHEN risk_level='warning' THEN 1 ELSE 0 END) as warning_count,
                SUM(CASE WHEN risk_level='danger' THEN 1 ELSE 0 END) as danger_count,
                SUM(CASE WHEN risk_level='critical' THEN 1 ELSE 0 END) as critical_count,
                AVG(total_anomaly_dims) as avg_anomaly_dims
            FROM system_metrics
            WHERE run_id = ?
        """, (run_id,))
        
        row = cursor.fetchone()
        
        if not row or row[0] == 0:
            return {
                'total': 0,
                'safe': 0,
                'warning': 0,
                'danger': 0,
                'critical': 0,
                'avg_anomaly_dims': 0
            }
        
        return {
            'total': row[0],
            'safe': row[1],
            'warning': row[2],
            'danger': row[3],
            'critical': row[4],
            'avg_anomaly_dims': row[5]
        }
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()
        logger.info("ExperienceDB已关闭")

