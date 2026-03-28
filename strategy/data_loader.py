from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "raw"
CONFIG_DIR = BASE_DIR / "config"


def load_symbols() -> list[dict]:
    with open(CONFIG_DIR / "symbols.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config["etfs"]


def load_price_data(symbol: str) -> pd.DataFrame:
    """
    读取单个ETF行情数据。
    默认文件路径: data/raw/{symbol}.csv
    CSV列要求:
    date,open,high,low,close,volume
    """
    file_path = DATA_DIR / f"{symbol}.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"找不到行情文件: {file_path}")

    df = pd.read_csv(file_path)
    required_cols = {"date", "open", "high", "low", "close", "volume"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"{symbol} 缺少列: {missing}")

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def load_all_prices() -> dict[str, pd.DataFrame]:
    symbols = load_symbols()
    data: dict[str, pd.DataFrame] = {}
    for item in symbols:
        symbol = item["symbol"]
        data[symbol] = load_price_data(symbol)
    return data
