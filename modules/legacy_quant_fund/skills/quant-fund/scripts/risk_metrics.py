"""
risk_metrics.py
===============
计算组合风险指标：VaR、回撤、相关性、压力测试。

用法:
    python risk_metrics.py \
        --positions data/positions.json \
        --prices data/etf_prices/ \
        --output data/risk_report.json
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def load_returns(prices_dir: str, codes: list, days: int = 252) -> pd.DataFrame:
    out = {}
    for code in codes:
        f = Path(prices_dir) / f"{code}.parquet"
        if not f.exists():
            continue
        df = pd.read_parquet(f)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").set_index("date")
        out[code] = df["close"].pct_change()
    return pd.DataFrame(out).dropna(how="all").tail(days)


def portfolio_returns(returns: pd.DataFrame, weights: dict) -> pd.Series:
    """根据权重合成组合日收益序列"""
    common = [c for c in weights.keys() if c in returns.columns]
    if not common:
        return pd.Series(dtype=float)
    w = pd.Series({c: weights[c] for c in common})
    w = w / w.sum() if w.sum() > 0 else w
    return (returns[common] * w).sum(axis=1)


def historical_var(port_ret: pd.Series, confidence: float = 0.95, horizon: int = 1) -> float:
    """历史模拟法 VaR"""
    if len(port_ret) < 30:
        return None
    quantile = port_ret.quantile(1 - confidence)
    return float(quantile * np.sqrt(horizon))


def parametric_var(port_ret: pd.Series, confidence: float = 0.95, horizon: int = 1) -> float:
    """参数法 VaR (假设正态分布,实际偏保守因为低估尾部)"""
    if len(port_ret) < 30:
        return None
    from scipy.stats import norm
    mean = port_ret.mean()
    std = port_ret.std()
    z = norm.ppf(1 - confidence)
    return float((mean + z * std) * np.sqrt(horizon))


def max_drawdown(port_ret: pd.Series) -> dict:
    """最大回撤"""
    if len(port_ret) < 30:
        return {"max_drawdown": None}
    cum = (1 + port_ret).cumprod()
    rolling_max = cum.cummax()
    dd = (cum - rolling_max) / rolling_max
    mdd = dd.min()
    mdd_date = dd.idxmin()
    peak_date = cum.loc[:mdd_date].idxmax()
    return {
        "max_drawdown": float(mdd),
        "max_drawdown_date": str(mdd_date.date()) if mdd_date else None,
        "peak_date": str(peak_date.date()) if peak_date else None,
        "current_drawdown": float(dd.iloc[-1]),
    }


def correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    """相关性矩阵"""
    return returns.corr()


def stress_test(returns: pd.DataFrame, weights: dict) -> dict:
    """
    历史极端日的组合表现回放。
    """
    common = [c for c in weights.keys() if c in returns.columns]
    if not common:
        return {}
    w = pd.Series({c: weights[c] for c in common})
    w = w / w.sum() if w.sum() > 0 else w

    port_ret = (returns[common] * w).sum(axis=1)

    # 找历史最差 5 天
    worst_days = port_ret.nsmallest(5)
    out = {
        "worst_5_days": [
            {"date": str(d.date()), "return": round(float(r), 4)}
            for d, r in worst_days.items()
        ],
        "best_5_days": [
            {"date": str(d.date()), "return": round(float(r), 4)}
            for d, r in port_ret.nlargest(5).items()
        ],
    }

    # 模拟场景：所有持仓股 -7%
    stock_codes = [c for c in common if not c.startswith("511") and not c.startswith("518")]
    bond_codes = [c for c in common if c.startswith("511")]
    stock_w = sum(w.get(c, 0) for c in stock_codes)
    bond_w = sum(w.get(c, 0) for c in bond_codes)

    out["scenarios"] = {
        "stock_crash_7pct": round(-0.07 * stock_w, 4),
        "bond_yield_up_30bp": round(-0.025 * bond_w, 4),  # 假设 10Y 国开久期 7,30bp 对应 -2.1%
        "fx_shock_2pct": "约影响跨境 ETF 仓位",
    }

    return out


def compute_full_risk_report(positions_path: str, prices_dir: str) -> dict:
    """生成完整风险报告"""
    with open(positions_path, "r", encoding="utf-8") as f:
        pos_data = json.load(f)

    total_capital = pos_data.get("total_capital", 200000)
    positions = pos_data.get("current_positions", [])
    constraints = pos_data.get("constraints", {})

    # 计算当前权重
    cur_value = {}
    for p in positions:
        code = p.get("code")
        if not code:
            continue
        f = Path(prices_dir) / f"{code}.parquet"
        if f.exists():
            df = pd.read_parquet(f)
            price = float(df["close"].iloc[-1])
        else:
            price = p.get("avg_cost", 0)
        cur_value[code] = p.get("shares", 0) * price

    cash = pos_data.get("cash", 0)
    total_value = sum(cur_value.values()) + cash
    weights = {c: v / total_value for c, v in cur_value.items() if v > 0}

    if not weights:
        return {"error": "无有效持仓"}

    returns = load_returns(prices_dir, list(weights.keys()))
    port_ret = portfolio_returns(returns, weights)

    # 风险指标
    var_95 = historical_var(port_ret, 0.95, 1)
    var_99 = historical_var(port_ret, 0.99, 1)
    var_30d = historical_var(port_ret, 0.95, 30)

    mdd = max_drawdown(port_ret)
    corr = correlation_matrix(returns)
    stress = stress_test(returns, weights)

    # 硬约束检查
    violations = []
    max_w = constraints.get("single_etf_max_weight", 0.30)
    for code, w in weights.items():
        if w > max_w:
            violations.append(f"{code} 权重 {w:.1%} > 上限 {max_w:.1%}")
    cash_ratio = cash / total_value
    min_cash = constraints.get("min_cash_ratio", 0.05)
    if cash_ratio < min_cash:
        violations.append(f"现金比例 {cash_ratio:.1%} < 下限 {min_cash:.1%}")

    # 风控线状态
    cur_dd = mdd.get("current_drawdown", 0)
    if cur_dd is None:
        light = "🟢"
    elif cur_dd > -0.08:
        light = "🟢"
    elif cur_dd > -0.12:
        light = "🟡"
    elif cur_dd > -0.15:
        light = "🟠"
    elif cur_dd > -0.20:
        light = "🔴"
    else:
        light = "⚫"

    # 最高相关性
    if not corr.empty and corr.shape[0] > 1:
        upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
        max_corr_value = upper.max().max()
        idx = upper.stack().idxmax() if not upper.stack().empty else None
        max_corr = {
            "value": round(float(max_corr_value), 3),
            "pair": list(idx) if idx else None,
        }
    else:
        max_corr = None

    return {
        "as_of_date": str(returns.index[-1].date()) if len(returns) > 0 else None,
        "total_value": round(total_value, 2),
        "cash": round(cash, 2),
        "cash_ratio": round(cash_ratio, 4),
        "weights": {c: round(w, 4) for c, w in weights.items()},
        "metrics": {
            "var_1d_95": round(var_95, 4) if var_95 else None,
            "var_1d_99": round(var_99, 4) if var_99 else None,
            "var_30d_95": round(var_30d, 4) if var_30d else None,
            "annual_vol": round(float(port_ret.std() * np.sqrt(252)), 4) if len(port_ret) > 0 else None,
            "annual_return": round(float(port_ret.mean() * 252), 4) if len(port_ret) > 0 else None,
            "sharpe": round(float(port_ret.mean() / port_ret.std() * np.sqrt(252)), 2)
                if len(port_ret) > 0 and port_ret.std() > 0 else None,
        },
        "drawdown": mdd,
        "max_correlation": max_corr,
        "stress_test": stress,
        "constraint_violations": violations,
        "risk_light": light,
    }


def main():
    parser = argparse.ArgumentParser(description="组合风险指标计算")
    parser.add_argument("--positions", required=True)
    parser.add_argument("--prices", default="data/etf_prices/")
    parser.add_argument("--output", default="data/risk_report.json")
    args = parser.parse_args()

    report = compute_full_risk_report(args.positions, args.prices)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n=== 风险报告 ({report.get('as_of_date')}) ===")
    print(f"组合总值: {report.get('total_value'):,.0f}")
    print(f"现金比例: {report.get('cash_ratio'):.1%}")
    print(f"风控灯  : {report.get('risk_light')}")
    print(f"\n关键指标:")
    m = report.get("metrics", {})
    print(f"  日 VaR(95%): {m.get('var_1d_95', 'N/A')}")
    print(f"  30日 VaR(95%): {m.get('var_30d_95', 'N/A')}")
    print(f"  年化波动率 : {m.get('annual_vol', 'N/A')}")
    print(f"  夏普比率   : {m.get('sharpe', 'N/A')}")
    dd = report.get("drawdown", {})
    print(f"  历史最大回撤: {dd.get('max_drawdown')} (于 {dd.get('max_drawdown_date')})")
    print(f"  当前回撤   : {dd.get('current_drawdown')}")

    if report.get("constraint_violations"):
        print(f"\n⚠️  约束违反 {len(report['constraint_violations'])} 项:")
        for v in report["constraint_violations"]:
            print(f"   - {v}")
    else:
        print(f"\n✓ 所有硬约束通过")

    print(f"\n完整报告: {args.output}")


if __name__ == "__main__":
    main()
