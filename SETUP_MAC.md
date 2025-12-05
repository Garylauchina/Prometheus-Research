# 🍎 MAC环境快速设置指南

> **目标**：5分钟内在MAC上完成Prometheus v5.2环境搭建
> 
> **前置要求**：MAC电脑，已安装Homebrew和Git

---

## 📦 快速设置（5步）

### **步骤1：安装Python 3.10+**

```bash
# 检查Python版本
python3 --version

# 如果版本 < 3.10，安装最新版本
brew install python@3.10
```

---

### **步骤2：克隆项目**

```bash
# 进入工作目录
cd ~/Projects  # 或你喜欢的目录

# 克隆仓库
git clone https://github.com/Garylauchina/Prometheus-Quant.git prometheus-v30

# 进入项目目录
cd prometheus-v30

# ⚠️ 重要：切换到 develop/v5.0 分支
git checkout develop/v5.0
```

---

### **步骤3：创建虚拟环境**

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 你应该看到命令提示符前面出现 (venv)
```

---

### **步骤4：安装依赖**

```bash
# 升级pip（可选但推荐）
pip install --upgrade pip

# 安装所有依赖
pip install -r requirements.txt

# 等待安装完成（可能需要1-2分钟）
```

---

### **步骤5：验证安装**

```bash
# 运行Fitness对比测试
python test_fitness_v2.py

# 预期输出：
# ✅ 稳健者、激进者、消极者模拟完成
# ✅ Fitness排名显示
# ✅ 无错误

# 运行真实进化测试（可选，需要2-3分钟）
python test_evolution_with_fitness_v2.py

# 预期输出：
# ✅ 10轮进化完成
# ✅ 前5名和后5名Agent信息显示
# ✅ 系统稳定运行
```

---

## ✅ 设置完成！

如果两个测试都成功运行，恭喜你！环境设置完成！

---

## 🔧 常用命令

### **虚拟环境管理**

```bash
# 激活虚拟环境（每次打开新终端都需要）
source venv/bin/activate

# 退出虚拟环境
deactivate
```

### **运行测试**

```bash
# 确保虚拟环境已激活
source venv/bin/activate

# Fitness对比测试
python test_fitness_v2.py

# 真实进化测试
python test_evolution_with_fitness_v2.py

# Daimon改进测试
python test_daimon_improvement.py
```

### **Git操作**

```bash
# 查看当前状态
git status

# 拉取最新代码
git pull origin main

# 查看提交历史
git log --oneline -10
```

---

## 🎯 在Cursor中开始工作

### **1. 打开项目**

```bash
# 打开Cursor（如果已安装）
open -a Cursor .

# 或者手动打开Cursor，然后 File -> Open Folder -> 选择 prometheus-v30
```

### **2. 在Cursor中打开关键文件**

建议先打开这些文件，作为上下文参考：

1. `MAC_HANDOVER.md` - 交接文档（**最重要**）
2. `PROJECT_CURRENT_STATUS.md` - 当前状态
3. `V5.2_FITNESS_UPGRADE_COMPLETE.md` - Fitness升级文档
4. `prometheus/core/agent_v5.py` - Agent核心
5. `prometheus/core/evolution_manager_v5.py` - 进化管理

### **3. 第一条指令给Cursor AI**

```
你好！我刚把项目从Windows转移到MAC。

请先阅读：
1. MAC_HANDOVER.md（交接文档）
2. PROJECT_CURRENT_STATUS.md（当前状态）

然后确认你了解：
- v5.2 Fitness系统升级（刚完成）
- 移除自杀机制的设计决策
- 待办事项（Day 3-7）

准备好后，我们讨论Day 3的开发计划。
```

---

## 🐛 常见问题

### **问题1：`python3: command not found`**

**解决方案**：
```bash
# 安装Python 3
brew install python@3.10

# 验证安装
python3 --version
```

### **问题2：`pip install` 失败**

**解决方案**：
```bash
# 升级pip
pip install --upgrade pip

# 如果还是失败，尝试使用清华镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### **问题3：虚拟环境激活失败**

**解决方案**：
```bash
# 确保你在项目目录
pwd  # 应该显示 .../prometheus-v30

# 重新创建虚拟环境
rm -rf venv
python3 -m venv venv
source venv/bin/activate
```

### **问题4：测试运行失败**

**解决方案**：
```bash
# 确保虚拟环境已激活
source venv/bin/activate

# 确保依赖已安装
pip install -r requirements.txt

# 检查Python版本
python --version  # 应该是 3.10+

# 再次运行测试
python test_fitness_v2.py
```

---

## 📚 下一步阅读

设置完成后，建议按以下顺序阅读文档：

1. ✅ `SETUP_MAC.md` - 你在这里
2. 📖 `MAC_HANDOVER.md` - 完整交接文档
3. 📖 `PROJECT_CURRENT_STATUS.md` - 当前状态快照
4. 📖 `V5.2_FITNESS_UPGRADE_COMPLETE.md` - Fitness升级详情
5. 📖 `FEAR_EXPERIMENT_SUMMARY.md` - Fear实验总结

---

## 🚀 准备就绪！

环境设置完成后，你就可以开始Day 3的开发了！

**Day 3目标**：Lineage熵监控优化

祝开发顺利！🎉

---

*最后更新：2025-12-05*

