from __future__ import annotations

from typing import Dict, List
import logging

import pandas as pd
import numpy as np

from src.features import add_features
from src.signal_engine import SignalEngine


class Backtester:
    def __init__(self, config: dict):
        self.config = config
        self.engine = SignalEngine(config)
        self.initial_capital = config['project']['initial_capital']
        self.cost_rate = config['project']['commission_rate'] + config['project']['slippage_rate']
        self.max_positions = config['project']['max_positions']
        self.max_weight = config['risk']['per_position_max_weight']
        self.total_exposure_cap = config['risk']['total_exposure_cap']
        self.daily_turnover_cap = config['risk']['daily_turnover_cap']
        self.max_portfolio_drawdown = config['risk']['max_portfolio_drawdown']
        self.cash_buffer = config['risk']['cash_buffer']
        self.logger = logging.getLogger(__name__)

    def run(self, dataset: Dict[str, pd.DataFrame], macro_bias: float = 0.0) -> tuple[pd.DataFrame, pd.DataFrame]:
        featured = {ticker: add_features(df, self.config) for ticker, df in dataset.items()}
        common_dates = sorted(set.intersection(*[set(df['date']) for df in featured.values()]))
        records: List[dict] = []
        current_weights: Dict[str, float] = {}
        portfolio_value = self.initial_capital
        portfolio_cummax = portfolio_value

        for date in common_dates[80:]:
            daily_rows = []
            for ticker, df in featured.items():
                sub = df[df['date'] <= date]
                row = sub.iloc[-1]
                score = self.engine._compute_total_score(row, macro_bias)
                action = self.engine._decide_action(score, row)
                daily_rows.append({
                    'ticker': ticker,
                    'close': row['close'],
                    'ret_1d': row['ret_1d'] if pd.notna(row['ret_1d']) else 0.0,
                    'score': score,
                    'action': action,
                })

            daily = pd.DataFrame(daily_rows).sort_values('score', ascending=False)
            picks = daily[daily['action'] != 'SELL'].head(self.max_positions).copy()
            if not picks.empty:
                picks['w'] = picks['score'].clip(lower=0.01)
                picks['w'] = picks['w'] / picks['w'].sum()
                picks['w'] = picks['w'].clip(upper=self.max_weight)
                picks['w'] = picks['w'] / picks['w'].sum()
                gross_cap = min(1.0 - self.cash_buffer, self.total_exposure_cap)
                picks['w'] = picks['w'] * gross_cap
                target_weights = dict(zip(picks['ticker'], picks['w']))
            else:
                target_weights = {}

            # Risk control: if current drawdown breaches, move to cash for this day.
            if portfolio_value / portfolio_cummax - 1.0 < -self.max_portfolio_drawdown:
                if current_weights:
                    self.logger.warning(
                        "Drawdown cap hit on %s (drawdown=%.4f). Moving to cash.",
                        str(date),
                        portfolio_value / portfolio_cummax - 1.0,
                    )
                target_weights = {}

            # Turnover definition: sum of absolute weight deltas (fraction of portfolio reallocated).
            raw_turnover = sum(
                abs(target_weights.get(t, 0.0) - current_weights.get(t, 0.0))
                for t in (set(target_weights) | set(current_weights))
            )

            if self.daily_turnover_cap is not None and raw_turnover > self.daily_turnover_cap and raw_turnover > 0:
                scale = self.daily_turnover_cap / raw_turnover
                self.logger.warning(
                    "Turnover cap hit on %s (turnover=%.4f, cap=%.4f). Scaling trades by %.4f.",
                    str(date),
                    raw_turnover,
                    self.daily_turnover_cap,
                    scale,
                )
                scaled_target: Dict[str, float] = {}
                for t in (set(target_weights) | set(current_weights)):
                    cur_w = current_weights.get(t, 0.0)
                    tgt_w = target_weights.get(t, 0.0)
                    new_w = cur_w + (tgt_w - cur_w) * scale
                    if new_w > 0:
                        scaled_target[t] = float(new_w)
                target_weights = scaled_target

            turnover = sum(
                abs(target_weights.get(t, 0.0) - current_weights.get(t, 0.0))
                for t in (set(target_weights) | set(current_weights))
            )

            pv0 = portfolio_value
            trading_cost = turnover * pv0 * self.cost_rate

            # Portfolio return uses weights at the start of the day.
            portfolio_ret = 0.0
            for _, row in daily.iterrows():
                portfolio_ret += current_weights.get(row['ticker'], 0.0) * float(row['ret_1d'])

            daily_return = portfolio_ret - (trading_cost / pv0 if pv0 > 0 else 0.0)
            portfolio_value = pv0 * (1 + daily_return)

            current_weights = target_weights

            if portfolio_value > portfolio_cummax:
                portfolio_cummax = portfolio_value

            records.append({
                'date': date,
                'portfolio_value': portfolio_value,
                'daily_return': daily_return,
                'turnover': turnover,
                'positions': len(current_weights),
            })

        equity = pd.DataFrame(records)
        summary = self._summarize(equity)
        return equity, summary

    def _summarize(self, equity: pd.DataFrame) -> pd.DataFrame:
        if equity.empty:
            return pd.DataFrame([{'metric': 'error', 'value': 'no data'}])

        returns = equity['daily_return'].fillna(0)
        annual_return = (1 + returns.mean()) ** 252 - 1
        annual_vol = returns.std() * np.sqrt(252)
        sharpe = annual_return / annual_vol if annual_vol > 0 else 0
        cummax = equity['portfolio_value'].cummax()
        drawdown = equity['portfolio_value'] / cummax - 1
        max_dd = drawdown.min()
        win_rate = (returns > 0).mean()

        return pd.DataFrame([
            {'metric': 'final_portfolio_value', 'value': round(float(equity['portfolio_value'].iloc[-1]), 2)},
            {'metric': 'annual_return', 'value': round(float(annual_return), 4)},
            {'metric': 'annual_volatility', 'value': round(float(annual_vol), 4)},
            {'metric': 'sharpe_proxy', 'value': round(float(sharpe), 4)},
            {'metric': 'max_drawdown', 'value': round(float(max_dd), 4)},
            {'metric': 'win_rate', 'value': round(float(win_rate), 4)},
        ])
