#!/usr/bin/env bash
# setup.sh - Sadie Personal Quant Fund 一键部署脚本
#
# 做的事:
# 1. 检查 Python 版本
# 2. 创建虚拟环境并装依赖
# 3. 把 skill 包复制到 ~/.claude/skills/quant-fund/
# 4. 把 scripts 软链接到 project/ 目录,保证一致
# 5. 拉取一次初始 ETF 数据
# 6. 设置 hooks 脚本可执行权限

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_SRC="$ROOT_DIR/skills/quant-fund"
SKILL_DEST="$HOME/.claude/skills/quant-fund"
PROJECT_DIR="$ROOT_DIR/project"
VENV_DIR="$ROOT_DIR/.venv"

echo "=========================================="
echo "  Sadie Personal Quant Fund Setup"
echo "=========================================="

# Step 1: Python check
echo ""
echo "[1/6] 检查 Python ..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 没找到 python3。请先安装 Python 3.10+"
    exit 1
fi
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "    ✓ Python $PY_VER"

# Step 2: virtualenv
echo ""
echo "[2/6] 创建虚拟环境 ..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo "    ✓ 已创建 $VENV_DIR"
else
    echo "    ✓ 已存在 $VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo ""
echo "[3/6] 安装依赖 ..."
pip install --upgrade pip --quiet
pip install -r "$ROOT_DIR/requirements.txt" --quiet
echo "    ✓ 依赖安装完成"

# Step 4: deploy skill to ~/.claude/skills/
echo ""
echo "[4/6] 部署 skill 包到 $SKILL_DEST ..."
mkdir -p "$HOME/.claude/skills"
if [ -L "$SKILL_DEST" ] || [ -d "$SKILL_DEST" ]; then
    echo "    ⚠️  $SKILL_DEST 已存在，备份为 ${SKILL_DEST}.bak.$(date +%Y%m%d-%H%M%S)"
    mv "$SKILL_DEST" "${SKILL_DEST}.bak.$(date +%Y%m%d-%H%M%S)"
fi
# 用软链接,这样改 skill 源文件会立即生效
ln -s "$SKILL_SRC" "$SKILL_DEST"
echo "    ✓ skill 已链接（修改源文件即时生效）"

# Step 5: link scripts into project/
echo ""
echo "[5/6] 链接脚本到 project/ ..."
mkdir -p "$PROJECT_DIR/scripts"
for f in "$SKILL_SRC/scripts/"*.py; do
    fname=$(basename "$f")
    target="$PROJECT_DIR/scripts/$fname"
    if [ ! -e "$target" ]; then
        ln -s "$f" "$target"
    fi
done
echo "    ✓ 脚本已链接"

# 复制 templates 和 data 初始模板（不链接,因为是要在 project 里独立编辑的）
mkdir -p "$PROJECT_DIR/data"
if [ ! -f "$PROJECT_DIR/data/etf_universe.csv" ]; then
    cp "$SKILL_SRC/data/etf_universe.csv" "$PROJECT_DIR/data/etf_universe.csv"
    echo "    ✓ 初始 ETF 池已复制"
fi
if [ ! -f "$PROJECT_DIR/data/positions.json" ]; then
    cp "$SKILL_SRC/data/positions.json" "$PROJECT_DIR/data/positions.json"
    echo "    ✓ 初始持仓 JSON 已复制（请编辑为你的实际持仓）"
fi

# Hook 脚本可执行
chmod +x "$PROJECT_DIR/.claude/hooks/"*.sh 2>/dev/null || true

# Step 6: initial data fetch (optional)
echo ""
echo "[6/6] 是否拉取初始 ETF 数据? (耗时约 2-3 分钟) [y/N]"
read -r REPLY
if [[ "$REPLY" =~ ^[Yy]$ ]]; then
    cd "$PROJECT_DIR"
    python scripts/fetch_etf_data.py --universe data/etf_universe.csv --output data/etf_prices/ --days 365 || {
        echo "    ⚠️  数据拉取失败，但不影响安装。可以稍后重试"
    }
    cd "$ROOT_DIR"
else
    echo "    跳过。需要时运行: cd project && python scripts/fetch_etf_data.py"
fi

echo ""
echo "=========================================="
echo "  ✓ 安装完成"
echo "=========================================="
echo ""
echo "下一步:"
echo "  1. 编辑 $PROJECT_DIR/data/positions.json 填入你的实际持仓"
echo "  2. cd $PROJECT_DIR"
echo "  3. source $VENV_DIR/bin/activate    （每次新开终端都要运行）"
echo "  4. claude                           （启动 Claude Code）"
echo ""
echo "试试这些命令:"
echo "  /morning-brief"
echo "  /signal-check 510300"
echo "  /rebalance-dry-run"
echo "  /monthly-review"
echo ""
