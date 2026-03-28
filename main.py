from __future__ import annotations

from agents.report_agent import generate_report, save_report
from agents.risk_agent import run_risk_check
from agents.strategy_agent import run_strategy


def main() -> None:
    strategy_output = run_strategy()
    risk_output = run_risk_check(strategy_output["latest_rows"])

    report_text = generate_report(strategy_output, risk_output)
    report_path = save_report(report_text)

    print("系统运行完成")
    print(report_text)
    print(f"\n报告已保存到: {report_path}")


if __name__ == "__main__":
    main()
