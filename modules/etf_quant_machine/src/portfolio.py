from __future__ import annotations

from typing import Dict

import pandas as pd


class PortfolioConstructor:
    def __init__(self, config: dict):
        self.config = config
        self.risk_cfg = config['risk']
        self.initial_capital = config['project']['initial_capital']

    def build_target_portfolio(self, signals: pd.DataFrame) -> pd.DataFrame:
        tradable = signals.copy()
        tradable = tradable[tradable['action'] != 'SELL'].copy()
        tradable = tradable.sort_values('signal_score', ascending=False).head(self.config['project']['max_positions'])

        if tradable.empty:
            return pd.DataFrame(columns=['ticker', 'target_weight', 'target_value', 'close', 'shares'])

        raw_weights = tradable['signal_score'].clip(lower=0.01)
        raw_weights = raw_weights / raw_weights.sum()
        raw_weights = raw_weights.clip(upper=self.risk_cfg['per_position_max_weight'])
        raw_weights = raw_weights / raw_weights.sum()

        gross_cap = 1 - self.risk_cfg['cash_buffer']
        gross_cap = min(gross_cap, self.risk_cfg['total_exposure_cap'])
        tradable['target_weight'] = raw_weights * gross_cap
        tradable['target_value'] = tradable['target_weight'] * self.initial_capital
        tradable['shares'] = (tradable['target_value'] / tradable['close']).fillna(0).astype(int)
        return tradable[['ticker', 'close', 'signal_score', 'action', 'target_weight', 'target_value', 'shares', 'atr']]

    def build_order_sheet(self, target_portfolio: pd.DataFrame, current_positions: Dict[str, int] | None = None) -> pd.DataFrame:
        current_positions = current_positions or {}
        rows = []
        target_map = {str(row['ticker']): int(row['shares']) for _, row in target_portfolio.iterrows()}
        current_positions = {str(k): int(v) for k, v in current_positions.items()}
        all_tickers = sorted(set(current_positions.keys()) | set(target_map.keys()), key=str)

        for ticker in all_tickers:
            current_shares = int(current_positions.get(ticker, 0))
            target_shares = int(target_map.get(ticker, 0))
            delta = target_shares - current_shares
            if delta > 0:
                side = 'BUY'
            elif delta < 0:
                side = 'SELL'
            else:
                side = 'HOLD'
            rows.append({
                'ticker': ticker,
                'current_shares': current_shares,
                'target_shares': target_shares,
                'delta_shares': delta,
                'side': side,
            })
        return pd.DataFrame(rows)
