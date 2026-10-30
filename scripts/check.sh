#!/usr/bin/env bash
# YangSpec 构建与静态检查。用法：
#   HUGO_BIN=/path/to/hugo scripts/check.sh
#   scripts/check.sh --full
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

HUGO_BIN="${HUGO_BIN:-hugo}"
if ! command -v "$HUGO_BIN" >/dev/null 2>&1; then
  echo "找不到 Hugo：$HUGO_BIN" >&2
  echo "安装 Hugo Extended 0.167.0，或设置 HUGO_BIN 指向该版本。" >&2
  exit 2
fi

log="$(mktemp)"
trap 'rm -f "$log"' EXIT

if ! "$HUGO_BIN" --environment production --cleanDestinationDir --printPathWarnings >"$log" 2>&1; then
  cat "$log"
  exit 1
fi
cat "$log"

if grep -q '^ERROR' "$log"; then
  echo "构建出现 ERROR" >&2
  exit 1
fi

# 只允许已登记的 PaperMod 弃用警告；新增警告视为回归。
unexpected="$(grep '^WARN' "$log" | grep -v 'LanguageCode' || true)"
if [ -n "$unexpected" ]; then
  echo "出现未登记的构建警告：" >&2
  printf '%s\n' "$unexpected" >&2
  exit 1
fi

if [ ! -f public/_headers ]; then
  echo "public/_headers 缺失：Cloudflare Pages 的安全头不会生效" >&2
  exit 1
fi

args=()
if [ "${1:-}" = "--full" ]; then
  args+=(--external)
elif [ -n "${1:-}" ]; then
  echo "未知参数：$1" >&2
  exit 2
fi

if [ ${#args[@]} -gt 0 ]; then
  python3 scripts/check.py public "${args[@]}"
else
  python3 scripts/check.py public
fi
