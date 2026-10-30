#!/usr/bin/env python3
"""YangSpec 站点静态检查。

只读构建产物与源码，不改文件。用于 scripts/check.sh；
也可以单独运行：python3 scripts/check.py public [--external]

检查项：
  1. 必需页面与 sitemap
  2. 站内链接、锚点、空链接
  3. 外部脚本、混合内容、外部图片
  4. Front matter 必填字段
  5. 邮箱/城市是否从 params 取值
  6. 源码隐私（Cookie、第三方统计、localStorage 用途）
  7. 未完成占位
  8. 单页传输量与 JS 预算
  9. 外链状态（--external）
"""

from __future__ import annotations

import argparse
import gzip
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urljoin, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
SITE_HOSTS = {"yangspec.com", "www.yangspec.com"}
ALLOWED_SCRIPT_HOSTS = {"static.cloudflareinsights.com"}
REQUIRED_PAGES = [
    "index.html",
    "about/index.html",
    "contact/index.html",
    "privacy/index.html",
    "posts/index.html",
    "404.html",
]
SKIP_DIRS = {"archive", "themes", ".git", "public", "resources", "node_modules"}

FAILS: list[str] = []
WARNS: list[str] = []
PASSES: list[str] = []


def ok(message: str) -> None:
    PASSES.append(message)


def warn(message: str) -> None:
    WARNS.append(message)


def fail(message: str) -> None:
    FAILS.append(message)


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.refs: list[tuple[str, str, str]] = []
        self.ids: set[str] = set()
        self.scripts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value for key, value in attrs if value is not None}
        if values.get("id"):
            self.ids.add(values["id"])
        if tag == "a" and values.get("name"):
            self.ids.add(values["name"])
        for attr in ("href", "src"):
            if attr in values:
                self.refs.append((tag, attr, values[attr]))
        if tag == "script" and values.get("src"):
            self.scripts.append(values["src"])


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def gzip_size(path: Path) -> int:
    return len(gzip.compress(path.read_bytes(), 9))


def page_url(relative: Path) -> str:
    url = "/" + relative.as_posix()
    if url.endswith("/index.html"):
        return url[: -len("index.html")]
    return url


def internal_target(site: Path, path: str) -> Path | None:
    """把 URL 路径映射到构建产物里的文件。"""
    clean = unquote(path)
    if clean in ("", "/"):
        candidate = site / "index.html"
        return candidate if candidate.exists() else None
    raw = clean.lstrip("/")
    candidates = [
        site / raw,
        site / raw / "index.html",
        site / (raw.rstrip("/") + ".html"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def load_params() -> tuple[str, str]:
    text = read_text(ROOT / "hugo.toml")
    match = re.search(r"(?ms)^\[params\]\s*$(.*?)(?=^\[|\Z)", text)
    block = match.group(1) if match else ""
    email = re.search(r'(?m)^\s*email\s*=\s*"([^"]+)"', block)
    city = re.search(r'(?m)^\s*city\s*=\s*"([^"]+)"', block)
    if not email:
        fail("hugo.toml 的 [params] 缺少 email")
    if not city:
        fail("hugo.toml 的 [params] 缺少 city")
    return (email.group(1) if email else "", city.group(1) if city else "")


def check_pages(site: Path) -> dict[Path, PageParser]:
    pages: dict[Path, PageParser] = {}
    for rel in REQUIRED_PAGES:
        if not (site / rel).is_file():
            fail(f"缺少页面：{rel}")
    if all((site / rel).is_file() for rel in REQUIRED_PAGES):
        ok(f"必需页面齐全（{len(REQUIRED_PAGES) - 1} 个路由 + 404）")

    for path in sorted(site.rglob("*.html")):
        parser = PageParser()
        parser.feed(read_text(path))
        pages[path.relative_to(site)] = parser

    sitemap = site / "sitemap.xml"
    if sitemap.is_file():
        locations = re.findall(r"<loc>(.*?)</loc>", read_text(sitemap))
        required = {"/", "/about/", "/contact/", "/privacy/", "/posts/"}
        found = {urlsplit(url).path or "/" for url in locations}
        # 构建产物里的每个 index.html 都应有条目，sitemap 也不应指向不存在的页面。
        indexable = {
            "/" + path.relative_to(site).as_posix()[: -len("index.html")]
            for path in site.rglob("index.html")
        }
        missing = required - found
        omitted = indexable - found
        unknown = found - indexable
        if missing:
            fail(f"sitemap 缺少：{', '.join(sorted(missing))}")
        if omitted:
            fail(f"sitemap 漏掉构建页面：{', '.join(sorted(omitted))}")
        if unknown:
            fail(f"sitemap 含不存在的页面：{', '.join(sorted(unknown))}")
        if "/404.html" in found:
            fail("sitemap 不应包含 404.html")
        if not (missing or omitted or unknown or "/404.html" in found):
            ok(f"sitemap 覆盖全部 {len(found)} 个可索引页面（不含 404）")
    else:
        fail("缺少 sitemap.xml")
    return pages


def check_links(site: Path, pages: dict[Path, PageParser]) -> set[str]:
    external: set[str] = set()
    id_cache: dict[Path, set[str]] = {}

    def ids_for(target: Path) -> set[str]:
        if target not in id_cache:
            parser = PageParser()
            parser.feed(read_text(target))
            id_cache[target] = parser.ids
        return id_cache[target]

    broken = 0
    for relative, parser in pages.items():
        base = page_url(relative)
        for tag, attr, raw_value in parser.refs:
            value = raw_value.strip()
            if not value:
                fail(f"{relative}: 空 {tag} {attr}")
                broken += 1
                continue
            if value == "#":
                fail(f"{relative}: 假链接 href=\"#\"")
                broken += 1
                continue
            if value.startswith("#"):
                if value[1:] not in parser.ids:
                    fail(f"{relative}: 锚点不存在 {value}")
                    broken += 1
                continue

            parts = urlsplit(value)
            scheme = parts.scheme.lower()
            if scheme in ("mailto", "tel", "javascript", "data"):
                continue

            absolute = urljoin(base, value)
            parts = urlsplit(absolute)
            if parts.scheme in ("http", "https"):
                if parts.netloc and parts.netloc not in SITE_HOSTS:
                    external.add(absolute)
                    continue
                path = parts.path
            elif parts.scheme:
                continue
            else:
                path = parts.path

            target = internal_target(site, path)
            if target is None:
                fail(f"{relative}: 站内链接不存在 {value}")
                broken += 1
                continue
            if parts.fragment and target.suffix == ".html":
                if unquote(parts.fragment) not in ids_for(target):
                    fail(f"{relative}: 锚点不存在 {value}")
                    broken += 1

    if broken == 0:
        ok(f"站内链接与锚点全部可达（{len(pages)} 个页面）")
    return external


def check_assets(site: Path, pages: dict[Path, PageParser]) -> None:
    external_scripts: list[str] = []
    for relative, parser in pages.items():
        base = page_url(relative)
        for tag, attr, value in parser.refs:
            absolute = urljoin(base, value)
            parts = urlsplit(absolute)
            if parts.scheme not in ("http", "https") or not parts.netloc:
                continue
            if parts.netloc in SITE_HOSTS:
                continue
            if tag == "script" and attr == "src":
                if parts.netloc not in ALLOWED_SCRIPT_HOSTS:
                    external_scripts.append(f"{relative}: {value}")
            elif tag == "img" and attr == "src":
                fail(f"{relative}: 外部图片 {value}")
            elif tag == "link" and attr == "href" and parts.path.endswith(
                (".css", ".woff", ".woff2")
            ):
                fail(f"{relative}: 外部样式/字体 {value}")
    if external_scripts:
        fail("出现未登记的第三方脚本：" + "; ".join(external_scripts))
    else:
        ok("没有未登记的第三方脚本或外部图片")


def check_content(email: str) -> None:
    content = ROOT / "content"
    count = 0
    for path in sorted(content.rglob("*.md")):
        if SKIP_DIRS & set(path.parts):
            continue
        count += 1
        text = read_text(path)
        if not text.startswith("---"):
            fail(f"{path.relative_to(ROOT)}: 缺少 Front matter")
            continue
        end = text.find("\n---", 3)
        if end == -1:
            fail(f"{path.relative_to(ROOT)}: Front matter 未闭合")
            continue
        front = text[3:end]
        for key in ("title", "date", "description"):
            if not re.search(rf"(?m)^{key}\s*:", front):
                fail(f"{path.relative_to(ROOT)}: Front matter 缺少 {key}")
        for found in re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text):
            if found != email:
                fail(f"{path.relative_to(ROOT)}: 邮箱 {found} 与 params.email 不一致")
    if count:
        ok(f"Front matter 与邮箱一致性检查通过（{count} 篇）")


def check_identity(city: str, email: str) -> None:
    leaked = False
    for path in sorted((ROOT / "layouts").rglob("*.html")):
        text = read_text(path)
        relative = path.relative_to(ROOT)
        if email and email in text:
            fail(f"{relative}: 模板硬编码了邮箱，应使用 site.Params.email")
            leaked = True
        if city and city in text:
            fail(f"{relative}: 模板硬编码了城市，应使用 site.Params.city")
            leaked = True
    if not leaked:
        ok("模板未硬编码邮箱与城市")


def scan_sources() -> list[Path]:
    targets: list[Path] = []
    for folder in ("content", "layouts", "assets", "static"):
        base = ROOT / folder
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if SKIP_DIRS & set(path.parts):
                continue
            if path.suffix.lower() in {".md", ".html", ".js", ".css", ".toml", ".json"}:
                targets.append(path)
    return targets


def check_privacy() -> None:
    patterns = {
        r"document\.cookie": "写 Cookie",
        r"\bgtag\s*\(": "Google Analytics",
        r"googletagmanager": "Google Tag Manager",
        r"google-analytics": "Google Analytics",
        r"plausible\.io": "Plausible",
        r"umami\.is": "Umami",
        r"hotjar": "Hotjar",
        r"clarity\.ms": "Microsoft Clarity",
        r"connect\.facebook\.net": "Meta Pixel",
        r"doubleclick": "DoubleClick",
    }
    hits: list[str] = []
    for path in scan_sources():
        text = read_text(path)
        relative = path.relative_to(ROOT)
        for pattern, label in patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                hits.append(f"{relative}: {label}")
        if (
            path.suffix != ".md"
            and "localStorage" in text
            and relative.as_posix() != "assets/js/site.js"
        ):
            hits.append(f"{relative}: localStorage 只允许用于主题偏好")
    if hits:
        for hit in hits:
            fail("隐私扫描：" + hit)
    else:
        ok("源码无 Cookie、第三方统计或额外 localStorage")

    site_js = ROOT / "assets/js/site.js"
    if site_js.is_file() and "pref-theme" not in read_text(site_js):
        fail("assets/js/site.js 使用了 localStorage，但未使用 pref-theme")


def check_stubs() -> None:
    hits = []
    for path in scan_sources():
        if path.suffix.lower() not in {".md", ".html", ".js", ".css"}:
            continue
        text = read_text(path)
        for match in re.finditer(r"\b(TODO|FIXME)\b", text):
            line = text.count("\n", 0, match.start()) + 1
            hits.append(f"{path.relative_to(ROOT)}:{line}")
    if hits:
        fail("未完成占位：" + ", ".join(hits))
    else:
        ok("没有 TODO/FIXME 占位")


def check_weight(site: Path, pages: dict[Path, PageParser]) -> None:
    heaviest = (0, "")
    js_total: dict[Path, int] = {}
    for relative, parser in pages.items():
        base = page_url(relative)
        total = gzip_size(site / relative)
        seen: set[Path] = set()
        for tag, attr, value in parser.refs:
            if (tag, attr) not in {("link", "href"), ("script", "src"), ("img", "src")}:
                continue
            parts = urlsplit(urljoin(base, value))
            if parts.scheme in ("http", "https") and parts.netloc not in SITE_HOSTS:
                continue
            target = internal_target(site, parts.path)
            if target is None or target in seen:
                continue
            seen.add(target)
            if target.suffix.lower() in {".css", ".js", ".png", ".jpg", ".jpeg", ".webp", ".avif", ".svg"}:
                total += gzip_size(target)
                if target.suffix.lower() == ".js":
                    js_total[target] = gzip_size(target)
        if total > heaviest[0]:
            heaviest = (total, relative.as_posix())
    if heaviest[0] > 1_000_000:
        fail(f"单页传输量 {heaviest[0] / 1000:.1f} KB 超过 1 MB：{heaviest[1]}")
    else:
        ok(f"最重页面 {heaviest[0] / 1000:.1f} KB（gzip，{heaviest[1]}）")
    js_bytes = sum(js_total.values())
    if js_bytes > 10_000:
        fail(f"首方 JS {js_bytes / 1000:.1f} KB（gzip）超过 10 KB")
    else:
        ok(f"首方 JS {js_bytes / 1000:.1f} KB（gzip）")


def check_external(urls: set[str]) -> None:
    if not urls:
        ok("没有需要检查的外链")
        return
    failures = 0
    for url in sorted(urls):
        status = None
        for method in ("HEAD", "GET"):
            request = Request(
                url,
                method=method,
                headers={"User-Agent": "YangSpec link check (+https://yangspec.com)"},
            )
            try:
                with urlopen(request, timeout=15) as response:
                    status = response.status
                break
            except HTTPError as error:
                status = error.code
                if method == "HEAD" and status in (403, 405, 429):
                    continue
                break
            except (URLError, TimeoutError, OSError) as error:
                status = str(error)
                break
        if isinstance(status, int) and 200 <= status < 400:
            continue
        if status in (403, 429):
            warn(f"外链暂时拒绝访问（{status}）：{url}")
            continue
        fail(f"外链失败（{status}）：{url}")
        failures += 1
    if failures == 0:
        ok(f"外链可达（{len(urls)} 个）")


def main() -> int:
    parser = argparse.ArgumentParser(description="YangSpec 站点静态检查")
    parser.add_argument("site", nargs="?", default="public", help="构建产物目录")
    parser.add_argument("--external", action="store_true", help="检查外链状态")
    args = parser.parse_args()

    site = (ROOT / args.site).resolve()
    if not site.is_dir():
        print(f"找不到构建产物：{site}", file=sys.stderr)
        return 2

    email, city = load_params()
    pages = check_pages(site)
    external = check_links(site, pages)
    check_assets(site, pages)
    check_content(email)
    check_identity(city, email)
    check_privacy()
    check_stubs()
    check_weight(site, pages)
    if args.external:
        check_external(external)

    for message in PASSES:
        print(f"[PASS] {message}")
    for message in WARNS:
        print(f"[WARN] {message}")
    for message in FAILS:
        print(f"[FAIL] {message}")

    if FAILS:
        print(f"\n{len(FAILS)} 项失败")
        return 1
    print(f"\n全部通过（{len(PASSES)} 项）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
