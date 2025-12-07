# DOCUMENT MAP（文档地图）

目标：快速找到“哪份文档管哪件事”，避免遗漏/重复。按版本层次与主题分类，标出关键文件与去向。

## 版本演进与审计
- `ARCHITECTURE_AUDIT_2025.md`：全局架构审计（v1→v5.5），保留/废弃判定。
- `ARCHITECTURE_RETHINK.md`：架构反思与未来方向。
- `AUDIT_SUMMARY.md`：审计摘要。
- `CODE_AUDIT_REPORT.md`：代码使用率/缺失模块审计。
- `docs/V6_FACADE_PLAN.md`：v6 封装/兼容策略（主干、Facade、legacy 隔离、Mock 场景）

## v5.x 核心（当前主线）
- 设计/计划/完成报告：`docs/V5.0_DESIGN_DECISIONS.md`，`docs/V5.0_DEVELOPMENT_PLAN.md`，`docs/V5.0_COMPLETION_REPORT.md`
- 模块参考：`docs/V5.0_MODULE_REFERENCE.md`
- 双熵/进化：`docs/V5.0_DUAL_ENTROPY_DESIGN.md`
- 升级指南：`docs/V5.1_UPGRADE_GUIDE.md`
- 进化系统：`docs/EVOLUTION.md`，`docs/EVOLUTION_SYSTEM.md`
- 账簿/血统修复：`docs/GENEALOGY_TRACKING_FIX.md`

## v4.x 关键设计（仍需继承的理念/模块）
- 架构与三层：`docs/V4.0_ARCHITECTURE.md`，`docs/V4.0_THREE_LAYERS.md`，`docs/V4.0_FINAL_ARCHITECTURE.md`
- 公告板/权限：`docs/V4.0_BULLETIN_BOARD_SYSTEM.md`，`docs/V4.0_TRADING_PERMISSIONS.md`
- 多样性/进化：`docs/V4.0_DIVERSITY_EVOLUTION.md`，`docs/V4.1_EVOLUTION_SYSTEM.md`
- 账簿一致性：`docs/V4.0_LEDGER_CONSISTENCY_FIX.md`
- 其他子主题：`docs/V4.0_*` 系列（情绪、博弈、路标、多资产等）

## 核心操作与速查
- 模块速查：`docs/module_registry.md`
- API Cookbook：`docs/cookbook.md`
- 场景化 Playbook 目录：`docs/playbook_index.md`（后续在 `docs/playbooks/` 填充单页）
- 参数/环境：`docs/PARAMETERS.md`，`docs/ENV_CONFIGURATION.md`
- 迁移指南：`docs/MIGRATION_GUIDE.md`
- 故障排查：`docs/TROUBLESHOOTING.md`
- 滑点/指标：`docs/SLIPPAGE_INTEGRATION.md`，`docs/TECHNICAL_INDICATORS.md`
- 交易流水修复：`docs/TRADE_ID_UUID_FIX.md`

## 账簿与交易
- 账簿设计与对账：`AgentAccount账户系统_设计说明.md`（根目录），`docs/V4.0_LEDGER_CONSISTENCY_FIX.md`
- OKX/交易指南：`LIVE_TRADING_GUIDE.md`，`TRADING_COST_VERIFICATION.md`，`check_*`/`detailed_okx_*`/`run_okx_*` 脚本及日志

## 测试与模板
- 标准测试模板：`templates/STANDARD_TEST_TEMPLATE.py`
- 重写计划：`templates/REWRITE_PLAN.md`
- 回测/极端场景参考：`test_ultimate_1000x_COMPLETE.py`（完整架构），`test_v53_okx_2000days.py`（需修复），`test_live_continuous.py`（OKX 虚拟盘，需继续完善）

## 部署与运维
- 环境/部署：`SETUP_MAC.md`，`DEPLOY.md`，`deploy_*`/`quick_restart_vps.py` 等
- 监控：`monitor_*` 脚本，`monitoring/` 目录

## 推荐阅读顺序（最快获取上下文）
1) `docs/module_registry.md`（2 分钟定位模块入口）  
2) `docs/cookbook.md`（直接可用的调用片段）  
3) `docs/playbook_index.md`（选场景，再看对应单页）  
4) `ARCHITECTURE_AUDIT_2025.md`（全局演进 + 保留/废弃）  
5) v5.x 设计/参考：`docs/V5.0_MODULE_REFERENCE.md` + `docs/V5.0_DUAL_ENTROPY_DESIGN.md`  
6) 账簿/OKX 相关：`AgentAccount账户系统_设计说明.md` + `LIVE_TRADING_GUIDE.md`

