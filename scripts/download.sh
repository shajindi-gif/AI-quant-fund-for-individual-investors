#!/usr/bin/env bash
# 在已激活的 venv 或项目 .venv 下拉取 ETF 日线；自动去掉常见代理变量，避免 AkShare 连东方财富失败。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PY="${ROOT}/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "Run scripts/setup.sh first." >&2
  exit 1
fi

export NO_PROXY='*'
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy

exec "$PY" download_etf_data.py "$@"
