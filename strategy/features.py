from __future__ import annotations

import pandas as pd


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["ret_1d"] = out["close"].pct_change()
    out["ret_20d"] = out["close"].pct_change(20)
    out["ret_60d"] = out["close"].pct_change(60)

    out["ma20"] = out["close"].rolling(20).mean()
    out["ma60"] = out["close"].rolling(60).mean()

    out["vol_20d"] = out["ret_1d"].rolling(20).std()
    out["rolling_max_60d"] = out["close"].rolling(60).max()
    out["drawdown_60d"] = out["close"] / out["rolling_max_60d"] - 1.0

    out = out.dropna().reset_index(drop=True)
    return out
