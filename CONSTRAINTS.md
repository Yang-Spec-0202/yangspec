# YangSpec 项目规范（CONSTRAINTS）

最后评审：2026-10-30 · 维护者：站长 · 下次评审：2027-01-31
适用范围：本仓库的 Hugo 源码、内容、静态资源与 Cloudflare Pages 部署配置。

这份文件定义“什么算可发布”。它优先于个人偏好和单次 PR 里的争论：改代码前先读，交付前按表自查。能自动检查的写成命令，不能自动检查的写成走查项；两者不混在一起冒充。

## 0. 底线（不因任何理由触碰）

1. 不新增绕过检查的注释或开关：`@ts-ignore`、`eslint-disable`、`# noqa`、`# type: ignore`、`nosemgrep`、`gitleaks:allow`。
2. 不留未完成品：`TODO` / `FIXME` 占位、`throw new Error("Not implemented")`、空 `catch {}`、`href="#"` 假链接、点了没反应的按钮。
3. 不跳过、不删除、不放宽检查来让改动通过。确需例外，按第 7 节登记，写明负责人与到期日。
4. 不把密码、验证码、Token、证件、银行或税务信息写进仓库、构建产物、日志或提交信息。
5. 不在源码引入 Cookie、表单、第三方统计、第三方字体/CDN 脚本。数据流一变，同一次改动内更新 `/privacy/`。
6. 不直接推送 `main`。所有改动走工作分支，经分支预览审阅后合并。
7. 不虚构经历、客户、数据或引用；不写“最好 / 第一 / 唯一”这类无法证实的自我评价。
8. 不为了“清理”删除 `archive/legacy-tools-site/`；恢复其中任何工具前，先确认原有测试与隐私文案仍然成立。

## 1. 已生效的约束

数字来自公开阈值或本站实测（第 5 节）。命令必须能在本仓库直接跑；跑不了就不算约束。

| # | 维度 | 约束 | 为什么是这个数 | 检查命令 | 运行时机 |
|---|------|------|----------------|----------|----------|
| 1 | 构建 | 退出码 0，0 个 `ERROR`；只允许 1 条已知 `WARN`（PaperMod 的 `.Language.LanguageCode` 弃用） | 构建错误必须当场归零；主题弃用警告是已登记的遗留，用 `--panicOnWarning` 会把它变成错误，不能假装没看见 | `HUGO_BIN=/path/to/hugo scripts/check.sh` | 每次改动 |
| 2 | 页面完整性 | `/`、`/about/`、`/contact/`、`/privacy/`、`404.html` 都存在；`sitemap.xml` 含四个可索引页面且不含 404 | 少一页就是线上 404；404 进 sitemap 会被搜索引擎收录 | 同上 | 每次改动 |
| 3 | 站内链接 | 断链 0；锚点指向存在的 `id`；无空链接、无 `href="#"` | 断链是读者唯一能立刻验证的错误 | 同上 | 每次改动 |
| 4 | Front matter | 每篇 `content/**/*.md` 都有 `title`、`date`、`description` | 缺 `description` 会让摘要与分享卡片退化成正文截断 | 同上 | 每次改动 |
| 5 | 身份字段 | 模板不硬编码邮箱、城市；正文出现的邮箱必须等于 `hugo.toml` 的 `params.email` | 改一次资料要改全站，是典型的“漏改一处就前后矛盾” | 同上 | 每次改动 |
| 6 | 源码隐私 | 源码不写 `document.cookie`，不引第三方统计/字体/CDN 脚本；`localStorage` 只允许主题偏好 `pref-theme` | 静态站的低成本承诺；源码扫描能在发布前拦住“顺手加个统计” | 同上 | 每次改动 |
| 7 | 传输预算 | 单页首次加载 ≤ 1 MB；首方 JS ≤ 10 KB（gzip） | 文字站的首屏预算应主要留给图片；超过 1 MB 在弱网下 LCP 必然失守 | 同上 | 每次改动 |
| 8 | 可访问性 | 移动端 Lighthouse Accessibility ≥ 95；无 critical/serious 问题（WCAG 2.2 AA） | AA 是公开站点的合理基线；95 给单条规则波动留余量 | `scripts/preview-check.sh <preview-url>` | 分支预览 |
| 9 | 性能 | 移动端 Lighthouse Performance ≥ 90；LCP ≤ 2.5 s；CLS ≤ 0.1；TBT ≤ 200 ms | 前三项是 Core Web Vitals 的 “good” 阈值；实验室拿不到稳定 INP，用 TBT 代理，字段数据出现后再以 INP ≤ 200 ms 为准 | 同上 | 分支预览 |
| 10 | 安全头 | 预览响应含 `nosniff`、`Referrer-Policy`、`Permissions-Policy`、`X-Frame-Options: DENY`/`frame-ancestors 'none'`，且站点自身不写 `Set-Cookie` | 静态站的低成本纵深防御；把“控制台里点过”变成仓库里可复现的配置 | 同上（localhost 自动跳过） | 分支预览 |
| 11 | 外链 | 发布前 4xx/5xx 为 0；403/429/超时重试后仍失败记警告，不阻断合并 | 外站会抖动、会防盗链，不能让别人的 503 卡住本站发布 | `scripts/check.sh --full` | 发布前 / 每月 |

运行时检查（8–10）依赖一个可访问的预览 URL；没有 URL 时标 `SKIP`，不得标 `PASS`。`scripts/preview-check.sh` 对 localhost 跳过安全头检查。

## 2. 内容规范

- 语言：简体中文。中英文之间加空格，使用全角标点；数字、单位、代码保持半角。
- Front matter 必填：`title`、`date`、`description`。`description` 同时用于摘要与分享卡片，写一句能独立成立的话，不堆关键词。
- 标题层级从 `##` 开始（`h1` 由模板输出），不跳级；一篇只表达一个主题。
- 图片必须有 `alt`；装饰图写 `alt=""`。正文图先经 Hugo 处理再输出，不直接引用外站图片，不加带追踪参数的 URL。
- 站内链接用 `ref` / `relref`，让构建期发现目标不存在；外链新窗口打开时必须带 `rel="noopener noreferrer"`。
- 事实、引文、数据给出来源链接和日期；无法核实的数字不写。日期统一 `YYYY-MM-DD`。
- 草稿用 `draft: true`，生产构建不包含；`--buildDrafts` 只允许本地使用。
- 隐私页逐项写清：Cloudflare 侧访问日志、是否启用 Web Analytics、`localStorage` 主题偏好、邮件留存、读者如何联系。不写“绝对安全”“完全匿名”。
- 对外文案与隐私页必须同时成立：首页说“没有第三方追踪脚本”，隐私页就不能写“使用访问统计”；反之亦然。当前两处不一致，见第 6 节。

## 3. 代码与结构规范

- 目录职责固定：`content/` 只放内容，`layouts/` 只放模板，`assets/` 放需处理的资源，`static/` 放原样发布的文件（含 `_headers`），`archive/` 不参与构建。
- 模板从 `baseof.html` 继承；可复用片段进 `_partials/`，不在页面模板里复制粘贴。署名、城市、邮箱一律取 `hugo.toml` 的 `params`。
- 样式只有 `assets/css/extended/personal.css` 一个入口；颜色与间距用自定义属性，深浅两套主题共用同一组变量。
- 新增 `!important` 必须注释原因。现有 `prefers-reduced-motion` 兜底与 `.block-more` 两处保留；改动对应区块时顺手清理。
- 首方 JS 只用于主题切换等必要交互，≤ 10 KB gzip，不引框架、不引 CDN。无 JS 时正文、导航、目录仍可用。
- 静态资源文件名用小写 kebab-case；图片给出宽高，避免 CLS；指纹化资源可长缓存，HTML 不缓存。
- 不为一个效果引入构建链。Node 只作为检查工具（Lighthouse），不进运行时。

## 4. 发布流程

1. 从 `main` 开工作分支：`feat/…`、`fix/…`、`content/…`、`chore/…`；一个分支一件事。
2. 提交用祈使句，说明“为什么”，不写“update”“fix bug”。一个提交只做一件事。
3. PR 写清：改了什么、为什么、验证命令与结果；改布局时附 390 / 768 / 1440 三档截图。
4. 合并条件：`scripts/check.sh` 通过、预览可访问、`preview-check.sh` 达标、diff 自审完成。合并由站长执行。
5. 发布即 push `main` 触发 Cloudflare Pages。发布后 10 分钟内核对线上响应头与 `/privacy/` 的数据流描述。
6. 回滚用 Cloudflare 的部署回滚，不靠 revert 抢时间。不 force-push 共享分支，不改写已发布历史。

## 5. 基线（2026-10-30 实测）

阈值先按现状记录，只要求“不变差”；等稳定后再收紧。工具：Hugo 0.167.0 extended、Chrome headless、Lighthouse 移动端默认节流。

| 指标 | 当前值 | 方向 |
|------|--------|------|
| 页面数 | 8 个 Hugo 页面，5 个 HTML（4 路由 + 404） | 不得无故减少 |
| 构建耗时 | 约 20–45 ms | 不得明显变慢 |
| HTML（gzip） | 首页 2.7 KB / 关于 3.1 KB / 隐私 3.3 KB | 单页不得增长 > 10% |
| CSS（gzip） | 6.3 KB | 不得增长 > 10% |
| 首方 JS（gzip） | ≈0.2–0.3 KB | 不得增长 |
| Lighthouse 移动端（localhost） | 四个页面均 100 / 100 / 100 / 100；LCP 0.6–0.8 s；CLS 0；TBT 0 ms | Performance 不得跌破 90 |
| Lighthouse 移动端（线上） | 2026-10-30：Performance 99–100，Accessibility 100，LCP 0.8–1.1 s，CLS 0 | 同上 |
| 站内链接 | 0 断链 | 必须保持 0 |
| 外链 | 3 个，均 200 | 失效数只降不升 |
| 正文对比度 | 5.7:1 – 12.6:1（深浅两套） | 正文 ≥ 4.5:1 |
| 站点 `Set-Cookie` | 线上 HEAD 未见 | 必须保持 0 |

Lighthouse 数字是单次实验室结果（localhost 与线上各一组），不等于真实用户字段数据；只用作回归门槛。

## 6. 待补齐与已知偏差

| 项 | 现状 | 处理 | 到期 |
|----|------|------|------|
| 隐私页与线上统计 | `/privacy/` 称使用 Cloudflare Web Analytics，但 2026-10-30 线上首页未注入 `cloudflareinsights` beacon（只见 Cloudflare email-decode 脚本） | 二选一：在 Cloudflare 开启 Web Analytics，或删掉隐私页对应段落；同时核对首页“没有第三方追踪脚本” | 2026-11-15 |
| 安全头来源 | 生产已有 `nosniff`、`Referrer-Policy`，但仓库此前没有 `_headers`，来源不可复现；2026-10-30 实测缺 `Permissions-Policy` 与 frame 保护 | 本分支新增 `static/_headers`；合并后在预览与生产核对四项头；HSTS 在控制台评估 `includeSubDomains` 后再开 | 2026-12-31 |
| CSP | 只设 `frame-ancestors`、`base-uri`、`form-action`；PaperMod 有内联主题脚本 | 升级主题时再评估 hash/nonce；不为了 CSP 引入 `unsafe-inline` 脚本白名单 | 主题升级时 |
| CI | 无 GitHub Actions，检查靠本地脚本 | 合并前手动跑；接入 CI 时把 `scripts/check.sh --full` 放进去 | 2026-12-31 |
| 外链监控 | 手动，发布前/每月 | 加定时任务或 GitHub Actions schedule | 2027-01-31 |
| 界面文案一致性 | 主题按钮初始中文、JS 运行时改成英文；表格提示为英文遗留 | 下一次 UI 改动统一为中文 | 2026-12-31 |

## 7. 例外

例外必须由站长登记；无负责人、无到期日、超过 90 天的例外自动失效。

| ID | 规则 | 范围 | 原因 | 负责人 | 到期 |
|----|------|------|------|--------|------|
| — | — | — | 暂无 | — | — |

## 8. 变更规则

- 收紧（新增规则、降低阈值）随时可做，单独提交。
- 放宽（删规则、抬阈值、加例外）必须单独 PR，标题以 `chore(constraints):` 开头，正文给出失败证据、替代方案与到期日。
- 本文件与功能改动不得出现在同一个提交里；评审时先看本文件 diff，再看代码。
- 每季度评审一次；阈值、工具或数据流变化时立即更新，不等季度。

## 9. 怎么跑

```bash
# 构建 + 静态检查（页面、链接、Front matter、身份、隐私、体积）
HUGO_BIN=/path/to/hugo scripts/check.sh

# 再加上外链检查（发布前或每月）
scripts/check.sh --full

# 本地预览后跑运行时检查（Lighthouse + Cookie/第三方请求）
python3 -m http.server 8099 --directory public
scripts/preview-check.sh http://127.0.0.1:8099
```

`HUGO_BIN` 不设时使用 PATH 里的 `hugo`；版本必须是 README 约定的 0.167.0 extended。没有 URL 时，第 8–10 项只能记 `SKIP`。
