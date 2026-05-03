from __future__ import annotations

from typing import Any, Dict, Iterable, List


def _missing_keys(d: Dict[str, Any], keys: Iterable[str]) -> List[str]:
    return [k for k in keys if k not in d]


def require_dict(config: Any, name: str) -> Dict[str, Any]:
    if not isinstance(config, dict):
        raise TypeError(f"{name} must be a dict, got: {type(config).__name__}")
    return config


def validate_config(config: Dict[str, Any]) -> None:
    """
    Basic configuration validation to catch typos early.

    This is intentionally lightweight (no third-party schema library).
    """
    require_dict(config, "config")

    required_top = ["project", "risk", "signals", "data", "universe", "manual_macro"]
    missing_top = _missing_keys(config, required_top)
    if missing_top:
        raise KeyError(f"Missing top-level config keys: {missing_top}")

    project = require_dict(config["project"], "config.project")
    risk = require_dict(config["risk"], "config.risk")
    signals = require_dict(config["signals"], "config.signals")
    data = require_dict(config["data"], "config.data")
    universe = require_dict(config["universe"], "config.universe")
    manual_macro = require_dict(config["manual_macro"], "config.manual_macro")

    required_project = [
        "name",
        "base_currency",
        "initial_capital",
        "commission_rate",
        "slippage_rate",
        "max_positions",
        "rebalance_mode",
    ]
    missing_project = _missing_keys(project, required_project)
    if missing_project:
        raise KeyError(f"Missing config.project keys: {missing_project}")

    required_risk = [
        "per_position_max_weight",
        "total_exposure_cap",
        "daily_turnover_cap",
        "atr_stop_multiple",
        "trailing_stop_multiple",
        "volatility_target",
        "max_portfolio_drawdown",
        "cash_buffer",
    ]
    missing_risk = _missing_keys(risk, required_risk)
    if missing_risk:
        raise KeyError(f"Missing config.risk keys: {missing_risk}")

    required_signals = [
        "lookback_momentum_days",
        "mean_reversion_days",
        "volume_window",
        "breakout_window",
        "rsi_window",
        "adx_window",
        "timing_threshold_buy",
        "timing_threshold_sell",
        "news_score_weight",
        "trend_weight",
        "momentum_weight",
        "mean_reversion_weight",
        "breakout_weight",
        "relative_strength_weight",
    ]
    missing_signals = _missing_keys(signals, required_signals)
    if missing_signals:
        raise KeyError(f"Missing config.signals keys: {missing_signals}")

    if not isinstance(signals["lookback_momentum_days"], list) or len(signals["lookback_momentum_days"]) < 3:
        raise ValueError("config.signals.lookback_momentum_days must be a list (len>=3).")

    required_data = ["raw_data_dir", "processed_data_dir", "accepted_extensions", "required_columns"]
    missing_data = _missing_keys(data, required_data)
    if missing_data:
        raise KeyError(f"Missing config.data keys: {missing_data}")

    required_universe = ["tickers"]
    missing_universe = _missing_keys(universe, required_universe)
    if missing_universe:
        raise KeyError(f"Missing config.universe keys: {missing_universe}")

    required_manual_macro = ["regime_score_range", "sentiment_score_range"]
    missing_manual_macro = _missing_keys(manual_macro, required_manual_macro)
    if missing_manual_macro:
        raise KeyError(f"Missing config.manual_macro keys: {missing_manual_macro}")

    # Light numeric sanity checks
    if project.get("initial_capital", 0) <= 0:
        raise ValueError("config.project.initial_capital must be > 0")
    if risk.get("cash_buffer", 0) < 0 or risk.get("cash_buffer", 0) >= 1:
        raise ValueError("config.risk.cash_buffer must be in [0, 1)")

