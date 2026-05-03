"""
portfolio_optimize.py
=====================
基于目标权重和约束，输出具体调仓方案。

支持三种优化方法:
1. 等权(equal)：在目标资产类内平均分配
2. 风险平价(risk_parity)：让每个仓位贡献相等的风险
3. 凯利缩水(kelly_fractional)：基于历史夏普做仓位（保守版）

用法:
    python portfolio_optimize.py \
        --target data/target_allocation.json \
        --positions data/positions.json \
        --prices data/etf_prices/ \
        --method risk_parity \
        --output data/proposed_trades.json
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def load_prices_returns(prices_dir: str, codes: list, lookback_days: int = 252) -> pd.DataFrame:
    """加载多只 ETF 的日收益率，对齐成宽表"""
    out = {}
    for code in codes:
        f = Path(prices_dir) / f"{code}.parquet"
        if not f.exists():
            print(f"[WARN] {code} 价格文件不存在，跳过")
            continue
        df = pd.read_parquet(f)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").set_index("date")
        out[code] = df["close"].pct_change()

    rets = pd.DataFrame(out).dropna(how="all").tail(lookback_days)
    return rets


def equal_weight(codes_per_category: dict) -> dict:
    """每类资产内等权"""
    weights = {}
    for category, info in codes_per_category.items():
        codes = info["codes"]
        target = info["target_weight"]
        if not codes:
            continue
        each = target / len(codes)
        for c in codes:
            weights[c] = each
    return weights


def risk_parity_weights(returns: pd.DataFrame, target_total: float = 1.0,
                        max_iter: int = 500, tol: float = 1e-7) -> dict:
    """
    风险平价：让每个标的对组合方差的边际贡献相等。
    使用 Spinu (2013) 的循环坐标下降法，保证权重非负。
    """
    if returns.empty or returns.shape[1] == 0:
        return {}

    cov = returns.cov().values * 252  # 年化协方差
    n = cov.shape[0]
    if n == 1:
        return {returns.columns[0]: target_total}

    # 用倒方差初始化（低风险资产权重大，符合直觉）
    diag = np.diag(cov)
    inv_vol = 1.0 / np.sqrt(np.maximum(diag, 1e-10))
    w = inv_vol / inv_vol.sum()

    # 循环坐标下降：每次只优化一个 w_i
    # 目标：让每个资产的 RC_i = sigma_p / n
    for _ in range(max_iter):
        w_old = w.copy()
        for i in range(n):
            # 固定其他权重，求解使 RC_i 等于平均的 w_i
            # RC_i = w_i * (Cov @ w)_i / sigma_p
            # target_rc = sigma_p / n
            # → w_i * (Cov @ w)_i = sigma_p^2 / n = (w' Cov w) / n
            # 这是关于 w_i 的二次方程，正根 = 解

            # 不含 w_i 的部分
            others = cov[i, :] @ w - cov[i, i] * w[i]
            # 当前组合方差（先固定其他 w_j）
            # 求解：a * w_i^2 + b * w_i + c = 0 形式
            # a = cov[i,i] * (1 - 1/n)
            # b = others * (1 - 2/n)
            # c = -(w_rest' Cov w_rest) / n

            mask = np.ones(n, dtype=bool)
            mask[i] = False
            w_rest = w.copy()
            w_rest[i] = 0
            var_rest = w_rest @ cov @ w_rest

            a = cov[i, i] - cov[i, i] / n
            b = others - 2 * others / n
            c = -var_rest / n

            disc = b * b - 4 * a * c
            if disc < 0 or a == 0:
                continue
            w_i_new = (-b + np.sqrt(disc)) / (2 * a)
            if w_i_new > 0:
                w[i] = w_i_new

        # 归一化到 1
        if w.sum() > 0:
            w = w / w.sum()

        # 收敛
        if np.max(np.abs(w - w_old)) < tol:
            break

    # 缩放到目标总权重
    w = w * target_total

    return {returns.columns[i]: round(float(w[i]), 4) for i in range(n)}


def kelly_fractional(returns: pd.DataFrame, target_total: float = 1.0,
                     fraction: float = 0.25) -> dict:
    """
    分数凯利：仓位 ∝ 历史夏普比率，但乘以一个保守系数（默认 1/4 凯利）。
    适合个人投资者（全凯利波动太大）。
    """
    if returns.empty:
        return {}

    annual_ret = returns.mean() * 252
    annual_vol = returns.std() * np.sqrt(252)
    sharpe = (annual_ret / annual_vol).fillna(0)

    # 只对正夏普赋权
    sharpe_pos = sharpe.clip(lower=0)
    if sharpe_pos.sum() == 0:
        # 退化为等权
        n = len(returns.columns)
        return {c: target_total / n for c in returns.columns}

    raw_weights = sharpe_pos * fraction
    # 归一
    w = raw_weights / raw_weights.sum() * target_total
    return {c: round(float(w[c]), 4) for c in w.index}


def apply_constraints(weights: dict, constraints: dict, total_capital: float) -> dict:
    """
    应用硬约束：
    - 单一 ETF 上限
    - 最小现金
    - 持仓数限制
    """
    weights = {k: v for k, v in weights.items() if v > 0.001}  # 去除极小仓位
    max_single = constraints.get("single_etf_max_weight", 0.30)

    # Cap 单一上限
    capped = {}
    excess = 0
    for code, w in weights.items():
        if w > max_single:
            excess += w - max_single
            capped[code] = max_single
        else:
            capped[code] = w

    # 把 excess 等比例分给未达上限的
    if excess > 0:
        room = {c: max_single - w for c, w in capped.items() if w < max_single}
        total_room = sum(room.values())
        if total_room > 0:
            for c, r in room.items():
                add = excess * r / total_room
                capped[c] = min(capped[c] + add, max_single)

    # 持仓数检查
    max_holdings = constraints.get("max_holdings", 8)
    if len(capped) > max_holdings:
        # 保留权重最高的
        sorted_holdings = sorted(capped.items(), key=lambda x: x[1], reverse=True)
        capped = dict(sorted_holdings[:max_holdings])
        # 重新归一
        s = sum(capped.values())
        capped = {k: v / s * (1 - constraints.get("min_cash_ratio", 0.05)) for k, v in capped.items()}

    return capped


def generate_trades(current_positions: list, target_weights: dict,
                    total_capital: float, latest_prices: dict) -> list:
    """
    把"目标权重"和"当前持仓"做差，生成具体买卖单。
    """
    trades = []

    # 当前持仓 dict {code: shares}
    cur_shares = {p["code"]: p.get("shares", 0) for p in current_positions if p.get("code")}

    # 计算目标股数
    target_shares = {}
    for code, weight in target_weights.items():
        price = latest_prices.get(code, 0)
        if price <= 0:
            print(f"[WARN] {code} 无价格,跳过")
            continue
        target_value = total_capital * weight
        # ETF 一手 = 100 股
        target_shares[code] = int(target_value / price / 100) * 100

    # 涉及到的所有标的
    all_codes = set(cur_shares.keys()) | set(target_shares.keys())

    for code in all_codes:
        cur = cur_shares.get(code, 0)
        tgt = target_shares.get(code, 0)
        diff = tgt - cur
        if diff == 0:
            continue
        price = latest_prices.get(code, 0)
        trades.append({
            "code": code,
            "action": "BUY" if diff > 0 else "SELL",
            "current_shares": cur,
            "target_shares": tgt,
            "diff_shares": diff,
            "estimated_price": price,
            "estimated_amount": abs(diff) * price,
        })

    return trades


def main():
    parser = argparse.ArgumentParser(description="组合优化与调仓单生成")
    parser.add_argument("--target", required=True, help="目标分类权重 JSON")
    parser.add_argument("--positions", required=True, help="当前持仓 JSON")
    parser.add_argument("--prices", default="data/etf_prices/", help="价格数据目录")
    parser.add_argument("--method", default="risk_parity",
                        choices=["equal", "risk_parity", "kelly_fractional"])
    parser.add_argument("--output", default="data/proposed_trades.json")
    args = parser.parse_args()

    with open(args.target, "r", encoding="utf-8") as f:
        target = json.load(f)
    with open(args.positions, "r", encoding="utf-8") as f:
        pos_data = json.load(f)

    total_capital = pos_data.get("total_capital", 200000)
    constraints = pos_data.get("constraints", {})

    # 收集所有候选 codes
    all_codes = []
    for cat_info in target.get("categories", {}).values():
        all_codes.extend(cat_info.get("codes", []))

    # 加载收益率
    returns = load_prices_returns(args.prices, all_codes)

    # 优化
    if args.method == "equal":
        weights = equal_weight(target["categories"])
    elif args.method == "risk_parity":
        # 对每个 category 内做风险平价，然后乘以 category 目标权重
        weights = {}
        for cat_name, info in target["categories"].items():
            codes = [c for c in info.get("codes", []) if c in returns.columns]
            if not codes:
                continue
            cat_returns = returns[codes].dropna()
            cat_w = risk_parity_weights(cat_returns, target_total=info["target_weight"])
            weights.update(cat_w)
    elif args.method == "kelly_fractional":
        # 同上
        weights = {}
        for cat_name, info in target["categories"].items():
            codes = [c for c in info.get("codes", []) if c in returns.columns]
            if not codes:
                continue
            cat_returns = returns[codes].dropna()
            cat_w = kelly_fractional(cat_returns, target_total=info["target_weight"])
            weights.update(cat_w)

    # 应用约束
    weights = apply_constraints(weights, constraints, total_capital)

    # 拉取最新价格
    latest_prices = {}
    for code in weights.keys():
        f = Path(args.prices) / f"{code}.parquet"
        if f.exists():
            df = pd.read_parquet(f)
            latest_prices[code] = float(df["close"].iloc[-1])

    # 生成交易单
    trades = generate_trades(
        pos_data.get("current_positions", []),
        weights,
        total_capital,
        latest_prices,
    )

    output = {
        "method": args.method,
        "target_weights": weights,
        "trades": trades,
        "total_capital": total_capital,
        "estimated_total_turnover": sum(t["estimated_amount"] for t in trades) / total_capital,
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n优化方法: {args.method}")
    print("目标权重:")
    for code, w in sorted(weights.items(), key=lambda x: -x[1]):
        print(f"  {code}: {w:.2%}")
    print(f"\n建议交易 {len(trades)} 笔，总换手率 {output['estimated_total_turnover']:.1%}")
    print(f"调仓单已存: {args.output}")


if __name__ == "__main__":
    main()
