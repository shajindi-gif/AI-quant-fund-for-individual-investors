from __future__ import annotations

from pathlib import Path
import logging

import pandas as pd


MANUAL_INPUT_PATH = Path('data/processed/manual_macro_input.csv')
logger = logging.getLogger(__name__)


def load_latest_macro_signal() -> dict:
    if not MANUAL_INPUT_PATH.exists():
        raise FileNotFoundError('manual_macro_input.csv not found under data/processed/')

    df = pd.read_csv(MANUAL_INPUT_PATH)
    if df.empty:
        raise ValueError('manual_macro_input.csv is empty')

    required_cols = [
        'date',
        'regime_score',
        'liquidity_score',
        'news_sentiment_score',
        'china_score',
        'us_score',
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"manual_macro_input.csv missing required columns: {missing}")

    df['date'] = pd.to_datetime(df['date'])
    if df['date'].isna().all():
        raise ValueError("manual_macro_input.csv: all `date` values are invalid.")
    row = df.sort_values('date').iloc[-1].to_dict()

    total = (
        row.get('regime_score', 0)
        + row.get('liquidity_score', 0)
        + row.get('news_sentiment_score', 0)
        + 0.5 * row.get('china_score', 0)
        + 0.5 * row.get('us_score', 0)
    )

    normalized = max(-1.0, min(1.0, total / 6.0))
    row['macro_composite'] = normalized

    # Warn only (do not change behavior): helps catch accidental out-of-range inputs.
    score_fields = ['regime_score', 'liquidity_score', 'news_sentiment_score', 'china_score', 'us_score']
    for f in score_fields:
        v = row.get(f)
        if v is None:
            continue
        try:
            fv = float(v)
            if fv < -2 or fv > 2:
                logger.warning("manual_macro_input.csv: `%s` is out of expected range [-2, 2]: %s", f, v)
        except (TypeError, ValueError):
            logger.warning("manual_macro_input.csv: `%s` is not numeric: %r", f, v)

    return row


def load_macro_time_series() -> pd.DataFrame:
    """
    Load full manual macro input as time series for diagnostics.

    Returns a dataframe sorted by date with `macro_composite`.
    """
    if not MANUAL_INPUT_PATH.exists():
        raise FileNotFoundError('manual_macro_input.csv not found under data/processed/')

    df = pd.read_csv(MANUAL_INPUT_PATH)
    if df.empty:
        raise ValueError('manual_macro_input.csv is empty')

    required_cols = [
        'date',
        'regime_score',
        'liquidity_score',
        'news_sentiment_score',
        'china_score',
        'us_score',
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"manual_macro_input.csv missing required columns: {missing}")

    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').drop_duplicates(subset=['date'], keep='last').reset_index(drop=True)
    if df['date'].isna().all():
        raise ValueError("manual_macro_input.csv: all `date` values are invalid.")

    total = (
        df['regime_score'].astype(float)
        + df['liquidity_score'].astype(float)
        + df['news_sentiment_score'].astype(float)
        + 0.5 * df['china_score'].astype(float)
        + 0.5 * df['us_score'].astype(float)
    )
    normalized = total / 6.0
    normalized = normalized.clip(lower=-1.0, upper=1.0)
    df['macro_composite'] = normalized
    return df
