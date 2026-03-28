from __future__ import annotations

import pandas as pd

from strategy.risk import evaluate_risk


def run_risk_check(latest_rows: list[dict]) -> dict:
    # 当前先用假净值曲线占位，后面接真实组合净值
    equity_curve = pd.Series([1.00, 1.01, 1.00, 1.02, 1.015, 1.018, 1.01])
    return evaluate_risk(latest_rows, equity_curve=equity_curve)
