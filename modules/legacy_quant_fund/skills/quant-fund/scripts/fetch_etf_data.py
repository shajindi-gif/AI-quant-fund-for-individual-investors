"""
fetch_etf_data.py
=================
从 akshare 拉取 ETF 历史行情、规模、跟踪误差等数据。

用法:
    python fetch_etf_data.py --universe data/etf_universe.csv --output data/etf_prices/
    python fetch_etf_data.py --code 510300 --days 365

依赖:
    pip install akshare pandas

注意:
    - akshare 是免费数据源,但稳定性不如付费
    - 高频调用可能被限流,脚本内置 0.3s 延迟
    - 跨境 ETF 部分字段可能缺失
"""
import argparse
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


def fetch_etf_history(code: str, days: int = 365) -> pd.DataFrame:
    """
    拉取单只 ETF 的历史行情(新浪财经源)。
    返回 DataFrame columns: date, open, close, high, low, volume, amount
    """
    try:
        import akshare as ak
    except ImportError:
        raise ImportError("请先安装 akshare: pip install akshare")

    # 新浪源代码格式: sh510300 / sz159915
    if code.startswith(("5", "6", "11", "15")):
        sina_code = "sh" + code if code.startswith(("5", "6")) else "sz" + code
    elif code.startswith(("0", "1", "3")):
        sina_code = "sz" + code
    else:
        sina_code = "sh" + code

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    try:
        # akshare 的新浪 ETF 行情接口
        df = ak.fund_etf_hist_sina(symbol=sina_code)
        if df is None or df.empty:
            print(f"[WARN] {code} 无数据返回")
            return pd.DataFrame()

        # 标准化列名(新浪源列名是英文)
        col_map = {
            "date": "date", "open": "open", "high": "high",
            "low": "low", "close": "close", "volume": "volume",
        }
        df = df.rename(columns=col_map)
        df["date"] = pd.to_datetime(df["date"])
        # 时间筛选
        df = df[df["date"] >= pd.to_datetime(start_date)]
        df["code"] = code
        # 补 amount 列(新浪源没提供成交额,用 close*volume 估算)
        if "amount" not in df.columns:
            df["amount"] = df["close"] * df["volume"]
        df = df.sort_values("date").reset_index(drop=True)
        return df

    except Exception as e:
        print(f"[ERROR] 拉取 {code} 失败: {e}")
        return pd.DataFrame()



def fetch_etf_realtime(code: str) -> dict:
    """
    拉取单只 ETF 实时行情（含规模、折溢价等）。
    """
    try:
        import akshare as ak
    except ImportError:
        return {}

    try:
        df = ak.fund_etf_spot_em()
        row = df[df["代码"] == code]
        if row.empty:
            return {}
        row = row.iloc[0]
        return {
            "code": code,
            "name": row.get("名称", ""),
            "price": float(row.get("最新价", 0)),
            "change_pct": float(row.get("涨跌幅", 0)),
            "amount": float(row.get("成交额", 0)),
            "volume": float(row.get("成交量", 0)),
            "turnover_rate": float(row.get("换手率", 0)) if row.get("换手率") else 0,
            "scale_billion": float(row.get("规模", 0)) if "规模" in row else None,
            "premium_rate": float(row.get("折价率", 0)) if "折价率" in row else None,
        }
    except Exception as e:
        print(f"[WARN] 实时数据 {code} 失败: {e}")
        return {}


def fetch_universe(universe_path: str, output_dir: str, days: int = 365):
    """批量拉取 ETF 池所有标的"""
    df_uni = pd.read_csv(universe_path, dtype={"code": str})
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    success, fail = 0, 0
    snapshot = []

    for _, row in df_uni.iterrows():
        code = row["code"]
        print(f"  → {code} {row['name']} ...", end=" ")
        df = fetch_etf_history(code, days=days)
        if not df.empty:
            df.to_parquet(output_path / f"{code}.parquet", index=False)
            print(f"OK ({len(df)} 行)")
            success += 1
        else:
            print("FAIL")
            fail += 1

        # 实时快照
        rt = fetch_etf_realtime(code)
        if rt:
            rt["category"] = row.get("category", "")
            snapshot.append(rt)

        time.sleep(0.3)  # 防限流

    # 保存实时快照
    if snapshot:
        snap_df = pd.DataFrame(snapshot)
        snap_df.to_csv(output_path / "_snapshot.csv", index=False, encoding="utf-8-sig")
        print(f"\n实时快照已存: {output_path}/_snapshot.csv")

    print(f"\n完成: 成功 {success}, 失败 {fail}")


def fetch_macro_indicators() -> dict:
    """
    拉取关键宏观指标（CPI/PPI/PMI/M2/社融）。
    返回最近 12 期数据。
    """
    try:
        import akshare as ak
    except ImportError:
        return {}

    out = {}
    try:
        # CPI
        cpi = ak.macro_china_cpi_monthly()
        out["cpi"] = cpi.tail(12).to_dict("records")
    except Exception as e:
        print(f"[WARN] CPI 拉取失败: {e}")

    try:
        # PPI
        ppi = ak.macro_china_ppi_yearly()
        out["ppi"] = ppi.tail(12).to_dict("records")
    except Exception as e:
        print(f"[WARN] PPI 拉取失败: {e}")

    try:
        # 制造业 PMI
        pmi = ak.macro_china_pmi_yearly()
        out["pmi"] = pmi.tail(12).to_dict("records")
    except Exception as e:
        print(f"[WARN] PMI 拉取失败: {e}")

    try:
        # M2
        m2 = ak.macro_china_money_supply()
        out["m2"] = m2.tail(12).to_dict("records")
    except Exception as e:
        print(f"[WARN] M2 拉取失败: {e}")

    return out


def fetch_index_valuation(index_code: str) -> dict:
    """
    拉取指数估值分位（PE/PB）。
    用 akshare 的中证指数估值接口。
    """
    try:
        import akshare as ak
    except ImportError:
        return {}

    try:
        # 中证指数估值
        df = ak.stock_zh_index_value_csindex(symbol=index_code)
        if df is None or df.empty:
            return {}
        latest = df.iloc[-1]
        return {
            "index_code": index_code,
            "date": str(latest.get("日期", "")),
            "pe_ttm": float(latest.get("市盈率1", 0)),
            "pb": float(latest.get("市净率1", 0)),
            "dividend_yield": float(latest.get("股息率1", 0)),
        }
    except Exception as e:
        print(f"[WARN] 指数估值 {index_code} 失败: {e}")
        return {}


def main():
    parser = argparse.ArgumentParser(description="ETF 数据拉取工具")
    parser.add_argument("--universe", default="data/etf_universe.csv", help="ETF 池 CSV 路径")
    parser.add_argument("--output", default="data/etf_prices/", help="输出目录")
    parser.add_argument("--days", type=int, default=365, help="拉取天数")
    parser.add_argument("--code", help="只拉单只 ETF（调试用）")
    parser.add_argument("--macro", action="store_true", help="同时拉取宏观数据")
    args = parser.parse_args()

    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始拉取数据 ...")

    if args.code:
        df = fetch_etf_history(args.code, days=args.days)
        rt = fetch_etf_realtime(args.code)
        print(df.tail(10))
        print("实时:", rt)
    else:
        fetch_universe(args.universe, args.output, days=args.days)

    if args.macro:
        print("\n拉取宏观数据 ...")
        macro = fetch_macro_indicators()
        macro_path = Path(args.output) / "_macro.json"
        macro_path.parent.mkdir(parents=True, exist_ok=True)
        with open(macro_path, "w", encoding="utf-8") as f:
            json.dump(macro, f, ensure_ascii=False, indent=2, default=str)
        print(f"宏观数据已存: {macro_path}")

    print(f"[{datetime.now().strftime('%H:%M:%S')}] 完成")


if __name__ == "__main__":
    main()
