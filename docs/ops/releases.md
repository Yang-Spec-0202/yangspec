# 发布记录

每次合并到 `main` 的生产部署追加一条，只追加、不改写。字段与红线见 [CONSTRAINTS.md](../../CONSTRAINTS.md) 第 3 节“工程日志”。本文件从 2026-11-01 起记录；第一条是基线，覆盖 `b54421a` 与 `673813e` 两次部署，更早的不追溯。

- 只记工程事实，不记访客数据（邮箱、IP、Cookie、Token、Cloudflare 账号信息一律不写）。
- 完整检查输出留在 gitignored 的 `reports/`，这里只留摘要。
- 回滚另起一条，写原因、影响范围与恢复时间。

## 模板

```markdown
### YYYY-MM-DD · <commit> · <一句话摘要>
- 改动：<PR 与范围>
- 检查：`scripts/check-record.sh --full` → 退出码、PASS 数、报告文件
- 生产：`scripts/preview-check.sh https://yangspec.com` → 七路由分数、LCP 范围、CLS、Set-Cookie、第三方请求
- 回滚点：<上一个生产 commit>
- 异常：无 / <现象、处理、耗时>
```

## 记录

### 2026-11-01 · 673813e · 文档与工程日志规范落地（基线）

- 改动：`b54421a` 把文档与工程日志规范写入 `CONSTRAINTS.md`，新增 `scripts/check-docs.py` 并接入 `check.sh`；`673813e`（PR #9）新增 `docs/`（架构、ADR、发布手册），README 收敛为入口。本条是工程日志启用后的基线。
- 检查：`scripts/check-record.sh --full` → 退出码 0，16 条 PASS（`check.py` 汇总 11 项 + 文档检查 5 项；Hugo 11 页、站内 0 断链、外链 3 个可达）；报告 `reports/check-20261101T192806.txt`。
- 生产：六条路由 Performance 100 / Accessibility 100，LCP 831–1041 ms，CLS 0；无 `Set-Cookie`，第三方请求仅 Cloudflare Web Analytics beacon，安全头齐全。
- 回滚点：`b54421a`（文档与日志规范合并，PR #9 之前的部署）。
- 异常：无。`docs/` 不参与构建，站点输出未变。

### 2026-11-01 · 1f919df · 发布记录与 check-record.sh

- 改动：PR #10 新增 `scripts/check-record.sh`，把 `check.sh` 的输出、commit 与退出码留到 gitignored 的 `reports/`；新增 `docs/ops/releases.md`，runbook 增加“记录发布”一节。复核时修正了首条记录的基线范围、回滚点与第三方请求表述。
- 检查：`scripts/check-record.sh --full` → 退出码 0，16 条 PASS（`check.py` 汇总 11 项 + 文档检查 5 项）；报告 `reports/check-20261101T194316.txt`。
- 生产：六条路由 Performance 100 / Accessibility 100，LCP 0.816–1.054 s，CLS 0；无 `Set-Cookie`，第三方请求仅 Cloudflare Web Analytics beacon，安全头齐全。
- 回滚点：`673813e`（PR #9 合并）。
- 异常：无。仅文档与检查脚本变化，站点输出未变。

### 2026-11-02 · bf41f95 · 文章分页、按年归档与文章导航

- 改动：PR #11（`feat/writing`）给 `/posts/` 增加分页（每页 8 篇），新增 `/archives/` 按年归档，文章页增加上一篇/下一篇与最后更新；`check.py` 增加分页结构、归档覆盖、邻居链与 lastmod 渲染检查，`preview-check.sh` 覆盖七条路由；决策记入 ADR 0004。
- 检查：`scripts/check-record.sh --full` → 退出码 0，`check.py` 15 项 PASS（含外链 3 个可达）+ `check-docs.py` 5 项 PASS，Hugo 12 页、站内 0 断链；报告 `reports/check-20261102T131315.txt`。
- 生产：七条路由 Performance 97–100（最低 `/posts/` 97）/ Accessibility 100，LCP 0.83–1.11 s，CLS 0，TBT 0 ms；无 `Set-Cookie`，第三方请求仅 Cloudflare Web Analytics beacon，安全头齐全。
- 回滚点：`9de7f13`（合并前的 `main`）。
- 异常：无。上线后 `/archives/`、文章页与 sitemap 均与构建一致；`/posts/page/1/` 是指向 `/posts/` 的别名，不进 sitemap。
