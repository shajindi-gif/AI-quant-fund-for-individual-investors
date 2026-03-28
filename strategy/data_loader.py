from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"
CONFIG_DIR = PROJECT_ROOT / "config"
SYMBOLS_PATH = CONFIG_DIR / "symbols.yaml"


def load_symbols() -> list[dict]:
    """
    读取 config/symbols.yaml 中的 etfs 列表。
    之后扩展标的：只需编辑该文件并重新运行 download_etf_data.py。
    """
    with open(SYMBOLS_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    etfs = config.get("etfs")
    if not isinstance(etfs, list) or not etfs:
        raise ValueError(f"{SYMBOLS_PATH} 中必须包含非空列表 etfs")

    for i, row in enumerate(etfs):
        if not isinstance(row, dict) or "symbol" not in row:
            raise ValueError(f"etfs[{i}] 必须是包含 symbol 字段的对象")
        sym = str(row["symbol"]).strip()
        if not sym:
            raise ValueError(f"etfs[{i}] symbol 不能为空")
        row["symbol"] = sym
    return etfs


def etf_codes() -> list[str]:
    """按 symbols.yaml 中的顺序返回 ETF 代码列表。"""
    return [row["symbol"] for row in load_symbols()]


def load_price_data(symbol: str) -> pd.DataFrame:
    """
    读取单个 ETF 行情。
    文件路径: data/raw/{symbol}.csv
    列: date, open, high, low, close, volume
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


def load_all_prices(*, only: Iterable[str] | None = None) -> dict[str, pd.DataFrame]:
    """
    加载 symbols.yaml 中配置的 ETF 行情。

    only: 若指定，仅加载这些代码（须为 yaml 中已配置子集，便于临时对比/回测子集）。
    """
    rows = load_symbols()
    codes = [r["symbol"] for r in rows]
    if only is not None:
        want = {str(s).strip() for s in only}
        unknown = want - set(codes)
        if unknown:
            raise ValueError(
                f"以下代码未在 symbols.yaml 中配置: {sorted(unknown)}。"
                "请先添加标的并下载 CSV。"
            )
        codes = [c for c in codes if c in want]

    data: dict[str, pd.DataFrame] = {}
    for symbol in codes:
        data[symbol] = load_price_data(symbol)
    return data
