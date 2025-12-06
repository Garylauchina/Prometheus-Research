"""
RegimeLibrary - Regime聚类和匹配

功能：
1. 从历史签名中聚类出Regime
2. 实时匹配当前签名到最近的Regime
3. Regime统计和分析
"""

from typing import List, Dict, Tuple, Optional
from collections import Counter
import numpy as np
import logging
import pickle
from pathlib import Path

logger = logging.getLogger(__name__)


class RegimeLibrary:
    """
    Regime库：聚类历史签名
    
    使用HDBSCAN或GMM聚类宏观向量
    """
    
    def __init__(self):
        self.regimes = {}  # regime_id -> RegimeInfo
        self.cluster_model = None
        self.pca_model = None
    
    def build_from_history(
        self,
        historical_signatures: List['WorldSignature_V2'],
        min_cluster_size: int = 50,
        min_samples: int = 10
    ):
        """
        从历史签名中聚类出Regime
        
        使用HDBSCAN聚类
        
        Args:
            historical_signatures: 历史签名列表
            min_cluster_size: 最小聚类大小
            min_samples: 最小样本数
        """
        if len(historical_signatures) < min_cluster_size:
            logger.warning(f"历史数据不足({len(historical_signatures)}个)，需要至少{min_cluster_size}个")
            return
        
        logger.info(f"开始从{len(historical_signatures)}个历史签名中聚类...")
        
        # 1. 提取所有宏观向量
        macro_vecs = np.array([sig.macro.macro_vec for sig in historical_signatures])
        
        logger.info(f"提取了{len(macro_vecs)}个宏观向量，维度={macro_vecs.shape[1]}")
        
        # 2. 降维（可选，如果维度>50）
        if macro_vecs.shape[1] > 50:
            try:
                from sklearn.decomposition import PCA
                self.pca_model = PCA(n_components=32)
                reduced_vecs = self.pca_model.fit_transform(macro_vecs)
                logger.info(f"PCA降维: {macro_vecs.shape[1]} → {reduced_vecs.shape[1]}")
            except ImportError:
                logger.warning("sklearn未安装，跳过PCA降维")
                reduced_vecs = macro_vecs
        else:
            reduced_vecs = macro_vecs
        
        # 3. 聚类
        try:
            import hdbscan
            self.cluster_model = hdbscan.HDBSCAN(
                min_cluster_size=min_cluster_size,
                min_samples=min_samples,
                metric='euclidean'
            )
            labels = self.cluster_model.fit_predict(reduced_vecs)
            logger.info("使用HDBSCAN聚类")
        except ImportError:
            logger.warning("hdbscan未安装，使用KMeans聚类")
            try:
                from sklearn.cluster import KMeans
                n_clusters = max(5, len(historical_signatures) // 200)
                self.cluster_model = KMeans(n_clusters=n_clusters, random_state=42)
                labels = self.cluster_model.fit_predict(reduced_vecs)
            except ImportError:
                logger.error("sklearn未安装，无法聚类")
                return
        
        # 4. 为每个cluster创建Regime
        unique_labels = set(labels)
        logger.info(f"发现{len(unique_labels)}个cluster")
        
        for label_id in unique_labels:
            if label_id == -1:  # 噪声点
                continue
            
            # 找到该cluster的所有签名
            cluster_mask = labels == label_id
            cluster_sigs = [sig for sig, mask in zip(historical_signatures, cluster_mask) if mask]
            
            if len(cluster_sigs) == 0:
                continue
            
            # 计算centroid
            centroid_vec = np.mean([sig.macro.macro_vec for sig in cluster_sigs], axis=0)
            
            # 找最代表性的tags
            all_tags = []
            for sig in cluster_sigs:
                all_tags.extend(sig.macro.human_tags)
            representative_tags = Counter(all_tags).most_common(5)
            
            # 统计该regime的特征
            regime_id = f"R_{label_id}"
            self.regimes[regime_id] = {
                'id': regime_id,
                'centroid_vec': centroid_vec,
                'representative_tags': [tag for tag, count in representative_tags],
                'member_count': len(cluster_sigs),
                'example_timestamps': [sig.timestamp for sig in cluster_sigs[:5]],
                'avg_danger': np.mean([sig.danger_index for sig in cluster_sigs]),
                'avg_opportunity': np.mean([sig.opportunity_index for sig in cluster_sigs]),
                'avg_stability': np.mean([sig.stability_score for sig in cluster_sigs])
            }
            
            logger.info(f"✅ {regime_id}: {len(cluster_sigs)}个成员, tags={representative_tags[:3]}")
        
        logger.info(f"✅ Regime库建立完成：{len(self.regimes)}个Regime")
    
    def match_regime(self, signature: 'WorldSignature_V2') -> Tuple[Optional[str], float]:
        """
        匹配当前签名到最近的Regime
        
        Args:
            signature: 当前签名
        
        Returns:
            (regime_id, confidence)
        """
        if not self.regimes:
            return None, 0.0
        
        # 计算与每个Regime centroid的相似度
        similarities = {}
        for regime_id, regime_info in self.regimes.items():
            sim = self._cosine_similarity(
                signature.macro.macro_vec,
                regime_info['centroid_vec']
            )
            similarities[regime_id] = sim
        
        # 找最相似的
        best_regime_id = max(similarities.items(), key=lambda x: x[1])
        
        return best_regime_id[0], best_regime_id[1]
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        # 转换到[0, 1]
        similarity = (similarity + 1) / 2
        
        return similarity
    
    def get_regime_info(self, regime_id: str) -> Optional[Dict]:
        """获取Regime信息"""
        return self.regimes.get(regime_id)
    
    def get_all_regimes(self) -> Dict:
        """获取所有Regime"""
        return self.regimes
    
    def save(self, filepath: str):
        """保存Regime库到文件"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'wb') as f:
            pickle.dump({
                'regimes': self.regimes,
                'cluster_model': self.cluster_model,
                'pca_model': self.pca_model
            }, f)
        
        logger.info(f"✅ Regime库已保存: {filepath}")
    
    def load(self, filepath: str):
        """从文件加载Regime库"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        self.regimes = data['regimes']
        self.cluster_model = data.get('cluster_model')
        self.pca_model = data.get('pca_model')
        
        logger.info(f"✅ Regime库已加载: {filepath}, {len(self.regimes)}个Regime")
    
    def summary(self) -> str:
        """打印Regime库摘要"""
        if not self.regimes:
            return "Regime库为空"
        
        lines = [
            f"╔════════════════════════════════════════════════════════════════╗",
            f"║ Regime库摘要                                                    ║",
            f"╠════════════════════════════════════════════════════════════════╣",
            f"║ 总Regime数: {len(self.regimes):<50} ║",
            f"╠════════════════════════════════════════════════════════════════╣"
        ]
        
        for regime_id, info in sorted(self.regimes.items()):
            lines.append(f"║ {regime_id}                                                          ║")
            lines.append(f"║   成员数: {info['member_count']:<53} ║")
            lines.append(f"║   代表tags: {', '.join(info['representative_tags'][:3]):<48} ║")
            lines.append(f"║   平均危险: {info['avg_danger']:.1%}  机会: {info['avg_opportunity']:.1%}  稳定: {info['avg_stability']:.1%}                ║")
            lines.append(f"╠════════════════════════════════════════════════════════════════╣")
        
        lines.append(f"╚════════════════════════════════════════════════════════════════╝")
        
        return "\n".join(lines)

