# 📚 Prometheus v6.0 文档中心

v6.0-Stage1的所有核心文档集中在这里。

---

## 🌟 必读文档

### 1. Stage 1黄金规则 ⭐⭐⭐
**文件**: [STAGE1_GOLDEN_RULES.md](STAGE1_GOLDEN_RULES.md)

**内容**：
- 极简市场环境的10条黄金规则
- 为什么这些规则是对的（基于复杂系统理论）
- 当前实现状态评分（70%）
- Stage 1的核心目标

**为什么必读**：这是v6.0的理论基础和设计指南。

---

### 2. Stage 1实施计划 ⭐⭐⭐
**文件**: [STAGE1_IMPLEMENTATION_PLAN.md](STAGE1_IMPLEMENTATION_PLAN.md)

**内容**：
- 完整的实施计划（3个Phase，7个Task）
- 详细的验收标准
- 时间线和优先级
- 成功指标

**为什么必读**：这是v6.0的行动指南。

---

### 3. v6.0架构文档 ⭐⭐
**文件**: [V6_ARCHITECTURE.md](V6_ARCHITECTURE.md)

**内容**：
- v6.0的完整架构设计
- 核心模块说明
- 数据流向
- 四层智能架构

**为什么重要**：理解系统设计。

---

## 🔍 深度分析

### 相似度匹配架构
**文件**: [SIMILARITY_ARCHITECTURE_V6.md](SIMILARITY_ARCHITECTURE_V6.md)

**内容**：
- Prophet如何匹配历史基因
- 加权欧氏距离 vs 余弦相似度
- 为什么选择加权欧氏距离（0.755 → 0.179）
- 误匹配防护

---

### 相似度计算详解
**文件**: [WORLDSIGNATURE_SIMILARITY.md](WORLDSIGNATURE_SIMILARITY.md)

**内容**：
- WorldSignature相似度的计算细节
- 数学公式和实现
- 性能分析（300条记录<20ms）
- 优化建议

---

### WorldSignature分析
**文件**: [WORLDSIGNATURE_ANALYSIS.md](WORLDSIGNATURE_ANALYSIS.md)

**内容**：
- WorldSignature的14个维度
- 各维度的含义和作用
- 牛市/熊市/震荡市的特征
- 数据有效性验证

---

## 📊 实战报告

### 基因收集成功报告
**文件**: [GENE_COLLECTION_SUCCESS.md](GENE_COLLECTION_SUCCESS.md)

**内容**：
- 1000周期训练成功
- 300条基因积累
- 进化收敛速度（0-1代）
- 牛市ROI 28%+

---

### 基因深度分析
**文件**: [GENE_ANALYSIS_DEEP_DIVE.md](GENE_ANALYSIS_DEEP_DIVE.md)

**内容**：
- Top基因的参数分析
- 牛市基因：directional_bias → 1.0
- 熊市基因：directional_bias → 0.22
- 震荡市基因多样性

---

### 稳定性 vs 性能
**文件**: [STABILITY_VS_PERFORMANCE.md](STABILITY_VS_PERFORMANCE.md)

**内容**：
- 高ROI vs 高稳定性（重复出现频率）
- 为什么重复不是bug而是稳定性指标
- 如何利用稳定性指标

---

## 🐛 问题修复

### 关键Bug修复记录
**文件**: [CRITICAL_BUG_FIX_V6_EVOLUTION.md](CRITICAL_BUG_FIX_V6_EVOLUTION.md)

**内容**：
- breeding_tax_rate参数bug
- 如何发现和修复
- 修复后的效果（1000周期成功）

---

### 税收机制总结
**文件**: [TAX_MECHANISM_V6_SUMMARY.md](TAX_MECHANISM_V6_SUMMARY.md)

**内容**：
- v6.0的税收机制设计
- 20%资金池目标
- 动态税率（0% or 10%）
- 为什么选择极简设计

---

## 📅 进度记录

### Week 1 进度
**文件**: [WEEK1_DAY1-2_PROGRESS.md](WEEK1_DAY1-2_PROGRESS.md), [WEEK1_DAY3-5_PROGRESS.md](WEEK1_DAY3-5_PROGRESS.md)

**内容**：
- 第一周的开发进度
- 遇到的问题和解决方案
- 重要决策记录

---

## 🧹 其他文档

### 清理计划
**文件**: [V6_CLEANUP_PLAN.md](V6_CLEANUP_PLAN.md)

**内容**：
- 代码库清理方案
- 目录结构重组
- 90+个旧测试归档

---

### Prophet实施总结
**文件**: [PROPHET_IMPLEMENTATION_SUMMARY.md](PROPHET_IMPLEMENTATION_SUMMARY.md)

**内容**：
- Prophet的实现过程
- 关键决策
- 遇到的挑战

---

## 📖 阅读路线

### 新手路线
```
1. STAGE1_GOLDEN_RULES.md（理解理论）
2. V6_ARCHITECTURE.md（理解架构）
3. STAGE1_IMPLEMENTATION_PLAN.md（理解计划）
4. GENE_COLLECTION_SUCCESS.md（看实战效果）
5. 开始使用（../examples/）
```

### 深入研究路线
```
1. SIMILARITY_ARCHITECTURE_V6.md（相似度匹配）
2. WORLDSIGNATURE_ANALYSIS.md（市场特征）
3. GENE_ANALYSIS_DEEP_DIVE.md（基因分析）
4. STABILITY_VS_PERFORMANCE.md（稳定性分析）
5. 查看源码（../../prometheus/）
```

### 问题排查路线
```
1. CRITICAL_BUG_FIX_V6_EVOLUTION.md（看已知bug）
2. TAX_MECHANISM_V6_SUMMARY.md（理解税收）
3. 运行诊断（../examples/diagnose_agent_behavior.py）
4. 查看测试（../tests/）
```

---

## 🎯 快速索引

### 按主题查找

**架构设计**：
- V6_ARCHITECTURE.md
- SIMILARITY_ARCHITECTURE_V6.md

**理论基础**：
- STAGE1_GOLDEN_RULES.md

**实施指南**：
- STAGE1_IMPLEMENTATION_PLAN.md
- V6_CLEANUP_PLAN.md

**实战分析**：
- GENE_COLLECTION_SUCCESS.md
- GENE_ANALYSIS_DEEP_DIVE.md
- WORLDSIGNATURE_ANALYSIS.md

**问题修复**：
- CRITICAL_BUG_FIX_V6_EVOLUTION.md
- TAX_MECHANISM_V6_SUMMARY.md

**进度记录**：
- WEEK1_DAY1-2_PROGRESS.md
- WEEK1_DAY3-5_PROGRESS.md

---

## 📝 文档约定

### 文档标记

- ⭐ 核心必读
- ⭐⭐ 重要推荐
- ⭐⭐⭐ 必读必会

### 更新规则

- 每个重大变更都有文档
- Bug修复都有记录
- 关键决策都有说明

---

## 🚀 下一步

### v6.1-Stage1.1（计划中）

将新增文档：
- STAGE1.1_MARKET_GENERATOR.md（结构切换市场）
- STAGE1.1_SLIPPAGE.md（固定滑点）
- STAGE1.1_PROFIT_FACTOR.md（PF为主导）

### v6.2-Stage2（未来）

将新增文档：
- STAGE2_REGIME_SWITCHING.md
- STAGE2_PROPHET_SCHEDULING.md
- STAGE2_PORTFOLIO_MANAGEMENT.md

---

## 💡 贡献指南

添加新文档时：
1. 使用清晰的文件名
2. 添加到本README索引
3. 在相关文档中交叉引用
4. 遵循Markdown格式规范

---

## 🙏 致谢

这些文档记录了v6.0从理论到实践的完整过程，基于：
- 复杂系统科学
- AlphaZero方法论
- 生物进化理论
- 大量实战验证

感谢所有贡献者！

