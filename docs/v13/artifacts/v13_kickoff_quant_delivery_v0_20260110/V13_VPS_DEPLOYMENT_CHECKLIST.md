# V13 VPS Deployment Checklist — 2026-01-10

**Purpose**: Quick checklist for VPS deployment and monitoring  
**Timeline**: 7-8 days  

---

## ☑️ Pre-Deployment (Day 0)

- [ ] VPS 可访问（SSH 连接正常）
- [ ] VPS 上已有 `~/Prometheus-Quant` 仓库
- [ ] VPS Python 版本 >= 3.10
- [ ] VPS 磁盘空间 >= 10 GB
- [ ] 网络稳定（ping VPS < 100ms, 丢包率 < 1%）

---

## ☑️ Deployment (Day 0, ~10 min)

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

# 4. Start recorder (systemd recommended)
sudo cp /tmp/v13-recorder.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start v13-recorder
sudo systemctl enable v13-recorder

# 5. Wait 10 minutes, then verify
bash /opt/prometheus/v13_recorder/monitor_recorder.sh
```

**Expected output (10 min later)**:
```
Status: ✓ RUNNING (systemd)
V13 Window Files:
  ✓ window.meta.yaml
  ✓ phenomena.log.md (5 lines)
  ✓ verdict.md: INTERRUPTED
Data Files:
  Books:  120 records
  Trades: 45 records
```

- [ ] Recorder 运行中（systemd or screen）
- [ ] 3 个 V13 窗口文件存在
- [ ] Books > 0
- [ ] Trades > 0

---

## ☑️ 24-Hour Check (Day 0 + 24h)

```bash
bash /opt/prometheus/v13_recorder/monitor_recorder.sh
```

**Expected data**:
- Books: 72K-288K
- Trades: 29K-144K
- Errors: < 100

**Return to Research team**:
1. Quant commit hash: `a360c21b8729a3a64f5afe1a859a52c12a49e461`
2. Capture root absolute path
3. 3 window files absolute paths
4. Short note: 连续观测 or 频繁中断/沉默？

- [ ] Monitor 脚本运行正常
- [ ] Books/Trades 数量正常增长
- [ ] 24h 报告已发送

---

## ☑️ Daily Monitoring (Days 1-6)

```bash
bash /opt/prometheus/v13_recorder/monitor_recorder.sh
```

**Check**:
- [ ] Status = RUNNING
- [ ] Books 持续增长
- [ ] Trades 持续增长
- [ ] Errors < 100
- [ ] No prolonged silence (> 5 min)

**If prolonged silence detected**:
- [ ] Check `phenomena.log.md` for automatic logging
- [ ] Do NOT restart recorder
- [ ] This is a valid observation (V13 accepts world silence)

---

## ☑️ 7-Day Verification (Day 7)

```bash
bash /opt/prometheus/v13_recorder/monitor_recorder.sh
```

**Expected**:
- Books: >= 500,000
- Trades: >= 200,000
- Duration: >= 168 hours (7 days)
- Disk: 350MB-1.4GB

**Check V13 window files**:
```bash
WINDOW_DIR="/data/prometheus/live_capture_v13/windows/<WINDOW_ID>"
cat ${WINDOW_DIR}/window.meta.yaml
cat ${WINDOW_DIR}/phenomena.log.md
cat ${WINDOW_DIR}/verdict.md
```

**Verdict expected**:
- `MEASURABLE` (if Books >= 100, Trades >= 10)
- `NOT_MEASURABLE` (if insufficient data)
- `REJECTED_BY_WORLD` (if Books = 0 or Trades = 0)

- [ ] Books >= 500,000
- [ ] Trades >= 200,000
- [ ] Duration >= 168h
- [ ] `verdict.md` 已更新
- [ ] 3 个窗口文件完整

---

## ☑️ Final Delivery (Day 8)

**If verdict = MEASURABLE**:
1. Build dataset from captured data (待 Research 提供工具)
2. Run provenance gate (G0)
3. Run E-liquidity gate (G1)
4. Run 3 survival space runs (seeds: 71001, 71002, 71003)
5. Verify runs

**If verdict = NOT_MEASURABLE or REJECTED_BY_WORLD**:
1. Return window directory path
2. Return `verdict.md` content
3. Return `phenomena.log.md` observations
4. No dataset build (V13 accepts this output)

**Return to Research team**:
1. Quant commit hash: `a360c21b8729a3a64f5afe1a859a52c12a49e461`
2. Window directory absolute path
3. `verdict.md` content
4. `phenomena.log.md` key observations
5. Books/Trades final count
6. (If MEASURABLE) Dataset_dir + gate reports + 3 run_dirs

- [ ] Verdict 已确认
- [ ] 最终报告已准备
- [ ] 已通知 Research 团队

---

## 🛠️ Troubleshooting

### Problem: Recorder not running

```bash
# Check systemd
sudo systemctl status v13-recorder
sudo journalctl -u v13-recorder -n 50

# Or check screen
screen -ls
screen -r v13_recorder
```

**Action**:
- [ ] Check logs for errors
- [ ] Check network connectivity
- [ ] If needed, restart: `sudo systemctl restart v13-recorder`

---

### Problem: Books/Trades = 0 for > 10 minutes

```bash
tail -n 20 ${WINDOW_DIR}/raw/recorder_log.jsonl
```

**Action**:
- [ ] Check if this is world refusal (recorded in `phenomena.log.md`)
- [ ] Do NOT synthesize or "fix" data
- [ ] Let recorder continue (may be prolonged silence)
- [ ] If persists for hours, this becomes `REJECTED_BY_WORLD` verdict

---

### Problem: Prolonged silence (> 5 min)

**V13 handling**:
- [ ] Recorder automatically logs to `phenomena.log.md`
- [ ] This is a valid observation, NOT a failure
- [ ] Do NOT restart recorder
- [ ] Let it continue

---

### Problem: Disk space low

```bash
df -h /data/prometheus/live_capture_v13/
```

**Action**:
- [ ] Ensure >= 10 GB free space
- [ ] If needed, clean up old files
- [ ] Do NOT delete current window files

---

## 📝 Key Files Reference

**V13 Window Files (required)**:
- `window.meta.yaml` - Window metadata
- `phenomena.log.md` - Observed facts only
- `verdict.md` - Single token verdict

**Data Files (optional)**:
- `raw/books5.jsonl` - Order-book data
- `raw/trades.jsonl` - Trade data
- `raw/recorder_log.jsonl` - Recorder log

**Scripts**:
- `monitor_recorder.sh` - Daily monitoring
- `start_recorder_in_screen.sh` - Screen runner

---

## ⏱️ Timeline Summary

| Day | Action | Expected |
|-----|--------|----------|
| **Day 0** | Deploy + Start | Status: RUNNING, Books > 0 |
| **Day 0+24h** | 24h check | Books: 72K-288K, send report |
| **Days 1-6** | Daily monitor | Books/Trades growing |
| **Day 7** | Verify completion | Books >= 500K, check verdict |
| **Day 8** | Final delivery | Dataset + gates + runs (if MEASURABLE) |

**Estimated completion**: 2026-01-18

---

## ✅ Success Criteria

**Code level**:
- [x] V13 recorder implemented
- [x] Deployment script ready
- [x] Guide documentation complete
- [x] Code pushed to GitHub

**Deployment level**:
- [ ] Recorder running on VPS
- [ ] 24h report delivered
- [ ] Daily monitoring completed (Days 1-6)

**Final delivery**:
- [ ] 7-day capture completed
- [ ] Verdict determined
- [ ] Final report delivered to Research

---

**Current Status**: Code ready, waiting for VPS deployment 🚀
