# V13 VPS 工作流程说明 v0 — 2026-01-12

Status: **FROZEN (operational)**  
Additive-only.

## §1 工作环境变更（已冻结）

### 1.1 程序员AI工作区
- **位置**: VPS（远程服务器）
- **限制**: 无法直接读取本地 Research 仓库的指令文件
- **交付物位置**: VPS 工作区（例如 `/data/prometheus/live_capture_v13/windows/`）

### 1.2 Research 侧（架构师）
- **位置**: 本地（`/Users/liugang/Cursor_Store/Prometheus-Research`）
- **职责**: 
  - 将指令文件发布到 VPS 的指令目录，供程序员AI直接读取
  - 用 SSH 连接 VPS 读取程序员的交付物

---

## §2 VPS 配置（从 .env 或已知配置）

### 2.1 已知配置（历史记录）
- **VPS IP**: `45.76.97.37`
- **SSH User**: `root`
- **SSH 命令格式**: `ssh root@45.76.97.37 "<command>"`

### 2.2 配置读取方式
- `.env` 文件位于 Research 根目录（可能被 `.gitignore` 过滤）
- 如果 `.env` 不可读，使用已知配置或用户提供

---

## §3 指令发布流程（冻结）

### 3.1 VPS 指令目录（已冻结）

**目录路径**: `/data/prometheus/v13_instructions/`

**规则**:
- 所有交付指令文件必须发布到此目录
- 程序员AI在VPS上直接读取此目录中的指令文件
- 文件名保持原样（如 `V13_XXX_EXEC_YYYYMMDD.md`）

### 3.2 架构师侧：发布指令到VPS

**方法**: 使用发布脚本将指令文件上传到VPS

**脚本**: `tools/v13/publish_instruction_to_vps.sh`

**示例**:
```bash
./tools/v13/publish_instruction_to_vps.sh docs/v13/deliveries/V13_PHASE1_COMPLETION_REPORT_TEMPLATE_AND_REVIEW_GATE_EXEC_20260112.md
```

**脚本功能**:
- 自动创建VPS指令目录（如不存在）
- 通过SCP上传指令文件
- 验证上传成功

### 3.3 程序员侧：读取指令

- 程序员AI在VPS上读取指令目录中的文件
- 指令文件路径: `/data/prometheus/v13_instructions/<FILENAME>`
- 程序员在 VPS 上执行指令
- 交付物保存在 VPS 工作区

---

## §4 交付物读取流程（冻结）

### 4.1 架构师侧：SSH 读取 VPS 文件

**方法**: 使用 SSH 命令连接 VPS 并读取文件

**示例**:
```bash
# 读取单个文件
ssh root@45.76.97.37 "cat /data/prometheus/live_capture_v13/windows/<WINDOW_ID>/window.meta.yaml"

# 读取并保存到本地
ssh root@45.76.97.37 "cat /data/prometheus/live_capture_v13/windows/<WINDOW_ID>/V13_PHASE1_WINDOW_COMPLETION_REPORT.md" > /tmp/v13_completion_report.md

# 列出目录
ssh root@45.76.97.37 "ls -la /data/prometheus/live_capture_v13/windows/"
```

### 4.2 文件路径约定

**VPS 工作区根目录**（建议）:
- `/data/prometheus/live_capture_v13/windows/<WINDOW_ID>/`

**必需文件**（V13 Capture Window Minimal Contract）:
- `window.meta.yaml`
- `phenomena.log.md`
- `verdict.md`
- `evidence.json` (如果已生成)

**完成报告**（Phase 1）:
- `<window_dir>/V13_PHASE1_WINDOW_COMPLETION_REPORT.md`

---

## §5 辅助工具（推荐）

### 5.1 读取 VPS 配置脚本

创建: `tools/v13/read_vps_config.sh`

```bash
#!/bin/bash
# Read VPS config from .env or use defaults

VPS_HOST="${VPS_HOST:-45.76.97.37}"
VPS_USER="${VPS_USER:-root}"

if [ -f .env ]; then
    source .env
    VPS_HOST="${VPS_HOST:-45.76.97.37}"
    VPS_USER="${VPS_USER:-root}"
fi

echo "VPS_HOST=$VPS_HOST"
echo "VPS_USER=$VPS_USER"
```

### 5.2 发布指令到VPS脚本

创建: `tools/v13/publish_instruction_to_vps.sh`

```bash
#!/bin/bash
# Publish instruction files to VPS instruction directory

./tools/v13/publish_instruction_to_vps.sh <INSTRUCTION_FILE> [VPS_HOST] [VPS_USER]
```

### 5.3 SSH 读取交付物脚本

创建: `tools/v13/fetch_vps_delivery.sh`

```bash
#!/bin/bash
# Fetch delivery files from VPS

WINDOW_ID="$1"
VPS_HOST="${VPS_HOST:-45.76.97.37}"
VPS_USER="${VPS_USER:-root}"
WINDOW_DIR="/data/prometheus/live_capture_v13/windows/${WINDOW_ID}"

if [ -z "$WINDOW_ID" ]; then
    echo "Usage: $0 <WINDOW_ID>"
    exit 1
fi

# Fetch completion report
ssh ${VPS_USER}@${VPS_HOST} "cat ${WINDOW_DIR}/V13_PHASE1_WINDOW_COMPLETION_REPORT.md" > /tmp/v13_${WINDOW_ID}_completion_report.md

# Fetch required window files
ssh ${VPS_USER}@${VPS_HOST} "cat ${WINDOW_DIR}/window.meta.yaml" > /tmp/v13_${WINDOW_ID}_window_meta.yaml
ssh ${VPS_USER}@${VPS_HOST} "cat ${WINDOW_DIR}/phenomena.log.md" > /tmp/v13_${WINDOW_ID}_phenomena.log.md
ssh ${VPS_USER}@${VPS_HOST} "cat ${WINDOW_DIR}/verdict.md" > /tmp/v13_${WINDOW_ID}_verdict.md

if ssh ${VPS_USER}@${VPS_HOST} "test -f ${WINDOW_DIR}/evidence.json"; then
    ssh ${VPS_USER}@${VPS_HOST} "cat ${WINDOW_DIR}/evidence.json" > /tmp/v13_${WINDOW_ID}_evidence.json
fi

echo "Files fetched to /tmp/v13_${WINDOW_ID}_*.{md,yaml,json}"
```

---

## §6 指令文件更新规则（冻结）

### 6.1 所有交付指令文件必须包含

**顶部说明**:
```markdown
# 注意：本指令文件需发布到VPS指令目录供程序员AI读取
# 架构师侧执行: ./tools/v13/publish_instruction_to_vps.sh <本文件路径>
# VPS路径: /data/prometheus/v13_instructions/<FILENAME>
```

### 6.2 路径引用规则

**禁止**: 直接引用本地绝对路径（如 `/Users/liugang/...`）

**改为**: 
- 如果指令需要引用 Research 仓库内容，在VPS上通过SSH读取或提供完整内容
- 如果指令需要引用 VPS 路径，使用 VPS 绝对路径（如 `/data/prometheus/...`）

---

## §7 示例工作流

### 7.1 发布指令

**架构师侧**:
```bash
./tools/v13/publish_instruction_to_vps.sh docs/v13/deliveries/V13_PHASE1_COMPLETION_REPORT_TEMPLATE_AND_REVIEW_GATE_EXEC_20260112.md
```

**输出**: 脚本会显示VPS路径，例如：
```
✓ Instruction file published successfully!
  VPS path: /data/prometheus/v13_instructions/V13_PHASE1_COMPLETION_REPORT_TEMPLATE_AND_REVIEW_GATE_EXEC_20260112.md
```

**程序员侧**: 在VPS上读取指令
```bash
cat /data/prometheus/v13_instructions/V13_PHASE1_COMPLETION_REPORT_TEMPLATE_AND_REVIEW_GATE_EXEC_20260112.md
```

### 7.2 读取交付物

**架构师侧**:
```bash
# 读取完成报告
ssh root@45.76.97.37 "cat /data/prometheus/live_capture_v13/windows/BTC-USDT-SWAP_2026-01-09T20:04:15Z__24h/V13_PHASE1_WINDOW_COMPLETION_REPORT.md"

# 或使用辅助脚本
./tools/v13/fetch_vps_delivery.sh BTC-USDT-SWAP_2026-01-09T20:04:15Z__24h
```

---

## §8 冻结日期

- **创建**: 2026-01-12
- **状态**: FROZEN (operational)
- **变更**: Additive-only
