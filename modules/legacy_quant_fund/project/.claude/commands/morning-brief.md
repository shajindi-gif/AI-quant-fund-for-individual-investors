---
description: 生成今日早盘前简报（市场速览 + 持仓表现 + 风险灯 + 关键事件）
argument-hint: 无需参数，直接 /morning-brief
---

请按以下顺序生成今日早盘前简报：

## 步骤

1. **拉取最新数据**（如果 data/etf_prices/ 中数据是 1 个交易日前的）：
   ```bash
   python scripts/fetch_etf_data.py --universe data/etf_universe.csv
   ```

2. **计算最新风险指标**：
   ```bash
   python scripts/risk_metrics.py --positions data/positions.json
   ```

3. **读取关键文件**：
   - `data/positions.json` 当前持仓
   - `data/etf_prices/_snapshot.csv` 实时快照
   - `data/risk_report.json` 风险报告

4. **使用 templates/daily_brief.md 模板生成报告**，填充：
   - 市场速览：沪深300、中证500、创业板、纳指、10Y国债、USDCNY、黄金的最新价 + 涨跌
   - 持仓表现：每只 ETF 当日涨跌、累计收益、目标 vs 当前权重、偏离度
   - 组合层面：当日 vs 60/40 基准
   - 风险灯：状态 + VaR + 波动率 + 最大相关性
   - 关键事件：过去 24 小时的主要财经事件（用 WebSearch 查最新）
   - PM 备注：1-2 句简短判断

5. **保存到** `logs/reports/YYYY-MM-DD-daily.md`

6. **输出给用户**：直接展示报告，不要冗余说明

## 注意

- 如果今天是周末或假期，提示用户"非交易日，无新数据"，跳过执行
- 如果某个数据缺失（比如港股盘前），明确标注 "N/A" 而不要编造
- PM 备注部分要简短，不超过 3 句话，且必须有具体数字支撑
- 触发深度分析的条件：任何持仓 ETF 单日波动 > 3%，或重大宏观事件，或回撤进入 🟡 以上
