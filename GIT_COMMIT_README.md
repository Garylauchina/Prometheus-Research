# Git提交脚本使用说明

## 📦 可用脚本

### 1. PowerShell版本（推荐）
**文件**: `git_commit_v5.1.ps1`

**特点**:
- ✅ 彩色输出
- ✅ 详细进度显示
- ✅ 文件存在性检查
- ✅ 交互式确认

**使用方法**:
```powershell
# 方法1：直接运行
.\git_commit_v5.1.ps1

# 方法2：如果遇到执行策略限制
powershell -ExecutionPolicy Bypass -File .\git_commit_v5.1.ps1
```

### 2. 批处理版本（简化）
**文件**: `git_commit_v5.1.bat`

**特点**:
- ✅ 简单直接
- ✅ 无依赖
- ✅ 双击即可运行

**使用方法**:
```cmd
# 方法1：双击运行
直接双击 git_commit_v5.1.bat

# 方法2：命令行
git_commit_v5.1.bat
```

---

## 📋 提交内容

脚本将按顺序执行4次提交：

### 第1次提交：核心功能
```
feat: v5.1核心功能实现

包含文件：
- prometheus/core/slippage_model.py
- prometheus/core/funding_rate_model.py
- prometheus/core/meta_genome.py
- prometheus/core/niche_protection.py
- prometheus/core/mastermind.py
- prometheus/core/agent_v5.py
- prometheus/core/inner_council.py
- prometheus/core/evolution_manager_v5.py
```

### 第2次提交：测试脚本
```
test: 添加v5.1完整测试套件

包含文件：
- test_slippage.py
- test_funding_rate.py
- test_meta_genome.py
- test_meta_evolution.py
- test_niche_protection.py
- test_mastermind_pressure.py
- test_complete_pressure.py
- test_v5_integration.py
- test_extreme_stress.py
```

### 第3次提交：工具和数据
```
feat: 添加历史数据下载工具

包含文件：
- tools/*
- data/okx/*.json（仅元数据）
```

### 第4次提交：文档
```
docs: v5.1完整文档

包含文件：
- docs/V5.1_UPGRADE_GUIDE.md
- docs/SLIPPAGE_INTEGRATION.md
- CHANGELOG_V5.1.md
- PROJECT_STATUS_V5.1.md
- TODO_TOMORROW.md
- DAILY_LOG_2025-12-05.md
```

---

## ⚠️ 注意事项

### 1. 执行前检查
```powershell
# 查看当前状态
git status

# 查看当前分支
git branch

# 查看远程仓库
git remote -v
```

### 2. 大文件处理
脚本**不会提交**以下大文件：
- `data/okx/*.csv` (CSV数据文件)
- `data/okx/*.parquet` (Parquet数据文件)

只会提交：
- `data/okx/*.json` (元数据文件)

如果需要提交数据文件，请手动添加：
```powershell
git add data/okx/*.csv
git commit -m "data: 添加历史数据"
```

### 3. 推送到远程
脚本最后会询问是否推送到远程仓库。

如果选择"否"，稍后可手动推送：
```powershell
git push
```

---

## 🔧 常见问题

### Q1: PowerShell脚本无法运行
**错误**: "因为在此系统上禁止运行脚本..."

**解决**:
```powershell
# 临时允许（推荐）
powershell -ExecutionPolicy Bypass -File .\git_commit_v5.1.ps1

# 或永久修改策略（需要管理员权限）
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Q2: 某些文件未找到
**现象**: 显示"⚠️ 未找到: xxx"

**原因**: 文件不存在或路径不对

**解决**: 这是正常的，脚本会跳过不存在的文件

### Q3: 提交失败
**错误**: "fatal: pathspec 'xxx' did not match any files"

**原因**: Git索引中没有该文件

**解决**:
```powershell
# 查看哪些文件被追踪
git ls-files

# 手动添加缺失的文件
git add <filename>
```

### Q4: 推送失败
**错误**: "error: failed to push some refs..."

**原因**: 远程仓库有新的提交

**解决**:
```powershell
# 先拉取远程更新
git pull --rebase

# 再推送
git push
```

---

## 📝 手动提交（备选）

如果脚本无法使用，可以手动执行：

```powershell
# 1. 核心功能
git add prometheus/core/slippage_model.py prometheus/core/funding_rate_model.py prometheus/core/meta_genome.py prometheus/core/niche_protection.py
git commit -m "feat: v5.1核心功能实现"

# 2. 测试脚本
git add test_*.py
git commit -m "test: 添加v5.1完整测试套件"

# 3. 工具和数据
git add tools/
git commit -m "feat: 添加历史数据下载工具"

# 4. 文档
git add docs/ CHANGELOG_V5.1.md PROJECT_STATUS_V5.1.md TODO_TOMORROW.md DAILY_LOG_2025-12-05.md
git commit -m "docs: v5.1完整文档"

# 5. 推送
git push
```

---

## 🎯 最佳实践

### 提交前
1. ✅ 确保所有测试通过
2. ✅ 检查代码无语法错误
3. ✅ 查看`git status`确认文件
4. ✅ 确认当前在正确的分支

### 提交后
1. ✅ 检查提交历史：`git log`
2. ✅ 验证推送成功：`git log origin/main..HEAD`
3. ✅ 在远程仓库查看提交

---

## 📊 提交统计

执行脚本后，将创建4次提交：

```
📦 v5.1完整提交
├─ feat: 核心功能 (~8文件)
├─ test: 测试套件 (~9文件)
├─ feat: 工具数据 (~5文件)
└─ docs: 完整文档 (~6文件)

总计：~28个文件
代码量：~5,000行
```

---

## 🆘 需要帮助？

遇到问题请：
1. 查看本文档的"常见问题"部分
2. 执行`git status`检查状态
3. 查看错误信息
4. 使用手动提交方式

---

**祝提交顺利！** 🎉

*最后更新：2025-12-05*

