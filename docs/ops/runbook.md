# 运维手册：发布、回滚、故障

命令都在仓库根目录执行。Hugo 需要 0.167.0 extended；本机没有全局安装时用 `HUGO_BIN` 指向该版本。

## 1. 发布前

1. 从 `main` 开工作分支（`feat/`、`fix/`、`content/`、`chore/`、`docs/`），一个分支只做一件事。
2. 构建与静态检查：

   ```bash
   HUGO_BIN=/path/to/hugo scripts/check.sh
   ```

   期望：退出码 0、0 个 `ERROR`、只有一条已登记的 `LanguageCode` 警告、所有检查项 `PASS`。
3. 改动布局或样式时，人工看 390 / 768 / 1440 px、深浅两套主题；键盘 Tab 走一遍导航与正文链接。
4. 开 PR，写清改了什么、为什么、验证命令与结果；改布局时附截图说明。

## 2. 发布

- 合并 PR 后，Cloudflare Pages 从 `main` 构建并发布。合并由站长执行。
- 分支预览：PR 的 Cloudflare 检查里有部署链接，别名是 `<branch>.yangspec.pages.dev`。
- 较长的分支名可能没有别名（访问返回 404），此时用部署哈希地址 `<hash>.yangspec.pages.dev`。

## 3. 发布后 10 分钟

```bash
scripts/preview-check.sh https://yangspec.com
```

期望：六条路由 Performance ≥ 90、Accessibility ≥ 95、LCP ≤ 2.5 s、CLS ≤ 0.1；无 `Set-Cookie`；无第三方请求；`nosniff`、`Referrer-Policy`、`Permissions-Policy`、`X-Frame-Options: DENY` 或 `frame-ancestors 'none'` 存在。

另外：

- 改了数据流（Cookie、表单、统计、`localStorage` 用途）时，核对 `/privacy/` 的描述与实际一致。
- 换了图标时，确认 `hugo.toml` 里 `[params.assets]` 的 `?v=` 已递增，否则浏览器与 CDN 会继续用缓存。

## 4. 回滚

1. 用 Cloudflare Pages 的部署回滚，回到上一个正常版本；不要用 revert 抢时间。
2. 回滚后 10 分钟内重跑第 3 节的生产检查。
3. 回滚原因与影响范围记录到 `ops/releases.md`（`ops-log` 模块启用后）。

## 5. 常见故障

| 现象 | 先查 | 处理 |
| --- | --- | --- |
| 构建失败 | 终端第一条 `ERROR` | 修好再跑 `check.sh`；不要跳过或放宽检查 |
| 预览 404 | 分支名与别名 | 用 PR 检查里的部署哈希地址 |
| 图标没更新 | `hugo.toml` 的 `?v=` | 递增版本号后重新发布 |
| 站内链接 404 | `check.sh` 的失败项 | 修 `ref` / `relref` 或目标文件路径 |
| 外链检查失败 | 目标站状态 | 403/429 记警告；5xx 等对方恢复后重跑 |
| Lighthouse 波动 | 网络与机器负载 | 同一 URL 重跑一次；仍低于阈值再当回归处理 |

## 6. 日常与月度

- 每月：`scripts/check.sh --full` 检查外链；抽查一次生产 `preview-check.sh`。
- 每季度：按 `CONSTRAINTS.md` 第 8 节评审阈值与例外。
- 升级 Hugo 或主题前：先确认兼容性，再同步 `README.md` 与 `CONSTRAINTS.md` 里的版本号。
