from __future__ import annotations

from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
REPORT_DIR = BASE_DIR / "reports" / "daily"


def generate_report(strategy_output: dict, risk_output: dict) -> str:
    today = datetime.now().strftime("%Y-%m-%d")

    latest_rows = strategy_output["latest_rows"]
    target_weights = strategy_output["target_weights"]

    lines = []
    lines.append(f"# 盘前简报 - {today}")
    lines.append("")
    lines.append("## 一、市场信号")
    for row in latest_rows:
        lines.append(
            f"- {row['symbol']}: score={row['score']}, trend_signal={row['trend_signal']}, "
            f"ret_20d={row['ret_20d']:.2%}, ret_60d={row['ret_60d']:.2%}, vol_20d={row['vol_20d']:.2%}"
        )

    lines.append("")
    lines.append("## 二、目标仓位")
    for symbol, weight in target_weights.items():
        lines.append(f"- {symbol}: {weight:.2%}")

    lines.append("")
    lines.append("## 三、风险状态")
    lines.append(f"- regime: {risk_output['regime']}")
    lines.append(f"- avg_vol: {risk_output['avg_vol']:.2%}")
    lines.append(f"- portfolio_drawdown: {risk_output['portfolio_drawdown']:.2%}")
    lines.append(f"- protection_mode: {risk_output['protection_mode']}")

    report = "\n".join(lines)
    return report


def save_report(report_text: str) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    path = REPORT_DIR / f"{today}.md"
    path.write_text(report_text, encoding="utf-8")
    return path
