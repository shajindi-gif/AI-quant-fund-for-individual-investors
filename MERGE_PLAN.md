# ai_quant_fund 合并计划

## 1. Incoming 来源

### _incoming/leihuo_portfolio_v2

初步判断：
- 包含 app/
- 包含 infra/
- 包含 scripts/
- 包含 data/
- 偏组合/投研/基础设施原型

### _incoming/quant_fund

初步判断：
- 主要包含 infra/
- 包含 postgres、qdrant、redis、minio 等基础设施卷目录
- 更像旧基础设施配置

## 2. 合并目标结构

```text
ai_quant_fund/
├── apps/
│   └── dashboard/
├── packages/
│   ├── data/
│   ├── strategies/
│   ├── backtest/
│   ├── risk/
│   └── reports/
├── infra/
├── scripts/
├── data/
├── reports/
├── docs/
└── _incoming/
