#!/usr/bin/env python3
"""YangSpec 站点静态检查。

只读构建产物与源码，不改文件。用于 scripts/check.sh；
也可以单独运行：python3 scripts/check.py public [--external]

检查项：
  1. 必需页面与 sitemap（分页页不进 sitemap）
  2. 站内链接、锚点、空链接
  3. 外部脚本、混合内容、外部图片
  4. Front matter 必填字段
  5. 邮箱/城市是否从 params 取值
  6. 源码隐私（Cookie、第三方统计、localStorage 用途）
  7. 未完成占位
  8. 单页传输量与 JS 预算
  9. 分页结构（页数、每页篇数、页码链、不重不漏）
  10. 归档覆盖（按年分组、不重不漏、只输出 HTML）
  11. 上一篇/下一篇链
  12. 文章最后更新渲染
  13. 文档栏目（总览、正文页数、不分页、sitemap、侧栏覆盖、上一节/下一节）
  14. llms.txt（存在、H1/摘要、覆盖 sitemap、无草稿与死链）
  15. 外链状态（--external）
"""

from __future__ import annotations

import argparse
import gzip
import re
import sys
from collections import Counter
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
    "archives/index.html",
    "docs/index.html",
    "404.html",
]
SKIP_DIRS = {"archive", "themes", ".git", "public", "resources", "node_modules"}

# 每页文章数记录在 docs/adr/0004；这里作为契约校验，防止配置回退成 Hugo 默认值。
EXPECTED_PAGER_SIZE = 8
# Hugo 会为分页生成 /posts/page/<n>/（含指向 /posts/ 的 page/1 别名），sitemap 不含分页页。
PAGINATION_ARTIFACT_RE = re.compile(r"(?:^|/)page/\d+/index\.html$")
POST_HREF_RE = re.compile(r"^/posts/(?!page(?:/|$))([^/]+)/$")
DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})")
PAGINATION_NAV_RE = re.compile(r"<nav[^>]*class=\"pagination\"[^>]*>(.*?)</nav>", re.S)
CURRENT_PAGE_RE = re.compile(r"<span[^>]*class=\"pagination-current\"[^>]*>\s*(\d+)\s*</span>")
PAGER_LINK_RE = re.compile(r"<a[^>]*href=\"([^\"]+)\"[^>]*>\s*(\d+)\s*</a>")
ARCHIVE_YEAR_RE = re.compile(r"<h2[^>]*class=\"archive-year\"[^>]*>", re.S)
YEAR_ID_RE = re.compile(r"id=\"archive-year-(\d{4})\"")
ARCHIVE_COUNT_RE = re.compile(r"(\d+)\s*篇")
ANCHOR_RE = re.compile(r"<a\b[^>]*\bhref=\"([^\"]+)\"[^>]*>", re.I)
POST_NAV_RE = re.compile(r"<nav[^>]*class=\"post-nav\"[^>]*>(.*?)</nav>", re.S)
POST_UPDATED_RE = re.compile(r"<p[^>]*class=\"post-updated\"[^>]*>(.*?)</p>", re.S)
TIME_DATE_RE = re.compile(r"<time[^>]*datetime=\"(\d{4}-\d{2}-\d{2})\"")
# /llms.txt 里的 Markdown 链接；只取目标，不看链接文字。
LLMS_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
LLMS_MAX_BYTES = 250_000

# 站内文档：content/docs/ 生成 /docs/；仓库 docs/ 是维护者文档，不参与构建。
DOCS_SOURCE_DIR = ROOT / "content" / "docs"
DOCS_NAV_DESKTOP_RE = re.compile(
    r"<nav\b[^>]*\bclass=\"[^\"]*\bdocs-nav\b[^\"]*\"[^>]*>(.*?)</nav>", re.S
)
DOCS_NAV_FOLD_RE = re.compile(
    r"<details\b[^>]*\bclass=\"[^\"]*\bdocs-nav-fold\b[^\"]*\"[^>]*>(.*?)</details>", re.S
)
ANCHOR_TAG_RE = re.compile(r"<a\b[^>]*>", re.I)
HREF_ATTR_RE = re.compile(r'href="([^"]*)"')
REL_ATTR_RE = re.compile(r'rel="([^"]*)"')

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


def front_matter(path: Path) -> dict[str, str]:
    """读取 Front matter 的顶层标量字段；不解析嵌套结构。"""
    text = read_text(path)
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fields: dict[str, str] = {}
    for line in text[3:end].splitlines():
        match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*)\s*:\s*(.+?)\s*$", line)
        if not match:
            continue
        fields[match.group(1)] = match.group(2).strip().strip('"').strip("'")
    return fields


def date_part(value: str | None) -> str:
    """把 Front matter 日期归一成 YYYY-MM-DD。"""
    if not value:
        return ""
    match = DATE_RE.match(value.strip().strip('"').strip("'"))
    return match.group(1) if match else ""


def load_posts() -> dict[str, dict[str, str]]:
    """content/posts/*.md → /posts/<slug>/ 的 Front matter 摘要。"""
    posts: dict[str, dict[str, str]] = {}
    for path in sorted((ROOT / "content" / "posts").glob("*.md")):
        if path.name == "_index.md":
            continue
        fields = front_matter(path)
        slug = fields.get("slug") or path.stem
        posts[f"/posts/{slug}/"] = {
            "file": path.relative_to(ROOT).as_posix(),
            "date": date_part(fields.get("date")),
            "lastmod": date_part(fields.get("lastmod")),
        }
    return posts


def built_posts(site: Path) -> dict[str, Path]:
    """构建产物里的文章页：/posts/<slug>/ → 相对路径。"""
    posts: dict[str, Path] = {}
    for path in sorted(site.glob("posts/*/index.html")):
        relative = path.relative_to(site)
        parts = relative.parts
        if len(parts) == 3 and parts[1] != "page":
            posts[f"/posts/{parts[1]}/"] = relative
    return posts


def resolved_post_meta(
    posts: dict[str, dict[str, str]], built: dict[str, Path]
) -> dict[str, dict[str, str]]:
    """把构建出来的文章对回内容源；对不上就报错，避免顺序校验静默跳过。"""
    resolved: dict[str, dict[str, str]] = {}
    unmatched: list[str] = []
    for url in sorted(built):
        meta = posts.get(url)
        if meta is None or not meta["date"]:
            unmatched.append(url)
        else:
            resolved[url] = meta
    if unmatched:
        fail("构建产物中的文章在 content/posts 找不到可用的 Front matter：" + ", ".join(unmatched))
    return resolved


def post_slugs(parser: PageParser) -> list[str]:
    """列表页里 /posts/<slug>/ 形式的文章链接，按出现顺序返回。"""
    slugs: list[str] = []
    for tag, attr, value in parser.refs:
        if tag != "a" or attr != "href":
            continue
        match = POST_HREF_RE.match(urlsplit(value).path)
        if match:
            slugs.append(match.group(1))
    return slugs


def normalize_post_url(value: str) -> str:
    path = urlsplit(value).path
    if not path.startswith("/"):
        path = "/" + path
    if not path.endswith("/"):
        path += "/"
    return path


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
        required = {"/", "/about/", "/contact/", "/privacy/", "/posts/", "/archives/", "/docs/"}
        found = {urlsplit(url).path or "/" for url in locations}
        # 构建产物里的每个 index.html 都应有条目，sitemap 也不应指向不存在的页面。
        # 分页页（/posts/page/<n>/）与 page/1 别名不进 sitemap，必须排除。
        indexable = {
            "/" + path.relative_to(site).as_posix()[: -len("index.html")]
            for path in site.rglob("index.html")
            if not PAGINATION_ARTIFACT_RE.search(path.relative_to(site).as_posix())
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
            ok(f"sitemap 覆盖全部 {len(found)} 个可索引页面（不含分页页与 404）")
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
                # 页内锚点可能是百分号编码的中文 id（如文档页内目录）。
                if unquote(value[1:]) not in parser.ids:
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


def load_pager_size() -> int | None:
    """读 hugo.toml 的 [pagination] pagerSize，并校验与 ADR 0004 的决定一致。"""
    text = read_text(ROOT / "hugo.toml")
    block = re.search(r"(?ms)^\[pagination\]\s*$(.*?)(?=^\[|\Z)", text)
    match = re.search(r"(?m)^\s*pagerSize\s*=\s*(\d+)\s*$", block.group(1)) if block else None
    if not match:
        fail(f"hugo.toml 缺少 [pagination] pagerSize = {EXPECTED_PAGER_SIZE}（见 docs/adr/0004）")
        return None
    size = int(match.group(1))
    if size != EXPECTED_PAGER_SIZE:
        fail(
            f"hugo.toml 的 pagerSize = {size}，与 docs/adr/0004 记录的每页 "
            f"{EXPECTED_PAGER_SIZE} 篇不一致"
        )
        return None
    return size


def pagination_page_numbers(site: Path) -> list[int]:
    numbers: list[int] = []
    for path in site.glob("posts/page/*/index.html"):
        parts = path.relative_to(site).parts
        if len(parts) == 4 and parts[2].isdigit():
            numbers.append(int(parts[2]))
    return sorted(numbers)


def page_number_from_href(href: str) -> int | None:
    path = urlsplit(href).path
    if path.rstrip("/") == "/posts":
        return 1
    match = re.match(r"^/posts/page/(\d+)/$", path)
    return int(match.group(1)) if match else None


def check_pagination(site: Path, pages: dict[Path, PageParser], built: dict[str, Path]) -> None:
    pager = load_pager_size()
    if pager is None:
        return

    total = len(built)
    expected_pages = (total + pager - 1) // pager
    numbers = pagination_page_numbers(site)
    list_rel = Path("posts/index.html")
    if list_rel not in pages:
        fail("缺少 /posts/ 列表页，无法检查分页结构")
        return

    problems: list[str] = []

    if expected_pages <= 1:
        extra = [number for number in numbers if number >= 2]
        if extra:
            problems.append("文章不足一页，不应生成分页页：" + ", ".join(map(str, extra)))
        if PAGINATION_NAV_RE.search(read_text(site / list_rel)):
            problems.append("只有一页时不应渲染分页导航")
    else:
        missing_pages = [number for number in range(2, expected_pages + 1) if number not in numbers]
        if missing_pages:
            problems.append(
                "分页页缺失：" + ", ".join(f"/posts/page/{number}/" for number in missing_pages)
            )
        unexpected = [number for number in numbers if number > expected_pages]
        if unexpected:
            problems.append(
                f"分页页数超出预期（{total} 篇 / 每页 {pager} 篇 = {expected_pages} 页）："
                + ", ".join(map(str, unexpected))
            )

        page_sets: dict[int, list[str]] = {}
        list_pages: list[tuple[int, Path]] = [(1, list_rel)] + [
            (number, Path(f"posts/page/{number}/index.html"))
            for number in range(2, expected_pages + 1)
        ]
        for number, relative in list_pages:
            parser = pages.get(relative)
            if parser is None:
                problems.append(f"缺少列表页 {relative.as_posix()}，无法核对第 {number} 页")
                continue
            slugs = post_slugs(parser)
            page_sets[number] = slugs
            expected_count = (
                pager if number < expected_pages else total - pager * (expected_pages - 1)
            )
            if len(slugs) != expected_count:
                problems.append(
                    f"第 {number} 页显示 {len(slugs)} 篇，每页 {pager} 篇时应为 {expected_count} 篇"
                )
            if len(slugs) != len(set(slugs)):
                problems.append(f"第 {number} 页有重复的文章链接")

            block = PAGINATION_NAV_RE.search(read_text(site / relative))
            if block is None:
                problems.append(f"第 {number} 页缺少分页导航")
                continue
            current = CURRENT_PAGE_RE.search(block.group(1))
            if current is None or int(current.group(1)) != number:
                problems.append(f"第 {number} 页的当前页标记不正确")
            targets: dict[int, int] = {}
            for href, label in PAGER_LINK_RE.findall(block.group(1)):
                target = page_number_from_href(href)
                if target is None:
                    problems.append(f"第 {number} 页有无法识别的分页链接 {href}")
                    continue
                targets[int(label)] = target
            # 当前页用 span 标记，其余页才是链接：两者合起来必须覆盖全部页码。
            labels = set(targets)
            if current is not None:
                labels.add(int(current.group(1)))
            if sorted(labels) != list(range(1, expected_pages + 1)):
                problems.append(f"第 {number} 页页码不全（应为 1–{expected_pages}）")
            for label, target in sorted(targets.items()):
                if label != target:
                    problems.append(f"第 {number} 页的页码 {label} 指向第 {target} 页")

        covered = [slug for slugs in page_sets.values() for slug in slugs]
        built_slugs = {url.strip("/").split("/")[-1] for url in built}
        if len(covered) != len(set(covered)):
            problems.append("分页列表出现重复文章")
        missing_slugs = built_slugs - set(covered)
        if missing_slugs:
            problems.append("分页列表漏掉文章：" + ", ".join(sorted(missing_slugs)))
        extra_slugs = set(covered) - built_slugs
        if extra_slugs:
            problems.append("分页列表包含不存在的文章：" + ", ".join(sorted(extra_slugs)))

    for problem in problems:
        fail("分页：" + problem)
    if not problems:
        if expected_pages <= 1:
            ok(f"分页结构正确（{total} 篇文章，1 页，未渲染分页导航）")
        else:
            ok(f"分页结构正确（{total} 篇 / 每页 {pager} 篇 / {expected_pages} 页，不重不漏）")


def has_archive_entry(parser: PageParser) -> bool:
    for tag, attr, value in parser.refs:
        if tag != "a" or attr != "href":
            continue
        if urlsplit(value).path.rstrip("/") == "/archives":
            return True
    return False


def check_archives(
    site: Path,
    pages: dict[Path, PageParser],
    built: dict[str, Path],
    posts: dict[str, dict[str, str]],
    resolved: dict[str, dict[str, str]],
) -> None:
    archive_rel = Path("archives/index.html")
    if archive_rel not in pages:
        fail("缺少 /archives/ 归档页，无法检查归档覆盖")
        return

    problems: list[str] = []
    archive_dir = site / "archives"
    if (archive_dir / "index.xml").is_file():
        problems.append("只应输出 HTML，不应生成 /archives/index.xml")
    if any((archive_dir / "page").glob("*/index.html")):
        problems.append("归档页不应分页")

    html = read_text(site / archive_rel)
    headings = list(ARCHIVE_YEAR_RE.finditer(html))
    if not headings:
        fail("归档页缺少年份分组标题")
        return

    groups: list[dict[str, object]] = []
    for index, match in enumerate(headings):
        tag = match.group(0)
        strip = html.find("</h2>", match.end())
        heading_text = html[match.end() : strip] if strip != -1 else ""
        year_match = YEAR_ID_RE.search(tag) or re.search(r"(\d{4})\s*年", heading_text)
        if year_match is None:
            problems.append("有年份分组标题缺少年份")
            continue
        count_match = ARCHIVE_COUNT_RE.search(heading_text)
        groups.append(
            {
                "year": year_match.group(1),
                "start": strip + len("</h2>") if strip != -1 else match.end(),
                "end": headings[index + 1].start() if index + 1 < len(headings) else len(html),
                "count": int(count_match.group(1)) if count_match else None,
            }
        )

    expected_by_year: dict[str, set[str]] = {}
    for url in built:
        meta = resolved.get(url)
        if meta is None:
            continue
        expected_by_year.setdefault(meta["date"][:4], set()).add(url.strip("/").split("/")[-1])

    seen_years: list[str] = []
    all_seen: list[str] = []
    for group in groups:
        year = str(group["year"])
        seen_years.append(year)
        slugs: list[str] = []
        for match in ANCHOR_RE.finditer(html, int(group["start"]), int(group["end"])):
            post_match = POST_HREF_RE.match(urlsplit(match.group(1)).path)
            if post_match:
                slugs.append(post_match.group(1))
        all_seen.extend(slugs)
        if len(slugs) != len(set(slugs)):
            problems.append(f"{year} 年有重复文章链接")
        expected = expected_by_year.get(year, set())
        missing = expected - set(slugs)
        extra = set(slugs) - expected
        if missing:
            problems.append(f"{year} 年漏掉文章：" + ", ".join(sorted(missing)))
        if extra:
            problems.append(f"{year} 年多出文章：" + ", ".join(sorted(extra)))
        if group["count"] is not None and int(group["count"]) != len(slugs):
            problems.append(f"{year} 年的篇数标注与文章链接数不一致")

    expected_years = sorted(expected_by_year, reverse=True)
    if seen_years != expected_years:
        missing_years = sorted(set(expected_years) - set(seen_years), reverse=True)
        extra_years = sorted(set(seen_years) - set(expected_years), reverse=True)
        if missing_years:
            problems.append("缺少年份分组：" + ", ".join(missing_years))
        if extra_years:
            problems.append("多出年份分组：" + ", ".join(extra_years))
    if len(all_seen) != len(set(all_seen)):
        problems.append("同一篇文章在多个年份分组中重复出现")

    expected_slugs = {url.strip("/").split("/")[-1] for url in built}
    if set(all_seen) != expected_slugs:
        missing = expected_slugs - set(all_seen)
        if missing:
            problems.append("归档漏掉文章：" + ", ".join(sorted(missing)))
        extra = set(all_seen) - expected_slugs
        if extra:
            problems.append("归档包含不存在的文章：" + ", ".join(sorted(extra)))

    # 归档入口：列表页尾部链接 + 页脚（首页可见）。
    for relative in (Path("posts/index.html"), Path("index.html")):
        parser = pages.get(relative)
        if parser is not None and not has_archive_entry(parser):
            problems.append(f"{relative.as_posix()} 缺少 /archives/ 入口链接")

    for problem in problems:
        fail("归档：" + problem)
    if not problems:
        ok(
            f"归档覆盖全部 {len(built)} 篇文章"
            f"（{len(groups)} 个年份分组，倒序，只输出 HTML）"
        )


def post_nav_links(html: str) -> tuple[str | None, str | None, list[str]]:
    """解析文章页的上一篇/下一篇导航；返回 (prev, next, 结构问题)。"""
    block = POST_NAV_RE.search(html)
    if block is None:
        return (None, None, [])
    prev_href: str | None = None
    next_href: str | None = None
    problems: list[str] = []
    for match in ANCHOR_RE.finditer(block.group(1)):
        attrs = match.group(0)
        href_match = re.search(r'href="([^"]*)"', attrs)
        rel_match = re.search(r'rel="([^"]*)"', attrs)
        if href_match is None:
            problems.append("导航链接缺少 href")
            continue
        rels = set(rel_match.group(1).split()) if rel_match else set()
        if "prev" in rels:
            if prev_href is not None:
                problems.append("出现多个 rel=prev")
            prev_href = href_match.group(1)
        elif "next" in rels:
            if next_href is not None:
                problems.append("出现多个 rel=next")
            next_href = href_match.group(1)
        else:
            problems.append("导航链接缺少 rel=prev/next")
    return (prev_href, next_href, problems)


def check_post_navigation(
    site: Path,
    built: dict[str, Path],
    resolved: dict[str, dict[str, str]],
) -> None:
    total = len(built)
    if total == 0:
        ok("没有文章，跳过上一篇/下一篇检查")
        return

    problems: list[str] = []
    edges: dict[str, dict[str, str | None]] = {}
    for url, relative in sorted(built.items()):
        prev_href, next_href, structure_problems = post_nav_links(read_text(site / relative))
        for message in structure_problems:
            problems.append(f"{url}: {message}")
        prev_url = normalize_post_url(prev_href) if prev_href else None
        next_url = normalize_post_url(next_href) if next_href else None
        for label, target in (("上一篇", prev_url), ("下一篇", next_url)):
            if target is not None and target not in built:
                problems.append(f"{url}: {label}链接指向不存在的文章 {target}")
        edges[url] = {"prev": prev_url, "next": next_url}

    if total == 1:
        url = next(iter(built))
        if edges[url]["prev"] or edges[url]["next"]:
            problems.append("只有一篇文章时不应渲染上一篇/下一篇")
        for problem in problems:
            fail("文章导航：" + problem)
        if not problems:
            ok("上一篇/下一篇正确（1 篇文章，无邻居导航）")
        return

    dates = [resolved[url]["date"] for url in built if url in resolved]
    unique_dates = len(dates) == total and len(set(dates)) == total
    if unique_dates:
        order = sorted(built, key=lambda url: resolved[url]["date"], reverse=True)
        for index, url in enumerate(order):
            expected_prev = order[index + 1] if index + 1 < total else None
            expected_next = order[index - 1] if index > 0 else None
            if edges[url]["prev"] != expected_prev:
                problems.append(
                    f"{url}: 上一篇应为 {expected_prev or '无（已是最早一篇）'}，"
                    f"实际为 {edges[url]['prev'] or '无'}"
                )
            if edges[url]["next"] != expected_next:
                problems.append(
                    f"{url}: 下一篇应为 {expected_next or '无（已是最新一篇）'}，"
                    f"实际为 {edges[url]['next'] or '无'}"
                )
    else:
        warn("文章日期有重复或缺失，只校验上下篇链的结构一致性，不校验先后方向")
        nexts = [edges[url]["next"] for url in built]
        prevs = [edges[url]["prev"] for url in built]
        if sum(1 for value in nexts if value is None) != 1:
            problems.append("应恰好有一篇最新文章没有下一篇")
        if sum(1 for value in prevs if value is None) != 1:
            problems.append("应恰好有一篇最早文章没有上一篇")
        for url in built:
            next_url = edges[url]["next"]
            if next_url is not None and edges.get(next_url, {}).get("prev") != url:
                problems.append(f"{url}: 下一篇 {next_url} 的上一篇没有指回来")
            prev_url = edges[url]["prev"]
            if prev_url is not None and edges.get(prev_url, {}).get("next") != url:
                problems.append(f"{url}: 上一篇 {prev_url} 的下一篇没有指回来")

    for problem in problems:
        fail("文章导航：" + problem)
    if not problems:
        ok(f"上一篇/下一篇链正确（{total} 篇，首末篇无多余邻居）")


def check_post_updated(
    site: Path,
    built: dict[str, Path],
    resolved: dict[str, dict[str, str]],
) -> None:
    problems: list[str] = []
    checked = 0
    for url, relative in sorted(built.items()):
        meta = resolved.get(url)
        if meta is None:
            continue
        checked += 1
        block = POST_UPDATED_RE.search(read_text(site / relative))
        lastmod = meta["lastmod"]
        needed = bool(lastmod) and lastmod != meta["date"]
        if needed and block is None:
            problems.append(f"{url}: 有 lastmod（{lastmod}）却没有渲染最后更新")
        elif not needed and block is not None:
            problems.append(f"{url}: date 与 lastmod 相同或没有 lastmod，不应渲染最后更新")
        elif needed and block is not None:
            time_match = TIME_DATE_RE.search(block.group(1))
            if time_match is None or time_match.group(1) != lastmod:
                problems.append(f"{url}: 最后更新日期与 lastmod {lastmod} 不一致")
    for problem in problems:
        fail("最后更新：" + problem)
    if not problems:
        ok(f"最后更新渲染与 Front matter 一致（{checked} 篇文章）")


def load_docs_order() -> list[dict[str, object]]:
    """content/docs/*.md 按 weight 升序；总览 _index.md 不参与排序。"""
    items: list[dict[str, object]] = []
    if not DOCS_SOURCE_DIR.is_dir():
        return items
    for path in sorted(DOCS_SOURCE_DIR.glob("*.md")):
        if path.name == "_index.md":
            continue
        fields = front_matter(path)
        try:
            weight = int(fields.get("weight") or 0)
        except ValueError:
            fail(f"{path.relative_to(ROOT)}: weight 不是整数")
            weight = 0
        slug = fields.get("slug") or path.stem
        items.append(
            {
                "url": f"/docs/{slug}/",
                "weight": weight,
                "file": path.relative_to(ROOT).as_posix(),
            }
        )
    items.sort(key=lambda item: (int(item["weight"]), str(item["url"])))
    return items


def built_docs(site: Path) -> dict[str, Path]:
    """构建产物里的文档正文页：/docs/<slug>/ → 相对路径。"""
    docs: dict[str, Path] = {}
    for path in sorted(site.glob("docs/*/index.html")):
        relative = path.relative_to(site)
        parts = relative.parts
        if len(parts) == 3 and parts[1] != "page":
            docs[f"/docs/{parts[1]}/"] = relative
    return docs


def normalize_docs_url(value: str) -> str:
    path = urlsplit(value).path
    if not path.startswith("/"):
        path = "/" + path
    if not path.endswith("/"):
        path += "/"
    return path


def docs_nav_links(html: str, pattern: re.Pattern[str]) -> list[str]:
    """从桌面侧栏或移动折叠块里取出文档链接（归一成 /docs/… 形式）。"""
    block = pattern.search(html)
    if block is None:
        return []
    links: list[str] = []
    for href in HREF_ATTR_RE.findall(block.group(1)):
        parts = urlsplit(href)
        if parts.scheme or not parts.path:
            continue
        path = normalize_docs_url(href)
        if path == "/docs/" or path.startswith("/docs/"):
            links.append(path)
    return links


def docs_pager_links(html: str) -> tuple[str | None, str | None, list[str]]:
    """解析文档页的上一节/下一节；返回 (prev, next, 结构问题)。"""
    prev_href: str | None = None
    next_href: str | None = None
    problems: list[str] = []
    for match in ANCHOR_TAG_RE.finditer(html):
        tag = match.group(0)
        rel_match = REL_ATTR_RE.search(tag)
        if rel_match is None:
            continue
        rels = set(rel_match.group(1).split())
        if not rels & {"prev", "next"}:
            continue
        href_match = HREF_ATTR_RE.search(tag)
        if href_match is None:
            problems.append("翻页链接缺少 href")
            continue
        if "prev" in rels:
            if prev_href is not None:
                problems.append("出现多个 rel=prev")
            prev_href = href_match.group(1)
        if "next" in rels:
            if next_href is not None:
                problems.append("出现多个 rel=next")
            next_href = href_match.group(1)
    return (
        normalize_docs_url(prev_href) if prev_href else None,
        normalize_docs_url(next_href) if next_href else None,
        problems,
    )


def check_docs_sidebar(html: str, label: str, targets: set[str]) -> list[str]:
    """桌面侧栏与移动折叠都要覆盖全部文档页 + 总览入口，各自不重不漏。"""
    problems: list[str] = []
    for name, pattern in (
        ("桌面侧栏", DOCS_NAV_DESKTOP_RE),
        ("移动端折叠目录", DOCS_NAV_FOLD_RE),
    ):
        links = docs_nav_links(html, pattern)
        if not links:
            problems.append(f"{label}: 缺少{name}")
            continue
        counts = Counter(links)
        for target in sorted(targets - set(counts)):
            problems.append(f"{label}: {name}缺少 {target}")
        for target in sorted(counts):
            if target in targets and counts[target] != 1:
                problems.append(f"{label}: {name}重复 {target}（{counts[target]} 次）")
    return problems


def check_docs_section(site: Path) -> None:
    """文档栏目：总览、正文页数、不分页、sitemap、侧栏覆盖、上一节/下一节。"""
    order = load_docs_order()
    if not order:
        fail("content/docs 没有文档正文，站点 /docs/ 栏目为空")
        return

    problems: list[str] = []
    built = built_docs(site)
    expected = {str(item["url"]) for item in order}

    if not (site / "docs" / "index.html").is_file():
        problems.append("缺少 /docs/ 总览页（docs/index.html）")
    if len(built) < 3:
        problems.append(f"文档正文页只有 {len(built)} 个，至少需要 3 个")
    if (site / "docs" / "page").exists():
        problems.append("文档栏目不应分页，但生成了 /docs/page/")
    if (site / "docs" / "index.xml").is_file():
        problems.append("文档栏目关闭 RSS，不应生成 /docs/index.xml")

    missing_built = expected - set(built)
    if missing_built:
        problems.append("content/docs 有源文件但未构建：" + ", ".join(sorted(missing_built)))
    extra_built = set(built) - expected
    if extra_built:
        problems.append("构建产物有 content/docs 找不到的文档页：" + ", ".join(sorted(extra_built)))

    sitemap = site / "sitemap.xml"
    if sitemap.is_file():
        found = {
            urlsplit(url).path or "/"
            for url in re.findall(r"<loc>(.*?)</loc>", read_text(sitemap))
        }
        for target in sorted((set(built) | {"/docs/"}) - found):
            problems.append(f"sitemap 缺少文档页 {target}")

    targets = set(built) | {"/docs/"}
    index_page = site / "docs" / "index.html"
    if index_page.is_file():
        problems.extend(check_docs_sidebar(read_text(index_page), "/docs/", targets))
    for index, item in enumerate(order):
        url = str(item["url"])
        relative = built.get(url)
        if relative is None:
            continue
        html = read_text(site / relative)

        # 侧栏：桌面与移动折叠两份都要覆盖全部文档页 + 总览入口，各自不重不漏。
        problems.extend(check_docs_sidebar(html, url, targets))

        # 上一节/下一节：按 content/docs 的 weight 升序，首末页没有多余邻居。
        prev_expected = str(order[index - 1]["url"]) if index > 0 else None
        next_expected = str(order[index + 1]["url"]) if index + 1 < len(order) else None
        prev_actual, next_actual, structure = docs_pager_links(html)
        for message in structure:
            problems.append(f"{url}: {message}")
        if prev_actual != prev_expected:
            problems.append(
                f"{url}: 上一节应为 {prev_expected or '无'}，实际为 {prev_actual or '无'}"
            )
        if next_actual != next_expected:
            problems.append(
                f"{url}: 下一节应为 {next_expected or '无'}，实际为 {next_actual or '无'}"
            )
        for label, actual in (("上一节", prev_actual), ("下一节", next_actual)):
            if actual is not None and actual not in built:
                problems.append(f"{url}: {label}指向不存在的文档页 {actual}")

    for problem in problems:
        fail("文档栏目：" + problem)
    if not problems:
        ok(
            f"文档栏目结构正确（总览 + {len(built)} 篇正文，"
            "侧栏覆盖完整，上一节/下一节与 weight 顺序一致）"
        )


def load_site_title() -> str:
    """hugo.toml 顶层的 title，用于校验 llms.txt 的 H1。"""
    match = re.search(r'(?m)^title\s*=\s*"([^"]+)"', read_text(ROOT / "hugo.toml"))
    return match.group(1) if match else ""


def check_llms(site: Path) -> None:
    """llms.txt：构建期生成、覆盖 sitemap 全部页面、无草稿与死链。"""
    title = load_site_title()
    path = site / "llms.txt"
    if not path.is_file():
        fail("缺少 llms.txt（home 的 LLMS 输出格式，见 layouts/index.llms.txt）")
        return
    raw = path.read_bytes()
    if not raw:
        fail("llms.txt 为空")
        return
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        fail(f"llms.txt 不是合法 UTF-8：{error}")
        return

    problems: list[str] = []
    if len(raw) > LLMS_MAX_BYTES:
        problems.append(f"体积 {len(raw)} 字节超过 {LLMS_MAX_BYTES}")
    non_empty = [line.strip() for line in text.splitlines() if line.strip()]
    if not non_empty or not non_empty[0].startswith("# "):
        problems.append("第一行应为 `# 站点名`")
    elif title and non_empty[0] != f"# {title}":
        problems.append(f"H1 应为 `# {title}`，实际是 `{non_empty[0]}`")
    if len(non_empty) < 2 or not non_empty[1].startswith("> "):
        problems.append("第二段应为 `> 摘要`（llms.txt 的 blockquote 约定）")

    internal: set[str] = set()
    dead: list[str] = []
    for raw_url in LLMS_LINK_RE.findall(text):
        parts = urlsplit(raw_url)
        if parts.scheme in ("mailto", "tel"):
            continue
        if parts.scheme in ("http", "https"):
            if parts.netloc and parts.netloc not in SITE_HOSTS:
                continue
            target = parts.path or "/"
        elif parts.scheme:
            continue
        else:
            target = parts.path or "/"
        internal.add(target)
        if target.endswith(".xml"):
            if not (site / target.lstrip("/")).is_file():
                dead.append(raw_url)
        elif internal_target(site, target) is None:
            dead.append(raw_url)
    if dead:
        problems.append("有死链：" + ", ".join(sorted(set(dead))[:8]))

    sitemap_paths: set[str] = set()
    sitemap = site / "sitemap.xml"
    if sitemap.is_file():
        sitemap_paths = {
            urlsplit(url).path or "/"
            for url in re.findall(r"<loc>(.*?)</loc>", read_text(sitemap))
        }
    if "/llms.txt" in sitemap_paths:
        problems.append("不应出现在 sitemap")
    missing = sitemap_paths - internal
    if missing:
        problems.append("漏掉 sitemap 页面：" + ", ".join(sorted(missing)))

    built = built_posts(site)
    listed_posts = {
        url for url in internal if url.startswith("/posts/") and url.endswith("/") and url != "/posts/"
    }
    extra = listed_posts - set(built)
    if extra:
        problems.append("列出了未构建的文章：" + ", ".join(sorted(extra)))
    missing_posts = set(built) - internal
    if missing_posts:
        problems.append("漏掉文章：" + ", ".join(sorted(missing_posts)))
    docs = built_docs(site)
    missing_docs = (set(docs) | {"/docs/"}) - internal
    if missing_docs:
        problems.append("漏掉文档入口：" + ", ".join(sorted(missing_docs)))

    for problem in problems:
        fail("llms.txt：" + problem)
    if not problems:
        ok(
            f"llms.txt 覆盖全部 {len(sitemap_paths)} 个可索引页面"
            f"（文章 {len(built)} 篇、文档 {len(docs)} 篇），无死链、不进 sitemap"
        )


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
    built = built_posts(site)
    posts = load_posts()
    resolved = resolved_post_meta(posts, built)
    check_pagination(site, pages, built)
    check_archives(site, pages, built, posts, resolved)
    check_post_navigation(site, built, resolved)
    check_post_updated(site, built, resolved)
    check_docs_section(site)
    check_llms(site)
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
