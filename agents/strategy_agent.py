from __future__ import annotations

from typing import Iterable

from strategy.data_loader import load_all_prices
from strategy.features import add_features
from strategy.portfolio import build_target_weights
from strategy.signal_engine import generate_signal


def run_strategy(*, only: Iterable[str] | None = None) -> dict:
    """
    only: 仅对 yaml 中已配置的子集标的跑信号（例如在 Notebook 里对比部分 ETF）。
    """
    prices = load_all_prices(only=only)
    latest_rows: list[dict] = []
    for symbol, df in prices.items():
        feat_df = add_features(df)
        sig_df = generate_signal(feat_df)
        last = sig_df.iloc[-1].to_dict()
        last["symbol"] = symbol
        latest_rows.append(last)
    target_weights = build_target_weights(latest_rows)
    return {
        "latest_rows": latest_rows,
        "target_weights": target_weights,
    }
