# 结果归档规范

统一将所有测试/回测/Mock/虚拟盘/实盘结果放入 `results/`，禁止散落在根目录。

目录结构（示例）
```
results/
  okx_paper/
    20251207/
      btc_swap_run_20251207T120000Z/
        config.json      # 运行配置（含种子、数据源、参数哈希）
        metrics.json     # 关键指标汇总
        logs.txt         # 运行日志（可链接外部日志文件）
        report.md        # 简要报告（可选）
        artifacts/       # 中间产物（快照、进度、图表）
  backtest/
    20251207/...
  mock/
    20251207/...
  real/
    20251207/...
  legacy/
    migrated_20251207_batch1/   # 历史散落文件迁移归档
```

命名规范
- 一级：mode = okx_paper / backtest / mock / real / legacy
- 二级：日期 YYYYMMDD
- 三级：run_id = <scenario>_<timestampZ>（例：`btc_swap_run_20251207T120000Z`）

落盘要求
- 必备：`config.json`（包含随机种子、数据源版本/路径、主要参数、commit hash/dirty 标记）
- 关键指标：写入 `metrics.json`
- 日志：`logs.txt`（若外部日志文件过大，可存路径/链接）
- 可选报告：`report.md`
- 中间产物：放 `artifacts/` 子目录

遗留文件处理
- 根目录散落的 json/txt/log 结果统一迁移到 `results/legacy/`，并在 README 中注明“历史记录，仅参考”。

