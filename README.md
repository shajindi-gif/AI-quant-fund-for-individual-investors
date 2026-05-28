# AI Quant Fund v1

这是一个个人版 AI 量化交易研究系统 v1。

## 当前功能

- 读取 ETF 历史行情
- 计算基础特征
- 生成趋势信号
- 做基础风险判断
- 生成日报

## 后续功能

- 接入新闻 AI 分析
- 接入真实账户持仓
- 接入自动调仓
- 接入回测模块

## 环境准备（macOS / Homebrew Python）

系统 Python 受 PEP 668 保护，**不要**全局 `pip install`。使用项目虚拟环境：

```bash
# 一键安装依赖（含 akshare）
bash scripts/setup.sh
source .venv/bin/activate

# 验证
python -c "import akshare as ak; print(ak.__version__)"

# 拉取 config/symbols.yaml 中的 ETF 日线 → data/raw/
bash scripts/download.sh
# 或: python download_etf_data.py
```

若 AkShare 报 `ProxyError` 或连不上 `push2his.eastmoney.com`，请用 `scripts/download.sh`（会临时取消代理环境变量），或在终端关闭 VPN/系统代理后重试。

Cursor / VS Code：打开本项目后选择解释器 **`.venv/bin/python`**（本地已生成 `.venv` 时）。

## 运行策略与日报

```bash
source .venv/bin/activate
python main.py
```

`data/raw/` 与 `reports/` 在本地生成，已写入 `.gitignore`，不提交 GitHub；换机器后重新 `bash scripts/download.sh` 即可。

## CSV 数据格式

将行情放到 `data/raw/510300.csv` 这类路径，格式如下：

```csv
date,open,high,low,close,volume
2025-01-02,3.95,3.98,3.90,3.96,1234567
2025-01-03,3.96,4.01,3.94,3.99,2234567
2025-01-06,4.00,4.03,3.97,4.02,1834567
```
