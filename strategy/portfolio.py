from __future__ import annotations

from pathlib import Path

import yaml

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"


def load_risk_limits() -> dict:
    with open(CONFIG_DIR / "risk_limits.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_target_weights(latest_rows: list[dict]) -> dict[str, float]:
    """
    输入每个标的最新一行信号，输出目标仓位
    """
    config = load_risk_limits()
    max_total_equity_weight = config["portfolio"]["max_total_equity_weight"]
    max_single_position_weight = config["portfolio"]["max_single_position_weight"]
    cash_min_weight = config["portfolio"]["cash_min_weight"]

    positive_symbols = [row["symbol"] for row in latest_rows if row["trend_signal"] == 1]

    weights: dict[str, float] = {}
    if not positive_symbols:
        return {"CASH": 1.0}

    raw_weight = min(max_single_position_weight, max_total_equity_weight / len(positive_symbols))

    allocated = 0.0
    for symbol in positive_symbols:
        weights[symbol] = raw_weight
        allocated += raw_weight

    cash_weight = max(1.0 - allocated, cash_min_weight)
    total_before_normalize = allocated + cash_weight

    for k in list(weights.keys()):
        weights[k] = weights[k] / total_before_normalize
    weights["CASH"] = cash_weight / total_before_normalize

    return weights
