# ✅ Windows → MAC 转移检查清单

> **目标**：确保平滑转移，无遗漏
> 
> **日期**：2025-12-05

---

## 📋 Windows端（提交前）

### **代码提交**
- [ ] 运行 `git status` 确认所有修改
- [ ] 运行 `test_fitness_v2.py` 确认测试通过
- [ ] 运行 `test_evolution_with_fitness_v2.py` 确认测试通过
- [ ] 确认所有重要文档已创建：
  - [ ] `MAC_HANDOVER.md`
  - [ ] `PROJECT_CURRENT_STATUS.md`
  - [ ] `SETUP_MAC.md`
  - [ ] `TRANSFER_CHECKLIST.md`
  - [ ] `V5.2_FITNESS_UPGRADE_COMPLETE.md`

### **Git操作**
- [ ] `git add .`
- [ ] `git commit -m "..."`（使用完整的commit message）
- [ ] `git push origin main`
- [ ] 确认GitHub上能看到最新提交

---

## 🍎 MAC端（设置时）

### **环境准备**
- [ ] Python 3.10+ 已安装
- [ ] Git 已安装
- [ ] Homebrew 已安装（可选但推荐）

### **项目克隆**
- [ ] 克隆仓库到MAC：`git clone https://github.com/Garylauchina/Prometheus-Quant.git`
- [ ] 进入项目目录：`cd prometheus-v30`
- [ ] 切换到开发分支：`git checkout develop/v5.0`
- [ ] 确认分支正确：`git branch`（应该显示 * develop/v5.0）

### **Python环境**
- [ ] 创建虚拟环境：`python3 -m venv venv`
- [ ] 激活虚拟环境：`source venv/bin/activate`
- [ ] 升级pip：`pip install --upgrade pip`
- [ ] 安装依赖：`pip install -r requirements.txt`

### **验证测试**
- [ ] 运行 `python test_fitness_v2.py`
- [ ] 运行 `python test_evolution_with_fitness_v2.py`
- [ ] 两个测试都成功通过

### **Cursor设置**
- [ ] 在Cursor中打开项目文件夹
- [ ] 打开 `MAC_HANDOVER.md` 作为上下文
- [ ] 打开 `PROJECT_CURRENT_STATUS.md` 作为参考
- [ ] 确认Cursor AI能够读取这些文档

---

## 📝 文档阅读（按顺序）

在开始开发前，建议阅读：

1. - [ ] `SETUP_MAC.md` - 环境设置
2. - [ ] `MAC_HANDOVER.md` - 完整交接文档（**最重要**）
3. - [ ] `PROJECT_CURRENT_STATUS.md` - 当前状态
4. - [ ] `V5.2_FITNESS_UPGRADE_COMPLETE.md` - Fitness升级
5. - [ ] `FEAR_EXPERIMENT_SUMMARY.md` - Fear实验

---

## 🔍 理解确认

在开始Day 3开发前，确认你理解：

- [ ] v5.2 Fitness系统的6个维度
- [ ] 为什么移除自杀机制
- [ ] fear_of_death作为可变基因的实现
- [ ] Daimon的动态fear_threshold
- [ ] 消极惩罚的触发条件
- [ ] 为什么消极者排名高于激进者（单场景）
- [ ] 为什么消极策略在真实进化中不会扩散

---

## 🎯 准备开始Day 3

确认以下项目都已完成：

- [ ] MAC环境设置完成
- [ ] 所有测试通过
- [ ] 文档已阅读
- [ ] 理解最近的设计决策
- [ ] 知道Day 3的目标（Lineage熵监控优化）

---

## 📞 应急联系信息

如果遇到问题，参考：

- **环境问题**：`SETUP_MAC.md` 的"常见问题"部分
- **项目理解**：`MAC_HANDOVER.md` 的"关键信息快速查询"
- **设计决策**：`V5.2_FITNESS_UPGRADE_COMPLETE.md`

---

## ✅ 全部完成！

当所有checkbox都被勾选后，你就可以开始Day 3开发了！

**下一步**：Day 3 - Lineage熵监控优化

---

*最后更新：2025-12-05*

