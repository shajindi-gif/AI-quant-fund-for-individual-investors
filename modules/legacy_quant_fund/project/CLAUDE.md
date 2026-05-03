# Sadie Personal Quant Fund — Claude Code 项目记忆

> 这是 Claude Code 在该项目目录下自动加载的项目记忆文件。
> 它告诉 Claude（在终端里跑的版本）：这个项目是干什么的、应该如何行动、不应该做什么。

## 项目身份

- **基金名称**：Sadie Personal Quant Fund
- **基金经理**：Sadie
- **本金规模**：人民币 200,000
- **起始日期**：2026-04-27
- **基准**：60% 沪深300（510300）+ 40% 10年国开（511260），月度再平衡
- **投资标的**：仅 ETF（A 股 + 港股通 + 跨境）
- **持仓数**：3–6 只
- **频率**：月度调仓 + 事件触发战术调整

## 目录约定

```
project/
├── CLAUDE.md                # 你正在读的文件
├── .claude/
│   ├── agents/              # subagent 定义
│   │   ├── pm.md
│   │   ├── macro-analyst.md
│   │   ├── technical-analyst.md
│   │   └── risk-manager.md
│   ├── commands/            # slash commands
│   │   ├── morning-brief.md
│   │   ├── signal-check.md
│   │   ├── rebalance-dry-run.md
│   │   └── monthly-review.md
│   ├── hooks/               # 钩子脚本
│   │   ├── post-tool-use.sh
│   │   └── stop-reminder.sh
│   └── settings.json
├── data/
│   ├── etf_universe.csv     # ETF 池
│   ├── positions.json       # 当前持仓（事实之源）
│   ├── etf_prices/          # 历史价格 parquet
│   └── signals.csv          # 最新信号
├── logs/
│   ├── decisions/           # 决策日志，YYYY-MM-DD-{type}.md
│   └── reports/             # 日报、月报
├── scripts/                 # Python 脚本（与 skill 中相同）
└── notebooks/               # Jupyter 探索（可选）
```

## 与 skill 的关系

这个项目复用 `~/.claude/skills/quant-fund/` 中的 skill 包：
- agent 提示词：从 skill 的 `agents/` 读取
- 模板：从 skill 的 `templates/` 读取
- 方法论：从 skill 的 `reference/` 读取
- Python 脚本：在 skill 与 project 间是软链接（setup.sh 处理），保证一致

如果用户在对话中提到"调仓"、"复盘"、"风险检查"，应该自动激活 skill。

## 关键工作流

### 月度调仓（每月最后 5 个交易日）
依次：拉数据 → macro → regime → allocation → selection → optimize → risk → 调仓单 → 决策日志。
对应命令：`/rebalance-dry-run`

### 日常监控（每个交易日早盘前）
对应命令：`/morning-brief`

### 单 ETF 研判
当用户输入"看看 XX ETF"时，调用 technical + fundamental subagent，输出评分卡。
对应命令：`/signal-check 510300`

### 月度复盘（每月第一个交易日）
对应命令：`/monthly-review`

## 不变量（每次启动都要检查）

```
[ ] data/positions.json 存在且 JSON 合法
[ ] 现金比例 ≥ 5%（除非紧急避险中）
[ ] 单一 ETF 仓位 ≤ 30%
[ ] 距上次调仓 ≥ 28 天（除非触发风控线）
```

如果任何不变量不满足，**第一件事是告知用户**，而非继续操作。

## 决策原则（写入记忆）

1. **不预测点位**。用"如果 X 则 Y"句式。
2. **不绕过 risk-manager subagent**。任何调仓建议必须由它审核。
3. **不直接下单**。我们只生成调仓清单，由 Sadie 自己在券商 APP 操作。
4. **每个决策有日志**。即便是"维持现状"也写一条说明。
5. **承认不确定**。把置信度（高/中/低）显式标出来。

## 沟通风格

- 中文母语，简洁不堆砌
- 量化先行：每个判断附数字
- 不用"暴涨"、"重磅"、"利好"这类词
- 同一段话里同一信息不要重复表达
- 工具输出是 ground truth，不要在没运行脚本时编造数字

## 可用工具与权限

- **可读**：`data/`、`logs/`、`.claude/`、`scripts/`、`README.md`
- **可写**：`logs/decisions/`、`logs/reports/`、`data/positions.json`（仅在用户确认后）、`data/signals.csv`、`data/risk_report.json`、`data/proposed_trades.json`
- **可执行**：`scripts/*.py`、`bash` 命令（注意网络白名单）
- **不可写**：`scripts/*`（除非用户明确要求改 logic）、`.claude/agents/*`（同前）

## 用户偏好

- Sadie 偏好读最终结论 + 关键依据，不需要冗长展开
- 使用图表/表格优于纯文字
- 复杂信息用代码块或 Markdown 表格而非段落
- 决策建议必须**明确**（"加 X% / 减 Y%"），不要"可以考虑"
