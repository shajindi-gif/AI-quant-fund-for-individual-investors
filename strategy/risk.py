from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"


def load_risk_limits() -> dict:
    with open(CONFIG_DIR / "risk_limits.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def evaluate_risk(latest_market_rows: list[dict], equity_curve: pd.Series | None = None) -> dict:
    config = load_risk_limits()

    high_vol_threshold = config["risk"]["high_vol_threshold"]
    drawdown_warning = config["risk"]["drawdown_warning"]
    drawdown_protection = config["risk"]["drawdown_protection"]

    avg_vol = sum(row["vol_20d"] for row in latest_market_rows) / len(latest_market_rows)

    portfolio_drawdown = 0.0
    if equity_curve is not None and len(equity_curve) > 5:
        rolling_max = equity_curve.cummax()
        drawdowns = equity_curve / rolling_max - 1.0
        portfolio_drawdown = float(drawdowns.min())

    regime = "neutral"
    protection_mode = False

    if avg_vol > high_vol_threshold:
        regime = "risk_off"

    if portfolio_drawdown <= -drawdown_warning:
        regime = "cautious"

    if portfolio_drawdown <= -drawdown_protection:
        regime = "protection"
        protection_mode = True

    return {
        "avg_vol": round(avg_vol, 4),
        "portfolio_drawdown": round(portfolio_drawdown, 4),
        "regime": regime,
        "protection_mode": protection_mode,
    }
