# ETF Quant Machine

一个面向个人资金体量（20万人民币级别）的本地量化研究与每日交易决策系统。

## 设计目标

这不是 Two Sigma / Renaissance 的复制品，而是把它们的**流程思想**压缩到个人可执行版本：

1. **数据标准化**：统一ETF历史行情格式。
2. **因子工程**：趋势、动量、均值回归、突破、相对强弱、波动约束。
3. **主观信息结构化**：把你每天阅读 WSJ / FT / NYT 的判断，压缩成几个离散分数。
4. **组合构建**：在有限资金下做权重分配、仓位上限、换手上限、止损约束。
5. **每日流程自动化**：一键运行，输出今日信号、目标仓位、交易清单、风险摘要。
6. **回测复盘**：在历史ETF数据上复盘策略表现。

## 你需要准备什么

### 1. 本地环境

```bash
cd ~/Desktop
mkdir etf_quant_machine
cd etf_quant_machine
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 数据格式

把每只 ETF 的 CSV 放进 `data/raw/`，文件名建议直接用代码命名：

- `510300.csv`
- `510500.csv`
- `159915.csv`
- `513100.csv`

每个 CSV 至少包含这些列：

- `date`
- `open`
- `high`
- `low`
- `close`
- `volume`

示例：

```csv
date,open,high,low,close,volume
2025-01-02,3.82,3.88,3.80,3.87,345678900
2025-01-03,3.87,3.90,3.85,3.89,298765400
```

## 每天如何运行

### 第一步：填写当天主观判断

编辑 `data/processed/manual_macro_input.csv`。

字段解释：

- `date`: 日期
- `regime_score`: 大盘风险偏好（-2 到 2）
- `liquidity_score`: 流动性与政策松紧（-2 到 2）
- `news_sentiment_score`: 你基于华尔街日报/FT/政策新闻的主观打分（-2 到 2）
- `china_score`: 对中国市场相关资产的方向判断（-2 到 2）
- `us_score`: 对美股/海外风险资产的方向判断（-2 到 2）

示例：

```csv
date,regime_score,liquidity_score,news_sentiment_score,china_score,us_score
2026-03-30,1,1,0,1,0
```

### 第二步：运行日常策略

```bash
python main.py run-daily
```

输出：

- `reports/latest_signals.csv`
- `reports/latest_orders.csv`
- `reports/latest_portfolio_summary.csv`
- `reports/daily_report.md`

### 第三步：历史回测

```bash
python main.py backtest
```

输出：

- `reports/backtest_equity_curve.csv`
- `reports/backtest_summary.csv`

## 目录结构

```text
etf_quant_machine/
├── config.yaml
├── main.py
├── requirements.txt
├── data/
│   ├── raw/
│   └── processed/
├── reports/
├── logs/
└── src/
    ├── config_loader.py
    ├── data_loader.py
    ├── features.py
    ├── manual_macro.py
    ├── signal_engine.py
    ├── portfolio.py
    ├── backtester.py
    └── reporting.py
```

## 个人版 Two Sigma / Renaissance 的正确理解

你要模仿的不是他们的资金规模和基础设施，而是他们的流程：

- 把主观判断变成结构化输入
- 把所有交易逻辑写成规则
- 每天让机器固定跑同一套流程
- 用风险模型限制自己
- 复盘每一笔决策而不是凭感觉频繁改规则

## 这个系统不做什么

- 不直接接券商账户
- 不自动下单
- 不抓外部新闻 API
- 不做高频交易
- 不承诺收益

这套系统适合你当前状态：

- 你有历史 ETF 数据
- 你有长期新闻阅读能力
- 你想把经验固化成流程
- 你资金体量不大，需要控制回撤而不是追求复杂执行

## 下一步强化方向

1. 把 ETF 扩展到 30-50 只。
2. 按主题分组：宽基 / 科技 / 红利 / 海外 / 商品 / 债券。
3. 给每个 ETF 增加最小成交额过滤。
4. 给主观打分做长期复盘，校验你的“新闻判断”是否真的有效。
5. 等系统稳定后，再考虑接入券商和自动下单。
