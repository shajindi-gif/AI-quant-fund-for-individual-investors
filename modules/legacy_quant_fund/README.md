# Sadie Personal Quant Fund

> 用 Claude（agent 分工）+ Python 工具链运行的个人 ETF 量化基金。
> 本金 20 万，标的仅 ETF，月度调仓，机构化决策流程。

## 这是什么

不是一个会自动下单的"程序化交易"系统，而是一个**机构化的决策辅助系统**：

- **5 层 agent 流水线**：信息采集 → 分析研究 → 投资决策 → 风控 → 执行复盘
- **PM 总协调**：唯一直接对话用户的角色，其他 agent 是它的下属
- **风控有否决权**：任何调仓建议必须经 risk-manager 审核
- **决策必留痕**：每次调仓都生成决策日志 + 30/60/90 天复盘锚点
- **不直接下单**：只输出调仓清单，由用户在券商 APP 手动操作

## 目录结构

```
quant-fund/
├── skills/quant-fund/      ← Claude Skill 包（部署到 ~/.claude/skills/）
│   ├── SKILL.md
│   ├── agents/             ← 10 个 agent 角色提示词
│   ├── scripts/            ← 5 个 Python 脚本
│   ├── templates/          ← 4 个 Markdown 模板
│   ├── data/               ← ETF 池 + 持仓
│   └── reference/          ← 方法论参考
│
├── project/                ← Claude Code 项目模板（用作你的本地工作目录）
│   ├── CLAUDE.md           ← 项目记忆
│   ├── .claude/
│   │   ├── agents/         ← 4 个 subagent 定义
│   │   ├── commands/       ← 4 个 slash commands
│   │   ├── hooks/          ← 自动审计 + 月末提醒
│   │   └── settings.json
│   ├── data/               ← 价格数据 + 持仓状态
│   ├── logs/decisions/     ← 决策日志
│   ├── logs/reports/       ← 日报 / 月报
│   └── scripts/            ← 软链接到 skills 中的脚本
│
├── README.md
├── requirements.txt
├── setup.sh                ← 一键部署
└── .gitignore
```

## 快速开始

### 1. 安装

```bash
git clone <repo>  # 或直接把这个目录拷到你的工作机
cd quant-fund
bash setup.sh
```

`setup.sh` 会做这些事：
- 创建 Python 虚拟环境
- 安装依赖（akshare、pandas、numpy、scipy 等）
- 把 skill 包复制到 `~/.claude/skills/quant-fund/`
- 把 project 模板复制（或链接）到你指定的工作目录
- 拉取一次初始数据

### 2. 编辑你的初始持仓

```bash
cd project
$EDITOR data/positions.json
```

把 `current_positions` 数组填成你当前实际持有的 ETF。如果是从零开始（200,000 全现金），保留默认就行。

### 3. 启动 Claude Code

```bash
cd project
claude
```

Claude 会自动加载 `CLAUDE.md` 项目记忆和 `.claude/` 下的所有配置。

### 4. 试试这些命令

```
/morning-brief          # 今日早盘前简报
/signal-check 510300    # 单只 ETF 评分卡
/rebalance-dry-run      # 月度调仓全流程（不下单）
/monthly-review         # 月度复盘
```

或者直接和 Claude 对话："帮我看看 510880 现在能不能买"——会自动激活 quant-fund skill。

## 4 周路线图

不要一上来就跑全流程。按这个节奏来：

### 第 1 周：搭骨架 + 跑通数据层

**目标**：所有脚本能跑通，每天能拉到数据。

- [ ] 完成 setup.sh，确认 Python 环境
- [ ] 跑一次全量数据拉取：`python scripts/fetch_etf_data.py --universe data/etf_universe.csv --macro`
- [ ] 跑信号计算：`python scripts/compute_signals.py`
- [ ] 跑风险指标：`python scripts/risk_metrics.py --positions data/positions.json`
- [ ] 跑回测：`python scripts/backtest.py --weights '{"510300":0.6,"511260":0.4}' --start 2020-01-01 --end 2026-04-27`
- [ ] **不要**这周做任何调仓

### 第 2 周：跑通核心 agent 链

**目标**：每天跑一次 morning-brief，每周跑一次 signal-check。

- [ ] 用 Claude Code 跑 `/morning-brief` 5 个交易日，看输出是否合理
- [ ] 对组合中每只 ETF 跑 `/signal-check`，看评分卡是否信息密度够
- [ ] 跑 macro-analyst subagent，看宏观研判输出
- [ ] **不要**这周做任何调仓

### 第 3 周：跑 risk-manager + journal

**目标**：建立决策日志习惯。

- [ ] 即使不调仓，每周写一条"维持现状"的决策日志，套用 `templates/decision_log.md`
- [ ] 跑 `/rebalance-dry-run`，看建议方案；不实际下单
- [ ] 主动找 risk-manager 输出"否决"的场景：手动构造一个超限的调仓方案，看它怎么否决
- [ ] 看决策日志里的"假设"和"触发条件"写得清不清晰

### 第 4 周：实盘试运行（小额）

**目标**：第一次真实执行，但只动 10% 仓位。

- [ ] 跑 `/rebalance-dry-run`，得到调仓单
- [ ] **只执行其中 10%**：比如建议买 5 万 511260，先买 5000
- [ ] 真实下单后，更新 `data/positions.json`
- [ ] 跑 `/monthly-review` 复盘
- [ ] 写一篇"第一次实盘心得"放进 `logs/decisions/`

### 第 2 个月起：正式月度调仓节奏

每月最后 5 个交易日跑 `/rebalance-dry-run` → 周末决策 → 周一执行。
每月第一个交易日跑 `/monthly-review`。

## 不变量（永远不要违反）

- 单 ETF ≤ 30%
- 单一行业 ≤ 25%
- 现金 ≥ 5%
- 海外 ≤ 20%
- 调仓最短间隔 4 周
- 单次换手 ≤ 50%
- 持仓 3-8 只

如果某次决策违反这些，risk-manager subagent 会否决。**不要找它谈条件**。

## 常见问题

**Q：akshare 拉数据经常超时怎么办？**
A：脚本内置 0.3s 延迟，仍超时则改用 `--code` 参数单标的拉取。或者订阅 tushare pro（少量付费），把 fetch_etf_data.py 改造一下。

**Q：能让 Claude 自动下单吗？**
A：技术上可以接券商接口，但**强烈不建议**。让 AI 自动下单意味着把 100% 的执行风险交给 AI，违背了"agent 分工"的初衷——AI 是辅助决策，最后一道闸门必须是人。

**Q：为什么不预测价格？**
A：因为预测不准的代价远大于预测准的收益。我们做的是"在不确定中识别概率优势"，不是赌方向。

**Q：业绩跑不赢沪深 300 怎么办？**
A：看时间尺度。在牛市里风险平价跑输是必然的；它换来的是熊市更小的回撤。如果连续 3 年（不是 3 个月）跑输基准 5% 以上，再考虑调整框架。

**Q：可以加个性化策略吗？比如某个行业 ETF 我特别看好？**
A：可以，作为"卫星仓位"加进来（≤ 10%），但仍要走完整流程：fundamental + technical + risk。不要因为"我看好"就跳过流程。

## 给自己的话

这是一套**纪律工具**，不是赚钱机器。
它最大的价值是让你**少做错事**，不是多做对事。
熊市里它会让你少亏 5%，牛市里它会让你少赚 10%——长期看，少亏比多赚更值钱。

如果你想看刺激，去玩个股。
如果你想十年后比朋友的同期投资多 50%，留在这里。

— PM agent
