# 🚀 Prometheus-Quant v5.0 设置指南

## 📋 执行清单

请按照以下顺序执行：

---

## ✅ Step 1: 提交v4.3并打标签

### 1.1 检查当前状态
```powershell
cd E:\Cursor_store\prometheus-v30
git status
git log --oneline -3
```

### 1.2 确认所有修改已提交
```powershell
# 查看最后一次提交
git show --stat

# 如果显示:
# f995815 fix: 修复基因多样性计算BUG并优化系统输出 (v4.3)
# 则说明v4.3的核心修复已提交，可以打标签
```

### 1.3 创建v4.3.0标签
```powershell
# 在当前分支打标签
git tag -a v4.3.0 -m "v4.3.0 稳定版

核心修复:
- 修复基因多样性计算BUG（0.00 → 0.12+）  
- 修复evolution_manager中Agent列表访问错误

新增功能:
- 每周期显示系统总盈亏（实盈+浮盈）
- 族谱系统基础结构（v5.0准备）

输出优化:
- 修复日志重复输出问题
- Agent排名显示优化（前5+后3）
- 日志量减少约60%

测试验证:
- 已通过722代长时间测试
- 基因多样性稳定在0.12
- 参数解锁机制正常工作
- 盈利比例55.6%"

# 查看标签
git tag -l

# 推送标签到远程
git push origin v4.3.0
```

**预期输出:**
```
Total 3 (delta 2), reused 0 (delta 0)
To https://github.com/Garylauchina/prometheus-v30.git
 * [new tag]         v4.3.0 -> v4.3.0
```

---

## ✅ Step 2: 在GitHub上重命名项目

### 2.1 访问GitHub仓库设置
1. 打开浏览器，访问: https://github.com/Garylauchina/prometheus-v30
2. 点击仓库页面右上角的 **Settings** 标签
3. 在 General → Repository name 中找到 "prometheus-v30"
4. 改为: `Prometheus-Quant`
5. 点击 **Rename** 按钮
6. 确认警告对话框（GitHub会自动重定向旧链接）

### 2.2 更新本地远程地址
```powershell
# 查看当前远程地址
git remote -v

# 更新为新地址
git remote set-url origin https://github.com/Garylauchina/Prometheus-Quant.git

# 验证更新
git remote -v

# 测试连接
git fetch origin
```

**预期输出:**
```
origin  https://github.com/Garylauchina/Prometheus-Quant.git (fetch)
origin  https://github.com/Garylauchina/Prometheus-Quant.git (push)
```

### 2.3 更新项目根目录
```powershell
# 可选：将本地文件夹也重命名
cd E:\Cursor_store
Rename-Item -Path "prometheus-v30" -NewName "Prometheus-Quant"

# 进入新目录
cd E:\Cursor_store\Prometheus-Quant
```

---

## ✅ Step 3: 创建v5.0开发分支

### 3.1 确保在正确的分支
```powershell
# 查看当前分支
git branch

# 确保在develop/v4.0分支
git checkout develop/v4.0

# 拉取最新代码
git pull origin develop/v4.0
```

### 3.2 创建v5.0分支
```powershell
# 基于develop/v4.0创建新分支
git checkout -b develop/v5.0

# 推送到远程
git push origin develop/v5.0

# 设置上游分支
git branch --set-upstream-to=origin/develop/v5.0 develop/v5.0
```

**预期输出:**
```
Switched to a new branch 'develop/v5.0'
Total 0 (delta 0), reused 0 (delta 0)
To https://github.com/Garylauchina/Prometheus-Quant.git
 * [new branch]      develop/v5.0 -> develop/v5.0
Branch 'develop/v5.0' set up to track remote branch 'develop/v5.0' from 'origin'.
```

### 3.3 验证分支设置
```powershell
# 查看所有分支
git branch -a

# 应该看到:
# * develop/v5.0
#   develop/v4.0
#   main
#   remotes/origin/develop/v5.0
#   remotes/origin/develop/v4.0
#   remotes/origin/main
```

---

## ✅ Step 4: 提交v5.0初始文件

### 4.1 查看新文件
```powershell
git status
```

**应该看到:**
```
Untracked files:
  docs/V5.0_DEVELOPMENT_PLAN.md
  prometheus/core/genealogy.py
  SETUP_V5.0.md
```

### 4.2 提交到v5.0分支
```powershell
# 添加文件
git add docs/V5.0_DEVELOPMENT_PLAN.md
git add prometheus/core/genealogy.py
git add SETUP_V5.0.md

# 提交
git commit -m "feat: 初始化v5.0开发 - 族谱系统基础

v5.0 核心功能规划:
1. 族谱系统（生殖隔离）
2. 基因多样性主动管理
3. 高级风控系统（夏普比率、最大回撤、VaR）
4. 先知期权监控

本次提交:
- 添加v5.0开发计划文档
- 实现GenealogyTree核心类（族谱系统）
- 实现AgentGenealogy和Family数据结构
- 实现亲缘系数计算算法
- 实现生殖隔离检查机制
- 添加v5.0设置指南

测试状态:
- 族谱系统单元测试通过
- 亲缘系数计算验证通过
- 生殖隔离逻辑验证通过

下一步:
- 集成族谱系统到evolution_manager
- 实现DiversityManager
- 编写单元测试"

# 推送到远程
git push origin develop/v5.0
```

---

## ✅ Step 5: 验证设置

### 5.1 检查GitHub
访问: https://github.com/Garylauchina/Prometheus-Quant

应该看到:
- [x] 仓库名已更改为 Prometheus-Quant
- [x] 有 v4.3.0 标签（在 Releases 页面）
- [x] 有 develop/v5.0 分支
- [x] develop/v5.0 分支包含新文件

### 5.2 检查本地分支
```powershell
# 查看当前分支
git branch

# 查看标签
git tag -l

# 查看提交历史
git log --oneline --graph --all -10
```

---

## 🎯 下一步工作

设置完成后，开始v5.0开发：

### 今天完成:
- [x] 创建v5.0开发计划
- [x] 实现族谱系统核心模块
- [x] 提交到v5.0分支

### 明天开始:
1. **集成族谱系统到evolution_manager**
   ```python
   # 在evolution_manager中添加:
   from prometheus.core.genealogy import GenealogyTree
   
   self.genealogy_tree = GenealogyTree(max_kinship=0.125)
   ```

2. **修改_select_parent方法**
   ```python
   def _select_parent(self, rankings, exclude_id=None):
       # 原有逻辑...
       
       # 添加生殖隔离检查
       while attempts < 10:
           candidate = self._weighted_select(rankings)
           if self.genealogy_tree.can_mate(parent1_id, candidate_id):
               return candidate
           attempts += 1
   ```

3. **在Agent创建时更新族谱**
   ```python
   # 在run_evolution_cycle中:
   self.genealogy_tree.add_agent(
       new_agent_id,
       parent1_id,
       parent2_id,
       generation,
       birth_time=cycle_count
   )
   ```

---

## 📊 v5.0 开发进度

### Week 1-2: 族谱系统
- [x] Day 1: 核心数据结构和算法（已完成）
- [ ] Day 2-3: 集成到evolution_manager
- [ ] Day 4-5: 单元测试和验证
- [ ] Day 6-7: 性能优化和文档

### Week 3: 基因多样性管理
- [ ] 实现DiversityManager
- [ ] 多样性评估算法
- [ ] 干预机制

### Week 4-5: 高级风控系统
- [ ] 实现风控指标计算
- [ ] 集成到Supervisor报告
- [ ] 可视化输出

### Week 6-7: 期权监控
- [ ] OptionsMonitor接口
- [ ] 数据获取和分析
- [ ] 集成到Mastermind

---

## ⚠️ 注意事项

1. **v4.0分支保持稳定**: 
   - 如果发现v4.3有bug，在 `develop/v4.0` 分支修复
   - 然后合并到 `develop/v5.0`

2. **增量提交**:
   - 每个功能完成后立即提交
   - 提交信息格式: `feat: 功能描述` 或 `fix: 修复描述`

3. **测试先行**:
   - 每个新功能都应有单元测试
   - 在 `tests/` 目录下创建对应测试文件

---

## 🎉 恭喜！

您已经完成了v5.0的初始设置！

- ✅ v4.3.0 已标记为稳定版
- ✅ 项目已重命名为 Prometheus-Quant
- ✅ develop/v5.0 分支已创建
- ✅ 族谱系统核心模块已实现

**准备开始v5.0的激动人心的开发之旅！** 🚀

---

*最后更新: 2025-12-04*
*版本: 1.0*

