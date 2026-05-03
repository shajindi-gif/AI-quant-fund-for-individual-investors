# 日报 - {{DATE}}

## 一、市场速览

| 指标 | 收盘 | 涨跌 | 成交额 |
|------|------|------|--------|
| 沪深300 | {{HS300}} | {{HS300_CHG}} | {{HS300_VOL}}亿 |
| 中证500 | {{ZZ500}} | {{ZZ500_CHG}} | {{ZZ500_VOL}}亿 |
| 创业板  | {{CYB}} | {{CYB_CHG}} | {{CYB_VOL}}亿 |
| 恒生科技| {{HSTECH}} | {{HSTECH_CHG}} | - |
| 纳斯达克| {{NDX}} | {{NDX_CHG}} | - |
| 10Y国债 | {{CGB10Y}}% | {{CGB10Y_CHG}}bp | - |
| USDCNY  | {{USDCNY}} | {{USDCNY_CHG}} | - |
| 黄金    | {{GOLD}} | {{GOLD_CHG}} | - |

## 二、持仓表现

| ETF | 代码 | 收盘价 | 当日涨跌 | 累计收益 | 目标权重 | 当前权重 | 偏离度 |
|-----|------|--------|---------|---------|---------|---------|--------|
| {{HOLDINGS_TABLE}} |

**组合当日**：{{PORTFOLIO_DAILY}}（vs 60/40 基准 {{BENCHMARK_DAILY}}）
**累计收益**：{{PORTFOLIO_CUM}}（基准 {{BENCHMARK_CUM}}）
**距高点回撤**：{{DRAWDOWN}}

## 三、风险灯

- 风控线状态：{{RISK_LIGHT}}（🟢 安全 / 🟡 黄色 / 🟠 橙色 / 🔴 红色）
- 30日 VaR(95%)：{{VAR}}
- 组合年化波动率：{{VOL}}
- 持仓最大相关性：{{MAX_CORR}}

## 四、关键事件（过去 24h）

{{NEWS_BULLETS}}

## 五、今日 PM 备注

{{PM_NOTE}}

---

*生成时间：{{GENERATED_AT}}*
*数据来源：akshare / 中债登 / Wind*
*下次例行更新：{{NEXT_UPDATE}}*
