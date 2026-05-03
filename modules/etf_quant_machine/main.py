from __future__ import annotations

import argparse
from pathlib import Path
import json
from datetime import datetime
import logging

import pandas as pd

from src.logging_utils import setup_logging
from src.config_loader import load_config
from src.data_loader import MarketDataLoader
from src.manual_macro import load_latest_macro_signal
from src.signal_engine import SignalEngine
from src.portfolio import PortfolioConstructor
from src.backtester import Backtester
from src.reporting import save_daily_outputs, save_backtest_outputs, save_run_metadata
from src.signal_diagnostics import run_signal_diagnostics


POSITIONS_PATH = Path('data/processed/current_positions.json')
logger = logging.getLogger(__name__)


def read_current_positions() -> dict:
    if not POSITIONS_PATH.exists():
        return {}
    with POSITIONS_PATH.open('r', encoding='utf-8') as f:
        return json.load(f)


def run_daily() -> None:
    config = load_config()
    loader = MarketDataLoader(config)
    dataset = loader.load_all()
    macro_input = load_latest_macro_signal()

    engine = SignalEngine(config)
    signals = engine.generate_latest_signals(dataset, macro_input)

    portfolio_builder = PortfolioConstructor(config)
    target_portfolio = portfolio_builder.build_target_portfolio(signals)
    current_positions = read_current_positions()
    order_sheet = portfolio_builder.build_order_sheet(target_portfolio, current_positions)

    save_daily_outputs(signals, target_portfolio, order_sheet, macro_input)
    save_run_metadata({
        "command": "run-daily",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project": config.get("project", {}),
        "dataset": {
            t: {"n_rows": int(len(df)), "start": str(df["date"].iloc[0]), "end": str(df["date"].iloc[-1])}
            for t, df in dataset.items()
        },
        "macro_input": {
            "date": str(macro_input.get("date")),
            "macro_composite": float(macro_input.get("macro_composite", 0.0)),
        },
    })
    print('Daily run complete. Files saved under reports/.')


def run_backtest() -> None:
    config = load_config()
    loader = MarketDataLoader(config)
    dataset = loader.load_all()

    macro_input = load_latest_macro_signal()
    macro_bias = float(macro_input.get('macro_composite', 0.0))

    bt = Backtester(config)
    equity, summary = bt.run(dataset, macro_bias=macro_bias)
    save_backtest_outputs(equity, summary)
    save_run_metadata({
        "command": "backtest",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project": config.get("project", {}),
        "dataset": {
            t: {"n_rows": int(len(df)), "start": str(df["date"].iloc[0]), "end": str(df["date"].iloc[-1])}
            for t, df in dataset.items()
        },
        "macro_input": {
            "macro_bias": macro_bias,
        },
    })
    print('Backtest complete. Files saved under reports/.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ETF Quant Machine')
    parser.add_argument('command', choices=['run-daily', 'backtest', 'analyze-signals'])
    args = parser.parse_args()

    setup_logging()
    logger.info("Starting run: %s", args.command)

    if args.command == 'run-daily':
        try:
            run_daily()
        except Exception:
            logger.exception("run-daily failed")
            raise
    elif args.command == 'backtest':
        try:
            run_backtest()
        except Exception:
            logger.exception("backtest failed")
            raise
    elif args.command == 'analyze-signals':
        try:
            config = load_config()
            outputs = run_signal_diagnostics(config)
            save_run_metadata({
                "command": "analyze-signals",
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "config": config,
                "outputs": outputs,
            })
            logger.info("Signal diagnostics complete. Reports saved under reports/.")
        except Exception:
            logger.exception("analyze-signals failed")
            raise
