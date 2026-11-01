# 发布记录

每次合并到 `main` 的生产部署追加一条，只追加、不改写。字段与红线见 [CONSTRAINTS.md](../../CONSTRAINTS.md) 第 3 节“工程日志”。

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

### 2026-11-01 · 673813e · 工程文档与文档/日志规范

- 改动：PR #9 新增 `docs/`（架构、ADR、发布手册），README 收敛为入口；`CONSTRAINTS.md` 第 3 节增加文档与工程日志规范、第 5 节基线复测；新增 `scripts/check-docs.py` 并接入 `check.sh`。
- 检查：`scripts/check-record.sh --full` → 退出码 0，16 项 PASS（Hugo 11 页、站内 0 断链、外链 3 个可达、文档检查 5 项）；报告 `reports/check-20261101T192806.txt`。
- 生产：六条路由 Performance 100 / Accessibility 100，LCP 831–1041 ms，CLS 0；无 `Set-Cookie`，无第三方请求，安全头齐全。
- 回滚点：`99e207d`（PR #8 合并）。
- 异常：无。`docs/` 不参与构建，站点输出未变。
