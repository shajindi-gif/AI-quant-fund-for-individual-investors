#!/usr/bin/env bash
# .claude/hooks/post-tool-use.sh
#
# 在 Claude 调用某些关键脚本后，自动追加一行到 logs/decisions/_audit.log
# 这是一个轻量级审计层，不替代正式决策日志，但能保证"任何脚本调用都有痕迹"。

set -euo pipefail

LOG_DIR="${CLAUDE_PROJECT_DIR:-.}/logs/decisions"
mkdir -p "$LOG_DIR"
AUDIT_LOG="$LOG_DIR/_audit.log"

TOOL_NAME="${CLAUDE_TOOL_NAME:-unknown}"
TOOL_INPUT="${CLAUDE_TOOL_INPUT:-}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# 只对关键脚本记录
if echo "$TOOL_INPUT" | grep -qE "(portfolio_optimize|risk_metrics|fetch_etf_data|backtest)"; then
    echo "[$TIMESTAMP] tool=$TOOL_NAME input=$(echo "$TOOL_INPUT" | head -c 200)" >> "$AUDIT_LOG"
fi

# 调仓单/决策日志生成时，提示用户检查
if echo "$TOOL_INPUT" | grep -qE "logs/decisions/.*\.md$"; then
    echo "📝 决策日志已写入。请确认 30/60/90 天复盘锚点已设置。"
fi

exit 0
