# 月度复盘 - {{YEAR}} 年 {{MONTH}} 月

## 一、收益总览

| 指标 | 本月 | 年初至今 | 自起始日 |
|------|------|---------|---------|
| 组合收益 | {{MONTHLY_RET}} | {{YTD_RET}} | {{ITD_RET}} |
| 基准（60/40） | {{BENCHMARK_M}} | {{BENCHMARK_YTD}} | {{BENCHMARK_ITD}} |
| 超额 | {{EXCESS_M}} | {{EXCESS_YTD}} | {{EXCESS_ITD}} |
| 最大回撤 | {{MDD_M}} | {{MDD_YTD}} | {{MDD_ITD}} |
| 夏普比率 | - | - | {{SHARPE}} |
| 年化波动率 | - | - | {{VOL_ANNUAL}} |

## 二、归因分析

### 主动收益拆解
| 来源 | 贡献 |
|------|------|
| 资产配置 | {{ALLOCATION_CONTRIB}} |
| 选品 | {{SELECTION_CONTRIB}} |
| 交互项 | {{INTERACTION_CONTRIB}} |
| **合计主动收益** | {{ACTIVE_RETURN}} |

### 单仓位贡献
{{POSITION_ATTRIBUTION_TABLE}}

## 三、宏观回顾

### 本月发生的关键事件
{{MONTHLY_EVENTS}}

### 宏观状态变化
- 月初象限：{{REGIME_START}}
- 月末象限：{{REGIME_END}}
- 是否发生切换：{{REGIME_SWITCHED}}

### 关键宏观数据演变
{{MACRO_DATA_TIMELINE}}

## 四、决策复盘

### 本月所有决策
{{MONTH_DECISIONS_LIST}}

### 决策正确性自评
| 决策 | 日期 | 是否兑现假设 | 收益贡献 | 教训 |
|------|------|-------------|---------|------|
| {{DECISION_REVIEW_TABLE}} |

## 五、行为偏差体检

- [ ] 过度交易？本月调仓 {{TRADE_COUNT}} 次，换手率 {{TURNOVER}}
- [ ] 业绩追涨？{{CHASING_CHECK}}
- [ ] 长期亏损不止损？{{NO_STOPLOSS_CHECK}}
- [ ] 锚定效应？{{ANCHORING_CHECK}}
- [ ] 情绪化交易？{{EMOTIONAL_CHECK}}

## 六、下月策略展望

### 当前最关键的 3 个问题
1. {{KEY_QUESTION_1}}
2. {{KEY_QUESTION_2}}
3. {{KEY_QUESTION_3}}

### 准备好的应对方案
| 触发条件 | 行动 |
|----------|------|
| {{TRIGGER_RESPONSE_TABLE}} |

### 下月目标权重（如有变化）
{{NEXT_MONTH_TARGET_WEIGHTS}}

## 七、给自己的话

{{SELF_REFLECTION}}

---

*生成时间：{{GENERATED_AT}}*
*下次月度复盘：{{NEXT_MONTHLY_REVIEW}}*
