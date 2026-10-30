#!/usr/bin/env bash
# 预览/线上运行时检查：Lighthouse、Cookie、安全头、第三方请求。
# 用法：scripts/preview-check.sh https://branch.pages.dev
set -euo pipefail

URL="${1:-}"
if [ -z "$URL" ]; then
  echo "用法：scripts/preview-check.sh <preview-url>" >&2
  exit 2
fi
URL="${URL%/}"

export npm_config_cache="${npm_config_cache:-/tmp/yangspec-npm}"
mkdir -p "$npm_config_cache"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

routes=(home:/ posts:/posts/ post:/posts/hello/ about:/about/ contact:/contact/ privacy:/privacy/)
for item in "${routes[@]}"; do
  name="${item%%:*}"
  path="${item#*:}"
  npx -y lighthouse "$URL$path" \
    --output=json --output-path="$tmp/$name.json" --quiet \
    --chrome-flags="--headless=new --no-sandbox" \
    --only-categories=performance,accessibility,best-practices,seo >/dev/null
done

python3 - "$tmp" "$URL" <<'PY'
import json
import sys
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urlsplit

tmp, base = sys.argv[1], sys.argv[2]
fails = []
passes = []

for name in ("home", "posts", "post", "about", "contact", "privacy"):
    with open(f"{tmp}/{name}.json", encoding="utf-8") as handle:
        data = json.load(handle)
    audits = data["audits"]
    scores = {key: round((value.get("score") or 0) * 100) for key, value in data["categories"].items()}
    lcp = audits.get("largest-contentful-paint", {}).get("numericValue")
    cls = audits.get("cumulative-layout-shift", {}).get("numericValue")
    tbt = audits.get("total-blocking-time", {}).get("numericValue")
    print(
        f"{name:8} perf={scores.get('performance')} a11y={scores.get('accessibility')} "
        f"LCP={lcp:.0f}ms CLS={cls:.3f} TBT={tbt:.0f}ms"
    )
    if scores.get("performance", 0) < 90:
        fails.append(f"{name}: Performance {scores.get('performance')} < 90")
    if scores.get("accessibility", 0) < 95:
        fails.append(f"{name}: Accessibility {scores.get('accessibility')} < 95")
    if lcp is not None and lcp > 2500:
        fails.append(f"{name}: LCP {lcp:.0f}ms > 2500ms")
    if cls is not None and cls > 0.1:
        fails.append(f"{name}: CLS {cls:.3f} > 0.1")
    if tbt is not None and tbt > 200:
        fails.append(f"{name}: TBT {tbt:.0f}ms > 200ms")

if not fails:
    passes.append("Lighthouse 六页达标")

host = urlsplit(base).hostname or ""
local = host in {"127.0.0.1", "localhost", "::1"}

if local:
    print("localhost：跳过安全头与 Set-Cookie 检查")
else:
    request = urllib.request.Request(
        base + "/",
        headers={"User-Agent": "YangSpec preview check"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        headers = {key.lower(): value for key, value in response.headers.items()}
        body = response.read().decode("utf-8", "replace")

    if "set-cookie" in headers:
        fails.append(f"站点写了 Set-Cookie：{headers['set-cookie'][:80]}")
    else:
        passes.append("没有 Set-Cookie")

    if headers.get("x-content-type-options", "").lower() != "nosniff":
        fails.append("缺少 X-Content-Type-Options: nosniff")
    if not headers.get("referrer-policy"):
        fails.append("缺少 Referrer-Policy")
    if not headers.get("permissions-policy"):
        fails.append("缺少 Permissions-Policy")
    csp = headers.get("content-security-policy", "")
    if headers.get("x-frame-options", "").upper() != "DENY" and "frame-ancestors 'none'" not in csp:
        fails.append("缺少 X-Frame-Options: DENY 或 frame-ancestors 'none'")

    class Refs(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.urls = []

        def handle_starttag(self, tag, attrs):
            values = {key: value for key, value in attrs if value is not None}
            if tag in {"script", "img", "iframe"} and values.get("src"):
                self.urls.append(values["src"])
            if tag == "link" and values.get("href"):
                # canonical、alternate 这类关系只声明身份，浏览器不会请求；
                # 只统计会真正取资源的 rel，避免把生产域名误报成第三方请求。
                fetching = {
                    "stylesheet",
                    "icon",
                    "apple-touch-icon",
                    "mask-icon",
                    "manifest",
                    "preload",
                    "modulepreload",
                    "prefetch",
                    "preconnect",
                    "dns-prefetch",
                }
                rels = set((values.get("rel") or "").lower().split())
                if rels & fetching:
                    self.urls.append(values["href"])

    parser = Refs()
    parser.feed(body)
    allowed = {"static.cloudflareinsights.com"}
    origin = urlsplit(base).netloc
    for value in parser.urls:
        parts = urlsplit(value)
        if parts.scheme not in ("http", "https") or not parts.netloc:
            continue
        if parts.netloc == origin or parts.netloc in allowed:
            continue
        fails.append(f"第三方请求：{value}")

for message in passes:
    print(f"[PASS] {message}")
for message in fails:
    print(f"[FAIL] {message}")
sys.exit(1 if fails else 0)
PY
