---
description: 月度调仓全流程演练（不实际下单），生成调仓单 + 决策日志
argument-hint: 可选 --method [equal|risk_parity|kelly_fractional]，默认 risk_parity
---

执行月度调仓的全流程演练。这是工作流 A，是 quant-fund skill 的核心流程。

## 流程（严格按顺序，不跳步）

### 0. 前置检查
- 检查 `data/positions.json` 中 `last_rebalance_date`
- 如距今 < 28 天，提示用户："距上次调仓 X 天，未到 4 周间隔。是否仍要执行？"等用户确认
- 如未触发风控线 + 未到间隔 → 默认拒绝执行

### 1. 数据刷新
```bash
python scripts/fetch_etf_data.py --universe data/etf_universe.csv --macro
```

### 2. 宏观研判
调用 **macro-analyst subagent**，输出宏观状态简报。

### 3. 状态识别
基于 macro-analyst 的输出，参考 skill 的 `agents/regime.md`：
- 给出当前所处的"增长×通胀"四象限
- 输出该象限下的资产排序建议

### 4. 大类资产配置
参考 skill 的 `agents/allocation.md`：
- 取该象限的基准配置
- 应用估值/利差/政策/不确定性 4 个调整因子（每条 ±5%，最多 ±15%）
- 输出 6 类资产（A/B/C/D/E/F）的目标权重

把目标权重写入临时 JSON，用于下一步：
```json
{
  "categories": {
    "A_broad": {"target_weight": 0.25, "codes": ["510300"]},
    "B_dividend": {"target_weight": 0.20, "codes": ["510880", "512890"]},
    ...
  }
}
```

### 5. 选品
参考 skill 的 `agents/selection.md`：在每个 category 下选 1-2 只 ETF（用 5 把尺子打分）。

### 6. 组合优化
```bash
python scripts/portfolio_optimize.py \
    --target /tmp/target_allocation.json \
    --positions data/positions.json \
    --prices data/etf_prices/ \
    --method ${ARGUMENTS:-risk_parity} \
    --output data/proposed_trades.json
```

### 7. 风控检查（必经）
调用 **risk-manager subagent**：
- 加载 `data/proposed_trades.json`
- 跑硬约束 + 流动性 + 相关性 + 风险指标
- 如否决 → **回到第 5 步**调整选品或权重；最多重试 2 次
- 如通过 → 继续

### 8. 生成调仓单
用 skill 的 `templates/trade_ticket.md` 模板，输出：
- `logs/reports/YYYY-MM-DD-trade-ticket.md`
- 卖出清单 + 买入清单 + 调仓后目标持仓 + 执行建议

### 9. 决策日志
用 skill 的 `templates/decision_log.md` 模板，输出到：
- `logs/decisions/YYYY-MM-DD-monthly-rebalance.md`
- 必须含 6 部分：摘要 / 市场快照 / 各 agent 输出 / 假设 / 触发条件 / 复盘节点

### 10. 输出给用户

按 PM agent 的标准输出格式：

```
## 1. 当前判断（一句话）
## 2. 关键依据（3-5 条带数字的事实）
## 3. 调仓建议（表格）
## 4. 触发止损/止盈条件
## 5. 风险提示
```

末尾补一句：
> ⚠️ 这是 dry-run，未实际下单。如确认执行，请在券商 APP 操作；执行完成后回来运行 `/update-positions` 更新持仓状态。

## 注意

- 整个流程**不直接修改** `data/positions.json`，等用户实际成交后再更新
- 各 subagent 的输出必须**整合**为统一叙事，不要拼接
- 数字必须从脚本输出读取，不要在没运行的情况下编造
- 如果 risk-manager 三次否决都失败，停止流程并告知用户
