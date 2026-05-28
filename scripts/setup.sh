#!/usr/bin/env bash
# 创建项目虚拟环境并安装依赖（含 akshare）。macOS Homebrew Python 需用 venv，勿全局 pip install。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  echo "Created .venv"
fi

.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt

.venv/bin/python -c "import akshare as ak; print('ok: akshare', ak.__version__)"

echo ""
echo "Done. Activate with:"
echo "  source .venv/bin/activate"
echo ""
echo "Then download ETF data:"
echo "  python download_etf_data.py"
