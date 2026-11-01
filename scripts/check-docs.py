#!/usr/bin/env python3
"""文档检查：相对链接、ADR 编号与索引、最后复核日期、阈值单一来源。

不读构建产物；`scripts/check.sh` 在构建后调用。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

FAILS: list[str] = []
PASSES: list[str] = []


def ok(message: str) -> None:
    PASSES.append(message)


def fail(message: str) -> None:
    FAILS.append(message)


LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE_RE = re.compile(r"```.*?```", re.S)
ADR_NAME_RE = re.compile(r"^(\d{4})-[a-z0-9-]+\.md$")
STATUS_RE = re.compile(r"(?m)^-\s*状态：(.+)$")
THRESHOLDS = [
    (r"Performance\s*≥\s*90", "Performance ≥ 90"),
    (r"Accessibility\s*≥\s*95", "Accessibility ≥ 95"),
    (r"LCP\s*≤\s*2\.5", "LCP ≤ 2.5"),
    (r"CLS\s*≤\s*0\.1", "CLS ≤ 0.1"),
    (r"TBT\s*≤\s*200", "TBT ≤ 200"),
]
SECRETS = [
    r"gh[pousr]_[A-Za-z0-9]{20,}",
    r"github_pat_[A-Za-z0-9_]{20,}",
    r"AKIA[0-9A-Z]{16}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
]
ALLOWED_STATUS = ("提议", "已采纳", "已取代", "已废弃")


def markdown_files() -> list[Path]:
    files = [ROOT / "README.md"]
    if DOCS.is_dir():
        files.extend(sorted(DOCS.rglob("*.md")))
    return [path for path in files if path.is_file()]


def check_links(files: list[Path]) -> None:
    checked = 0
    for path in files:
        text = FENCE_RE.sub("", path.read_text(encoding="utf-8", errors="replace"))
        for match in LINK_RE.finditer(text):
            target = match.group(1).strip()
            if not target or target.startswith(("#", "http://", "https://", "mailto:", "tel:")):
                continue
            parts = urlsplit(target)
            if parts.scheme:
                fail(f"{path.relative_to(ROOT)}: 不支持的链接协议 {target}")
                continue
            if not parts.path:
                continue
            resolved = (path.parent / unquote(parts.path)).resolve()
            if ROOT not in resolved.parents and resolved != ROOT:
                fail(f"{path.relative_to(ROOT)}: 链接越出仓库 {target}")
                continue
            checked += 1
            if not resolved.exists():
                line = text.count("\n", 0, match.start()) + 1
                fail(f"{path.relative_to(ROOT)}:{line}: 链接目标不存在 {target}")
    ok(f"文档相对链接可达（{checked} 个）")


def check_adrs() -> None:
    adr_dir = DOCS / "adr"
    if not adr_dir.is_dir():
        return
    index = adr_dir / "README.md"
    template = adr_dir / "template.md"
    if not index.is_file():
        fail("docs/adr/README.md 缺失")
        return
    if not template.is_file():
        fail("docs/adr/template.md 缺失")
    index_text = index.read_text(encoding="utf-8", errors="replace")
    numbers: list[str] = []
    for path in sorted(adr_dir.glob("*.md")):
        if path.name in {"README.md", "template.md"}:
            continue
        match = ADR_NAME_RE.match(path.name)
        if not match:
            fail(f"docs/adr/{path.name}: 文件名应为 NNNN-kebab-title.md")
            continue
        numbers.append(match.group(1))
        if path.name not in index_text:
            fail(f"docs/adr/{path.name}: 未出现在 README 索引")
        text = path.read_text(encoding="utf-8", errors="replace")
        status = STATUS_RE.search(text)
        if not status:
            fail(f"docs/adr/{path.name}: 缺少“- 状态：”")
        elif not status.group(1).strip().startswith(ALLOWED_STATUS):
            fail(f"docs/adr/{path.name}: 状态不在 提议/已采纳/已取代/已废弃 之内")
    if len(numbers) != len(set(numbers)):
        fail("ADR 编号重复")
    if numbers and sorted(numbers) != numbers:
        fail("ADR 编号未按升序排列")
    ok(f"ADR 文件名、状态与索引一致（{len(numbers)} 条）")


def check_review_date() -> None:
    index = DOCS / "README.md"
    if not index.is_file():
        fail("docs/README.md 缺失")
        return
    text = index.read_text(encoding="utf-8", errors="replace")
    if not re.search(r"最后复核：\d{4}-\d{2}-\d{2}", text):
        fail("docs/README.md 缺少“最后复核：YYYY-MM-DD”")
    else:
        ok("docs/README.md 有最后复核日期")


def check_single_source(files: list[Path]) -> None:
    hits = []
    for path in files:
        if path == ROOT / "CONSTRAINTS.md":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern, label in THRESHOLDS:
            for match in re.finditer(pattern, text):
                line = text.count("\n", 0, match.start()) + 1
                hits.append(f"{path.relative_to(ROOT)}:{line}（{label}）")
    if hits:
        for hit in hits:
            fail(f"阈值只写在 CONSTRAINTS.md，文档改为链接：{hit}")
    else:
        ok("文档没有复制 CONSTRAINTS.md 的阈值")


def check_secrets(files: list[Path]) -> None:
    hits = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in SECRETS:
            if re.search(pattern, text):
                hits.append(str(path.relative_to(ROOT)))
    if hits:
        fail("文档疑似包含密钥：" + ", ".join(sorted(set(hits))))
    else:
        ok("文档未发现密钥模式")


def main() -> int:
    if (ROOT / "public" / "docs").exists():
        fail("public/docs 存在：docs/ 不应进入 Hugo 构建")
    has_docs = DOCS.is_dir() and any(DOCS.rglob("*.md"))
    if not has_docs:
        ok("docs/ 尚未建立，跳过文档检查")
    else:
        files = markdown_files()
        check_links(files)
        check_adrs()
        check_review_date()
        check_single_source(files)
        check_secrets(files)

    for message in PASSES:
        print(f"[PASS] {message}")
    for message in FAILS:
        print(f"[FAIL] {message}")
    if FAILS:
        print(f"\n{len(FAILS)} 项失败")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
