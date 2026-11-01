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
- 生产：`scripts/preview-check.sh https://yangspec.com` → 六路由分数、LCP 范围、CLS、Set-Cookie、第三方请求
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
