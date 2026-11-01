#!/usr/bin/env bash
# 运行 scripts/check.sh，并把完整输出、提交号与退出码留存到 gitignored 的 reports/。
# 用法：
#   HUGO_BIN=/path/to/hugo scripts/check-record.sh
#   HUGO_BIN=/path/to/hugo scripts/check-record.sh --full
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$ROOT/reports"

stamp="$(date +%Y%m%dT%H%M%S)"
report="$ROOT/reports/check-${stamp}.txt"
commit="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"

set +e
"$ROOT/scripts/check.sh" "$@" 2>&1 | tee "$report"
status=${PIPESTATUS[0]}
set -e

{
  echo
  echo "---"
  echo "时间：$(date '+%Y-%m-%dT%H:%M:%S%z')"
  echo "提交：${commit}"
  echo "退出码：${status}"
} | tee -a "$report"

echo "报告：reports/$(basename "$report")"
exit "$status"
