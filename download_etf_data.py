import akshare as ak
import pandas as pd
from pathlib import Path

symbols = ["510300", "510500", "515180", "518880", "512880", "515000", "513180", "511010"]
out_dir = Path("data/raw")
out_dir.mkdir(parents=True, exist_ok=True)

for symbol in symbols:
    df = ak.fund_etf_hist_em(symbol=symbol, period="daily", adjust="qfq")
    # 不同版本返回列名可能略有差异，先打印看一下
    print(symbol, df.columns.tolist())

    rename_map = {
        "日期": "date",
        "开盘": "open",
        "收盘": "close",
        "最高": "high",
        "最低": "low",
        "成交量": "volume",
    }
    df = df.rename(columns=rename_map)

    keep_cols = ["date", "open", "high", "low", "close", "volume"]
    df = df[keep_cols].copy()
    df.to_csv(out_dir / f"{symbol}.csv", index=False, encoding="utf-8-sig")

print("全部导出完成")
