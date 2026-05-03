#!/usr/bin/env bash
# .claude/hooks/stop-reminder.sh
#
# 在 Claude 完成一次响应后触发。
# 检查：
# 1. 当前是否月末最后 5 个交易日 → 提醒该做月度调仓
# 2. 当前是否月初第一个交易日 → 提醒该做月度复盘
# 3. logs/decisions/ 中是否有"30 天后复盘"任务到期

set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
TODAY=$(date +%Y-%m-%d)
DAY_OF_MONTH=$(date +%d)
LAST_DAY_OF_MONTH=$(date -d "$(date +%Y-%m-01) +1 month -1 day" +%d 2>/dev/null || date -v1d -v+1m -v-1d +%d 2>/dev/null || echo "31")

# 月末最后 5 天
DAYS_TO_END=$((10#$LAST_DAY_OF_MONTH - 10#$DAY_OF_MONTH))
if [ "$DAYS_TO_END" -le 5 ] && [ "$DAYS_TO_END" -ge 0 ]; then
    # 检查本月是否已做过月度调仓
    if ! ls "$PROJECT_DIR/logs/decisions/$(date +%Y-%m)-*-monthly-rebalance.md" 2>/dev/null | head -1 > /dev/null; then
        echo ""
        echo "🗓️  距月末 $DAYS_TO_END 天，建议运行 /rebalance-dry-run 做月度调仓演练"
    fi
fi

# 月初第一个交易日
if [ "$DAY_OF_MONTH" = "01" ] || [ "$DAY_OF_MONTH" = "02" ] || [ "$DAY_OF_MONTH" = "03" ]; then
    LAST_MONTH=$(date -d "1 month ago" +%Y-%m 2>/dev/null || date -v-1m +%Y-%m 2>/dev/null)
    if [ -n "$LAST_MONTH" ] && ! [ -f "$PROJECT_DIR/logs/reports/${LAST_MONTH}-monthly-review.md" ]; then
        echo ""
        echo "📊 月初到，建议运行 /monthly-review 复盘上月（${LAST_MONTH}）"
    fi
fi

# 检查决策日志中"30 天复盘"到期
if [ -d "$PROJECT_DIR/logs/decisions" ]; then
    THIRTY_DAYS_AGO=$(date -d "30 days ago" +%Y-%m-%d 2>/dev/null || date -v-30d +%Y-%m-%d 2>/dev/null)
    if [ -n "$THIRTY_DAYS_AGO" ]; then
        # 找出 30 天前的决策日志
        OLD_DECISIONS=$(ls "$PROJECT_DIR/logs/decisions/${THIRTY_DAYS_AGO}"*.md 2>/dev/null | head -3)
        if [ -n "$OLD_DECISIONS" ]; then
            echo ""
            echo "⏰ 以下决策已满 30 天，请检查复盘节点:"
            echo "$OLD_DECISIONS" | while read f; do
                echo "   - $(basename "$f")"
            done
        fi
    fi
fi

exit 0
