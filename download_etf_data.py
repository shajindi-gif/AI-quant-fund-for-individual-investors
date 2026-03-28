"""
从 AkShare 拉取 symbols.yaml 中配置的 ETF 日线，写入 data/raw/{code}.csv。

扩展标的：编辑 config/symbols.yaml 后重新运行本脚本即可。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import akshare as ak

# 从项目根目录运行时保证能 import strategy
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from strategy.data_loader import DATA_DIR, etf_codes, load_symbols

AK_RENAME = {
    "日期": "date",
    "开盘": "open",
    "收盘": "close",
    "最高": "high",
    "最低": "low",
    "成交量": "volume",
}
KEEP_COLS = ["date", "open", "high", "low", "close", "volume"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="下载 ETF 日线 CSV（与 symbols.yaml 对齐）")
    p.add_argument(
        "--symbols",
        nargs="*",
        metavar="CODE",
        help="只下载指定代码（默认：symbols.yaml 中全部）",
    )
    p.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="不打印每只 ETF 的列名（AkShare 版本排查时可去掉 -q）",
    )
    return p.parse_args()


def resolve_codes(cli_symbols: list[str] | None) -> list[str]:
    if not cli_symbols:
        return etf_codes()
    configured = {r["symbol"] for r in load_symbols()}
    out: list[str] = []
    for raw in cli_symbols:
        code = str(raw).strip()
        if code not in configured:
            raise SystemExit(
                f"错误: {code!r} 未在 config/symbols.yaml 中配置，请先添加该标的。"
            )
        out.append(code)
    return out


def download_one(symbol: str, *, quiet: bool) -> bool:
    df = ak.fund_etf_hist_em(symbol=symbol, period="daily", adjust="qfq")
    if not quiet:
        print(symbol, df.columns.tolist())

    df = df.rename(columns=AK_RENAME)
    missing = set(KEEP_COLS) - set(df.columns)
    if missing:
        print(f"[跳过] {symbol}: 缺少列 {missing}，请检查 AkShare 返回字段")
        return False

    df = df[KEEP_COLS].copy()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA_DIR / f"{symbol}.csv", index=False, encoding="utf-8-sig")
    return True


def main() -> None:
    args = parse_args()
    codes = resolve_codes(args.symbols)
    ok, fail = 0, 0
    for symbol in codes:
        try:
            if download_one(symbol, quiet=args.quiet):
                ok += 1
            else:
                fail += 1
        except Exception as e:  # noqa: BLE001 — 单只失败不中断整批
            print(f"[失败] {symbol}: {e}")
            fail += 1
    print(f"完成: 成功 {ok}，失败 {fail}，输出目录 {DATA_DIR.resolve()}")


if __name__ == "__main__":
    main()
