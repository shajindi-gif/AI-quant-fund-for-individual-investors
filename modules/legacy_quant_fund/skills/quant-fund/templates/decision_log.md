# 决策日志 - {{DATE}} - {{DECISION_TYPE}}

> 决策ID：{{DECISION_ID}}
> 决策类型：{{DECISION_TYPE}}（月度调仓 / 战术调整 / 触发止损 / 触发止盈 / 紧急避险）
> 决策人：PM Agent + 用户最终确认

## 1. 决策摘要（一句话）

{{DECISION_SUMMARY}}

## 2. 决策时的市场快照

### 市场行情
| 指标 | 数值 |
|------|------|
| 沪深300 | {{HS300}} ({{HS300_CHG}}) |
| 中证500 | {{ZZ500}} ({{ZZ500_CHG}}) |
| 创业板  | {{CYB}} ({{CYB_CHG}}) |
| 10Y国债 | {{CGB10Y}}% ({{CGB10Y_CHG}}bp) |
| USDCNY  | {{USDCNY}} ({{USDCNY_CHG}}) |

### 关键宏观数据（最新一期）
- CPI 同比：{{CPI}}
- PPI 同比：{{PPI}}
- 制造业 PMI：{{PMI}}
- M2 同比：{{M2}}
- 社融存量同比：{{TSF}}

### 当前所处宏观象限
**{{REGIME}}**（置信度：{{REGIME_CONFIDENCE}}）

### 过去 7 天关键事件
{{RECENT_EVENTS}}

## 3. 决策依据（各 agent 输入摘要）

### macro_agent 说
> {{MACRO_INSIGHT}}

### regime_agent 说
> {{REGIME_INSIGHT}}

### technical_agent 说
> {{TECHNICAL_INSIGHT}}

### fundamental_agent 说
> {{FUNDAMENTAL_INSIGHT}}

### allocation_agent 给出的目标权重
{{ALLOCATION_OUTPUT}}

### selection_agent 给出的具体 ETF
{{SELECTION_OUTPUT}}

### risk_agent 审核结果
> {{RISK_REVIEW}}

## 4. 假设与前提

### 本次决策的核心假设
1. **{{ASSUMPTION_1}}**
2. **{{ASSUMPTION_2}}**
3. **{{ASSUMPTION_3}}**

### 假设不成立时的应对
| 假设 | 不成立的标志 | 应对动作 |
|------|------------|---------|
| {{ASSUMPTION_1}} | {{INVALIDATION_1}} | {{RESPONSE_1}} |
| {{ASSUMPTION_2}} | {{INVALIDATION_2}} | {{RESPONSE_2}} |
| {{ASSUMPTION_3}} | {{INVALIDATION_3}} | {{RESPONSE_3}} |

## 5. 触发条件验证清单

| 条件 | 阈值 | 当前值 | 已触发? | 验证日期 |
|------|------|-------|--------|---------|
| {{TRIGGER_TABLE}} |

### 止盈/止损条件
| 条件 | 阈值 | 行动 |
|------|------|------|
| {{STOP_TABLE}} |

## 6. 复盘节点

- [ ] **+30 天复盘**（{{REVIEW_30}}）：核心假设是否成立？
- [ ] **+60 天复盘**（{{REVIEW_60}}）：决策是否兑现预期？
- [ ] **+90 天复盘**（{{REVIEW_90}}）：纳入季度归因
- [ ] **下次调仓时**（{{NEXT_REBALANCE}}）：检查触发条件

### +30 天复盘记录
*（30 天后填写）*

- 假设兑现情况：
- 实际收益贡献：
- 教训与改进：

### +60 天复盘记录
*（60 天后填写）*

### +90 天复盘记录
*（90 天后填写）*

---

## 附录：原始数据快照

```json
{{RAW_DATA_SNAPSHOT}}
```

*生成时间：{{GENERATED_AT}}*
