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
        """初始化数据库表"""
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
                timestamp TEXT NOT NULL
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
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()
        logger.info("ExperienceDB已关闭")

