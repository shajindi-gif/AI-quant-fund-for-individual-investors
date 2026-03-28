from __future__ import annotations

import pandas as pd


def generate_signal(df: pd.DataFrame) -> pd.DataFrame:
    """
    趋势评分：
    1. 20日收益率 > 0
    2. 60日收益率 > 0
    3. close > ma20
    4. close > ma60

    每满足一项 +1，总分 0~4
    """
    out = df.copy()
    out["score"] = 0

    out.loc[out["ret_20d"] > 0, "score"] += 1
    out.loc[out["ret_60d"] > 0, "score"] += 1
    out.loc[out["close"] > out["ma20"], "score"] += 1
    out.loc[out["close"] > out["ma60"], "score"] += 1

    out["trend_signal"] = 0
    out.loc[out["score"] >= 3, "trend_signal"] = 1
    out.loc[out["score"] <= 1, "trend_signal"] = -1

    return out
