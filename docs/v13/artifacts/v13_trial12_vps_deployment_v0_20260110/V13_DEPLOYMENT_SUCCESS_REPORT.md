# V13 Recorder VPS 部署成功报告 — 2026-01-10

## ✅ 部署状态：成功运行

**VPS IP**: 45.76.97.37  
**部署时间**: 2026-01-09 20:04 UTC  
**Window ID**: `BTC-USDT-SWAP_2026-01-09T20:04:15Z__24h`  

---

## 📊 当前运行状态

**Recorder 状态**: ✓ RUNNING (screen session)  
**运行时长**: 已启动 ~10 分钟  

### 数据收集情况
- **Books**: 126 records (order-book L1 bid/ask)
- **Trades**: 277 records
- **Errors**: 0
- **数据收集速率**: 正常

### V13 Window Files (已创建)
✅ `window.meta.yaml` - 窗口元数据  
✅ `phenomena.log.md` - 观测日志  
✅ `verdict.md` - 当前状态: `INTERRUPTED` (运行中)  

---

## 📂 重要路径

**Window Root**:
```
/data/prometheus/live_capture_v13/windows/BTC-USDT-SWAP_2026-01-09T20:04:15Z__24h
```

**Recorder 安装**:
```
/opt/prometheus/v13_recorder/
```

**监控脚本**:
```bash
ssh root@45.76.97.37 "bash /opt/prometheus/v13_recorder/monitor_recorder.sh"
```

---

## 🔧 SSH 连接修复记录

经过多轮排查，最终发现问题：
- ❌ 不是公钥问题
- ❌ 不是防火墙问题
- ❌ 不是 host keys 问题
- ✅ **问题**：SSH 只监听 localhost (127.0.0.1)
- ✅ **解决**：配置 `ListenAddress 0.0.0.0`，重启 sshd

**关键修复命令**:
```bash
sed -i 's/^ListenAddress.*/ListenAddress 0.0.0.0/' /etc/ssh/sshd_config
systemctl restart sshd
```

---

## 📋 V13 Phase 1 配置 (Observation-first)

**关键变更**：
- ✅ 窗口时长：24小时（不是7天）
- ✅ 不计算 L / gates（Phase 1 只观测）
- ✅ 不运行裁决
- ✅ 接受 NOT_MEASURABLE / INTERRUPTED / REJECTED_BY_WORLD 为合法输出

**成功标准**：
> 我们能看到至少一个：cooperate / silence / refusal / drift

---

## 📅 时间线

| 时间 | 里程碑 | 状态 |
|------|--------|------|
| **Day 0 (2026-01-09 20:04 UTC)** | Recorder 启动 | ✅ 完成 |
| **Day 0 + 24h (2026-01-10 20:04 UTC)** | 24h 窗口完成 | ⏳ 等待中 |
| **检查时间** | 每天监控一次 | ⏳ 进行中 |

---

## 🔍 监控命令

### 快速检查
```bash
ssh root@45.76.97.37 "bash /opt/prometheus/v13_recorder/monitor_recorder.sh"
```

### 实时查看 logs
```bash
ssh root@45.76.97.37 "screen -r v13_recorder"
# Ctrl-A then D to detach
```

### 查看窗口文件
```bash
ssh root@45.76.97.37 "cat /data/prometheus/live_capture_v13/windows/BTC-USDT-SWAP_2026-01-09T20:04:15Z__24h/window.meta.yaml"
ssh root@45.76.97.37 "cat /data/prometheus/live_capture_v13/windows/BTC-USDT-SWAP_2026-01-09T20:04:15Z__24h/verdict.md"
```

---

## 📊 预期数据量 (24小时)

| 指标 | 预期值 |
|------|--------|
| Books | 72K-288K records |
| Trades | 29K-144K records |
| 磁盘占用 | 50-200 MB |
| Verdict | MEASURABLE (如果数据充足) |

---

## 📝 24小时后的报告要求

需要返回给 Research 团队：

1. ✅ Quant commit hash: `a360c21b8729a3a64f5afe1a859a52c12a49e461`
2. ⏳ Capture root 绝对路径
3. ⏳ 3个窗口文件绝对路径：
   - `window.meta.yaml`
   - `phenomena.log.md`
   - `verdict.md`
4. ⏳ 简短说明：连续观测 or 频繁中断/沉默？

---

## ⚠️ V13 核心提醒

### ✅ 接受的输出（等价）
1. 结构显影（`MEASURABLE`）
2. 世界沉默（prolonged silence）
3. 裁决拒绝（`NOT_MEASURABLE`）
4. 世界拒绝（`REJECTED_BY_WORLD`）

### ❌ 禁止的行为
1. ❌ 伪造世界证据（no synthetic bid/ask）
2. ❌ Proxy 进入裁决层
3. ❌ 将 NOT_MEASURABLE 解释为失败
4. ❌ 为稳定性牺牲方法论一致性

---

## ✅ 部署检查清单

- [x] VPS SSH 连接修复
- [x] V13 代码上传
- [x] 部署脚本执行
- [x] Recorder 启动 (screen)
- [x] 数据收集验证 (Books > 0, Trades > 0)
- [x] V13 window files 创建
- [x] 监控脚本可用
- [ ] 24h 数据收集完成（明天检查）
- [ ] 24h 状态报告返回

---

## 🎉 部署总结

经过复杂的 SSH 问题排查（~2小时），最终成功：
1. ✅ SSH 连接修复
2. ✅ V13 Recorder 部署
3. ✅ 数据实时收集中
4. ✅ V13 Window Files 正常创建

**下一步**：等待 24 小时后检查数据收集情况，生成状态报告。

---

**部署完成时间**: 2026-01-09 20:15 UTC  
**预计 24h 完成时间**: 2026-01-10 20:04 UTC
