from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd

from src.data_loader import MarketDataLoader
from src.features import add_features
from src.manual_macro import load_macro_time_series
from src.signal_engine import SignalEngine


REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def run_signal_diagnostics(config: dict, output_prefix: str = "") -> Dict[str, str]:
    """
    Generate research/diagnostics artifacts for signal quality:
    - per ticker: score components + action history
    - overview: action frequencies and score stats per ticker
    """
    loader = MarketDataLoader(config)
    dataset = loader.load_all()
    used_tickers = sorted([str(t) for t in dataset.keys()], key=str)
    configured_tickers = sorted([str(t) for t in config["universe"]["tickers"]], key=str)
    missing_tickers = sorted(list(set(configured_tickers) - set(used_tickers)), key=str)

    macro_ts = load_macro_time_series()[["date", "macro_composite"]].sort_values("date")
    engine = SignalEngine(config)

    per_ticker_paths: Dict[str, str] = {}
    overview_rows: List[dict] = []
    combined_rows: List[pd.DataFrame] = []

    for ticker, df in dataset.items():
        feat = add_features(df, config).sort_values("date").reset_index(drop=True)

        # Align macro composite to each trading date (as-of join).
        merged = pd.merge_asof(
            feat,
            macro_ts,
            on="date",
            direction="backward",
        )
        merged["macro_composite"] = merged["macro_composite"].fillna(0.0)

        rows: List[dict] = []
        for _, row in merged.iterrows():
            macro_score = float(row["macro_composite"])
            comp = engine.explain_score(row, macro_score)
            action = engine._decide_action(comp["signal_score"], row)

            rows.append(
                {
                    "ticker": ticker,
                    "date": row["date"],
                    "close": row["close"],
                    "trend_score": row["trend_score"],
                    "momentum_score": row["momentum_score"],
                    "mean_reversion_score": row["mean_reversion_score"],
                    "breakout_score": row["breakout_score"] + row["breakdown_score"],
                    "relative_strength": row["relative_strength_proxy"],
                    "rsi": row["rsi"],
                    "adx": row["adx"],
                    "atr": row["atr"] if pd.notna(row["atr"]) else 0.0,
                    "macro_score": macro_score,
                    "signal_score": comp["signal_score"],
                    "action": action,
                    # contributions
                    "trend_contrib": comp["trend_contrib"],
                    "momentum_contrib": comp["momentum_contrib"],
                    "mean_reversion_contrib": comp["mean_reversion_contrib"],
                    "breakout_contrib": comp["breakout_contrib"],
                    "relative_strength_contrib": comp["relative_strength_contrib"],
                    "macro_contrib": comp["macro_contrib"],
                    "volatility_penalty": comp["volatility_penalty"],
                    "overbought_penalty": comp["overbought_penalty"],
                    "oversold_bonus": comp["oversold_bonus"],
                    "trend_strength_bonus": comp["trend_strength_bonus"],
                    "raw_total": comp["raw_total"],
                }
            )

        hist = pd.DataFrame(rows)
        hist_path = REPORT_DIR / f"{output_prefix}signals_history_{ticker}.csv"
        hist.to_csv(hist_path, index=False)
        per_ticker_paths[ticker] = str(hist_path)
        combined_rows.append(hist)

        if not hist.empty:
            action_counts = hist["action"].value_counts(normalize=True)
            def _pct(name: str) -> float:
                return float(action_counts.get(name, 0.0))

            overview_rows.append(
                {
                    "ticker": ticker,
                    "start_date": str(hist["date"].min()),
                    "end_date": str(hist["date"].max()),
                    "n_rows": int(len(hist)),
                    "buy_pct": _pct("BUY"),
                    "hold_pct": _pct("HOLD"),
                    "sell_pct": _pct("SELL"),
                    "signal_score_mean": float(hist["signal_score"].mean()),
                    "signal_score_std": float(hist["signal_score"].std()),
                    "signal_score_min": float(hist["signal_score"].min()),
                    "signal_score_max": float(hist["signal_score"].max()),
                }
            )

    overview_path = REPORT_DIR / f"{output_prefix}signals_overview.csv"
    overview_df = pd.DataFrame(overview_rows).sort_values("ticker") if overview_rows else pd.DataFrame()
    overview_df.to_csv(overview_path, index=False)

    combined_path = REPORT_DIR / f"{output_prefix}signals_combined.csv"
    combined = pd.concat(combined_rows, ignore_index=True) if combined_rows else pd.DataFrame()
    combined.to_csv(combined_path, index=False)

    return {
        "used_tickers": ",".join(used_tickers),
        "missing_tickers": ",".join(missing_tickers),
        "overview": str(overview_path),
        "combined": str(combined_path),
        **per_ticker_paths,
    }

