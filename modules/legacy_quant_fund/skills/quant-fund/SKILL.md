---
name: quant-fund
description: 个人量化基金 ETF 投资全流程运营 skill。当用户需要做 ETF 资产配置、月度调仓、组合风险检查、宏观策略更新、技术信号研判、写投资日报或月度复盘、做决策归因时使用。覆盖 A 股/港股/跨境 ETF 的研究-投决-执行-风控-复盘完整链条。无论用户是否明确说"量化基金"，只要涉及 ETF 投资决策、组合优化、仓位调整、宏观资产配置判断，都应使用此 skill。
---

# Quant Fund Operating Skill

这是一个为个人投资者打造的"机构化流程"ETF 投资 skill。它不预测涨跌，它做的是把买卖决策流程模块化、纪律化、可复盘化。

## 核心定位

- **资金规模假设**：人民币 20–50 万级别个人账户
- **标的**：仅 ETF（A 股、港股通、跨境）
- **频率**：月度调仓 + 事件触发战术调整
- **持仓数**：3–6 只 ETF
- **风格**：核心-卫星（Core-Satellite）

> ⚠️ 重要：本 skill 输出的是**有据可查的决策建议**，不是投资建议。最终下单决定由用户做。所有决策必须落到 `decision_log.md`，留痕。

## 触发场景

只要用户提到以下任意一项，立即激活本 skill：

- "本月调仓"、"月度复盘"、"重新平衡"
- "宏观更新"、"现在该买什么 ETF"
- "我的组合风险怎么样"、"该减仓吗"
- "帮我看看 XX ETF"（涉及具体 ETF 代码）
- "归因"、"业绩复盘"、"年度总结"
- "建仓"、"加仓"、"换仓"
- 用户提到具体 ETF 代码（510300、159915、513100 等）

## 核心工作流

### 工作流 A：月度全面调仓（每月最后 5 个交易日触发）

依次执行（**严格按顺序，不跳步**）：

1. **数据刷新**：`bash scripts/fetch_etf_data.py --universe data/etf_universe.csv`
2. **宏观研判**：读 `agents/macro.md`，调用对应 agent 输出宏观状态报告
3. **状态识别**：读 `agents/regime.md`，输出当前所处的"增长×通胀"四象限
4. **大类配置**：读 `agents/allocation.md`，给出股/债/商品/现金的目标比例
5. **具体选品**：读 `agents/selection.md`，在每类资产下选 1–2 只最优 ETF
6. **组合优化**：`bash scripts/portfolio_optimize.py`，给出建议权重
7. **风控检查**：读 `agents/risk.md`，检查约束、计算 VaR、回撤
8. **生成调仓单**：套用 `templates/trade_ticket.md`
9. **决策落档**：套用 `templates/decision_log.md`，写明每个仓位变动的理由

### 工作流 B：日常监控（每个交易日早盘前）

简版工作流，只在以下条件下触发深度分析：
- 任何持仓 ETF 单日波动 > 3%
- 重大宏观事件（央行降息、CPI 超预期、关税等）
- 用户主动询问

否则只生成 `templates/daily_brief.md` 的简版。

### 工作流 C：单只 ETF 深度研判

用户问"XX ETF 现在能不能买"时：
1. 读 `agents/technical.md` + `agents/fundamental.md`
2. 拉取该 ETF 历史数据 + 底层指数估值
3. 输出"评分卡"：估值分位、动量、波动率、相对强度、规模流动性
4. 给出"在当前组合中应占权重"建议（不是孤立的"买/不买"）

### 工作流 D：月度归因复盘

每月第一个交易日：
1. 读 `agents/attribution.md`
2. 计算上月组合收益 vs 基准（沪深300）
3. 拆分为：资产配置贡献 / 选品贡献 / 择时贡献
4. 套用 `templates/monthly_review.md`

## 永远遵守的硬约束

这些是 hard constraint，任何 agent 输出违反这些都必须被 risk_agent 否决：

| 约束 | 阈值 |
|------|------|
| 单一 ETF 仓位上限 | ≤ 30% |
| 单一行业 ETF 上限 | ≤ 25% |
| 现金最低保留 | ≥ 5% |
| 调仓最短间隔 | ≥ 4 周（除非触发风控线） |
| 单次调仓换手率上限 | ≤ 50% |
| 组合最大回撤警戒线 | -15%（触及强制降仓位） |
| 组合最大回撤强平线 | -20%（触及全部转货币 ETF） |

## Agent 调用方式

每个 `agents/*.md` 都是一个**专门角色的系统提示词**。当主线程需要调用某个 agent 时：

1. 读取该 agent 的 .md 文件
2. 把内容作为 sub-task 的 system context
3. 提供它需要的输入数据（市场数据、当前持仓等）
4. 把它的输出汇总给 PM agent 做最终决策

## 关键文件索引

- `agents/pm.md` - 总协调，唯一直接对话用户的角色
- `agents/macro.md` - 宏观分析师
- `agents/news.md` - 财经新闻聚合
- `agents/regime.md` - 宏观状态识别（增长×通胀四象限）
- `agents/technical.md` - 技术分析（动量、均线、RS）
- `agents/fundamental.md` - 基本面（估值分位、股息、盈利）
- `agents/allocation.md` - 大类资产配置
- `agents/selection.md` - 同类 ETF 选品
- `agents/risk.md` - 风控检查与压力测试
- `agents/attribution.md` - 业绩归因
- `agents/journal.md` - 决策日志记录员

- `scripts/fetch_etf_data.py` - 数据获取（akshare）
- `scripts/compute_signals.py` - 信号计算
- `scripts/portfolio_optimize.py` - 组合优化（风险平价 + 等权 + 凯利缩水）
- `scripts/risk_metrics.py` - VaR、回撤、相关性
- `scripts/backtest.py` - 简易历史回测

- `templates/daily_brief.md` - 日报模板
- `templates/monthly_review.md` - 月度复盘模板
- `templates/trade_ticket.md` - 调仓单模板
- `templates/decision_log.md` - 决策日志模板

- `data/etf_universe.csv` - ETF 池（默认 20 只覆盖主要资产）
- `data/positions.json` - 当前持仓（用户填）

- `reference/etf_list_china.md` - 中国主要 ETF 分类清单
- `reference/regime_framework.md` - 宏观状态识别框架
- `reference/risk_parity_guide.md` - 风险平价方法论

## 写作风格要求（输出给用户的内容）

- **简洁、不堆砌**：用户是中文母语者，避免翻译腔
- **量化先行**：每个观点配数字（"沪深300 PE 分位 32%"，不是"估值偏低"）
- **理由可证伪**：不写"市场情绪谨慎"这种废话；写"两融余额周环比 -2.3%、北向资金连续 5 日净流出"
- **决策必有触发条件**：建议加仓必须给出"如果 XX 跌破 YY 则止损"
- **不预测点位**：拒绝回答"沪深 300 能涨到多少"这类问题
