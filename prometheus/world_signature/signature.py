"""
WorldSignature_V2 - 完整市场签名

整合宏观和微观编码，提供完整的市场情境描述
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime
import numpy as np
import uuid
import json

from .macro_code import MacroCode
from .micro_code import MicroCode


@dataclass
class WorldSignature_V2:
    """
    完整的市场签名 v2.0
    
    整合：
    - MacroCode: 宏观编码（长时间窗口）
    - MicroCode: 微观编码（短时间窗口）
    - Regime识别
    - 评分指标
    """
    
    # ========== 基本信息 ==========
    id: str
    timestamp: float
    instrument: str
    version: str = "WSS_v2.0"
    
    # ========== 双层编码 ==========
    macro: MacroCode = None
    micro: MicroCode = None
    
    # ========== Regime识别 ==========
    regime_id: Optional[str] = None
    regime_confidence: float = 0.0
    
    # ========== 评分指标 ==========
    novelty_score: float = 0.0
    stability_score: float = 1.0
    danger_index: float = 0.0
    opportunity_index: float = 0.5
    
    # ========== 元数据 ==========
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        """验证数据"""
        assert self.macro is not None, "macro不能为空"
        assert self.micro is not None, "micro不能为空"
        assert 0 <= self.regime_confidence <= 1, "regime_confidence必须在[0,1]"
        assert 0 <= self.novelty_score <= 1, "novelty_score必须在[0,1]"
        assert 0 <= self.stability_score <= 1, "stability_score必须在[0,1]"
        assert 0 <= self.danger_index <= 1, "danger_index必须在[0,1]"
        assert 0 <= self.opportunity_index <= 1, "opportunity_index必须在[0,1]"
    
    @classmethod
    def generate_id(cls) -> str:
        """生成唯一ID"""
        return str(uuid.uuid4())
    
    def to_compact_string(self) -> str:
        """
        紧凑字符串表示
        
        示例: "M:TRD↑|V:HIGH||m:SPRD_W|DI:-0.45||R:R_17(0.82)||N:0.74"
        """
        parts = [
            self.macro.compact_text,
            self.micro.compact_text,
            f"R:{self.regime_id}({self.regime_confidence:.2f})" if self.regime_id else "R:NONE",
            f"N:{self.novelty_score:.2f}"
        ]
        return "||".join(parts)
    
    def to_human_readable(self) -> str:
        """
        人类可读表示
        """
        dt = datetime.fromtimestamp(self.timestamp)
        
        return f"""
╔════════════════════════════════════════════════════════════════╗
║ Market Signature (WSS_v2.0)                                     ║
╠════════════════════════════════════════════════════════════════╣
║ Time:       {dt.strftime('%Y-%m-%d %H:%M:%S')}                            ║
║ Instrument: {self.instrument:<50} ║
║ ID:         {self.id[:36]}  ║
╠════════════════════════════════════════════════════════════════╣
║ 宏观情境 (Macro):                                               ║
║ {', '.join(self.macro.human_tags):<60} ║
╠════════════════════════════════════════════════════════════════╣
║ 微观情境 (Micro):                                               ║
║ {', '.join(self.micro.human_tags):<60} ║
╠════════════════════════════════════════════════════════════════╣
║ Regime: {self.regime_id or 'UNKNOWN':<20} (置信度: {self.regime_confidence:>5.1%})          ║
╠════════════════════════════════════════════════════════════════╣
║ 评分 (Scores):                                                  ║
║ • 新颖度 (Novelty):      {self.novelty_score:>5.1%}                          ║
║ • 稳定度 (Stability):    {self.stability_score:>5.1%}                          ║
║ • 危险指数 (Danger):     {self.danger_index:>5.1%}                          ║
║ • 机会指数 (Opportunity): {self.opportunity_index:>5.1%}                          ║
╚════════════════════════════════════════════════════════════════╝
"""
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'timestamp': self.timestamp,
            'instrument': self.instrument,
            'version': self.version,
            'macro': self.macro.to_dict(),
            'micro': self.micro.to_dict(),
            'regime_id': self.regime_id,
            'regime_confidence': self.regime_confidence,
            'novelty_score': self.novelty_score,
            'stability_score': self.stability_score,
            'danger_index': self.danger_index,
            'opportunity_index': self.opportunity_index,
            'metadata': self.metadata
        }
    
    def to_json(self, indent: int = 2) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WorldSignature_V2':
        """从字典创建"""
        return cls(
            id=data['id'],
            timestamp=data['timestamp'],
            instrument=data['instrument'],
            version=data.get('version', 'WSS_v2.0'),
            macro=MacroCode.from_dict(data['macro']),
            micro=MicroCode.from_dict(data['micro']),
            regime_id=data.get('regime_id'),
            regime_confidence=data.get('regime_confidence', 0.0),
            novelty_score=data.get('novelty_score', 0.0),
            stability_score=data.get('stability_score', 1.0),
            danger_index=data.get('danger_index', 0.0),
            opportunity_index=data.get('opportunity_index', 0.5),
            metadata=data.get('metadata', {})
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'WorldSignature_V2':
        """从JSON字符串创建"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def get_combined_vector(self) -> np.ndarray:
        """
        获取组合向量（Macro + Micro）
        
        用于相似度计算
        """
        return np.concatenate([self.macro.macro_vec, self.micro.micro_vec])
    
    def summary(self) -> Dict:
        """
        获取摘要信息
        
        用于快速查看关键指标
        """
        return {
            'timestamp': datetime.fromtimestamp(self.timestamp).isoformat(),
            'instrument': self.instrument,
            'regime': f"{self.regime_id}({self.regime_confidence:.1%})",
            'macro_summary': ', '.join(self.macro.human_tags[:3]),
            'micro_summary': ', '.join(self.micro.human_tags[:3]),
            'scores': {
                'novelty': f"{self.novelty_score:.1%}",
                'stability': f"{self.stability_score:.1%}",
                'danger': f"{self.danger_index:.1%}",
                'opportunity': f"{self.opportunity_index:.1%}"
            }
        }


def calculate_similarity(sig1: WorldSignature_V2, sig2: WorldSignature_V2) -> Dict:
    """
    计算两个签名的相似度
    
    整合：Tag匹配 + 向量余弦相似度
    
    Returns:
        {
            'overall': float,        # 综合相似度
            'tag_sim': float,        # 标签相似度
            'vec_sim': float,        # 向量相似度
            'macro_sim': float,      # 宏观相似度
            'micro_sim': float       # 微观相似度
        }
    """
    # 1. Tag相似度（Jaccard）
    tags1_macro = set(sig1.macro.human_tags)
    tags2_macro = set(sig2.macro.human_tags)
    
    if len(tags1_macro | tags2_macro) > 0:
        tag_sim_macro = len(tags1_macro & tags2_macro) / len(tags1_macro | tags2_macro)
    else:
        tag_sim_macro = 0.0
    
    tags1_micro = set(sig1.micro.human_tags)
    tags2_micro = set(sig2.micro.human_tags)
    
    if len(tags1_micro | tags2_micro) > 0:
        tag_sim_micro = len(tags1_micro & tags2_micro) / len(tags1_micro | tags2_micro)
    else:
        tag_sim_micro = 0.0
    
    tag_similarity = 0.5 * tag_sim_macro + 0.5 * tag_sim_micro
    
    # 2. 向量相似度（Cosine）
    vec_sim_macro = cosine_similarity(sig1.macro.macro_vec, sig2.macro.macro_vec)
    vec_sim_micro = cosine_similarity(sig1.micro.micro_vec, sig2.micro.micro_vec)
    
    vec_similarity = 0.5 * vec_sim_macro + 0.5 * vec_sim_micro
    
    # 3. 综合相似度（α=0.7, β=0.3）
    α = 0.7  # 向量权重（主要）
    β = 0.3  # 标签权重（辅助）
    
    final_similarity = α * vec_similarity + β * tag_similarity
    
    return {
        'overall': final_similarity,
        'tag_sim': tag_similarity,
        'vec_sim': vec_similarity,
        'macro_sim': vec_sim_macro,
        'micro_sim': vec_sim_micro
    }


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    计算余弦相似度
    
    Args:
        vec1: 向量1
        vec2: 向量2
    
    Returns:
        相似度 [0, 1]
    """
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    similarity = dot_product / (norm1 * norm2)
    
    # 转换到[0, 1]
    similarity = (similarity + 1) / 2
    
    return similarity

