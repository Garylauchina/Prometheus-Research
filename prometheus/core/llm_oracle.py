"""
LLM先知 - Prometheus v4.0
使用大语言模型辅助主脑进行战略决策
"""

from typing import Dict, List, Optional
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class LLMOracle:
    """
    LLM先知 - AI辅助决策系统
    
    职责：
    1. 分析市场数据和系统状态
    2. 提供战略建议
    3. 预测市场趋势
    4. 建议参数调整
    """
    
    def __init__(self, model: str = "gpt-4", api_key: Optional[str] = None):
        """
        初始化LLM先知
        
        Args:
            model: LLM模型名称
            api_key: API密钥
        """
        self.model = model
        self.api_key = api_key
        self.decision_history: List[Dict] = []
        
        logger.info(f"LLM先知已初始化，模型: {model}")
    
    def analyze_market_situation(self,
                                 market_data: Dict,
                                 agent_statistics: Dict,
                                 system_metrics: Dict) -> Dict:
        """
        分析当前市场和系统状况
        
        Args:
            market_data: 市场数据
            agent_statistics: Agent统计数据
            system_metrics: 系统指标
            
        Returns:
            Dict: 分析结果和建议
        """
        # 构建提示词
        prompt = self._build_analysis_prompt(market_data, agent_statistics, system_metrics)
        
        # 调用LLM（这里是接口，需要根据实际LLM服务实现）
        llm_response = self._call_llm(prompt)
        
        # 解析LLM响应
        analysis = self._parse_llm_response(llm_response)
        
        # 记录决策
        self.decision_history.append({
            'timestamp': datetime.now(),
            'prompt': prompt,
            'response': llm_response,
            'analysis': analysis
        })
        
        logger.info(f"LLM分析完成: {analysis.get('summary', 'N/A')}")
        return analysis
    
    def _build_analysis_prompt(self,
                               market_data: Dict,
                               agent_statistics: Dict,
                               system_metrics: Dict) -> str:
        """
        构建LLM分析提示词
        
        Args:
            market_data: 市场数据
            agent_statistics: Agent统计
            system_metrics: 系统指标
            
        Returns:
            str: 提示词
        """
        prompt = f"""
你是Prometheus交易系统的AI先知，负责分析市场和系统状况，提供战略建议。

【市场数据】
{json.dumps(market_data, indent=2, ensure_ascii=False)}

【Agent群体统计】
- 总数量: {agent_statistics.get('total_agents', 0)}
- 平均表现: {agent_statistics.get('avg_performance', 0):.2%}
- 平均适应度: {agent_statistics.get('avg_fitness', 0):.2f}
- 策略多样性: {agent_statistics.get('diversity', 0):.2f}

【系统指标】
- 系统回撤: {system_metrics.get('drawdown', 0):.2%}
- 整体收益: {system_metrics.get('total_return', 0):.2%}
- 风险水平: {system_metrics.get('risk_level', 'N/A')}

请基于以上信息，提供以下分析：

1. 市场状态判断（牛市/熊市/震荡/高波动）
2. 系统健康评估（健康/警告/危急）
3. Agent群体表现分析
4. 建议的策略调整：
   - 资金利用率调整建议
   - 风险等级调整建议
   - 淘汰压力调整建议
   - 环境压力调整建议
5. 预警和注意事项
6. 具体行动建议

请以JSON格式返回，包含以下字段：
{{
    "market_regime": "bull/bear/ranging/volatile",
    "market_confidence": 0.0-1.0,
    "system_health": "healthy/warning/critical",
    "analysis_summary": "简要总结",
    "strategy_adjustments": {{
        "capital_utilization": 0.5-1.0,
        "risk_level": 1-5,
        "selection_pressure": 0.0-1.0,
        "environmental_pressure": 0.0-2.0
    }},
    "warnings": ["警告1", "警告2"],
    "recommendations": ["建议1", "建议2"],
    "reasoning": "详细reasoning"
}}
"""
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """
        调用LLM服务
        
        Args:
            prompt: 提示词
            
        Returns:
            str: LLM响应
        """
        # TODO: 实现实际的LLM调用
        # 这里需要根据使用的LLM服务（OpenAI、Claude、本地模型等）来实现
        
        # 模拟响应（实际使用时需要替换）
        logger.warning("使用模拟LLM响应，请实现实际的LLM调用")
        
        mock_response = {
            "market_regime": "ranging",
            "market_confidence": 0.7,
            "system_health": "healthy",
            "analysis_summary": "市场处于震荡状态，Agent群体表现稳定",
            "strategy_adjustments": {
                "capital_utilization": 0.7,
                "risk_level": 3,
                "selection_pressure": 0.5,
                "environmental_pressure": 1.0
            },
            "warnings": ["部分Agent连续亏损，需要关注"],
            "recommendations": [
                "维持当前策略",
                "适当增加策略多样性"
            ],
            "reasoning": "基于当前市场数据和Agent表现，系统运行正常，无需大幅调整"
        }
        
        return json.dumps(mock_response, ensure_ascii=False)
    
    def _parse_llm_response(self, response: str) -> Dict:
        """
        解析LLM响应
        
        Args:
            response: LLM响应字符串
            
        Returns:
            Dict: 解析后的分析结果
        """
        try:
            analysis = json.loads(response)
            return analysis
        except json.JSONDecodeError as e:
            logger.error(f"LLM响应解析失败: {e}")
            # 返回默认值
            return {
                "market_regime": "unknown",
                "market_confidence": 0.5,
                "system_health": "warning",
                "analysis_summary": "LLM响应解析失败",
                "strategy_adjustments": {
                    "capital_utilization": 0.7,
                    "risk_level": 3,
                    "selection_pressure": 0.5,
                    "environmental_pressure": 1.0
                },
                "warnings": ["LLM分析失败"],
                "recommendations": ["使用默认策略"],
                "reasoning": "LLM响应格式错误"
            }
    
    def get_statistics(self) -> Dict:
        """
        获取LLM先知统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            'model': self.model,
            'total_decisions': len(self.decision_history),
            'last_decision_time': self.decision_history[-1]['timestamp'] if self.decision_history else None
        }


class HumanOracle:
    """
    人工干预 - 人类操作员决策系统
    
    提供人工干预接口，允许操作员直接调整系统参数
    """
    
    def __init__(self):
        """初始化人工干预系统"""
        self.intervention_history: List[Dict] = []
        logger.info("人工干预系统已初始化")
    
    def manual_decision(self,
                       operator_name: str,
                       adjustments: Dict,
                       reason: str) -> Dict:
        """
        人工决策
        
        Args:
            operator_name: 操作员名称
            adjustments: 调整参数
            reason: 干预原因
            
        Returns:
            Dict: 决策结果
        """
        decision = {
            'timestamp': datetime.now(),
            'operator': operator_name,
            'type': 'manual_intervention',
            'adjustments': adjustments,
            'reason': reason
        }
        
        self.intervention_history.append(decision)
        
        logger.info(f"人工干预 by {operator_name}: {reason}")
        logger.info(f"调整参数: {adjustments}")
        
        return decision
    
    def emergency_shutdown(self, operator_name: str, reason: str) -> Dict:
        """
        紧急关闭
        
        Args:
            operator_name: 操作员
            reason: 关闭原因
            
        Returns:
            Dict: 关闭决策
        """
        decision = {
            'timestamp': datetime.now(),
            'operator': operator_name,
            'type': 'emergency_shutdown',
            'reason': reason
        }
        
        self.intervention_history.append(decision)
        
        logger.critical(f"紧急关闭 by {operator_name}: {reason}")
        
        return decision
    
    def get_statistics(self) -> Dict:
        """
        获取人工干预统计
        
        Returns:
            Dict: 统计信息
        """
        return {
            'total_interventions': len(self.intervention_history),
            'intervention_types': {
                'manual': sum(1 for d in self.intervention_history if d['type'] == 'manual_intervention'),
                'emergency': sum(1 for d in self.intervention_history if d['type'] == 'emergency_shutdown')
            },
            'last_intervention': self.intervention_history[-1] if self.intervention_history else None
        }

