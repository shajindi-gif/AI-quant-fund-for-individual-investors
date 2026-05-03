
## 2026-05-03

### 合并来源
- ~/Projects/etf_quant_machine
- ~/Projects/archive/quant-fund-old
- ~/Projects/archive/leihuo_stack/leihuo_portfolio

### 合并目标
- ~/Projects/ai_quant_fund/modules/

### 合并方式
- rsync 复制
- 排除 .git / .venv / venv / __pycache__

### 后续动作
- 统一 requirements.txt
- 统一数据目录 data/
- 统一报告目录 reports/
- 把 ETF 策略改造成 ai_quant_fund 的一个子模块
