"""
compute_signals.py
==================
基于 fetch_etf_data.py 拉下来的价格序列，计算技术信号。

输出:
    - 趋势状态（多头排列/空头排列/震荡）
    - 动量（20/60/252 日）
    - 相对强度排名
    - 波动率分位数
    - 价格位置

用法:
    python compute_signals.py --data-dir data/etf_prices/ --output data/signals.csv
    python compute_signals.py --code 510300  # 单标的详查
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def load_prices(data_dir: str, code: str = None) -> dict:
    """加载所有 parquet 文件，返回 {code: DataFrame}"""
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"数据目录不存在: {data_dir}，请先运行 fetch_etf_data.py")

    out = {}
    for f in data_path.glob("*.parquet"):
        c = f.stem
        if code and c != code:
            continue
        df = pd.read_parquet(f)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").set_index("date")
        out[c] = df
    return out


def compute_trend(close: pd.Series) -> dict:
    """计算均线状态 + 趋势判定"""
    if len(close) < 120:
        return {"ma20": None, "ma60": None, "ma120": None, "trend": "insufficient_data"}

    ma20 = close.rolling(20).mean().iloc[-1]
    ma60 = close.rolling(60).mean().iloc[-1]
    ma120 = close.rolling(120).mean().iloc[-1]

    if ma20 > ma60 > ma120:
        trend = "bull"  # 多头排列
    elif ma20 < ma60 < ma120:
        trend = "bear"  # 空头排列
    else:
        trend = "range"  # 震荡

    return {
        "ma20": round(ma20, 4),
        "ma60": round(ma60, 4),
        "ma120": round(ma120, 4),
        "trend": trend,
        "price_to_ma20": round(close.iloc[-1] / ma20 - 1, 4),
        "price_to_ma60": round(close.iloc[-1] / ma60 - 1, 4),
    }


def compute_momentum(close: pd.Series) -> dict:
    """20/60/252 日动量"""
    out = {}
    for window, label in [(20, "1m"), (60, "3m"), (120, "6m"), (252, "1y")]:
        if len(close) > window:
            out[f"momentum_{label}"] = round(close.iloc[-1] / close.iloc[-window - 1] - 1, 4)
        else:
            out[f"momentum_{label}"] = None
    return out


def compute_volatility(close: pd.Series) -> dict:
    """波动率 + 历史分位数"""
    if len(close) < 252:
        return {"vol_20d_annual": None, "vol_pct_1y": None}

    daily_ret = close.pct_change().dropna()
    vol_20d = daily_ret.tail(20).std() * np.sqrt(252)

    # 滚动 20 日波动率，看当前在过去 1 年的分位
    rolling_vol = daily_ret.rolling(20).std() * np.sqrt(252)
    rolling_vol_1y = rolling_vol.tail(252).dropna()
    if len(rolling_vol_1y) > 30:
        pct = (rolling_vol_1y < vol_20d).mean()
    else:
        pct = None

    return {
        "vol_20d_annual": round(vol_20d, 4),
        "vol_pct_1y": round(pct, 2) if pct is not None else None,
    }


def compute_position(close: pd.Series) -> dict:
    """价格位置：距 52 周高低点"""
    if len(close) < 252:
        return {"dist_to_52w_high": None, "dist_to_52w_low": None}
    high_52w = close.tail(252).max()
    low_52w = close.tail(252).min()
    cur = close.iloc[-1]
    return {
        "dist_to_52w_high": round(cur / high_52w - 1, 4),
        "dist_to_52w_low": round(cur / low_52w - 1, 4),
    }


def compute_relative_strength(prices: dict, benchmark_code: str = "510300") -> pd.DataFrame:
    """
    计算每只 ETF 相对基准的超额收益（60/120 日）。
    """
    if benchmark_code not in prices:
        print(f"[WARN] 基准 {benchmark_code} 不在数据中，跳过相对强度")
        return pd.DataFrame()

    bm = prices[benchmark_code]["close"]
    out = []
    for code, df in prices.items():
        c = df["close"]
        if len(c) < 120:
            continue

        rs_60 = (c.iloc[-1] / c.iloc[-61] - 1) - (bm.iloc[-1] / bm.iloc[-61] - 1) \
            if len(bm) > 60 else None
        rs_120 = (c.iloc[-1] / c.iloc[-121] - 1) - (bm.iloc[-1] / bm.iloc[-121] - 1) \
            if len(bm) > 120 else None

        out.append({
            "code": code,
            "rs_60": round(rs_60, 4) if rs_60 is not None else None,
            "rs_120": round(rs_120, 4) if rs_120 is not None else None,
        })

    df_out = pd.DataFrame(out)
    if not df_out.empty:
        df_out["rs_60_rank"] = df_out["rs_60"].rank(ascending=False, method="min")
        df_out["rs_120_rank"] = df_out["rs_120"].rank(ascending=False, method="min")
    return df_out


def technical_score(signals: dict) -> float:
    """
    把多维信号合成一个 0–10 的综合技术评分。
    简单线性加权,权重可调。
    """
    score = 5.0  # 中性起点

    # 趋势：多头 +2，空头 -2
    if signals.get("trend") == "bull":
        score += 2
    elif signals.get("trend") == "bear":
        score -= 2

    # 动量：60 日动量 > 5% 加分，< -5% 减分
    m60 = signals.get("momentum_3m")
    if m60 is not None:
        if m60 > 0.05:
            score += 1
        elif m60 < -0.05:
            score -= 1

    # 距 52 周高点：太远（< -20%）警示，太近（> -2%）也警示（追高）
    d_high = signals.get("dist_to_52w_high")
    if d_high is not None:
        if -0.10 < d_high < -0.02:  # 健康回调
            score += 0.5
        elif d_high > -0.02:  # 接近新高,追高风险
            score -= 0.5

    return round(max(0, min(10, score)), 1)


def compute_all(data_dir: str, benchmark_code: str = "510300") -> pd.DataFrame:
    """对所有 ETF 计算信号，输出汇总表"""
    prices = load_prices(data_dir)
    if not prices:
        raise ValueError("没有找到任何价格数据")

    rs_df = compute_relative_strength(prices, benchmark_code)

    rows = []
    for code, df in prices.items():
        close = df["close"]
        signals = {"code": code, "latest_date": df.index[-1].strftime("%Y-%m-%d")}
        signals.update(compute_trend(close))
        signals.update(compute_momentum(close))
        signals.update(compute_volatility(close))
        signals.update(compute_position(close))
        signals["score"] = technical_score(signals)

        # 加入相对强度
        rs_row = rs_df[rs_df["code"] == code]
        if not rs_row.empty:
            signals["rs_60"] = rs_row.iloc[0]["rs_60"]
            signals["rs_60_rank"] = int(rs_row.iloc[0]["rs_60_rank"])
            signals["rs_120"] = rs_row.iloc[0]["rs_120"]
            signals["rs_120_rank"] = int(rs_row.iloc[0]["rs_120_rank"])

        rows.append(signals)

    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description="ETF 信号计算")
    parser.add_argument("--data-dir", default="data/etf_prices/", help="价格数据目录")
    parser.add_argument("--output", default="data/signals.csv", help="信号输出路径")
    parser.add_argument("--benchmark", default="510300", help="相对强度基准 ETF")
    parser.add_argument("--code", help="只看单只 ETF")
    args = parser.parse_args()

    if args.code:
        prices = load_prices(args.data_dir, args.code)
        if args.code not in prices:
            print(f"未找到 {args.code} 的数据")
            return
        df = prices[args.code]
        signals = {"code": args.code}
        signals.update(compute_trend(df["close"]))
        signals.update(compute_momentum(df["close"]))
        signals.update(compute_volatility(df["close"]))
        signals.update(compute_position(df["close"]))
        signals["score"] = technical_score(signals)
        for k, v in signals.items():
            print(f"  {k:25s}: {v}")
    else:
        df = compute_all(args.data_dir, args.benchmark)
        df = df.sort_values("score", ascending=False)
        df.to_csv(args.output, index=False, encoding="utf-8-sig")
        print(f"信号汇总已存: {args.output}")
        print("\n技术评分 Top 10:")
        print(df[["code", "trend", "momentum_3m", "rs_60_rank", "vol_pct_1y", "score"]].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
