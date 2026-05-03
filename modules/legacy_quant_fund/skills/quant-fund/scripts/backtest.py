"""
backtest.py
===========
简易历史回测：给定一组权重和再平衡频率，在历史数据上跑表现。

用法:
    python backtest.py \
        --weights '{"510300":0.4,"511260":0.4,"518880":0.2}' \
        --prices data/etf_prices/ \
        --start 2020-01-01 \
        --end 2026-04-27 \
        --rebalance monthly \
        --output data/backtest_report.html
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def load_aligned_prices(prices_dir: str, codes: list, start: str, end: str) -> pd.DataFrame:
    """加载多只 ETF 价格，对齐为宽表"""
    out = {}
    for code in codes:
        f = Path(prices_dir) / f"{code}.parquet"
        if not f.exists():
            print(f"[WARN] {code} 文件不存在")
            continue
        df = pd.read_parquet(f)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").set_index("date")
        out[code] = df["close"]

    prices = pd.DataFrame(out)
    prices = prices.loc[start:end].dropna(how="all").ffill()
    return prices


def backtest_static_weights(prices: pd.DataFrame, weights: dict,
                             rebalance: str = "monthly",
                             initial: float = 200000,
                             cost_bps: float = 5) -> dict:
    """
    静态权重回测，定期再平衡。
    cost_bps：单边交易成本（5 bp = 0.05%）
    """
    common = [c for c in weights.keys() if c in prices.columns]
    w = pd.Series({c: weights[c] for c in common})
    w = w / w.sum()
    px = prices[common].dropna()

    if px.empty:
        return {"error": "无有效价格数据"}

    # 确定再平衡日期
    if rebalance == "daily":
        rebal_dates = px.index
    elif rebalance == "weekly":
        rebal_dates = px.resample("W-FRI").last().index
    elif rebalance == "monthly":
        rebal_dates = px.resample("ME").last().index
    elif rebalance == "quarterly":
        rebal_dates = px.resample("QE").last().index
    elif rebalance == "none":
        rebal_dates = pd.DatetimeIndex([px.index[0]])
    else:
        rebal_dates = px.resample("ME").last().index

    rebal_dates = [d for d in rebal_dates if d in px.index]

    # 初始建仓
    nav_history = []
    cash = initial
    holdings = {c: 0.0 for c in common}  # shares
    last_rebal_idx = 0

    for date in px.index:
        # 当前组合 NAV
        nav = cash + sum(holdings[c] * px.loc[date, c] for c in common)
        nav_history.append({"date": date, "nav": nav})

        # 是否再平衡日
        if date in rebal_dates:
            target_value = {c: nav * w[c] for c in common}
            cur_value = {c: holdings[c] * px.loc[date, c] for c in common}
            for c in common:
                diff_value = target_value[c] - cur_value[c]
                cost = abs(diff_value) * cost_bps / 10000
                cash -= cost
                # 调整股数
                holdings[c] = target_value[c] / px.loc[date, c]
                cur_value[c] = holdings[c] * px.loc[date, c]
            cash = nav - sum(cur_value.values())

    nav_df = pd.DataFrame(nav_history).set_index("date")
    nav_df["nav_norm"] = nav_df["nav"] / nav_df["nav"].iloc[0]
    nav_df["daily_ret"] = nav_df["nav"].pct_change().fillna(0)

    # 指标
    total_return = nav_df["nav"].iloc[-1] / nav_df["nav"].iloc[0] - 1
    n_years = len(nav_df) / 252
    cagr = (1 + total_return) ** (1 / n_years) - 1 if n_years > 0 else 0
    annual_vol = nav_df["daily_ret"].std() * np.sqrt(252)
    sharpe = cagr / annual_vol if annual_vol > 0 else 0

    cum = nav_df["nav"]
    rolling_max = cum.cummax()
    dd = (cum - rolling_max) / rolling_max
    mdd = dd.min()
    mdd_date = dd.idxmin()

    return {
        "weights": dict(w),
        "rebalance": rebalance,
        "start": str(nav_df.index[0].date()),
        "end": str(nav_df.index[-1].date()),
        "total_return": round(float(total_return), 4),
        "cagr": round(float(cagr), 4),
        "annual_vol": round(float(annual_vol), 4),
        "sharpe": round(float(sharpe), 2),
        "max_drawdown": round(float(mdd), 4),
        "max_drawdown_date": str(mdd_date.date()) if mdd_date else None,
        "final_nav": round(float(nav_df["nav"].iloc[-1]), 2),
        "nav_series": nav_df.reset_index().to_dict("records"),
    }


def render_html_report(result: dict, output_path: str, benchmark_result: dict = None):
    """生成单文件 HTML 报告（含图）"""
    nav_data = result["nav_series"]

    # 准备 plotly 数据
    chart_data = {
        "策略": {"x": [str(r["date"])[:10] for r in nav_data],
                 "y": [r["nav_norm"] for r in nav_data]},
    }
    if benchmark_result and "nav_series" in benchmark_result:
        bm_data = benchmark_result["nav_series"]
        chart_data["基准(60/40)"] = {
            "x": [str(r["date"])[:10] for r in bm_data],
            "y": [r["nav_norm"] for r in bm_data],
        }

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>回测报告 {result['start']} - {result['end']}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: -apple-system, "PingFang SC", sans-serif; max-width: 1100px;
                margin: 30px auto; padding: 20px; color: #222; }}
        h1 {{ border-bottom: 2px solid #2c3e50; padding-bottom: 10px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }}
        .metric {{ padding: 15px; background: #f8f9fa; border-left: 4px solid #2c3e50;
                   border-radius: 4px; }}
        .metric .label {{ font-size: 12px; color: #888; }}
        .metric .value {{ font-size: 22px; font-weight: bold; color: #2c3e50; }}
        .metric .value.neg {{ color: #c0392b; }}
        .metric .value.pos {{ color: #27ae60; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #2c3e50; color: white; }}
        #chart {{ width: 100%; height: 500px; }}
    </style>
</head>
<body>
    <h1>回测报告</h1>
    <p>区间：{result['start']} ~ {result['end']} | 再平衡：{result['rebalance']}</p>

    <div class="metrics">
        <div class="metric">
            <div class="label">总收益</div>
            <div class="value {'pos' if result['total_return']>0 else 'neg'}">{result['total_return']:.2%}</div>
        </div>
        <div class="metric">
            <div class="label">年化收益 (CAGR)</div>
            <div class="value {'pos' if result['cagr']>0 else 'neg'}">{result['cagr']:.2%}</div>
        </div>
        <div class="metric">
            <div class="label">年化波动率</div>
            <div class="value">{result['annual_vol']:.2%}</div>
        </div>
        <div class="metric">
            <div class="label">夏普比率</div>
            <div class="value">{result['sharpe']:.2f}</div>
        </div>
        <div class="metric">
            <div class="label">最大回撤</div>
            <div class="value neg">{result['max_drawdown']:.2%}</div>
        </div>
        <div class="metric">
            <div class="label">最大回撤日</div>
            <div class="value" style="font-size:14px;">{result['max_drawdown_date']}</div>
        </div>
        <div class="metric">
            <div class="label">期末净值</div>
            <div class="value">{result['final_nav']:,.0f}</div>
        </div>
        <div class="metric">
            <div class="label">Calmar</div>
            <div class="value">{result['cagr']/-result['max_drawdown']:.2f}</div>
        </div>
    </div>

    <h2>权重配置</h2>
    <table>
        <tr><th>ETF</th><th>权重</th></tr>
        {''.join(f'<tr><td>{c}</td><td>{w:.2%}</td></tr>' for c, w in result['weights'].items())}
    </table>

    <h2>净值曲线</h2>
    <div id="chart"></div>

    <script>
    var traces = [];
    {''.join(f'traces.push({{x: {json.dumps(d["x"])}, y: {json.dumps(d["y"])}, name: "{name}", mode: "lines"}});' for name, d in chart_data.items())}
    Plotly.newPlot('chart', traces, {{
        margin: {{l:50, r:30, t:30, b:50}},
        xaxis: {{title: '日期'}},
        yaxis: {{title: '净值（起始=1）'}},
        legend: {{x: 0.01, y: 0.99}},
    }});
    </script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    parser = argparse.ArgumentParser(description="组合回测")
    parser.add_argument("--weights", required=True, help='JSON 字符串,如 \'{"510300":0.6,"511260":0.4}\'')
    parser.add_argument("--prices", default="data/etf_prices/")
    parser.add_argument("--start", default="2020-01-01")
    parser.add_argument("--end", default="2026-04-27")
    parser.add_argument("--rebalance", default="monthly",
                        choices=["daily", "weekly", "monthly", "quarterly", "none"])
    parser.add_argument("--initial", type=float, default=200000)
    parser.add_argument("--cost-bps", type=float, default=5)
    parser.add_argument("--benchmark", default='{"510300":0.6,"511260":0.4}', help="基准权重")
    parser.add_argument("--output", default="data/backtest_report.html")
    args = parser.parse_args()

    weights = json.loads(args.weights)
    benchmark = json.loads(args.benchmark) if args.benchmark else None

    all_codes = list(set(list(weights.keys()) + (list(benchmark.keys()) if benchmark else [])))
    prices = load_aligned_prices(args.prices, all_codes, args.start, args.end)

    if prices.empty:
        print("无可用数据")
        return

    print(f"\n[策略回测]")
    result = backtest_static_weights(prices[[c for c in weights if c in prices.columns]],
                                      weights, args.rebalance, args.initial, args.cost_bps)
    print(f"  总收益: {result['total_return']:.2%}")
    print(f"  年化  : {result['cagr']:.2%}")
    print(f"  夏普  : {result['sharpe']:.2f}")
    print(f"  最大回撤: {result['max_drawdown']:.2%}")

    bm_result = None
    if benchmark:
        print(f"\n[基准回测]")
        bm_result = backtest_static_weights(prices[[c for c in benchmark if c in prices.columns]],
                                             benchmark, args.rebalance, args.initial, args.cost_bps)
        print(f"  总收益: {bm_result['total_return']:.2%}")
        print(f"  年化  : {bm_result['cagr']:.2%}")
        print(f"  夏普  : {bm_result['sharpe']:.2f}")

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    render_html_report(result, args.output, bm_result)
    print(f"\nHTML 报告: {args.output}")


if __name__ == "__main__":
    main()
