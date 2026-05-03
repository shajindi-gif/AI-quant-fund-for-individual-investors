from __future__ import annotations

import numpy as np
import pandas as pd


def compute_rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    avg_up = up.ewm(alpha=1 / window, adjust=False).mean()
    avg_down = down.ewm(alpha=1 / window, adjust=False).mean()
    rs = avg_up / avg_down.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def compute_atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift(1)).abs()
    low_close = (df['low'] - df['close'].shift(1)).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window).mean()


def compute_adx(df: pd.DataFrame, window: int = 14) -> pd.Series:
    up_move = df['high'].diff()
    down_move = -df['low'].diff()

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    tr = pd.concat([
        df['high'] - df['low'],
        (df['high'] - df['close'].shift(1)).abs(),
        (df['low'] - df['close'].shift(1)).abs(),
    ], axis=1).max(axis=1)

    atr = tr.rolling(window).mean()
    plus_di = 100 * pd.Series(plus_dm, index=df.index).rolling(window).sum() / atr
    minus_di = 100 * pd.Series(minus_dm, index=df.index).rolling(window).sum() / atr
    dx = ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)) * 100
    return dx.rolling(window).mean().fillna(20)


def add_features(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    out = df.copy()
    signal_cfg = config['signals']
    out['ret_1d'] = out['close'].pct_change()
    out['ret_5d'] = out['close'].pct_change(signal_cfg['lookback_momentum_days'][0])
    out['ret_20d'] = out['close'].pct_change(signal_cfg['lookback_momentum_days'][1])
    out['ret_60d'] = out['close'].pct_change(signal_cfg['lookback_momentum_days'][2])

    out['ma_5'] = out['close'].rolling(5).mean()
    out['ma_10'] = out['close'].rolling(10).mean()
    out['ma_20'] = out['close'].rolling(20).mean()
    out['ma_60'] = out['close'].rolling(60).mean()
    out['std_20'] = out['ret_1d'].rolling(20).std()
    out['vol_ratio'] = out['volume'] / out['volume'].rolling(signal_cfg['volume_window']).mean()
    out['breakout_high'] = out['close'].rolling(signal_cfg['breakout_window']).max().shift(1)
    out['breakout_low'] = out['close'].rolling(signal_cfg['breakout_window']).min().shift(1)
    out['rsi'] = compute_rsi(out['close'], signal_cfg['rsi_window'])
    out['atr'] = compute_atr(out, signal_cfg['adx_window'])
    out['adx'] = compute_adx(out, signal_cfg['adx_window'])

    out['trend_score'] = 0.0
    out.loc[out['ma_5'] > out['ma_20'], 'trend_score'] += 0.35
    out.loc[out['ma_20'] > out['ma_60'], 'trend_score'] += 0.35
    out.loc[out['close'] > out['ma_20'], 'trend_score'] += 0.30

    out['momentum_score'] = (
        out['ret_5d'].fillna(0) * 0.3 +
        out['ret_20d'].fillna(0) * 0.4 +
        out['ret_60d'].fillna(0) * 0.3
    )

    mr_days = signal_cfg['mean_reversion_days']
    out['mean_reversion_score'] = -out['close'].pct_change(mr_days).fillna(0)
    out['breakout_score'] = np.where(out['close'] > out['breakout_high'], 1.0, 0.0)
    out['breakdown_score'] = np.where(out['close'] < out['breakout_low'], -1.0, 0.0)
    out['relative_strength_proxy'] = out['ret_20d'].fillna(0) / out['std_20'].replace(0, np.nan)
    out['relative_strength_proxy'] = out['relative_strength_proxy'].replace([np.inf, -np.inf], 0).fillna(0)
    return out
