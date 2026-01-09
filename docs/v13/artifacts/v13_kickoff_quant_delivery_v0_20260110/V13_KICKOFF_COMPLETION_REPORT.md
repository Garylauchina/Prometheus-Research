# V13 Kickoff Completion Report — 2026-01-10

**Status**: ✅ Code ready, waiting for VPS deployment  
**Quant Branch**: `v13_trial12_live_recorder_v0_20260110`  
**Commit**: `a360c21b8729a3a64f5afe1a859a52c12a49e461`  

---

## ✅ 已完成工作

### 1. V13 分支创建
- ✅ 从 `main` 创建新分支 `v13_trial12_live_recorder_v0_20260110`
- ✅ 代码已推送到 GitHub

### 2. V13 文档学习
- ✅ 阅读 V13 SSOT One-Page
- ✅ 阅读 V13 Capture Window Minimal Contract
- ✅ 理解核心理念：
  - 接受世界沉默/拒绝/漂移为一级输出
  - `NOT_MEASURABLE` 是有效裁决，不是工程失败
  - 禁止 proxy 进入裁决层（无合成世界证据）

### 3. V13 Recorder 实现
**文件**: `tools/v13/run_realtime_orderbook_trades_recorder_v13.py`

**V13 Capture Window 协议（冻结合同）**：
- ✅ `window.meta.yaml` - 窗口元数据（window_id, start_ts, end_ts, observation_mode, connection_status_summary）
- ✅ `phenomena.log.md` - 观测到的事实（仅事实，无分析）
- ✅ `verdict.md` - 单词裁决（`MEASURABLE`/`NOT_MEASURABLE`/`INTERRUPTED`/`REJECTED_BY_WORLD`）

**核心功能**：
- ✅ OKX WebSocket books5 (order-book L1 bid/ask) 收集
- ✅ OKX WebSocket trades 收集
- ✅ 自动重连机制
- ✅ 自动 phenomena 记录（prolonged silence, reconnects）
- ✅ Verdict 自动判定（基于数据充足性）

**关键设计**：
- Window files 在 recorder 启动时初始化
- `verdict.md` 初始为 `INTERRUPTED`，shutdown 时更新
- Phenomena log 自动记录 5min+ silence
- 不目录深度冻结，只冻结 3 个文件的存在和语义

### 4. VPS 部署脚本
**文件**: `tools/v13/deploy_v13_recorder_to_vps.sh`

**功能**：
- ✅ 自动创建目录（`/opt/prometheus/v13_recorder`, `/data/prometheus/live_capture_v13`）
- ✅ 安装 Python 依赖（`websocket-client`）
- ✅ 复制 recorder 脚本
- ✅ 生成 systemd service 文件
- ✅ 生成 screen runner 脚本
- ✅ 生成监控脚本（`monitor_recorder.sh`）

**简化设计**：
- 利用 VPS 上现有的 `Prometheus-Quant` 仓库
- 使用 `git pull` 同步代码（不需要 scp）

### 5. 部署指南
**文件**: `docs/V13_VPS_DEPLOYMENT_GUIDE.md`

**内容**：
- ✅ Quick Start（3步）
- ✅ 监控计划（每天检查一次）
- ✅ 预期数据量（7天 500K-2M books, 200K-1M trades）
- ✅ 7天验证清单
- ✅ 故障排查指南
- ✅ V13 核心理念提醒

---

## 📦 交付物

### Quant 代码（GitHub）
**Branch**: `v13_trial12_live_recorder_v0_20260110`  
**Commit**: `a360c21b8729a3a64f5afe1a859a52c12a49e461`  
**GitHub**: https://github.com/Garylauchina/Prometheus-Quant

**文件**：
1. `tools/v13/run_realtime_orderbook_trades_recorder_v13.py` (15KB, 428 lines)
2. `tools/v13/deploy_v13_recorder_to_vps.sh` (7.4KB, bash script)
3. `docs/V13_VPS_DEPLOYMENT_GUIDE.md` (5.8KB, markdown)

---

## 🚀 下一步：VPS 部署（手动）

### Step 1: SSH 到 VPS

```bash
ssh your-vps-user@your-vps-ip
```

### Step 2: 同步代码

```bash
cd ~/Prometheus-Quant
git fetch --all
git checkout v13_trial12_live_recorder_v0_20260110
git pull origin v13_trial12_live_recorder_v0_20260110
```

### Step 3: 运行部署脚本

```bash
bash tools/v13/deploy_v13_recorder_to_vps.sh
```

### Step 4: 启动 Recorder（推荐 systemd）

```bash
sudo cp /tmp/v13-recorder.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start v13-recorder
sudo systemctl enable v13-recorder
```

### Step 5: 验证运行（10分钟后）

```bash
bash /opt/prometheus/v13_recorder/monitor_recorder.sh
```

**预期输出**：
```
Status: ✓ RUNNING (systemd)

V13 Window Files:
  ✓ window.meta.yaml
  ✓ phenomena.log.md (5 lines)
  ✓ verdict.md: INTERRUPTED

Data Files:
  Books:  120 records
  Trades: 45 records
  Errors: 0
```

---

## 📊 监控计划

### 每日检查（Days 1-6）
```bash
bash /opt/prometheus/v13_recorder/monitor_recorder.sh
```

### 预期数据增长

| 时间 | Books | Trades | 磁盘 |
|------|-------|--------|------|
| 1 小时 | 3K-12K | 1K-6K | 3-8 MB |
| 1 天 | 72K-288K | 29K-144K | 50-200 MB |
| **7 天** | **500K-2M** | **200K-1M** | **350MB-1.4GB** |

---

## 📝 24 小时报告要求（即使不完整）

**返回给 Research 团队**：
1. ✅ Quant commit hash: `a360c21b8729a3a64f5afe1a859a52c12a49e461`
2. ⏳ Capture root 绝对路径: `/data/prometheus/live_capture_v13/windows/<WINDOW_ID>`
3. ⏳ 3个窗口文件绝对路径:
   - `window.meta.yaml`
   - `phenomena.log.md`
   - `verdict.md`
4. ⏳ 简短说明：连续观测 or 频繁中断/沉默？

---

## 📝 7 天最终报告要求

**返回给 Research 团队**：
1. ✅ Quant commit hash: `a360c21b8729a3a64f5afe1a859a52c12a49e461`
2. ⏳ Dataset_dir 绝对路径（从 captured 数据构建）
3. ⏳ Gate 输出（Research 运行 provenance + E-liquidity gates）
4. ⏳ 3 个 run_dirs（3 seeds full runs，如果 gates PASS）
5. ⏳ 如果 gates FAIL/NOT_MEASURABLE，返回 `verdict.md` 和证据指针

---

## ⚠️ V13 核心原则（提醒）

### ✅ 接受的输出（等价）
1. 结构显影（完整数据，`MEASURABLE`）
2. 世界沉默（prolonged silence，记录在 `phenomena.log.md`）
3. 裁决拒绝（`NOT_MEASURABLE`）
4. 世界拒绝（`REJECTED_BY_WORLD`）

### ❌ 硬禁止
1. ❌ 为 replay 伪造世界证据（no synthetic bid/ask）
2. ❌ 使用 proxy 进入裁决层
3. ❌ 因接口变化而"适配规则维持功能"
4. ❌ 将 `NOT_MEASURABLE` 解释为工程失败
5. ❌ 为提高稳定性牺牲方法论一致性

---

## 🎯 时间线

- **Day 0 (今天 2026-01-10)**: 
  - ✅ V13 代码完成
  - ✅ 代码推送 GitHub
  - ⏳ VPS 部署（手动）
  
- **Day 0 + 24h (2026-01-11)**:
  - ⏳ 检查 recorder 状态
  - ⏳ 返回 24h 状态报告
  
- **Days 1-6 (2026-01-11 ~ 2026-01-16)**:
  - ⏳ 每日监控（运行 `monitor_recorder.sh`）
  - ⏳ 观察连续性和现象
  
- **Day 7 (2026-01-17)**:
  - ⏳ 验证完成（Books >= 500K, Trades >= 200K）
  - ⏳ 检查 `verdict.md`
  - ⏳ 打包数据（可选）
  
- **Day 8 (2026-01-18)**:
  - ⏳ 构建 dataset（如果 verdict = MEASURABLE）
  - ⏳ 运行 gates 验证
  - ⏳ 运行 3 个 survival space runs
  - ⏳ 最终验证并返回报告

**预计完成**: 2026-01-18

---

## 📚 参考文档

**V13 核心（Research）**:
- V13 SSOT One-Page: `Prometheus-Research/docs/v13/V13_SSOT_STARTUP_ONE_PAGE_V0_20260110.md`
- V13 Capture Window Contract: `Prometheus-Research/docs/v13/V13_SSOT_CAPTURE_WINDOW_MIN_CONTRACT_V0_20260110.md`
- V13 Dev Plan: `Prometheus-Research/docs/v13/V13_DEV_PLAN_V0_20260110.md`
- V13 Kickoff: `Prometheus-Research/docs/v13/deliveries/V13_KICKOFF_TO_QUANT_PROGRAMMER_EXEC_20260110.md`

**Trial-12 原始（Research）**:
- Trial-12 Pre-reg: `Prometheus-Research/docs/v12/pre_reg/V12_TRIAL12_REALTIME_ORDERBOOK_CAPTURE_E_CONTRACT_V0_20260109.md`
- Trial-12 Delivery: `Prometheus-Research/docs/v12/deliveries/V12_TRIAL12_REALTIME_ORDERBOOK_CAPTURE_E_CONTRACT_EXEC_20260109.md`

**Quant 交付（本仓库）**:
- V13 Deployment Guide: `docs/V13_VPS_DEPLOYMENT_GUIDE.md`

---

## ✅ 交付确认

**已交付给 Research 团队**：
- ✅ Quant commit hash: `a360c21b8729a3a64f5afe1a859a52c12a49e461`
- ✅ Branch: `v13_trial12_live_recorder_v0_20260110`
- ✅ GitHub: https://github.com/Garylauchina/Prometheus-Quant
- ✅ 3 个核心文件（recorder, deploy script, guide）
- ✅ 完整部署指南

**等待用户行动**：
- ⏳ VPS 部署（手动）
- ⏳ 24h 状态检查
- ⏳ 7天数据收集
- ⏳ 最终验证和报告

---

**所有准备工作已完成！可以开始 VPS 部署了！** 🎉

---

## 附录：快速命令参考

### VPS 部署（完整命令序列）
```bash
# 1. SSH to VPS
ssh your-vps-user@your-vps-ip

# 2. Sync code
cd ~/Prometheus-Quant
git fetch --all
git checkout v13_trial12_live_recorder_v0_20260110
git pull origin v13_trial12_live_recorder_v0_20260110

# 3. Deploy
bash tools/v13/deploy_v13_recorder_to_vps.sh

# 4. Start (systemd)
sudo cp /tmp/v13-recorder.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start v13-recorder
sudo systemctl enable v13-recorder

# 5. Monitor (10 min later)
bash /opt/prometheus/v13_recorder/monitor_recorder.sh
```

### 每日监控
```bash
bash /opt/prometheus/v13_recorder/monitor_recorder.sh
```

### 7天验证
```bash
bash /opt/prometheus/v13_recorder/monitor_recorder.sh
# Check: Books >= 500,000, Trades >= 200,000, verdict.md
```
